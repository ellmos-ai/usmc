# -*- coding: utf-8 -*-
"""
Tests fuer USMC High-Level API
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from usmc import api
from usmc.client import USMCClient


class TestUSMCApi(unittest.TestCase):
    """Tests fuer die High-Level API."""

    def setUp(self):
        """Initialisiert temp DB fuer jeden Test."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        api.init(db_path=self.db_path, agent_id="test_api")

    def tearDown(self):
        """Loescht temp DB und setzt API zurueck."""
        api._client = None
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_fact_and_facts(self):
        result = api.fact("system", "os", "Windows 11", confidence=0.9)
        self.assertTrue(result['merged'])

        facts = api.facts(category="system")
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]['value'], 'Windows 11')

    def test_note_and_working(self):
        result = api.note("Test-Notiz", priority=1)
        self.assertIn('id', result)

        notes = api.working()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]['content'], 'Test-Notiz')

    def test_scratch_and_loop(self):
        api.scratch("Scratchpad-Inhalt")
        api.loop("Loop-Iteration 1")

        notes = api.working()
        self.assertEqual(len(notes), 2)

    def test_clear(self):
        api.note("Notiz 1")
        api.note("Notiz 2")
        count = api.clear()
        self.assertEqual(count, 2)
        self.assertEqual(len(api.working()), 0)

    def test_lesson_and_lessons(self):
        result = api.lesson(
            title="Test-Bug",
            problem="Problem X",
            solution="Loesung Y",
            severity='high'
        )
        self.assertIn('id', result)

        lessons = api.lessons(severity='high')
        self.assertEqual(len(lessons), 1)

    def test_start_and_end(self):
        session = api.start(task="Testing")
        self.assertIn('id', session)

        success = api.end(session['id'], notes="Done")
        self.assertTrue(success)

    def test_context(self):
        api.fact("system", "os", "Windows 11", confidence=0.9)
        api.note("Aktueller Task")

        ctx = api.context()
        self.assertIn("Aktuelle Notizen", ctx)
        self.assertIn("Sichere Fakten", ctx)

    def test_status(self):
        api.fact("system", "os", "Windows 11")
        status = api.status()
        self.assertEqual(status['facts_count'], 1)
        self.assertEqual(status['agent_id'], 'test_api')

    def test_remember_and_forget(self):
        api.remember("framework", "FastAPI")
        facts = api.facts(category='project')
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]['confidence'], 0.95)

        deleted = api.forget("framework")
        self.assertTrue(deleted)
        facts = api.facts(category='project')
        self.assertEqual(len(facts), 0)

        # Nochmal loeschen sollte False zurueckgeben
        deleted_again = api.forget("framework")
        self.assertFalse(deleted_again)

    def test_set_agent(self):
        api.set_agent("new_agent")
        api.fact("system", "test", "value")

        facts = api.facts()
        self.assertEqual(facts[0]['agent_id'], 'new_agent')

    def test_lazy_init(self):
        """Test dass get_client() ohne init() funktioniert."""
        api._client = None
        # Sollte nicht crashen
        client = api.get_client()
        self.assertIsInstance(client, USMCClient)


if __name__ == '__main__':
    unittest.main()
