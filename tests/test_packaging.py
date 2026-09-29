# -*- coding: utf-8 -*-
"""Packaging, build integrity, and install smoke tests for USMC."""

import subprocess
import sys
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

import usmc

ROOT = Path(__file__).resolve().parents[1]


class TestPackagingContract(unittest.TestCase):
    def setUp(self):
        self.pyproject_path = ROOT / "pyproject.toml"
        self.assertTrue(self.pyproject_path.is_file(), "pyproject.toml must exist")
        if tomllib:
            with open(self.pyproject_path, "rb") as f:
                self.pyproject = tomllib.load(f)
        else:
            self.pyproject = {}

    def test_build_system_declaration(self):
        if not tomllib:
            self.skipTest("tomllib not available")
        build_sys = self.pyproject.get("build-system", {})
        self.assertIn("setuptools>=77", build_sys.get("requires", []))
        self.assertEqual(build_sys.get("build-backend"), "setuptools.build_meta")

    def test_project_metadata_and_version_parity(self):
        if not tomllib:
            self.skipTest("tomllib not available")
        proj = self.pyproject.get("project", {})
        self.assertEqual(proj.get("name"), "usmc")
        self.assertIn("version", proj.get("dynamic", []))
        dynamic_cfg = self.pyproject.get("tool", {}).get("setuptools", {}).get("dynamic", {})
        self.assertEqual(dynamic_cfg.get("version", {}).get("attr"), "usmc.__version__")
        self.assertEqual(usmc.__version__, "0.3.0")

    def test_console_script_entrypoint(self):
        if not tomllib:
            self.skipTest("tomllib not available")
        scripts = self.pyproject.get("project", {}).get("scripts", {})
        self.assertEqual(scripts.get("usmc"), "usmc.cli:main")
        import usmc.cli
        self.assertTrue(callable(usmc.cli.main), "usmc.cli.main must be a callable entrypoint")

    def test_package_files_manifest(self):
        pkg_dir = ROOT / "usmc"
        for expected in [
            "__init__.py",
            "client.py",
            "api.py",
            "cli.py",
            "schema.py",
            "memory_union.contract.json",
        ]:
            file_path = pkg_dir / expected
            self.assertTrue(file_path.is_file(), f"Package file missing: {expected}")
            self.assertGreater(file_path.stat().st_size, 0, f"Package file empty: {expected}")

    def test_pep639_license_and_no_osi_classifier_conflict(self):
        if not tomllib:
            self.skipTest("tomllib not available")
        proj = self.pyproject.get("project", {})
        self.assertEqual(proj.get("license"), "MIT")
        classifiers = proj.get("classifiers", [])
        for c in classifiers:
            self.assertFalse(c.startswith("License :: OSI Approved"), f"PEP 639 conflict: found classifier {c}")

    def test_pip_metadata_dry_run_smoke(self):
        """Smoke check that pip parses pyproject.toml and resolves package metadata."""
        cmd = [sys.executable, "-m", "pip", "install", "--no-deps", ".", "--dry-run"]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(res.returncode, 0, f"pip dry-run failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        self.assertIn("usmc-0.3.0", res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
