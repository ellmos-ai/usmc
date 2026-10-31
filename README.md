<img src="assets/banner.png" width="100%" alt="USMC banner">

# USMC — United Shared Memory Client

[![CI](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml/badge.svg)](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/Tests-181%20passed%20%7C%20100%25-brightgreen.svg)](#install-and-try)
[![Dependabot](https://img.shields.io/badge/Dependabot-active-brightgreen.svg)](.github/dependabot.yml)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)

**Languages:** [English](README.md) · [Deutsch](README_de.md) · [Español](README_es.md)

> This concise entry point replaces the former long `README.md` from [source commit `bf281f1`](https://github.com/ellmos-ai/usmc/blob/bf281f1d68e9e6af44db9d12588a000fac531a61/README.md). Its corrected archival edition is now [docs/archive/README.full.en.md](docs/archive/README.full.en.md); the linked commit preserves the original source revision.

USMC is a Python package and CLI that stores facts, lessons, working notes, and session handoffs in SQLite. The declared direct runtime dependency list is empty; Python 3.10 or newer is required.

## Data and runtime scope

By default, the database path is `~/.usmc/usmc_memory.db`. Set `USMC_DB` or pass `--db` to choose another path; custom paths are used as supplied. USMC does not automatically prune stored records. Choose a suitable local path and manage its permissions, backups, and retention for your use case.

The reviewed package source contains no direct HTTP client. Installing from GitHub or building the package uses network-capable tools, and a calling agent or other process may use the network independently. USMC does not provide a firewall or sandbox; processes inherit the privileges of their launcher.

## Install and try

Install from the Git source (this requires Git/Python packaging tools and network access):

```console
python -m pip install "git+https://github.com/ellmos-ai/usmc.git"
usmc --help
usmc status
```

For a local checkout, use `python -m pip install -e ".[test]"`. The `[test]` extra is for development and testing.

```python
from usmc import USMCClient

client = USMCClient(agent_id="codex")
client.add_fact("project", "status", "in progress", confidence=0.8)
print(client.generate_context())
```

## Documentation

- [Full guide and API examples](docs/archive/README.full.en.md)
- [Security and data-handling notes](SECURITY.md)
- [Contributing and test commands](CONTRIBUTING.md)
- [Third-party license inventory](THIRD_PARTY_LICENSES.md) and [plain-text license notes](THIRD_PARTY_LICENSES.txt)
- [Machine-readable guide](llms.txt)
- [Changelog](CHANGELOG.md)

## Related projects

[BACH](https://github.com/ellmos-ai/bach) can use the optional shared-memory schema defined by USMC's `memory_union.contract.json`; see the migration and opt-in details in the full guide. This describes a schema relationship, not an automatic installation or a security boundary.
[ellmos-stack](https://github.com/ellmos-ai/ellmos-stack) composes USMC as its curated-memory component in a self-hosted research stack; its installer fetches USMC from a pinned Git commit. This describes that stack composition, not an installation or launch guarantee provided by USMC.
[GARDENER](https://github.com/ellmos-ai/gardener) offers optional read-only source templates for USMC replica snapshots; they are disabled by default and require a separate sync snapshot plus caller opt-in.

## License

The project is provided under the [MIT License](LICENSE); attribution details are in [NOTICE](NOTICE).

### Legacy section links

<a id="sec-01"></a>
<a id="key-features"></a>
<a id="hauptmerkmale"></a>
<a id="características-principales"></a>
1. [Open the archived section](docs/archive/README.full.en.md#sec-01)

<a id="sec-02"></a>
<a id="core-capabilities--primitives"></a>
<a id="kernkonzepte--primitive"></a>
<a id="conceptos-clave-y-primitivas"></a>
2. [Open the archived section](docs/archive/README.full.en.md#sec-02)

<a id="sec-03"></a>
<a id="target-personas--discoverability"></a>
<a id="zielgruppen--auffindbarkeit"></a>
<a id="arquetipos-de-usuario--visibilidad"></a>
3. [Open the archived section](docs/archive/README.full.en.md#sec-03)

<a id="sec-04"></a>
<a id="comparative-matrix-vs-alternatives"></a>
<a id="vergleichsmatrix-gegenueber-alternativen"></a>
<a id="matriz-comparativa-frente-a-alternativas"></a>
4. [Open the archived section](docs/archive/README.full.en.md#sec-04)

<a id="sec-05"></a>
<a id="architecture--data-flow"></a>
<a id="architektur--datenfluss"></a>
<a id="arquitectura-y-flujo-de-datos"></a>
5. [Open the archived section](docs/archive/README.full.en.md#sec-05)

<a id="sec-06"></a>
<a id="ascii-topology"></a>
<a id="ascii-topologie"></a>
<a id="topologia-ascii"></a>
6. [Open the archived section](docs/archive/README.full.en.md#sec-06)

<a id="sec-07"></a>
<a id="multi-agent-interaction-sequence"></a>
<a id="multi-agenten-interaktionssequenz"></a>
<a id="secuencia-de-interacción-multi-agente"></a>
7. [Open the archived section](docs/archive/README.full.en.md#sec-07)

<a id="sec-08"></a>
<a id="governance--runtime-invariants"></a>
<a id="governance--laufzeit-invarianten"></a>
<a id="invariantes-de-gobernanza-y-ejecución"></a>
8. [Open the archived section](docs/archive/README.full.en.md#sec-08)

<a id="sec-09"></a>
<a id="quick-start"></a>
<a id="schnellstart"></a>
<a id="inicio-rápido"></a>
9. [Open the archived section](docs/archive/README.full.en.md#sec-09)

<a id="sec-10"></a>
<a id="core-concepts--primitives"></a>
<a id="kernkonzepte--primitive-details"></a>
<a id="conceptos-clave-detalles"></a>
10. [Open the archived section](docs/archive/README.full.en.md#sec-10)

<a id="sec-11"></a>
<a id="finding-things--advanced-filtering"></a>
<a id="gezieltes-suchen--filterung"></a>
<a id="búsqueda-precisa-y-filtros"></a>
11. [Open the archived section](docs/archive/README.full.en.md#sec-11)

<a id="sec-12"></a>
<a id="multi-agent-session-coordination"></a>
<a id="multi-agenten-sitzungskoordination"></a>
<a id="coordinación-de-sesiones-multi-agente"></a>
12. [Open the archived section](docs/archive/README.full.en.md#sec-12)

<a id="sec-13"></a>
<a id="runtime-language-contract"></a>
<a id="laufzeit-sprachvertrag"></a>
<a id="contrato-de-idioma-en-ejecución"></a>
13. [Open the archived section](docs/archive/README.full.en.md#sec-13)

<a id="sec-14"></a>
<a id="database-schema--state-isolation"></a>
<a id="datenbankschema--status-isolation"></a>
<a id="esquema-de-base-de-datos-y-aislamiento"></a>
14. [Open the archived section](docs/archive/README.full.en.md#sec-14)

<a id="sec-15"></a>
<a id="sibling-ecosystem--positioning"></a>
<a id="geschwister-oekosystem--positionierung"></a>
<a id="ecosistema-hermano-y-posicionamiento"></a>
15. [Open the archived section](docs/archive/README.full.en.md#sec-15)

<a id="sec-16"></a>
<a id="testing--quality-gates"></a>
<a id="testen--qualitaetstore"></a>
<a id="pruebas-y-verificacion"></a>
16. [Open the archived section](docs/archive/README.full.en.md#sec-16)

<a id="sec-17"></a>
<a id="third-party-licenses--transparency"></a>
<a id="drittanbieter-lizenzen--transparenz"></a>
<a id="licencias-de-terceros-y-transparencia"></a>
17. [Open the archived section](docs/archive/README.full.en.md#sec-17)

<a id="sec-18"></a>
<a id="security-policy--liability"></a>
<a id="sicherheitsrichtlinie--haftung"></a>
<a id="politica-de-seguridad-y-responsabilidad"></a>
<a id="license--liability"></a>
<a id="lizenz--haftung"></a>
<a id="licencia-y-responsabilidad"></a>
<a id="security-policy--vulnerability-reporting"></a>
<a id="sicherheitsrichtlinie--meldewege"></a>
<a id="política-de-seguridad-y-reporte-de-vulnerabilidades"></a>
18. [Open the archived section](docs/archive/README.full.en.md#sec-18)
