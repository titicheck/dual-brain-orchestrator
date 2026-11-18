from __future__ import annotations

import json
import pathlib
import re
import subprocess
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "skills" / "orchestrator" / "SKILL.md"
PLUGIN_JSON = REPO_ROOT / "plugin.json"
README_MD = REPO_ROOT / "README.md"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", text, re.DOTALL)
    if not match:
        raise AssertionError("SKILL.md missing YAML frontmatter")
    raw_meta, body = match.group(1), match.group(2)
    meta: dict[str, str] = {}
    for line in raw_meta.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


class PackageContractTests(unittest.TestCase):
    def test_single_root_plugin_manifest_and_zero_forbidden_bundles(self) -> None:
        self.assertTrue(PLUGIN_JSON.is_file(), "plugin.json must exist at repo root")
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        self.assertEqual(data.get("name"), "orchestrator")
        self.assertEqual(data.get("skills"), ["./skills/orchestrator"])
        self.assertIsInstance(data.get("version"), str)
        self.assertTrue(data["version"].strip())
        self.assertIsInstance(data.get("description"), str)
        self.assertTrue(data["description"].strip())

        forbidden = [
            "rules",
            "hooks",
            "hooks.json",
            ".claude-plugin",
            ".codex-plugin",
        ]
        for rel in forbidden:
            self.assertFalse(
                (REPO_ROOT / rel).exists(),
                f"Forbidden V1 top-level path exists: {rel}",
            )

    def test_skill_frontmatter_and_non_spontaneous_continuity_triggers(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        self.assertEqual(meta.get("name"), "orchestrator")
        self.assertNotIn("disable-model-invocation", meta)
        desc = meta.get("description", "")
        self.assertNotIn("names orchestrator", desc.lower())
        self.assertIn("AGENTS.md", desc)
        self.assertIn("/orchestrator", desc)
        self.assertIn("Approve-First", desc)
        self.assertIn("bound_subagent_id", desc)

    def test_readme_copyable_snippet_under_1000_bytes_and_seam_2b_checklist(self) -> None:
        self.assertTrue(README_MD.is_file(), "README.md must exist at repo root")
        text = README_MD.read_text(encoding="utf-8")
        self.assertIn("Seam 2B", text)
        for marker in (
            "exit_plan_mode",
            "enter_plan_mode",
            "check-origin",
            "orchestrator-tier:",
            "Isolated Subagent",
        ):
            self.assertIn(marker, text, f"README missing checklist/doc marker: {marker}")

        # Verify at least one copyable snippet block containing orchestrator-tier: < 1,000 UTF-8 bytes
        fenced = re.findall(r"```(?:markdown|md|text)?\r?\n(.*?)\r?\n```", text, re.DOTALL)
        tier_blocks = [b for b in fenced if "orchestrator-tier:" in b]
        self.assertTrue(tier_blocks, "README must contain a copyable orchestrator-tier: snippet")
        for block in tier_blocks:
            self.assertLess(len(block.encode("utf-8")), 1000)

    def test_relative_markdown_links_and_repo_hygiene(self) -> None:
        cjk_re = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")
        link_re = re.compile(r"\[[^\]]+\]\(([^)#\s]+)(?:#[^)]*)?\)")

        files = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "ls-files", "--others", "--cached", "--exclude-standard"],
            text=True,
        ).splitlines()
        for rel in files:
            p = REPO_ROOT / rel
            if not p.is_file():
                continue
            txt = p.read_text(encoding="utf-8")
            self.assertFalse(
                cjk_re.findall(txt),
                f"CJK characters detected in {rel}",
            )
            if p.suffix == ".md":
                for target in link_re.findall(txt):
                    if target.startswith(("http://", "https://", "C:", "c:", "file:")):
                        continue
                    resolved = (p.parent / target).resolve()
                    self.assertTrue(
                        resolved.exists(),
                        f"Broken relative link in {rel}: {target}",
                    )


if __name__ == "__main__":
    unittest.main()
