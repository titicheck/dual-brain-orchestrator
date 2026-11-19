# Post-V1 Host Primitives, Inheritance Isolation, and Role Matrix Audit

Empirical primary-source audit conducted on `2026-11-19` against installed Antigravity host documentation, binary symbols, live Language Server RPC metadata, and captured `Seam 2B` trajectories, settling [ADR-0006](../adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md).

---

## 1. Host Primitive & Binary Verification Evidence

| Audit Topic | Primary Source Verified | Empirical Finding |
|---|---|---|
| **Lifecycle Hooks (`PreToolUse`)** | Built-in `agy-customizations/docs/hooks.md` (lines 85–240, 426–429) | Host supports `SessionStart`, `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, and `Stop` (no `Decide` event). `PreToolUse` runs synchronously via `cmd /c` on Windows per matched tool call across all sessions and subagents; its JSON stdin (`conversationId`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath`, `modelName`, `lastUserInput`, `hookEventName`, `cwd`, `toolCall`, `stepIdx`) excludes active declared toolsets (`exit_plan_mode`) and resolved `AGENTS.md` trees, making safe conditional gating fragile and slow. |
| **Workflow Engine (`run_workflow`)** | Built-in `run-workflow/SKILL.md` (lines 9, 111, 133–135) | Explicit guidance says *"Don't use for a single delegated task (use a subagent)"*. Line 111 confirms *"every agent ends when the workflow ends"*, preventing `Idle` multi-turn `Execution Subagent` KV-cache reuse across user turns. Line 133 confirms *"The user cannot be asked anything from a workflow: a call that needs user approval that has not already been granted is denied."* |
| **Subagent Rule & Skill Inheritance** | Built-in `migrate-agent-settings/SKILL.md` (lines 146–162), `agy.exe` symbol scan, live `GetAllPlugins` `egm` `mixinConfig`, and [03-ab-benchmark-and-kv-cache-telemetry.md](03-ab-benchmark-and-kv-cache-telemetry.md) | No `inheritCustomizations` key exists in Antigravity plugin or `agents/*.md` schemas (`name`, `description`, `subagent`, `mainAgent`, `tools` only); compiled `egm` agents still include `skills` and `user_rules` sections. Existing `step 0` gating yielded `0/3` spurious `orchestrator/SKILL.md` reads across `cee193f2`, `72e8ba49`, and `49cee118`, so keeping `TypeName="self"` preserves `AGENTS.md` standards and engineering skills (`karpathy-guidelines`, `verification-before-completion`) at zero extra `SKILL.md` clutter. |
| **Micro-Edit Exemption vs Quota & Safety** | [01-official-orchestrator-system.md](01-official-orchestrator-system.md) (Part 2.1, Part 2.3) & [03-ab-benchmark-and-kv-cache-telemetry.md](03-ab-benchmark-and-kv-cache-telemetry.md) | Calling `edit_file` directly in `Trunk Session` forces a second full-context frontier LLM turn (`80k–150k` prefix) after tool return and permanently appends edit traces to the frontier pool (burning scarce non-Gemini quota when using `Claude Opus` planner) while eroding the zero-exception edit boundary (`0/84` unauthorized `Trunk Session` edits observed). Depth Matching concise 1–2 sentence `RESUME_EXISTING` `<plan>` dispatch preserves both purity and offload economics. |

---

## 2. Updated Antigravity Model Roster & `engineering-kit` Workflow Role Matrix (`2026-11-19`)

Live `swarm{action: "models", all: true}` query on `2026-11-19` verified the release of:
- **`Gemini 4 Neon`** (`gemini-4-neon-low`, `gemini-4-neon-medium`, `gemini-4-neon-high`, `gemini-4-neon-xhigh`);
- **`Orchestrator (Neon)`** (`gemini-pro-orchestrator-neon`, sharing the same `exit_plan_mode` / `enter_plan_mode` virtual-model host protocol covered automatically by Gate 1).

Quota isolation observed on `2026-11-19`:
- `Claude Opus 5.5`, `Claude Sonnet 5.5`, and `GPT-OSS 120B (Medium)` reported `100%` remaining quota (shared third-party pool);
- `Gemini 3.8 Flash`, `Gemini 4 Argon`, `Gemini 4 Carbon`, `Gemini 4 Hydrogen`, `Gemini 4 Neon`, and native `Orchestrator` variants reported `90%` remaining quota (Google Gemini pool).

Operational model assignment across `engineering-kit` stages:

| `engineering-kit` Stage | Primary Artifacts & Actions | Recommended Selection | When `Carbon (High)` Applies |
|---|---|---|---|
| **1. Exploratory Ideation & `/grill-me`** | Interactive boundary questioning & design tradeoff discussion | Primary: **`Gemini 4 Neon (High)`**; Cross-family critique: **`Claude Opus 5.5`** | No — avoid same-family high-latency turns |
| **2. Spec & ADR Convergence** | `.scratch/.../spec.md`, `docs/adr/*.md` | **`Gemini 4 Neon (High / XHigh)`** | No — standard modular specs fit well within `512K` |
| **3. Dual-Brain Daily Implementation** | Ticket execution, `<plan>` dispatch, `[plan review]` | Trunk: **`Gemini 4 Neon (High)`**; `Execution Subagent`: **`orchestrator-tier: flash`** (`Hydrogen`) | No — `Neon` tool-calling adherence protects soft orchestration invariants |
| **4. Review & Pre-Completion Gates** | `code-review`, `egm-*`, `verification-before-completion` | **`Gemini 4 Neon (High)`** or **`Claude Opus 5.5`** (`Isolated Subagent`) | No |
| **5. `> 512K` Repo Ingestion & Root-Cause Deep Dives** | First-pass mapping over huge monolithic repos exceeding `512K` context, or single-shot offline deadlock/invariant proofs | **`Gemini 4 Carbon (High)`** (`1M` context ceiling) | Yes — hard `512K` context or dead-end deep-search boundary only |
