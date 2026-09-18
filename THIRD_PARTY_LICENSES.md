# Third-Party Licenses & Software Inventory

**Project:** `usmc` (United Shared Memory Client)  
**License:** [MIT License](LICENSE)  
**Audit Date:** 2026-09-18  
**Repository:** [ellmos-ai/usmc](https://github.com/ellmos-ai/usmc)  
**Umbrella Collective:** [open-bricks](https://github.com/open-bricks)  

---

## Runtime Architecture & Dependencies

`usmc` is engineered as a **zero-dependency, local-first shared memory client and coordination store for LLM agents and multi-agent frameworks**. It provides lightweight, structured working memory, persistent facts, categorized lessons, and prompt-context generation over a robust local SQLite database with write-ahead logging (WAL), zero daemon overhead, and fail-safe multi-agent concurrency.

### Mandatory Runtime Dependencies

`usmc` maintains a **zero external runtime dependency footprint** (`dependencies = []`). The entire runtime execution relies strictly on the official Python Standard Library:

| Package / Module | Version Spec | License | Type | Purpose |
|---|---|---|---|---|
| *Python Standard Library* | `>=3.10` | PSF-2.0 | Built-in | Core runtime: `argparse`, `dataclasses`, `datetime`, `json`, `os`, `pathlib`, `sqlite3`, `sys`, `typing` |

All state persistence is handled entirely via Python's built-in `sqlite3` driver. Zero third-party telemetry, analytics, cloud synchronization, or remote networking services are packaged or contacted.

### Development & Test Tooling

The following tools are utilized exclusively for offline automated testing, code quality auditing, packaging, and linting:

| Package / Tool | Version Spec | License | Scope | Purpose |
|---|---|---|---|---|
| [pytest](https://pytest.org/) | `>=7.0` | MIT | `[dev]` | Automated unit, contract, and metadata test runner |
| [ruff](https://github.com/astral-sh/ruff) | `>=0.6` | MIT OR Apache-2.0 | `[dev]` | High-performance Python code style and lint enforcement |
| [setuptools](https://github.com/pypa/setuptools) | `>=77.0` | MIT | `[build-system]` | Standard packaging and build backend |
| [wheel](https://github.com/pypa/wheel) | `>=0.40` | MIT | `[build-system]` | Standard built-package distribution format |

---

## Zero-Copyleft Guarantee & Unprivileged Execution

- **Zero-Copyleft Guarantee:** All runtime code and development dependencies are governed strictly by permissive, business-friendly open-source licenses (MIT, Apache-2.0, PSF-2.0). The codebase contains **zero** GPL, AGPL, or viral copyleft components.
- **Unprivileged User-Mode Operation (`RunAsInvoker`):** All CLI commands, memory ingestion, SQLite transactions, and state queries execute purely within unprivileged user space. No administrative rights, root elevation, sudo, or UAC prompts are ever required.

---

## Governance & Runtime Invariants

`usmc` strictly enforces ten foundational governance and runtime invariants:

| Invariant | Category | Description |
|---|---|---|
| `INV-LOCAL-01` | Local-First & Zero-Egress | 100% offline-ready; all operations persist to local SQLite (`~/.usmc/usmc.db` or configured path); zero telemetry or outbound network calls. |
| `INV-UNPRIV-02` | Unprivileged User Mode (`RunAsInvoker`) | All CLI commands, API calls, and background routines operate strictly in unprivileged user space. |
| `INV-SQLITE-03` | ACID & WAL Concurrency | Resilient multi-agent concurrency via SQLite WAL mode, busy handlers, and atomic transaction semantics. |
| `INV-SCHEMA-04` | Backward-Compatible Schema Evolution | Automated idempotent migration and schema evolution ensuring seamless inter-agent backward compatibility. |
| `INV-BOUND-05` | Bounded Ring Buffer & Pruning | Safe retention limits and deterministic pruning prevent uncontrolled disk expansion in long-running agent loops. |
| `INV-FILTER-06` | In-Engine Delimiter Filtering | SQL WHERE clause filtering with delimiter-anchored matching prevents busy-loop starvation and post-fetch truncation. |
| `INV-LANG-07` | Stable Protocol & Language Contract | Human-readable prose localized to German (`RUNTIME_LANGUAGE = "de"`), while CLI subcommands and JSON keys remain stable English tokens. |
| `INV-ISOL-08` | Strict State Isolation | Shared memory databases reside strictly in user directories (`~/.usmc/` or custom targets), completely isolated from git repositories. |
| `INV-AUDIT-09` | Complete SPDX Audit Transparency | 100% Python standard library at runtime; zero external runtime dependencies and zero copyleft risks. |
| `INV-SLA-10` | Cross-Platform Parity & SLA | Consistent behavior across Windows, Linux, and macOS with committed 48h response / 5-day triage security SLA. |

---

## License Texts & Attribution

### MIT License (`usmc`, `pytest`, `ruff`, `setuptools`, `wheel`)

```
MIT License

Copyright (c) 2026 Lukas Geiger / ellmos-ai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Python Software Foundation License Version 2 (`Python Standard Library`)

```
1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and
the Individual or Organization ("Licensee") accessing and otherwise using this
software ("Python") in source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works, distribute,
and otherwise use Python alone or in any derivative version, provided, however, that
PSF's License Agreement and PSF's notice of copyright, i.e., "Copyright (c) 2001-2026
Python Software Foundation; All Rights Reserved" are included in Python alone or in
any derivative version prepared by Licensee.
```

### Apache License Version 2.0 (`ruff`)

```
Copyright (c) Astral Software Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
