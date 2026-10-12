<img src="assets/banner.png" width="100%" alt="Banner de USMC">

# USMC — United Shared Memory Client

[![CI](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml/badge.svg)](https://github.com/ellmos-ai/usmc/actions/workflows/ci.yml)
[![Licencia MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)

**Idiomas:** [English](README.md) · [Deutsch](README_de.md) · [Español](README_es.md)

> Esta página breve sustituye el antiguo `README_es.md` extenso del [commit fuente `bf281f1`](https://github.com/ellmos-ai/usmc/blob/bf281f1d68e9e6af44db9d12588a000fac531a61/README_es.md). La edición archivada corregida, ahora en [docs/archive/README.full.es.md](docs/archive/README.full.es.md), conserva la guía detallada; el commit enlazado mantiene la revisión fuente original.

USMC es un paquete de Python y una CLI que guarda hechos, lecciones, notas de trabajo y traspasos de sesión en SQLite. La lista declarada de dependencias directas en ejecución está vacía; requiere Python 3.10 o posterior.

## Datos y alcance de ejecución

La ruta predeterminada de la base de datos es `~/.usmc/usmc_memory.db`. `USMC_DB` o `--db` permiten elegir otra ruta; las rutas personalizadas se usan tal como se indican. USMC no purga registros automáticamente. Elige una ruta local adecuada y gestiona permisos, copias de seguridad y retención según tu uso.

El código fuente del paquete revisado no contiene un cliente HTTP directo. La instalación desde GitHub y la compilación usan herramientas con capacidad de red, y los agentes u otros procesos que llaman a USMC pueden usar la red por separado. USMC no proporciona firewall ni sandbox; los procesos heredan los privilegios de quien los inicia.

## Instalar y probar

Instalación desde el repositorio Git (requiere Git, herramientas de empaquetado de Python y acceso a la red):

```console
python -m pip install "git+https://github.com/ellmos-ai/usmc.git"
usmc --help
usmc status
```

Para una copia local: `python -m pip install -e ".[test]"`. El extra `[test]` es para desarrollo y pruebas.

```python
from usmc import USMCClient

client = USMCClient(agent_id="codex")
client.add_fact("project", "status", "en curso", confidence=0.8)
print(client.generate_context())
```

## Documentación

- [Guía completa y ejemplos de API](docs/archive/README.full.es.md)
- [Seguridad y tratamiento de datos](SECURITY.md)
- [Contribución y comandos de prueba](CONTRIBUTING.md)
- [Inventario de licencias de terceros](THIRD_PARTY_LICENSES.md) y [versión de texto](THIRD_PARTY_LICENSES.txt)
- [Guía para máquinas](llms.txt)
- [Registro de cambios](CHANGELOG.md)

## Proyectos relacionados

[BACH](https://github.com/ellmos-ai/bach) puede usar el esquema opcional de memoria compartida definido por `memory_union.contract.json` de USMC; consulta en la guía completa los detalles de migración y activación. Describe una relación de esquema, no una instalación automática ni un límite de seguridad.
[ellmos-stack](https://github.com/ellmos-ai/ellmos-stack) incluye USMC como componente de memoria curada en una pila de investigación autohospedada; su instalador obtiene USMC de un commit Git fijado. Esta relación describe la composición del stack; USMC no instala ni inicia ellmos-stack.
[GARDENER](https://github.com/ellmos-ai/gardener) ofrece plantillas opcionales de solo lectura para instantáneas réplica de USMC; están desactivadas por defecto y requieren una instantánea creada por un mecanismo de sincronización separado y la activación del llamador.

## Licencia

El proyecto se ofrece bajo la [licencia MIT](LICENSE); los detalles de atribución están en [NOTICE](NOTICE).

### Enlaces de secciones anteriores

<a id="sec-01"></a>
<a id="características-principales"></a>
<a id="key-features"></a>
<a id="hauptmerkmale"></a>
1. [Secci?n archivada](docs/archive/README.full.es.md#sec-01)

<a id="sec-02"></a>
<a id="capacidades-clave--primitivas"></a>
<a id="core-capabilities--primitives"></a>
<a id="kernkonzepte--primitive"></a>
2. [Secci?n archivada](docs/archive/README.full.es.md#sec-02)

<a id="sec-03"></a>
<a id="arquetipos-de-usuario--visibilidad"></a>
<a id="target-personas--discoverability"></a>
<a id="zielgruppen--auffindbarkeit"></a>
3. [Secci?n archivada](docs/archive/README.full.es.md#sec-03)

<a id="sec-04"></a>
<a id="matriz-comparativa-frente-a-alternativas"></a>
<a id="comparative-matrix-vs-alternatives"></a>
<a id="vergleichsmatrix-gegenueber-alternativen"></a>
4. [Secci?n archivada](docs/archive/README.full.es.md#sec-04)

<a id="sec-05"></a>
<a id="arquitectura-y-flujo-de-datos"></a>
<a id="architecture--data-flow"></a>
<a id="architektur--datenfluss"></a>
5. [Secci?n archivada](docs/archive/README.full.es.md#sec-05)

<a id="sec-06"></a>
<a id="topologia-ascii"></a>
<a id="ascii-topology"></a>
<a id="ascii-topologie"></a>
6. [Secci?n archivada](docs/archive/README.full.es.md#sec-06)

<a id="sec-07"></a>
<a id="secuencia-de-interacción-multi-agente"></a>
<a id="multi-agent-interaction-sequence"></a>
<a id="multi-agenten-interaktionssequenz"></a>
7. [Secci?n archivada](docs/archive/README.full.es.md#sec-07)

<a id="sec-08"></a>
<a id="invariantes-de-gobernanza-y-ejecución"></a>
<a id="governance--runtime-invariants"></a>
<a id="governance--laufzeit-invarianten"></a>
8. [Secci?n archivada](docs/archive/README.full.es.md#sec-08)

<a id="sec-09"></a>
<a id="inicio-rápido"></a>
<a id="quick-start"></a>
<a id="schnellstart"></a>
9. [Secci?n archivada](docs/archive/README.full.es.md#sec-09)

<a id="sec-10"></a>
<a id="conceptos-clave-y-primitivas"></a>
<a id="core-concepts--primitives"></a>
<a id="kernkonzepte--detaillierte-primitive"></a>
10. [Secci?n archivada](docs/archive/README.full.es.md#sec-10)

<a id="sec-11"></a>
<a id="búsqueda-precisa-y-filtros"></a>
<a id="finding-things--advanced-filtering"></a>
<a id="gezieltes-suchen--filterung"></a>
11. [Secci?n archivada](docs/archive/README.full.es.md#sec-11)

<a id="sec-12"></a>
<a id="coordinación-de-sesiones-multi-agente"></a>
<a id="multi-agent-session-coordination"></a>
<a id="multi-agenten-sitzungskoordination"></a>
12. [Secci?n archivada](docs/archive/README.full.es.md#sec-12)

<a id="sec-13"></a>
<a id="contrato-de-idioma-en-ejecución"></a>
<a id="runtime-language-contract"></a>
<a id="laufzeit-sprachvertrag"></a>
13. [Secci?n archivada](docs/archive/README.full.es.md#sec-13)

<a id="sec-14"></a>
<a id="esquema-de-base-de-datos-y-aislamiento"></a>
<a id="database-schema--state-isolation"></a>
<a id="datenbankschema--status-isolation"></a>
14. [Secci?n archivada](docs/archive/README.full.es.md#sec-14)

<a id="sec-15"></a>
<a id="ecosistema-hermano-y-posicionamiento"></a>
<a id="sibling-ecosystem--positioning"></a>
<a id="geschwister-oekosystem--positionierung"></a>
15. [Secci?n archivada](docs/archive/README.full.es.md#sec-15)

<a id="sec-16"></a>
<a id="pruebas-y-verificacion"></a>
<a id="testing--quality-gates"></a>
<a id="testen--qualitaetstore"></a>
16. [Secci?n archivada](docs/archive/README.full.es.md#sec-16)

<a id="sec-17"></a>
<a id="licencias-de-terceros-y-transparencia"></a>
<a id="third-party-licenses--transparency"></a>
<a id="drittanbieter-lizenzen--transparenz"></a>
17. [Secci?n archivada](docs/archive/README.full.es.md#sec-17)

<a id="sec-18"></a>
<a id="politica-de-seguridad-y-responsabilidad"></a>
<a id="security-policy--liability"></a>
<a id="sicherheitsrichtlinie--haftung"></a>
<a id="licencia-y-responsabilidad"></a>
<a id="license--liability"></a>
<a id="lizenz--haftung"></a>
<a id="política-de-seguridad-y-reporte-de-vulnerabilidades"></a>
<a id="security-policy--vulnerability-reporting"></a>
<a id="sicherheitsrichtlinie--meldewege"></a>
18. [Secci?n archivada](docs/archive/README.full.es.md#sec-18)
