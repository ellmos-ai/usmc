# -*- coding: utf-8 -*-
"""
USMC High-Level API
====================

Convenience functions for fast access without an explicit client instance.
Singleton pattern with a global default database.

Usage:
    from usmc import api

    api.init(agent_id="opus")
    api.fact("system", "os", "Windows 11")
    api.note("Current task: implement feature X")
    api.lesson("Encoding bug", "cp1252", "PYTHONIOENCODING=utf-8")

    print(api.context())
    print(api.status())

Author: Lukas Geiger
License: MIT
"""

from typing import Optional, List, Dict, Iterable

from .client import USMCClient

# Global client instance
_client: Optional[USMCClient] = None


def init(
    db_path: Optional[str] = None,
    agent_id: str = "default"
) -> USMCClient:
    """
    Initializes the global USMC instance.

    Args:
        db_path: Path to database (default: ``~/.usmc/usmc_memory.db``,
            override via env ``USMC_DB`` -- see ``client.default_db_path``)
        agent_id: Agent identifier

    Returns:
        The initialized client instance
    """
    global _client
    _client = USMCClient(db_path=db_path, agent_id=agent_id)
    return _client


def get_client() -> USMCClient:
    """Returns the global client instance (lazy init)."""
    global _client
    if _client is None:
        _client = USMCClient(agent_id="default")
    return _client


def set_agent(agent_id: str) -> None:
    """Sets the agent ID for new entries."""
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
    Stores a fact.

    Args:
        category: user, project, system, or domain
        key: Key
        value: Value
        confidence: Confidence 0.0-1.0

    Returns:
        Dict with result
    """
    return get_client().add_fact(category, key, value, confidence)


def facts(
    category: Optional[str] = None,
    min_confidence: float = 0.0,
    agent_id: Optional[str] = None,
    grep: Optional[str] = None
) -> List[Dict]:
    """Retrieves facts (optionally filtered).

    Args:
        category: user, project, system, or domain
        min_confidence: Minimum confidence
        agent_id: Only facts from this agent
        grep: Substring in key or value
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
    Stores a note in working memory.

    Args:
        content: Note text
        priority: Priority (higher = more important)
        tags: Comma-separated tags

    Returns:
        Dict with result
    """
    return get_client().add_working(content, type='note', priority=priority, tags=tags)


def scratch(content: str) -> Dict:
    """Stores a scratchpad entry (temporary)."""
    return get_client().add_working(content, type='scratchpad', priority=-1)


def loop(content: str) -> Dict:
    """Stores a loop entry (for iterations)."""
    return get_client().add_working(content, type='loop', priority=0)


def working(
    limit: int = 10,
    agent_id: Optional[str] = None,
    tags=None,
    tags_all: bool = False,
    grep: Optional[str] = None
) -> List[Dict]:
    """Retrieves active working memory entries (optionally filtered).

    Args:
        limit: Maximum number of entries
        agent_id: Only notes from this agent
        tags: Tag filter ('a,b' or list), OR-connected
        tags_all: True = all tags must match (AND)
        grep: Substring in content

    Filters are applied in the database query before ``limit``.
    """
    return get_client().get_working(
        limit=limit, agent_id=agent_id,
        tags=tags, tags_all=tags_all, grep=grep
    )


def clear() -> int:
    """Deletes all working memory entries for the current agent."""
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
    Stores a lesson learned.

    Args:
        title: Short title
        problem: Problem description
        solution: Solution
        severity: critical, high, medium, low
        category: Category (default: general)
        source_key/episode_key: Jointly set idempotent v2 keys
        contract: Optional provenance, review, privacy, and policy fields

    Returns:
        Dict with result
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
    """Retrieves lessons learned (optionally filtered).

    Args:
        severity: critical, high, medium, or low
        limit: Maximum number of entries
        agent_id: Only lessons from this agent
        grep: Substring in title, problem, or solution
        delivery_eligible_only: Only return lessons eligible for delivery
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
    """Stores idempotent, separately evaluable feedback for a lesson."""
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
    """Sets editorial review status without publishing side effects."""
    return get_client().set_lesson_editorial_status(lesson_id, status)


def lesson_promotion(lesson_id: int) -> Dict:
    """Evaluates the direct promotion gate; always disabled in production."""
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
    """Delivers contextual or selected lessons synchronously within limits."""
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
    """Starts a new session."""
    return get_client().start_session(
        task=task,
        lesson_context=lesson_context,
        lesson_ids=lesson_ids,
        lesson_limit=lesson_limit,
        delivery_key=delivery_key,
        lesson_session_key=lesson_session_key,
    )


def end(session_id: int, notes: Optional[str] = None) -> bool:
    """Ends a session with optional handoff notes."""
    return get_client().end_session(session_id, handoff_notes=notes)


# ═══════════════════════════════════════════════════════════════════════════
# Context & Status
# ═══════════════════════════════════════════════════════════════════════════

def context(max_items: int = 5) -> str:
    """Generates compact context for LLM prompts."""
    return get_client().generate_context(max_items=max_items)


def status() -> Dict:
    """Returns memory statistics."""
    return get_client().get_status()


def changes(since: str) -> Dict:
    """Retrieves all changes since a given timestamp."""
    return get_client().get_changes_since(since)


# ═══════════════════════════════════════════════════════════════════════════
# Shortcuts
# ═══════════════════════════════════════════════════════════════════════════

def remember(key: str, value: str, category: str = 'project') -> Dict:
    """Shortcut: stores a fact with high confidence."""
    return fact(category, key, value, confidence=0.95)


def forget(key: str, category: str = 'project') -> bool:
    """
    Deletes a fact (hard delete).

    Args:
        key: Fact key
        category: Category (default: project)

    Returns:
        True if deleted, False if not found
    """
    return get_client().delete_fact(key, category=category)
