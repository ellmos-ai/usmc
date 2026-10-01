# Contributing to USMC

[English](#english) | [Deutsch](#deutsch)

---

<a id="english"></a>
## English

Thank you for your interest in contributing to **USMC (United Shared Memory Client)**!

### Architectural Principles & Governance Invariants

`usmc` is a sovereign, zero-dependency Python shared memory library and CLI coordination store for local LLM agents and multi-agent frameworks. It provides lightweight, structured working memory, persistent facts, categorized lessons, session handoffs, and prompt-context generation over a robust local SQLite database with write-ahead logging (WAL), zero daemon overhead, and fail-safe multi-agent concurrency. All contributions must respect our foundational invariants:

1. **100% Local-First & Zero-Egress (`INV-LOCAL-01`)**: All operations persist to local SQLite (`~/.usmc/usmc.db` or configured local target); zero telemetry, analytics, cloud synchronization, or outbound network calls.
2. **Unprivileged RunAsInvoker (`INV-UNPRIV-02`)**: All CLI commands, API calls, and background routines execute strictly within unprivileged user space; no administrative rights, root elevation, sudo, or UAC prompts are ever required.
3. **ACID & WAL Concurrency (`INV-SQLITE-03`)**: Resilient multi-agent concurrency via SQLite Write-Ahead Logging (WAL) mode, busy handlers, and atomic transaction semantics.
4. **Backward-Compatible Schema Evolution (`INV-SCHEMA-04`)**: Automated, idempotent migrations and schema evolution ensuring seamless inter-agent backward compatibility.
5. **Bounded Ring Buffer & Pruning (`INV-BOUND-05`)**: Safe retention limits and deterministic pruning prevent uncontrolled disk expansion in long-running agent loops.
6. **In-Engine Delimiter Filtering (`INV-FILTER-06`)**: SQL WHERE clause filtering with delimiter-anchored matching prevents busy-loop starvation and post-fetch truncation.
7. **Stable Protocol & Language Contract (`INV-LANG-07`)**: Human-readable prose localized to German (`RUNTIME_LANGUAGE = "de"`), while CLI subcommands and JSON keys remain stable English tokens.
8. **Strict State Isolation (`INV-ISOL-08`)**: Shared memory databases reside strictly in user directories (`~/.usmc/` or custom targets), completely isolated from git repositories.
9. **Complete SPDX Audit Transparency (`INV-AUDIT-09`)**: 100% Python Standard Library at runtime (`dependencies = []`); zero external runtime dependencies and zero copyleft risks.
10. **48h Security Response SLA (`INV-SLA-10`)**: Committed vulnerability triage and response within 48 hours via [SECURITY.md](SECURITY.md).

### Development Guidelines & Quality Gates

- **Plan D Architecture**: Development, git operations, and tests occur strictly in the canonical local git repository clone (`C:\_Local_DEV\repos\usmc`). OneDrive mirrors are derived read-only projections.
- **Python Compatibility**: Python 3.10, 3.11, 3.12, 3.13, and 3.14 support.
- **Zero-Dependency Core**: The core package relies strictly on the official Python Standard Library; external runtime dependencies are strictly prohibited.
- **Version Freeze Policy**: Versions are strictly frozen per T-20260920-167562623 unless explicitly authorized by maintainers. All ongoing improvements land under `## [Unreleased]` in `CHANGELOG.md`.
- **Pre-commit Quality Gates**:
  - Bytecode compilation: `python -m compileall -q usmc tests`
  - Code formatting & linting: `ruff check .`
  - Automated test suite: `pytest -ra -v` (100% green required)
  - Git whitespace hygiene: `git diff --check`
- **Security Vulnerabilities**: Never report security vulnerabilities publicly. Please follow our [SECURITY.md](SECURITY.md) guidelines for responsible disclosure (48h response SLA).

---

<a id="deutsch"></a>
## Deutsch

Vielen Dank für Ihr Interesse an einer Mitarbeit an **USMC (United Shared Memory Client)**!

### Architektur-Prinzipien & Governance-Invarianten

`usmc` ist eine souveräne Python-Speicherschicht ohne externe Laufzeitabhängigkeiten für lokale LLM-Agenten und Multi-Agenten-Systeme. Sie bietet eine einheitliche, SQLite-basierte Persistenz für Fakten, gelernte Lektionen, sitzungsbezogene Arbeitsnotizen, Übergabekontext und kompakte Prompt-Generierung ohne Hintergrund-Daemon oder Cloud-Dienst. Alle Beiträge müssen unsere grundlegenden Invarianten einhalten:

1. **100% Local-First & Zero-Egress (`INV-LOCAL-01`)**: Sämtliche Operationen persistieren in einer lokalen SQLite-Datenbank (`~/.usmc/usmc.db` oder konfigurierter lokaler Pfad); keinerlei Telemetrie oder externe Netzwerkaufrufe.
2. **Unprivilegierter Benutzermodus / RunAsInvoker (`INV-UNPRIV-02`)**: Alle CLI-Befehle, API-Aufrufe und Routinen operieren strikt im Standard-Benutzerkontext; administrative Rechte oder UAC-Elevation werden niemals angefordert.
3. **ACID & WAL-Nebenläufigkeit (`INV-SQLITE-03`)**: Ausfallsichere Multi-Agenten-Gleichzeitigkeit durch SQLite WAL-Modus, Busy-Handler und atomare Transaktionen.
4. **Abwärtskompatible Schema-Evolution (`INV-SCHEMA-04`)**: Automatische, idempotente Migrationen garantieren nahtlosen Zugriff über Agenten-Generationen hinweg.
5. **Ringpuffer & Bereinigung (`INV-BOUND-05`)**: Konfigurierbare Aufbewahrungsgrenzen und deterministische Bereinigung verhindern unkontrolliertes Festplattenwachstum.
6. **In-Engine Delimiter-Filterung (`INV-FILTER-06`)**: SQL-WHERE-Filterung mit Begrenzungszeichen verhindert Aushungerung durch Schreibschleifen und Nachfilter-Verlust.
7. **Stabiler Protokollvertrag (`INV-LANG-07`)**: Menschliche Ausgabetexte auf Deutsch (`RUNTIME_LANGUAGE = "de"`), CLI-Befehle und JSON-Schlüssel als stabile englische Token.
8. **Strikte Zustandstrennung (`INV-ISOL-08`)**: Datenbanken residieren isoliert im Benutzerverzeichnis (`~/.usmc/`), vollständig getrennt von Git-Repositories.
9. **Vollständige SPDX-Transparenz (`INV-AUDIT-09`)**: 100% reine Python-Standardbibliothek zur Laufzeit (`dependencies = []`); keinerlei externe Laufzeit-Abhängigkeiten oder Copyleft-Risiken.
10. **48h Sicherheits-Reaktions-SLA (`INV-SLA-10`)**: Verbindliche Sicherheits-Ersteinschätzung innerhalb von 48 Stunden gemäß [SECURITY.md](SECURITY.md).

### Richtlinien für Entwickler & Qualitäts-Tore

- **Plan D Architektur**: Entwicklung und Tests erfolgen ausschließlich im lokalen kanonischen Git-Repository (`C:\_Local_DEV\repos\usmc`).
- **Python-Unterstützung**: Python 3.10 bis 3.14.
- **Null externe Laufzeitabhängigkeiten**: Der Kern basiert rein auf der Python-Standardbibliothek.
- **Versions-Einfrier-Richtlinie**: Versionen bleiben eingefroren per T-20260920-167562623; Neuerungen werden unter `## [Unreleased]` in `CHANGELOG.md` erfasst.
- **Qualitäts-Tore vor Commits**:
  - Bytecode-Prüfung: `python -m compileall -q usmc tests`
  - Linter & Code-Prüfung: `ruff check .`
  - Testsuite: `pytest -ra -v` (100% grün erforderlich)
  - Git-Whitespace-Prüfung: `git diff --check`
- **Sicherheitsmeldungen**: Sicherheitslücken bitte nicht öffentlich melden, sondern gemäß [SECURITY.md](SECURITY.md) vertraulich einreichen (48h Reaktions-SLA).
