# Activation Modes, Coexistence Boundaries, and Package Structure

Type: grilling
Status: resolved
Blocked by: 02

## Question

Once the core Occam-converged Trunk-Subsidiary protocol is locked in Ticket `02`, how should the skill/plugin be triggered (on-demand vs global rule), how does it coexist cleanly with native Orchestrator sessions and isolated blind-review subagents (e.g., `egm-*`), what minimal subsidiary lifecycle/reset rule (if any) earns its place in V1, and what is the simplest repository layout ready for `/to-spec`?

## Answer

1. **Matt-Aligned Pure-Skill Plugin Packaging, Shared-Library Rule Adoption & Fast-Tier Lock ([ADR-0003](../../../docs/adr/0003-dual-mode-plugin-rule-and-unified-orchestrator-package.md))**: Ship under the unified plugin and skill name `orchestrator` with zero top-level `rules/` directory, zero `hooks.json`, and zero persistent sidecars (`plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `README.md`, self-contained `skills/orchestrator/` including `agents/openai.yaml` and `references/rule-adoption.md`, and `tests/`). Both `SKILL.md` and `agents/openai.yaml` keep model-side invocation enabled while `SKILL.md`'s frontmatter `description` forbids spontaneous self-activation on ordinary prompts—activating **only** on explicit `/orchestrator` invocation (defaulting to the fast tier while allowing scoped tier overrides) or explicit opt-in to **Rule-Driven Auto Mode** via shared-library/workspace `AGENTS.md` or `CLAUDE.md` (strictly locked to the fast tier—`"flash"` on Antigravity—with conversational tier drift prohibited).
2. **Coexistence & Parallel Orthogonality with Isolated Subagents ([ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md), [ADR-0005](../../../docs/adr/0005-universal-native-subagent-carrier-and-swarm-deference.md))**: Under Rule-Driven Auto Mode (enforced in both `references/rule-adoption.md` and `SKILL.md`'s defense-in-depth Entry Gate), yield silently when native `exit_plan_mode`/`enter_plan_mode` tools exist or `/swarm` is invoked for the active task (unless `/orchestrator` is explicitly invoked); check **session origin (`step 0`)** so top-level `<USER_REQUEST>` sessions (including `<report>` wakeups) orchestrate while `[Message] sender=<parent_uuid>` subagents, `[swarm]`/`[board]` `@<member>` sessions, and `[EXECUTION SUBAGENT — SINGLE PHASE]` sessions always run single-phase even when workspace `AGENTS.md` propagates into child sessions; keep `Execution Subagent` and `Isolated Subagents` completely parallel and orthogonal—attaching `Living Memory Window` and fast-tier offloading solely to the bound `Execution Subagent` while leaving all plugin/skill `Isolated Subagents` (`egm-*`, `code-review`, `research`) 100% governed by their own skill/host model rules with zero special-case review routing inside `orchestrator`.
3. **Subsidiary Lifecycle ([ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md))**: Coupled directly to Trunk `CHECKPOINT` compaction epochs with zero arbitrary turn-count caps.

## Comments

- **Locked Q1 (Activation Mode) & Q3 (Matt Pure-Skill Packaging & Shared-Rule Adoption)** in [ADR-0003](../../../docs/adr/0003-dual-mode-plugin-rule-and-unified-orchestrator-package.md) (revised to eliminate Antigravity plugin-toggle coupling per user architectural feedback).
- **Subsidiary reset lifecycle** was already settled in Ticket `02` via compaction-synced rotation ([ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md)).
- **Locked Q2 (Coexistence & Foreman Delegation — Option A)** in [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) after verifying `L0-1` SQLite `generatorMetadata` across all `92` subagents (`81` Exec-mode `egm-*`/`self` inherited Right Brain `M669`, `11` Plan-mode `research` inherited Left Brain `M667`). Ticket resolved.
