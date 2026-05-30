<p align="center">
  <img src="assets/ellmos-logo.jpg" alt="ellmos USMC Logo" width="260">
</p>

# USMC - United Shared Memory Client

[![CI](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml/badge.svg)](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)

**English:** [README.md](README.md)

USMC ist eine Python-Speicherschicht ohne externe Abhängigkeiten für LLM-Agenten. Mehrere lokale Agenten teilen sich damit eine SQLite-basierte Erinnerung für Fakten, Lektionen, Arbeitsnotizen, Sitzungen und kompakten Prompt-Kontext.

Dieses Repository ist das ellmos-Projekt `ellmos-ai/usmc`, in Suchtexten auch **ellmos USMC** oder **United Shared Memory Client**. Es steht in keiner Beziehung zum United States Marine Corps.

## Zweck

LLM-Agenten verlieren zwischen Läufen oft Kontext oder verteilen Notizen über mehrere Werkzeuge. USMC hält nur den Speicherteil klein und wiederverwendbar:

- Persistente Fakten mit Confidence-Werten speichern.
- Lektionen als Problem/Lösungs-Muster dokumentieren.
- Temporäre Arbeitsnotizen für eine Sitzung halten.
- Agenten-Sitzungen und Übergabenotizen nachvollziehen.
- Kompakte Kontextblöcke für Prompts erzeugen.
- Eine lokale SQLite-Datenbank zwischen Agenten teilen.

USMC ist Tier 1 der ellmos-Familie. Rinnsal und BACH bauen größere Orchestrierungsschichten darauf auf, während USMC bewusst nur Speicher bereitstellt.

## Installation

Direkt von GitHub:

```bash
pip install git+https://github.com/ellmos-ai/usmc.git
```

Aus einem lokalen Checkout:

```bash
pip install -e .
```

Der PyPI-Paketname `usmc` ist für dieses Projekt vorgesehen, aber noch nicht veröffentlicht. Bis zum ersten PyPI-Release bitte die GitHub-Installation verwenden.

## Schnellstart

```python
from usmc import USMCClient

client = USMCClient(agent_id="codex")

client.add_fact("project", "framework", "FastAPI", confidence=0.9)
client.add_lesson(
    title="Windows-Encoding",
    problem="Python-Subprocess-Ausgabe nutzte cp1252",
    solution="Mit PYTHONIOENCODING=utf-8 ausführen",
    severity="high",
)
client.add_working("Aktuell wird eine Release-Checkliste vorbereitet")

print(client.generate_context())
```

High-Level API:

```python
from usmc import api

api.init(agent_id="claude")
api.remember("repo", "ellmos-ai/usmc")
api.note("README und Paketmetadaten prüfen")
api.lesson("Marketing-Check", "Keine Suchsichtbarkeit", "ellmos-usmc-Wording nutzen")

print(api.status())
print(api.context())
```

CLI:

```bash
usmc status
usmc fact project framework FastAPI --confidence 0.9
usmc note "Aktuelle Aufgabe: Release-Polish"
usmc lesson "Encoding-Bug" "cp1252-Ausgabe" "PYTHONIOENCODING=utf-8 setzen" --severity high
usmc context
usmc changes "2026-02-28T00:00:00" --json
```

## Kernkonzepte

| Konzept | Gespeicherter Inhalt | Typische Nutzung |
|---|---|---|
| Fakten | Persistentes Schlüssel/Wert-Wissen mit Confidence | Projektfakten, Systemfakten, Nutzerpräferenzen |
| Lektionen | Wiederverwendbare Problem/Lösungs-Einträge mit Schweregrad | Fehler, Betriebsregeln, Workflow-Fixes |
| Arbeitsgedächtnis | Temporäre aktive Notizen | Aktueller Aufgabenstand und Scratchpad-Kontext |
| Sitzungen | Start/Ende-Einträge mit Übergabenotizen | Kontinuität zwischen Agenten |
| Änderungen | Abfragbarer Änderungsstrom | Leichtgewichtige Synchronisierung |

## Multi-Agent-Beispiel

```python
from usmc import USMCClient

codex = USMCClient(db_path="shared.db", agent_id="codex")
claude = USMCClient(db_path="shared.db", agent_id="claude")

codex.add_fact("repo", "status", "needs docs", confidence=0.7)
claude.add_fact("repo", "status", "docs ready", confidence=0.95)

print(codex.get_facts(category="repo"))
```

Wenn zwei Agenten denselben Fakt schreiben, gewinnt der Wert mit höherer Confidence.

## Datenbankschema

- `usmc_facts` - persistente Fakten mit Confidence-Werten
- `usmc_lessons` - gelernte Lektionen mit Schweregrad
- `usmc_working` - temporäre Notizen, Kontext, Scratchpad
- `usmc_sessions` - Agenten-Sitzungsverlauf

Die Datenbank ist reines SQLite. Es gibt keinen Daemon, Broker, Cloud-Dienst oder externe Laufzeitabhängigkeit.

## Einordnung

USMC ist absichtlich kleiner als vollständige Agentenplattformen:

| Projekttyp | Umfang | Rolle von USMC |
|---|---|---|
| Agent-Frameworks | Tools, Planung, Orchestrierung, Ausführung | Gemeinsame Speicherschicht darunter |
| Chat-Assistenten | Gesprächsschleife und UI | Dauerhaftes Wissen außerhalb des Chatverlaufs |
| MCP-Server | Tool-Zugriff über Protokoll | Lokales Speicher-Backend |
| BACH / Rinnsal | ellmos-Orchestrierungsschichten | Wiederverwendbare Speicherbasis |

## Entwicklung

```bash
python -m pytest -q
python -m compileall -q usmc tests
python -m build
```

## Verwandte Projekte

- [Rinnsal](https://github.com/ellmos-ai/rinnsal) - kompakte ellmos-Orchestrierungsschicht
- [BACH](https://github.com/ellmos-ai/bach) - vollständiges textbasiertes LLM-Betriebssystem
- [ellmos-stack](https://github.com/ellmos-ai/ellmos-stack) - Deployment- und Ökosystemkontext

## Lizenz

MIT License - Copyright (c) 2026 Lukas Geiger

## Haftung

Dieses Projekt ist eine unentgeltliche Open-Source-Schenkung. Die Haftung des Urhebers ist gemäß § 521 BGB auf Vorsatz und grobe Fahrlässigkeit beschränkt.

Nutzung auf eigenes Risiko. Keine Wartungszusage, keine Verfügbarkeitsgarantie, keine Gewähr für Fehlerfreiheit oder Eignung für einen bestimmten Zweck.
