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
      (2026-07-04: `pip install --dry-run .` + `pip install --user .` + CLI-Smoke
      erfolgreich durchgeführt — formale Doku des Checks steht noch aus.)
- [x] Decide whether the local runtime database should move under `data/` for
      clearer runtime-state separation. (Entschieden + umgesetzt 2026-06-28/2026-07-04:
      Default ist jetzt per-System `~/.usmc/usmc_memory.db`, Override `USMC_DB` —
      Runtime-State liegt damit ganz außerhalb des Repos.)

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

---

## Audit 2026-06-12

**Auditor:** Claude (Software-Audit-Agent)
**Stand:** Git-Arbeitsbaum sauber (`git status` leer), HEAD `dd78610`. 50 Tests vorhanden (README-Angabe stimmt aktuell). Keine Secrets, keine harten persönlichen Pfade, kein `.db`-Tracking gefunden — Gate-Befunde vom 2026-06-04 weiterhin gültig.

### Fixes

- [x] **(hoch, erledigt 2026-07-04: Doku-Fix in beiden READMEs, Beispiel-Kategorie
      `repo`→`project` da `repo` ValueError warf)** Doku widerspricht Code beim Cross-Agent-Confidence-Merge: `README.md:126` und `README_de.md:114` behaupten „When two agents write the same fact, the higher-confidence value wins". Tatsächlich gilt der Confidence-Merge in `usmc/client.py:135-158` nur **pro Agent** (UNIQUE-Constraint `(agent_id, category, key)` in `usmc/schema.py:30`); zwei Agenten erzeugen zwei getrennte Zeilen — bestätigt durch `tests/test_client.py::test_multi_agent_facts` (erwartet 2 Zeilen). Entweder README-Abschnitt „Multi-Agent Example" korrigieren (Merge ist per-Agent, `get_facts` sortiert nur nach Confidence) oder Cross-Agent-Merge implementieren. Doku-Fix ist der kleinere Eingriff.
- [x] **(mittel, erledigt 2026-07-04: `timeout=5.0` + `PRAGMA busy_timeout=5000`)** Kein busy_timeout bei SQLite-Verbindungen: `usmc/client.py:76-86` öffnet pro Operation eine neue Verbindung ohne `timeout`-Parameter/`PRAGMA busy_timeout`. Bei parallelem Schreiben mehrerer Agenten (Kernanwendungsfall!) drohen trotz WAL „database is locked"-Fehler. `sqlite3.connect(str(self.db_path), timeout=5.0)` oder `PRAGMA busy_timeout` setzen.
- [ ] **(mittel) Deutsche Laufzeit-Ausgaben im englischen Public-Repo:** `generate_context()` liefert deutsche Überschriften („## Aktuelle Notizen", „## Sichere Fakten", „Kein Kontext verfuegbar." — `usmc/client.py:527-548`), und sämtliche CLI-Meldungen/Hilfetexte in `usmc/cli.py` sind deutsch (z. B. „Fakt gespeichert", „Keine Fakten gefunden", argparse-Hilfen). Für `ellmos-ai/usmc` auf Englisch umstellen oder bewusst dokumentieren. Achtung: `tests/test_client.py:162,170-172` prüfen die deutschen Strings — mit anpassen.
- [x] **(mittel, überholt: Datei nicht mehr vorhanden; Default seit feb0a30/2026-07-04 `~/.usmc`)** Laufzeit-DB `usmc_memory.db` liegt im Repo-Root: 69 KB, Stand 2026-02-28, OneDrive-synchronisiert. Sie ist gitignoriert (nicht getrackt), gehört aber nicht in den Projektordner — löschen oder nach `data/` verschieben (deckt sich mit dem offenen MEDIUM-Eintrag vom 2026-06-04).
- [x] **(niedrig, erledigt 2026-07-04: Single Source `usmc.__version__` via `dynamic = ["version"]`, CLI importiert)** Version dreifach gepflegt: `pyproject.toml:7` (`0.1.0`), `usmc/__init__.py:33` (`__version__`) und hartkodiert in `usmc/cli.py:226` (`version='usmc 0.1.0'`). CLI sollte `from . import __version__` nutzen; ideal eine Quelle (z. B. `dynamic = ["version"]`).
- [x] **(niedrig, erledigt 2026-07-04: `USMCClient.delete_fact()` öffentlich, `forget()` delegiert)** `usmc/api.py:237`: ungenutzter `import sqlite3` in `forget()`; außerdem greift `forget()` auf die privaten `client._get_conn()/_close_conn()` zu. Besser `delete_fact()` als öffentliche Methode in `USMCClient` ergänzen und `forget()` darauf umstellen.
- [ ] **(niedrig) Interne Docstrings/Kommentare weiterhin deutsch:** `usmc/client.py`, `usmc/api.py`, `usmc/cli.py`, `usmc/schema.py` (Modul-Docstrings, Methoden-Docs). Der HIGH-Eintrag vom 2026-06-04 hat nur `usmc/__init__.py` übersetzt. Für Public-Repo-Konsistenz übersetzen oder als bewusste Entscheidung dokumentieren.

### Upgrades

- [x] **(mittel, erledigt 2026-07-04: `setuptools>=77`, `wheel` entfernt; per pip-Metadaten-Build + Install verifiziert)** `pyproject.toml:2` Build-Anforderung anheben: Der SPDX-Lizenzausdruck `license = "MIT"` (Zeile 10, PEP 639) erfordert setuptools >= 77; deklariert ist nur `setuptools>=68.0` — mit altem setuptools schlägt der Build fehl. Auf `setuptools>=77` anheben; `"wheel"` aus `requires` entfernen (wird von modernem setuptools nicht mehr benötigt).
- [ ] **(niedrig) CI-Matrix erweitern:** `.github/workflows/ci.yml` testet Python 3.10-3.13; Python 3.14 ergänzen (und Classifier in `pyproject.toml` nachziehen).
- [ ] **(niedrig) Lint-Step in CI:** Kein Linter/Formatter konfiguriert. `ruff check` als zusätzlicher CI-Step wäre bei Zero-Dependency-Anspruch ein günstiger Qualitätsgewinn.
- [ ] **(niedrig) `tests/test_client.py:13` (analog `test_api.py`/`test_cli.py`):** `sys.path.insert`-Hack entfernen — CI installiert ohnehin per `pip install -e .`.
- [ ] **(niedrig) Optionales `[project.optional-dependencies]` dev/test-Extra** (pytest), damit `pip install -e .[test]` reproduzierbar ist statt Ad-hoc-Installation in CI.

### Änderungen

- [x] **(mittel, erledigt 2026-07-04: `build/`, `dist/`, `usmc.egg-info/`, `.pytest_cache/`, `__pycache__/` lokal gelöscht)** Build-Artefakte im OneDrive-Ordner aufräumen: `build/`, `dist/` (usmc-0.1.0.tar.gz + .whl vom 2026-06-05), `usmc.egg-info/`, `.pytest_cache/` und `__pycache__/` (in `usmc/` und `tests/`) sind gitignoriert, erzeugen aber OneDrive-Sync-Last. Lokal löschen; Builds künftig außerhalb von OneDrive oder mit anschließendem Cleanup.
- [x] **(niedrig, erledigt 2026-07-04: Zahl entfernt)** Hartkodierte Testanzahl in `README.md:25` („50 tests"): Stimmt heute exakt (11+17+22), veraltet aber bei jedem neuen Test. Formulierung ohne Zahl wählen oder bei Test-Änderungen mitpflegen.
- [x] **(niedrig, erledigt 2026-07-04: `usmc_meta` in beiden READMEs ergänzt)** README „Database Schema" (`README.md:128-135`): Tabelle `usmc_meta` (Schema-Version, `usmc/schema.py:73-76`) fehlt in der Aufzählung — der Vollständigkeit halber ergänzen.
- [ ] **(niedrig) Quelle-der-Wahrheit-Hinweis:** `.TOPICS/.AI/CLAUDE.md` listet USMC unter `.OS/`, diese Kopie liegt unter `.MODULES/USMC` — deckt sich mit dem offenen HIGH-Eintrag vom 2026-06-04; bei der Entscheidung auch die `.AI/CLAUDE.md`-Ordnerübersicht konsistent machen.

### Status der Alt-Einträge (Stand 2026-06-12)

- HIGH „Source of truth `.AI/.OS` vs. `usmc_bridge.py`": **weiterhin offen** (siehe Änderungen, letzter Punkt).
- MEDIUM „build/package smoke check": de facto durchgeführt (`python -m build` am 2026-06-05, Artefakte in `dist/`), aber noch **nicht dokumentiert** — Eintrag bleibt offen.
- MEDIUM „Laufzeit-DB nach `data/`": **weiterhin offen**, jetzt als konkreter Fix-Punkt oben aufgenommen.
- LOW „Cross-Agent-Handoff-Beispiele" und „Benchmark-Notizen": **weiterhin offen**.

---

## Review 2026-07-04 (Modul-Review-Loop Lauf 2, frischer Subagent + Fable)

**Stand:** Divergenz main↔origin per rebase aufgelöst (Banner-Commit 96ddf9b
integriert, local-first-Commit feb0a30 gepusht); OneDrive-Duplikat-Working-Tree
(README/banner.svg, byte-identisch zu 96ddf9b) bereinigt; Audit-2026-06-12-
Abschnitt als Fremdänderung nachzertifiziert und committet.

### Gefixt (alle 2026-07-04, Tests 50→59 grün)

- [x] **(hoch)** feb0a30 war unvollständig: `USMCClient.__init__` hatte weiterhin
      den cwd-Default `usmc_memory.db` — nur CLI/API waren umgestellt. Jetzt eine
      Quelle der Wahrheit: `usmc.client.default_db_path()` (`~/.usmc`, Env
      `USMC_DB`), von Client, api UND CLI genutzt; CLI re-exportiert sie.
- [x] **(hoch)** Import-Seiteneffekt: `api.py` berechnete `_default_db` auf
      Modulebene via `cli.default_db_path()`, das `~/.usmc` bereits beim bloßen
      `import usmc` anlegte (und `api`→`cli`-Schichtungsverletzung). Jetzt lazy:
      Verzeichnis entsteht erst beim tatsächlichen Client-Connect.
- [x] **(hoch)** Breaking Change undokumentiert + ungetestet: CHANGELOG-Eintrag,
      README-Abschnitt „Default Database Location" (DE+EN), neue
      `tests/test_paths.py` (Default, `USMC_DB`-Override, kein Seiteneffekt,
      Client-Default, CLI=Client-Quelle, delete_fact, Versions-Single-Source).
- [x] **(neu, mittel)** README-Multi-Agent-Beispiel nutzte Kategorie `"repo"` —
      `add_fact` validiert gegen `user/project/system/domain`, das Beispiel warf
      also `ValueError`. Auf `"project"` korrigiert (DE+EN).
- [x] Installierten `usmc`-CLI (user site-packages) aus dem gefixten Stand neu
      installiert und live verifiziert (`usmc status` → `~/.usmc/usmc_memory.db`,
      Bestandsdaten intakt).

### Weiterhin offen (bewusst nicht in diesem Lauf)

- [ ] **(mittel)** Deutsche Laufzeit-Ausgaben (`generate_context()`, CLI-Meldungen)
      im englischen Public-Repo — Umstellung berührt Tests und ist eine
      Sprach-Grundsatzentscheidung (vgl. clutch: deutsche Domänensprache bewusst).
- [ ] **(niedrig)** Interne Docstrings deutsch; CI-Matrix 3.14; ruff-Lint-Step;
      `sys.path.insert`-Hacks; `[project.optional-dependencies]` test-Extra;
      Source-of-truth `.MODULES` vs `.OS` (HIGH-Alt-Eintrag).
