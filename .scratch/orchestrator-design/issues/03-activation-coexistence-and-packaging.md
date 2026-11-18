# Activation Modes, Coexistence Boundaries, and Package Structure

Type: grilling
Status: claimed
Blocked by: 02

## Question

Once the core Occam-converged Trunk-Subsidiary protocol is locked in Ticket `02`, how should the skill/plugin be triggered (on-demand vs global rule), how does it coexist cleanly with native Orchestrator sessions and isolated blind-review subagents (e.g., `egm-*`), what minimal subsidiary lifecycle/reset rule (if any) earns its place in V1, and what is the simplest repository layout ready for `/to-spec`?

## Comments

- **Locked Q1 (Activation Mode) & Q3 (Naming & Package Structure)** in [ADR-0003](../../../docs/adr/0003-dual-mode-plugin-rule-and-unified-orchestrator-package.md):
  - **Q1**: Mode 1 dual-mode activation—bundle `rules/AGENTS.md` + `skills/orchestrator/SKILL.md` so enabling the plugin on Antigravity turns on default orchestration (disabling = zero tokens), while standalone `skills/orchestrator/` installs stay manual `/orchestrator`.
  - **Q3**: Unified plugin and skill identifier `orchestrator` (verified collision-free across `~/.gemini`) with self-contained assets under `skills/orchestrator/` (`SKILL.md`, `scripts/sync_memory.py`, `references/execution-protocol.md`, `references/harnesses.md`) and thin root manifests (`plugin.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`), `rules/AGENTS.md`, and `README.md`.
- **Subsidiary reset lifecycle** was already settled in Ticket `02` via compaction-synced rotation ([ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md)).
- **Remaining Open Item (Q2)**: Coexistence and non-interference boundaries (native `Orchestrator` deference, subagent `rules/AGENTS.md` recursion guard, and `Isolated Subagents` / nested multi-agent delegation at `depth = 1 -> 2` vs single-depth harnesses) pending user confirmation after reviewing Official Orchestrator's empirical `L0-1` behavior.
