# -*- coding: utf-8 -*-
"""Repository hygiene checks for local-only sensitive artifacts."""

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestRepositoryHygiene(unittest.TestCase):
    def check_ignored(self, path: str) -> bool:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", path],
            cwd=ROOT,
            check=False,
        )
        return result.returncode == 0

    def test_sensitive_local_files_are_ignored(self):
        for path in [
            ".env.local",
            ".npmrc",
            ".pypirc",
            "credentials.json",
            "secrets.json",
            "token.json",
            "npm_recovery_codes.txt",
            "private.pem",
            "id_rsa.key",
            "client.p12",
            "memory.sqlite",
            "memory.sqlite3",
            "README-Mac Studio.md",
        ]:
            with self.subTest(path=path):
                self.assertTrue(self.check_ignored(path), path)

    def test_public_examples_remain_trackable(self):
        for path in [".env.example", ".env.sample"]:
            with self.subTest(path=path):
                self.assertFalse(self.check_ignored(path), path)


if __name__ == "__main__":
    unittest.main()
