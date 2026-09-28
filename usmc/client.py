# -*- coding: utf-8 -*-
"""
USMCClient - United Shared Memory Client
=========================================

Standalone cross-agent memory sharing with dedicated SQLite DB.
No dependency or access to bach.db -- fully independent.
Human-readable context prompt output deliberately remains German
for backwards compatibility; see ``usmc.RUNTIME_LANGUAGE``.

Methods:
    add_fact(), get_facts(), add_lesson(), get_lessons(),
    add_working(), get_working(), start_session(), end_session(),
    generate_context(), get_changes_since()

Author: Lukas Geiger
License: MIT
"""

import os
import sqlite3
import re
from pathlib import Path
from typing import Optional, List, Dict, Iterable
from datetime import datetime

from . import memory_union, schema
from .lesson_contract import (
    FEEDBACK_PROMPT,
    LESSON_INGEST_HASH_VERSION,
    MAX_SESSION_LESSONS,
    NEW_LESSON_INITIAL_WEIGHT,
    VALID_EDITORIAL_STATUSES,
    canonical_hash,
    direct_promotion_policy,
    lesson_ingest_hash,
    lesson_weight,
    validate_lesson_contract,
)


_LESSON_FIELDS = (
    "id", "category", "severity", "title", "problem", "solution",
    "agent_id", "is_active", "confidence", "times_shown", "source_kind",
    "source_key", "episode_key", "source_hash", "event_anchor",
    "editorial_status", "evidence_class", "privacy_scope",
    "sensitive_source", "user_preference", "policy_relevant", "conflict_flag",
    "mutates_skill", "mutates_workflow", "ingest_payload_hash",
    "ingest_payload_hash_version",
    "helpful_count", "unhelpful_count",
    "independent_repeat_count", "delivery_failure_count", "last_delivered_at",
    "created_at", "updated_at",
)
_LESSON_SELECT = ", ".join(_LESSON_FIELDS)


def _lesson_dict(row) -> Dict:
    result = dict(zip(_LESSON_FIELDS, row))
    result["weight"] = lesson_weight(result)
    return result


def _assert_keyed_lesson_integrity(lesson: Dict) -> None:
    """Fail closed when a keyed v2 row no longer matches its immutable hash."""
    keyed = lesson.get("source_key") is not None or lesson.get("episode_key") is not None
    if not keyed:
        return
    if not lesson.get("source_key") or not lesson.get("episode_key"):
        raise RuntimeError(
            f"Lesson {lesson.get('id')} besitzt einen unvollständigen Idempotenzschlüssel"
        )
    if lesson.get("ingest_payload_hash_version") != LESSON_INGEST_HASH_VERSION:
        raise RuntimeError(
            f"Lesson {lesson.get('id')} besitzt keine gültige Intake-Hashversion"
        )
    stored_hash = lesson.get("ingest_payload_hash")
    if not stored_hash or lesson_ingest_hash(lesson) != stored_hash:
        raise RuntimeError(
            f"Lesson {lesson.get('id')} verletzt die unveränderliche Zeilenintegrität"
        )


def _like_escape(value: str) -> str:
    """Escapes LIKE wildcards so a search term is matched literally.

    Without escaping, '%' and '_' in search terms act as wildcards where
    '_' matches any single character. Queries using this helper set
    ``ESCAPE '\\'``.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _split_tags(tags) -> List[str]:
    """Normalizes tag specification into a list of strings.

    Accepts 'a,b', 'a, b', or ['a', 'b']; empty parts are discarded.
    """
    if tags is None:
        return []
    raw = tags.split(",") if isinstance(tags, str) else list(tags)
    return [str(t).strip() for t in raw if str(t).strip()]


def default_db_path() -> str:
    """Per-system local default DB path (NOT cwd/OneDrive).

    Default: ``~/.usmc/usmc_memory.db``; override via env ``USMC_DB``.
    Does NOT create directories on import -- the parent folder is created
    only upon connection by USMCClient (no import side-effects).
    """
    env = os.environ.get("USMC_DB")
    if env:
        return env
    return str(Path.home() / ".usmc" / "usmc_memory.db")


class USMCClient:
    """
    Cross-agent memory client with dedicated SQLite DB.

    Usage:
        client = USMCClient()  # ~/.usmc/usmc_memory.db (Override: Env USMC_DB)
        client.add_fact("system", "os", "Windows 11", confidence=0.95)
        client.add_working("Current task: implement USMC")
        facts = client.get_facts()
        context = client.generate_context()

    Multi-Agent:
        opus = USMCClient(agent_id="opus")
        sonnet = USMCClient(agent_id="sonnet")
        opus.add_fact("project", "framework", "FastAPI")
        changes = sonnet.get_changes_since("2026-02-28T00:00:00")
    """

    VALID_CATEGORIES = ('user', 'project', 'system', 'domain')
    VALID_SEVERITIES = ('critical', 'high', 'medium', 'low')
    VALID_WORKING_TYPES = ('note', 'context', 'scratchpad', 'loop')

    def __init__(
        self,
        db_path: str | Path | None = None,
        agent_id: str = "default"
    ):
        """
        Initializes the USMC Client.

        Args:
            db_path: Path to USMC database (created if non-existent).
                Default: ``default_db_path()`` — per-system local database at
                ``~/.usmc/usmc_memory.db``, override via env ``USMC_DB``.
            agent_id: Agent identifier for multi-agent tracking.
        """
        if db_path is None:
            db_path = default_db_path()
        self._is_memory = str(db_path) == ':memory:'
        self.db_path = db_path if self._is_memory else Path(db_path)
        self.agent_id = agent_id
        self._shared_conn = None  # Fuer :memory: DBs
        if not self._is_memory:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensures database and schema exist.

        With ``USMC_MEMORY_UNION=1``, the DB is migrated once to the shared
        BACH/OCEAN schema (memory_*); file databases are backed up prior to migration.
        Without the variable, schema remains at usmc_*. A database on v1 contract
        is always upgraded to the latest contract.
        """
        conn = self._get_conn()
        try:
            version = memory_union.union_version(conn)
            if version < memory_union.UNION_VERSION:
                # Auf Vertrag v2 sind usmc_lessons & Co. Views/entfallen.
                schema.migrate(conn)
            wanted = os.environ.get("USMC_MEMORY_UNION") == "1" or version > 0
            if wanted and version < memory_union.UNION_VERSION:
                if not self._is_memory:
                    self._close_conn(conn)
                    memory_union.backup_database(self.db_path)
                    conn = self._get_conn()
                memory_union.apply_union(conn)
            self._union = memory_union.is_union(conn)
        finally:
            if not self._is_memory:
                self._close_conn(conn)

    def _table(self, name: str) -> str:
        """Write target: memory_* in union schema, otherwise usmc_*.

        Reads always go through usmc_* (which are read views in union schema).
        """
        return f"memory_{name}" if self._union else f"usmc_{name}"

    def _insert_session(self, conn: sqlite3.Connection, now: str, task: Optional[str]):
        if self._union:
            return conn.execute(
                "INSERT INTO memory_sessions (session_id, agent_id, started_at, current_task) "
                "VALUES (?, ?, ?, ?)",
                (memory_union.new_session_key(), self.agent_id, now, task),
            )
        return conn.execute(
            "INSERT INTO usmc_sessions (agent_id, started_at, current_task) VALUES (?, ?, ?)",
            (self.agent_id, now, task),
        )

    def _get_conn(self) -> sqlite3.Connection:
        """Creates DB connection with WAL mode."""
        if self._is_memory:
            if self._shared_conn is None:
                self._shared_conn = sqlite3.connect(':memory:')
                self._shared_conn.execute("PRAGMA foreign_keys=ON")
            return self._shared_conn
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _close_conn(self, conn: sqlite3.Connection) -> None:
        """Closes connection (except for :memory: DB)."""
        if not self._is_memory:
            conn.close()

    def _source(self) -> str:
        """Determines source string for write operations."""
        return f"agent:{self.agent_id}"

    # ═══════════════════════════════════════════════════════════════
    # Filter-Bausteine (nur lesend, kein Schema-Eingriff)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _tag_filter(tags, match_all: bool = False):
        """Constructs a delimiter-anchored condition for the tags column.

        A plain ``tags LIKE '%rh%'`` would also match 'research' or
        'rhythm'. Wrapping both the column and the search term with commas ensures
        tags match only as complete elements. Whitespace is stripped so
        'a, b' and 'a,b' behave identically.

        Args:
            tags: Tag specification ('a,b' or list).
            match_all: True = all tags must match (AND),
                False = at least one tag must match (OR, default).

        Returns:
            (sql_fragment, params) or (None, []) if nothing to filter.
            NULL tags never match (concatenation with NULL yields NULL).
        """
        terms = _split_tags(tags)
        if not terms:
            return None, []
        expr = "(',' || REPLACE(tags, ' ', '') || ',') LIKE ('%,' || ? || ',%') ESCAPE '\\'"
        joiner = " AND " if match_all else " OR "
        return "(" + joiner.join([expr] * len(terms)) + ")", [_like_escape(t) for t in terms]

    @staticmethod
    def _grep_filter(grep: Optional[str], columns):
        """Constructs a LIKE condition across multiple columns (OR-combined).

        Case-insensitivity is standard SQLite ASCII behavior; non-ASCII umlauts
        are distinguished unless ICU is compiled in.

        Returns:
            (sql_fragment, params) or (None, []) if nothing to filter.
        """
        if not grep or not grep.strip():
            return None, []
        like = f"%{_like_escape(grep.strip())}%"
        expr = " OR ".join(f"{c} LIKE ? ESCAPE '\\'" for c in columns)
        return f"({expr})", [like] * len(columns)

    # ═══════════════════════════════════════════════════════════════
    # Facts
    # ═══════════════════════════════════════════════════════════════

    def add_fact(
        self,
        category: str,
        key: str,
        value: str,
        confidence: float = 1.0
    ) -> Dict:
        """
        Adds or updates a fact (confidence_merge).

        Overwrites only if new confidence >= existing confidence.

        Args:
            category: Category (user, project, system, domain).
            key: Fact key.
            value: Fact value.
            confidence: Confidence score 0.0-1.0 (default: 1.0).

        Returns:
            Dict containing fact data and 'merged' (bool).

        Raises:
            ValueError: If category or confidence is invalid.
        """
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"category muss einer von {self.VALID_CATEGORIES} sein")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence muss zwischen 0.0 und 1.0 liegen")

        now = datetime.now().isoformat()
        source = self._source()

        conn = self._get_conn()
        try:
            existing = conn.execute(
                "SELECT confidence FROM usmc_facts "
                "WHERE agent_id = ? AND category = ? AND key = ?",
                (self.agent_id, category, key)
            ).fetchone()

            if existing and existing[0] is not None and existing[0] > confidence:
                return {
                    'category': category, 'key': key, 'value': value,
                    'confidence': confidence, 'source': source,
                    'updated_at': now, 'merged': False,
                    'reason': f'existing confidence higher ({existing[0]:.2f} > {confidence:.2f})'
                }

            conn.execute(f"""
                INSERT INTO {self._table('facts')}
                    (agent_id, category, key, value, confidence, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_id, category, key) DO UPDATE SET
                    value = excluded.value,
                    confidence = excluded.confidence,
                    source = excluded.source,
                    updated_at = excluded.updated_at
            """, (self.agent_id, category, key, value, confidence, source, now, now))
            conn.commit()

            return {
                'category': category, 'key': key, 'value': value,
                'confidence': confidence, 'source': source,
                'updated_at': now, 'merged': True
            }
        finally:
            self._close_conn(conn)

    def get_facts(
        self,
        category: Optional[str] = None,
        min_confidence: float = 0.0,
        agent_id: Optional[str] = None,
        grep: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieves facts from database.

        Args:
            category: Filter by category (optional).
            min_confidence: Minimum confidence threshold (0.0-1.0).
            agent_id: Filter by agent (optional, default: all agents).
            grep: Fulltext substring search over key and value (optional).

        Returns:
            List of fact dicts.
        """
        conn = self._get_conn()
        try:
            conditions = ["confidence >= ?"]
            params: list = [min_confidence]

            if category:
                conditions.append("category = ?")
                params.append(category)
            if agent_id:
                conditions.append("agent_id = ?")
                params.append(agent_id)

            grep_sql, grep_params = self._grep_filter(grep, ["key", "value"])
            if grep_sql:
                conditions.append(grep_sql)
                params.extend(grep_params)

            where = " AND ".join(conditions)
            rows = conn.execute(f"""
                SELECT category, key, value, confidence, source, agent_id, updated_at
                FROM usmc_facts
                WHERE {where}
                ORDER BY category, confidence DESC, key
            """, params).fetchall()

            return [
                {
                    'category': r[0], 'key': r[1], 'value': r[2],
                    'confidence': r[3], 'source': r[4],
                    'agent_id': r[5], 'updated_at': r[6]
                }
                for r in rows
            ]
        finally:
            self._close_conn(conn)

    def delete_fact(self, key: str, category: str = "project") -> bool:
        """
        Deletes a fact for this agent.

        Args:
            key: Fact key.
            category: Category (default: project).

        Returns:
            True if deleted, False if not found.
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                f"DELETE FROM {self._table('facts')} "
                "WHERE agent_id = ? AND category = ? AND key = ?",
                (self.agent_id, category, key)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            self._close_conn(conn)

    # ═══════════════════════════════════════════════════════════════
    # Working Memory
    # ═══════════════════════════════════════════════════════════════

    def add_working(
        self,
        content: str,
        type: str = 'note',
        priority: int = 0,
        tags: Optional[str] = None
    ) -> Dict:
        """
        Adds an active working memory note.

        Args:
            content: Note content.
            type: Note type ('note', 'context', 'scratchpad', 'loop').
            priority: Priority (higher = more important).
            tags: Comma-separated tags.

        Returns:
            Dict containing note data including 'id'.

        Raises:
            ValueError: On invalid note type.
        """
        if type not in self.VALID_WORKING_TYPES:
            raise ValueError(f"type muss einer von {self.VALID_WORKING_TYPES} sein")

        now = datetime.now().isoformat()

        conn = self._get_conn()
        try:
            cursor = conn.execute(f"""
                INSERT INTO {self._table('working')}
                    (agent_id, type, content, priority, tags, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (self.agent_id, type, content, priority, tags, now, now))
            conn.commit()

            return {
                'id': cursor.lastrowid,
                'type': type, 'content': content,
                'priority': priority, 'tags': tags,
                'agent_id': self.agent_id, 'created_at': now
            }
        finally:
            self._close_conn(conn)

    def get_working(
        self,
        limit: int = 10,
        agent_id: Optional[str] = None,
        tags=None,
        tags_all: bool = False,
        grep: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieves active working memory notes.

        All filters apply in the WHERE clause prior to the LIMIT: with
        ``limit=10``, the top 10 matching notes for the filter are returned.

        Args:
            limit: Maximum count (highest priority, newest first).
            agent_id: Filter by agent (optional, default: all).
            tags: Tag filter ('a,b' or list); default OR-combined.
            tags_all: True = all tags must match (AND).
            grep: Fulltext substring filter across content (optional).

        Returns:
            List of note dicts.
        """
        conn = self._get_conn()
        try:
            conditions = ["is_active = 1"]
            params: list = []

            if agent_id:
                conditions.append("agent_id = ?")
                params.append(agent_id)

            tag_sql, tag_params = self._tag_filter(tags, match_all=tags_all)
            if tag_sql:
                conditions.append(tag_sql)
                params.extend(tag_params)

            grep_sql, grep_params = self._grep_filter(grep, ["content"])
            if grep_sql:
                conditions.append(grep_sql)
                params.extend(grep_params)

            where = " AND ".join(conditions)
            params.append(limit)

            rows = conn.execute(f"""
                SELECT id, type, content, priority, tags, agent_id, created_at
                FROM usmc_working
                WHERE {where}
                ORDER BY priority DESC, created_at DESC
                LIMIT ?
            """, params).fetchall()

            return [
                {
                    'id': r[0], 'type': r[1], 'content': r[2],
                    'priority': r[3], 'tags': r[4],
                    'agent_id': r[5], 'created_at': r[6]
                }
                for r in rows
            ]
        finally:
            self._close_conn(conn)

    def clear_working(self, agent_only: bool = True) -> int:
        """
        Deactivates working memory entries (soft-delete).

        Args:
            agent_only: Only deactivate own notes (default: True).

        Returns:
            Count of deactivated entries.
        """
        now = datetime.now().isoformat()
        conn = self._get_conn()
        try:
            if agent_only:
                cursor = conn.execute(
                    f"UPDATE {self._table('working')} SET is_active = 0, updated_at = ? "
                    "WHERE is_active = 1 AND agent_id = ?",
                    (now, self.agent_id)
                )
            else:
                cursor = conn.execute(
                    f"UPDATE {self._table('working')} SET is_active = 0, updated_at = ? "
                    "WHERE is_active = 1",
                    (now,)
                )
            conn.commit()
            return cursor.rowcount
        finally:
            self._close_conn(conn)

    # ═══════════════════════════════════════════════════════════════
    # Lessons Learned
    # ═══════════════════════════════════════════════════════════════

    def add_lesson(
        self,
        title: str,
        problem: str,
        solution: str,
        severity: str = 'medium',
        category: str = 'general',
        source_key: Optional[str] = None,
        episode_key: Optional[str] = None,
        source_hash: Optional[str] = None,
        event_anchor: Optional[str] = None,
        editorial_status: Optional[str] = None,
        evidence_class: Optional[str] = None,
        privacy_scope: Optional[str] = None,
        source_kind: Optional[str] = None,
        weight: Optional[float] = None,
        sensitive_source: Optional[bool] = None,
        user_preference: Optional[bool] = None,
        policy_relevant: Optional[bool] = None,
        conflict_flag: Optional[bool] = None,
        mutates_skill: Optional[bool] = None,
        mutates_workflow: Optional[bool] = None,
    ) -> Dict:
        """
        Adds a lesson or ingests it idempotently.

        Legacy unkeyed calls remain append-only starting with confidence 1.0.
        When ``source_key`` and ``episode_key`` are provided together, the v2
        contract applies: exactly one immutable intake payload with lower initial
        weight (0.20). An identical retry returns the existing row; a diverging
        payload fails closed without mutation.

        Args:
            title: Short title.
            problem: Problem description.
            solution: Solution description.
            severity: Severity level ('critical', 'high', 'medium', 'low').
            category: Category (e.g. 'bug', 'workflow', 'tool', 'general').
            source_key: Stable source key (required with episode_key).
            episode_key: Stable episode key within source.

        Returns:
            Dict containing lesson data, ``created`` flag, and computed ``weight``.

        Raises:
            ValueError: On invalid severity or contract violation.
        """
        if severity not in self.VALID_SEVERITIES:
            raise ValueError(f"severity muss einer von {self.VALID_SEVERITIES} sein")

        source_key = source_key.strip() if source_key is not None else None
        episode_key = episode_key.strip() if episode_key is not None else None
        keyed = source_key is not None or episode_key is not None
        resolved_source_kind = source_kind or ("agent" if keyed else "legacy")
        resolved_editorial = editorial_status or ("review" if keyed else "legacy")
        resolved_evidence = evidence_class or "unknown"
        resolved_privacy = privacy_scope or "local"
        resolved_weight = (
            float(weight)
            if weight is not None
            else (NEW_LESSON_INITIAL_WEIGHT if keyed else 1.0)
        )
        validate_lesson_contract(
            source_kind=resolved_source_kind,
            source_key=source_key,
            episode_key=episode_key,
            editorial_status=resolved_editorial,
            evidence_class=resolved_evidence,
            privacy_scope=resolved_privacy,
            weight=resolved_weight,
        )

        if keyed and source_hash is None:
            source_hash = canonical_hash({
                "source_key": source_key,
                "episode_key": episode_key,
                "title": title,
                "problem": problem,
                "solution": solution,
                "event_anchor": event_anchor,
            })

        now = datetime.now().isoformat()
        flag_values = (
            int(bool(sensitive_source)), int(bool(user_preference)),
            int(bool(policy_relevant)), int(bool(conflict_flag)),
            int(bool(mutates_skill)), int(bool(mutates_workflow)),
        )
        ingest_payload_hash = None
        if keyed:
            ingest_payload_hash = lesson_ingest_hash({
                "category": category,
                "severity": severity,
                "title": title,
                "problem": problem,
                "solution": solution,
                "source_kind": resolved_source_kind,
                "source_key": source_key,
                "episode_key": episode_key,
                "source_hash": source_hash,
                "event_anchor": event_anchor,
                "evidence_class": resolved_evidence,
                "privacy_scope": resolved_privacy,
                "sensitive_source": flag_values[0],
                "user_preference": flag_values[1],
                "policy_relevant": flag_values[2],
                "conflict_flag": flag_values[3],
                "mutates_skill": flag_values[4],
                "mutates_workflow": flag_values[5],
            })

        conn = self._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = None
            if keyed:
                existing_row = conn.execute(
                    f"SELECT {_LESSON_SELECT} FROM {self._table('lessons')} "
                    "WHERE source_key = ? AND episode_key = ?",
                    (source_key, episode_key),
                ).fetchone()
                existing = _lesson_dict(existing_row) if existing_row else None
                if existing:
                    _assert_keyed_lesson_integrity(existing)
                if existing and existing["ingest_payload_hash"] != ingest_payload_hash:
                    raise ValueError(
                        "source_key/episode_key wurde bereits mit einem anderen "
                        "Lesson-Payload verwendet; für eine inhaltliche Änderung "
                        "ist ein neuer episode_key oder ein Reviewpfad erforderlich"
                    )

            if existing:
                conn.commit()
                result = existing
                result["created"] = False
                result["upserted"] = True
                return result

            sql = f"""
                INSERT INTO {self._table('lessons')}
                    (agent_id, category, severity, title, problem, solution,
                     is_active, confidence, times_shown, source_kind, source_key,
                     episode_key, source_hash, event_anchor, editorial_status,
                     evidence_class, privacy_scope, sensitive_source,
                     user_preference, policy_relevant, conflict_flag,
                     mutates_skill, mutates_workflow, ingest_payload_hash,
                     ingest_payload_hash_version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                self.agent_id, category, severity, title, problem, solution,
                resolved_weight, resolved_source_kind, source_key, episode_key,
                source_hash, event_anchor, resolved_editorial, resolved_evidence,
                resolved_privacy, *flag_values, ingest_payload_hash,
                LESSON_INGEST_HASH_VERSION if keyed else None, now, now,
            )
            cursor = conn.execute(sql, params)
            lesson_id = cursor.lastrowid
            row = conn.execute(
                f"SELECT {_LESSON_SELECT} FROM {self._table('lessons')} WHERE id = ?",
                (lesson_id,),
            ).fetchone()
            conn.commit()
            result = _lesson_dict(row)
            result["created"] = True
            result["upserted"] = keyed
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            self._close_conn(conn)

    def get_lessons(
        self,
        limit: int = 10,
        severity: Optional[str] = None,
        agent_id: Optional[str] = None,
        grep: Optional[str] = None,
        delivery_eligible_only: bool = False,
    ) -> List[Dict]:
        """
        Retrieves lessons learned.

        Args:
            limit: Maximum count.
            severity: Filter by severity (optional).
            agent_id: Filter by agent (optional, default: all).
            grep: Fulltext substring search over title, problem, and solution (optional).
            delivery_eligible_only: Only editorially approved, local/private,
                non-sensitive lessons. Legacy rows remain visible for compatibility.

        Returns:
            List of lesson dicts.
        """
        conn = self._get_conn()
        try:
            conditions = ["is_active = 1"]
            params: list = []

            if severity:
                conditions.append("severity = ?")
                params.append(severity)
            if agent_id:
                conditions.append("agent_id = ?")
                params.append(agent_id)
            if delivery_eligible_only:
                conditions.append("editorial_status IN ('legacy', 'approved')")
                conditions.append("privacy_scope IN ('local', 'private')")
                conditions.append("sensitive_source = 0")

            grep_sql, grep_params = self._grep_filter(
                grep, ["title", "problem", "solution"]
            )
            if grep_sql:
                conditions.append(grep_sql)
                params.extend(grep_params)

            where = " AND ".join(conditions)
            params.append(limit)

            rows = conn.execute(f"""
                SELECT {_LESSON_SELECT}
                FROM {self._table('lessons')}
                WHERE {where}
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5
                    END,
                    created_at DESC
                LIMIT ?
            """, params).fetchall()

            return [_lesson_dict(row) for row in rows]
        finally:
            self._close_conn(conn)

    def get_lesson(self, lesson_id: int) -> Optional[Dict]:
        """Retrieve a single lesson with provenance and signal state.

        Read-only query -- unblocked in union mode, see get_lessons().
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                f"SELECT {_LESSON_SELECT} FROM {self._table('lessons')} WHERE id = ?",
                (lesson_id,),
            ).fetchone()
            return _lesson_dict(row) if row else None
        finally:
            self._close_conn(conn)

    def set_lesson_editorial_status(self, lesson_id: int, status: str) -> Dict:
        """Set verifiable editorial status without publishing."""
        if status not in VALID_EDITORIAL_STATUSES or status == "legacy":
            raise ValueError("status muss draft, review, approved oder rejected sein")
        now = datetime.now().isoformat()
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                f"UPDATE {self._table('lessons')} SET editorial_status = ?, updated_at = ? "
                "WHERE id = ?",
                (status, now, lesson_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Lesson {lesson_id} nicht gefunden")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._close_conn(conn)
        return self.get_lesson(lesson_id)

    def record_lesson_feedback(
        self,
        lesson_id: int,
        feedback_key: str,
        helpful: Optional[bool] = None,
        independent_repeat: bool = False,
        delivery_failed: bool = False,
        delivery_key: Optional[str] = None,
        event_anchor: Optional[str] = None,
    ) -> Dict:
        """Record feedback exactly once and update decoupled counters.

        An independent repetition can be recorded alongside ``delivery_failed``.
        It remains an independent signal; there is no automatic equivalence
        between repetition and delivery failure.
        """
        feedback_key = feedback_key.strip()
        if not feedback_key:
            raise ValueError("feedback_key darf nicht leer sein")
        if helpful is not None and not isinstance(helpful, bool):
            raise ValueError("helpful muss True, False oder None sein")
        if helpful is None and not independent_repeat and not delivery_failed:
            raise ValueError("mindestens ein Feedbacksignal muss gesetzt sein")

        payload = {
            "lesson_id": lesson_id,
            "feedback_key": feedback_key,
            "helpful": helpful,
            "independent_repeat": bool(independent_repeat),
            "delivery_failed": bool(delivery_failed),
            "delivery_key": delivery_key,
            "event_anchor": event_anchor,
        }
        payload_hash = canonical_hash(payload)
        now = datetime.now().isoformat()
        conn = self._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if not conn.execute(
                f"SELECT 1 FROM {self._table('lessons')} WHERE id = ? AND is_active = 1",
                (lesson_id,),
            ).fetchone():
                raise ValueError(f"Lesson {lesson_id} nicht gefunden")
            if delivery_key and not conn.execute(
                f"SELECT 1 FROM {self._table('lesson_deliveries')} "
                "WHERE lesson_id = ? AND delivery_key = ?",
                (lesson_id, delivery_key),
            ).fetchone():
                raise ValueError("delivery_key gehört nicht zu dieser Lesson")

            existing = conn.execute(
                f"SELECT id, lesson_id, payload_hash FROM {self._table('lesson_feedback')} "
                "WHERE feedback_key = ?",
                (feedback_key,),
            ).fetchone()
            if existing and (
                existing[1] != lesson_id or existing[2] != payload_hash
            ):
                raise ValueError(
                    "feedback_key wurde bereits global mit einer anderen Lesson "
                    "oder einem anderen Payload verwendet"
                )
            created = existing is None
            if created:
                cursor = conn.execute(f"""
                    INSERT INTO {self._table('lesson_feedback')}
                        (lesson_id, feedback_key, helpful, independent_repeat,
                         delivery_failed, delivery_key, event_anchor, payload_hash,
                         agent_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lesson_id, feedback_key,
                    None if helpful is None else int(helpful),
                    int(bool(independent_repeat)), int(bool(delivery_failed)),
                    delivery_key, event_anchor, payload_hash, self.agent_id, now,
                ))
                feedback_id = cursor.lastrowid
            else:
                feedback_id = existing[0]

            conn.execute(f"""
                UPDATE {self._table('lessons')} SET
                    helpful_count = (
                        SELECT COUNT(*) FROM {self._table('lesson_feedback')}
                        WHERE lesson_id = ? AND helpful = 1
                    ),
                    unhelpful_count = (
                        SELECT COUNT(*) FROM {self._table('lesson_feedback')}
                        WHERE lesson_id = ? AND helpful = 0
                    ),
                    independent_repeat_count = (
                        SELECT COUNT(*) FROM {self._table('lesson_feedback')}
                        WHERE lesson_id = ? AND independent_repeat = 1
                    ),
                    delivery_failure_count = (
                        SELECT COUNT(*) FROM {self._table('lesson_feedback')}
                        WHERE lesson_id = ? AND delivery_failed = 1
                    ),
                    updated_at = ?
                WHERE id = ?
            """, (lesson_id, lesson_id, lesson_id, lesson_id, now, lesson_id))
            row = conn.execute(
                f"SELECT {_LESSON_SELECT} FROM {self._table('lessons')} WHERE id = ?",
                (lesson_id,),
            ).fetchone()
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._close_conn(conn)

        result = {
            "id": feedback_id,
            "lesson_id": lesson_id,
            "feedback_key": feedback_key,
            "created": created,
            "delivery_failure_candidate": bool(independent_repeat and delivery_key),
        }
        result.update({
            key: value for key, value in _lesson_dict(row).items()
            if key in (
                "weight", "helpful_count", "unhelpful_count",
                "independent_repeat_count", "delivery_failure_count",
            )
        })
        return result

    def evaluate_lesson_promotion(
        self, lesson_id: int, *, direct_promotion_enabled: bool = False
    ) -> Dict:
        """Evaluates promotion policy only; no publication or mutation."""
        lesson = self.get_lesson(lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} nicht gefunden")
        _assert_keyed_lesson_integrity(lesson)
        return direct_promotion_policy(
            lesson, direct_promotion_enabled=direct_promotion_enabled
        )

    @staticmethod
    def _prepare_delivery_request(
        session_key: str,
        delivery_key: str,
        context: Optional[str],
        lesson_ids: Optional[Iterable[int]],
        limit: int,
        *,
        session_start: bool = False,
        session_task: Optional[str] = None,
    ) -> Dict:
        session_key = session_key.strip()
        delivery_key = delivery_key.strip()
        if not session_key or not delivery_key:
            raise ValueError("session_key und delivery_key dürfen nicht leer sein")
        if not 1 <= limit <= MAX_SESSION_LESSONS:
            raise ValueError(f"limit muss zwischen 1 und {MAX_SESSION_LESSONS} liegen")
        selected_ids = list(dict.fromkeys(int(item) for item in (lesson_ids or [])))
        mode = "selected" if selected_ids else "context"
        request = {
            "session_key": session_key,
            "delivery_key": delivery_key,
            "mode": mode,
            "context": context,
            "lesson_ids": selected_ids,
            "limit": limit,
        }
        if session_start:
            request["session_start"] = True
            request["session_task"] = session_task
        return {
            "session_key": session_key,
            "delivery_key": delivery_key,
            "context": context,
            "selected_ids": selected_ids,
            "limit": limit,
            "mode": mode,
            "request_hash": canonical_hash(request),
        }

    def _replay_delivery_batch(
        self,
        conn: sqlite3.Connection, delivery_key: str
    ) -> List[Dict]:
        lesson_select = ", ".join(f"l.{field}" for field in _LESSON_FIELDS)
        rows = conn.execute(
            f"SELECT {lesson_select}, d.session_key, d.delivery_mode, "
            f"d.feedback_prompt FROM {self._table('lesson_deliveries')} d "
            f"JOIN {self._table('lessons')} l ON l.id = d.lesson_id "
            "WHERE d.delivery_key = ? ORDER BY d.id ASC",
            (delivery_key,),
        ).fetchall()
        result = []
        field_count = len(_LESSON_FIELDS)
        for row in rows:
            item = _lesson_dict(row[:field_count])
            _assert_keyed_lesson_integrity(item)
            item.update({
                "delivery_key": delivery_key,
                "session_key": row[field_count],
                "delivery_mode": row[field_count + 1],
                "new_delivery": False,
                "feedback_prompt": row[field_count + 2],
            })
            result.append(item)
        return result

    def _deliver_lessons_in_transaction(
        self,
        conn: sqlite3.Connection,
        prepared: Dict,
        *,
        session_id: Optional[int] = None,
    ) -> List[Dict]:
        delivery_key = prepared["delivery_key"]
        batch = conn.execute(
            f"SELECT request_hash, session_id FROM {self._table('lesson_delivery_batches')} "
            "WHERE delivery_key = ?",
            (delivery_key,),
        ).fetchone()
        if batch:
            if batch[0] != prepared["request_hash"]:
                raise ValueError(
                    "delivery_key wurde bereits für eine andere Anfrage verwendet"
                )
            if session_id is not None and batch[1] != session_id:
                raise ValueError(
                    "delivery_key gehört bereits zu einem anderen SessionStart"
                )
            return self._replay_delivery_batch(conn, delivery_key)

        now = datetime.now().isoformat()
        conn.execute(f"""
            INSERT INTO {self._table('lesson_delivery_batches')}
                (delivery_key, session_id, session_key, delivery_mode,
                 request_hash, agent_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            delivery_key, session_id, prepared["session_key"], prepared["mode"],
            prepared["request_hash"], self.agent_id, now,
        ))

        base_where = (
            "is_active = 1 AND editorial_status IN ('legacy', 'approved') "
            "AND privacy_scope IN ('local', 'private') "
            "AND sensitive_source = 0"
        )
        selected_ids = prepared["selected_ids"]
        context = prepared["context"]
        if selected_ids:
            placeholders = ",".join("?" for _ in selected_ids)
            rows = conn.execute(
                f"SELECT {_LESSON_SELECT} FROM {self._table('lessons')} "
                f"WHERE {base_where} AND id IN ({placeholders})",
                selected_ids,
            ).fetchall()
            by_id = {row[0]: _lesson_dict(row) for row in rows}
            candidates = [by_id[item] for item in selected_ids if item in by_id]
        else:
            rows = conn.execute(
                f"SELECT {_LESSON_SELECT} FROM {self._table('lessons')} WHERE {base_where}"
            ).fetchall()
            candidates = [_lesson_dict(row) for row in rows]
            terms = [
                term.casefold() for term in re.findall(r"\w+", context or "")
                if len(term) >= 2
            ] or [(context or "").strip().casefold()]

            def relevance(lesson):
                haystack = " ".join(str(lesson.get(field) or "") for field in (
                    "category", "title", "problem", "solution",
                    "source_key", "event_anchor",
                )).casefold()
                return sum(1 for term in terms if term in haystack)

            candidates = [item for item in candidates if relevance(item) > 0]
            severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            candidates.sort(
                key=lambda item: (
                    relevance(item), item["weight"],
                    severity_rank.get(item["severity"], 0), item["created_at"],
                ),
                reverse=True,
            )

        for lesson in candidates:
            _assert_keyed_lesson_integrity(lesson)

        delivered = []
        for lesson in candidates[:prepared["limit"]]:
            payload_hash = canonical_hash({
                "lesson_id": lesson["id"],
                "delivery_key": delivery_key,
                "session_key": prepared["session_key"],
                "mode": prepared["mode"],
                "context": context,
            })
            conn.execute(f"""
                INSERT INTO {self._table('lesson_deliveries')}
                    (lesson_id, delivery_key, session_key, delivery_mode,
                     context, feedback_prompt, payload_hash, agent_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lesson["id"], delivery_key, prepared["session_key"],
                prepared["mode"], context, FEEDBACK_PROMPT, payload_hash,
                self.agent_id, now,
            ))
            conn.execute(
                f"UPDATE {self._table('lessons')} SET times_shown = times_shown + 1, "
                "last_delivered_at = ?, updated_at = ? WHERE id = ?",
                (now, now, lesson["id"]),
            )
            item = dict(lesson)
            item["times_shown"] = item["times_shown"] + 1
            item["last_delivered_at"] = now
            item.update({
                "delivery_key": delivery_key,
                "session_key": prepared["session_key"],
                "delivery_mode": prepared["mode"],
                "new_delivery": True,
                "feedback_prompt": FEEDBACK_PROMPT,
            })
            delivered.append(item)
        return delivered

    def deliver_lessons(
        self,
        session_key: str,
        delivery_key: str,
        context: Optional[str] = None,
        lesson_ids: Optional[Iterable[int]] = None,
        limit: int = MAX_SESSION_LESSONS,
    ) -> List[Dict]:
        """Delivers up to three approved lessons exactly once."""
        prepared = self._prepare_delivery_request(
            session_key, delivery_key, context, lesson_ids, limit
        )
        if not prepared["selected_ids"] and not (context and context.strip()):
            return []
        conn = self._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            delivered = self._deliver_lessons_in_transaction(conn, prepared)
            conn.commit()
            return delivered
        except Exception:
            conn.rollback()
            raise
        finally:
            self._close_conn(conn)

    # ═══════════════════════════════════════════════════════════════
    # Sessions
    # ═══════════════════════════════════════════════════════════════

    def start_session(
        self,
        task: Optional[str] = None,
        lesson_context: Optional[str] = None,
        lesson_ids: Optional[Iterable[int]] = None,
        lesson_limit: int = MAX_SESSION_LESSONS,
        delivery_key: Optional[str] = None,
        lesson_session_key: Optional[str] = None,
    ) -> Dict:
        """
        Starts a new agent session.

        Args:
            task: Optional task description.
            lesson_context: Explicit context for targeted lesson delivery.
            lesson_ids: Explicitly selected lesson IDs.
            delivery_key: Stable idempotency ID; required when delivering lessons.

        Returns:
            Dict containing session data including 'id'.
        """
        selected_ids = list(lesson_ids or [])
        wants_lessons = bool(selected_ids or (lesson_context and lesson_context.strip()))
        if wants_lessons and not delivery_key:
            raise ValueError("delivery_key ist bei SessionStart-Zustellung Pflicht")
        now = datetime.now().isoformat()
        conn = self._get_conn()
        try:
            if not wants_lessons:
                cursor = self._insert_session(conn, now, task)
                conn.commit()
                return {
                    'id': cursor.lastrowid,
                    'agent_id': self.agent_id,
                    'started_at': now,
                    'current_task': task,
                }

            prepared = self._prepare_delivery_request(
                lesson_session_key or delivery_key,
                delivery_key,
                lesson_context,
                selected_ids,
                lesson_limit,
                session_start=True,
                session_task=task,
            )
            conn.execute("BEGIN IMMEDIATE")
            batch = conn.execute(
                "SELECT request_hash, session_id "
                f"FROM {self._table('lesson_delivery_batches')} WHERE delivery_key = ?",
                (prepared["delivery_key"],),
            ).fetchone()
            if batch:
                if batch[0] != prepared["request_hash"]:
                    raise ValueError(
                        "delivery_key wurde bereits für eine andere Anfrage verwendet"
                    )
                if batch[1] is None:
                    raise ValueError(
                        "delivery_key stammt nicht aus einem atomaren SessionStart"
                    )
                session = conn.execute(
                    "SELECT id, agent_id, started_at, current_task "
                    "FROM usmc_sessions WHERE id = ?",
                    (batch[1],),
                ).fetchone()
                if session is None:
                    raise RuntimeError(
                        "Delivery-Batch verweist auf eine fehlende Session"
                    )
                lessons = self._replay_delivery_batch(
                    conn, prepared["delivery_key"]
                )
                conn.commit()
                return {
                    "id": session[0],
                    "agent_id": session[1],
                    "started_at": session[2],
                    "current_task": session[3],
                    "lessons": lessons,
                }

            session_id = self._insert_session(conn, now, task).lastrowid
            lessons = self._deliver_lessons_in_transaction(
                conn, prepared, session_id=session_id
            )
            conn.commit()
            return {
                "id": session_id,
                "agent_id": self.agent_id,
                "started_at": now,
                "current_task": task,
                "lessons": lessons,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            self._close_conn(conn)

    def end_session(self, session_id: int, handoff_notes: Optional[str] = None) -> bool:
        """
        Ends an active session.

        Args:
            session_id: Session ID.
            handoff_notes: Notes for the next session.

        Returns:
            True if successful.
        """
        now = datetime.now().isoformat()

        conn = self._get_conn()
        try:
            cursor = conn.execute(f"""
                UPDATE {self._table('sessions')}
                SET ended_at = ?, handoff_notes = ?
                WHERE id = ? AND agent_id = ?
            """, (now, handoff_notes, session_id, self.agent_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            self._close_conn(conn)

    # ═══════════════════════════════════════════════════════════════
    # Context Generation
    # ═══════════════════════════════════════════════════════════════

    def generate_context(self, max_items: int = 5) -> str:
        """
        Generates compact context for LLM prompts.

        Args:
            max_items: Maximum items per category.

        Returns:
            Formatted context string (Markdown).
        """
        parts = []

        working = self.get_working(limit=max_items)
        if working:
            parts.append("## Aktuelle Notizen")
            for note in working:
                parts.append(f"- [{note['agent_id']}] {note['content'][:100]}")
            parts.append("")

        facts = self.get_facts(min_confidence=0.7)[:max_items]
        if facts:
            parts.append("## Sichere Fakten")
            for fact in facts:
                parts.append(
                    f"- {fact['key']}: {fact['value'][:80]} [{fact['confidence']:.1f}]"
                )
            parts.append("")

        lessons = self.get_lessons(
            limit=max_items, delivery_eligible_only=True
        )
        if lessons:
            parts.append("## Wichtige Lessons")
            for lesson in lessons:
                parts.append(f"- **{lesson['title']}**: {lesson['solution'][:60]}")
            parts.append("")

        return "\n".join(parts) if parts else "Kein Kontext verfügbar."

    # ═══════════════════════════════════════════════════════════════
    # Sync
    # ═══════════════════════════════════════════════════════════════

    def get_changes_since(self, since: str) -> Dict[str, list]:
        """
        Retrieves all changes since a given timestamp.

        Args:
            since: ISO timestamp (e.g. '2026-02-28T00:00:00').

        Returns:
            Dict containing 'facts', 'working', 'lessons', 'sync_timestamp'.
        """
        conn = self._get_conn()
        try:
            facts = conn.execute("""
                SELECT category, key, value, confidence, source, agent_id, updated_at
                FROM usmc_facts WHERE updated_at > ?
                ORDER BY updated_at ASC
            """, (since,)).fetchall()

            working = conn.execute("""
                SELECT id, type, content, tags, agent_id, created_at, updated_at
                FROM usmc_working WHERE updated_at > ? AND is_active = 1
                ORDER BY updated_at ASC
            """, (since,)).fetchall()

            lessons = conn.execute(f"""
                SELECT {_LESSON_SELECT}
                FROM {self._table('lessons')} WHERE updated_at > ? AND is_active = 1
                ORDER BY updated_at ASC
            """, (since,)).fetchall()

            return {
                'facts': [
                    {'category': r[0], 'key': r[1], 'value': r[2],
                     'confidence': r[3], 'source': r[4],
                     'agent_id': r[5], 'updated_at': r[6]}
                    for r in facts
                ],
                'working': [
                    {'id': r[0], 'type': r[1], 'content': r[2],
                     'tags': r[3], 'agent_id': r[4],
                     'created_at': r[5], 'updated_at': r[6]}
                    for r in working
                ],
                'lessons': [_lesson_dict(row) for row in lessons],
                'sync_timestamp': datetime.now().isoformat()
            }
        finally:
            self._close_conn(conn)

    # ═══════════════════════════════════════════════════════════════
    # Status
    # ═══════════════════════════════════════════════════════════════

    def get_status(self) -> Dict:
        """Returns memory statistics."""
        conn = self._get_conn()
        try:
            facts = conn.execute("SELECT COUNT(*) FROM usmc_facts").fetchone()[0]
            working = conn.execute(
                "SELECT COUNT(*) FROM usmc_working WHERE is_active = 1"
            ).fetchone()[0]
            lessons = conn.execute(
                f"SELECT COUNT(*) FROM {self._table('lessons')} WHERE is_active = 1"
            ).fetchone()[0]
            sessions = conn.execute("SELECT COUNT(*) FROM usmc_sessions").fetchone()[0]
            feedback = conn.execute(
                f"SELECT COUNT(*) FROM {self._table('lesson_feedback')}"
            ).fetchone()[0]
            deliveries = conn.execute(
                f"SELECT COUNT(*) FROM {self._table('lesson_deliveries')}"
            ).fetchone()[0]
            confident = conn.execute(
                "SELECT COUNT(*) FROM usmc_facts WHERE confidence >= 0.8"
            ).fetchone()[0]

            return {
                'facts_count': facts,
                'working_count': working,
                'lessons_count': lessons,
                'sessions_count': sessions,
                'lesson_feedback_count': feedback,
                'lesson_deliveries_count': deliveries,
                'confident_facts': confident,
                'agent_id': self.agent_id,
                'db_path': str(self.db_path)
            }
        finally:
            self._close_conn(conn)
