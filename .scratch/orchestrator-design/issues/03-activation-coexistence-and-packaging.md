# Activation Modes, Coexistence Boundaries, and Package Structure

Type: grilling
Status: resolved
Blocked by: 02

## Question

Once the core Occam-converged Trunk-Subsidiary protocol is locked in Ticket `02`, how should the skill/plugin be triggered (on-demand vs global rule), how does it coexist cleanly with native Orchestrator sessions and isolated blind-review subagents (e.g., `egm-*`), what minimal subsidiary lifecycle/reset rule (if any) earns its place in V1, and what is the simplest repository layout ready for `/to-spec`?

## Answer

1. **Dual-Mode Activation, Global `flash` Lock & Unified Package ([ADR-0003](../../../docs/adr/0003-dual-mode-plugin-rule-and-unified-orchestrator-package.md))**: Ship under the unified plugin and skill name `orchestrator` with both `rules/AGENTS.md` (plugin toggle = default global orchestration locked strictly to default `flash` execution tier with conversational tier overrides disallowed to prevent global drift; disabled = zero tokens) and `skills/orchestrator/SKILL.md` (manual `/orchestrator` defaulting to `flash` and allowing scoped explicit tier overrides on that invocation), keeping all runtime assets self-contained inside `skills/orchestrator/` alongside thin root manifests (`plugin.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`) and `README.md`.
2. **Coexistence & Parallel Orthogonality with Isolated Subagents ([ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md), [ADR-0005](../../../docs/adr/0005-universal-native-subagent-carrier-and-swarm-deference.md))**: Yield silently when native `exit_plan_mode`/`enter_plan_mode` tools exist or `/swarm` is invoked (unless `/orchestrator` is explicitly invoked); restrict `rules/AGENTS.md` strictly to top-level `<USER_REQUEST>` sessions so `[Message] sender=<parent_uuid>` subagents and `[swarm]`/`[board]` `@<member>` sessions always run single-phase; keep `Execution Subagent` and `Isolated Subagents` completely parallel and orthogonal—attaching `Living Memory Window` and `flash` offloading solely to the bound `Execution Subagent` while leaving all plugin/skill `Isolated Subagents` (`egm-*`, `code-review`, `research`) 100% governed by their own skill/host model rules with zero special-case review routing inside `orchestrator`.
3. **Subsidiary Lifecycle ([ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md))**: Coupled directly to Trunk `CHECKPOINT` compaction epochs with zero arbitrary turn-count caps.

## Comments

- **Locked Q1 (Activation Mode) & Q3 (Naming & Package Structure)** in [ADR-0003](../../../docs/adr/0003-dual-mode-plugin-rule-and-unified-orchestrator-package.md).
- **Subsidiary reset lifecycle** was already settled in Ticket `02` via compaction-synced rotation ([ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md)).
- **Locked Q2 (Coexistence & Foreman Delegation — Option A)** in [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) after verifying `L0-1` SQLite `generatorMetadata` across all `92` subagents (`81` Exec-mode `egm-*`/`self` inherited Right Brain `M669`, `11` Plan-mode `research` inherited Left Brain `M667`). Ticket resolved.
