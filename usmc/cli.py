# -*- coding: utf-8 -*-
"""
USMC Command-Line Interface
============================

CLI fuer USMC Memory-Operationen.

Verwendung:
    usmc status
    usmc fact system os "Windows 11"
    usmc facts --category system
    usmc note "Aktueller Task: Feature X"
    usmc working
    usmc lesson "Bug-Title" "Problem" "Solution" --severity high
    usmc lessons
    usmc context
    usmc clear

Gezielt suchen statt scrollen (working/facts/lessons):
    usmc working --tags store              # ODER-Verknuepfung bei 'a,b'
    usmc working --tags store,welle --tags-all
    usmc working --agent codex-cli         # Filter, NICHT die Schreib-Identitaet
    usmc working --grep "Partner Center"

Die Filter laufen in der Datenbankabfrage, also vor --limit.

Author: Lukas Geiger
License: MIT
"""

import argparse
import json
import sys
from typing import Optional

from . import __version__
from .client import USMCClient, default_db_path  # noqa: F401 (Re-Export)


def get_client(args) -> USMCClient:
    """Erstellt Client basierend auf CLI-Args."""
    return USMCClient(
        db_path=args.db,  # None -> default_db_path() im Client
        agent_id=args.agent or "cli"
    )


def cmd_status(args) -> int:
    """Zeigt Memory-Statistiken."""
    client = get_client(args)
    status = client.get_status()

    print(f"USMC Memory Status")
    print(f"==================")
    print(f"DB:              {status['db_path']}")
    print(f"Agent:           {status['agent_id']}")
    print(f"Facts:           {status['facts_count']} ({status['confident_facts']} mit confidence >= 0.8)")
    print(f"Working Memory:  {status['working_count']} aktiv")
    print(f"Lessons:         {status['lessons_count']} aktiv")
    print(f"Sessions:        {status['sessions_count']} total")
    return 0


def cmd_fact(args) -> int:
    """Speichert einen Fakt."""
    client = get_client(args)
    result = client.add_fact(
        category=args.category,
        key=args.key,
        value=args.value,
        confidence=args.confidence
    )

    if result.get('merged'):
        print(f"[OK] Fakt gespeichert: {args.key} = {args.value}")
    else:
        print(f"[SKIP] Nicht ueberschrieben: {result.get('reason', 'unknown')}")
    return 0


def _print_empty(args, message: str, names) -> int:
    """Meldet ein leeres Ergebnis -- als JSON-Array, wenn --json gesetzt ist.

    Mit Filtern ist "leer" der Normalfall statt der Ausnahme, und der typische
    Aufrufer ist ein Programm: eine deutsche Prosazeile im --json-Modus wuerde
    dessen Parser brechen.
    """
    if args.json:
        print("[]")
        return 0
    active = [f"{label}={value}" for label, value in names if value]
    hint = f" (Filter aktiv: {', '.join(active)})" if active else ""
    print(message + hint)
    return 0


def cmd_facts(args) -> int:
    """Listet Fakten auf."""
    client = get_client(args)
    facts = client.get_facts(
        category=args.category,
        min_confidence=args.min_confidence,
        agent_id=args.filter_agent,
        grep=args.grep
    )

    if not facts:
        return _print_empty(args, "Keine Fakten gefunden.", [
            ('--category', args.category),
            ('--agent', args.filter_agent),
            ('--grep', args.grep),
        ])

    if args.json:
        print(json.dumps(facts, indent=2, ensure_ascii=False))
    else:
        print(f"{'Category':<12} {'Key':<20} {'Value':<30} {'Conf':>5}")
        print("-" * 70)
        for f in facts:
            val = f['value'][:28] + ".." if len(f['value']) > 30 else f['value']
            print(f"{f['category']:<12} {f['key']:<20} {val:<30} {f['confidence']:>5.2f}")
    return 0


def cmd_note(args) -> int:
    """Speichert eine Notiz."""
    client = get_client(args)
    result = client.add_working(
        content=args.content,
        type=args.type,
        priority=args.priority,
        tags=args.tags
    )
    print(f"[OK] Notiz gespeichert (ID: {result['id']})")
    return 0


def cmd_working(args) -> int:
    """Listet Working Memory auf."""
    client = get_client(args)
    notes = client.get_working(
        limit=args.limit,
        agent_id=args.filter_agent,
        tags=args.tags,
        tags_all=args.tags_all,
        grep=args.grep
    )

    if not notes:
        return _print_empty(args, "Keine aktiven Notizen.", [
            ('--tags' + ('-all' if args.tags_all else ''), args.tags),
            ('--agent', args.filter_agent),
            ('--grep', args.grep),
        ])

    if args.json:
        print(json.dumps(notes, indent=2, ensure_ascii=False))
    else:
        for n in notes:
            prio = f"[P{n['priority']}]" if n['priority'] != 0 else ""
            tags = f" #{n['tags']}" if n['tags'] else ""
            print(f"[{n['id']}] {prio} {n['content'][:60]}{tags}")
    return 0


def cmd_clear(args) -> int:
    """Loescht Working Memory."""
    client = get_client(args)
    count = client.clear_working(agent_only=not args.all)
    print(f"[OK] {count} Eintraege deaktiviert.")
    return 0


def cmd_lesson(args) -> int:
    """Speichert eine Lesson Learned."""
    client = get_client(args)
    result = client.add_lesson(
        title=args.title,
        problem=args.problem,
        solution=args.solution,
        severity=args.severity,
        category=args.category
    )
    print(f"[OK] Lesson gespeichert (ID: {result['id']})")
    return 0


def cmd_lessons(args) -> int:
    """Listet Lessons Learned auf."""
    client = get_client(args)
    lessons = client.get_lessons(
        limit=args.limit,
        severity=args.severity,
        agent_id=args.filter_agent,
        grep=args.grep
    )

    if not lessons:
        return _print_empty(args, "Keine Lessons gefunden.", [
            ('--severity', args.severity),
            ('--agent', args.filter_agent),
            ('--grep', args.grep),
        ])

    if args.json:
        print(json.dumps(lessons, indent=2, ensure_ascii=False))
    else:
        for l in lessons:
            sev = {'critical': '!!!', 'high': '!! ', 'medium': '!  ', 'low': '   '}
            print(f"[{l['id']}] {sev.get(l['severity'], '   ')} {l['title']}")
            print(f"     Problem:  {l['problem'][:50]}")
            print(f"     Solution: {l['solution'][:50]}")
            print()
    return 0


def cmd_context(args) -> int:
    """Generiert Kontext fuer LLM-Prompts."""
    client = get_client(args)
    ctx = client.generate_context(max_items=args.max_items)
    print(ctx)
    return 0


def cmd_session_start(args) -> int:
    """Startet eine neue Session."""
    client = get_client(args)
    result = client.start_session(task=args.task)
    print(f"[OK] Session gestartet (ID: {result['id']})")
    return 0


def cmd_session_end(args) -> int:
    """Beendet eine Session."""
    client = get_client(args)
    success = client.end_session(args.session_id, handoff_notes=args.notes)
    if success:
        print(f"[OK] Session {args.session_id} beendet.")
    else:
        print(f"[ERROR] Session {args.session_id} nicht gefunden.")
        return 1
    return 0


def cmd_changes(args) -> int:
    """Zeigt Aenderungen seit Zeitstempel."""
    client = get_client(args)
    changes = client.get_changes_since(args.since)

    if args.json:
        print(json.dumps(changes, indent=2, ensure_ascii=False))
    else:
        print(f"Aenderungen seit {args.since}:")
        print(f"  Facts:   {len(changes['facts'])}")
        print(f"  Working: {len(changes['working'])}")
        print(f"  Lessons: {len(changes['lessons'])}")
        print(f"  Sync-TS: {changes['sync_timestamp']}")
    return 0


def main(argv: Optional[list] = None) -> int:
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(
        prog='usmc',
        description='USMC - United Shared Memory Client CLI'
    )
    parser.add_argument('--db', '-d', help='Pfad zur Datenbank (default: ~/.usmc/usmc_memory.db, Env USMC_DB)')
    parser.add_argument('--agent', '-a', help='Agent-ID (default: cli)')
    parser.add_argument('--version', '-V', action='version', version=f'usmc {__version__}')

    subparsers = parser.add_subparsers(dest='command', help='Verfuegbare Befehle')

    # status
    p_status = subparsers.add_parser('status', help='Zeigt Memory-Statistiken')
    p_status.set_defaults(func=cmd_status)

    # fact
    p_fact = subparsers.add_parser('fact', help='Speichert einen Fakt')
    p_fact.add_argument('category', choices=['user', 'project', 'system', 'domain'])
    p_fact.add_argument('key', help='Fakt-Schluessel')
    p_fact.add_argument('value', help='Fakt-Wert')
    p_fact.add_argument('--confidence', '-c', type=float, default=1.0, help='Konfidenz (0.0-1.0)')
    p_fact.set_defaults(func=cmd_fact)

    # facts
    p_facts = subparsers.add_parser('facts', help='Listet Fakten auf')
    p_facts.add_argument('--category', '-c', choices=['user', 'project', 'system', 'domain'])
    p_facts.add_argument('--min-confidence', '-m', type=float, default=0.0)
    p_facts.add_argument('--agent', dest='filter_agent', metavar='NAME',
                         help='Nur Fakten dieses Agents (Filter, nicht die Schreib-Identitaet)')
    p_facts.add_argument('--grep', '-g', metavar='BEGRIFF',
                         help='Teilstring in key oder value (ASCII-Gross-/Kleinschreibung egal)')
    p_facts.add_argument('--json', '-j', action='store_true', help='JSON-Ausgabe')
    p_facts.set_defaults(func=cmd_facts)

    # note
    p_note = subparsers.add_parser('note', help='Speichert eine Notiz')
    p_note.add_argument('content', help='Notiz-Inhalt')
    p_note.add_argument('--type', '-t', choices=['note', 'context', 'scratchpad', 'loop'], default='note')
    p_note.add_argument('--priority', '-p', type=int, default=0)
    p_note.add_argument('--tags', help='Komma-separierte Tags')
    p_note.set_defaults(func=cmd_note)

    # working
    p_working = subparsers.add_parser(
        'working',
        help='Listet Working Memory auf',
        description=(
            'Listet aktive Working-Memory-Notizen. Die Filter wirken in der '
            'Datenbankabfrage, also vor --limit: --tags store -l 10 liefert die '
            '10 besten Store-Notizen, nicht die Store-Notizen unter den letzten 10. '
            'Konvention: der erste Tag einer Notiz benennt die Pipeline.'
        )
    )
    p_working.add_argument('--limit', '-l', type=int, default=10)
    p_working.add_argument('--tags', metavar='T1[,T2]',
                           help='Nur Notizen mit diesen Tags; Komma = ODER. '
                                'Ein Tag matcht nur als ganzer Listeneintrag '
                                '("rh" trifft nicht "research")')
    p_working.add_argument('--tags-all', action='store_true',
                           help='Aendert --tags von ODER auf UND (alle Tags muessen vorkommen)')
    p_working.add_argument('--agent', dest='filter_agent', metavar='NAME',
                           help='Nur Notizen dieses Agents (Filter, nicht die Schreib-Identitaet)')
    p_working.add_argument('--grep', '-g', metavar='BEGRIFF',
                           help='Teilstring im Inhalt (ASCII-Gross-/Kleinschreibung egal)')
    p_working.add_argument('--json', '-j', action='store_true', help='JSON-Ausgabe')
    p_working.set_defaults(func=cmd_working)

    # clear
    p_clear = subparsers.add_parser('clear', help='Loescht Working Memory')
    p_clear.add_argument('--all', action='store_true', help='Alle Agents (nicht nur eigene)')
    p_clear.set_defaults(func=cmd_clear)

    # lesson
    p_lesson = subparsers.add_parser('lesson', help='Speichert eine Lesson Learned')
    p_lesson.add_argument('title', help='Kurztitel')
    p_lesson.add_argument('problem', help='Problem-Beschreibung')
    p_lesson.add_argument('solution', help='Loesung')
    p_lesson.add_argument('--severity', '-s', choices=['critical', 'high', 'medium', 'low'], default='medium')
    p_lesson.add_argument('--category', '-c', default='general')
    p_lesson.set_defaults(func=cmd_lesson)

    # lessons
    p_lessons = subparsers.add_parser('lessons', help='Listet Lessons auf')
    p_lessons.add_argument('--severity', '-s', choices=['critical', 'high', 'medium', 'low'])
    p_lessons.add_argument('--limit', '-l', type=int, default=10)
    p_lessons.add_argument('--agent', dest='filter_agent', metavar='NAME',
                           help='Nur Lessons dieses Agents (Filter, nicht die Schreib-Identitaet)')
    p_lessons.add_argument('--grep', '-g', metavar='BEGRIFF',
                           help='Teilstring in title, problem oder solution '
                                '(ASCII-Gross-/Kleinschreibung egal)')
    p_lessons.add_argument('--json', '-j', action='store_true', help='JSON-Ausgabe')
    p_lessons.set_defaults(func=cmd_lessons)

    # context
    p_ctx = subparsers.add_parser('context', help='Generiert LLM-Kontext')
    p_ctx.add_argument('--max-items', '-m', type=int, default=5)
    p_ctx.set_defaults(func=cmd_context)

    # session start
    p_start = subparsers.add_parser('start', help='Startet eine Session')
    p_start.add_argument('--task', '-t', help='Task-Beschreibung')
    p_start.set_defaults(func=cmd_session_start)

    # session end
    p_end = subparsers.add_parser('end', help='Beendet eine Session')
    p_end.add_argument('session_id', type=int, help='Session-ID')
    p_end.add_argument('--notes', '-n', help='Handoff-Notes')
    p_end.set_defaults(func=cmd_session_end)

    # changes
    p_changes = subparsers.add_parser('changes', help='Zeigt Aenderungen seit Zeitstempel')
    p_changes.add_argument('since', help='ISO-Zeitstempel (z.B. 2026-02-28T00:00:00)')
    p_changes.add_argument('--json', '-j', action='store_true', help='JSON-Ausgabe')
    p_changes.set_defaults(func=cmd_changes)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unerwarteter Fehler: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
