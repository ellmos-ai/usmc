# -*- coding: utf-8 -*-
"""Packaging metadata, public documentation navigation, and workflow checks."""

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

import usmc

ROOT = Path(__file__).resolve().parents[1]
ENTRY_GUIDES = {
    "README.md": "docs/archive/README.full.en.md",
    "README_de.md": "docs/archive/README.full.de.md",
    "README_es.md": "docs/archive/README.full.es.md",
}


def _markdown_ids_and_headings(text):
    ids = set(re.findall(r'<a id="([^"]+)"', text))
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        label = re.sub(r"<[^>]+>|`", "", heading).lower().strip()
        label = re.sub(r"[^\w\- ]", "", label, flags=re.UNICODE).replace(" ", "-")
        ids.add(label)
    return ids


class TestMetadataContract(unittest.TestCase):
    def test_readmes_and_archived_guides_exist(self):
        for entry, archive in ENTRY_GUIDES.items():
            for name in (entry, archive):
                path = ROOT / name
                with self.subTest(name=name):
                    self.assertTrue(path.is_file())
                    self.assertGreater(path.stat().st_size, 1000)

    def test_language_switchers_linked(self):
        expected = ["[English](README.md)", "[Deutsch](README_de.md)", "[Español](README_es.md)"]
        for name in ENTRY_GUIDES:
            text = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                for link in expected:
                    self.assertIn(link, text)

    def test_readme_internal_links_and_fragments_resolve(self):
        documents = list(ENTRY_GUIDES) + list(ENTRY_GUIDES.values())
        issues = []
        for name in documents:
            path = ROOT / name
            text = path.read_text(encoding="utf-8")
            for destination in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
                target_text = destination.strip().split()[0].strip("<>")
                if target_text.startswith(("https://", "http://", "mailto:", "data:")):
                    continue
                target_path, _, fragment = target_text.partition("#")
                target = (path.parent / unquote(target_path)).resolve() if target_path else path.resolve()
                try:
                    target.relative_to(ROOT.resolve())
                except ValueError:
                    issues.append((name, destination, "path escapes repository"))
                    continue
                if not target.exists():
                    issues.append((name, destination, "target missing"))
                    continue
                if fragment and target.is_file() and target.suffix.lower() in {".md", ".txt"}:
                    target_ids = _markdown_ids_and_headings(target.read_text(encoding="utf-8"))
                    if unquote(fragment) not in target_ids:
                        issues.append((name, destination, "fragment missing"))
        self.assertEqual(issues, [])

    def test_legacy_section_links_reach_archived_guides(self):
        for entry_name, archive_name in ENTRY_GUIDES.items():
            entry = (ROOT / entry_name).read_text(encoding="utf-8")
            archive = (ROOT / archive_name).read_text(encoding="utf-8")
            entry_ids = set(re.findall(r'<a id="([^"]+)"', entry))
            archive_ids = set(re.findall(r'<a id="([^"]+)"', archive))
            for number in range(1, 19):
                anchor = f"sec-{number:02d}"
                with self.subTest(entry=entry_name, anchor=anchor):
                    self.assertIn(anchor, entry_ids)
                    self.assertIn(anchor, archive_ids)
                    self.assertIn(f"{Path(archive_name).name}#{anchor}", entry)
            self.assertEqual(len(entry_ids), len(re.findall(r'<a id="([^"]+)"', entry)))

    def test_machine_readable_guide_has_current_source_references(self):
        text = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("https://github.com/ellmos-ai/usmc", text)
        self.assertIn("README_de.md", text)
        self.assertIn("README_es.md", text)
        self.assertIn("SECURITY.md", text)
        self.assertIn("THIRD_PARTY_LICENSES.md", text)
        self.assertIn("0.3.0", text)

    def test_governance_files_exist(self):
        for name in [
            "NOTICE", "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.txt",
            "MARKETING-LOG.txt", "SECURITY.md", "CHANGELOG.md", "LICENSE", ".gitignore",
        ]:
            path = ROOT / name
            with self.subTest(name=name):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 50)

    def test_ci_workflow_hardening(self):
        workflows = ROOT / ".github" / "workflows"
        self.assertTrue(workflows.is_dir())
        for name in ["stale.yml", "welcome.yml", "auto-assign.yml", "label-sync.yml", "ci.yml"]:
            with self.subTest(name=name):
                self.assertTrue((workflows / name).is_file())
        stale = (workflows / "stale.yml").read_text(encoding="utf-8")
        self.assertIn("actions/stale@v9", stale)
        self.assertIn("timeout-minutes: 10", stale)
        welcome = (workflows / "welcome.yml").read_text(encoding="utf-8")
        self.assertIn("actions/first-interaction@v3", welcome)
        ci = (workflows / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("ruff check .", ci)
        for text in [stale, welcome, ci]:
            self.assertIn("concurrency:", text)
            self.assertIn("cancel-in-progress: true", text)

    def test_security_policy_has_bilingual_private_reporting_routes(self):
        text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("## Deutsch", text)
        self.assertIn("## English", text)
        self.assertIn("https://github.com/ellmos-ai/usmc/security/advisories/new", text)
        self.assertIn("security@ellmos.ai", text)

    def test_project_version_and_changelog_release_history(self):
        self.assertEqual(usmc.__version__, "0.3.0")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## 0.3.0 - 2026-09-26", changelog)
        self.assertIn("## 0.2.3 - 2026-09-19", changelog)

    def test_package_metadata_scope(self):
        try:
            import tomllib
        except ModuleNotFoundError:
            try:
                import tomli as tomllib
            except ModuleNotFoundError as exc:
                self.fail(f"tomli is required to inspect project metadata on this Python: {exc}")
        with (ROOT / "pyproject.toml").open("rb") as stream:
            metadata = tomllib.load(stream)
        project = metadata["project"]
        self.assertEqual(project["license"], "MIT")
        self.assertEqual(project["requires-python"], ">=3.10")
        self.assertEqual(project.get("dependencies", []), [])
        self.assertEqual(project["scripts"]["usmc"], "usmc.cli:main")
        self.assertEqual(metadata["build-system"]["build-backend"], "setuptools.build_meta")
        self.assertIn("setuptools>=77", metadata["build-system"]["requires"])
        self.assertIn("pytest>=7.0", project["optional-dependencies"]["test"])
        self.assertIn("ruff>=0.1.0", project["optional-dependencies"]["test"])
        self.assertIn("tomli>=2.0; python_version < '3.11'", project["optional-dependencies"]["test"])
        self.assertEqual(set(project["license-files"]), {"LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.txt"})

    def test_notice_and_license_attribution(self):
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("usmc (United Shared Memory Client)", notice)
        self.assertIn("Copyright (c) 2026 Lukas Geiger", notice)
        self.assertIn("MIT License", license_text)

    def test_optional_bach_schema_contract_is_present(self):
        contract = ROOT / "usmc" / "memory_union.contract.json"
        self.assertTrue(contract.is_file())
        for name in ENTRY_GUIDES:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("https://github.com/ellmos-ai/bach", text)
            self.assertIn("memory_union.contract.json", text)

    def test_pep621_contributing_url(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('Contributing = "https://github.com/ellmos-ai/usmc/blob/main/CONTRIBUTING.md"', pyproject)
        self.assertIn(".pytest_tmp*", pyproject)
        self.assertIn(".nyc_output", pyproject)

    def test_dependabot_configuration(self):
        dep_path = ROOT / ".github" / "dependabot.yml"
        self.assertTrue(dep_path.is_file(), "Missing .github/dependabot.yml")
        text = dep_path.read_text(encoding="utf-8")
        self.assertIn("version: 2", text)
        self.assertIn('package-ecosystem: "pip"', text)
        self.assertIn("open-pull-requests-limit: 0", text)
        self.assertIn("security-updates", text)
        self.assertIn('package-ecosystem: "github-actions"', text)
        self.assertIn("open-pull-requests-limit: 3", text)
        self.assertIn('timezone: "Europe/Berlin"', text)

    def test_ci_whitespace_gate_and_tri_platform(self):
        ci_path = ROOT / ".github" / "workflows" / "ci.yml"
        self.assertTrue(ci_path.is_file(), "Missing .github/workflows/ci.yml")
        text = ci_path.read_text(encoding="utf-8")
        self.assertIn("git diff --check", text, "Missing git diff --check quality gate")
        self.assertIn("ubuntu-latest", text)
        self.assertIn("windows-latest", text)
        self.assertIn("macos-latest", text)

    def test_pep621_metadata_freeze_and_security_urls(self):
        self.assertEqual(usmc.__version__, "0.3.0", "Version bump forbidden in Pfad A/B runs (T-20260920-167562623)")
        pyproject_path = ROOT / "pyproject.toml"
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        project = data.get("project", {})
        urls = project.get("urls", {})
        self.assertIn("Security", urls)
        self.assertIn("Contributing", urls)
        classifiers = project.get("classifiers", [])
        for c in classifiers:
            self.assertFalse(c.startswith("License ::"), f"OSI classifier found in violation of PEP 639: {c}")

    def test_gitignore_hardened_multi_host_and_taskplan(self):
        gi_path = ROOT / ".gitignore"
        text = gi_path.read_text(encoding="utf-8")
        self.assertIn("thumbs.db", text)
        self.assertIn("*-TASKPLAN*", text)
        self.assertIn("TASKPLAN*", text)
        self.assertIn("*-ASUS-GEI.*", text)
        self.assertIn("*-WORKSTATION-LG.*", text)


if __name__ == "__main__":
    unittest.main()
