# -*- coding: utf-8 -*-
"""Vereinigungsschema BACH = OCEAN (S1): nur Temp-DBs, nie ~/.usmc."""

import hashlib
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from usmc import memory_union as mu
from usmc import schema
from usmc.client import USMCClient

# Gleicher Wert steht im BACH-Test (vendorte Kopie muss byte-identisch sein).
CONTRACT_SHA256 = "d3b5d051924cd19b18c6e891b462d2cbfc46fd69e21feccd9e5439b348f0d851"

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


def _names(conn, kind):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = ?", (kind,))}


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
        self.assertEqual(copied, {"usmc_facts": 2, "usmc_working": 2, "usmc_lessons": 1, "usmc_sessions": 2})
        self.assertTrue(mu.is_union(conn))
        self.assertEqual(
            _names(conn, "view"), {"usmc_facts", "usmc_working", "usmc_lessons", "usmc_sessions"}
        )
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
        self.assertEqual(mu.describe_schema(conn), mu.load_contract()["schema"])

    def test_history_keeps_null_provenance(self):
        conn = _v1_db()
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
        conn.execute("ALTER TABLE usmc_lessons ADD COLUMN source_key TEXT")
        conn.commit()
        with self.assertRaises(mu.UnionMigrationError) as ctx:
            mu.apply_union(conn)
        self.assertIn("source_key", str(ctx.exception))
        self._assert_unchanged(conn)

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


if __name__ == "__main__":
    unittest.main()
