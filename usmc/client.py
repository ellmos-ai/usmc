# -*- coding: utf-8 -*-
"""
USMCClient - United Shared Memory Client
=========================================

Standalone Cross-Agent Memory Sharing mit eigener SQLite-DB.
Kein Zugriff auf bach.db -- voellig unabhaengig.

Methoden:
    add_fact(), get_facts(), add_lesson(), get_lessons(),
    add_working(), get_working(), start_session(), end_session(),
    generate_context(), get_changes_since()

Author: Lukas Geiger
License: MIT
"""

import os
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from . import schema


def _like_escape(value: str) -> str:
    """Maskiert LIKE-Platzhalter, damit ein Suchbegriff woertlich gilt.

    Ohne Maskierung waeren '%' und '_' im Suchbegriff Wildcards -- '_' wuerde
    also jedes beliebige Zeichen treffen. Passend dazu setzen alle Abfragen
    ``ESCAPE '\\'``.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _split_tags(tags) -> List[str]:
    """Normalisiert eine Tag-Angabe zu einer Liste.

    Akzeptiert 'a,b', 'a, b' oder ['a', 'b']; leere Teile fallen weg.
    """
    if tags is None:
        return []
    raw = tags.split(",") if isinstance(tags, str) else list(tags)
    return [str(t).strip() for t in raw if str(t).strip()]


def default_db_path() -> str:
    """Per-System lokaler Default-DB-Pfad (NICHT cwd/OneDrive).

    Default: ``~/.usmc/usmc_memory.db``; Override via Env ``USMC_DB``.
    Legt selbst NICHTS an — das Verzeichnis wird erst beim tatsaechlichen
    Verbinden durch USMCClient erstellt (kein Import-Seiteneffekt).
    """
    env = os.environ.get("USMC_DB")
    if env:
        return env
    return str(Path.home() / ".usmc" / "usmc_memory.db")


class USMCClient:
    """
    Cross-Agent Memory Client mit eigener SQLite-DB.

    Verwendung:
        client = USMCClient()  # ~/.usmc/usmc_memory.db (Override: Env USMC_DB)
        client.add_fact("system", "os", "Windows 11", confidence=0.95)
        client.add_working("Aktueller Task: USMC implementieren")
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
        Initialisiert den USMC Client.

        Args:
            db_path: Pfad zur USMC-Datenbank (wird erstellt falls nicht
                vorhanden). Default: ``default_db_path()`` — per-System
                lokal unter ``~/.usmc/usmc_memory.db``, Override via
                Env ``USMC_DB``.
            agent_id: Agent-Kennung fuer Multi-Agent-Tracking
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
        """Stellt sicher, dass DB und Schema existieren."""
        conn = self._get_conn()
        try:
            schema.migrate(conn)
        finally:
            if not self._is_memory:
                self._close_conn(conn)

    def _get_conn(self) -> sqlite3.Connection:
        """Erstellt DB-Verbindung mit WAL-Mode."""
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
        """Schliesst Connection (ausser bei :memory: DB)."""
        if not self._is_memory:
            conn.close()

    def _source(self) -> str:
        """Bestimmt Source-String fuer Write-Operationen."""
        return f"agent:{self.agent_id}"

    # ═══════════════════════════════════════════════════════════════
    # Filter-Bausteine (nur lesend, kein Schema-Eingriff)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _tag_filter(tags, match_all: bool = False):
        """Baut eine begrenzer-verankerte Bedingung fuer die tags-Spalte.

        Ein nacktes ``tags LIKE '%rh%'`` traefe auch 'research' oder
        'rhythm'. Deshalb wird die Spalte beidseitig mit Kommas umschlossen
        und der Tag inklusive seiner Kommas gesucht -- ein Tag matcht damit
        nur als ganzer Listeneintrag. Leerzeichen in der Spalte werden vorher
        entfernt, damit 'a, b' und 'a,b' gleich behandelt werden.

        Args:
            tags: Tag-Angabe ('a,b' oder Liste)
            match_all: True = alle Tags muessen vorkommen (UND),
                False = mindestens einer (ODER, default)

        Returns:
            (sql_fragment, params) oder (None, []) wenn nichts zu filtern ist.
            NULL-Tags matchen nie (Konkatenation mit NULL ergibt NULL).
        """
        terms = _split_tags(tags)
        if not terms:
            return None, []
        expr = "(',' || REPLACE(tags, ' ', '') || ',') LIKE ('%,' || ? || ',%') ESCAPE '\\'"
        joiner = " AND " if match_all else " OR "
        return "(" + joiner.join([expr] * len(terms)) + ")", [_like_escape(t) for t in terms]

    @staticmethod
    def _grep_filter(grep: Optional[str], columns):
        """Baut eine LIKE-Bedingung ueber mehrere Spalten (ODER-verknuepft).

        Gross-/Kleinschreibung wird von SQLites LIKE fuer ASCII ignoriert;
        Umlaute werden unterschieden (SQLite kennt ohne ICU kein Unicode-Casefolding).

        Returns:
            (sql_fragment, params) oder (None, []) wenn nichts zu filtern ist.
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
        Fuegt Fakt hinzu oder aktualisiert ihn (confidence_merge).

        Ueberschreibt nur wenn neue confidence >= bestehende.

        Args:
            category: Kategorie (user, project, system, domain)
            key: Fakt-Schluessel
            value: Fakt-Wert
            confidence: Konfidenz 0.0-1.0 (default: 1.0)

        Returns:
            Dict mit Fakt-Daten + 'merged' (bool)

        Raises:
            ValueError: Bei ungueltiger Kategorie oder Konfidenz
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

            conn.execute("""
                INSERT INTO usmc_facts
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
        Holt Facts aus der DB.

        Args:
            category: Filter nach Kategorie (optional)
            min_confidence: Minimale Konfidenz (0.0-1.0)
            agent_id: Filter nach Agent (optional, default: alle Agents)
            grep: Volltext-Teilstring ueber key und value (optional)

        Returns:
            Liste von Fakt-Dicts
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
        Loescht einen Fakt dieses Agents.

        Args:
            key: Fakt-Schluessel
            category: Kategorie (default: project)

        Returns:
            True wenn geloescht, False wenn nicht gefunden
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM usmc_facts "
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
        Fuegt eine Working-Memory-Notiz hinzu.

        Args:
            content: Notiz-Inhalt
            type: Typ ('note', 'context', 'scratchpad', 'loop')
            priority: Prioritaet (hoeher = wichtiger)
            tags: Komma-separierte Tags

        Returns:
            Dict mit Notiz-Daten inkl. 'id'

        Raises:
            ValueError: Bei ungueltigem Typ
        """
        if type not in self.VALID_WORKING_TYPES:
            raise ValueError(f"type muss einer von {self.VALID_WORKING_TYPES} sein")

        now = datetime.now().isoformat()

        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                INSERT INTO usmc_working
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
        Holt aktive Working-Memory-Notizen.

        Alle Filter wirken in der WHERE-Klausel, also VOR dem Limit: bei
        ``limit=10`` werden die 10 besten Treffer *des Filters* geliefert,
        nicht der Filter auf die letzten 10 Notizen angewendet.

        Args:
            limit: Maximale Anzahl (hoechste Prioritaet, dann neueste zuerst)
            agent_id: Filter nach Agent (optional, default: alle)
            tags: Tag-Filter ('a,b' oder Liste); default ODER-verknuepft
            tags_all: True = alle angegebenen Tags muessen vorkommen (UND)
            grep: Volltext-Teilstring ueber content (optional)

        Returns:
            Liste von Notiz-Dicts
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
        Deaktiviert Working-Memory-Eintraege (Soft-Delete).

        Args:
            agent_only: Nur eigene Notizen deaktivieren (default: True)

        Returns:
            Anzahl deaktivierter Eintraege
        """
        now = datetime.now().isoformat()
        conn = self._get_conn()
        try:
            if agent_only:
                cursor = conn.execute(
                    "UPDATE usmc_working SET is_active = 0, updated_at = ? "
                    "WHERE is_active = 1 AND agent_id = ?",
                    (now, self.agent_id)
                )
            else:
                cursor = conn.execute(
                    "UPDATE usmc_working SET is_active = 0, updated_at = ? "
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
        category: str = 'general'
    ) -> Dict:
        """
        Fuegt eine Lesson Learned hinzu.

        Args:
            title: Kurztitel
            problem: Problem-Beschreibung
            solution: Loesung
            severity: Schweregrad ('critical', 'high', 'medium', 'low')
            category: Kategorie (z.B. 'bug', 'workflow', 'tool', 'general')

        Returns:
            Dict mit Lesson-Daten inkl. 'id'

        Raises:
            ValueError: Bei ungueltiger Severity
        """
        if severity not in self.VALID_SEVERITIES:
            raise ValueError(f"severity muss einer von {self.VALID_SEVERITIES} sein")

        now = datetime.now().isoformat()

        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                INSERT INTO usmc_lessons
                    (agent_id, category, severity, title, problem, solution,
                     is_active, confidence, times_shown, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, 1.0, 0, ?, ?)
            """, (self.agent_id, category, severity, title, problem, solution, now, now))
            conn.commit()

            return {
                'id': cursor.lastrowid,
                'category': category, 'severity': severity,
                'title': title, 'problem': problem, 'solution': solution,
                'agent_id': self.agent_id, 'created_at': now
            }
        finally:
            self._close_conn(conn)

    def get_lessons(
        self,
        limit: int = 10,
        severity: Optional[str] = None,
        agent_id: Optional[str] = None,
        grep: Optional[str] = None
    ) -> List[Dict]:
        """
        Holt Lessons Learned.

        Args:
            limit: Maximale Anzahl
            severity: Filter nach Severity (optional)
            agent_id: Filter nach Agent (optional, default: alle)
            grep: Volltext-Teilstring ueber title, problem und solution (optional)

        Returns:
            Liste von Lesson-Dicts
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

            grep_sql, grep_params = self._grep_filter(
                grep, ["title", "problem", "solution"]
            )
            if grep_sql:
                conditions.append(grep_sql)
                params.extend(grep_params)

            where = " AND ".join(conditions)
            params.append(limit)

            rows = conn.execute(f"""
                SELECT id, category, severity, title, problem, solution,
                       agent_id, created_at
                FROM usmc_lessons
                WHERE {where}
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5
                    END,
                    created_at DESC
                LIMIT ?
            """, params).fetchall()

            return [
                {
                    'id': r[0], 'category': r[1], 'severity': r[2],
                    'title': r[3], 'problem': r[4], 'solution': r[5],
                    'agent_id': r[6], 'created_at': r[7]
                }
                for r in rows
            ]
        finally:
            self._close_conn(conn)

    # ═══════════════════════════════════════════════════════════════
    # Sessions
    # ═══════════════════════════════════════════════════════════════

    def start_session(self, task: Optional[str] = None) -> Dict:
        """
        Startet eine neue Agent-Session.

        Args:
            task: Optionale Task-Beschreibung

        Returns:
            Dict mit Session-Daten inkl. 'id'
        """
        now = datetime.now().isoformat()

        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                INSERT INTO usmc_sessions (agent_id, started_at, current_task)
                VALUES (?, ?, ?)
            """, (self.agent_id, now, task))
            conn.commit()

            return {
                'id': cursor.lastrowid,
                'agent_id': self.agent_id,
                'started_at': now,
                'current_task': task
            }
        finally:
            self._close_conn(conn)

    def end_session(self, session_id: int, handoff_notes: Optional[str] = None) -> bool:
        """
        Beendet eine Session.

        Args:
            session_id: Session-ID
            handoff_notes: Notizen fuer die naechste Session

        Returns:
            True wenn erfolgreich
        """
        now = datetime.now().isoformat()

        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                UPDATE usmc_sessions
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
        Generiert kompakten Kontext fuer LLM-Prompts.

        Args:
            max_items: Maximale Items pro Kategorie

        Returns:
            Formatierter Kontext-String (Markdown)
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

        lessons = self.get_lessons(limit=max_items)
        if lessons:
            parts.append("## Wichtige Lessons")
            for lesson in lessons:
                parts.append(f"- **{lesson['title']}**: {lesson['solution'][:60]}")
            parts.append("")

        return "\n".join(parts) if parts else "Kein Kontext verfuegbar."

    # ═══════════════════════════════════════════════════════════════
    # Sync
    # ═══════════════════════════════════════════════════════════════

    def get_changes_since(self, since: str) -> Dict[str, list]:
        """
        Holt alle Aenderungen seit einem Zeitstempel.

        Args:
            since: ISO-Zeitstempel (z.B. '2026-02-28T00:00:00')

        Returns:
            Dict mit 'facts', 'working', 'lessons', 'sync_timestamp'
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

            lessons = conn.execute("""
                SELECT id, category, severity, title, problem, solution,
                       agent_id, created_at, updated_at
                FROM usmc_lessons WHERE updated_at > ? AND is_active = 1
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
                'lessons': [
                    {'id': r[0], 'category': r[1], 'severity': r[2],
                     'title': r[3], 'problem': r[4], 'solution': r[5],
                     'agent_id': r[6], 'created_at': r[7], 'updated_at': r[8]}
                    for r in lessons
                ],
                'sync_timestamp': datetime.now().isoformat()
            }
        finally:
            self._close_conn(conn)

    # ═══════════════════════════════════════════════════════════════
    # Status
    # ═══════════════════════════════════════════════════════════════

    def get_status(self) -> Dict:
        """Gibt Memory-Statistiken zurueck."""
        conn = self._get_conn()
        try:
            facts = conn.execute("SELECT COUNT(*) FROM usmc_facts").fetchone()[0]
            working = conn.execute(
                "SELECT COUNT(*) FROM usmc_working WHERE is_active = 1"
            ).fetchone()[0]
            lessons = conn.execute(
                "SELECT COUNT(*) FROM usmc_lessons WHERE is_active = 1"
            ).fetchone()[0]
            sessions = conn.execute("SELECT COUNT(*) FROM usmc_sessions").fetchone()[0]
            confident = conn.execute(
                "SELECT COUNT(*) FROM usmc_facts WHERE confidence >= 0.8"
            ).fetchone()[0]

            return {
                'facts_count': facts,
                'working_count': working,
                'lessons_count': lessons,
                'sessions_count': sessions,
                'confident_facts': confident,
                'agent_id': self.agent_id,
                'db_path': str(self.db_path)
            }
        finally:
            self._close_conn(conn)
