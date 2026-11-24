<img src="assets/banner.png" width="100%" alt="Banner do USMC">

# USMC — United Shared Memory Client

[![CI](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml/badge.svg)](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/Tests-194%20passed%20%7C%20100%25-brightgreen.svg)](#install-and-try)
[![Dependabot](https://img.shields.io/badge/Dependabot-active-brightgreen.svg)](.github/dependabot.yml)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Zero dependências](https://img.shields.io/badge/Dependencies-0%20runtime-blue.svg)](#data-and-runtime-scope)
[![Armazenamento](https://img.shields.io/badge/Storage-SQLite%20(WAL)-informational.svg)](#data-and-runtime-scope)

**Idiomas:** [English](README.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Português](README_pt.md) · [Русский](README_ru.md) · [简体中文](README_zh.md) · [日本語](README_ja.md) · [العربية](README_ar.md) · [हिन्दी](README_hi.md) · [বাংলা](README_bn.md)

<!-- lang-only: en,fr,pt,ru,zh,ja,ar,hi,bn -->
> Este ponto de entrada conciso substitui o antigo `README.md` extenso do [commit fonte `bf281f1`](https://github.com/ellmos-ai/usmc/blob/bf281f1d68e9e6af44db9d12588a000fac531a61/README.md). Sua edição arquivada corrigida está agora em [docs/archive/README.full.en.md](docs/archive/README.full.en.md) (em inglês); o commit vinculado preserva a revisão original da fonte.
<!-- /lang-only -->

USMC é um pacote Python e uma CLI que armazena fatos, lições aprendidas, notas de trabalho e passagens de sessão no SQLite. A lista declarada de dependências diretas de tempo de execução está vazia; é necessário Python 3.10 ou superior.

<a id="data-and-runtime-scope"></a>
## Dados e escopo de execução

Por padrão, o caminho do banco de dados é `~/.usmc/usmc_memory.db`. Defina `USMC_DB` ou passe `--db` para escolher outro caminho; caminhos personalizados são usados exatamente como fornecidos. O USMC não remove registros armazenados automaticamente. Escolha um caminho local adequado e gerencie suas permissões, backups e retenção conforme o seu caso de uso.

```mermaid
graph LR
  subgraph Agents["Agentes Autônomos"]
    Claude["Claude Code"]
    Gemini["Antigravity / Gemini"]
    Codex["Codex / GPT"]
  end

  subgraph USMC["Arquitetura USMC"]
    Client["Cliente USMC / CLI"]
    DB[("SQLite local (modo WAL)<br/>~/.usmc/usmc_memory.db")]
  end

  Claude -->|"fatos / lições / notas de trabalho"| Client
  Gemini -->|"passagem entre agentes"| Client
  Codex -->|"recuperação de contexto"| Client
  Client <-->|"transações ACID (zero dependências)"| DB
```

O código-fonte revisado do pacote não contém nenhum cliente HTTP direto. A instalação a partir do GitHub ou a compilação do pacote utiliza ferramentas com acesso à rede, e um agente chamador ou outro processo pode usar a rede de forma independente. O USMC não fornece firewall nem sandbox; os processos herdam os privilégios de quem os inicia.

<a id="install-and-try"></a>
## Instalar e testar

Instale a partir da fonte Git (requer ferramentas de empacotamento Git/Python e acesso à rede):

```console
python -m pip install "git+https://github.com/ellmos-ai/usmc.git"
usmc --help
usmc status
usmc setup --dry-run
```

Para uma cópia local, use `python -m pip install -e ".[test]"`. O extra `[test]` destina-se a desenvolvimento e testes.

```python
from usmc import USMCClient

client = USMCClient(agent_id="codex")
client.add_fact("project", "status", "in progress", confidence=0.8)
print(client.generate_context())
```

## Documentação

- [Guia completo e exemplos de API (em inglês)](docs/archive/README.full.en.md)
- [Código de conduta](CODE_OF_CONDUCT.md)
- [Notas sobre segurança e tratamento de dados](SECURITY.md)
- [Contribuição e comandos de teste](CONTRIBUTING.md)
- [Inventário de licenças de terceiros](THIRD_PARTY_LICENSES.md) e [notas de licença em texto simples](THIRD_PARTY_LICENSES.txt)
- [Guia legível por máquina](llms.txt)
- [Registro de alterações](CHANGELOG.md)

## Projetos relacionados

[BACH](https://github.com/ellmos-ai/bach) pode usar o esquema opcional de memória compartilhada definido por `memory_union.contract.json` do USMC; consulte os detalhes de migração e ativação no guia completo. Isso descreve uma relação de esquema, não uma instalação automática ou um limite de segurança.
[ellmos-stack](https://github.com/ellmos-ai/ellmos-stack) compõe o USMC como seu componente de memória curada em uma pilha de pesquisa auto-hospedada; seu instalador obtém o USMC a partir de um commit Git fixado. Isso descreve a composição dessa pilha, não uma garantia de instalação ou inicialização fornecida pelo USMC.
[GARDENER](https://github.com/ellmos-ai/gardener) oferece modelos de origem opcionais somente leitura para instantâneos de réplica do USMC; eles são desativados por padrão e exigem um instantâneo de sincronização separado além da ativação explícita pelo chamador.

## Licença

O projeto é disponibilizado sob a [Licença MIT](LICENSE); os detalhes de atribuição estão em [NOTICE](NOTICE).

### Links para seções anteriores

<a id="sec-01"></a>
<a id="key-features"></a>
<a id="hauptmerkmale"></a>
<a id="características-principales"></a>
1. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-01)

<a id="sec-02"></a>
<a id="core-capabilities--primitives"></a>
<a id="kernkonzepte--primitive"></a>
<a id="conceptos-clave-y-primitivas"></a>
2. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-02)

<a id="sec-03"></a>
<a id="target-personas--discoverability"></a>
<a id="zielgruppen--auffindbarkeit"></a>
<a id="arquetipos-de-usuario--visibilidad"></a>
3. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-03)

<a id="sec-04"></a>
<a id="comparative-matrix-vs-alternatives"></a>
<a id="vergleichsmatrix-gegenueber-alternativen"></a>
<a id="matriz-comparativa-frente-a-alternativas"></a>
4. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-04)

<a id="sec-05"></a>
<a id="architecture--data-flow"></a>
<a id="architektur--datenfluss"></a>
<a id="arquitectura-y-flujo-de-datos"></a>
5. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-05)

<a id="sec-06"></a>
<a id="ascii-topology"></a>
<a id="ascii-topologie"></a>
<a id="topologia-ascii"></a>
6. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-06)

<a id="sec-07"></a>
<a id="multi-agent-interaction-sequence"></a>
<a id="multi-agenten-interaktionssequenz"></a>
<a id="secuencia-de-interacción-multi-agente"></a>
7. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-07)

<a id="sec-08"></a>
<a id="governance--runtime-invariants"></a>
<a id="governance--laufzeit-invarianten"></a>
<a id="invariantes-de-gobernanza-y-ejecución"></a>
8. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-08)

<a id="sec-09"></a>
<a id="quick-start"></a>
<a id="schnellstart"></a>
<a id="inicio-rápido"></a>
9. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-09)

<a id="sec-10"></a>
<a id="core-concepts--primitives"></a>
<a id="kernkonzepte--primitive-details"></a>
<a id="conceptos-clave-detalles"></a>
10. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-10)

<a id="sec-11"></a>
<a id="finding-things--advanced-filtering"></a>
<a id="gezieltes-suchen--filterung"></a>
<a id="búsqueda-precisa-y-filtros"></a>
11. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-11)

<a id="sec-12"></a>
<a id="multi-agent-session-coordination"></a>
<a id="multi-agenten-sitzungskoordination"></a>
<a id="coordinación-de-sesiones-multi-agente"></a>
12. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-12)

<a id="sec-13"></a>
<a id="runtime-language-contract"></a>
<a id="laufzeit-sprachvertrag"></a>
<a id="contrato-de-idioma-en-ejecución"></a>
13. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-13)

<a id="sec-14"></a>
<a id="database-schema--state-isolation"></a>
<a id="datenbankschema--status-isolation"></a>
<a id="esquema-de-base-de-datos-y-aislamiento"></a>
14. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-14)

<a id="sec-15"></a>
<a id="sibling-ecosystem--positioning"></a>
<a id="geschwister-oekosystem--positionierung"></a>
<a id="ecosistema-hermano-y-posicionamiento"></a>
15. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-15)

<a id="sec-16"></a>
<a id="testing--quality-gates"></a>
<a id="testen--qualitaetstore"></a>
<a id="pruebas-y-verificacion"></a>
16. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-16)

<a id="sec-17"></a>
<a id="third-party-licenses--transparency"></a>
<a id="drittanbieter-lizenzen--transparenz"></a>
<a id="licencias-de-terceros-y-transparencia"></a>
17. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-17)

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
18. [Abrir a seção arquivada](docs/archive/README.full.en.md#sec-18)
