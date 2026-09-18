# -*- coding: utf-8 -*-
"""Metadata and documentation parity contract tests."""

import unittest
from pathlib import Path

import usmc

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

        self.assertIn("Tests-108%20passed", en_text)
        self.assertIn("Tests-108%20bestanden", de_text)
        self.assertIn("Tests-108%20aprobados", es_text)

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
        self.assertIn("Last-checked: 2026-09-18", text)
        self.assertIn("0.2.2", text)
        self.assertIn("README_es.md", text)
        self.assertIn("THIRD_PARTY_LICENSES.md", text)
        self.assertIn("SECURITY.md", text)
        self.assertIn("MARKETING-LOG.txt", text)

    def test_hygiene_and_governance_files_exist(self):
        for name in [
            "THIRD_PARTY_LICENSES.md",
            "MARKETING-LOG.txt",
            "SECURITY.md",
            "CHANGELOG.md",
            "LICENSE",
            ".gitignore",
        ]:
            path = ROOT / name
            with self.subTest(name=name):
                self.assertTrue(path.exists(), f"{name} must exist")
                self.assertGreater(path.stat().st_size, 50, f"{name} must not be empty")

    def test_ci_workflow_hardening(self):
        workflows = ROOT / ".github" / "workflows"
        self.assertTrue(workflows.exists())

        stale = (workflows / "stale.yml").read_text(encoding="utf-8")
        self.assertIn("actions/stale@v9", stale)
        self.assertIn("timeout-minutes: 10", stale)
        self.assertIn("concurrency:", stale)
        self.assertIn("cancel-in-progress: true", stale)

        welcome = (workflows / "welcome.yml").read_text(encoding="utf-8")
        self.assertIn("actions/first-interaction@v3", welcome)
        self.assertIn("timeout-minutes: 5", welcome)
        self.assertIn("concurrency:", welcome)
        self.assertIn("cancel-in-progress: true", welcome)

        ci = (workflows / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("timeout-minutes: 15", ci)
        self.assertIn("concurrency:", ci)
        self.assertIn("cancel-in-progress: true", ci)
        self.assertIn("ruff check .", ci)

    def test_security_policy_bilingual_and_sla(self):
        sec = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("## Deutsch", sec)
        self.assertIn("## English", sec)
        self.assertIn("48 Stunden", sec)
        self.assertIn("48 hours", sec)
        self.assertIn("5 Werktagen", sec)
        self.assertIn("5 business days", sec)
        self.assertIn("https://github.com/ellmos-ai/usmc/security/advisories/new", sec)
        self.assertIn("security@ellmos.ai", sec)

    def test_third_party_licenses_invariants(self):
        tpl = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        self.assertIn("Zero-Copyleft Guarantee", tpl)
        self.assertIn("RunAsInvoker", tpl)
        self.assertIn("dependencies = []", tpl)
        for i in range(1, 11):
            inv = f"INV-{'' if i == 10 else ''}{'LOCAL' if i == 1 else 'UNPRIV' if i == 2 else 'SQLITE' if i == 3 else 'SCHEMA' if i == 4 else 'BOUND' if i == 5 else 'FILTER' if i == 6 else 'LANG' if i == 7 else 'ISOL' if i == 8 else 'AUDIT' if i == 9 else 'SLA'}-{i:02d}"
            self.assertIn(inv, tpl)

    def test_version_consistency(self):
        self.assertEqual(usmc.__version__, "0.2.2")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## 0.2.2 - 2026-09-18", changelog)
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("Source version is `0.2.2`", llms)

    def test_pyproject_toml_guardrails(self):
        pyproj = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('license-files = ["LICENSE", "THIRD_PARTY_LICENSES.md"]', pyproj)
        self.assertIn('minversion = "7.0"', pyproj)
        self.assertIn("norecursedirs =", pyproj)
        self.assertIn("[tool.ruff]", pyproj)


if __name__ == "__main__":
    unittest.main()
