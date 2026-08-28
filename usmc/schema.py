# -*- coding: utf-8 -*-
"""
USMC Database Schema Definition + Migration
============================================

Eigene SQLite-DB (usmc_memory.db), unabhaengig von bach.db.
Tabellen: usmc_facts, usmc_working, usmc_lessons, usmc_sessions

Author: Lukas Geiger
License: MIT
"""

import sqlite3
from typing import Optional

from .lesson_contract import FEEDBACK_PROMPT, canonical_hash, lesson_ingest_hash

SCHEMA_VERSION = 2

SCHEMA_SQL = """
-- Facts: Persistente Fakten mit Konfidenz und Agent-Tracking
CREATE TABLE IF NOT EXISTS usmc_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source TEXT,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(agent_id, category, key)
);

-- Working Memory: Temporaere Notizen, Kontext, Scratchpad
CREATE TABLE IF NOT EXISTS usmc_working (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL DEFAULT 'note',
    content TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    tags TEXT,
    agent_id TEXT NOT NULL DEFAULT 'default',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Lessons Learned: Erfahrungen und Problemloesungen
CREATE TABLE IF NOT EXISTS usmc_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL DEFAULT 'general',
    severity TEXT NOT NULL DEFAULT 'medium',
    title TEXT NOT NULL,
    problem TEXT NOT NULL,
    solution TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    is_active INTEGER DEFAULT 1,
    confidence REAL DEFAULT 1.0,
    times_shown INTEGER DEFAULT 0,
    source_kind TEXT NOT NULL DEFAULT 'legacy',
    source_key TEXT,
    episode_key TEXT,
    source_hash TEXT,
    event_anchor TEXT,
    editorial_status TEXT NOT NULL DEFAULT 'legacy',
    evidence_class TEXT NOT NULL DEFAULT 'unknown',
    privacy_scope TEXT NOT NULL DEFAULT 'local',
    sensitive_source INTEGER NOT NULL DEFAULT 0,
    user_preference INTEGER NOT NULL DEFAULT 0,
    policy_relevant INTEGER NOT NULL DEFAULT 0,
    conflict_flag INTEGER NOT NULL DEFAULT 0,
    mutates_skill INTEGER NOT NULL DEFAULT 0,
    mutates_workflow INTEGER NOT NULL DEFAULT 0,
    ingest_payload_hash TEXT,
    helpful_count INTEGER NOT NULL DEFAULT 0,
    unhelpful_count INTEGER NOT NULL DEFAULT 0,
    independent_repeat_count INTEGER NOT NULL DEFAULT 0,
    delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    last_delivered_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Idempotente, getrennte Nutzungs-/Wiederholungs-/Zustellsignale
CREATE TABLE IF NOT EXISTS usmc_lesson_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    feedback_key TEXT NOT NULL,
    helpful INTEGER,
    independent_repeat INTEGER NOT NULL DEFAULT 0,
    delivery_failed INTEGER NOT NULL DEFAULT 0,
    delivery_key TEXT,
    event_anchor TEXT,
    payload_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    UNIQUE(feedback_key),
    CHECK(helpful IS NULL OR helpful IN (0, 1)),
    FOREIGN KEY(lesson_id) REFERENCES usmc_lessons(id) ON DELETE CASCADE
);

-- Begrenzte, idempotente Zustellungen (kein Benachrichtigungs-Daemon)
CREATE TABLE IF NOT EXISTS usmc_lesson_delivery_batches (
    delivery_key TEXT PRIMARY KEY,
    session_id INTEGER,
    session_key TEXT NOT NULL,
    delivery_mode TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES usmc_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS usmc_lesson_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    delivery_key TEXT NOT NULL,
    session_key TEXT NOT NULL,
    delivery_mode TEXT NOT NULL,
    context TEXT,
    feedback_prompt TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    UNIQUE(lesson_id, delivery_key),
    FOREIGN KEY(lesson_id) REFERENCES usmc_lessons(id) ON DELETE CASCADE
);

-- Sessions: Agent-Session-Tracking fuer Kontinuitaet
CREATE TABLE IF NOT EXISTS usmc_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    current_task TEXT,
    handoff_notes TEXT
);

-- Schema-Version tracking
CREATE TABLE IF NOT EXISTS usmc_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Indizes fuer Performance
CREATE INDEX IF NOT EXISTS idx_facts_category ON usmc_facts(category);
CREATE INDEX IF NOT EXISTS idx_facts_agent ON usmc_facts(agent_id);
CREATE INDEX IF NOT EXISTS idx_facts_updated ON usmc_facts(updated_at);
CREATE INDEX IF NOT EXISTS idx_working_active ON usmc_working(is_active);
CREATE INDEX IF NOT EXISTS idx_working_agent ON usmc_working(agent_id);
CREATE INDEX IF NOT EXISTS idx_lessons_active ON usmc_lessons(is_active);
CREATE INDEX IF NOT EXISTS idx_lessons_severity ON usmc_lessons(severity);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lessons_source_episode
    ON usmc_lessons(source_key, episode_key)
    WHERE source_key IS NOT NULL AND episode_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lessons_delivery_selection
    ON usmc_lessons(is_active, editorial_status, privacy_scope);
CREATE INDEX IF NOT EXISTS idx_lesson_feedback_lesson
    ON usmc_lesson_feedback(lesson_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lesson_feedback_key
    ON usmc_lesson_feedback(feedback_key);
CREATE INDEX IF NOT EXISTS idx_lesson_deliveries_lesson
    ON usmc_lesson_deliveries(lesson_id, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lesson_delivery_batches_key
    ON usmc_lesson_delivery_batches(delivery_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lesson_deliveries_lesson_key
    ON usmc_lesson_deliveries(lesson_id, delivery_key);
CREATE INDEX IF NOT EXISTS idx_lesson_deliveries_batch_order
    ON usmc_lesson_deliveries(delivery_key, id);
CREATE INDEX IF NOT EXISTS idx_sessions_agent ON usmc_sessions(agent_id);
"""


LESSON_V2_COLUMNS = (
    ("source_kind", "TEXT NOT NULL DEFAULT 'legacy'"),
    ("source_key", "TEXT"),
    ("episode_key", "TEXT"),
    ("source_hash", "TEXT"),
    ("event_anchor", "TEXT"),
    ("editorial_status", "TEXT NOT NULL DEFAULT 'legacy'"),
    ("evidence_class", "TEXT NOT NULL DEFAULT 'unknown'"),
    ("privacy_scope", "TEXT NOT NULL DEFAULT 'local'"),
    ("sensitive_source", "INTEGER NOT NULL DEFAULT 0"),
    ("user_preference", "INTEGER NOT NULL DEFAULT 0"),
    ("policy_relevant", "INTEGER NOT NULL DEFAULT 0"),
    ("conflict_flag", "INTEGER NOT NULL DEFAULT 0"),
    ("mutates_skill", "INTEGER NOT NULL DEFAULT 0"),
    ("mutates_workflow", "INTEGER NOT NULL DEFAULT 0"),
    ("ingest_payload_hash", "TEXT"),
    ("helpful_count", "INTEGER NOT NULL DEFAULT 0"),
    ("unhelpful_count", "INTEGER NOT NULL DEFAULT 0"),
    ("independent_repeat_count", "INTEGER NOT NULL DEFAULT 0"),
    ("delivery_failure_count", "INTEGER NOT NULL DEFAULT 0"),
    ("last_delivered_at", "TEXT"),
)


LESSON_V2_SQL = """
CREATE TABLE IF NOT EXISTS usmc_lesson_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    feedback_key TEXT NOT NULL,
    helpful INTEGER,
    independent_repeat INTEGER NOT NULL DEFAULT 0,
    delivery_failed INTEGER NOT NULL DEFAULT 0,
    delivery_key TEXT,
    event_anchor TEXT,
    payload_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    UNIQUE(feedback_key),
    CHECK(helpful IS NULL OR helpful IN (0, 1)),
    FOREIGN KEY(lesson_id) REFERENCES usmc_lessons(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS usmc_lesson_delivery_batches (
    delivery_key TEXT PRIMARY KEY,
    session_id INTEGER,
    session_key TEXT NOT NULL,
    delivery_mode TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES usmc_sessions(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS usmc_lesson_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    delivery_key TEXT NOT NULL,
    session_key TEXT NOT NULL,
    delivery_mode TEXT NOT NULL,
    context TEXT,
    feedback_prompt TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    UNIQUE(lesson_id, delivery_key),
    FOREIGN KEY(lesson_id) REFERENCES usmc_lessons(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lessons_source_episode
    ON usmc_lessons(source_key, episode_key)
    WHERE source_key IS NOT NULL AND episode_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lessons_delivery_selection
    ON usmc_lessons(is_active, editorial_status, privacy_scope);
CREATE INDEX IF NOT EXISTS idx_lesson_feedback_lesson
    ON usmc_lesson_feedback(lesson_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lesson_feedback_key
    ON usmc_lesson_feedback(feedback_key);
CREATE INDEX IF NOT EXISTS idx_lesson_deliveries_lesson
    ON usmc_lesson_deliveries(lesson_id, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lesson_delivery_batches_key
    ON usmc_lesson_delivery_batches(delivery_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lesson_deliveries_lesson_key
    ON usmc_lesson_deliveries(lesson_id, delivery_key);
CREATE INDEX IF NOT EXISTS idx_lesson_deliveries_batch_order
    ON usmc_lesson_deliveries(delivery_key, id);
"""


V2_TABLE_COLUMNS = {
    "usmc_lesson_feedback": (
        ("id", None),
        ("lesson_id", "INTEGER"),
        ("feedback_key", "TEXT"),
        ("helpful", "INTEGER"),
        ("independent_repeat", "INTEGER NOT NULL DEFAULT 0"),
        ("delivery_failed", "INTEGER NOT NULL DEFAULT 0"),
        ("delivery_key", "TEXT"),
        ("event_anchor", "TEXT"),
        ("payload_hash", "TEXT"),
        ("agent_id", "TEXT NOT NULL DEFAULT 'default'"),
        ("created_at", "TEXT NOT NULL DEFAULT ''"),
    ),
    "usmc_lesson_delivery_batches": (
        ("delivery_key", "TEXT"),
        ("session_id", "INTEGER"),
        ("session_key", "TEXT"),
        ("delivery_mode", "TEXT"),
        ("request_hash", "TEXT"),
        ("agent_id", "TEXT NOT NULL DEFAULT 'default'"),
        ("created_at", "TEXT NOT NULL DEFAULT ''"),
    ),
    "usmc_lesson_deliveries": (
        ("id", None),
        ("lesson_id", "INTEGER"),
        ("delivery_key", "TEXT"),
        ("session_key", "TEXT"),
        ("delivery_mode", "TEXT"),
        ("context", "TEXT"),
        ("feedback_prompt", f"TEXT NOT NULL DEFAULT '{FEEDBACK_PROMPT}'"),
        ("payload_hash", "TEXT"),
        ("agent_id", "TEXT NOT NULL DEFAULT 'default'"),
        ("created_at", "TEXT NOT NULL DEFAULT ''"),
    ),
}


REQUIRED_V2_INDEXES = (
    (
        "usmc_lessons", "idx_lessons_source_episode", True,
        ("source_key", "episode_key"), True,
        "CREATE UNIQUE INDEX idx_lessons_source_episode "
        "ON usmc_lessons(source_key, episode_key) "
        "WHERE source_key IS NOT NULL AND episode_key IS NOT NULL",
    ),
    (
        "usmc_lessons", "idx_lessons_delivery_selection", False,
        ("is_active", "editorial_status", "privacy_scope"), False,
        "CREATE INDEX idx_lessons_delivery_selection "
        "ON usmc_lessons(is_active, editorial_status, privacy_scope)",
    ),
    (
        "usmc_lesson_feedback", "idx_lesson_feedback_lesson", False,
        ("lesson_id",), False,
        "CREATE INDEX idx_lesson_feedback_lesson "
        "ON usmc_lesson_feedback(lesson_id)",
    ),
    (
        "usmc_lesson_feedback", "idx_lesson_feedback_key", True,
        ("feedback_key",), False,
        "CREATE UNIQUE INDEX idx_lesson_feedback_key "
        "ON usmc_lesson_feedback(feedback_key)",
    ),
    (
        "usmc_lesson_delivery_batches", "idx_lesson_delivery_batches_key", True,
        ("delivery_key",), False,
        "CREATE UNIQUE INDEX idx_lesson_delivery_batches_key "
        "ON usmc_lesson_delivery_batches(delivery_key)",
    ),
    (
        "usmc_lesson_deliveries", "idx_lesson_deliveries_lesson", False,
        ("lesson_id", "created_at"), False,
        "CREATE INDEX idx_lesson_deliveries_lesson "
        "ON usmc_lesson_deliveries(lesson_id, created_at)",
    ),
    (
        "usmc_lesson_deliveries", "idx_lesson_deliveries_lesson_key", True,
        ("lesson_id", "delivery_key"), False,
        "CREATE UNIQUE INDEX idx_lesson_deliveries_lesson_key "
        "ON usmc_lesson_deliveries(lesson_id, delivery_key)",
    ),
    (
        "usmc_lesson_deliveries", "idx_lesson_deliveries_batch_order", False,
        ("delivery_key", "id"), False,
        "CREATE INDEX idx_lesson_deliveries_batch_order "
        "ON usmc_lesson_deliveries(delivery_key, id)",
    ),
)


def init_db(conn: sqlite3.Connection) -> None:
    """Erstellt alle Tabellen und setzt Schema-Version."""
    try:
        conn.executescript("BEGIN IMMEDIATE;\n" + SCHEMA_SQL)
        conn.execute(
            "INSERT OR REPLACE INTO usmc_meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_schema_version(conn: sqlite3.Connection) -> Optional[int]:
    """Liest aktuelle Schema-Version aus der DB."""
    try:
        row = conn.execute(
            "SELECT value FROM usmc_meta WHERE key = 'schema_version'"
        ).fetchone()
        return int(row[0]) if row else None
    except sqlite3.OperationalError:
        return None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _index_state(conn: sqlite3.Connection, table: str, index: str):
    row = next(
        (item for item in conn.execute(f"PRAGMA index_list({table})") if item[1] == index),
        None,
    )
    if row is None:
        return None
    columns = tuple(
        item[2] for item in conn.execute(f"PRAGMA index_info({index})").fetchall()
    )
    return bool(row[2]), columns, bool(row[4])


def _v2_repair_needed(conn: sqlite3.Connection) -> bool:
    lesson_columns = _table_columns(conn, "usmc_lessons")
    if any(name not in lesson_columns for name, _ in LESSON_V2_COLUMNS):
        return True
    for table, required in V2_TABLE_COLUMNS.items():
        if not _table_exists(conn, table):
            return True
        columns = _table_columns(conn, table)
        if any(name not in columns for name, _ in required):
            return True
    for table, index, unique, columns, partial, _ in REQUIRED_V2_INDEXES:
        if _index_state(conn, table, index) != (unique, columns, partial):
            return True
    if conn.execute(
        "SELECT 1 FROM usmc_lessons WHERE source_key IS NOT NULL "
        "AND episode_key IS NOT NULL AND ingest_payload_hash IS NULL LIMIT 1"
    ).fetchone():
        return True
    if conn.execute(
        "SELECT 1 FROM usmc_lesson_feedback WHERE payload_hash IS NULL LIMIT 1"
    ).fetchone():
        return True
    if conn.execute(
        "SELECT 1 FROM usmc_lesson_deliveries WHERE payload_hash IS NULL LIMIT 1"
    ).fetchone():
        return True
    return False


def migrate(conn: sqlite3.Connection) -> None:
    """Prüft und repariert alle additiven v2-Invarianten transaktional."""
    version = get_schema_version(conn)
    lessons_exists = _table_exists(conn, "usmc_lessons")

    if version is None and not lessons_exists:
        init_db(conn)
        return
    if version is None:
        version = 1
    if version > SCHEMA_VERSION:
        raise RuntimeError(
            f"DB-Schema {version} ist neuer als unterstütztes Schema {SCHEMA_VERSION}"
        )
    if version < SCHEMA_VERSION or _v2_repair_needed(conn):
        _migrate_v1_to_v2(conn)


def _ensure_table_columns(
    conn: sqlite3.Connection, table: str, definitions
) -> None:
    columns = _table_columns(conn, table)
    for name, definition in definitions:
        if name in columns:
            continue
        if definition is None:
            raise RuntimeError(
                f"Partielles v2-Schema kann Pflichtspalte {table}.{name} "
                "nicht additiv rekonstruieren"
            )
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def _require_complete_rows(
    conn: sqlite3.Connection, table: str, columns
) -> None:
    for column in columns:
        if conn.execute(
            f"SELECT 1 FROM {table} WHERE {column} IS NULL LIMIT 1"
        ).fetchone():
            raise RuntimeError(
                f"Partielles v2-Schema enthält nicht rekonstruierbare Werte in "
                f"{table}.{column}"
            )


def _reject_duplicates(
    conn: sqlite3.Connection, table: str, columns, label: str,
    where: Optional[str] = None,
) -> None:
    grouped = ", ".join(columns)
    where_sql = f"WHERE {where} " if where else ""
    row = conn.execute(
        f"SELECT {grouped}, COUNT(*) FROM {table} "
        f"{where_sql}"
        f"GROUP BY {grouped} HAVING COUNT(*) > 1 LIMIT 1"
    ).fetchone()
    if row:
        key = ", ".join(repr(item) for item in row[:-1])
        raise RuntimeError(f"{label}: doppelter Schlüssel {key}")


def _backfill_lesson_payload_hashes(conn: sqlite3.Connection) -> None:
    fields = (
        "category", "severity", "title", "problem", "solution", "source_kind",
        "source_key", "episode_key", "source_hash", "event_anchor",
        "editorial_status", "evidence_class", "privacy_scope", "confidence",
        "sensitive_source", "user_preference", "policy_relevant", "conflict_flag",
        "mutates_skill", "mutates_workflow",
    )
    rows = conn.execute(
        f"SELECT id, {', '.join(fields)} FROM usmc_lessons "
        "WHERE source_key IS NOT NULL AND episode_key IS NOT NULL "
        "AND ingest_payload_hash IS NULL"
    ).fetchall()
    for row in rows:
        payload = dict(zip(fields, row[1:]))
        conn.execute(
            "UPDATE usmc_lessons SET ingest_payload_hash = ? WHERE id = ?",
            (lesson_ingest_hash(payload), row[0]),
        )


def _backfill_feedback_payload_hashes(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id, lesson_id, feedback_key, helpful, independent_repeat, "
        "delivery_failed, delivery_key, event_anchor FROM usmc_lesson_feedback "
        "WHERE payload_hash IS NULL"
    ).fetchall()
    for row in rows:
        payload = {
            "lesson_id": row[1],
            "feedback_key": row[2],
            "helpful": None if row[3] is None else bool(row[3]),
            "independent_repeat": bool(row[4]),
            "delivery_failed": bool(row[5]),
            "delivery_key": row[6],
            "event_anchor": row[7],
        }
        conn.execute(
            "UPDATE usmc_lesson_feedback SET payload_hash = ? WHERE id = ?",
            (canonical_hash(payload), row[0]),
        )


def _backfill_delivery_payload_hashes(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id, lesson_id, delivery_key, session_key, delivery_mode, context "
        "FROM usmc_lesson_deliveries WHERE payload_hash IS NULL"
    ).fetchall()
    for row in rows:
        payload = {
            "lesson_id": row[1],
            "delivery_key": row[2],
            "session_key": row[3],
            "mode": row[4],
            "context": row[5],
        }
        conn.execute(
            "UPDATE usmc_lesson_deliveries SET payload_hash = ? WHERE id = ?",
            (canonical_hash(payload), row[0]),
        )


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Erweitert und repariert den Lesson-Vertrag atomar auf Schema v2."""
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS usmc_meta "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        _ensure_table_columns(conn, "usmc_lessons", LESSON_V2_COLUMNS)

        # CREATE TABLE wird einzeln ausgeführt: executescript würde die
        # umschließende Migrationstransaktion implizit committen.
        for statement in LESSON_V2_SQL.split(";")[:3]:
            if statement.strip():
                conn.execute(statement)
        for table, definitions in V2_TABLE_COLUMNS.items():
            _ensure_table_columns(conn, table, definitions)

        _require_complete_rows(
            conn, "usmc_lesson_feedback", ("lesson_id", "feedback_key")
        )
        _require_complete_rows(
            conn, "usmc_lesson_delivery_batches",
            ("delivery_key", "session_key", "delivery_mode", "request_hash"),
        )
        _require_complete_rows(
            conn, "usmc_lesson_deliveries",
            ("lesson_id", "delivery_key", "session_key", "delivery_mode"),
        )
        _backfill_lesson_payload_hashes(conn)
        _backfill_feedback_payload_hashes(conn)
        _backfill_delivery_payload_hashes(conn)

        _reject_duplicates(
            conn, "usmc_lessons", ("source_key", "episode_key"),
            "Lesson-Idempotenzmigration fehlgeschlagen",
            "source_key IS NOT NULL AND episode_key IS NOT NULL",
        )
        _reject_duplicates(
            conn, "usmc_lesson_feedback", ("feedback_key",),
            "Feedback-Idempotenzmigration fehlgeschlagen",
        )
        _reject_duplicates(
            conn, "usmc_lesson_delivery_batches", ("delivery_key",),
            "Delivery-Batch-Migration fehlgeschlagen",
        )
        _reject_duplicates(
            conn, "usmc_lesson_deliveries", ("lesson_id", "delivery_key"),
            "Delivery-Migration fehlgeschlagen",
        )

        for table, index, unique, columns, partial, sql in REQUIRED_V2_INDEXES:
            state = _index_state(conn, table, index)
            if state is None:
                conn.execute(sql)
            elif state != (unique, columns, partial):
                raise RuntimeError(
                    f"v2-Index {index} besitzt eine unerwartete Definition"
                )
        conn.execute(
            "INSERT OR REPLACE INTO usmc_meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
