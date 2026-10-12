# Contributing to USMC

[English](#english) | [Deutsch](#deutsch)

<a id="english"></a>
## English

Thank you for your interest in contributing to USMC.

### Project behavior

USMC is a Python package and CLI that stores facts, lessons, working notes, and session handoffs in SQLite. The project declares no direct runtime dependencies. Its database path defaults to `~/.usmc/usmc_memory.db` and can be overridden; do not assume that custom paths stay within a home directory. The package source review found no direct HTTP client, but Git, pip, build tools, and callers may use the network. The package does not sandbox callers, change process privileges, or automatically prune records.

### Development

Use a source checkout and a Python version supported by `pyproject.toml` (`>=3.10`). Install the test tools with:

```console
python -m pip install -e ".[test]"
```

Run the relevant checks before submitting changes:

```console
python -m pytest -ra -v
python -m ruff check .
python -m compileall -q usmc tests
git diff --check
```

Tests must use temporary databases and isolated home/config paths. They must not read or mutate a maintainer's real `~/.usmc` database. Tests that enable `USMC_MEMORY_UNION` should use a disposable database and verify backup/migration effects there.

Keep the package version unchanged unless a maintainer explicitly authorizes a version change. Record user-visible changes under `## [Unreleased]` in `CHANGELOG.md`. Do not describe a source observation as a firewall, certification, complete dependency audit, or deployment guarantee.

For security reports, follow [SECURITY.md](SECURITY.md) and use its private reporting channel.

<a id="deutsch"></a>
## Deutsch

Vielen Dank für dein Interesse an einer Mitarbeit an USMC.

### Projektverhalten

USMC ist ein Python-Paket mit CLI, das Fakten, Lessons Learned, Arbeitsnotizen und Sitzungsübergaben in SQLite speichert. Das Projekt deklariert keine direkten Laufzeit-Abhängigkeiten. Der Standardpfad der Datenbank ist `~/.usmc/usmc_memory.db` und kann überschrieben werden; benutzerdefinierte Pfade bleiben nicht zwingend im Home-Verzeichnis. Die geprüften Paketmodule enthalten keinen direkten HTTP-Client, aber Git, pip, Build-Werkzeuge und aufrufende Programme können das Netzwerk nutzen. Das Paket isoliert Aufrufer nicht in einer Sandbox, ändert keine Prozessrechte und löscht Datensätze nicht automatisch.

### Entwicklung

Arbeite mit einem Quellcheckout und einer von `pyproject.toml` unterstützten Python-Version (`>=3.10`). Installiere die Testwerkzeuge mit:

```console
python -m pip install -e ".[test]"
```

Führe vor dem Einreichen die passenden Prüfungen aus:

```console
python -m pytest -ra -v
python -m ruff check .
python -m compileall -q usmc tests
git diff --check
```

Tests müssen temporäre Datenbanken und isolierte Home-/Konfigurationspfade verwenden. Sie dürfen keine echte `~/.usmc`-Datenbank eines Maintainers lesen oder ändern. Tests, die `USMC_MEMORY_UNION` aktivieren, verwenden eine wegwerfbare Datenbank und prüfen Sicherungs- und Migrationseffekte ausschließlich dort.

Ändere die Paketversion nur nach ausdrücklicher Freigabe durch einen Maintainer. Erfasse sichtbare Änderungen unter `## [Unreleased]` in `CHANGELOG.md`. Beschreibe eine Quellbeobachtung nicht als Firewall, Zertifizierung, vollständiges Abhängigkeits-Audit oder Bereitstellungsgarantie.

Sicherheitsmeldungen gehören gemäß [SECURITY.md](SECURITY.md) auf den dort beschriebenen privaten Meldeweg.