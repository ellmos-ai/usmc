# Changelog

All notable changes to USMC are documented here.

## Unreleased

- **Internal Docstrings Clean Translation to English (2026-09-29):**
  - **Internal Codebase Consistency:** Standardized internal module and method docstrings across `usmc/client.py`, `usmc/api.py`, `usmc/cli.py`, and `usmc/schema.py` to clean, idiomatically concise English aligned with public repository standards.
  - **Backward-Compatible Runtime Preserved:** Retained German prompt headers and messages in `generate_context()` and CLI output for backwards compatibility (`usmc.RUNTIME_LANGUAGE = "de"`).
  - **Full Test Suite Verification:** All 177 tests and 122 subtests green, 0 ruff errors.
- **Developer Dependencies & Clean Test Imports (2026-09-28):**
  - **`[project.optional-dependencies]` in `pyproject.toml`:** Declared `test = ["pytest>=7.0", "ruff>=0.1.0"]` enabling standardized, reproducible developer installs via `pip install -e .[test]`.
  - **Clean Test Suite Imports:** Removed redundant `sys.path.insert(0, ...)` workarounds from `tests/test_api.py`, `tests/test_cli.py`, `tests/test_client.py`, and `tests/test_paths.py` in favor of standard editable installs and `pytest.ini_options.pythonpath = "."`.
  - **Clean Ruff Linting:** Passed with 0 errors across codebase.
- **Discoverability, Visual Architecture, Level 1 SBOM, 18-Point Navigation Parity & PEP 621 Saturation (Pfad B, 2026-09-28):**
  - **Version Freeze Compliance (T-20260920-167562623):** Maintained frozen version `0.3.0` across package manifests and metadata tests.
  - **PEP 621 Metadata Saturation (`pyproject.toml`):**
    - Saturated `keywords` to maximum 20/20 matching remote GitHub repository topics (`agent-framework`, `agent-memory`, `ai-agent`, `automation`, `cross-agent`, `cross-agent-memory`, `llm`, `llm-agents`, `llm-memory`, `local-ai`, `local-first`, `memory`, `open-source`, `prompt-context`, `python`, `python-cli`, `shared-memory`, `sqlite`, `sqlite-memory`, `zero-dependency`).
    - Added dedicated plain-text companion URLs under `[project.urls]`: `Plain-Text Licenses`, `Third-Party Licenses (Text)`, and `Level 1 SBOM`.
  - **18-Point Trilingual Navigation Parity & Dual HTML Anchors:**
    - Expanded Quick Navigation architecture from 16 to 18 numbered points across English (`README.md`), German (`README_de.md`), and Spanish (`README_es.md`).
    - Implemented reciprocal dual HTML anchors (`<a id="sec-01"></a>` through `<a id="sec-18"></a>`) alongside human-readable IDs (`#key-features`, `#sec-01`, etc.) for seamless cross-linking and machine parsing.
    - Tagged target personas with explicit structured IDs (`[PERSONA-01]` through `[PERSONA-04]`).
  - **ASCII Four-View Architectural Topology Projection (Section 6):**
    - Added dedicated four-view ASCII topology diagram projection across all three README variants: View 1 (Client Runtimes & Agent Drivers), View 2 (USMC Core Engine & Memory Primitives), View 3 (ACID WAL Persistence & Concurrency), and View 4 (Governance, Security & Ecosystem Perimeter).
  - **Quality Gates, Contract Testing & CI Guidance (Section 16):**
    - Added dedicated Section 16 documenting offline testing commands (`pytest`, `ruff check .`, `compileall`, `git diff --check`), baseline pass rates (177 passed, 122 subtests), and CI concurrency settings.
  - **Level 1 SBOM Software Inventory & Transparency (`THIRD_PARTY_LICENSES.txt` & `THIRD_PARTY_LICENSES.md`):**
    - Re-audited software inventory Stand 2026-09-28 certifying unprivileged user-mode execution (`RunAsInvoker`), 100% Python Standard Library runtime, Zero-Copyleft licensing, and invariant matrix cross-references.
  - **Statutory Legal Notice & Security SLA (Section 18):**
    - Documented German statutory liability limitation pursuant to Section 521 BGB (§ 521 BGB Gefälligkeitsrecht for unpaid open-source contributions) and reiterated 48h Security Response SLA.
  - **Machine-Readable LLM Context (`llms.txt`):**
    - Updated verified date to `2026-09-28`, refreshed baseline test metrics (177 passed, 122 subtests), Level 1 SBOM companion references, and § 521 BGB notice.
- **Lesson contract v2 joins the shared BACH/OCEAN memory contract (S2a, T-20260920-823767362):** union contract version 2. `memory_lessons` carries the lesson-v2 columns (provenance, idempotency, feedback counters, delivery), and `memory_lesson_feedback`, `memory_lesson_delivery_batches` and `memory_lesson_deliveries` are part of the pinned contract. `apply_union()` now moves `usmc_lessons` and its three side tables with unchanged IDs (children dropped before parents, foreign keys intact) and upgrades a database on contract v1 in place; rows on both sides abort without mutation. The client addresses every lesson table through `_table()`, so keyed lessons, editorial status, feedback and delivery (including SessionStart delivery) work in union mode; the policy lock `LessonV2UnionUnsupportedError` is removed. `memory_union.py` is self-contained again (no package imports) so BACH can vendor it byte-identically. Opt-in stays `USMC_MEMORY_UNION=1`; no live database is switched by this change.

## 0.3.0 - 2026-09-26

- **Repository Hygiene, CI Lifecycle Workflows, Lock Defense & NOTICE Attribution (Pfad A, 2026-09-26):**
  - **Version Freeze Compliance (T-20260920-167562623):** Version `0.2.3` preserved unchanged across all manifests and code constants.
  - **Canonical Open-Source NOTICE Attribution:** Added root `NOTICE` attribution file documenting copyright (c) 2026 Lukas Geiger, ellmos-ai infrastructure, open-bricks umbrella ecosystem, and cross-references to `LICENSE`, `THIRD_PARTY_LICENSES.md`, and `THIRD_PARTY_LICENSES.txt`.
  - **Level 1 SBOM Software Inventory (`THIRD_PARTY_LICENSES.txt` & `THIRD_PARTY_LICENSES.md`):** Re-audited software inventory Stand 2026-09-26, certifying unprivileged user-mode execution (`RunAsInvoker`), zero external runtime dependencies (`dependencies = []`), 100% Python Standard Library runtime, and full compliance with 10 runtime invariants (`INV-LOCAL-01` through `INV-SLA-10`).
  - **CI/CD Lifecycle Workflow Hardening:**
    - Hardened `.github/workflows/auto-assign.yml` with top-level concurrency (`cancel-in-progress: true`), `timeout-minutes: 5`, and least-privilege permissions (`issues: write`, `pull-requests: write`).
    - Hardened `.github/workflows/label-sync.yml` with top-level concurrency (`cancel-in-progress: true`) and `timeout-minutes: 5`.
  - **Multi-Host Cloud-Sync & Lock Defense (`.gitignore`):**
    - Reinforced canonical locks (`LOCK.user.*`, `LOCK.until.*`, `LOCK.condition.*`, `.automation-lock`, `LOCK.permissions.json`).
    - Added multi-host sync guard patterns (`*-IDEAPAD*`, `*_WORKSTATION*`, `*_WORKSTATION-LG*`, `*-WORKSTATION.*`, `*-WORKSTATION-LG.*`).
    - Added test & cache dirs (`.pytest_temp/`, `.pytest_tmp*/`, `.tox/`) and editor swap patterns (`Desktop.ini`, `*.swp`, `*.swo`).
  - **PEP 621 Standardisierung (`pyproject.toml`):**
    - Expanded `license-files` whitelist to include `NOTICE` and `THIRD_PARTY_LICENSES.txt`.
    - Added `Notice` URL to `[project.urls]`.
    - Hardened `[tool.pytest.ini_options]` with `norecursedirs` (`.pytest_temp`, `.hypothesis`, `.turbo`, `.tox`) and `addopts = "-ra -v --basetemp=.pytest_temp"`.
  - **Documentation & LLM Context Parity:**
    - Added `Attribution-NOTICE-blue.svg` badge and updated verified date to `2026-09-26` across `README.md`, `README_de.md`, and `README_es.md` while preserving all 16 navigation anchors.
    - Updated `llms.txt` Stand 2026-09-26 with links to `NOTICE` and `THIRD_PARTY_LICENSES.txt`.
  - **Contract Test Suite Expansion:**
    - Extended `tests/test_metadata.py` with `test_notice_attribution`, `test_level1_sbom_inventory`, auto-assign/label-sync workflow hardening tests, pyproject guardrails, and updated test badge synchronization (126 passed, 58 subtests).
    - Extended `tests/test_repository_hygiene.py` with canonical lock, IDEAPAD, and swap file ignore contract tests.
- **Shared BACH/OCEAN memory schema (S1, T-20260920-823767362):** new `usmc.memory_union` with the canonical DDL of the memory tables shared with BACH, a pinned PRAGMA contract (`memory_union.contract.json`), and an opt-in migration (`USMC_MEMORY_UNION=1`) from `usmc_*` to `memory_*` with a prior file backup, `usmc_*` read views, provenance triggers installed only after the copy, and fail-closed handling of unknown columns. The client writes to `memory_*` once the union is active; reads keep using `usmc_*`. Tests never open `~/.usmc` (`tests/conftest.py`).
- **Lesson contract v2 scoped to `usmc_*`, locked in union mode (T-20260922-668077756):** integrated the S3 lesson-v2 contract (see 0.2.1 below) onto the shared-schema branch. Lessons are not yet split into the shared schema at all: `usmc_lessons` keeps carrying every lesson row (v1 and v2 alike) regardless of union mode, and `memory_union.apply_union()` recognizes the known v2 columns and deliberately skips converting `usmc_lessons` (stays a real, writable table; facts/working/sessions still migrate normally) instead of aborting the whole migration — moving lessons into `memory_*` is a separate, not-yet-implemented step tracked as an S2 requirement of T-20260920-823767362. Only the v2 write/mutation surface (keyed `add_lesson()`, `set_lesson_editorial_status`, `record_lesson_feedback`, `deliver_lessons`, lesson delivery in `start_session()`) raises `LessonV2UnionUnsupportedError` on a union database — a policy lock, not a technical necessity, until lesson-v2 has its own BACH/OCEAN contract stage. **Reads stay unlocked in union mode:** `get_lessons()`, `get_lesson()`, and `generate_context()` (which calls `get_lessons()` internally) keep working unchanged, since `usmc_lessons` is always readable — an initial version locked these read paths too, which would have broken `usmc lessons`/`usmc context` and every SessionStart context hook after switching a database to union mode; this was caught in review before merge and fixed. The plain, unkeyed `add_lesson()` call is unaffected in either mode and, like every lesson write, lands on `usmc_lessons`.

## 0.2.3 - 2026-09-19

Turnusgemäßer Pfad B Discoverability-, Marketing-, Dokumentations- und Navigationslauf:

- **16-Point Navigation Architecture & Trilingual Parity**:
  - Implemented comprehensive 16-point Quick Navigation structure synchronized across English (`README.md`), German (`README_de.md`), and Spanish (`README_es.md`) with 100% mutual anchor parity.
  - Added dedicated top-level sections: Key Features, Target Personas & Discoverability, Comparative Matrix vs Alternatives, Governance & Runtime Invariants, Core Concepts & Primitives, Finding Things & Advanced Filtering, Multi-Agent Session Coordination, Sibling Ecosystem & Positioning, Third-Party Licenses & Transparency, and Security Policy.
- **Target Personas & SEO Discoverability Matrix**:
  - Formulated 4 distinct technical target personas:
    1. *Autonomous Multi-Agent Swarm Engineers (Claude Code, Antigravity/Gemini, Codex, BACH)*: Need zero-daemon, multi-agent SQLite shared memory with atomic WAL concurrency and cross-agent handoffs.
    2. *Local-First & Zero-Egress AI Systems Engineers*: Require 100% offline persistence, zero network egress, and strict file isolation in user home directories.
    3. *Desktop Application & MCP Tool Integrators (PySide6, Electron, MCP Servers)*: Need lightweight (<1 ms cold start), embeddable process-state memory primitive with zero background services.
    4. *Enterprise Security & Compliance Auditors*: Demand 100% Python Standard Library runtime, Zero-Copyleft guarantee (MIT/PSF-2.0 only), unprivileged user-mode execution (`RunAsInvoker`), and transparent 48h security SLA.
  - Structured high-intent trilingual keyword matrix (English, German, Spanish).
- **10-Dimension Comparative Matrix vs 4 Alternatives**:
  - Benchmarked `usmc` against Ad-Hoc JSON/Markdown Files, Central Cloud Redis/Vector DBs, Heavyweight Agent Memory Frameworks (Mem0, Zep, LangGraph Store), and Raw Ad-Hoc SQLite Scripts across 10 architectural criteria (Runtime Dependencies, Zero-Egress, Daemon Overhead, Multi-Agent Concurrency, Memory Primitives, Confidence Merging, Context Generation, In-Engine SQL Filtering, State Isolation, and Security SLA).
- **Governance & Runtime Invariants Alignment**:
  - Documented the 10 foundational invariants (`INV-LOCAL-01` through `INV-SLA-10`) in all three READMEs, harmonized with `THIRD_PARTY_LICENSES.md` and `MARKETING-LOG.txt`.
- **Third-Party Licenses & Software Inventory**:
  - Updated `THIRD_PARTY_LICENSES.md` audit to 2026-09-19, confirming 0 external runtime dependencies (`dependencies = []`), pure Python standard library core, unprivileged execution mode, and Zero-Copyleft license compliance.
- **Sibling Ecosystem & Community Cross-Linking**:
  - Added structured ecosystem table linking `usmc` (Tier 1) to `rinnsal` (Tier 2), `bach` (Tier 3), `skills`, `connectors`, `clutch`, `policy-registry`, `open-bricks`, and `dev-bricks/DevCenter`.
- **Automated Contract Test Suite Expansion**:
  - Extended `tests/test_metadata.py` with contract tests verifying 16-point navigation parity, target personas presence, comparative matrix presence, governance invariants table, sibling ecosystem links, test badge synchronization, and version parity.

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

- Added the backward-compatible lesson contract schema v2. Keyed lessons use a unique
  `(source_key, episode_key)` and retry-safe immutable intake semantics while the original unkeyed
  `add_lesson()` path remains append-only. The additive migration preserves v1 rows and supports
  mixed old/new clients without a destructive contract phase.
- Added provenance, editorial, evidence and privacy fields with a low `0.20` starting weight for
  keyed lessons. Helpful use, unhelpful use, independent repetition and delivery failure are
  stored as separate idempotent feedback signals.
- Added request-idempotent, synchronous lesson delivery for explicit context or selected IDs,
  including optional SessionStart integration. Delivery is capped at three approved/legacy,
  local/private, non-sensitive lessons and asks one short helpfulness question; there is no
  notification daemon.
- Added a pure direct-promotion policy surface. The product gate remains off and never publishes;
  user preferences, policy content, conflicts, sensitive sources, and skill/workflow mutation
  always require review.
- Added high-level API and CLI surfaces (`lesson-feedback`, `lesson-review`, `lesson-policy`,
  `lesson-deliver`, and optional `start` delivery flags) plus isolated migration, concurrent
  deduplication, rollback/retry, weighting, privacy/review and backward-compatibility tests.
- Hardened the v2 idempotency invariants after review: keyed lesson retries now require the full
  immutable intake payload; feedback keys are globally exactly-once; delivery retries replay the
  persisted batch; partial-v2 schemas repair all required named columns/indexes transactionally;
  and SessionStart commits or rolls back its session and delivery together.
- Corrected the immutable intake-hash boundary so legitimate editorial review and later weighting
  state cannot invalidate an original retry, including backfill from the pre-hash v2 schema.
- Added fail-closed keyed-row integrity checks before retry, promotion policy evaluation, new
  delivery and delivery replay. Immutable row tampering cannot be promoted, delivered or silently
  accepted as a new v2 hash baseline; mutable review, weighting and counter state remains valid.
- Corrected the PyPI statement in `README.md`, `README_de.md` and `llms.txt`: the name `usmc`
  is **not** reserved for this project. As of 2026-08-08 no project of that name exists on
  PyPI, so a PyPI package called `usmc` is not necessarily this one. Install from GitHub.
- Documented that the CLI messages, `--help` texts and `generate_context()` headings are
  currently German while the rest of the project is English, so the gap is visible instead
  of surprising users.
- Removed the internal pre-release audit file `TODO.md` from version control and added it to
  `.gitignore`; it is planning material, not repository content.
- Added `.gitattributes` (`* text=auto eol=lf`, binary assets excluded). The committed files
  were already LF, but nothing pinned that, so working copies drifted into mixed CRLF/LF.
- Rewrote the remaining German `.gitignore` comments in neutral English.
- Synchronized the maintained German README with the canonical English
  onboarding structure and restored byte-identical code and Mermaid examples.
- Technical hygiene: test the zero-dependency package on Python 3.14 in CI and
  advertise that supported target in the package classifiers.

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
