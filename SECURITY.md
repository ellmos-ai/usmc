# Sicherheitsrichtlinie / Security Policy

## Deutsch

### Unterstützte Versionen

| Version | Unterstützt | Anmerkung |
|---------|-------------|-----------|
| **0.2.x** | :white_check_mark: Aktiv | Aktuelle Haupt- und Wartungsversion |
| < 0.2.0 | :x: Veraltet | Bitte auf Version 0.2.2+ aktualisieren |

### Sicherheitslücken melden

Wenn Sie eine Sicherheitslücke oder Schwachstelle in **usmc** (United Shared Memory Client) entdecken, melden Sie diese bitte verantwortungsbewusst und diskret:

1. **Kein öffentliches GitHub-Issue eröffnen.**
2. **GitHub Private Vulnerability Reporting verwenden:** [Security Advisories](https://github.com/ellmos-ai/usmc/security/advisories/new)
3. Fügen Sie eine präzise Beschreibung, Reproduktionsschritte sowie die potenzielle Sicherheitsauswirkung bei.

Falls GitHub Private Vulnerability Reporting im Repository nicht verfügbar sein sollte, kontaktieren Sie das Sicherheitsteam direkt per E-Mail:
- `security@ellmos.ai`
- `support@lukasgeiger.com`
- `lukas@open-bricks.org`
- `security@open-bricks.org`

### Reaktionszeit & SLA

- **Erstreaktion:** Innerhalb von **48 Stunden** (**48 hours**) an Werktagen mit Eingangsbestätigung.
- **Triage & Einstufung:** Innerhalb von **5 Werktagen** (**5 business days**) mit technischer Bewertung und Priorisierung.
- **Patch-Bereitstellung:** Kritische Sicherheitsbehebungen werden unverzüglich als Point-Release bereitgestellt.

### Sicherheitsprinzipien & Laufzeit-Invarianten

- **100% Local-First & Zero Egress:** usmc persistiert ausschließlich in der lokalen SQLite-Datenbank (`~/.usmc/usmc.db` oder benutzerdefinierter lokaler Pfad). Es existiert keinerlei Telemetrie, Tracking oder externer Netzwerkzugriff.
- **Unprivilegierter Benutzermodus (`RunAsInvoker`):** Alle CLI- und Modul-Operationen laufen vollständig im unprivilegierten Benutzerkontext ohne Administrator- oder Root-Rechte.
- **ACID-Transaktionssicherheit & WAL:** Robuste Multi-Agenten-Gleichzeitigkeit durch SQLite Write-Ahead Logging (WAL) und Busy-Handler.
- **Isolierter Speicherort:** Die Datenbank liegt standardmäßig im Benutzerverzeichnis (`~/.usmc/`), niemals innerhalb von Quellcode-Repositories.

| Invariante | Kategorie | Beschreibung |
|---|---|---|
| `INV-LOCAL-01` | Local-First & Zero-Egress | 100% offlinefähig; sämtliche Operationen persistieren in lokaler SQLite; keine Netzwerkaufrufe oder Telemetrie. |
| `INV-UNPRIV-02` | Unprivilegierter Benutzermodus (`RunAsInvoker`) | Sämtliche Prozesse operieren im unprivilegierten Benutzerkontext ohne Root-/Admin-Elevation. |
| `INV-SQLITE-03` | ACID & WAL-Nebenläufigkeit | Ausfallsichere Multi-Agenten-Gleichzeitigkeit durch SQLite WAL-Modus, Busy-Handler und atomare Transaktionen. |
| `INV-SCHEMA-04` | Abwärtskompatible Schema-Evolution | Automatische, idempotente Migrationen garantieren nahtlosen Zugriff über Agenten-Generationen hinweg. |
| `INV-BOUND-05` | Ringpuffer & Bereinigung | Konfigurierbare Aufbewahrungsgrenzen und deterministische Bereinigung verhindern unkontrolliertes Festplattenwachstum. |
| `INV-FILTER-06` | In-Engine Delimiter-Filterung | SQL-WHERE-Filterung mit Begrenzungszeichen verhindert Aushungerung durch Schreibschleifen und Nachfilter-Verlust. |
| `INV-LANG-07` | Stabiler Protokollvertrag | Menschliche Ausgabetexte auf Deutsch (`RUNTIME_LANGUAGE = "de"`), CLI-Befehle und JSON-Schlüssel als stabile englische Token. |
| `INV-ISOL-08` | Strikte Zustandstrennung | Datenbanken residieren isoliert im Benutzerverzeichnis (`~/.usmc/`), vollständig getrennt von Git-Repositories. |
| `INV-AUDIT-09` | Vollständige SPDX-Transparenz | 100% reine Python-Standardbibliothek zur Laufzeit; keinerlei externe Laufzeit-Abhängigkeiten oder Copyleft-Risiken. |
| `INV-SLA-10` | Plattformunabhängigkeit & SLA | Einheitliches Verhalten unter Windows, Linux und macOS mit 48h-Sicherheits-Reaktions-SLA. |

---

## English

### Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| **0.2.x** | :white_check_mark: Active | Current primary and maintenance release |
| < 0.2.0 | :x: End of Life | Please upgrade to version 0.2.2+ |

### Reporting Security Issues

If you discover a security vulnerability or concern in **usmc** (United Shared Memory Client), please disclose it responsibly:

1. **Do not file a public GitHub issue.**
2. **Use GitHub Private Vulnerability Reporting:** [Security Advisories](https://github.com/ellmos-ai/usmc/security/advisories/new)
3. Include detailed steps to reproduce, impact assessment, and any proposed remediations.

If Private Vulnerability Reporting is unavailable, contact the security team via email:
- `security@ellmos.ai`
- `support@lukasgeiger.com`
- `lukas@open-bricks.org`
- `security@open-bricks.org`

### Response Time & SLA

- **Initial Response:** Within **48 hours** on business days.
- **Triage & Assessment:** Within **5 business days** with confirmed assessment and mitigation timeline.
- **Patch Release:** Critical security patches are released as high-priority point releases.

### Security Principles & Runtime Invariants

- **100% Local-First & Zero Egress:** usmc persists exclusively to the local SQLite database (`~/.usmc/usmc.db` or configured local target). No telemetry, tracking, or external network requests exist.
- **Non-Elevation User Mode (`RunAsInvoker`):** All CLI tools and modules operate strictly within unprivileged user space. No administrative or root elevation is ever requested or required.
- **ACID Transaction Resilience & WAL:** Resilient multi-agent concurrency via SQLite Write-Ahead Logging (WAL) and busy handlers.
- **Isolated Database State:** The database resides strictly in user home (`~/.usmc/`), never inside source repositories.

| Invariant | Category | Description |
|---|---|---|
| `INV-LOCAL-01` | Local-First & Zero-Egress | 100% offline-ready; all operations persist to local SQLite; zero telemetry or outbound network calls. |
| `INV-UNPRIV-02` | Unprivileged User Mode (`RunAsInvoker`) | All CLI commands, API calls, and background routines operate strictly in unprivileged user space. |
| `INV-SQLITE-03` | ACID & WAL Concurrency | Resilient multi-agent concurrency via SQLite WAL mode, busy handlers, and atomic transaction semantics. |
| `INV-SCHEMA-04` | Backward-Compatible Schema Evolution | Automated idempotent migration and schema evolution ensuring seamless inter-agent backward compatibility. |
| `INV-BOUND-05` | Bounded Ring Buffer & Pruning | Safe retention limits and deterministic pruning prevent uncontrolled disk expansion in long-running agent loops. |
| `INV-FILTER-06` | In-Engine Delimiter Filtering | SQL WHERE clause filtering with delimiter-anchored matching prevents busy-loop starvation and post-fetch truncation. |
| `INV-LANG-07` | Stable Protocol & Language Contract | Human-readable prose localized to German (`RUNTIME_LANGUAGE = "de"`), while CLI subcommands and JSON keys remain stable English tokens. |
| `INV-ISOL-08` | Strict State Isolation | Shared memory databases reside strictly in user directories (`~/.usmc/` or custom targets), completely isolated from git repositories. |
| `INV-AUDIT-09` | Complete SPDX Audit Transparency | 100% Python standard library at runtime; zero external runtime dependencies and zero copyleft risks. |
| `INV-SLA-10` | Cross-Platform Parity & SLA | Consistent behavior across Windows, Linux, and macOS with committed 48h response / 5-day triage security SLA. |
