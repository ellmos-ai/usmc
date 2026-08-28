# -*- coding: utf-8 -*-
"""
USMC High-Level API
====================

Convenience-Funktionen fuer schnellen Zugriff ohne explizite Client-Instanz.
Singleton-Pattern mit globaler Default-DB.

Verwendung:
    from usmc import api

    api.init(agent_id="opus")
    api.fact("system", "os", "Windows 11")
    api.note("Aktueller Task: Feature X implementieren")
    api.lesson("Encoding-Bug", "cp1252", "PYTHONIOENCODING=utf-8")

    print(api.context())
    print(api.status())

Author: Lukas Geiger
License: MIT
"""

from pathlib import Path
from typing import Optional, List, Dict, Iterable

from .client import USMCClient

# Globale Client-Instanz
_client: Optional[USMCClient] = None


def init(
    db_path: Optional[str] = None,
    agent_id: str = "default"
) -> USMCClient:
    """
    Initialisiert die globale USMC-Instanz.

    Args:
        db_path: Pfad zur DB (default: ``~/.usmc/usmc_memory.db``,
            Override via Env ``USMC_DB`` — siehe ``client.default_db_path``)
        agent_id: Agent-Kennung

    Returns:
        Die initialisierte Client-Instanz
    """
    global _client
    _client = USMCClient(db_path=db_path, agent_id=agent_id)
    return _client


def get_client() -> USMCClient:
    """Gibt die globale Client-Instanz zurueck (lazy init)."""
    global _client
    if _client is None:
        _client = USMCClient(agent_id="default")
    return _client


def set_agent(agent_id: str) -> None:
    """Setzt die Agent-ID fuer neue Eintraege."""
    client = get_client()
    client.agent_id = agent_id


# ═══════════════════════════════════════════════════════════════════════════
# Facts
# ═══════════════════════════════════════════════════════════════════════════

def fact(
    category: str,
    key: str,
    value: str,
    confidence: float = 1.0
) -> Dict:
    """
    Speichert einen Fakt.

    Args:
        category: user, project, system, oder domain
        key: Schluessel
        value: Wert
        confidence: Konfidenz 0.0-1.0

    Returns:
        Dict mit Ergebnis
    """
    return get_client().add_fact(category, key, value, confidence)


def facts(
    category: Optional[str] = None,
    min_confidence: float = 0.0,
    agent_id: Optional[str] = None,
    grep: Optional[str] = None
) -> List[Dict]:
    """Holt Fakten (optional gefiltert).

    Args:
        category: user, project, system oder domain
        min_confidence: Minimale Konfidenz
        agent_id: Nur Fakten dieses Agents
        grep: Teilstring in key oder value
    """
    return get_client().get_facts(
        category=category, min_confidence=min_confidence,
        agent_id=agent_id, grep=grep
    )


# ═══════════════════════════════════════════════════════════════════════════
# Working Memory
# ═══════════════════════════════════════════════════════════════════════════

def note(
    content: str,
    priority: int = 0,
    tags: Optional[str] = None
) -> Dict:
    """
    Speichert eine Notiz im Working Memory.

    Args:
        content: Notiz-Text
        priority: Prioritaet (hoeher = wichtiger)
        tags: Komma-separierte Tags

    Returns:
        Dict mit Ergebnis
    """
    return get_client().add_working(content, type='note', priority=priority, tags=tags)


def scratch(content: str) -> Dict:
    """Speichert einen Scratchpad-Eintrag (temporaer)."""
    return get_client().add_working(content, type='scratchpad', priority=-1)


def loop(content: str) -> Dict:
    """Speichert einen Loop-Eintrag (fuer Iterationen)."""
    return get_client().add_working(content, type='loop', priority=0)


def working(
    limit: int = 10,
    agent_id: Optional[str] = None,
    tags=None,
    tags_all: bool = False,
    grep: Optional[str] = None
) -> List[Dict]:
    """Holt aktive Working-Memory-Eintraege (optional gefiltert).

    Args:
        limit: Maximale Anzahl
        agent_id: Nur Notizen dieses Agents
        tags: Tag-Filter ('a,b' oder Liste), ODER-verknuepft
        tags_all: True = alle Tags muessen vorkommen (UND)
        grep: Teilstring im Inhalt

    Die Filter wirken in der Datenbankabfrage, also vor ``limit``.
    """
    return get_client().get_working(
        limit=limit, agent_id=agent_id,
        tags=tags, tags_all=tags_all, grep=grep
    )


def clear() -> int:
    """Loescht alle Working-Memory-Eintraege des aktuellen Agents."""
    return get_client().clear_working(agent_only=True)


# ═══════════════════════════════════════════════════════════════════════════
# Lessons
# ═══════════════════════════════════════════════════════════════════════════

def lesson(
    title: str,
    problem: str,
    solution: str,
    severity: str = 'medium',
    category: str = 'general',
    source_key: Optional[str] = None,
    episode_key: Optional[str] = None,
    **contract,
) -> Dict:
    """
    Speichert eine Lesson Learned.

    Args:
        title: Kurztitel
        problem: Problem-Beschreibung
        solution: Loesung
        severity: critical, high, medium, low
        source_key/episode_key: Gemeinsam gesetzter idempotenter v2-Schluessel
        contract: Optionale Provenienz-, Review-, Privacy- und Policyfelder

    Returns:
        Dict mit Ergebnis
    """
    return get_client().add_lesson(
        title=title,
        problem=problem,
        solution=solution,
        severity=severity,
        category=category,
        source_key=source_key,
        episode_key=episode_key,
        **contract,
    )


def lessons(
    severity: Optional[str] = None,
    limit: int = 10,
    agent_id: Optional[str] = None,
    grep: Optional[str] = None,
    delivery_eligible_only: bool = False,
) -> List[Dict]:
    """Holt Lessons Learned (optional gefiltert).

    Args:
        severity: critical, high, medium oder low
        limit: Maximale Anzahl
        agent_id: Nur Lessons dieses Agents
        grep: Teilstring in title, problem oder solution
    """
    return get_client().get_lessons(
        limit=limit, severity=severity, agent_id=agent_id, grep=grep,
        delivery_eligible_only=delivery_eligible_only,
    )


def lesson_feedback(
    lesson_id: int,
    feedback_key: str,
    helpful: Optional[bool] = None,
    independent_repeat: bool = False,
    delivery_failed: bool = False,
    delivery_key: Optional[str] = None,
    event_anchor: Optional[str] = None,
) -> Dict:
    """Speichert eine idempotente, getrennt auswertbare Rueckmeldung."""
    return get_client().record_lesson_feedback(
        lesson_id=lesson_id,
        feedback_key=feedback_key,
        helpful=helpful,
        independent_repeat=independent_repeat,
        delivery_failed=delivery_failed,
        delivery_key=delivery_key,
        event_anchor=event_anchor,
    )


def lesson_review(lesson_id: int, status: str) -> Dict:
    """Setzt den Redaktionsstatus ohne Publikationswirkung."""
    return get_client().set_lesson_editorial_status(lesson_id, status)


def lesson_promotion(lesson_id: int) -> Dict:
    """Prueft den Direct-Promotion-Gate; produktiv immer deaktiviert."""
    return get_client().evaluate_lesson_promotion(
        lesson_id, direct_promotion_enabled=False
    )


def deliver_lessons(
    session_key: str,
    delivery_key: str,
    context: Optional[str] = None,
    lesson_ids: Optional[Iterable[int]] = None,
    limit: int = 3,
) -> List[Dict]:
    """Liefert synchron und begrenzt Kontext- oder Auswahl-Lessons."""
    return get_client().deliver_lessons(
        session_key=session_key,
        delivery_key=delivery_key,
        context=context,
        lesson_ids=lesson_ids,
        limit=limit,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Sessions
# ═══════════════════════════════════════════════════════════════════════════

def start(
    task: Optional[str] = None,
    lesson_context: Optional[str] = None,
    lesson_ids: Optional[Iterable[int]] = None,
    lesson_limit: int = 3,
    delivery_key: Optional[str] = None,
    lesson_session_key: Optional[str] = None,
) -> Dict:
    """Startet eine neue Session."""
    return get_client().start_session(
        task=task,
        lesson_context=lesson_context,
        lesson_ids=lesson_ids,
        lesson_limit=lesson_limit,
        delivery_key=delivery_key,
        lesson_session_key=lesson_session_key,
    )


def end(session_id: int, notes: Optional[str] = None) -> bool:
    """Beendet eine Session mit optionalen Handoff-Notes."""
    return get_client().end_session(session_id, handoff_notes=notes)


# ═══════════════════════════════════════════════════════════════════════════
# Context & Status
# ═══════════════════════════════════════════════════════════════════════════

def context(max_items: int = 5) -> str:
    """Generiert kompakten Kontext fuer LLM-Prompts."""
    return get_client().generate_context(max_items=max_items)


def status() -> Dict:
    """Gibt Memory-Statistiken zurueck."""
    return get_client().get_status()


def changes(since: str) -> Dict:
    """Holt alle Aenderungen seit einem Zeitstempel."""
    return get_client().get_changes_since(since)


# ═══════════════════════════════════════════════════════════════════════════
# Shortcuts
# ═══════════════════════════════════════════════════════════════════════════

def remember(key: str, value: str, category: str = 'project') -> Dict:
    """Shortcut: Speichert einen Fakt mit hoher Konfidenz."""
    return fact(category, key, value, confidence=0.95)


def forget(key: str, category: str = 'project') -> bool:
    """
    Loescht einen Fakt (hard delete).

    Args:
        key: Fakt-Schluessel
        category: Kategorie (default: project)

    Returns:
        True wenn geloescht, False wenn nicht gefunden
    """
    return get_client().delete_fact(key, category=category)
