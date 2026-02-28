# -*- coding: utf-8 -*-
"""
Tests fuer USMCClient
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Package-Pfad hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent))

from usmc import USMCClient


class TestUSMCClient(unittest.TestCase):
    """Grundlegende Tests fuer den USMC Client."""

    def setUp(self):
        """Erstellt temp DB fuer jeden Test."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        self.client = USMCClient(db_path=self.db_path, agent_id="test_agent")

    def tearDown(self):
        """Loescht temp DB."""
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    # ── Facts ──────────────────────────────────────────────────

    def test_add_and_get_fact(self):
        result = self.client.add_fact("system", "os", "Windows 11", confidence=0.9)
        self.assertTrue(result['merged'])
        self.assertEqual(result['key'], 'os')

        facts = self.client.get_facts(category="system")
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]['value'], 'Windows 11')
        self.assertEqual(facts[0]['confidence'], 0.9)

    def test_confidence_merge_rejects_lower(self):
        self.client.add_fact("system", "os", "Windows 11", confidence=0.9)
        result = self.client.add_fact("system", "os", "Linux", confidence=0.5)
        self.assertFalse(result['merged'])

        facts = self.client.get_facts(category="system")
        self.assertEqual(facts[0]['value'], 'Windows 11')

    def test_confidence_merge_accepts_higher(self):
        self.client.add_fact("system", "os", "Windows 10", confidence=0.5)
        result = self.client.add_fact("system", "os", "Windows 11", confidence=0.9)
        self.assertTrue(result['merged'])

        facts = self.client.get_facts(category="system")
        self.assertEqual(facts[0]['value'], 'Windows 11')

    def test_confidence_merge_accepts_equal(self):
        self.client.add_fact("system", "os", "Windows 10", confidence=0.8)
        result = self.client.add_fact("system", "os", "Windows 11", confidence=0.8)
        self.assertTrue(result['merged'])

    def test_invalid_category(self):
        with self.assertRaises(ValueError):
            self.client.add_fact("invalid", "key", "value")

    def test_invalid_confidence(self):
        with self.assertRaises(ValueError):
            self.client.add_fact("system", "key", "value", confidence=1.5)

    def test_get_facts_min_confidence(self):
        self.client.add_fact("system", "a", "low", confidence=0.3)
        self.client.add_fact("system", "b", "high", confidence=0.9)

        facts = self.client.get_facts(min_confidence=0.5)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]['key'], 'b')

    # ── Working Memory ─────────────────────────────────────────

    def test_add_and_get_working(self):
        result = self.client.add_working("Test-Notiz", type='note', priority=1)
        self.assertIn('id', result)
        self.assertEqual(result['content'], 'Test-Notiz')

        notes = self.client.get_working()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]['content'], 'Test-Notiz')

    def test_clear_working(self):
        self.client.add_working("Notiz 1")
        self.client.add_working("Notiz 2")
        count = self.client.clear_working()
        self.assertEqual(count, 2)

        notes = self.client.get_working()
        self.assertEqual(len(notes), 0)

    def test_clear_working_agent_only(self):
        self.client.add_working("Agent A Notiz")

        other = USMCClient(db_path=self.db_path, agent_id="other_agent")
        other.add_working("Agent B Notiz")

        count = self.client.clear_working(agent_only=True)
        self.assertEqual(count, 1)

        notes_b = other.get_working(agent_id="other_agent")
        self.assertEqual(len(notes_b), 1)

    def test_invalid_working_type(self):
        with self.assertRaises(ValueError):
            self.client.add_working("test", type='invalid')

    # ── Lessons ────────────────────────────────────────────────

    def test_add_and_get_lesson(self):
        result = self.client.add_lesson(
            title="Encoding-Bug",
            problem="cp1252 statt UTF-8",
            solution="PYTHONIOENCODING=utf-8 setzen",
            severity='high',
            category='bug'
        )
        self.assertIn('id', result)

        lessons = self.client.get_lessons()
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['title'], 'Encoding-Bug')

    def test_invalid_severity(self):
        with self.assertRaises(ValueError):
            self.client.add_lesson("t", "p", "s", severity='invalid')

    def test_lessons_severity_filter(self):
        self.client.add_lesson("A", "p", "s", severity='low')
        self.client.add_lesson("B", "p", "s", severity='critical')

        critical = self.client.get_lessons(severity='critical')
        self.assertEqual(len(critical), 1)
        self.assertEqual(critical[0]['title'], 'B')

    # ── Sessions ───────────────────────────────────────────────

    def test_start_and_end_session(self):
        session = self.client.start_session(task="Testing")
        self.assertIn('id', session)
        self.assertEqual(session['agent_id'], 'test_agent')

        success = self.client.end_session(session['id'], handoff_notes="Done")
        self.assertTrue(success)

    # ── Context ────────────────────────────────────────────────

    def test_generate_context_empty(self):
        ctx = self.client.generate_context()
        self.assertEqual(ctx, "Kein Kontext verfuegbar.")

    def test_generate_context_with_data(self):
        self.client.add_fact("system", "os", "Windows 11", confidence=0.9)
        self.client.add_working("Aktueller Task")
        self.client.add_lesson("Bug", "Problem", "Loesung", severity='high')

        ctx = self.client.generate_context()
        self.assertIn("Aktuelle Notizen", ctx)
        self.assertIn("Sichere Fakten", ctx)
        self.assertIn("Wichtige Lessons", ctx)

    # ── Sync ───────────────────────────────────────────────────

    def test_get_changes_since(self):
        self.client.add_fact("system", "os", "Windows 11")
        self.client.add_working("Notiz")
        self.client.add_lesson("L", "P", "S")

        changes = self.client.get_changes_since("2000-01-01T00:00:00")
        self.assertEqual(len(changes['facts']), 1)
        self.assertEqual(len(changes['working']), 1)
        self.assertEqual(len(changes['lessons']), 1)
        self.assertIn('sync_timestamp', changes)

    def test_get_changes_since_future(self):
        self.client.add_fact("system", "os", "Windows 11")
        changes = self.client.get_changes_since("2099-01-01T00:00:00")
        self.assertEqual(len(changes['facts']), 0)

    # ── Multi-Agent ────────────────────────────────────────────

    def test_multi_agent_facts(self):
        agent_a = USMCClient(db_path=self.db_path, agent_id="opus")
        agent_b = USMCClient(db_path=self.db_path, agent_id="sonnet")

        agent_a.add_fact("project", "lang", "Python")
        agent_b.add_fact("project", "lang", "TypeScript")

        all_facts = agent_a.get_facts(category="project")
        self.assertEqual(len(all_facts), 2)

        opus_facts = agent_a.get_facts(category="project", agent_id="opus")
        self.assertEqual(len(opus_facts), 1)
        self.assertEqual(opus_facts[0]['value'], 'Python')

    # ── Status ─────────────────────────────────────────────────

    def test_get_status(self):
        self.client.add_fact("system", "os", "Windows 11", confidence=0.9)
        self.client.add_working("Notiz")
        self.client.add_lesson("L", "P", "S")
        self.client.start_session()

        status = self.client.get_status()
        self.assertEqual(status['facts_count'], 1)
        self.assertEqual(status['working_count'], 1)
        self.assertEqual(status['lessons_count'], 1)
        self.assertEqual(status['sessions_count'], 1)
        self.assertEqual(status['confident_facts'], 1)
        self.assertEqual(status['agent_id'], 'test_agent')

    # ── DB Creation ────────────────────────────────────────────

    def test_creates_db_if_not_exists(self):
        new_path = self.db_path + "_new.db"
        try:
            client = USMCClient(db_path=new_path, agent_id="test")
            status = client.get_status()
            self.assertEqual(status['facts_count'], 0)
        finally:
            try:
                os.unlink(new_path)
            except OSError:
                pass


if __name__ == '__main__':
    unittest.main()
