# -*- coding: utf-8 -*-
"""Contract tests ensuring public examples execute cleanly."""

from pathlib import Path
import tempfile
import unittest

from examples.cross_agent_handoff import run_handoff_demo


class TestExamplesContract(unittest.TestCase):
    def test_cross_agent_handoff_example_execution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_db = Path(temp_dir) / "test_handoff.db"
            # Must run without raising any exceptions
            run_handoff_demo(demo_db)
            self.assertTrue(demo_db.exists())
            self.assertGreater(demo_db.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
