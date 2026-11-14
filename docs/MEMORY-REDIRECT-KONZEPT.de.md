# Konzept: Memory-Ablagen der Agenten auf USMC umleiten (Entscheidungsvorlage)

> Status: Entwurf zur Entscheidung, nichts davon ist umgesetzt. Es wurden keine Memory-Dateien verschoben oder importiert.
> Auslöser: Nutzerwunsch vom 2026-11-13, Ticket T-20261113-611040941 („USMC soll bei der Installation die Memory-Ablagen der Agenten auf USMC umleiten, zumindest bei anderen Nutzern“).
> Herkunft der Belege: **Ist-Stand ASUS-GEI 2026-11-13** (aus dem Ticket übernommen, hier nicht nachgemessen) und **WS-Messung 2026-11-14** (WORKSTATION-LG, eigene Messung, nur lesend). Was nicht gemessen wurde, steht ausdrücklich als „nicht gemessen“.

## 1. Ausgangslage im USMC-Modul (WS-Messung, Stand `origin/main` 7fc26e8)

- **Kein Installer-Hook.** `pip install` legt nur den Einstiegspunkt `usmc = usmc.cli:main` an (`pyproject.toml`, `[project.scripts]`). Es gibt keinen Post-Install-Schritt, kein Agenten-Discovery und keinen Import- oder Umleitungspfad im Paket.
- **CLI-Befehle** (`usmc/cli.py`): `status`, `fact`, `facts`, `note`, `working`, `clear`, `lesson`, `lessons`, `feedback`, `review`, `policy`, `deliver`, `context`, `start`, `end`, `changes`. Ein Befehl für Import oder Konfiguration der Agenten fehlt.
- **Vorhandene Bausteine, auf denen ein Import aufsetzen kann:**
  - `lesson` mit `--source-kind import`, `--source-key`, `--episode-key`, `--source-hash`: ein Aufruf mit Schlüsselpaar ist idempotent (identischer Wiederholungsaufruf liefert die vorhandene Zeile, abweichende Nutzlast schlägt ohne Änderung fehl). Neue geschlüsselte Lektionen starten mit Gewicht 0,20 und Status `review`.
  - `fact` (`add_fact`): schreibt oder aktualisiert nach Konfidenz (überschreibt nur bei gleicher oder höherer Konfidenz); kein Herkunftsfeld.
  - `--privacy-scope` (`local|private|shared|public`) und `--sensitive-source`.
  - `memory_union` (Vereinigungsschema BACH = OCEAN) ist opt-in (`USMC_MEMORY_UNION=1`).
- Ein Import- und Umleitungsweg ist also **neu zu bauen**. Die Idempotenz und die Herkunftsfelder sind vorhanden.

## 2. Heutige Ablage je Agent

| Agent | Ablage (WS-Messung 2026-11-14) | Ist-Stand ASUS-GEI 2026-11-13 (Ticket) |
|---|---|---|
| Claude Code | `~/.claude/projects/<projekt-slug>/memory/` je Projekt-Silo. WS: 56 Dateien im Home-Silo `C--Users-lukas`, 16 in `C--Users-lukas-OneDrive`, dazu mehrere kleine Silos (0 bis 7 Dateien). `autoMemoryEnabled: true`, **kein** `autoMemoryDirectory` gesetzt. | MEMORY.md plus gut 130 Dateien unter `~/.claude/projects/C--Users-User/memory`; MEMORY.md vollständig nur in Home-Sitzungen. |
| Codex | `~/.codex/memories/` (8 Einträge: `MEMORY.md`, `memory_summary.md`, `automation_memory_proxy_…md`, Unterordner `automations/`, `extensions/`). Hooks: `~/.codex/hooks.json` mit MemoryHooker (SessionStart, UserPromptSubmit). MemoryHooker-Config `~/.codex/memoryhooker.toml`: `backend.order = ["gardener", "files"]`, **USMC steht dort nicht in der Kette**. | `~/.codex/memories/`; Treffer vom MemoryHooker nur bei SessionStart. |
| Gemini/agy | `~/.gemini/memory.md` (29 Zeilen), `memory.txt` (31), `MEMORY.md` (29), `memory.json`, `memory/` (1 Datei), `AUTOMATIONS-MEMORY.md`, `automations_memory.json`, `antigravity_automation_memory.json`, `githubbot_automation_memory.json`. **Keine MemoryHooker-Hooks**: `~/.gemini/settings.json` enthält keinen `hooks`-Abschnitt. | Dieselben Dateinamen; im Hook-Register `.SYNC/hooks/adoption/laptop.json` keine MemoryHooker-Hooks. Die Annahme des Nutzers, Gemini habe solche Hooks, ist auf beiden Hosts nicht belegt; neuere Antigravity-Versionen nicht geprüft. |
| Kimi | Keine eigene Memory-Datei gefunden (`~/.kimi-code/` enthält `config.toml`, `hooks/`, `sessions/`, `session_index.jsonl`, `hook-state/`, kein `memory*`). `config.toml` verdrahtet MemoryHooker als `[[hooks]]`. | MemoryHooker-Backend `files` als drittes Kettenglied nach `usmc` und `gardener`. |
| USMC selbst | `~/.usmc/usmc_memory.db` (kanonische DB). | Cross-Host-Abgleich über `sqlite-transit-sync` laut Recheck 2026-08-26 `CARRIER_GREEN / APPLICATION_CONTRACT_BLOCKED` (active=false; Ticket T-20260727-04). |

Nicht gemessen: Inhalte und Duplikatquote der Bestände, Verhalten von Claude Code bei geändertem `autoMemoryDirectory` (nur aus Ticket als Option bekannt), tatsächliche USMC-Backend-Konfiguration von MemoryHooker auf Kimi/Claude auf WS.

## 3. Grundprinzipien des Konzepts

1. **Umleiten heißt Schreibweg und Leseweg, nicht Dateien löschen.** Der Bestand bleibt unangetastet, bis der Nutzer die Migration ausdrücklich freigibt.
2. **Was alle Agenten betrifft, gehört nach USMC** (Regel vom 2026-11-13, USMC-Lektion 140). Was nur die Harness eines Agenten betrifft, bleibt dort und bekommt höchstens einen Zeiger.
3. **Installer ändert nichts ohne Zustimmung.** Standard ist ein reiner Probelauf (Dry-Run) mit Bericht. Änderungen an Agenten-Konfigurationen sind opt-in je Agent, mit Backup und Rückrollweg.
4. **Herkunft vor Menge.** Jede importierte Zeile trägt Agent, Quellpfad und Inhaltshash.

## 4. Mechanik je Agent

### 4.1 Claude Code
- **Schreibweg:** zwei Optionen. (a) `autoMemoryDirectory` in `~/.claude/settings.json` auf einen von USMC verwalteten Ordner setzen; dort entstehen weiter Dateien, ein USMC-Wächter importiert sie. (b) Regeldatei-Zeiger in der globalen `CLAUDE.md` („Allgemeines Wissen: `usmc fact` / `usmc lesson`“) plus ein Hook (Stop oder SessionEnd), der neue Memory-Dateien einsammelt. Empfehlung (b) für fremde Nutzer, weil es nichts am Speicherort der Harness ändert; (a) erst nach Test, ob die Silostruktur pro Projekt erhalten bleibt.
- **Leseweg:** MemoryHooker mit `usmc` als erstem Backend (SessionStart, UserPromptSubmit). MEMORY.md bleibt als Index erhalten; Claude lädt sie unabhängig von USMC.
- **Import:** je Silo Datei für Datei: Frontmatter (`name`, `description`, `type`) auslesen, `type: user|feedback|project|reference` auf `fact`-Kategorie bzw. `lesson` abbilden, `--source-kind import --source-key claude:<silo-slug>/<dateiname> --episode-key <sha256 des Inhalts>`. Silo-Slug und Dateiname sind stabile Schlüssel, der Hash erkennt Änderungen.
- **Bleibt agentenspezifisch:** MEMORY.md-Index, Projekt-Silo-Struktur, Harness-Eigenheiten (Tool- und Hook-Besonderheiten dieser Installation).
- **Risiken:** Verlust der Silo-Trennung (private Projektnotizen werden global lesbar; `--privacy-scope private` und Filter nötig); `autoMemoryDirectory` ändert das Verhalten der Harness (Wirkung ungeprüft); MEMORY.md und USMC driften auseinander, wenn beide beschrieben werden.

### 4.2 Codex
- **Schreibweg:** Codex hat keinen konfigurierbaren Memory-Ordner im Konzept belegt. Hook auf `Stop`/`SessionEnd` (laut globaler Regel vorhandene Events) oder Regeldatei-Zeiger in `GPT.md`/`AGENTS.md`. `~/.codex/memories/` wird von der App selbst geschrieben und bleibt unverändert.
- **Leseweg:** `memoryhooker.toml`: `usmc` an den Anfang von `backend.order` (heute `gardener`, `files`).
- **Import:** `MEMORY.md` und `memory_summary.md` als Quelle; `automation_memory_proxy_*.md` und `automations/` sind Automationszustand und gehören **nicht** in USMC-Lektionen.
- **Bleibt agentenspezifisch:** Automationszustand, App-Zustand (`state_5.sqlite` u. ä.).
- **Risiken:** App-eigene Konsolidierung (`memory-writing-agent`) kann Dateien umschreiben, der Hash ändert sich, es entstehen Folgeversionen statt Duplikate (Gewichtung und `review`-Status fangen das ab, kostet Pflege); Änderung von `hooks.json`/`config.toml` verlangt erneutes Vertrauen über `/hooks`.

### 4.3 Gemini/agy
- **Schreibweg:** Es gibt auf WS und laut Ticket auf ASUS-GEI keine Hooks. Ohne Hook bleibt nur der Regeldatei-Zeiger (`GEMINI.md`: „Allgemeines Wissen per `usmc …` ablegen“) und der Datei-Weg (agy schreibt in seinen Workspace; ein Wächter importiert).
- **Leseweg:** Kein Hook-Weg belegt; Ersatz: statisch erzeugter USMC-Kontext (`usmc context`) in eine von Gemini ohnehin gelesene Datei, oder Hook, sobald Antigravity ihn unterstützt (nicht geprüft).
- **Import:** `memory.md`/`memory.txt`/`MEMORY.md` (inhaltsähnlich, Dublettengefahr), `memory.json`, `memory/`. `AUTOMATIONS-MEMORY.md` und die `*_automation_memory.json` sind Automationsprotokolle und gehören laut `CLAUDE.md` nicht in Boot-Dateien; sie bleiben agentenspezifisch.
- **Risiken:** schwächster Kandidat, weil der Leseweg fehlt; die drei ähnlichen Memory-Dateien erzeugen Dubletten, wenn man sie getrennt importiert; Annahme „Gemini hat Hooks“ ungeprüft.

### 4.4 Kimi
- **Schreibweg:** Kimi besitzt keine eigene Memory-Datei (WS gemessen). Hooks sind vorhanden (`[[hooks]]` in `config.toml`), ein Schreibhook nach USMC ist technisch möglich (Details nicht geprüft).
- **Leseweg:** MemoryHooker ist bereits verdrahtet; laut Ticket-Ist-Stand ASUS-GEI ist `usmc` dort bereits erstes Backend. Auf WS nicht gemessen.
- **Import:** nichts zu importieren.
- **Risiken:** gering; Kimi ist der Agent, der den USMC-Weg am weitesten schon geht.

## 5. Import des Bestands (agentenübergreifend)

1. **Probelauf zuerst:** `usmc import --agent <name> --dry-run` (neuer Befehl) zählt Dateien, Kandidaten, erwartete Duplikate und Konflikte und schreibt nichts.
2. **Schlüsselschema:** `source_key = <agent>:<relativer Pfad>`, `episode_key = sha256(Inhalt)`, `source_kind = import`, `privacy_scope = private` als Standard. Wiederholter Lauf erzeugt keine Dubletten; geänderte Dateien erzeugen eine neue Episode statt einer stillen Überschreibung.
3. **Inhaltsduplikate zwischen Agenten:** gleiche Aussage in Claude- und Gemini-Memory würde zwei Lektionen ergeben. Vorschlag: normalisierter Inhaltshash als zusätzlicher Dublettenschlüssel im Import, Treffer werden als Verweis auf die erste Fassung gebucht, nicht neu angelegt.
4. **Zustand und Protokolle ausschließen:** Automationsgedächtnis, Session-Zustand, Tokens, Zugangsdaten. Der Import prüft auf Geheimnisse (nur Fundorte, nie Werte, siehe USMC-Regel) und überspringt verdächtige Dateien mit Meldung.
5. **Gewichtung:** importierte Lektionen starten mit dem Vertragsgewicht 0,20 und Status `review`; Fakten über `fact` mit Konfidenz < 1,0 (z. B. 0,6), damit spätere echte Einträge sie überschreiben.

## 6. Installer-Verhalten für fremde Nutzer

- `pip install usmc` bleibt nebenwirkungsfrei (Paketregel „keine Import-Seiteneffekte“).
- Neuer, getrennter Schritt `usmc setup` (interaktiv), der je gefundenen Agenten fragt: Bestand importieren? Schreibweg umleiten? Leseweg (MemoryHooker-Backend) aktivieren? Jede Antwort ist einzeln und widerrufbar; vor jeder Änderung Backup der betroffenen Konfiguration, danach Readback.
- Für die eigene Instanz des Nutzers gilt dasselbe, aber ohne automatische Migration (siehe Nutzerfrage 1).
- Mehrere Rechner: Ohne aktiven USMC-Abgleich (`sqlite-transit-sync`, Ticket T-20260727-04) meint „alle“ nur den lokalen Host. Das Konzept ist davon unabhängig lieferbar, die Aussage „alle Agenten auf allen Rechnern“ erst nach Aktivierung des Abgleichs.

## 7. Risiken im Überblick

- Privatsphäre: Silo-Notizen werden durch Zentralisierung breiter lesbar.
- Doppelte Wahrheit: MEMORY.md und USMC beide beschreibbar führt zum Auseinanderlaufen; eine Seite muss führen.
- Harness-Verhalten: Konfigurationsänderungen (`autoMemoryDirectory`, `hooks.json`, `config.toml`) wurden nicht getestet.
- Qualität: Import ohne Kuratierung füllt USMC mit Rauschen; Gewicht 0,20 und `review` begrenzen die Wirkung, ersetzen die Kuratierung nicht.
- Reichweite: Gemini hat keinen belegten Leseweg.

## 8. Nutzerfragen

1. Sollen die **eigenen Claude-Einträge des Nutzers** (Home-Silo, 56 Dateien auf WS) nach USMC migriert werden, oder nur bei anderen Nutzern installiert werden? (Offen aus der Sitzung vom 2026-11-13.)
2. Soll für Claude Code der **Regeldatei-/Hook-Weg (4.1 b)** oder `autoMemoryDirectory` (4.1 a) getestet werden?
3. Wer **führt** bei MEMORY.md und USMC: soll MEMORY.md nur noch Index und Zeiger sein?
4. Darf der Import Claude-Silos, die als `private` markiert werden sollen, nach USMC ziehen, oder nur das Home-Silo?
5. **Gemini:** Hook-Unterstützung zuerst klären, oder zunächst nur Zeiger in `GEMINI.md`?
6. **Mehrere Rechner:** Soll das Konzept bis zum aktiven USMC-Abgleich (T-20260727-04) zurückgestellt oder lokal begonnen werden?
7. Soll `usmc setup` ein Teil des USMC-Pakets werden (neue Funktion, Doku und Tests im Modul) oder ein separates Hilfsskript bleiben?
