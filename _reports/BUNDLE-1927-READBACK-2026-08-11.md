# TASKPLAN Readback — bundle 1927 — 2026-08-11

## Fresh local evidence

- Repository: `C:\_Local_DEV\repos\usmc`
- Local `HEAD`: `fd77cca` (`main`); the worktree's only pre-existing dirty
  tracked file was `TODO.md` and was not modified.
- `python -m pytest -q`: **61 passed, 15 subtests passed**.
- `python -m compileall -q usmc tests`: passed.
- `ruff check .`: passed.
- `python -m usmc.cli --version`: `usmc 0.1.0`; `--help` rendered normally;
  `usmc.RUNTIME_LANGUAGE` is `de`.
- `python -m build --no-isolation`: sdist and wheel for `usmc-0.1.0` built.

## Cross-file synchronization

- `llms.txt` now has `Last-checked: 2026-08-11` and the same 61-test/15-subtest
  receipt.
- README EN/DE now expose the dated verification snapshot and retain the
  matching 61-test badges and German runtime-language contract.
- `CHANGELOG.md` records the current evidence under `[Unreleased]`.
- `pyproject.toml` remains dynamically versioned from `usmc.__version__`,
  requires Python 3.10+, and advertises classifiers 3.10–3.14.
- `ellmos-module.v2.json` remains `active`/`public-candidate` with the local
  directory as source of truth and the canonical GitHub repository URL.
- Historical audit entries in `TODO.md` (2026-06-04/06-12) and its existing
  uncommitted TASKWRITER section are foreign state; they were read and left
  unchanged rather than overwritten.

## Git, CI, and release boundary

- Local tracking state was `main...origin/main [ahead 3]` with tracking ref
  `origin/main=7d3270a`; a read-only `git ls-remote` showed live remote main
  `0a89e9ae773127c5da64a3862d9a424061abaaf8` and no tag refs.
- Remote workflow run
  [31243843416](https://github.com/ellmos-ai/usmc/actions/runs/31243843416)
  is green for remote SHA `0a89e9a…` on Python 3.10–3.14, but it does not
  certify local `fd77cca`.
- No push, tag, public release, or other GitHub-side mutation was performed;
  publication remains a maintainer-controlled gate.
