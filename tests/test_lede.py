#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lede", ROOT / "scripts" / "lede.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load scripts/lede.py")
lede = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lede)


class LedeAdversarialTests(unittest.TestCase):
    def compare_rc(self, discord, telegram):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            d = directory / "discord.txt"
            t = directory / "telegram.txt"
            d.write_text(discord, encoding="utf-8")
            t.write_text(telegram, encoding="utf-8")
            return lede._compare_args(["--discord-file", str(d), "--telegram-file", str(t)])

    def test_identical_short_clone_is_rejected(self):
        text = "**Predixa is live**\n\nOpen the app today and review the launch details at https://app.predixa.xyz."
        self.assertEqual(self.compare_rc(text, text), 1)

    def test_long_synonym_clone_is_rejected(self):
        discord = """## Predixa adds workspace roles

## What changed
Choose a role for each member in workspace settings. Owners can update access at any time.

## Why it matters
Clear roles help teams control access and keep responsibilities visible.

## What you need to do
Open workspace settings, review every member, and save the correct role.

## What's next
The new controls are available today at https://app.predixa.xyz.
"""
        telegram = """**Predixa adds workspace roles**

**What changed**
Select a role for every member in workspace settings. Owners may revise access whenever needed.

**Why it matters**
Defined roles let teams manage access and make responsibilities clear.

**What you need to do**
Visit workspace settings, check each member, and save the right role.

**What's next**
The controls are live now. https://app.predixa.xyz
"""
        self.assertEqual(self.compare_rc(discord, telegram), 1)

    def test_independent_platform_architecture_passes(self):
        discord = """## Workspace roles are live

Owners can now assign each member a role from workspace settings.

Review access today: [Open Predixa](https://app.predixa.xyz)
"""
        telegram = """**Review who can access your workspace**

Open https://app.predixa.xyz and check each member's role. Owners can change assignments from workspace settings; the controls are available now.
"""
        self.assertEqual(self.compare_rc(discord, telegram), 0)

    def test_generic_label_stack_is_rejected(self):
        text = "**What changed**\nFact.\n\n**Why it matters**\nFiller.\n\n**What's next**\nSummary."
        self.assertTrue(lede.structural_errors(text))

    def test_unsupported_urgency_is_rejected(self):
        self.assertTrue(lede.structural_errors("Act now before it is too late."))

    def test_factual_deadline_without_hype_passes(self):
        text = "Old API keys stop working on August 1. Rotate yours in account settings before then."
        self.assertEqual(lede.structural_errors(text), [])


if __name__ == "__main__":
    unittest.main()
