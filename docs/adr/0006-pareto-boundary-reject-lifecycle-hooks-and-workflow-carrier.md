# Pareto Boundary: Reject Lifecycle Hooks, Workflow Carrier, Child Stripping, and Trunk Micro-Edit Exemptions

## Context

Following V1 verification and live head-to-head benchmarking ([03-ab-benchmark-and-kv-cache-telemetry.md](../research/03-ab-benchmark-and-kv-cache-telemetry.md)), a post-V1 architectural audit ([04-post-v1-host-primitives-and-model-matrix-audit.md](../research/04-post-v1-host-primitives-and-model-matrix-audit.md)) evaluated four potential hardening changes and one defensive maintenance enhancement:

1. Adding Antigravity lifecycle `hooks.json` (`PreToolUse`) guards to hard-block `Trunk Session` workspace edits outside the model prompt;
2. Replacing native `invoke_subagent` + `send_message` with `run_workflow` scripted Python agent orchestration;
3. Stripping inherited workspace/global rules and skills from `Execution Subagent` (or adding redundant child skip clauses to static `AGENTS.md` rules) under the hypothesis of an `inheritCustomizations` isolation flag;
4. Opening a small-edit exemption (`<= 5` lines of spelling or configuration changes) executed directly inside `Trunk Session` instead of dispatching `Execution Subagent`;
5. Adding a conditional host transcript schema probe in `tests/test_package_contracts.py` plus updating `README.md` `Seam 2B` examples to include the newly released `Orchestrator (Neon)` model.

## Decision

Freeze the V1 pure-skill single-manifest architecture at its current Pareto boundary without adding `hooks.json` or replacing native subagents with `run_workflow`; retain `TypeName="self"` inheritance for `Execution Subagent` without extra redundant `AGENTS.md` child-suppression prose; reject any `Trunk Session` micro-edit loophole so the zero-edit `Trunk Session` discipline remains strict and binary; and add only the zero-runtime-overhead conditional host transcript schema probe plus `Orchestrator (Neon)` documentation sync.

## Consequences

1. **Lifecycle `hooks.json` Rejected**: Primary-source inspection of Antigravity's `hooks.md` shows `PreToolUse` spawns synchronous shell commands (`cmd /c` on Windows) globally across all conversations and active `Execution Subagents`, while omitting active tool declarations (`exit_plan_mode`) and resolved `AGENTS.md` trees from stdin—creating false-positive block hazards on unconfigured or native Orchestrator runs and violating pure-skill zero-global-side-effect packaging (`ADR-0003`).
2. **Scripted `run_workflow` Carrier Rejected**: Primary-source inspection of `run-workflow/SKILL.md` establishes that every `agent()` inside a workflow is terminated when the workflow exits (*"every agent ends when the workflow ends"*), destroying cross-turn `Idle` `Execution Subagent` KV-cache continuation, and that non-preapproved tool calls inside workflows are denied without prompting the user.
3. **Rule Inheritance Retained (`TypeName="self"`)**: Binary symbol inspection of `agy.exe` and `GetAllPlugins` `mixinConfig` confirms no `inheritCustomizations` setting exists. Keeping `TypeName="self"` preserves workspace `AGENTS.md` rules (`karpathy-guidelines`, `verification-before-completion`) and project engineering skills on `Execution Subagent` (`100%` prefix-cached from step 2 onward), while existing `step 0` gating already kept child `SKILL.md` reads at `0/3` in live runs without extra rule clutter.
4. **Binary Zero-Edit `Trunk Session` Boundary Preserved**: Allowing small direct edits in `Trunk Session` would consume an extra full-context frontier `Trunk Session` turn (burning scarce `Claude Opus` or `Neon` quota instead of offloading to `flash`) and erode the zero-exception boundary that yielded `0%` unauthorized `Trunk Session` edits across 84 observed steps. Settled small follow-ups rely strictly on Depth Matching concise 1–2 sentence `RESUME_EXISTING` `<plan>` dispatch.
5. **Defensive Schema & Doc Sync Added**: Adding a conditional local transcript probe catches upstream host JSONL schema drift early without impacting CI or clean machines (`skipTest` when absent), and Gate 1 (`exit_plan_mode` / `enter_plan_mode` detection) automatically covers `Orchestrator (Neon)` alongside `Orchestrator (Carbon)` and `Orchestrator (Argon)`.
