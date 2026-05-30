<p align="center">
  <img src="assets/ellmos-logo.jpg" alt="ellmos USMC logo" width="260">
</p>

# USMC - United Shared Memory Client

[![CI](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml/badge.svg)](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)

**Deutsch:** [README_de.md](README_de.md)

USMC is a zero-dependency Python memory layer for LLM agents. It gives multiple local agents one shared SQLite-backed memory for facts, lessons, working notes, sessions, and compact prompt context.

This repository is the ellmos project `ellmos-ai/usmc`, also described as **ellmos USMC** or **United Shared Memory Client** in search text. It is not related to the United States Marine Corps.

## Why It Exists

LLM agent projects often lose context between runs or duplicate notes across tools. USMC keeps the memory part small and reusable:

- Store persistent facts with confidence scores.
- Record lessons as problem/solution patterns.
- Keep session-scoped working notes.
- Track agent sessions and handoff notes.
- Generate compact context blocks for prompts.
- Share one local SQLite database across different agents.

USMC is Tier 1 of the ellmos family. Rinnsal and BACH build larger orchestration layers on top, but USMC stays focused on memory only.

## Install

From GitHub:

```bash
pip install git+https://github.com/ellmos-ai/usmc.git
```

From a local checkout:

```bash
pip install -e .
```

The PyPI package name `usmc` is reserved for this project but not yet published. Until the first PyPI release, use the GitHub install form above.

## Quick Start

```python
from usmc import USMCClient

client = USMCClient(agent_id="codex")

client.add_fact("project", "framework", "FastAPI", confidence=0.9)
client.add_lesson(
    title="Windows encoding",
    problem="Python subprocess output used cp1252",
    solution="Run with PYTHONIOENCODING=utf-8",
    severity="high",
)
client.add_working("Currently preparing a release checklist")

print(client.generate_context())
```

High-level API:

```python
from usmc import api

api.init(agent_id="claude")
api.remember("repo", "ellmos-ai/usmc")
api.note("Audit README and package metadata")
api.lesson("Marketing check", "No search visibility", "Use ellmos-usmc wording")

print(api.status())
print(api.context())
```

CLI:

```bash
usmc status
usmc fact project framework FastAPI --confidence 0.9
usmc note "Current task: release polish"
usmc lesson "Encoding bug" "cp1252 output" "Set PYTHONIOENCODING=utf-8" --severity high
usmc context
usmc changes "2026-02-28T00:00:00" --json
```

## Core Concepts

| Concept | What it stores | Typical use |
|---|---|---|
| Facts | Persistent key/value knowledge with confidence | Project facts, system facts, user preferences |
| Lessons | Reusable problem/solution records with severity | Bugs, operational rules, workflow fixes |
| Working memory | Temporary active notes | Current task state and scratchpad context |
| Sessions | Start/end records with handoff notes | Cross-agent continuity |
| Changes | Pollable update stream | Lightweight sync between agents |

## Multi-Agent Example

```python
from usmc import USMCClient

codex = USMCClient(db_path="shared.db", agent_id="codex")
claude = USMCClient(db_path="shared.db", agent_id="claude")

codex.add_fact("repo", "status", "needs docs", confidence=0.7)
claude.add_fact("repo", "status", "docs ready", confidence=0.95)

print(codex.get_facts(category="repo"))
```

When two agents write the same fact, the higher-confidence value wins.

## Database Schema

- `usmc_facts` - persistent facts with confidence scores
- `usmc_lessons` - lessons learned with severity
- `usmc_working` - temporary notes, context, scratchpad
- `usmc_sessions` - agent session tracking

The database is plain SQLite. There is no daemon, broker, cloud service, or external runtime dependency.

## Positioning

USMC is deliberately smaller than full agent platforms:

| Project type | Scope | USMC role |
|---|---|---|
| Agent frameworks | Tools, planning, orchestration, execution | Add shared memory underneath |
| Chat assistants | Conversation loop and UI | Store durable knowledge outside chat history |
| MCP servers | Tool exposure over protocol | Use USMC as local memory backend |
| BACH / Rinnsal | ellmos orchestration layers | USMC is the reusable memory primitive |

## Development

```bash
python -m pytest -q
python -m compileall -q usmc tests
python -m build
```

## Related Projects

- [Rinnsal](https://github.com/ellmos-ai/rinnsal) - compact ellmos orchestration layer
- [BACH](https://github.com/ellmos-ai/bach) - full text-based LLM operating system
- [ellmos-stack](https://github.com/ellmos-ai/ellmos-stack) - deployment and ecosystem context

## License

MIT License - Copyright (c) 2026 Lukas Geiger

## Liability

This project is an unpaid open-source donation. Liability is limited to intent and gross negligence under Section 521 German Civil Code. Use at your own risk. No warranty, no maintenance guarantee, and no fitness-for-purpose promise are provided.
