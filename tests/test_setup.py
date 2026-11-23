# -*- coding: utf-8 -*-
"""Tests for `usmc setup` non-destructive import and agent memory redirection."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from usmc import USMCClient
from usmc.cli import main
from usmc.setup import _INDEX_START, _SETUP_START, run_setup


class TestUSMCSetup(unittest.TestCase):
    def _build_fake_home(self, root: Path) -> dict[str, Path]:
        home = root / "fakehome"
        home.mkdir()
        home_slug = home.resolve()
        import re

        slug = re.sub(r"[^A-Za-z0-9]", "-", str(home_slug))

        # 1. Claude Home silo + non-private silo + marked private silos
        home_mem = home / ".claude" / "projects" / slug / "memory"
        home_mem.mkdir(parents=True)
        (home_mem / "MEMORY.md").write_text("# Memory Index\n- [prefs](prefs.md)\n", encoding="utf-8")
        (home_mem / "prefs.md").write_text(
            "---\nname: User Prefs\ntype: user\n---\nAlways run unit tests before commit.\n",
            encoding="utf-8",
        )
        (home_mem / "feedback.md").write_text(
            "---\nname: Feedback Rule\ntype: feedback\n---\nNever skip lock checks.\n",
            encoding="utf-8",
        )

        pub_mem = home / ".claude" / "projects" / "work-public-repo" / "memory"
        pub_mem.mkdir(parents=True)
        (pub_mem / "project_note.md").write_text(
            "---\nname: Public Repo Note\ntype: project\n---\nCI matrix covers Python 3.10 and 3.12.\n",
            encoding="utf-8",
        )

        priv_marker = home / ".claude" / "projects" / "client-silo" / "memory"
        priv_marker.mkdir(parents=True)
        (priv_marker / ".usmc-private").write_text("private\n", encoding="utf-8")
        (priv_marker / "secret_notes.md").write_text("Private client details must never enter USMC.\n", encoding="utf-8")

        priv_fm = home / ".claude" / "projects" / "other-silo" / "memory"
        priv_fm.mkdir(parents=True)
        (priv_fm / "notes.md").write_text(
            "---\nname: Hidden\nprivacy: private\n---\nDo not import this private silo.\n",
            encoding="utf-8",
        )

        priv_name = home / ".claude" / "projects" / "my-private-notes" / "memory"
        priv_name.mkdir(parents=True)
        (priv_name / "diary.md").write_text("Named private silo should be skipped.\n", encoding="utf-8")

        claude_settings = home / ".claude" / "settings.json"
        claude_settings.write_text(json.dumps({"autoMemoryEnabled": True}), encoding="utf-8")
        claude_rule = home / ".claude" / "CLAUDE.md"
        claude_rule.write_text("# Global Claude Rules\nExisting rule stays.\n", encoding="utf-8")

        # 2. Codex memories + memoryhooker.toml + GPT.md
        codex_mem = home / ".codex" / "memories"
        codex_mem.mkdir(parents=True)
        (codex_mem / "MEMORY.md").write_text("Codex cross-session insight.\n", encoding="utf-8")
        (codex_mem / "automation_memory_proxy_x.md").write_text("Automation proxy must be skipped.\n", encoding="utf-8")
        (codex_mem / "automations").mkdir()
        (codex_mem / "automations" / "job.md").write_text("Automation state must be skipped.\n", encoding="utf-8")
        (home / ".codex" / "memoryhooker.toml").write_text(
            '[mode]\nactive = "remember"\n\n[backend]\norder = ["gardener", "files"]\n',
            encoding="utf-8",
        )
        (home / ".codex" / "GPT.md").write_text("# Codex Rules\nKeep existing lines.\n", encoding="utf-8")

        # 3. Gemini rules + duplicate memory + automations log + settings.json
        gem = home / ".gemini"
        (gem / "memory").mkdir(parents=True)
        (gem / "GEMINI.md").write_text("# Gemini Rules\nExisting guidance.\n", encoding="utf-8")
        (gem / "MEMORY.md").write_text("# Gemini Memory\n- Gemini architectural note.\n", encoding="utf-8")
        (gem / "memory" / "duplicate.md").write_text("Always run unit tests before commit.\n", encoding="utf-8")  # duplicate of prefs
        (gem / "AUTOMATIONS-MEMORY.md").write_text("Automation run log must be skipped.\n", encoding="utf-8")
        (gem / "settings.json").write_text('{"theme":"Default"}\n', encoding="utf-8")

        # 4. Secret-containing file (must be skipped & redacted in warnings)
        fake_tok = "ghp_" + "A" * 24
        (home_mem / "leak.md").write_text(f"token = {fake_tok}\n", encoding="utf-8")

        return {
            "home": home,
            "home_mem": home_mem,
            "claude_rule": claude_rule,
            "claude_settings": claude_settings,
            "hooker_toml": home / ".codex" / "memoryhooker.toml",
            "gpt_md": home / ".codex" / "GPT.md",
            "gem_rule": gem / "GEMINI.md",
            "gem_mem": gem / "MEMORY.md",
            "gem_settings": gem / "settings.json",
            "fake_tok": fake_tok,
        }

    def test_dry_run_makes_no_writes_and_apply_is_idempotent_with_private_silo_exclusion(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = self._build_fake_home(root)
            db_path = str(root / "usmc.db")

            # 1. Dry-run writes nothing
            dry = run_setup(home_dir=env["home"], db_path=db_path, apply=False)
            self.assertEqual(dry["mode"], "dry-run")
            self.assertEqual(dry["import"]["imported"], 0)
            self.assertGreaterEqual(dry["import"]["would_import"], 4)
            self.assertEqual(dry["import"]["skipped_secrets"], 1)
            self.assertEqual(
                {s["silo"] for s in dry["import"]["skipped_private_silos"]},
                {"client-silo", "other-silo", "my-private-notes"},
            )
            self.assertFalse(Path(db_path).exists())
            self.assertNotIn(_SETUP_START, env["claude_rule"].read_text(encoding="utf-8"))
            for w in dry["import"]["warnings"]:
                self.assertIn("[REDACTED:", w)
                self.assertNotIn(env["fake_tok"], w)

            # 2. Apply imports Home + non-private silos, updates configs with backup, preserves sources
            prefs_before = (env["home_mem"] / "prefs.md").read_bytes()
            applied = run_setup(home_dir=env["home"], db_path=db_path, apply=True)
            self.assertEqual(applied["mode"], "apply")
            self.assertEqual(applied["import"]["imported"], 5)
            self.assertEqual(applied["import"]["skipped_duplicates"], 1)
            self.assertEqual((env["home_mem"] / "prefs.md").read_bytes(), prefs_before)

            # Verify private silos, automation files, and secrets are absent from DB
            client = USMCClient(db_path=db_path, agent_id="verify")
            lessons = client.get_lessons(limit=100)
            titles = {item["title"] for item in lessons}
            joined = "\n".join(item["solution"] for item in lessons)
            self.assertIn("User Prefs", titles)
            self.assertIn("Public Repo Note", titles)
            self.assertNotIn("Private client details", joined)
            self.assertNotIn("Do not import this private silo", joined)
            self.assertNotIn("Named private silo", joined)
            self.assertNotIn("Automation proxy must be skipped", joined)
            self.assertNotIn("Automation log", joined)
            self.assertNotIn(env["fake_tok"], joined)
            for item in lessons:
                if item["source_kind"] == "import":
                    self.assertEqual(item["editorial_status"], "review")
                    self.assertEqual(item["privacy_scope"], "private")
                    self.assertAlmostEqual(item["confidence"], 0.20)

            # Verify pointers, index preservation, memoryhooker order, and untouched settings
            self.assertIn(_SETUP_START, env["claude_rule"].read_text(encoding="utf-8"))
            self.assertIn("Existing rule stays.", env["claude_rule"].read_text(encoding="utf-8"))
            idx_text = (env["home_mem"] / "MEMORY.md").read_text(encoding="utf-8")
            self.assertIn(_INDEX_START, idx_text)
            self.assertIn("- [prefs](prefs.md)", idx_text)
            self.assertNotIn("autoMemoryDirectory", env["claude_settings"].read_text(encoding="utf-8"))

            toml_text = env["hooker_toml"].read_text(encoding="utf-8")
            self.assertIn('order = ["usmc", "gardener", "files"]', toml_text)
            self.assertIn("Keep existing lines.", env["gpt_md"].read_text(encoding="utf-8"))
            self.assertIn(_SETUP_START, env["gpt_md"].read_text(encoding="utf-8"))
            self.assertIn(_SETUP_START, env["gem_rule"].read_text(encoding="utf-8"))
            self.assertEqual(env["gem_settings"].read_text(encoding="utf-8"), '{"theme":"Default"}\n')
            self.assertTrue(any(env["hooker_toml"].parent.glob("memoryhooker.toml.bak.*")))

            # 3. Second apply is 100% idempotent (0 new imports, no duplicate writes)
            second = run_setup(home_dir=env["home"], db_path=db_path, apply=True)
            self.assertEqual(second["import"]["imported"], 0)
            self.assertEqual(len(client.get_lessons(limit=100)), len(lessons))

            # 4. --check confirms configured state read-only
            checked = run_setup(home_dir=env["home"], db_path=db_path, check=True)
            self.assertEqual(checked["mode"], "check")
            self.assertTrue(checked["agents"]["claude"]["rule_pointer"])
            self.assertTrue(checked["agents"]["claude"]["memory_index_pointer"])
            self.assertTrue(checked["agents"]["codex"]["usmc_first_in_order"])
            self.assertTrue(checked["agents"]["gemini"]["rule_pointer"])
            self.assertTrue(checked["agents"]["gemini"]["hooks_untouched"])

    def test_cli_setup_json_dry_run_and_apply(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = self._build_fake_home(root)
            db_path = str(root / "cli_usmc.db")
            from io import StringIO
            from unittest.mock import patch

            stdout = StringIO()
            with patch("sys.stdout", stdout):
                rc = main(["--db", db_path, "setup", "--home", str(env["home"]), "--json"])
            self.assertEqual(rc, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["mode"], "dry-run")

            stdout2 = StringIO()
            with patch("sys.stdout", stdout2):
                rc2 = main(["--db", db_path, "setup", "--home", str(env["home"]), "--apply", "--json"])
            self.assertEqual(rc2, 0)
            payload2 = json.loads(stdout2.getvalue())
            self.assertEqual(payload2["mode"], "apply")
            self.assertEqual(payload2["import"]["imported"], 5)
            self.assertEqual(payload2["import"]["skipped_duplicates"], 1)


if __name__ == "__main__":
    unittest.main()
