# -*- coding: utf-8 -*-
"""Agent memory import and non-destructive USMC redirection setup.

Implements the ``usmc setup`` workflow:
- Safe-by-default dry-run preview (``--apply`` required to write).
- Idempotent import of Claude Code, Codex, and Gemini memory notes using
  ``source_kind="import"``, stable ``source_key``/``episode_key``, initial weight
  ``0.20``, ``editorial_status="review"``, and ``privacy_scope="private"``.
- Strict exclusion of silos marked ``private`` (imports Home + non-private silos).
- Source files are never deleted or overwritten; ``MEMORY.md`` receives an
  idempotent USMC-leads index/pointer block while preserving existing entries.
- Rule-file pointers (Claude ``CLAUDE.md``, Codex ``GPT.md``/``memoryhooker.toml``,
  Gemini ``GEMINI.md``) with timestamped backups and readback verification.
- Never sets ``autoMemoryDirectory`` or injects untested Gemini hooks.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .client import NEW_LESSON_INITIAL_WEIGHT, USMCClient

SUPPORTED_AGENTS = ("claude", "codex", "gemini", "kimi")

_SETUP_START = "<!-- USMC-SETUP:START -->"
_SETUP_END = "<!-- USMC-SETUP:END -->"
_INDEX_START = "<!-- USMC-MEMORY-INDEX:START -->"
_INDEX_END = "<!-- USMC-MEMORY-INDEX:END -->"

_SECRET_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("GitHub token", re.compile(r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("OpenAI key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "Credential assignment",
        re.compile(r"(?i)\b(?:password|passwd|api_key|secret_key|auth_token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-.]{12,}"),
    ),
)

_PRIVATE_SILO_MARKERS = {".private", ".usmc-private", "PRIVATE", "PRIVATE.md"}
_PRIVATE_SILO_NAME_RE = re.compile(
    r"(?:^|[-_.])(?:private|privat|credentials|private-data|research|forschung|umbruch|temp|scratch)(?:$|[-_.])",
    re.IGNORECASE,
)
_TOML_ORDER_RE = re.compile(r"(?ms)^(\[backend\]\s*(?:[^\[]*?))^(order\s*=\s*\[[^\]]*\])")

_CLAUDE_RULE_BLOCK = "\n".join(
    [
        _SETUP_START,
        "## USMC Memory Redirection (Claude Code)",
        "- Agentenuebergreifendes Wissen (`facts`, `lessons`, `notes`) in USMC speichern: `usmc fact ...`, `usmc lesson ...`, `usmc note ...`.",
        "- Bestehende Projekt-Silos und `MEMORY.md` bleiben als Index erhalten (`autoMemoryDirectory` wird nicht veraendert).",
        _SETUP_END,
    ]
)

_CODEX_RULE_BLOCK = "\n".join(
    [
        _SETUP_START,
        "## USMC Memory Redirection (Codex)",
        "- Fuehrender cross-agent Speicher ist USMC (`usmc context`, `usmc fact`, `usmc lesson`); MemoryHooker liest `usmc` zuerst.",
        "- `~/.codex/memories/` bleibt als App-Bestand unberuehrt; Automationszustand wird nicht nach USMC importiert.",
        _SETUP_END,
    ]
)

_GEMINI_RULE_BLOCK = "\n".join(
    [
        _SETUP_START,
        "## USMC Memory Redirection (Gemini / Antigravity)",
        "- Allgemeines, agentenuebergreifendes Wissen ueber `usmc fact` / `usmc lesson` / `usmc note` ablegen; `usmc context` liefert den kompakten Stand.",
        "- Automationsprotokolle (`AUTOMATIONS-MEMORY.md`, `*_automation_memory.json`) bleiben lokal und gehoeren nicht in USMC.",
        _SETUP_END,
    ]
)

_MEMORY_INDEX_BLOCK = "\n".join(
    [
        _INDEX_START,
        "> **USMC fuehrt (Index-Hinweis):** Agentenuebergreifende Fakten und Lessons leben fuehrend in USMC (`~/.usmc/usmc_memory.db` via `usmc`). Diese `MEMORY.md` dient als Index und Zeiger; bestehende Eintraege bleiben unveraendert erhalten.",
        _INDEX_END,
    ]
)


def _home_slug(home: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(home.resolve()))


def _detect_secret_category(text: str) -> Optional[str]:
    for category, pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            return category
    return None


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}, text
    meta: Dict[str, str] = {}
    for raw in lines[1:end_idx]:
        if ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        meta[k.strip().lower()] = v.strip().strip("\"'")
    body = "\n".join(lines[end_idx + 1 :]).strip()
    return meta, body


def _normalized_digest(body: str) -> str:
    norm = re.sub(r"\s+", " ", body.strip()).casefold()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strip_usmc_blocks(text: str) -> str:
    cleaned = re.sub(rf"{re.escape(_SETUP_START)}.*?{re.escape(_SETUP_END)}\s*", "", text, flags=re.S)
    cleaned = re.sub(rf"{re.escape(_INDEX_START)}.*?{re.escape(_INDEX_END)}\s*", "", cleaned, flags=re.S)
    return cleaned.strip()


def _is_private_silo(silo_dir: Path, home_slug: str) -> Tuple[bool, Optional[str]]:
    if silo_dir.name.casefold() == home_slug.casefold():
        return False, None
    memory_dir = silo_dir / "memory"
    for base in (silo_dir, memory_dir):
        if not base.is_dir():
            continue
        for marker in _PRIVATE_SILO_MARKERS:
            if (base / marker).exists():
                return True, f"marker:{marker}"
    if _PRIVATE_SILO_NAME_RE.search(silo_dir.name):
        return True, "silo-name:private"
    if memory_dir.is_dir():
        for md in sorted(memory_dir.glob("*.md")):
            try:
                head = md.read_text(encoding="utf-8", errors="replace")[:1500]
            except OSError:
                continue
            meta, _ = _parse_frontmatter(head)
            if meta.get("privacy", "").lower() == "private" or meta.get("privacy_scope", "").lower() == "private":
                return True, f"frontmatter:{md.name}"
            if meta.get("private", "").lower() in {"true", "1", "yes"}:
                return True, f"frontmatter:{md.name}"
    return False, None


def _backup_and_write(path: Path, new_text: str, marker: str, apply: bool) -> Dict[str, str]:
    existed = path.is_file()
    old_text = path.read_text(encoding="utf-8", errors="replace") if existed else ""
    if old_text == new_text:
        return {"path": str(path), "action": "unchanged", "backup": "", "readback": "ok"}
    if not apply:
        return {
            "path": str(path),
            "action": "would_update" if existed else "would_create",
            "backup": "",
            "readback": "dry-run",
        }
    backup_path = ""
    if existed:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        cand = path.with_name(f"{path.name}.bak.{stamp}")
        idx = 1
        while cand.exists():
            idx += 1
            cand = path.with_name(f"{path.name}.bak.{stamp}.{idx}")
        shutil.copy2(path, cand)
        backup_path = str(cand)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_text, encoding="utf-8")
    verified = path.read_text(encoding="utf-8", errors="replace")
    if marker not in verified:
        raise RuntimeError(f"Readback-Pruefung fehlgeschlagen fuer {path}")
    return {
        "path": str(path),
        "action": "updated" if existed else "created",
        "backup": backup_path,
        "readback": "ok",
    }


def _upsert_block(existing: str, block: str, start_marker: str, end_marker: str, *, prepend: bool = False) -> str:
    pattern = re.compile(rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.S)
    if pattern.search(existing):
        return pattern.sub(lambda _m: block, existing, count=1)
    if not existing.strip():
        return block + "\n"
    if prepend:
        return block + "\n\n" + existing.lstrip("\r\n")
    sep = "\n" if existing.endswith("\n") else "\n\n"
    return existing + sep + block + "\n"


def _rewrite_memoryhooker_toml(text: str) -> Tuple[str, bool]:
    """Ensure 'usmc' is first in [backend] order = [...] without disturbing other config."""
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
        tomllib = None

    current_order: Optional[List[str]] = None
    if tomllib is not None:
        try:
            parsed = tomllib.loads(text)
            order = (parsed.get("backend") or {}).get("order")
            if isinstance(order, list):
                current_order = [str(item) for item in order]
        except Exception:
            current_order = None

    m = _TOML_ORDER_RE.search(text)
    if not m:
        if current_order and current_order[0] == "usmc":
            return text, False
        addition = '\n[backend]\norder = ["usmc", "gardener", "files"]\n'
        return text.rstrip() + "\n" + addition, True

    if current_order is None:
        raw_items = re.findall(r"['\"]([^'\"]+)['\"]", m.group(2))
        current_order = raw_items

    if current_order and current_order[0] == "usmc":
        return text, False

    new_order = ["usmc"] + [x for x in current_order if x != "usmc"]
    formatted = "order = [" + ", ".join(f'"{x}"' for x in new_order) + "]"
    updated = text[: m.start(2)] + formatted + text[m.end(2) :]
    return updated, True


def _seed_existing_indexes(client: USMCClient) -> Tuple[set, set]:
    existing_keys = set()
    existing_digests = set()
    for lesson in client.get_lessons(limit=100000):
        sk = lesson.get("source_key")
        ek = lesson.get("episode_key")
        if sk and ek:
            existing_keys.add((sk, ek))
        existing_digests.add(_normalized_digest(lesson.get("solution", "")))
        if lesson.get("source_hash"):
            existing_digests.add(f"hash:{lesson['source_hash']}")
    return existing_keys, existing_digests


def _import_markdown_entry(
    client: Optional[USMCClient],
    *,
    agent_tag: str,
    source_key: str,
    title: str,
    body: str,
    category: str = "general",
    user_preference: bool = False,
    policy_relevant: bool = False,
    apply: bool,
    seen_keys: set,
    seen_digests: set,
    summary: Dict,
) -> None:
    stripped = _strip_usmc_blocks(body)
    if not stripped:
        summary["skipped_empty"] += 1
        return
    secret_cat = _detect_secret_category(stripped)
    if secret_cat:
        summary["skipped_secrets"] += 1
        summary["warnings"].append(f"{source_key}: [REDACTED:{secret_cat}]")
        return

    raw_sha = _content_sha256(stripped)
    episode_key = raw_sha[:32]
    norm_digest = _normalized_digest(stripped)
    if (source_key, episode_key) in seen_keys:
        summary["skipped_existing"] += 1
        return
    if f"hash:{raw_sha}" in seen_digests or norm_digest in seen_digests:
        summary["skipped_duplicates"] += 1
        return

    seen_keys.add((source_key, episode_key))
    seen_digests.add(norm_digest)
    seen_digests.add(f"hash:{raw_sha}")

    if not apply or client is None:
        summary["would_import"] += 1
        return

    res = client.add_lesson(
        title=title[:200],
        problem=f"Importiert aus {agent_tag} ({source_key})",
        solution=stripped[:4000],
        severity="medium",
        category=category,
        source_kind="import",
        source_key=source_key,
        episode_key=episode_key,
        source_hash=raw_sha,
        editorial_status="review",
        evidence_class="unknown",
        privacy_scope="private",
        weight=NEW_LESSON_INITIAL_WEIGHT,
        user_preference=user_preference or None,
        policy_relevant=policy_relevant or None,
    )
    if res.get("created"):
        summary["imported"] += 1
    else:
        summary["skipped_existing"] += 1


def _choose_claude_rule_path(home: Path) -> Path:
    claude_dir_rule = home / ".claude" / "CLAUDE.md"
    if claude_dir_rule.is_file():
        return claude_dir_rule
    home_rule = home / "CLAUDE.md"
    if home_rule.is_file():
        return home_rule
    return claude_dir_rule


def _choose_gemini_rule_path(home: Path) -> Path:
    dot_rule = home / ".gemini" / "GEMINI.md"
    if dot_rule.is_file():
        return dot_rule
    home_rule = home / "GEMINI.md"
    if home_rule.is_file():
        return home_rule
    return dot_rule


def run_setup(
    *,
    home_dir: Optional[Path] = None,
    db_path: Optional[str] = None,
    agent_id: str = "setup",
    agents: Optional[Iterable[str]] = None,
    apply: bool = False,
    check: bool = False,
) -> Dict:
    """Inspect, preview (dry-run), or apply USMC memory redirection across agents."""
    home = Path(home_dir).expanduser() if home_dir is not None else Path.home()
    selected = tuple(dict.fromkeys(a.strip().lower() for a in (agents or SUPPORTED_AGENTS) if a.strip()))
    for a in selected:
        if a not in SUPPORTED_AGENTS:
            raise ValueError(f"Unbekannter Agent: {a!r} (erlaubt: {', '.join(SUPPORTED_AGENTS)})")

    mode = "check" if check else ("apply" if apply else "dry-run")
    resolved_db = Path(db_path).expanduser() if db_path else (home / ".usmc" / "usmc_memory.db")
    client = USMCClient(db_path=str(resolved_db), agent_id=agent_id) if (mode == "apply" or resolved_db.is_file()) else None
    seen_keys: set = set()
    seen_digests: set = set()
    if client is not None:
        seen_keys, seen_digests = _seed_existing_indexes(client)

    report: Dict = {
        "mode": mode,
        "home": str(home),
        "db_path": str(client.db_path) if client is not None else str(resolved_db),
        "import": {
            "imported": 0,
            "would_import": 0,
            "skipped_existing": 0,
            "skipped_duplicates": 0,
            "skipped_secrets": 0,
            "skipped_empty": 0,
            "skipped_private_silos": [],
            "warnings": [],
        },
        "files": [],
        "agents": {},
    }
    imp = report["import"]

    # 1. Claude Code
    if "claude" in selected:
        projects_dir = home / ".claude" / "projects"
        home_slug = _home_slug(home)
        silos_scanned = 0
        non_private_silos: List[Path] = []
        if projects_dir.is_dir():
            for silo in sorted(p for p in projects_dir.iterdir() if p.is_dir()):
                is_priv, reason = _is_private_silo(silo, home_slug)
                if is_priv:
                    imp["skipped_private_silos"].append({"silo": silo.name, "reason": reason})
                    continue
                silos_scanned += 1
                non_private_silos.append(silo)
                mem_dir = silo / "memory"
                if not mem_dir.is_dir():
                    continue
                md_files = sorted(mem_dir.glob("*.md"))
                non_index = [p for p in md_files if p.name.upper() != "MEMORY.MD"]
                candidates = non_index if non_index else md_files
                for md in candidates:
                    if not check:
                        raw = md.read_text(encoding="utf-8", errors="replace")
                        meta, body = _parse_frontmatter(raw)
                        entry_type = meta.get("type", "").lower()
                        cat = entry_type if entry_type in {"user", "feedback", "project", "reference"} else "general"
                        title = meta.get("name") or f"claude/{silo.name}/{md.stem}"
                        _import_markdown_entry(
                            client,
                            agent_tag="Claude Code",
                            source_key=f"claude:{silo.name}/{md.name}",
                            title=title,
                            body=body,
                            category=cat,
                            user_preference=(entry_type == "user"),
                            policy_relevant=(entry_type == "feedback"),
                            apply=(mode == "apply"),
                            seen_keys=seen_keys,
                            seen_digests=seen_digests,
                            summary=imp,
                        )
                idx_file = mem_dir / "MEMORY.md"
                if idx_file.is_file() and not check:
                    old_idx = idx_file.read_text(encoding="utf-8", errors="replace")
                    new_idx = _upsert_block(old_idx, _MEMORY_INDEX_BLOCK, _INDEX_START, _INDEX_END, prepend=True)
                    report["files"].append(_backup_and_write(idx_file, new_idx, _INDEX_START, apply=(mode == "apply")))

        rule_path = _choose_claude_rule_path(home)
        claude_settings = home / ".claude" / "settings.json"
        auto_mem_set = False
        if claude_settings.is_file():
            try:
                auto_mem_set = "autoMemoryDirectory" in json.loads(claude_settings.read_text(encoding="utf-8"))
            except Exception:
                auto_mem_set = False
        if (projects_dir.is_dir() or rule_path.is_file()) and not check:
            old_rule = rule_path.read_text(encoding="utf-8", errors="replace") if rule_path.is_file() else ""
            new_rule = _upsert_block(old_rule, _CLAUDE_RULE_BLOCK, _SETUP_START, _SETUP_END)
            report["files"].append(_backup_and_write(rule_path, new_rule, _SETUP_START, apply=(mode == "apply")))

        rule_has_pointer = rule_path.is_file() and _SETUP_START in rule_path.read_text(encoding="utf-8", errors="replace")
        index_has_pointer = any(
            (s / "memory" / "MEMORY.md").is_file()
            and _INDEX_START in (s / "memory" / "MEMORY.md").read_text(encoding="utf-8", errors="replace")
            for s in non_private_silos
        )
        report["agents"]["claude"] = {
            "detected": projects_dir.is_dir() or rule_path.is_file(),
            "silos_eligible": silos_scanned,
            "rule_path": str(rule_path),
            "rule_pointer": rule_has_pointer,
            "memory_index_pointer": index_has_pointer,
            "autoMemoryDirectory_untouched": not auto_mem_set,
        }

    # 2. Codex
    if "codex" in selected:
        codex_dir = home / ".codex"
        mem_dir = codex_dir / "memories"
        if mem_dir.is_dir() and not check:
            for fname in ("MEMORY.md", "memory_summary.md"):
                fpath = mem_dir / fname
                if not fpath.is_file():
                    continue
                raw = fpath.read_text(encoding="utf-8", errors="replace")
                _import_markdown_entry(
                    client,
                    agent_tag="Codex",
                    source_key=f"codex:memories/{fname}",
                    title=f"codex/{fpath.stem}",
                    body=raw,
                    category="general",
                    apply=(mode == "apply"),
                    seen_keys=seen_keys,
                    seen_digests=seen_digests,
                    summary=imp,
                )

        hooker_toml = codex_dir / "memoryhooker.toml"
        usmc_first = False
        if hooker_toml.is_file():
            raw_toml = hooker_toml.read_text(encoding="utf-8", errors="replace")
            updated_toml, changed = _rewrite_memoryhooker_toml(raw_toml)
            if not check and changed:
                report["files"].append(_backup_and_write(hooker_toml, updated_toml, '"usmc"', apply=(mode == "apply")))
            after_toml = updated_toml if (mode == "apply" and changed) else raw_toml
            usmc_first = not _rewrite_memoryhooker_toml(after_toml)[1]

        gpt_md = codex_dir / "GPT.md"
        if gpt_md.is_file() and not check:
            old_gpt = gpt_md.read_text(encoding="utf-8", errors="replace")
            new_gpt = _upsert_block(old_gpt, _CODEX_RULE_BLOCK, _SETUP_START, _SETUP_END)
            report["files"].append(_backup_and_write(gpt_md, new_gpt, _SETUP_START, apply=(mode == "apply")))

        report["agents"]["codex"] = {
            "detected": codex_dir.is_dir(),
            "memoryhooker_toml": str(hooker_toml) if hooker_toml.is_file() else None,
            "usmc_first_in_order": usmc_first,
            "gpt_md_pointer": gpt_md.is_file() and _SETUP_START in gpt_md.read_text(encoding="utf-8", errors="replace"),
        }

    # 3. Gemini / Antigravity
    if "gemini" in selected:
        gem_dir = home / ".gemini"
        if gem_dir.is_dir() and not check:
            import_candidates: List[Path] = []
            for fname in ("MEMORY.md", "memory.md", "memory.txt"):
                p = gem_dir / fname
                if p.is_file() and not any(p.samefile(existing) for existing in import_candidates):
                    import_candidates.append(p)
            sub_mem = gem_dir / "memory"
            if sub_mem.is_dir():
                import_candidates.extend(sorted(sub_mem.glob("*.md")))
            for cand in import_candidates:
                if cand.name.upper() == "AUTOMATIONS-MEMORY.MD" or cand.name.endswith("_automation_memory.json"):
                    continue
                raw = cand.read_text(encoding="utf-8", errors="replace")
                rel = cand.relative_to(gem_dir).as_posix()
                _import_markdown_entry(
                    client,
                    agent_tag="Gemini",
                    source_key=f"gemini:{rel}",
                    title=f"gemini/{cand.stem}",
                    body=raw,
                    category="general",
                    apply=(mode == "apply"),
                    seen_keys=seen_keys,
                    seen_digests=seen_digests,
                    summary=imp,
                )
            gem_idx = gem_dir / "MEMORY.md"
            if gem_idx.is_file():
                old_gidx = gem_idx.read_text(encoding="utf-8", errors="replace")
                new_gidx = _upsert_block(old_gidx, _MEMORY_INDEX_BLOCK, _INDEX_START, _INDEX_END, prepend=True)
                report["files"].append(_backup_and_write(gem_idx, new_gidx, _INDEX_START, apply=(mode == "apply")))

        gem_rule = _choose_gemini_rule_path(home)
        if (gem_dir.is_dir() or gem_rule.is_file()) and not check:
            old_gem = gem_rule.read_text(encoding="utf-8", errors="replace") if gem_rule.is_file() else ""
            new_gem = _upsert_block(old_gem, _GEMINI_RULE_BLOCK, _SETUP_START, _SETUP_END)
            report["files"].append(_backup_and_write(gem_rule, new_gem, _SETUP_START, apply=(mode == "apply")))

        report["agents"]["gemini"] = {
            "detected": gem_dir.is_dir() or gem_rule.is_file(),
            "rule_path": str(gem_rule),
            "rule_pointer": gem_rule.is_file() and _SETUP_START in gem_rule.read_text(encoding="utf-8", errors="replace"),
            "hooks_untouched": True,
        }

    # 4. Kimi
    if "kimi" in selected:
        kimi_dir = home / ".kimi-code"
        kimi_hooker = kimi_dir / "memoryhooker.toml"
        kimi_cfg = kimi_dir / "config.toml"
        usmc_first = False
        if kimi_hooker.is_file():
            raw_ktoml = kimi_hooker.read_text(encoding="utf-8", errors="replace")
            updated_ktoml, changed = _rewrite_memoryhooker_toml(raw_ktoml)
            if not check and changed:
                report["files"].append(_backup_and_write(kimi_hooker, updated_ktoml, '"usmc"', apply=(mode == "apply")))
            after_ktoml = updated_ktoml if (mode == "apply" and changed) else raw_ktoml
            usmc_first = not _rewrite_memoryhooker_toml(after_ktoml)[1]
        elif kimi_cfg.is_file():
            usmc_first = "memoryhooker" in kimi_cfg.read_text(encoding="utf-8", errors="replace").lower()
        report["agents"]["kimi"] = {
            "detected": kimi_dir.is_dir(),
            "config_path": str(kimi_hooker if kimi_hooker.is_file() else kimi_cfg) if kimi_dir.is_dir() else None,
            "memoryhooker_wired": usmc_first,
        }

    return report


def format_setup_report(report: Dict) -> str:
    """Render a concise German summary for CLI output."""
    lines = [
        f"USMC Setup ({report['mode']})",
        "====================",
        f"Home:   {report['home']}",
        f"DB:     {report['db_path']}",
    ]
    imp = report["import"]
    if report["mode"] != "check":
        lines.append(
            "Import: "
            f"{imp['imported']} importiert, {imp['would_import']} geplant, "
            f"{imp['skipped_existing']} bereits vorhanden, "
            f"{imp['skipped_duplicates']} inhaltliche Dubletten, "
            f"{imp['skipped_secrets']} Secret-Warnungen"
        )
    if imp["skipped_private_silos"]:
        names = ", ".join(s["silo"] for s in imp["skipped_private_silos"])
        lines.append(f"Private Silos übersprungen: {names}")
    for w in imp["warnings"]:
        lines.append(f"  [WARN] {w}")
    for name, info in report["agents"].items():
        lines.append(f"Agent {name}: {json.dumps(info, ensure_ascii=False)}")
    for f in report["files"]:
        if f["action"] != "unchanged":
            bak = f" (Backup: {f['backup']})" if f["backup"] else ""
            lines.append(f"  [{f['action']}] {f['path']}{bak} [readback={f['readback']}]")
    return "\n".join(lines)
