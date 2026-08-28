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
    UNIQUE(lesson_id, feedback_key),
    CHECK(helpful IS NULL OR helpful IN (0, 1)),
    FOREIGN KEY(lesson_id) REFERENCES usmc_lessons(id) ON DELETE CASCADE
);

-- Begrenzte, idempotente Zustellungen (kein Benachrichtigungs-Daemon)
CREATE TABLE IF NOT EXISTS usmc_lesson_delivery_batches (
    delivery_key TEXT PRIMARY KEY,
    session_key TEXT NOT NULL,
    delivery_mode TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL
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
CREATE INDEX IF NOT EXISTS idx_lesson_deliveries_lesson
    ON usmc_lesson_deliveries(lesson_id, created_at);
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
    UNIQUE(lesson_id, feedback_key),
    CHECK(helpful IS NULL OR helpful IN (0, 1)),
    FOREIGN KEY(lesson_id) REFERENCES usmc_lessons(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS usmc_lesson_delivery_batches (
    delivery_key TEXT PRIMARY KEY,
    session_key TEXT NOT NULL,
    delivery_mode TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL
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
CREATE INDEX IF NOT EXISTS idx_lesson_deliveries_lesson
    ON usmc_lesson_deliveries(lesson_id, created_at);
"""


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


def migrate(conn: sqlite3.Connection) -> None:
    """Fuehrt ggf. Schema-Migration durch."""
    version = get_schema_version(conn)
    lessons_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'usmc_lessons'"
    ).fetchone()

    if version is None and not lessons_exists:
        init_db(conn)
        return

    # Eine alte DB ohne usmc_meta ist als v1 zu behandeln. Das verhindert,
    # dass CREATE TABLE IF NOT EXISTS faelschlich als vollstaendige Migration
    # gilt, obwohl additive Spalten fehlen.
    if version is None:
        version = 1
    if version > SCHEMA_VERSION:
        raise RuntimeError(
            f"DB-Schema {version} ist neuer als unterstuetztes Schema {SCHEMA_VERSION}"
        )

    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(usmc_lessons)").fetchall()
    }
    feedback_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' "
        "AND name = 'usmc_lesson_feedback'"
    ).fetchone()
    deliveries_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' "
        "AND name = 'usmc_lesson_deliveries'"
    ).fetchone()
    delivery_batches_exist = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' "
        "AND name = 'usmc_lesson_delivery_batches'"
    ).fetchone()
    missing_columns = [name for name, _ in LESSON_V2_COLUMNS if name not in columns]

    # Auch eine nach Teilfehler faelschlich auf v2 gesetzte DB wird repariert.
    if (
        version < 2
        or missing_columns
        or not feedback_exists
        or not deliveries_exists
        or not delivery_batches_exist
    ):
        _migrate_v1_to_v2(conn)


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Erweitert den Lesson-Vertrag atomar und wiederholbar auf Schema v2."""
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS usmc_meta "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(usmc_lessons)").fetchall()
        }
        for name, definition in LESSON_V2_COLUMNS:
            if name not in columns:
                conn.execute(
                    f"ALTER TABLE usmc_lessons ADD COLUMN {name} {definition}"
                )
        # ``executescript`` wuerde vorab implizit committen und damit die
        # ALTER-Schritte aus der Transaktion loesen. Einzelne execute-Aufrufe
        # halten Expand + Indizes + Version dagegen atomar zusammen.
        for statement in LESSON_V2_SQL.split(";"):
            if statement.strip():
                conn.execute(statement)
        conn.execute(
            "INSERT OR REPLACE INTO usmc_meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
