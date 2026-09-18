# Changelog

All notable changes to USMC are documented here.

## 0.2.2 - 2026-09-18

Turnusgemäßer Pfad A Wartungs-, Hygiene-, CI-Härtungs- und Versionslauf:

- **CI/CD Workflow Automation & Hardening**:
  - Upgraded `.github/workflows/stale.yml` to `actions/stale@v9`, added `timeout-minutes: 10`, `concurrency: group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true`, and least-privilege permissions (`issues: write`, `pull-requests: write`).
  - Hardened `.github/workflows/welcome.yml` with `timeout-minutes: 5` and concurrency `cancel-in-progress: true`.
  - Hardened `.github/workflows/ci.yml` with `timeout-minutes: 15`, concurrency `cancel-in-progress: true`, and automated `ruff check .` lint enforcement.
- **Multi-Host Cloud-Sync & Lock Defense (`.gitignore`)**:
  - Hardened `.gitignore` against synchronization conflict copies (`*conflicted copy*`, `* (Kopie)*`, `* (Copy)*`, `*-ASUS*`, `*-ASUS-GEI*`, `*-LAPTOP*`, `*-WORKSTATION*`, `*-WORKSTATION-LG*`, `*-Mac Studio*`, `*-MacBook*`).
  - Added multi-agent lock patterns (`LOCK*`, `LOCK.user.*`, `LOCK.until.*`, `LOCK.condition.*`, `LOCK.permissions.json`, `uv.lock`, with preservation of `!package-lock.json`).
  - Added test caches and build artifacts (`.hypothesis/`, `.nyc_output/`, `node_modules/`, `*.orig`, `*.rej`, `*.tmp`, `*.bak`).
- **Packaging & Pytest Guardrails (`pyproject.toml`)**:
  - Standardized `license-files = ["LICENSE", "THIRD_PARTY_LICENSES.md"]`.
  - Configured `[tool.pytest.ini_options]` with `minversion = "7.0"`, `norecursedirs = [".git", ".pytest_cache", "__pycache__", "build", "dist"]`, and `addopts = "-ra -v"`.
  - Added standardized PEP 621 URLs for `Changelog`, `Security`, `Parent Organization`, and `Umbrella Ecosystem`.
  - Added `[tool.ruff]` and `[tool.ruff.lint]` configuration sections.
- **Third-Party License & SBOM Audit (`THIRD_PARTY_LICENSES.md`)**:
  - Stand 2026-09-18: Verified zero external runtime dependencies (`dependencies = []`, 100% Python standard library: `sqlite3`, `json`, `os`, `sys`, etc.).
  - Formal runtime invariant mapping (`INV-LOCAL-01` through `INV-SLA-10`).
  - Certified unprivileged user-mode execution (`RunAsInvoker`) and Zero-Copyleft guarantee (MIT / PSF-2.0 only).
- **Security Policy Hardening (`SECURITY.md`)**:
  - Upgraded to bilingual German/English policy with private vulnerability reporting link.
  - Committed to 48h initial response / 5 business days triage SLA and security contacts (`security@ellmos.ai`, `support@lukasgeiger.com`, `security@open-bricks.org`).
- **Local Maintenance Register (`MARKETING-LOG.txt`)**:
  - Created local technical hygiene and baseline discoverability log Stand 2026-09-18.
- **Synchronized LLM Context (`llms.txt`)**:
  - Updated `Last-checked` timestamp to `2026-09-18`, version to `0.2.2`, and verified test suite coverage.
- **Automated Contract & Hygiene Tests (`tests/test_metadata.py`, `tests/test_repository_hygiene.py`)**:
  - Added contract tests for CI workflow hardening (concurrency, timeouts, action versions), version consistency across files, `THIRD_PARTY_LICENSES.md` invariants, bilingual `SECURITY.md`, and multi-host conflict ignore rules.
- **Discoverability & Internationalization (Pfad B Integration)**:
  - Multi-agent interaction sequence diagram (`sequenceDiagram` with `autonumber` and strictly quoted labels).
  - Trilingual language switchers (`English · Deutsch · Español`) and full Spanish documentation (`README_es.md`).
  - Runtime language contract: human-readable API/CLI prose stays German (`de`) via `usmc.RUNTIME_LANGUAGE == "de"`.
  - Corrected PyPI statement in READMEs and `llms.txt` (name `usmc` is not claimed on PyPI).

## 0.2.1 - 2026-08-13

## 2026-07-27

- Technical hygiene & maintenance check: updated `llms.txt` verification timestamp to 2026-07-27, cleaned up untracked local OneDrive conflict files, and verified full test suite (61/61 passed).

## 2026-07-26

- Discoverability & SEO check (Path B): added GFM LLM note callouts (`> [!NOTE]`) to `README.md` and `README_de.md` clarifying the role of USMC as Tier 1 shared memory primitive in the ellmos AI ecosystem, updated `llms.txt` verification timestamp to 2026-07-26, verified test suite (61/61 passed), and updated marketing log.

## 2026-07-25

- Technical hygiene & maintenance check: added `[tool.pytest.ini_options]` in `pyproject.toml`
  with `pythonpath = "."`, verified test suite (61/61 passed), module `compileall`,
  and repository hygiene.

## 2026-07-22

- Technical hygiene & documentation maintenance: updated `llms.txt` `Last-checked`
  timestamp to 2026-07-22, verified test suite (61/61 passed), module compileall,
  and repository hygiene.

## 2026-07-12

- Security hygiene: expanded `.gitignore` for local env variants, token and
  credential files, recovery-code files, private keys/certificates, SQLite
  variants and OneDrive conflict copies.
- Added a repository hygiene regression test that checks sensitive local
  artifacts stay ignored while `.env.example` and `.env.sample` remain
  trackable.

## 2026-07-04

- **Changed (breaking): default database location is now per-system local.**
  Without an explicit `db_path`, `USMCClient`, the high-level `api` and the
  `usmc` CLI all resolve to `~/.usmc/usmc_memory.db` (override via the
  `USMC_DB` environment variable). Previously `USMCClient()` created
  `usmc_memory.db` in the current working directory. Introduced for the CLI
  in the 2026-06-28 local-first change; now unified in a single source of
  truth (`usmc.client.default_db_path`) used by client, api and CLI.
- Fixed: importing `usmc` no longer creates `~/.usmc` as a side effect —
  the directory is created lazily when a client actually connects.
- Fixed: SQLite connections now use a 5 s busy timeout (`timeout=5.0` +
  `PRAGMA busy_timeout`), reducing `database is locked` errors when several
  agents write in parallel.
- Added: public `USMCClient.delete_fact()`; `api.forget()` now delegates to
  it instead of touching private client internals.
- Fixed: `usmc --version` reads `usmc.__version__`; package version is now
  single-sourced via `[tool.setuptools.dynamic]` in `pyproject.toml`.
- Fixed: build requirement raised to `setuptools>=77` (needed for the SPDX
  `license = "MIT"` expression, PEP 639); dropped the obsolete `wheel`
  build requirement.
- Docs: corrected the multi-agent README example (category `"repo"` is not
  a valid category and raised `ValueError`; confidence merging is per agent,
  not cross-agent) and documented the default database location in both
  READMEs.

## 2026-06-11

- Add `## Audience` and `## Search Phrases` sections to `llms.txt` for LLM-crawler standard compliance.
- Move `Last-checked` inline marker to proper `## Last-checked:` header at top of `llms.txt`.

## 2026-06-10

- Add "Start Here" quick-reference table to README for faster onboarding.
- Add `last-checked` date to `llms.txt` for LLM crawler freshness signalling.

## 2026-06-05

- Keep runtime artifacts out of Git with explicit `*.pyc` and `data/` ignore rules.
- Add the pre-release `TODO.md` gate summary for source-of-truth, release and packaging follow-ups.
- Point the security advisory link to `ellmos-ai/usmc`.
- Translate the package-level docstring to English for public API consistency.
- Refresh the test workflow to `actions/checkout@v6` and `actions/setup-python@v6`.

## 2026-05-30

- Sharpen README, README_de, package metadata and `llms.txt` for ellmos USMC discoverability.
- Add the `USMC tests` GitHub Actions workflow for Python 3.10 through 3.13.
- Clarify that USMC is the United Shared Memory Client and not related to the United States Marine Corps.
