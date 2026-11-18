# 03: Multi-Harness Plugin Packaging, Global Routing Rule, and Non-Recursion Guards

**What to build:** Full dual-mode `orchestrator` plugin packaging across Antigravity, Claude Code, and Codex—enclosing the standalone skill module with multi-harness manifests, user documentation, an always-on global routing rule with native Orchestrator deference and child-subagent non-recursion guards, and an automated package and behavioral compliance verification suite (`Seam 2`).

**Blocked by:** 02: Standalone On-Demand Orchestrator Skill and Two-Phase Execution Protocol

**Status:** ready-for-agent

- [ ] Packages valid multi-harness plugin manifests under the unified `orchestrator` identifier across Antigravity, Claude Code, and Codex alongside clear installation and dual-mode usage documentation, with zero startup shell hooks and zero persistent sidecar processes so disabling the plugin reduces context overhead to zero tokens while standalone skill installs remain manual `/orchestrator`.
- [ ] Provides a concise always-on plugin routing rule (strictly within the host's `24,000`-byte per-file rule cap) that routes qualifying top-level conversations into the `orchestrator` skill protocol when the plugin is enabled.
- [ ] Enforces both runtime coexistence guards inside the global routing rule and skill entry gate: (1) yields silently when native same-thread phase-transition tools (`exit_plan_mode` or `enter_plan_mode`) are already present unless `/orchestrator` is explicitly invoked, and (2) activates exclusively on top-level human requests (`<USER_REQUEST>` / `USER_INPUT`), remaining strictly inert whenever a session is woken by an inter-agent `<SYSTEM_MESSAGE>` (`[Message] timestamp=... sender=<parent_uuid> ...`) or subagent role prompt so child subagents never recurse into two-phase orchestration.
- [ ] Delivers an automated `Seam 2` package contract validator verifying manifest validity, unified `orchestrator` naming consistency, zero CJK characters across repository files, and global rule byte-budget compliance, paired with live end-to-end verification of native Orchestrator deference and child-subagent single-phase non-recursion.
