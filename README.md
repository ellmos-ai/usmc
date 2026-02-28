# USMC -- United Shared Memory Client

**Status: Alpha (v0.1.0)**

Cross-agent memory sharing via standalone SQLite. No external dependencies.

## Install

```bash
pip install usmc
```

## Quick Start

### Client API

```python
from usmc import USMCClient

# Initialize (creates usmc_memory.db)
client = USMCClient(agent_id="my-agent")

# Facts (persistent knowledge)
client.add_fact("project", "framework", "FastAPI", confidence=0.9)
client.add_fact("system", "os", "Windows 11")
facts = client.get_facts(min_confidence=0.8)

# Lessons (learned patterns)
client.add_lesson(
    title="Encoding Bug",
    problem="cp1252 statt UTF-8",
    solution="PYTHONIOENCODING=utf-8 setzen",
    severity="high"
)
lessons = client.get_lessons(severity="high")

# Working memory (session-scoped notes)
client.add_working("Currently refactoring auth module")
working = client.get_working()

# Sessions
session = client.start_session(task="Feature X")
# ... work ...
client.end_session(session['id'], handoff_notes="Refactored auth")

# Context generation (for LLM prompts)
context = client.generate_context()

# Sync (poll-based)
changes = client.get_changes_since("2026-02-28T00:00:00")
```

### High-Level API

For quick, stateless access without managing client instances:

```python
from usmc import api

# Initialize once
api.init(agent_id="opus")

# Facts
api.fact("system", "os", "Windows 11")
api.remember("framework", "FastAPI")  # shortcut with confidence=0.95
facts = api.facts(category="system")

# Working memory
api.note("Aktueller Task: Feature X")
api.scratch("Temporaere Notiz")
api.loop("Iteration 1 von 5")
notes = api.working()
api.clear()  # deactivate all notes

# Lessons
api.lesson("Bug-Title", "Problem", "Solution", severity="high")
lessons = api.lessons()

# Sessions
session = api.start(task="Testing")
api.end(session['id'], notes="Done")

# Context & Status
print(api.context())
print(api.status())
```

### CLI

```bash
# Status
usmc status

# Facts
usmc fact system os "Windows 11"
usmc fact project framework FastAPI --confidence 0.9
usmc facts
usmc facts --category system --json

# Working memory
usmc note "Aktueller Task: Feature implementieren"
usmc note "High priority" --priority 5 --tags "important,urgent"
usmc working
usmc clear

# Lessons
usmc lesson "Encoding Bug" "cp1252 Problem" "PYTHONIOENCODING=utf-8" --severity high
usmc lessons
usmc lessons --severity critical

# Context
usmc context

# Sessions
usmc start --task "Feature X"
usmc end 1 --notes "Done"

# Sync
usmc changes "2026-02-28T00:00:00" --json

# Options
usmc --db custom.db --agent my-agent status
```

## Multi-Agent

Multiple agents can share the same DB:

```python
opus = USMCClient(db_path="shared.db", agent_id="opus")
sonnet = USMCClient(db_path="shared.db", agent_id="sonnet")

opus.add_fact("project", "status", "in-progress", confidence=0.8)
sonnet.add_fact("project", "status", "completed", confidence=0.95)
# Confidence merge: sonnet's higher confidence wins
```

## Features

- Standalone SQLite database (no external dependencies)
- Confidence-based conflict resolution
- Multi-agent support with agent_id tracking
- Session management with handoff notes
- Context generation for LLM prompts
- Change tracking via `get_changes_since()`
- High-level API for quick access
- Full CLI for terminal use
- Zero external dependencies (stdlib only)

## Database Schema

- `usmc_facts` - Persistent facts with confidence scores
- `usmc_working` - Temporary notes, context, scratchpad
- `usmc_lessons` - Lessons learned with severity
- `usmc_sessions` - Agent session tracking

## Origin

Developed from the SharedMemoryClient research prototype.
Part of the BACH ecosystem but fully standalone.

## License

MIT License -- Copyright (c) 2026 Lukas Geiger

## Author

Lukas Geiger (github.com/lukisch)
