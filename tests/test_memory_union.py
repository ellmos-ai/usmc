# -*- coding: utf-8 -*-
"""Vereinigungsschema BACH = OCEAN (S1, Vertrag v2 aus S2): nur Temp-DBs, nie ~/.usmc."""

import hashlib
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from usmc import memory_union as mu
from usmc import schema
from usmc.client import USMCClient

# Gleicher Wert steht im BACH-Test (vendorte Kopie muss byte-identisch sein).
CONTRACT_SHA256 = "9eab5303103de3fbd2cdc8eb39e4d246dd50d19ded949764a88a952a75f06739"

V1_ROWS = """
INSERT INTO usmc_sessions (id, agent_id, started_at, ended_at, current_task, handoff_notes)
VALUES (7, 'claude-code', '2026-09-01T10:00', NULL, 'offen', NULL),
       (8, 'codex', '2026-09-01T09:00', '2026-09-01T09:30', 'fertig', 'RESUME: x');
INSERT INTO usmc_facts (id, category, key, value, confidence, source, agent_id, created_at, updated_at)
VALUES (3, 'system', 'k', 'v', 0.9, 'agent:codex', 'codex', 't0', 't1'),
       (4, 'system', 'k', 'v2', 1.0, 'agent:claude-code', 'claude-code', 't0', 't1');
INSERT INTO usmc_working (id, type, content, priority, tags, agent_id, is_active, created_at, updated_at)
VALUES (11, 'handoff', 'uebergabe', 1, 'a,b', 'claude-code', 1, 't0', 't1'),
       (12, 'note', 'notiz', 0, NULL, 'codex', 0, 't0', 't1');
INSERT INTO usmc_lessons (id, category, severity, title, problem, solution, agent_id,
                          is_active, confidence, times_shown, created_at, updated_at)
VALUES (21, 'general', 'high', 'T', 'P', 'S', 'codex', 1, 0.5, 2, 't0', 't1');
"""


def _v1_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    schema.init_db(conn)
    conn.executescript(V1_ROWS)
    conn.commit()
    return conn


def _v1_db_with_fresh_provenance_session() -> sqlite3.Connection:
    conn = _v1_db()
    conn.execute(
        "UPDATE usmc_sessions SET started_at = datetime('now', '-1 minute') WHERE id = 7"
    )
    conn.commit()
    return conn


def _union_v1_state(conn: sqlite3.Connection) -> None:
    """Zustand nach Vertrag v1: memory_lessons ohne v2-Spalten, usmc_lessons
    samt Nebentabellen noch real, usmc_meta.memory_union = 1."""
    v2 = set(mu._LESSON_V2_COLUMN_NAMES)
    ddl = mu.TABLE_DDL["memory_lessons"]
    lines = [line for line in ddl.splitlines() if line.strip().split(" ")[0] not in v2]
    conn.execute("\n".join(lines).replace("visibility TEXT,", "visibility TEXT"))
    for table in ("memory_sessions", "memory_working", "memory_facts"):
        conn.execute(mu.TABLE_DDL[table])
    conn.execute("CREATE TABLE IF NOT EXISTS usmc_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT OR REPLACE INTO usmc_meta VALUES ('memory_union', '1')")
    conn.commit()


def _names(conn, kind):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = ?", (kind,))}


def _provenance_db(*sessions) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    mu.create_union_schema(conn)
    for session_id, key, started_modifier, agent_id in sessions:
        conn.execute(
            """INSERT INTO memory_sessions (id, session_id, started_at, agent_id)
               VALUES (?, ?, datetime('now', ?), ?)""",
            (session_id, key, started_modifier, agent_id),
        )
    conn.commit()
    return conn


def _insert_working_and_read_provenance(conn: sqlite3.Connection, agent_id: str):
    conn.execute(
        "INSERT INTO memory_working (type, content, agent_id) VALUES ('note', ?, ?)",
        (f"note-{agent_id}", agent_id),
    )
    return conn.execute(
        "SELECT created_by_session_id, updated_by_session_id "
        "FROM memory_working WHERE content = ?",
        (f"note-{agent_id}",),
    ).fetchone()


class TestContract(unittest.TestCase):
    def test_fresh_schema_matches_contract(self):
        conn = sqlite3.connect(":memory:")
        mu.create_union_schema(conn)
        self.assertEqual(mu.describe_schema(conn), mu.load_contract()["schema"])

    def test_contract_bytes_pinned(self):
        # CRLF-normalisiert, damit ein autocrlf-Checkout den Pin nicht bricht.
        raw = mu.CONTRACT_PATH.read_bytes().replace(b"\r\n", b"\n")
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(digest, CONTRACT_SHA256)

    def test_working_types_cover_bach_and_usmc(self):
        for kind in ("scratchpad", "context", "loop", "note", "handoff", "task"):
            self.assertIn(kind, mu.WORKING_TYPES)
        self.assertTrue(set(USMCClient.VALID_WORKING_TYPES) <= set(mu.WORKING_TYPES))


class TestApplyUnion(unittest.TestCase):
    def test_v1_rows_move_with_ids_and_compat_views(self):
        conn = _v1_db()
        copied = mu.apply_union(conn)
        self.assertEqual(copied, {
            "usmc_facts": 2, "usmc_working": 2, "usmc_lessons": 1, "usmc_sessions": 2,
            "usmc_lesson_feedback": 0, "usmc_lesson_delivery_batches": 0,
            "usmc_lesson_deliveries": 0,
        })
        self.assertEqual(mu.union_version(conn), mu.UNION_VERSION)
        self.assertEqual(
            _names(conn, "view"), {"usmc_facts", "usmc_working", "usmc_lessons", "usmc_sessions"}
        )
        self.assertFalse({n for n in _names(conn, "table") if n.startswith("usmc_lesson")})
        self.assertEqual(
            conn.execute("SELECT agent_id, value FROM usmc_facts WHERE id = 4").fetchone(),
            ("claude-code", "v2"),
        )
        self.assertEqual(
            conn.execute("SELECT session_id, handoff_notes FROM memory_sessions WHERE id = 8").fetchone(),
            ("usmc-8", "RESUME: x"),
        )
        self.assertEqual(
            conn.execute("SELECT type FROM usmc_working WHERE id = 11").fetchone(), ("handoff",)
        )
        self.assertEqual(
            conn.execute("SELECT title, source_kind FROM memory_lessons WHERE id = 21").fetchone(),
            ("T", "legacy"),
        )
        self.assertEqual(mu.describe_schema(conn), mu.load_contract()["schema"])

    def test_history_keeps_null_provenance(self):
        conn = _v1_db_with_fresh_provenance_session()
        mu.apply_union(conn)
        stamped = conn.execute(
            "SELECT COUNT(*) FROM memory_working WHERE created_by_session_id IS NOT NULL"
        ).fetchone()[0]
        self.assertEqual(stamped, 0)
        conn.execute(
            "INSERT INTO memory_working (type, content, agent_id) VALUES ('note', 'neu', 'claude-code')"
        )
        self.assertEqual(
            conn.execute(
                "SELECT created_by_session_id FROM memory_working WHERE content = 'neu'"
            ).fetchone(),
            ("usmc-7",),
        )

    def test_idempotent(self):
        conn = _v1_db()
        mu.apply_union(conn)
        self.assertEqual(mu.apply_union(conn), {})

    def _assert_unchanged(self, conn):
        self.assertFalse(mu.is_union(conn))
        self.assertEqual(_names(conn, "view"), set())
        self.assertFalse({n for n in _names(conn, "table") if n.startswith("memory_")})
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM usmc_working").fetchone()[0], 2)

    def test_unmapped_columns_abort_without_mutation(self):
        conn = _v1_db()
        conn.execute("ALTER TABLE usmc_facts ADD COLUMN mystery_field TEXT")
        conn.commit()
        with self.assertRaises(mu.UnionMigrationError) as ctx:
            mu.apply_union(conn)
        self.assertIn("mystery_field", str(ctx.exception))
        self._assert_unchanged(conn)

    def test_lesson_v2_rows_and_side_tables_move_with_ids(self):
        conn = _v1_db()
        conn.executescript("""
UPDATE usmc_lessons SET source_key = 'src', episode_key = 'ep', editorial_status = 'approved',
       helpful_count = 1 WHERE id = 21;
INSERT INTO usmc_lesson_delivery_batches VALUES ('d-1', 7, 'sess', 'explicit', 'h', 'codex', 't0');
INSERT INTO usmc_lesson_deliveries (id, lesson_id, delivery_key, session_key, delivery_mode,
    context, feedback_prompt, payload_hash, agent_id, created_at)
VALUES (5, 21, 'd-1', 'sess', 'explicit', NULL, 'hilfreich?', 'h', 'codex', 't0');
INSERT INTO usmc_lesson_feedback (id, lesson_id, feedback_key, helpful, payload_hash, agent_id, created_at)
VALUES (9, 21, 'f-1', 1, 'h', 'codex', 't0');
""")
        copied = mu.apply_union(conn)
        self.assertEqual(
            (copied["usmc_lesson_feedback"], copied["usmc_lesson_delivery_batches"],
             copied["usmc_lesson_deliveries"]), (1, 1, 1),
        )
        self.assertEqual(
            conn.execute(
                "SELECT source_key, episode_key, editorial_status, helpful_count "
                "FROM memory_lessons WHERE id = 21"
            ).fetchone(),
            ("src", "ep", "approved", 1),
        )
        self.assertEqual(conn.execute("SELECT lesson_id FROM memory_lesson_feedback WHERE id = 9").fetchone(), (21,))
        self.assertEqual(conn.execute("SELECT lesson_id FROM memory_lesson_deliveries WHERE id = 5").fetchone(), (21,))
        self.assertEqual(
            conn.execute("SELECT session_id FROM memory_lesson_delivery_batches").fetchone(), (7,)
        )
        self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_union_v1_database_is_upgraded_to_current_contract(self):
        conn = _v1_db()
        _union_v1_state(conn)
        copied = mu.apply_union(conn)
        self.assertEqual(copied["usmc_lessons"], 1)
        self.assertEqual(mu.union_version(conn), mu.UNION_VERSION)
        self.assertEqual(mu.describe_schema(conn), mu.load_contract()["schema"])
        self.assertEqual(
            conn.execute("SELECT title FROM memory_lessons WHERE id = 21").fetchone(), ("T",)
        )

    def test_rows_on_both_sides_abort_without_mutation(self):
        conn = _v1_db()
        _union_v1_state(conn)
        conn.execute(
            "INSERT INTO memory_lessons (id, category, title, solution) VALUES (99, 'g', 'X', 'Y')"
        )
        conn.commit()
        with self.assertRaises(mu.UnionMigrationError) as ctx:
            mu.apply_union(conn)
        self.assertIn("target-not-empty memory_lessons", str(ctx.exception))
        self.assertEqual(mu.union_version(conn), 1)
        self.assertEqual(mu._object_type(conn, "usmc_lessons"), "table")

    def test_lesson_v2_column_list_matches_usmc_schema(self):
        # Das Modul ist fuer BACH eigenstaendig; die Spaltenliste darf nicht driften.
        self.assertEqual(
            tuple(mu._LESSON_V2_COLUMN_NAMES), tuple(name for name, _ in schema.LESSON_V2_COLUMNS)
        )
        union = {r[1]: (r[2], r[3], r[4]) for r in _pragma(mu.TABLE_DDL["memory_lessons"], "memory_lessons")}
        legacy = {r[1]: (r[2], r[3], r[4]) for r in _pragma(schema.SCHEMA_SQL, "usmc_lessons")}
        for name in mu._LESSON_V2_COLUMN_NAMES:
            self.assertEqual(union[name], legacy[name], name)

    def test_constraint_violation_rolls_back_everything(self):
        conn = _v1_db()
        conn.execute("UPDATE usmc_facts SET category = 'unbekannt' WHERE id = 3")
        conn.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            mu.apply_union(conn)
        self._assert_unchanged(conn)

    def test_open_transaction_is_refused(self):
        conn = _v1_db()
        conn.execute("BEGIN")
        with self.assertRaises(mu.UnionMigrationError):
            mu.apply_union(conn)


class TestProvenanceTriggers(unittest.TestCase):
    def test_fresh_open_session_stamps_new_row(self):
        conn = _provenance_db((1, "fresh-session", "-1 minute", "agent-a"))
        self.addCleanup(conn.close)

        self.assertEqual(
            _insert_working_and_read_provenance(conn, "agent-a"),
            ("fresh-session", "fresh-session"),
        )

    def test_stale_open_session_leaves_new_row_unstamped(self):
        conn = _provenance_db((1, "stale-session", "-48 hours", "agent-a"))
        self.addCleanup(conn.close)

        self.assertEqual(_insert_working_and_read_provenance(conn, "agent-a"), (None, None))

    def test_iso_t_format_fixture_at_cutoff_is_correctly_treated_as_stale(self):
        # Reproduziert den Bug aus dem Review von usmc#11: eine mit der echten
        # Anwendungs-Schreibweise (datetime.now().isoformat(), lokale Zeit, "T"-
        # Separator) erzeugte Session, die etwas mehr als _SESSION_STALENESS_HOURS
        # alt ist, MUSS als stale gelten (NULL-Provenienz). Vor dem Fix vergleicht
        # der Trigger diesen Zeitstempel als reinen Text gegen SQLites UTC-
        # datetime('now', ...) mit Leerzeichen-Separator -- "T" > " " plus ein
        # moeglicher UTC/Lokalzeit-Versatz lassen die Session faelschlich frisch
        # erscheinen (reales Fenster bis zu ~48h statt 24h). Dieser Test ist ohne
        # den Fix ROT.
        stale_started_at = (
            datetime.now() - timedelta(hours=mu._SESSION_STALENESS_HOURS + 6)
        ).isoformat()
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        mu.create_union_schema(conn)
        conn.execute(
            "INSERT INTO memory_sessions (id, session_id, started_at, agent_id) "
            "VALUES (1, 'iso-t-stale', ?, 'agent-a')",
            (stale_started_at,),
        )
        conn.commit()

        conn.execute(
            "INSERT INTO memory_working (type, content, agent_id) "
            "VALUES ('note', 'iso-t-check', 'agent-a')"
        )
        row = conn.execute(
            "SELECT created_by_session_id FROM memory_working WHERE content = 'iso-t-check'"
        ).fetchone()
        self.assertEqual(row, (None,))

    def test_fresh_matching_agent_wins_over_younger_other_agent(self):
        conn = _provenance_db(
            (1, "younger-other", "-1 minute", "agent-other"),
            (2, "older-match", "-10 minutes", "agent-target"),
        )
        self.addCleanup(conn.close)

        self.assertEqual(
            _insert_working_and_read_provenance(conn, "agent-target"),
            ("older-match", "older-match"),
        )

    def test_fresh_other_agent_wins_over_stale_matching_agent(self):
        conn = _provenance_db(
            (1, "fresh-other", "-1 minute", "agent-other"),
            (2, "stale-match", "-48 hours", "agent-target"),
        )
        self.addCleanup(conn.close)

        self.assertEqual(
            _insert_working_and_read_provenance(conn, "agent-target"),
            ("fresh-other", "fresh-other"),
        )

    def test_install_provenance_triggers_is_idempotent(self):
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        mu.create_union_schema(conn, triggers=False)

        mu.install_provenance_triggers(conn)
        mu.install_provenance_triggers(conn)

        self.assertEqual(
            conn.execute(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE type = 'trigger' AND name LIKE 'trg_memory_%_session_provenance_%'"
            ).fetchone()[0],
            len(mu.PROVENANCE_TABLES) * 2,
        )


class TestClientUnionMode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "usmc_memory.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_stays_on_usmc_tables(self):
        with mock.patch.dict(os.environ, {"USMC_MEMORY_UNION": ""}):
            USMCClient(db_path=self.db).add_fact("system", "k", "v")
        conn = sqlite3.connect(self.db)
        self.assertIn("usmc_facts", _names(conn, "table"))
        self.assertNotIn("memory_facts", _names(conn, "table"))
        conn.close()

    def test_opt_in_backs_up_then_client_writes_union_tables(self):
        USMCClient(db_path=self.db, agent_id="codex").add_working("alt", type="note")
        with mock.patch.dict(os.environ, {"USMC_MEMORY_UNION": "1"}):
            client = USMCClient(db_path=self.db, agent_id="codex")
            client.add_fact("system", "k", "v", confidence=0.5)
            client.add_fact("system", "k", "v2", confidence=0.9)
            session = client.start_session("aufgabe")
            client.add_working("neu", type="context")
            client.add_lesson("T", "P", "S")
            self.assertTrue(client.end_session(session["id"], handoff_notes="RESUME: weiter"))
            status = client.get_status()
        backups = list(Path(self.tmp.name).glob("usmc_memory.db.pre-memory-union-*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((status["facts_count"], status["working_count"], status["sessions_count"]), (1, 2, 1))
        conn = sqlite3.connect(self.db)
        self.assertEqual(conn.execute("SELECT value FROM memory_facts").fetchone(), ("v2",))
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM memory_working").fetchone()[0], 2)
        row = conn.execute(
            "SELECT session_id, handoff_notes FROM memory_sessions WHERE id = ?", (session["id"],)
        ).fetchone()
        self.assertTrue(row[0].startswith("usmc-") and row[1] == "RESUME: weiter")
        conn.close()


class TestLessonV2InUnionMode(unittest.TestCase):
    """S2: Lesson-Schema v2 ist Teil des gemeinsamen Vertrags und laeuft im
    Union-Modus vollstaendig auf memory_lessons und den Nebentabellen."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "usmc_memory.db"
        with mock.patch.dict(os.environ, {"USMC_MEMORY_UNION": "1"}):
            self.client = USMCClient(db_path=self.db, agent_id="codex")

    def tearDown(self):
        self.tmp.cleanup()

    def _count(self, table):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        finally:
            conn.close()

    def test_keyed_lesson_feedback_and_delivery_use_union_tables(self):
        lesson = self.client.add_lesson("T", "P", "S", source_key="hook:codex", episode_key="ep-1")
        again = self.client.add_lesson("T", "P", "S", source_key="hook:codex", episode_key="ep-1")
        self.assertEqual((lesson["created"], again["created"], again["id"]), (True, False, lesson["id"]))
        self.client.set_lesson_editorial_status(lesson["id"], "approved")
        delivered = self.client.deliver_lessons("sess", "deliv-1", lesson_ids=[lesson["id"]])
        self.assertEqual([item["id"] for item in delivered], [lesson["id"]])
        feedback = self.client.record_lesson_feedback(
            lesson["id"], "fb-1", helpful=True, delivery_key="deliv-1"
        )
        self.assertEqual(feedback["helpful_count"], 1)
        self.assertEqual(
            [self._count(t) for t in ("memory_lessons", "memory_lesson_feedback",
                                      "memory_lesson_delivery_batches", "memory_lesson_deliveries")],
            [1, 1, 1, 1],
        )
        conn = sqlite3.connect(self.db)
        self.assertFalse({n for n in _names(conn, "table") if n.startswith("usmc_lesson")})
        conn.close()

    def test_session_start_delivery_creates_union_session(self):
        lesson = self.client.add_lesson("T", "P", "S", source_key="s", episode_key="e")
        self.client.set_lesson_editorial_status(lesson["id"], "approved")
        session = self.client.start_session(
            "aufgabe", lesson_ids=[lesson["id"]], delivery_key="deliv-2"
        )
        self.assertEqual([item["id"] for item in session["lessons"]], [lesson["id"]])
        conn = sqlite3.connect(self.db)
        key = conn.execute("SELECT session_id FROM memory_sessions WHERE id = ?", (session["id"],)).fetchone()
        conn.close()
        self.assertTrue(key[0].startswith("usmc-"))

    def test_reads_and_context_work(self):
        self.client.add_lesson("T", "P", "S")
        self.assertEqual([item["title"] for item in self.client.get_lessons()], ["T"])
        self.assertIsInstance(self.client.generate_context(), str)
        self.assertEqual(self.client.get_status()["lessons_count"], 1)

    def test_union_v1_file_is_upgraded_on_open_with_backup(self):
        tmp = Path(self.tmp.name) / "v1.db"
        conn = sqlite3.connect(tmp)
        schema.init_db(conn)
        conn.executescript(V1_ROWS)
        _union_v1_state(conn)
        conn.close()
        with mock.patch.dict(os.environ, {"USMC_MEMORY_UNION": ""}):
            client = USMCClient(db_path=tmp, agent_id="codex")
        self.assertEqual([item["id"] for item in client.get_lessons()], [21])
        self.assertEqual(len(list(Path(self.tmp.name).glob("v1.db.pre-memory-union-*.bak"))), 1)


def _pragma(ddl, table):
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(ddl)
        return conn.execute(f"PRAGMA table_info({table})").fetchall()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
