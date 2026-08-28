# -*- coding: utf-8 -*-
"""Pure validation, scoring and policy helpers for the v2 lesson contract."""

import hashlib
import json
from typing import Dict, Optional


NEW_LESSON_INITIAL_WEIGHT = 0.20
MAX_SESSION_LESSONS = 3
FEEDBACK_PROMPT = "War diese Lesson hilfreich? (ja/nein)"

VALID_SOURCE_KINDS = ("legacy", "agent", "user", "import")
VALID_EDITORIAL_STATUSES = ("legacy", "draft", "review", "approved", "rejected")
VALID_EVIDENCE_CLASSES = ("unknown", "anecdotal", "corroborated", "verified")
VALID_PRIVACY_SCOPES = ("local", "private", "shared", "public")


def canonical_hash(payload: Dict) -> str:
    """Return a stable SHA-256 for an idempotency payload."""
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_lesson_contract(
    *,
    source_kind: str,
    source_key: Optional[str],
    episode_key: Optional[str],
    editorial_status: str,
    evidence_class: str,
    privacy_scope: str,
    weight: float,
) -> None:
    """Validate additive v2 fields while allowing the legacy unkeyed path."""
    if source_kind not in VALID_SOURCE_KINDS:
        raise ValueError(f"source_kind muss einer von {VALID_SOURCE_KINDS} sein")
    if bool(source_key) != bool(episode_key):
        raise ValueError("source_key und episode_key müssen gemeinsam gesetzt werden")
    if source_key is not None and not source_key.strip():
        raise ValueError("source_key darf nicht leer sein")
    if episode_key is not None and not episode_key.strip():
        raise ValueError("episode_key darf nicht leer sein")
    if editorial_status not in VALID_EDITORIAL_STATUSES:
        raise ValueError(
            f"editorial_status muss einer von {VALID_EDITORIAL_STATUSES} sein"
        )
    if evidence_class not in VALID_EVIDENCE_CLASSES:
        raise ValueError(
            f"evidence_class muss einer von {VALID_EVIDENCE_CLASSES} sein"
        )
    if privacy_scope not in VALID_PRIVACY_SCOPES:
        raise ValueError(f"privacy_scope muss einer von {VALID_PRIVACY_SCOPES} sein")
    if not 0.0 <= weight <= 1.0:
        raise ValueError("weight muss zwischen 0.0 und 1.0 liegen")


def lesson_weight(lesson: Dict) -> float:
    """Compute a bounded score from independent, auditable signal counters."""
    score = float(lesson.get("confidence") or 0.0)
    score += int(lesson.get("helpful_count") or 0) * 0.10
    score -= int(lesson.get("unhelpful_count") or 0) * 0.15
    score += int(lesson.get("independent_repeat_count") or 0) * 0.05
    score -= int(lesson.get("delivery_failure_count") or 0) * 0.10
    return round(max(0.0, min(1.0, score)), 4)


def direct_promotion_policy(
    lesson: Dict, *, direct_promotion_enabled: bool = False
) -> Dict:
    """Evaluate but never execute the narrow direct-promotion policy.

    The product gate defaults to off. ``allowed`` therefore remains false in
    production until a later rollout explicitly supplies an enabled policy.
    This helper performs no editorial update, publication or workflow change.
    """
    reasons = []
    if lesson.get("source_kind") != "agent":
        reasons.append("source-not-agent")
    if lesson.get("privacy_scope") not in {"local", "private"}:
        reasons.append("privacy-not-local-private")
    if lesson.get("evidence_class") != "verified":
        reasons.append("evidence-not-verified")
    if not all(
        lesson.get(field)
        for field in ("source_key", "episode_key", "source_hash", "event_anchor")
    ):
        reasons.append("provenance-incomplete")
    if lesson.get("editorial_status") == "rejected":
        reasons.append("editorially-rejected")
    if bool(lesson.get("sensitive_source")):
        reasons.append("sensitive-source")
    if bool(lesson.get("user_preference")):
        reasons.append("user-preference")
    if bool(lesson.get("policy_relevant")):
        reasons.append("policy-relevant")
    if bool(lesson.get("conflict_flag")):
        reasons.append("conflict")
    if bool(lesson.get("mutates_skill")):
        reasons.append("skill-mutation")
    if bool(lesson.get("mutates_workflow")):
        reasons.append("workflow-mutation")

    eligible = not reasons
    return {
        "lesson_id": lesson.get("id"),
        "eligible": eligible,
        "gate_enabled": bool(direct_promotion_enabled),
        "allowed": eligible and bool(direct_promotion_enabled),
        "requires_review": not eligible or not direct_promotion_enabled,
        "review_reasons": reasons or (["product-gate-disabled"] if not direct_promotion_enabled else []),
        "automatic_publication": False,
    }
