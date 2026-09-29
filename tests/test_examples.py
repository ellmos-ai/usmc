# -*- coding: utf-8 -*-
"""Contract tests ensuring public examples execute cleanly."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from examples.cross_agent_handoff import run_handoff_demo
from examples.benchmark_scaling import run_benchmark


ROOT = Path(__file__).resolve().parents[1]


class TestExamplesContract(unittest.TestCase):
    def test_cross_agent_handoff_example_execution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_db = Path(temp_dir) / "test_handoff.db"
            # Must run without raising any exceptions
            run_handoff_demo(demo_db)
            self.assertTrue(demo_db.exists())
            self.assertGreater(demo_db.stat().st_size, 0)

    def test_benchmark_scaling_example_execution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_db = Path(temp_dir) / "test_bench.db"
            res = run_benchmark(db_path=demo_db, iterations=15, concurrent_ops=5, verbose=False)
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["metrics"]["integrity_check"], "ok")
            self.assertGreater(res["metrics"]["fact_write_ops_per_sec"], 0)
            self.assertGreater(res["metrics"]["concurrent_ops_per_sec"], 0)
            self.assertTrue(demo_db.exists())
            self.assertGreater(demo_db.stat().st_size, 0)

    def test_benchmark_cli_invocation_json(self):
        cmd = [
            sys.executable,
            str(ROOT / "examples" / "benchmark_scaling.py"),
            "--iterations", "10",
            "--concurrent-ops", "5",
            "--json"
        ]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, f"Benchmark CLI failed: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(data["metrics"]["integrity_check"], "ok")
        self.assertEqual(data["iterations"], 10)


if __name__ == "__main__":
    unittest.main()
