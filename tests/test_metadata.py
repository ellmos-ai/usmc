# -*- coding: utf-8 -*-
"""Metadata and documentation parity contract tests."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestMetadataContract(unittest.TestCase):
    def test_readmes_exist(self):
        for name in ["README.md", "README_de.md", "README_es.md"]:
            path = ROOT / name
            self.assertTrue(path.exists(), f"{name} must exist")
            self.assertGreater(path.stat().st_size, 1000, f"{name} must not be empty")

    def test_language_switchers_linked(self):
        en_text = (ROOT / "README.md").read_text(encoding="utf-8")
        de_text = (ROOT / "README_de.md").read_text(encoding="utf-8")
        es_text = (ROOT / "README_es.md").read_text(encoding="utf-8")

        for text, filename in [(en_text, "README.md"), (de_text, "README_de.md"), (es_text, "README_es.md")]:
            with self.subTest(filename=filename):
                self.assertIn("[English](README.md)", text)
                self.assertIn("[Deutsch](README_de.md)", text)
                self.assertIn("[Español](README_es.md)", text)

    def test_test_badges_synchronized(self):
        en_text = (ROOT / "README.md").read_text(encoding="utf-8")
        de_text = (ROOT / "README_de.md").read_text(encoding="utf-8")
        es_text = (ROOT / "README_es.md").read_text(encoding="utf-8")

        self.assertIn("Tests-102%20passed", en_text)
        self.assertIn("Tests-102%20bestanden", de_text)
        self.assertIn("Tests-102%20aprobados", es_text)

    def test_mermaid_sequence_diagram_present(self):
        for name in ["README.md", "README_de.md", "README_es.md"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("```mermaid", text)
                self.assertIn("sequenceDiagram", text)
                self.assertIn("autonumber", text)
                self.assertIn("start_session", text)

    def test_llms_txt_updated(self):
        path = ROOT / "llms.txt"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("Last-checked: 2026-09-10", text)
        self.assertIn("README_es.md", text)


if __name__ == "__main__":
    unittest.main()
