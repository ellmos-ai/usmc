# Changelog

All notable changes to USMC are documented here.

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
