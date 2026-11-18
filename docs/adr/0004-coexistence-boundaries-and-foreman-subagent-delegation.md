# Coexistence Boundaries, Three-Way Inbound Routing, and Isolated Subagent Orthogonality

## Context

In Antigravity workspaces, `AGENTS.md` / `GEMINI.md` rules propagate automatically into child subagents, native `Orchestrator` virtual-model sessions expose same-thread hot-swap tools, `/swarm` workflows coordinate multi-agent boards, and third-party plugins/skills (`research`, `egm-*`, `code-review`) spawn parallel `Isolated Subagents` from the `Trunk Session`. Without strict entry ordering and sender-scoped `[Message]` routing, `orchestrator` risks recursing inside child subagents, running unnecessary CLI checks on pure Q&A turns, or colliding with legitimate `Isolated Subagent` wakeups.

## Decision

1. **Ordered Entry Gate With Zero-CLI Pure Q&A Fast-Path**:
   - **Gate 0 (Activation Authority)**: Authorize when active `AGENTS.md` / `GEMINI.md` rules adopt `orchestrator`, literal `/orchestrator` was invoked in the current or earlier turn of the session, or read-only inspection of `<Artifact Directory Path>/scratch/orchestrator/state.json` (when present) shows non-null `bound_subagent_id`.
   - **Gate 1 (Unconditional Native Orchestrator Deference)**: If exact lowercase `exit_plan_mode` or `enter_plan_mode` exists in the toolset, yield unconditionally (even if `/orchestrator` was typed).
   - **Gate 2 (Active `/swarm` Deference)**: Yield silently to explicit leading/command `/swarm` invocations (distinct from prose mentioning `/swarm`) and `[swarm]` / `[board]` `@<worker>` turns.
   - **Gate 3 (Uncompacted Root Check + Direct Answer Fast-Path + Fail-Closed Compaction Check)**: On uncompacted conversations, yield single-phase if `step 0` started with `[Message] timestamp=... sender=<parent_uuid>` (no preceding user turns), `[swarm]`, `[board]`, or `[EXECUTION SUBAGENT — SINGLE PHASE]`. Otherwise, evaluate the **Direct Answer Gate** first: when the turn is a pure question, explanation, or zero-edit review and is **not** an inbound `[Message]` wakeup from `state.bound_subagent_id`, answer directly in-session and stop with **zero** CLI subprocess calls or disk writes—even post-compaction. Only on turns proceeding toward workspace edits, external side effects, `[plan review]`, or recovery: if host `<CONTEXT_SUMMARY>` or `# Resuming from a compaction` framing appears outside user text, run read-only `skills/orchestrator/scripts/sync_memory.py check-origin` first and yield single-phase on `"SUBAGENT"`, `"UNKNOWN"`, or any non-zero exit code—backed up by `sync`'s `SKIP_SUBAGENT_SESSION` guard before any dispatch. Verify `invoke_subagent` and `send_message` only after reaching dispatch.

2. **Three-Way Inbound `[Message]` Routing**:
   - If `state.json` is absent, treat `bound_subagent_id` as `null` and `execution_subagent_ids` as `[]` with zero CLI writes.
   - **`sender == state.bound_subagent_id`**: Enter Official `[plan review]` (never letting `[plan review]` edits happen directly in `Trunk Session`; if the user sends an additive request while `manage_subagents("list")` shows `"running"`, either yield to await active execution completion or `kill` + `reset` + re-plan cleanly without double-messaging `"running"`).
   - **`sender != state.bound_subagent_id` and `sender in state.execution_subagent_ids`** (including superseded/killed branches): Orphaned `Execution Subagent`—ignore its payload and `kill` if still running without entering `[plan review]`; `retired_subagent_max_step` keeps its late `<report>` out of subsequent `Living Memory Window` pages.
   - **`sender not in state.execution_subagent_ids`**: Parallel `Isolated Subagent` or host system notice—process normally in `Trunk Session` with zero `state.json` mutation or `[plan review]` gating.
   - When on-demand raw inspection is needed after compaction, `references/harnesses.md` derives `<bound_subagent_id>`'s `logAbsoluteUri` deterministically as the sibling transcript `<parent of Artifact Directory Path>/<bound_subagent_id>/.system_generated/logs/transcript.jsonl`.

3. **Parallel `Isolated Subagent` Orthogonality**:
   - `Living Memory Window` and `orchestrator-tier:` apply **exclusively** to the single bound `Execution Subagent`; all `Isolated Subagents` invoked from `Trunk Session` retain 100% of their native skill/host model rules and receive zero injected memory. Nested workers inside an active `Execution Subagent` inherit its model naturally (handing back via Trigger #2 if nested tools are disabled).

## Consequences

- Pure Q&A turns execute with zero CLI overhead both before and after compaction, while edits, tagless/tagged `[Message]` wakeups from `bound_subagent_id`, and `[plan review]` continuations retain strict fail-closed subagent non-recursion.
- Parallel `Isolated Subagents` (`research`, `egm-*`, `code-review`) coexist safely alongside an active bound `Execution Subagent` without ever being misclassified as orphaned executors.
