# -*- coding: utf-8 -*-
"""
Tests fuer default_db_path() und den vereinheitlichten Default-DB-Pfad
(Client, API, CLI) sowie delete_fact().
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Package-Pfad hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent))

from usmc import USMCClient, __version__
from usmc.client import default_db_path


class TestDefaultDbPath(unittest.TestCase):
    """default_db_path(): per-System lokal, USMC_DB-Override, kein Seiteneffekt."""

    def setUp(self):
        self._saved = os.environ.pop("USMC_DB", None)

    def tearDown(self):
        if self._saved is not None:
            os.environ["USMC_DB"] = self._saved
        else:
            os.environ.pop("USMC_DB", None)

    def test_default_is_home_usmc(self):
        p = Path(default_db_path())
        self.assertEqual(p, Path.home() / ".usmc" / "usmc_memory.db")

    def test_env_override(self):
        os.environ["USMC_DB"] = r"X:\somewhere\custom.db"
        self.assertEqual(default_db_path(), r"X:\somewhere\custom.db")

    def test_no_side_effect_on_call(self):
        """default_db_path() legt selbst nichts an."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sub" / "mem.db"
            os.environ["USMC_DB"] = str(target)
            default_db_path()
            self.assertFalse(target.parent.exists())

    def test_client_uses_default_and_creates_parent(self):
        """USMCClient() ohne db_path nutzt den Default und legt das Verzeichnis an."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sub" / "mem.db"
            os.environ["USMC_DB"] = str(target)
            client = USMCClient(agent_id="pathtest")
            self.assertEqual(Path(client.db_path), target)
            self.assertTrue(target.exists())

    def test_cli_default_matches_client_default(self):
        from usmc.cli import default_db_path as cli_ddp
        self.assertIs(cli_ddp, default_db_path)


class TestDeleteFact(unittest.TestCase):
    """Oeffentliche delete_fact()-Methode."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.client = USMCClient(db_path=self.tmp.name, agent_id="test_agent")

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def test_delete_existing(self):
        self.client.add_fact("project", "framework", "FastAPI")
        self.assertTrue(self.client.delete_fact("framework"))
        self.assertEqual(self.client.get_facts(category="project"), [])

    def test_delete_missing_returns_false(self):
        self.assertFalse(self.client.delete_fact("nope"))

    def test_delete_respects_agent_scope(self):
        other = USMCClient(db_path=self.tmp.name, agent_id="other")
        other.add_fact("project", "shared", "value")
        self.assertFalse(self.client.delete_fact("shared"))
        self.assertTrue(other.delete_fact("shared"))


class TestVersionSingleSource(unittest.TestCase):
    def test_cli_version_uses_package_version(self):
        import usmc.cli as cli
        self.assertEqual(cli.__version__, __version__)


if __name__ == "__main__":
    unittest.main()
