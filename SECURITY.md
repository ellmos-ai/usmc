# Security policy

## Deutsch

### Versionen

Die Paketmetadaten nennen derzeit Version 0.3.0. Diese Richtlinie verspricht keine Sicherheitswartung für frühere Versionszweige. Prüfe vor dem Einsatz den aktuellen Quellstand, die Release-Hinweise und die CI-Ergebnisse.

### Sicherheitslücken melden

Bitte melde Schwachstellen nicht öffentlich. Verwende [GitHub Private Vulnerability Reporting](https://github.com/ellmos-ai/usmc/security/advisories/new). Falls dieser Weg nicht verfügbar ist, nutze `security@ellmos.ai`. Füge, soweit möglich, betroffene Version, Reproduktionsschritte und beobachtete Auswirkungen bei. Teile keine echten Nutzerdaten oder Zugangsdaten in einem Bericht.

### Reaktionsziele

Die Maintainer streben eine erste Rückmeldung innerhalb von 48 Stunden und eine Triage innerhalb von fünf Werktagen an. Das sind Arbeitsziele, keine vertragliche Service-Level-Zusage; Zeiten können je nach Verfügbarkeit und Schweregrad abweichen. Eine Fehlerbehebung oder ein Veröffentlichungszeitpunkt wird nicht zugesagt.

### Quellumfang und Betriebsgrenzen

USMC speichert Datensätze in einer SQLite-Datei. Der Standardpfad ist `~/.usmc/usmc_memory.db`; `USMC_DB`, `--db` und das Python-Argument `db_path` können ihn überschreiben. Ein benutzerdefinierter Pfad ist nicht auf das Home-Verzeichnis beschränkt. Die Datei unterliegt den Rechten des Hosts; USMC verschlüsselt sie nicht selbst und entfernt gespeicherte Datensätze nicht automatisch.

Die geprüften Paketmodule enthalten keinen direkten HTTP-Client. Das ist eine begrenzte Aussage über den Quellstand, keine Egress-Firewall: Installation, Git/Python-Buildwerkzeuge und aufrufende Programme können Netzwerkzugriff verwenden. USMC erstellt keine Sandbox und ändert die Rechte des gestarteten Prozesses nicht; der Prozess erbt die Rechte seines Launchers.

SQLite-Transaktionen und WAL regeln Datenbankzugriffe. Agentenkennungen sind Datenlabels, keine Prozess-Authentifizierung oder Betriebssystem-Sperre. Anwendungen bleiben für Zugriff, Pfadwahl, Sicherungen und Aufbewahrung verantwortlich. `USMC_MEMORY_UNION=1` aktiviert einen optionalen Schema-Migrationspfad; lies die zugehörigen Hinweise und Tests, bevor du ihn auf vorhandenen Daten nutzt.

Die Software und diese Dokumentation sind keine Zertifizierung, vollständige Sicherheitsprüfung oder Rechtsberatung. Wenn du möglicherweise personenbezogene oder vertrauliche Daten speicherst, prüfe Zweck, Rechtsgrundlage, Zugriff, Sicherung und Aufbewahrung für deinen Einsatz.

## English

### Versions

The package metadata currently declares version 0.3.0. This policy does not promise security maintenance for earlier release lines. Before use, check the current source revision, release notes, and CI results.

### Reporting a vulnerability

Please do not disclose vulnerabilities in a public issue. Use [GitHub Private Vulnerability Reporting](https://github.com/ellmos-ai/usmc/security/advisories/new). If that route is unavailable, contact `security@ellmos.ai`. Include the affected version, reproduction steps, and observed impact where possible. Do not include real user data or credentials in a report.

### Response targets

Maintainers aim to acknowledge reports within 48 hours and triage them within five business days. These are working targets, not a contractual service-level commitment; timing may vary with availability and severity. No fix or release date is promised.

### Source scope and operating boundaries

USMC stores records in an SQLite file. The default path is `~/.usmc/usmc_memory.db`; `USMC_DB`, `--db`, and the Python `db_path` argument can override it. A custom path is not restricted to the home directory. The file uses host filesystem permissions; USMC does not encrypt it itself or automatically remove stored records.

The reviewed package modules contain no direct HTTP client. This is a bounded statement about the source, not an egress firewall: installation, Git/Python build tools, and calling programs may use the network. USMC does not create a sandbox or change the launched process's privileges; the process inherits privileges from its launcher.

SQLite transactions and WAL govern database access. Agent identifiers are data labels, not process authentication or an operating-system lock. Applications remain responsible for access, path choice, backups, and retention. `USMC_MEMORY_UNION=1` enables an optional schema migration path; read its guidance and tests before enabling it on existing data.

The software and this document are not a certification, complete security audit, or legal advice. If you may store personal or confidential data, assess purpose, legal basis, access, backups, and retention for your deployment.