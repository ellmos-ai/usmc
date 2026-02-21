# USMC -- United Shared Memory Client

**Status: Under Construction**

This project will provide a unified cross-agent memory access layer,
enabling multiple LLM agents to share persistent knowledge across sessions
and platforms.

## Origin

USMC is being developed from the research conducted in the
**SharedMemoryClient** project (currently located under
`MODULAR_AGENTS/SharedMemoryClient/`). The SharedMemoryClient is a
research prototype exploring cross-agent memory sharing patterns.
Once the research phase concludes, the findings will be consolidated
into this standalone USMC implementation.

## Planned Features

- Unified memory API for multiple LLM agent frameworks
- Cross-session persistence (SQLite-based)
- Memory deduplication and conflict resolution
- Access control (read/write permissions per agent)
- Memory decay and relevance scoring
- Plugin architecture for different storage backends

## Related Research

- SharedMemoryClient (research prototype): `../SharedMemoryClient/`
- BACH Memory System: Cross-project memory with silo architecture
- Claude Code Memory: Project-based `.claude/` memory files

## Timeline

- Research phase: ongoing (SharedMemoryClient)
- Architecture design: after research conclusions
- Implementation: TBD

## License

MIT License -- Copyright (c) 2026 Lukas Geiger

## Author

Lukas Geiger (github.com/lukisch)
