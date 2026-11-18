# Activation Modes, Coexistence Boundaries, and Package Structure

Type: grilling
Status: resolved
Blocked by: 02

## Question

Once the core Occam-converged Trunk-Subsidiary protocol is locked in Ticket `02`, how should the skill/plugin be triggered (on-demand vs global rule), how does it coexist cleanly with native Orchestrator sessions and isolated blind-review subagents (e.g., `egm-*`), what minimal subsidiary lifecycle/reset rule (if any) earns its place in V1, and what is the simplest repository layout ready for `/to-spec`?

## Answer

1. **Dual-Mode Activation & Unified Package ([ADR-0003](../../../docs/adr/0003-dual-mode-plugin-rule-and-unified-orchestrator-package.md))**: Ship under the unified plugin and skill name `orchestrator` with both `rules/AGENTS.md` (plugin toggle = default global orchestration on Antigravity; disabled = zero tokens) and `skills/orchestrator/SKILL.md` (manual `/orchestrator` for standalone skill installs), keeping all runtime assets (`SKILL.md`, `scripts/sync_memory.py`, `references/execution-protocol.md`, `references/harnesses.md`) self-contained inside `skills/orchestrator/` alongside thin root manifests (`plugin.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`) and `README.md`.
2. **Coexistence, Non-Recursion, and Foreman Delegation ([ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md))**: Yield silently when native `exit_plan_mode`/`enter_plan_mode` tools exist (unless `/orchestrator` is explicitly invoked); restrict `rules/AGENTS.md` strictly to top-level `<USER_REQUEST>` sessions so `[Message] sender=<parent_uuid>` subagents always run single-phase; attach `Living Memory Window` exclusively to the single bound `Execution Subagent` while leaving `Isolated Subagents` (`research`, `egm-*`, slice workers, code reviewers) zero-memory; and let `Execution Subagent` (`depth = 1`) act as foreman on nested-capable hosts (preserving offloaded `Model: "inherit"` inheritance) with Hand-back Trigger #5 fallback to `Trunk Session` (`depth = 0`) on single-depth harnesses.
3. **Subsidiary Lifecycle ([ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md))**: Coupled directly to Trunk `CHECKPOINT` compaction epochs with zero arbitrary turn-count caps.

## Comments

- **Locked Q1 (Activation Mode) & Q3 (Naming & Package Structure)** in [ADR-0003](../../../docs/adr/0003-dual-mode-plugin-rule-and-unified-orchestrator-package.md).
- **Subsidiary reset lifecycle** was already settled in Ticket `02` via compaction-synced rotation ([ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md)).
- **Locked Q2 (Coexistence & Foreman Delegation — Option A)** in [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) after verifying `L0-1` SQLite `generatorMetadata` across all `92` subagents (`81` Exec-mode `egm-*`/`self` inherited Right Brain `M669`, `11` Plan-mode `research` inherited Left Brain `M667`). Ticket resolved.
