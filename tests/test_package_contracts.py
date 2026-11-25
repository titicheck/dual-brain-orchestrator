from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import textwrap
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "skills" / "orchestrator" / "SKILL.md"
EXECUTION_PROTOCOL_MD = REPO_ROOT / "skills" / "orchestrator" / "references" / "execution-protocol.md"
HARNESSES_MD = REPO_ROOT / "skills" / "orchestrator" / "references" / "harnesses.md"
PLUGIN_JSON = REPO_ROOT / "plugin.json"
README_MD = REPO_ROOT / "README.md"
SCRIPTS_DIR = REPO_ROOT / "skills" / "orchestrator" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import sync_memory  # noqa: E402


def _github_heading_slugs(md_text: str) -> set[str]:
    slugs: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in md_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^#{1,6}[ \t]+(.+?)[ \t]*#*$", line)
        if not m:
            continue
        title = m.group(1)
        title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title)
        title = title.replace("`", "").lower().strip()
        slug_chars: list[str] = []
        for ch in title:
            if ch == " ":
                slug_chars.append("-")
            elif ch in ("-", "_") or ch.isalnum():
                slug_chars.append(ch)
        base = "".join(slug_chars)
        count = seen.get(base, 0)
        seen[base] = count + 1
        slugs.add(base if count == 0 else f"{base}-{count}")
    return slugs


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
    def _extract_fenced_blocks(self, text: str) -> list[str]:
        blocks: list[str] = []
        in_fence = False
        lang = ""
        buf: list[str] = []
        for line in text.splitlines():
            stripped = line.lstrip()
            if not in_fence and stripped.startswith("```"):
                in_fence = True
                lang = stripped[3:].strip().lower()
                buf = []
            elif in_fence and line.strip() == "```":
                in_fence = False
                if lang in {"", "markdown", "md", "text"}:
                    blocks.append("\n".join(buf))
            elif in_fence:
                buf.append(line)
        return blocks

    def _extract_adoption_blocks(self, path: pathlib.Path, label: str) -> list[str]:
        text = path.read_text(encoding="utf-8")
        fenced = self._extract_fenced_blocks(text)
        adoption_blocks = [
            b for b in fenced if "## Orchestrator" in b and "orchestrator-tier:" in b
        ]
        self.assertTrue(
            adoption_blocks,
            f"{label} must contain a copyable ## Orchestrator adoption snippet",
        )
        for block in adoption_blocks:
            self.assertLess(
                len(block.encode("utf-8")),
                1000,
                f"{label} adoption snippet must stay < 1,000 UTF-8 bytes",
            )
        return adoption_blocks

    def test_single_root_plugin_manifest_and_zero_forbidden_bundles(self) -> None:
        self.assertTrue(PLUGIN_JSON.is_file(), "plugin.json must exist at repo root")
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        self.assertEqual(data.get("name"), "orchestrator")
        self.assertNotIn("skills", data)
        self.assertLessEqual(set(data.keys()), {"name", "version", "description", "repository"})
        self.assertTrue(SKILL_MD.is_file(), "skills/orchestrator/SKILL.md must exist")
        self.assertEqual(data.get("version"), "2.0.1")
        self.assertIsInstance(data.get("description"), str)
        self.assertTrue(data["description"].strip())

        forbidden = [
            "rules",
            "hooks",
            "hooks.json",
            "mcp_config.json",
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
            "Orchestrator (Neon)",
            "check-origin",
            "orchestrator-tier:",
            "Isolated Subagent",
        ):
            self.assertIn(marker, text, f"README missing checklist/doc marker: {marker}")

        # Verify at least one copyable snippet block containing orchestrator-tier: < 1,000 UTF-8 bytes
        fenced = self._extract_fenced_blocks(text)
        tier_blocks = [b for b in fenced if "orchestrator-tier:" in b]
        self.assertTrue(tier_blocks, "README must contain a copyable orchestrator-tier: snippet")
        for block in tier_blocks:
            self.assertLess(len(block.encode("utf-8")), 1000)

    def test_trunk_efficiency_and_tier_precedence_guards(self) -> None:
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("except conversational", skill_text.lower())
        self.assertNotIn("zero tier overrides", skill_text.lower())
        self.assertIn("untouched by `orchestrator-tier:`", skill_text)
        self.assertRegex(
            skill_text,
            re.compile(
                r"never[^\n]*read_file[^\n]*sync_memory\.py[^\n]*execution-protocol\.md",
                re.IGNORECASE,
            ),
        )
        self.assertRegex(
            skill_text,
            re.compile(r"git status --short[^\n]*git diff --stat"),
        )
        self.assertRegex(
            skill_text,
            re.compile(r"do \*\*not\*\* re-read[^\n]*re-run", re.IGNORECASE),
        )
        self.assertRegex(
            skill_text.split("## `Trunk Session` Planning Turn", 1)[1],
            re.compile(r"compact[^\n]*Approve-First|Approve-First[^\n]*compact", re.IGNORECASE),
        )

        harnesses_text = HARNESSES_MD.read_text(encoding="utf-8")
        self.assertRegex(
            harnesses_text,
            re.compile(r"sync_memory\.py[^\n]*never[^\n]*read_file", re.IGNORECASE),
        )
        self.assertRegex(
            harnesses_text,
            re.compile(r"execution-protocol\.md[^\n]*never[^\n]*read_file", re.IGNORECASE),
        )

        readme_text = README_MD.read_text(encoding="utf-8")
        self.assertIn("untouched by `orchestrator-tier:`", readme_text)
        adoption_blocks = self._extract_adoption_blocks(README_MD, "README.md")
        for block in adoption_blocks:
            lower = block.lower()
            self.assertIn("conversational", lower)
            self.assertIn("never override", lower)
            self.assertIn("bound `execution subagent`", lower)

    def test_relative_markdown_links_and_repo_hygiene(self) -> None:
        cjk_re = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")
        link_re = re.compile(r"\[[^\]]+\]\(([^)#\s]+)?(?:#([^)\s]+))?\)")
        zh_switcher = "[\u7b80\u4f53\u4e2d\u6587](README.zh-CN.md)"

        readme_zh = REPO_ROOT / "README.zh-CN.md"
        self.assertTrue(readme_zh.is_file(), "README.zh-CN.md must exist")
        zh_text = readme_zh.read_text(encoding="utf-8")
        self.assertIn("[English](README.md)", zh_text)
        self.assertIn("Seam 2B", zh_text)
        zh_blocks = self._extract_adoption_blocks(readme_zh, "README.zh-CN.md")
        for block in zh_blocks:
            self.assertIn("\u53e3\u5934", block)
            self.assertIn("\u7edd\u4e0d\u8986\u76d6", block)
        self.assertIn(zh_switcher, README_MD.read_text(encoding="utf-8"))

        slug_cache: dict[pathlib.Path, set[str]] = {}
        files = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "ls-files", "--others", "--cached", "--exclude-standard"],
            text=True,
        ).splitlines()
        for rel in files:
            p = REPO_ROOT / rel
            if not p.is_file():
                continue
            txt = p.read_text(encoding="utf-8")
            if rel != "README.zh-CN.md":
                check_txt = txt.replace(zh_switcher, "", 1) if rel == "README.md" else txt
                self.assertFalse(
                    cjk_re.findall(check_txt),
                    f"CJK characters detected in {rel}",
                )
            if p.suffix == ".md":
                for target, fragment in link_re.findall(txt):
                    if not target and not fragment:
                        continue
                    if target.startswith(("http://", "https://")):
                        continue
                    self.assertFalse(
                        re.match(r"^(?:[A-Za-z]:|file:)", target),
                        f"Machine-local path link detected in {rel}: {target}",
                    )
                    resolved = (p.parent / target).resolve() if target else p.resolve()
                    self.assertTrue(
                        resolved.exists(),
                        f"Broken relative link in {rel}: {target}",
                    )
                    if fragment and resolved.is_file() and resolved.suffix == ".md":
                        if re.fullmatch(r"L\d+(?:-L\d+)?", fragment):
                            continue
                        if resolved not in slug_cache:
                            slug_cache[resolved] = _github_heading_slugs(
                                resolved.read_text(encoding="utf-8")
                            )
                        self.assertIn(
                            fragment,
                            slug_cache[resolved],
                            f"Broken anchor in {rel}: {target}#{fragment}",
                        )

    def test_conditional_host_transcript_schema_probe(self) -> None:
        brain_root = pathlib.Path.home() / ".gemini" / "antigravity" / "brain"
        cli_script = REPO_ROOT / "skills" / "orchestrator" / "scripts" / "sync_memory.py"
        if not brain_root.is_dir():
            self.skipTest("No local Antigravity transcripts found for conditional host schema probe")
        candidates = [
            p
            for p in brain_root.glob("*/.system_generated/logs/transcript.jsonl")
            if p.is_file() and p.stat().st_size > 0
        ]
        if not candidates:
            self.skipTest("No local Antigravity transcripts found for conditional host schema probe")
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for tpath in candidates[:2]:
            folded = sync_memory.fold_jsonl_file(tpath)
            self.assertGreater(len(folded), 0, f"Zero valid JSONL records in {tpath}")

            proc = subprocess.run(
                [sys.executable, str(cli_script), "check-origin", "--transcript", str(tpath)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(proc.returncode, 0, f"check-origin failed on {tpath}: {proc.stderr}")
            origin = json.loads(proc.stdout).get("origin")
            self.assertIn(origin, {"TRUNK", "SUBAGENT", "UNKNOWN"})

    def test_session_bound_command_ownership_contracts(self) -> None:
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        protocol_text = EXECUTION_PROTOCOL_MD.read_text(encoding="utf-8")
        harnesses_text = HARNESSES_MD.read_text(encoding="utf-8")

        for forbidden_host_token in ("WaitMsBeforeAsync", "10000", "manage_task"):
            self.assertNotIn(forbidden_host_token, skill_text)
            self.assertNotIn(forbidden_host_token, protocol_text)
        for forbidden_protocol_tool in (
            "run_command",
            "manage_task",
            "schedule",
            "<SYSTEM_MESSAGE>",
            "invoke_subagent",
            "send_message",
            "manage_subagents",
            "define_subagent",
            "subagent-default-tier",
            "orchestrator-tier",
            "ConversationIds",
            "TypeName",
            "logAbsoluteUri",
            "transcript.jsonl",
        ):
            self.assertNotIn(forbidden_protocol_tool, protocol_text)
        for text in (skill_text, protocol_text, harnesses_text):
            self.assertNotIn("../..", text)

        self.assertNotIn("observational `run_command` builds, tests, or queries", skill_text)
        self.assertIn("Session-Bound Command Ownership Invariant", skill_text.split("## Ordered Entry Gate", 1)[0])
        skill_lower = skill_text.lower()
        self.assertIn("never yield", skill_lower)
        self.assertIn("still running", skill_lower)
        self.assertIn("three-tier verification ladder", skill_lower)
        self.assertIn("persistent services cannot outlive a dispatch", skill_lower)

        protocol_lower = protocol_text.lower()
        for marker in (
            "terminal state",
            "terminate any still-running command",
            "not an exit",
            "polling timers",
            "poll task status",
        ):
            self.assertIn(marker, protocol_lower)
        self.assertNotIn("~30", protocol_lower)

        sec1 = harnesses_text.split("## 2.", 1)[0]
        self.assertIn("WaitMsBeforeAsync <= 10000 ms", sec1)
        self.assertIn("transcript_full.jsonl", sec1)
        handshake_section = harnesses_text.split("## 3. Antigravity Dispatch Handshake", 1)[1].split("## 4. Recovery", 1)[0].lower()
        self.assertIn("terminal state", handshake_section)
        self.assertIn("still-running", handshake_section)
        self.assertIn("not an exit", handshake_section)
        self.assertIn("without polling", handshake_section)
        self.assertIn("terminat", handshake_section)

    def test_adoption_snippets_follow_ssot_thin_pointer_contract(self) -> None:
        readme_zh = REPO_ROOT / "README.zh-CN.md"
        for label, path in [("README.md", README_MD), ("README.zh-CN.md", readme_zh)]:
            adoption_blocks = self._extract_adoption_blocks(path, label)
            for block in adoption_blocks:
                lower = block.lower()
                for required in (
                    "skill.md",
                    "exit_plan_mode",
                    "enter_plan_mode",
                    "/swarm",
                    "execution subagent",
                ):
                    self.assertIn(
                        required,
                        lower,
                        f"{label} adoption snippet missing required token: {required}",
                    )
                for forbidden in (
                    "bound_subagent_id",
                    "[plan review]",
                    "invoke_subagent",
                    "send_message",
                    "check-origin",
                    "--tier",
                    "isolated subagent",
                ):
                    self.assertNotIn(
                        forbidden,
                        lower,
                        f"{label} adoption snippet must not duplicate SKILL.md internal token: {forbidden}",
                    )

    def test_dual_brain_vs_native_subagent_boundary_contracts(self) -> None:
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        protocol_text = EXECUTION_PROTOCOL_MD.read_text(encoding="utf-8")
        harnesses_text = HARNESSES_MD.read_text(encoding="utf-8")
        adr4_text = (
            REPO_ROOT / "docs" / "adr" / "0004-coexistence-boundaries-and-foreman-subagent-delegation.md"
        ).read_text(encoding="utf-8")

        top_level_skill = skill_text.split("## Ordered Entry Gate", 1)[0]
        self.assertIn("Unified Dual-Brain Scope", top_level_skill)
        self.assertIn("exclusively", top_level_skill.lower())
        self.assertIn("living memory window", top_level_skill.lower())
        self.assertIn("orchestrator-tier:", top_level_skill)
        self.assertIn("read-only", top_level_skill.lower())
        self.assertNotIn("Parallel `Isolated Subagent` Orthogonality", skill_text)

        self.assertNotIn("inherit the active execution model tier", protocol_text.lower())
        for label, doc_text in [
            ("ADR-0004", adr4_text),
            ("SKILL.md", skill_text),
            ("harnesses.md", harnesses_text),
        ]:
            lower = doc_text.lower()
            self.assertNotIn("inherit its model", lower, f"Legacy tier inheritance in {label}")
            self.assertNotIn("inheriting the execution model", lower, f"Legacy tier inheritance in {label}")

        protocol_lower = protocol_text.lower()
        for marker in ("child subagent", "never directly to", "trigger #2"):
            self.assertIn(marker, protocol_lower)
        sec2 = protocol_lower.split("## 2.", 1)[1].split("## 3.", 1)[0]
        sec4 = protocol_lower.split("## 4.", 1)[1].split("## 5.", 1)[0]
        sec5 = protocol_lower.split("## 5.", 1)[1]
        for sec_name, sec_text in [
            ("Section 2", sec2),
            ("Section 4", sec4),
            ("Section 5", sec5),
        ]:
            self.assertIn("child subagent", sec_text, f"{sec_name} missing child subagent parity")
        self.assertIn("living memory window", sec5)

        handshake_section = harnesses_text.split("## 3. Antigravity Dispatch Handshake", 1)[1].split("## 4. Recovery", 1)[0].lower()
        recovery_section = harnesses_text.split("## 4. Recovery", 1)[1].split("## 5. Future Client", 1)[0].lower()
        for section_name, section in [
            ("Dispatch Handshake", handshake_section),
            ("Section 4 Recovery", recovery_section),
        ]:
            self.assertIn("child subagent", section, f"{section_name} missing child subagent guard")
        self.assertIn("waiting_for_dependents", handshake_section)
        self.assertIn("descendants", recovery_section)
        self.assertIn("waiting_for_dependents", recovery_section)
        self.assertNotIn("--force-spawn", harnesses_text)
        self.assertNotIn("RESUME_EXISTING", harnesses_text)
        self.assertIn("corrupt state.json", harnesses_text)
        self.assertIn("latest parent dispatch", protocol_lower)
        self.assertIn("last", skill_text.split("## Static Execution Tier Resolution", 1)[1].split("## `Trunk Session` Planning Turn", 1)[0].lower())
        self.assertIn("git log --stat", skill_text)
        self.assertLess(recovery_section.index("kill"), recovery_section.index("reset"))

    def test_v114_compaction_reread_and_failure_excerpt_cap(self) -> None:
        harnesses_text = HARNESSES_MD.read_text(encoding="utf-8")
        handshake_section = (
            harnesses_text.split("## 3. Antigravity Dispatch Handshake", 1)[1]
            .split("## 4. Recovery", 1)[0]
            .lower()
        )
        for marker in (
            "<skilldir>/references/execution-protocol.md",
            "# resuming from a compaction",
            "if not yet re-read since that summary",
        ):
            self.assertIn(
                marker,
                handshake_section,
                f"Dispatch Handshake missing compaction re-read clause: {marker}",
            )

        protocol_sec5 = EXECUTION_PROTOCOL_MD.read_text(encoding="utf-8").split("## 5.", 1)[1].lower()
        self.assertIn("<=15 verbatim lines", protocol_sec5)
        self.assertIn("first error + final summary", protocol_sec5)

        spawn_match = re.search(
            r"## 3\. Antigravity Dispatch Handshake.*?```text\r?\n(.*?)\r?\n\s*```",
            harnesses_text,
            re.DOTALL,
        )
        self.assertIsNotNone(spawn_match, "Dispatch Handshake fenced envelope not found")
        spawn_envelope = textwrap.dedent(spawn_match.group(1)).replace(
            "<SkillDir>",
            "/users/example-user/.gemini/config/plugins/orchestrator/skills/orchestrator-dir",
        )
        marker = "if not yet re-read since that summary)."
        self.assertIn(marker, spawn_envelope)
        end_offset = len(
            spawn_envelope[: spawn_envelope.index(marker) + len(marker)].encode("utf-8")
        )
        self.assertLess(
            end_offset,
            600,
            f"SPAWN_NEW re-read clause byte offset {end_offset} >= 600",
        )

    def test_v200_stateless_always_new_contracts(self) -> None:
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        skill_lower = skill_text.lower()
        self.assertIn("skip redundant", skill_lower)
        self.assertRegex(
            skill_lower,
            re.compile(r"prior `<plan>` bodies[^\n]*never exported to `pages/page_\*\.md`"),
        )
        self.assertIn("already failed", skill_lower)
        self.assertIn("invoke_subagent", skill_text)
        self.assertIn("manage_subagents", skill_text)
        self.assertNotIn("RESUME_EXISTING", skill_text)
        self.assertNotIn("--force-spawn", skill_text)
        self.assertNotIn("--tier", skill_text)

        planning_turn = skill_text.split("## `Trunk Session` Planning Turn", 1)[1].split(
            "## Planner Review Gate", 1
        )[0]
        self.assertIn('manage_subagents(Action="list")', planning_turn)
        self.assertIn("Then run `sync`", planning_turn)
        self.assertLess(
            planning_turn.index('manage_subagents(Action="list")'),
            planning_turn.index("Then run `sync`"),
            "P2-1 ordering: manage_subagents(Action=\"list\") must precede Then run `sync`",
        )

        harnesses_text = HARNESSES_MD.read_text(encoding="utf-8")
        self.assertNotIn("RESUME_EXISTING", harnesses_text)
        self.assertNotIn("--force-spawn", harnesses_text)
        self.assertNotIn("--subagent-transcript", harnesses_text)
        self.assertNotIn("~30", harnesses_text)
        handshake = harnesses_text.split("## 3. Antigravity Dispatch Handshake", 1)[1].split("## 4. Recovery", 1)[0]
        self.assertIn('manage_subagents(Action="list")', handshake)
        self.assertIn("before calling `sync`", handshake)
        self.assertIn("retired_subagent_id", handshake)
        self.assertIn('manage_subagents(Action="kill", ConversationIds=[<retired_subagent_id>])', handshake)
        self.assertIn("never spend a dedicated extra post-`bind`", handshake)
        self.assertIn("otherwise apply §4 first", handshake)

        recovery = harnesses_text.split("## 4. Recovery", 1)[1].split("## 5. Future Client", 1)[0].lower()
        self.assertIn("never respawn", recovery)
        self.assertIn("plain-text `<report>`", recovery)

        sync_src = (SCRIPTS_DIR / "sync_memory.py").read_text(encoding="utf-8")
        for removed in (
            "RESUME_EXISTING",
            "should_rotate_for_cost",
            "import hashlib",
            "import datetime",
            "from datetime",
            "time.time",
        ):
            self.assertNotIn(removed, sync_src)


if __name__ == "__main__":
    unittest.main()
