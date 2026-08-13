# -*- coding: utf-8 -*-
"""
Tests fuer USMC CLI
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from usmc import USMCClient
from usmc.cli import main


class TestUSMCCli(unittest.TestCase):
    """Tests fuer das CLI."""

    def setUp(self):
        """Erstellt temp DB fuer jeden Test."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name

    def tearDown(self):
        """Loescht temp DB."""
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def run_cli(self, args: list) -> tuple:
        """Fuehrt CLI aus und gibt (return_code, stdout, stderr) zurueck."""
        full_args = ['--db', self.db_path, '--agent', 'test'] + args
        stdout = StringIO()
        stderr = StringIO()
        with patch('sys.stdout', stdout), patch('sys.stderr', stderr):
            try:
                code = main(full_args)
            except SystemExit as e:
                code = e.code if e.code is not None else 0
        return code, stdout.getvalue(), stderr.getvalue()

    def test_status_empty(self):
        code, out, err = self.run_cli(['status'])
        self.assertEqual(code, 0)
        self.assertIn('USMC Memory Status', out)
        self.assertIn('Facts:           0', out)

    def test_fact_and_facts(self):
        code, out, err = self.run_cli(['fact', 'system', 'os', 'Windows 11'])
        self.assertEqual(code, 0)
        self.assertIn('[OK]', out)

        code, out, err = self.run_cli(['facts'])
        self.assertEqual(code, 0)
        self.assertIn('system', out)
        self.assertIn('os', out)
        self.assertIn('Windows 11', out)

    def test_fact_with_confidence(self):
        code, out, err = self.run_cli(['fact', 'system', 'os', 'Windows 11', '-c', '0.8'])
        self.assertEqual(code, 0)

        code, out, err = self.run_cli(['facts', '--json'])
        self.assertEqual(code, 0)
        self.assertIn('"confidence": 0.8', out)

    def test_facts_filter(self):
        self.run_cli(['fact', 'system', 'os', 'Windows'])
        self.run_cli(['fact', 'project', 'name', 'USMC'])

        code, out, err = self.run_cli(['facts', '--category', 'system'])
        self.assertEqual(code, 0)
        self.assertIn('os', out)
        self.assertNotIn('USMC', out)

    def test_note_and_working(self):
        code, out, err = self.run_cli(['note', 'Test-Notiz'])
        self.assertEqual(code, 0)
        self.assertIn('[OK]', out)

        code, out, err = self.run_cli(['working'])
        self.assertEqual(code, 0)
        self.assertIn('Test-Notiz', out)

    def test_note_with_options(self):
        code, out, err = self.run_cli(['note', 'High-Prio', '-p', '5', '-t', 'context', '--tags', 'important'])
        self.assertEqual(code, 0)

        code, out, err = self.run_cli(['working', '--json'])
        self.assertIn('"priority": 5', out)
        self.assertIn('"type": "context"', out)

    def test_clear(self):
        self.run_cli(['note', 'Notiz 1'])
        self.run_cli(['note', 'Notiz 2'])

        code, out, err = self.run_cli(['clear'])
        self.assertEqual(code, 0)
        self.assertIn('2 Eintraege deaktiviert', out)

        code, out, err = self.run_cli(['working'])
        self.assertIn('Keine aktiven Notizen', out)

    def test_lesson_and_lessons(self):
        code, out, err = self.run_cli(['lesson', 'Bug', 'Problem', 'Solution', '-s', 'high'])
        self.assertEqual(code, 0)
        self.assertIn('[OK]', out)

        code, out, err = self.run_cli(['lessons'])
        self.assertEqual(code, 0)
        self.assertIn('Bug', out)
        self.assertIn('!!', out)  # high severity marker

    def test_lessons_filter(self):
        self.run_cli(['lesson', 'Critical', 'P', 'S', '-s', 'critical'])
        self.run_cli(['lesson', 'Low', 'P', 'S', '-s', 'low'])

        code, out, err = self.run_cli(['lessons', '-s', 'critical'])
        self.assertIn('Critical', out)
        self.assertNotIn('Low', out)

    def test_context_empty(self):
        code, out, err = self.run_cli(['context'])
        self.assertEqual(code, 0)
        self.assertIn('Kein Kontext', out)

    def test_context_with_data(self):
        self.run_cli(['fact', 'system', 'os', 'Windows 11'])
        self.run_cli(['note', 'Aktueller Task'])

        code, out, err = self.run_cli(['context'])
        self.assertEqual(code, 0)
        self.assertIn('Aktuelle Notizen', out)
        self.assertIn('Sichere Fakten', out)

    def test_session_start_and_end(self):
        code, out, err = self.run_cli(['start', '-t', 'Testing'])
        self.assertEqual(code, 0)
        self.assertIn('Session gestartet', out)
        self.assertIn('ID: 1', out)

        code, out, err = self.run_cli(['end', '1', '-n', 'Done'])
        self.assertEqual(code, 0)
        self.assertIn('beendet', out)

    def test_end_nonexistent_session(self):
        code, out, err = self.run_cli(['end', '999'])
        self.assertEqual(code, 1)
        self.assertIn('nicht gefunden', out)

    def test_changes(self):
        self.run_cli(['fact', 'system', 'os', 'Windows 11'])

        code, out, err = self.run_cli(['changes', '2000-01-01T00:00:00'])
        self.assertEqual(code, 0)
        self.assertIn('Facts:   1', out)

    def test_changes_json(self):
        self.run_cli(['fact', 'system', 'os', 'Windows 11'])

        code, out, err = self.run_cli(['changes', '2000-01-01T00:00:00', '--json'])
        self.assertEqual(code, 0)
        self.assertIn('"facts":', out)
        self.assertIn('"sync_timestamp":', out)

    def test_invalid_category(self):
        code, out, err = self.run_cli(['fact', 'invalid', 'key', 'value'])
        # argparse sollte das abfangen
        self.assertNotEqual(code, 0)

    def test_no_command(self):
        code, out, err = self.run_cli([])
        self.assertEqual(code, 1)

    # ── Suchfilter ─────────────────────────────────────────────

    def test_working_tags_filter(self):
        self.run_cli(['note', 'Store-Welle 3', '--tags', 'store,welle'])
        self.run_cli(['note', 'RH-Beweis', '--tags', 'rh'])

        code, out, err = self.run_cli(['working', '--tags', 'store'])
        self.assertEqual(code, 0)
        self.assertIn('Store-Welle 3', out)
        self.assertNotIn('RH-Beweis', out)

    def test_working_tags_or_and_all(self):
        self.run_cli(['note', 'Beide', '--tags', 'store,welle'])
        self.run_cli(['note', 'Nur store', '--tags', 'store'])

        code, out, err = self.run_cli(['working', '--tags', 'store,welle'])
        self.assertIn('Beide', out)
        self.assertIn('Nur store', out)

        code, out, err = self.run_cli(['working', '--tags', 'store,welle', '--tags-all'])
        self.assertIn('Beide', out)
        self.assertNotIn('Nur store', out)

    def test_working_grep_filter(self):
        self.run_cli(['note', 'Partner Center Submission'])
        self.run_cli(['note', 'Etwas anderes'])

        code, out, err = self.run_cli(['working', '--grep', 'partner'])
        self.assertEqual(code, 0)
        self.assertIn('Partner Center', out)
        self.assertNotIn('Etwas anderes', out)

    def test_working_agent_filter(self):
        self.run_cli(['note', 'Von test'])
        stdout = StringIO()
        with patch('sys.stdout', stdout):
            main(['--db', self.db_path, '--agent', 'codex', 'note', 'Von codex'])

        code, out, err = self.run_cli(['working', '--agent', 'codex'])
        self.assertEqual(code, 0)
        self.assertIn('Von codex', out)
        self.assertNotIn('Von test', out)

    def test_subcommand_agent_does_not_clobber_write_identity(self):
        """--agent am Subcommand filtert; die globale Schreib-Identitaet bleibt."""
        seen = []
        real_cls = USMCClient

        def spy(db_path=None, agent_id=None):
            seen.append(agent_id)
            return real_cls(db_path=db_path, agent_id=agent_id)

        stdout = StringIO()
        with patch('usmc.cli.USMCClient', side_effect=spy), patch('sys.stdout', stdout):
            code = main(['--db', self.db_path, '--agent', 'writer',
                         'working', '--agent', 'other'])

        self.assertEqual(code, 0)
        self.assertEqual(seen, ['writer'])

    def test_working_empty_result_names_active_filters(self):
        self.run_cli(['note', 'Irgendwas'])
        code, out, err = self.run_cli(['working', '--tags', 'gibtsnicht'])
        self.assertEqual(code, 0)
        self.assertIn('Keine aktiven Notizen.', out)
        self.assertIn('gibtsnicht', out)

    def test_working_filter_with_json(self):
        self.run_cli(['note', 'Store A', '--tags', 'store'])
        self.run_cli(['note', 'RH B', '--tags', 'rh'])

        code, out, err = self.run_cli(['working', '--tags', 'store', '--json'])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['content'], 'Store A')

    def test_facts_grep_and_agent_filter(self):
        self.run_cli(['fact', 'system', 'store_pfad', 'C:/apps'])
        self.run_cli(['fact', 'system', 'os', 'Windows 11'])

        code, out, err = self.run_cli(['facts', '--grep', 'store'])
        self.assertEqual(code, 0)
        self.assertIn('store_pfad', out)
        self.assertNotIn('Windows 11', out)

        code, out, err = self.run_cli(['facts', '--agent', 'niemand'])
        self.assertEqual(code, 0)
        self.assertIn('Keine Fakten gefunden.', out)

    def test_lessons_grep_and_agent_filter(self):
        self.run_cli(['lesson', 'Encoding', 'cp1252 kaputt', 'PYTHONIOENCODING setzen'])
        self.run_cli(['lesson', 'Anderes', 'p', 's'])

        code, out, err = self.run_cli(['lessons', '--grep', 'cp1252'])
        self.assertEqual(code, 0)
        self.assertIn('Encoding', out)
        self.assertNotIn('Anderes', out)

        code, out, err = self.run_cli(['lessons', '--agent', 'niemand'])
        self.assertEqual(code, 0)
        self.assertIn('Keine Lessons gefunden.', out)

    def test_empty_filter_result_is_valid_json_with_json_flag(self):
        """Mit Filtern ist 'leer' der Normalfall -- --json muss parsebar bleiben."""
        self.run_cli(['note', 'Irgendwas', '--tags', 'store'])
        self.run_cli(['fact', 'system', 'os', 'Windows 11'])
        self.run_cli(['lesson', 'Titel', 'p', 's'])

        for args in (['working', '--tags', 'gibtsnicht', '--json'],
                     ['facts', '--grep', 'gibtsnicht', '--json'],
                     ['lessons', '--grep', 'gibtsnicht', '--json']):
            with self.subTest(command=args[0]):
                code, out, err = self.run_cli(args)
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(out), [])

    def test_filters_are_optional(self):
        """Ohne Filter bleibt das Verhalten unveraendert (Rueckwaertskompatibilitaet)."""
        self.run_cli(['note', 'A', '--tags', 'store'])
        self.run_cli(['note', 'B'])

        code, out, err = self.run_cli(['working'])
        self.assertEqual(code, 0)
        self.assertIn('A', out)
        self.assertIn('B', out)


if __name__ == '__main__':
    unittest.main()
