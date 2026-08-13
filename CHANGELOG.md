# Changelog

All notable changes to USMC are documented here.

## 0.2.1 - 2026-08-13

`working`, `facts` and `lessons` can be searched instead of only scrolled.

- **New filters.** `working` gained `--tags`, `--tags-all`, `--agent` and `--grep`;
  `facts` and `lessons` gained `--agent` and `--grep`. The same arguments exist on
  `USMCClient.get_working/get_facts/get_lessons` and on the high-level `api.working/facts/lessons`,
  appended to the existing signatures so positional callers are unaffected. Read-only: no schema
  change, no new index, no change to output formats or JSON keys.
  - `--grep` covers `content` for working notes, `key` and `value` for facts, and
    `title`, `problem` and `solution` for lessons.
  - `--tags` exists on `working` only; it is the sole table with a tags column.
- **Filters are applied in the WHERE clause, before `LIMIT`.** This is the point of the change:
  filtering after the fetch would reproduce the reported bug, where the ten most recent notes are
  all from one busy loop and a search for anything else comes back empty.
- **Tag matching is delimiter-anchored.** The column is compared as `,a,b,` against `,<tag>,`, so
  `--tags rh` no longer matches `research` or `rhythm`. Spacing is normalized, so `a,b` and `a, b`
  behave identically, and rows without tags never match a tag filter.
- **`%` and `_` in a `--grep` term are escaped** and therefore literal, not LIKE wildcards.
- **The subcommand `--agent` is a filter, not an identity.** It uses its own destination, so
  `usmc --agent writer working --agent other` keeps `writer` as the writing identity and filters
  for `other`. A regression test asserts exactly this, because argparse would otherwise silently
  overwrite the global option with the subparser default.
- Empty result messages now name the active filters, so a filter typo is visible instead of
  looking like an empty database. **With `--json` an empty result prints `[]`** rather than that
  German sentence: filtering makes "no hits" the normal case, and the caller who filters
  programmatically is the one whose parser would break on prose.
- Documented in `README.md` and `README_de.md`, including the search convention: USMC carries
  process state, subject-matter status lives in the canonical registers, and the first tag of a
  note names its pipeline.
- Test suite grew from 61 to 96 tests.

Reported as ticket T-20260813-90: a model searching for store entries found nothing because
`usmc working` offered no filter beyond `--limit` and the list was dominated by research notes.

## Unreleased

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
