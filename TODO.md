# Pre-Release TODO: USMC

**Audit Date:** 2026-06-04
**Auditor:** Codex automation `ai-modules-care`
**Target Repo:** `ellmos-ai/usmc`

USMC is a standalone-capable shared-memory library and CLI. The local `.MODULES`
copy is still documented as OS-near, so release decisions should continue to
check whether `.MODULES/USMC` or a future `.OS` location is the source of truth.

## BLOCKER

- [x] **Secrets:** No secret patterns found by the Final Gate Check on 2026-06-04.
- [x] **Private Data:** No PII patterns found by the Final Gate Check on 2026-06-04.
- [x] **Hardcoded Paths:** No hardcoded personal paths found by the Final Gate Check on 2026-06-04.
- [x] **Database Files:** No `.db` files are tracked by Git; local `usmc_memory.db` remains ignored.
- [x] **.env Files:** No `.env` files are tracked by Git.
- [x] **BACH Internals:** No BACH-internal blocker documents found in the module root.
- [x] **.gitignore:** Minimum gate entries are present.
- [x] **LICENSE:** MIT license file present.
- [x] **README.md:** English README present.

## HIGH PRIORITY

- [ ] Decide the long-term source of truth for USMC against `.AI/.OS` and BACH's `usmc_bridge.py`.
- [x] Translate or intentionally document the remaining German module docstring text in `usmc/__init__.py`.
- [x] Check repository URL consistency before a public release; `SECURITY.md` now points to the `ellmos-ai/usmc` advisory URL used by the README.

## MEDIUM PRIORITY

- [x] Add `CHANGELOG.md` before the next tagged release.
- [ ] Add a documented build/package smoke check once PyPI publishing is planned.
- [ ] Decide whether the local runtime database should move under `data/` for clearer runtime-state separation.

## LOW PRIORITY

- [ ] Add optional examples for cross-agent handoff workflows.
- [ ] Add benchmark notes for large memory tables if USMC becomes a shared backend for more agents.

## STATUS

| Category | Status | Notes |
|----------|--------|-------|
| Secrets | PASS | Final Gate Check found no secret patterns. |
| Private Data (PII) | PASS | Final Gate Check found no PII patterns. |
| .gitignore | PASS | Explicit `*.pyc`, `*.db`, `.env`, `.venv/`, IDE and `data/` entries present. |
| Language (English) | PASS | English README and public package docstring are present. |
| BACH Internals | PASS | No BACH-internal blocker documents found. |
| Database Files | PASS | No `.db` files tracked; local runtime DB is ignored. |
| README.md | PASS | English README present. |
| LICENSE | PASS | MIT license present. |
| Tests | PASS | `python -m pytest -q` passed 50 tests on 2026-06-05. |
| **Overall** | **READY FOR GATE** | Gate passes locally; source-of-truth and PyPI packaging polish remain follow-ups. |

**Audit Date:** 2026-06-04
**Gate Check Exit Code:** `0`

---

*Based on `MODULES/_templates/TODO_TEMPLATE.md`; scoped for the 2026-06-04 automation check.*
