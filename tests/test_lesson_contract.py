# -*- coding: utf-8 -*-
"""Acceptance tests for the additive, idempotent lesson contract."""

import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from usmc import USMCClient, api
from usmc import schema


V1_SQL = """
CREATE TABLE usmc_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL,
    key TEXT NOT NULL, value TEXT NOT NULL, confidence REAL DEFAULT 1.0,
    source TEXT, agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    UNIQUE(agent_id, category, key)
);
CREATE TABLE usmc_working (
    id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL DEFAULT 'note',
    content TEXT NOT NULL, priority INTEGER DEFAULT 0, tags TEXT,
    agent_id TEXT NOT NULL DEFAULT 'default', is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE usmc_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL DEFAULT 'general',
    severity TEXT NOT NULL DEFAULT 'medium', title TEXT NOT NULL,
    problem TEXT NOT NULL, solution TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default', is_active INTEGER DEFAULT 1,
    confidence REAL DEFAULT 1.0, times_shown INTEGER DEFAULT 0,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE usmc_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL,
    started_at TEXT NOT NULL, ended_at TEXT, current_task TEXT,
    handoff_notes TEXT
);
CREATE TABLE usmc_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
INSERT INTO usmc_meta VALUES ('schema_version', '1');
"""


class TempDbCase(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.db_path = handle.name

    def tearDown(self):
        api._client = None
        for suffix in ("", "-wal", "-shm"):
            try:
                os.unlink(self.db_path + suffix)
            except OSError:
                pass


class TestLessonMigration(TempDbCase):
    def _create_v1(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(V1_SQL)
        conn.execute(
            "INSERT INTO usmc_lessons "
            "(category, severity, title, problem, solution, agent_id, "
            "is_active, confidence, times_shown, created_at, updated_at) "
            "VALUES ('bug', 'high', 'Alt', 'Problem', 'Lösung', 'legacy', "
            "1, 1.0, 2, '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
        )
        conn.commit()
        conn.close()

    def test_v1_database_migrates_additively_and_old_path_stays_usable(self):
        self._create_v1()

        client = USMCClient(self.db_path, "new")
        lesson = client.get_lessons()[0]
        self.assertEqual(lesson["title"], "Alt")
        self.assertEqual(lesson["editorial_status"], "legacy")
        self.assertEqual(lesson["source_kind"], "legacy")
        self.assertEqual(lesson["times_shown"], 2)
        self.assertEqual(lesson["weight"], 1.0)

        old_result = client.add_lesson("Neu", "P", "S")
        self.assertFalse(old_result["upserted"])
        self.assertEqual(old_result["weight"], 1.0)
        self.assertEqual(len(client.get_lessons()), 2)

        conn = sqlite3.connect(self.db_path)
        self.assertEqual(schema.get_schema_version(conn), 2)
        schema.migrate(conn)
        schema.migrate(conn)
        self.assertEqual(schema.get_schema_version(conn), 2)

        # Ein alter Client kennt nur die v1-Spalten. Dessen INSERT bleibt nach
        # der Expand-Migration gültig und ist anschließend über v2 lesbar.
        conn.execute(
            "INSERT INTO usmc_lessons "
            "(category, severity, title, problem, solution, agent_id, "
            "is_active, confidence, times_shown, created_at, updated_at) "
            "VALUES ('general', 'medium', 'Alter Client', 'P', 'S', "
            "'v1-writer', 1, 1.0, 0, '2026-01-02T00:00:00', "
            "'2026-01-02T00:00:00')"
        )
        conn.commit()
        conn.close()
        mixed = client.get_lessons(grep="Alter Client")[0]
        self.assertEqual(mixed["source_kind"], "legacy")
        self.assertEqual(mixed["editorial_status"], "legacy")

    def test_v1_database_without_meta_is_detected_and_migrated(self):
        self._create_v1()
        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP TABLE usmc_meta")
        conn.commit()
        conn.close()

        client = USMCClient(self.db_path, "missing-meta")
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(schema.get_schema_version(conn), 2)
        conn.close()
        self.assertEqual(client.get_lessons()[0]["title"], "Alt")

    def test_partial_v1_migration_is_retry_safe(self):
        self._create_v1()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "ALTER TABLE usmc_lessons ADD COLUMN source_kind "
            "TEXT NOT NULL DEFAULT 'legacy'"
        )
        conn.commit()
        conn.close()

        client = USMCClient(self.db_path, "retry")
        columns = {
            row[1]
            for row in sqlite3.connect(self.db_path)
            .execute("PRAGMA table_info(usmc_lessons)")
            .fetchall()
        }
        self.assertIn("source_key", columns)
        self.assertIn("delivery_failure_count", columns)
        self.assertEqual(client.get_lessons()[0]["title"], "Alt")

    def test_partial_v2_repairs_all_columns_and_named_indexes(self):
        USMCClient(self.db_path, "partial-v2")
        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP INDEX idx_lessons_source_episode")
        conn.execute("DROP TABLE usmc_lesson_feedback")
        conn.execute("DROP TABLE usmc_lesson_delivery_batches")
        conn.execute("DROP TABLE usmc_lesson_deliveries")
        conn.executescript("""
            CREATE TABLE usmc_lesson_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER, feedback_key TEXT, helpful INTEGER,
                independent_repeat INTEGER DEFAULT 0,
                delivery_failed INTEGER DEFAULT 0, delivery_key TEXT,
                payload_hash TEXT, agent_id TEXT, created_at TEXT
            );
            CREATE TABLE usmc_lesson_delivery_batches (
                delivery_key TEXT, session_key TEXT, delivery_mode TEXT,
                request_hash TEXT, agent_id TEXT, created_at TEXT
            );
            CREATE TABLE usmc_lesson_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER, delivery_key TEXT, session_key TEXT,
                delivery_mode TEXT, context TEXT, feedback_prompt TEXT,
                agent_id TEXT, created_at TEXT
            );
        """)
        conn.commit()
        schema.migrate(conn)
        schema.migrate(conn)

        self.assertIn(
            "event_anchor",
            {row[1] for row in conn.execute("PRAGMA table_info(usmc_lesson_feedback)")},
        )
        self.assertIn(
            "session_id",
            {row[1] for row in conn.execute(
                "PRAGMA table_info(usmc_lesson_delivery_batches)"
            )},
        )
        self.assertIn(
            "payload_hash",
            {row[1] for row in conn.execute("PRAGMA table_info(usmc_lesson_deliveries)")},
        )
        indexes = {
            row[1]
            for table in (
                "usmc_lessons", "usmc_lesson_feedback",
                "usmc_lesson_delivery_batches", "usmc_lesson_deliveries",
            )
            for row in conn.execute(f"PRAGMA index_list({table})")
        }
        self.assertTrue({
            "idx_lessons_source_episode",
            "idx_lesson_feedback_key",
            "idx_lesson_delivery_batches_key",
            "idx_lesson_deliveries_lesson_key",
            "idx_lesson_deliveries_batch_order",
        }.issubset(indexes))
        self.assertEqual(schema.get_schema_version(conn), 2)
        conn.close()

    def test_partial_v2_backfills_keyed_lesson_payload_hash(self):
        client = USMCClient(self.db_path, "payload-backfill")
        lesson = client.add_lesson(
            "Backfill", "Problem", "Lösung",
            source_key="legacy-v2", episode_key="episode",
            event_anchor="anchor", evidence_class="verified",
            sensitive_source=True,
        )
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE usmc_lessons SET ingest_payload_hash = NULL WHERE id = ?",
            (lesson["id"],),
        )
        conn.commit()
        schema.migrate(conn)
        payload_hash = conn.execute(
            "SELECT ingest_payload_hash FROM usmc_lessons WHERE id = ?",
            (lesson["id"],),
        ).fetchone()[0]
        self.assertTrue(payload_hash)
        schema.migrate(conn)
        conn.close()

        retry = client.add_lesson(
            "Backfill", "Problem", "Lösung",
            source_key="legacy-v2", episode_key="episode",
            event_anchor="anchor", evidence_class="verified",
            sensitive_source=True,
        )
        self.assertFalse(retry["created"])
        self.assertTrue(retry["sensitive_source"])

    def test_global_feedback_duplicates_fail_migration_and_roll_back(self):
        client = USMCClient(self.db_path, "duplicate-fixture")
        first = client.add_lesson("Erste", "P", "S")
        second = client.add_lesson("Zweite", "P", "S")
        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP TABLE usmc_lesson_feedback")
        conn.executescript("""
            CREATE TABLE usmc_lesson_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL, feedback_key TEXT NOT NULL,
                helpful INTEGER, independent_repeat INTEGER DEFAULT 0,
                delivery_failed INTEGER DEFAULT 0, delivery_key TEXT,
                payload_hash TEXT, agent_id TEXT, created_at TEXT,
                UNIQUE(lesson_id, feedback_key)
            );
        """)
        for lesson_id, payload_hash in ((first["id"], "a"), (second["id"], "b")):
            conn.execute(
                "INSERT INTO usmc_lesson_feedback "
                "(lesson_id, feedback_key, helpful, payload_hash, agent_id, created_at) "
                "VALUES (?, 'globally-duplicated', 1, ?, 'fixture', '2026-01-01')",
                (lesson_id, payload_hash),
            )
        conn.execute(
            "UPDATE usmc_meta SET value = '1' WHERE key = 'schema_version'"
        )
        conn.commit()

        with self.assertRaisesRegex(RuntimeError, "Feedback-Idempotenzmigration"):
            schema.migrate(conn)
        self.assertEqual(schema.get_schema_version(conn), 1)
        self.assertNotIn(
            "event_anchor",
            {row[1] for row in conn.execute("PRAGMA table_info(usmc_lesson_feedback)")},
        )
        self.assertEqual(
            conn.execute(
                "SELECT COUNT(*) FROM usmc_lesson_feedback "
                "WHERE feedback_key = 'globally-duplicated'"
            ).fetchone()[0],
            2,
        )
        self.assertNotIn(
            "idx_lesson_feedback_key",
            {row[1] for row in conn.execute("PRAGMA index_list(usmc_lesson_feedback)")},
        )
        conn.close()


class TestIdempotentLessonIntake(TempDbCase):
    def setUp(self):
        super().setUp()
        self.client = USMCClient(self.db_path, "writer")

    def test_keyed_retry_is_immutable_and_preserves_protection(self):
        first = self.client.add_lesson(
            "Titel", "Problem", "Lösung",
            source_key="hook:codex", episode_key="episode-1",
            event_anchor="event-1", evidence_class="verified",
            sensitive_source=True,
        )
        self.client.record_lesson_feedback(
            first["id"], "feedback-1", helpful=True
        )
        self.client.set_lesson_editorial_status(first["id"], "approved")

        second = self.client.add_lesson(
            "Titel", "Problem", "Lösung",
            source_key="hook:codex", episode_key="episode-1",
            event_anchor="event-1", evidence_class="verified",
            sensitive_source=True,
        )
        self.assertEqual(first["id"], second["id"])
        self.assertFalse(second["created"])
        self.assertEqual(second["created_at"], first["created_at"])
        self.assertEqual(second["helpful_count"], 1)
        self.assertEqual(second["editorial_status"], "approved")
        self.assertTrue(second["sensitive_source"])
        self.assertEqual(second["confidence"], 0.2)
        self.assertEqual(len(self.client.get_lessons()), 1)

        with self.assertRaisesRegex(ValueError, "anderen Lesson-Payload"):
            self.client.add_lesson(
                "Titel", "Problem", "Lösung",
                source_key="hook:codex", episode_key="episode-1",
                event_anchor="event-1", evidence_class="verified",
                sensitive_source=False,
            )
        protected = self.client.get_lesson(first["id"])
        self.assertEqual(protected["title"], "Titel")
        self.assertTrue(protected["sensitive_source"])
        policy = self.client.evaluate_lesson_promotion(
            first["id"], direct_promotion_enabled=True
        )
        self.assertFalse(policy["allowed"])
        self.assertIn("sensitive-source", policy["review_reasons"])
        self.assertEqual(
            self.client.deliver_lessons(
                "protected-session", "protected-delivery",
                lesson_ids=[first["id"]],
            ),
            [],
        )

    def test_concurrent_retries_deduplicate_to_one_row(self):
        workers = 8
        barrier = Barrier(workers)

        def write(index):
            client = USMCClient(self.db_path, f"agent-{index}")
            barrier.wait()
            return client.add_lesson(
                "Parallel", "P", "S",
                source_key="source", episode_key="episode",
                event_anchor="event",
            )["id"]

        with ThreadPoolExecutor(max_workers=workers) as pool:
            ids = list(pool.map(write, range(workers)))

        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(len(self.client.get_lessons(grep="Parallel")), 1)

    def test_aborted_insert_can_be_retried_without_duplicate(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TRIGGER fail_lesson BEFORE INSERT ON usmc_lessons
            BEGIN SELECT RAISE(ABORT, 'simulated crash'); END
        """)
        conn.commit()
        conn.close()

        with self.assertRaises(sqlite3.IntegrityError):
            self.client.add_lesson(
                "Crash", "P", "S", source_key="source", episode_key="crash"
            )
        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP TRIGGER fail_lesson")
        conn.commit()
        conn.close()

        first = self.client.add_lesson(
            "Crash", "P", "S", source_key="source", episode_key="crash"
        )
        second = self.client.add_lesson(
            "Crash", "P", "S", source_key="source", episode_key="crash"
        )
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(self.client.get_lessons(grep="Crash")), 1)


class TestLessonFeedbackAndDelivery(TempDbCase):
    def setUp(self):
        super().setUp()
        self.client = USMCClient(self.db_path, "feedback")
        self.lesson = self.client.add_lesson(
            "Encoding", "cp1252", "UTF-8 verwenden",
            source_key="source", episode_key="episode",
            event_anchor="event", evidence_class="verified",
        )

    def test_helpful_repeat_and_delivery_failure_are_separate(self):
        self.client.set_lesson_editorial_status(self.lesson["id"], "approved")
        delivered = self.client.deliver_lessons(
            "session-1", "delivery-1", lesson_ids=[self.lesson["id"]]
        )
        self.assertEqual(delivered[0]["feedback_prompt"], "War diese Lesson hilfreich? (ja/nein)")

        helpful = self.client.record_lesson_feedback(
            self.lesson["id"], "f-helpful", helpful=True,
            delivery_key="delivery-1",
        )
        repeated = self.client.record_lesson_feedback(
            self.lesson["id"], "f-repeat", independent_repeat=True,
            delivery_key="delivery-1",
        )
        failed = self.client.record_lesson_feedback(
            self.lesson["id"], "f-failed", delivery_failed=True,
            delivery_key="delivery-1",
        )
        self.assertEqual(helpful["weight"], 0.3)
        self.assertTrue(repeated["delivery_failure_candidate"])
        self.assertEqual(repeated["independent_repeat_count"], 1)
        self.assertEqual(failed["delivery_failure_count"], 1)
        self.assertEqual(failed["weight"], 0.25)

    def test_feedback_retry_is_idempotent_and_conflict_is_rejected(self):
        first = self.client.record_lesson_feedback(
            self.lesson["id"], "same", helpful=True
        )
        second = self.client.record_lesson_feedback(
            self.lesson["id"], "same", helpful=True
        )
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(second["helpful_count"], 1)
        with self.assertRaises(ValueError):
            self.client.record_lesson_feedback(
                self.lesson["id"], "same", helpful=False
            )

    def test_feedback_key_is_globally_exactly_once(self):
        other = self.client.add_lesson(
            "Andere Lesson", "P", "S",
            source_key="source", episode_key="other-feedback",
        )
        first = self.client.record_lesson_feedback(
            self.lesson["id"], "global-feedback", helpful=True
        )
        retry = self.client.record_lesson_feedback(
            self.lesson["id"], "global-feedback", helpful=True
        )
        self.assertTrue(first["created"])
        self.assertFalse(retry["created"])

        with self.assertRaisesRegex(ValueError, "bereits global"):
            self.client.record_lesson_feedback(
                other["id"], "global-feedback", helpful=True
            )
        with self.assertRaisesRegex(ValueError, "bereits global"):
            self.client.record_lesson_feedback(
                self.lesson["id"], "global-feedback", independent_repeat=True
            )
        self.assertEqual(self.client.get_lesson(self.lesson["id"])["helpful_count"], 1)
        self.assertEqual(self.client.get_lesson(other["id"])["helpful_count"], 0)

    def test_concurrent_same_feedback_key_counts_once(self):
        workers = 8
        barrier = Barrier(workers)

        def write(index):
            client = USMCClient(self.db_path, f"feedback-{index}")
            barrier.wait()
            return client.record_lesson_feedback(
                self.lesson["id"], "parallel-feedback", helpful=True
            )["created"]

        with ThreadPoolExecutor(max_workers=workers) as pool:
            created = list(pool.map(write, range(workers)))

        self.assertEqual(created.count(True), 1)
        self.assertEqual(self.client.get_lesson(self.lesson["id"])["helpful_count"], 1)

    def test_feedback_transaction_rolls_back_and_retries_cleanly(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TRIGGER fail_feedback BEFORE INSERT ON usmc_lesson_feedback
            BEGIN SELECT RAISE(ABORT, 'simulated crash'); END
        """)
        conn.commit()
        conn.close()
        with self.assertRaises(sqlite3.IntegrityError):
            self.client.record_lesson_feedback(
                self.lesson["id"], "retry", helpful=True
            )
        self.assertEqual(self.client.get_lesson(self.lesson["id"])["helpful_count"], 0)

        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP TRIGGER fail_feedback")
        conn.commit()
        conn.close()
        result = self.client.record_lesson_feedback(
            self.lesson["id"], "retry", helpful=True
        )
        self.assertEqual(result["helpful_count"], 1)

    def test_delivery_retry_does_not_increment_times_shown(self):
        self.client.set_lesson_editorial_status(self.lesson["id"], "approved")
        first = self.client.deliver_lessons(
            "session", "delivery", context="Encoding"
        )
        second = self.client.deliver_lessons(
            "session", "delivery", context="Encoding"
        )
        self.assertTrue(first[0]["new_delivery"])
        self.assertFalse(second[0]["new_delivery"])
        self.assertEqual(self.client.get_lesson(self.lesson["id"])["times_shown"], 1)
        with self.assertRaises(ValueError):
            self.client.deliver_lessons(
                "session", "delivery", context="anderer Kontext"
            )

    def test_delivery_retry_replays_first_batch_without_reselection(self):
        self.client.set_lesson_editorial_status(self.lesson["id"], "approved")
        first = self.client.deliver_lessons(
            "stable-session", "stable-delivery", context="Encoding", limit=1
        )
        self.assertEqual([item["id"] for item in first], [self.lesson["id"]])

        later = self.client.add_lesson(
            "Encoding bevorzugt", "Encoding", "Neue Lösung",
            source_key="source", episode_key="later",
            event_anchor="later", weight=0.9,
        )
        self.client.set_lesson_editorial_status(later["id"], "approved")
        retry = self.client.deliver_lessons(
            "stable-session", "stable-delivery", context="Encoding", limit=1
        )
        self.assertEqual([item["id"] for item in retry], [self.lesson["id"]])
        self.assertFalse(retry[0]["new_delivery"])
        self.assertEqual(self.client.get_lesson(self.lesson["id"])["times_shown"], 1)
        self.assertEqual(self.client.get_lesson(later["id"])["times_shown"], 0)
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(
            conn.execute(
                "SELECT COUNT(*) FROM usmc_lesson_deliveries "
                "WHERE delivery_key = 'stable-delivery'"
            ).fetchone()[0],
            1,
        )
        conn.close()

    def test_concurrent_same_delivery_key_counts_once(self):
        self.client.set_lesson_editorial_status(self.lesson["id"], "approved")
        workers = 8
        barrier = Barrier(workers)

        def deliver(index):
            client = USMCClient(self.db_path, f"delivery-{index}")
            barrier.wait()
            result = client.deliver_lessons(
                "session-parallel", "delivery-parallel",
                lesson_ids=[self.lesson["id"]],
            )
            return result[0]["new_delivery"]

        with ThreadPoolExecutor(max_workers=workers) as pool:
            created = list(pool.map(deliver, range(workers)))

        self.assertEqual(created.count(True), 1)
        self.assertEqual(self.client.get_lesson(self.lesson["id"])["times_shown"], 1)

    def test_aborted_delivery_rolls_back_batch_and_retries_cleanly(self):
        self.client.set_lesson_editorial_status(self.lesson["id"], "approved")
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TRIGGER fail_delivery BEFORE INSERT ON usmc_lesson_deliveries
            BEGIN SELECT RAISE(ABORT, 'simulated delivery crash'); END
        """)
        conn.commit()
        conn.close()

        with self.assertRaises(sqlite3.IntegrityError):
            self.client.deliver_lessons(
                "session-crash", "delivery-crash",
                lesson_ids=[self.lesson["id"]],
            )
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(
            conn.execute(
                "SELECT COUNT(*) FROM usmc_lesson_delivery_batches "
                "WHERE delivery_key = 'delivery-crash'"
            ).fetchone()[0],
            0,
        )
        conn.execute("DROP TRIGGER fail_delivery")
        conn.commit()
        conn.close()

        result = self.client.deliver_lessons(
            "session-crash", "delivery-crash",
            lesson_ids=[self.lesson["id"]],
        )
        self.assertTrue(result[0]["new_delivery"])
        self.assertEqual(self.client.get_lesson(self.lesson["id"])["times_shown"], 1)


class TestLessonPolicyAndSessionStart(TempDbCase):
    def setUp(self):
        super().setUp()
        self.client = USMCClient(self.db_path, "policy")

    def _lesson(self, episode, **kwargs):
        return self.client.add_lesson(
            f"Lesson {episode}", "Problem", "Lösung",
            source_key="agent:codex", episode_key=episode,
            event_anchor=f"event:{episode}", evidence_class="verified",
            **kwargs,
        )

    def test_direct_promotion_is_pure_and_product_gate_defaults_off(self):
        lesson = self._lesson("eligible")
        default = self.client.evaluate_lesson_promotion(lesson["id"])
        enabled = self.client.evaluate_lesson_promotion(
            lesson["id"], direct_promotion_enabled=True
        )
        self.assertTrue(default["eligible"])
        self.assertFalse(default["allowed"])
        self.assertEqual(default["review_reasons"], ["product-gate-disabled"])
        self.assertTrue(enabled["allowed"])
        self.assertFalse(enabled["automatic_publication"])
        self.assertEqual(self.client.get_lesson(lesson["id"])["editorial_status"], "review")

    def test_privacy_policy_conflict_sensitive_and_mutation_always_review(self):
        cases = {
            "public": ({"privacy_scope": "public"}, "privacy-not-local-private"),
            "sensitive": ({"sensitive_source": True}, "sensitive-source"),
            "preference": ({"user_preference": True}, "user-preference"),
            "policy": ({"policy_relevant": True}, "policy-relevant"),
            "conflict": ({"conflict_flag": True}, "conflict"),
            "skill": ({"mutates_skill": True}, "skill-mutation"),
            "workflow": ({"mutates_workflow": True}, "workflow-mutation"),
        }
        for episode, (kwargs, reason) in cases.items():
            with self.subTest(episode=episode):
                lesson = self._lesson(episode, **kwargs)
                policy = self.client.evaluate_lesson_promotion(
                    lesson["id"], direct_promotion_enabled=True
                )
                self.assertFalse(policy["eligible"])
                self.assertFalse(policy["allowed"])
                self.assertIn(reason, policy["review_reasons"])

    def test_session_start_is_bounded_contextual_and_review_gated(self):
        visible = []
        for index in range(4):
            lesson = self._lesson(f"visible-{index}")
            self.client.set_lesson_editorial_status(lesson["id"], "approved")
            visible.append(lesson["id"])
        hidden_review = self._lesson("hidden-review")
        hidden_public = self._lesson("hidden-public", privacy_scope="public")
        self.client.set_lesson_editorial_status(hidden_public["id"], "approved")
        hidden_sensitive = self._lesson("hidden-sensitive", sensitive_source=True)
        self.client.set_lesson_editorial_status(hidden_sensitive["id"], "approved")

        started = self.client.start_session(
            task="Lesson visible",
            lesson_context="Lesson visible",
            lesson_limit=3,
            delivery_key="start-1",
        )
        delivered_ids = {item["id"] for item in started["lessons"]}
        self.assertEqual(len(delivered_ids), 3)
        self.assertTrue(delivered_ids.issubset(set(visible)))
        self.assertNotIn(hidden_review["id"], delivered_ids)
        self.assertNotIn(hidden_public["id"], delivered_ids)
        self.assertNotIn(hidden_sensitive["id"], delivered_ids)
        generated = self.client.generate_context(max_items=20)
        self.assertNotIn("hidden-review", generated)
        self.assertNotIn("hidden-public", generated)
        self.assertNotIn("hidden-sensitive", generated)

        plain = self.client.start_session(task="Ohne Zustellung")
        self.assertNotIn("lessons", plain)
        with self.assertRaises(ValueError):
            self.client.start_session(lesson_context="Lesson")
        with self.assertRaises(ValueError):
            self.client.deliver_lessons("s", "d", context="Lesson", limit=4)

    def test_session_start_delivery_is_atomic_and_retry_returns_same_session(self):
        lesson = self._lesson("atomic-success")
        self.client.set_lesson_editorial_status(lesson["id"], "approved")
        first = self.client.start_session(
            task="Atomar",
            lesson_ids=[lesson["id"]],
            delivery_key="atomic-start",
        )
        retry = self.client.start_session(
            task="Atomar",
            lesson_ids=[lesson["id"]],
            delivery_key="atomic-start",
        )
        self.assertEqual(first["id"], retry["id"])
        self.assertTrue(first["lessons"][0]["new_delivery"])
        self.assertFalse(retry["lessons"][0]["new_delivery"])
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM usmc_sessions").fetchone()[0], 1)
        self.assertEqual(
            conn.execute(
                "SELECT COUNT(*) FROM usmc_lesson_deliveries "
                "WHERE delivery_key = 'atomic-start'"
            ).fetchone()[0],
            1,
        )
        conn.close()
        self.assertEqual(self.client.get_lesson(lesson["id"])["times_shown"], 1)

        with self.assertRaisesRegex(ValueError, "andere Anfrage"):
            self.client.start_session(
                task="Geänderter Payload",
                lesson_ids=[lesson["id"]],
                delivery_key="atomic-start",
            )
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM usmc_sessions").fetchone()[0], 1)
        conn.close()
        self.assertEqual(self.client.get_lesson(lesson["id"])["times_shown"], 1)

    def test_session_start_delivery_failure_rolls_back_and_retries_cleanly(self):
        lesson = self._lesson("atomic-failure")
        self.client.set_lesson_editorial_status(lesson["id"], "approved")
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TRIGGER fail_atomic_delivery
            BEFORE INSERT ON usmc_lesson_deliveries
            BEGIN SELECT RAISE(ABORT, 'simulated atomic delivery crash'); END
        """)
        conn.commit()
        conn.close()

        with self.assertRaises(sqlite3.IntegrityError):
            self.client.start_session(
                task="Rollback",
                lesson_ids=[lesson["id"]],
                delivery_key="atomic-failure",
            )
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM usmc_sessions").fetchone()[0], 0)
        self.assertEqual(
            conn.execute(
                "SELECT COUNT(*) FROM usmc_lesson_delivery_batches "
                "WHERE delivery_key = 'atomic-failure'"
            ).fetchone()[0],
            0,
        )
        conn.execute("DROP TRIGGER fail_atomic_delivery")
        conn.commit()
        conn.close()
        self.assertEqual(self.client.get_lesson(lesson["id"])["times_shown"], 0)

        retried = self.client.start_session(
            task="Rollback",
            lesson_ids=[lesson["id"]],
            delivery_key="atomic-failure",
        )
        self.assertEqual(len(retried["lessons"]), 1)
        self.assertEqual(self.client.get_lesson(lesson["id"])["times_shown"], 1)

    def test_session_start_rejects_standalone_delivery_key_without_session_row(self):
        lesson = self._lesson("atomic-collision")
        self.client.set_lesson_editorial_status(lesson["id"], "approved")
        self.client.deliver_lessons(
            "standalone", "shared-delivery-key", lesson_ids=[lesson["id"]]
        )
        with self.assertRaisesRegex(ValueError, "andere Anfrage"):
            self.client.start_session(
                task="SessionStart",
                lesson_ids=[lesson["id"]],
                lesson_session_key="standalone",
                delivery_key="shared-delivery-key",
            )
        conn = sqlite3.connect(self.db_path)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM usmc_sessions").fetchone()[0], 0)
        self.assertEqual(
            conn.execute(
                "SELECT COUNT(*) FROM usmc_lesson_deliveries "
                "WHERE delivery_key = 'shared-delivery-key'"
            ).fetchone()[0],
            1,
        )
        conn.close()
        self.assertEqual(self.client.get_lesson(lesson["id"])["times_shown"], 1)

    def test_high_level_api_exposes_contract_without_changing_old_call(self):
        api.init(self.db_path, "api")
        old = api.lesson("Alt", "P", "S")
        new = api.lesson(
            "Neu", "P", "S", source_key="api", episode_key="1",
            event_anchor="event", evidence_class="verified",
        )
        api.lesson_review(new["id"], "approved")
        delivered = api.deliver_lessons(
            "session", "delivery-api", lesson_ids=[new["id"]]
        )
        feedback = api.lesson_feedback(
            new["id"], "feedback-api", helpful=True,
            delivery_key="delivery-api",
        )
        self.assertFalse(old["upserted"])
        self.assertTrue(new["upserted"])
        self.assertEqual(len(delivered), 1)
        self.assertEqual(feedback["helpful_count"], 1)
        self.assertFalse(api.lesson_promotion(new["id"])["allowed"])


if __name__ == "__main__":
    unittest.main()
