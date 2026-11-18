# Occam's-Razor Adaptation from Same-Thread Hot-Swap to Native Subagent Interop

Type: grilling
Status: resolved
Blocked by: 01

## Question

Auditing `docs/research/01-official-orchestrator-system.md` part by part under Occam's Razor ("introduce nothing beyond what thread separation strictly forces"), what is the minimal set of modifications needed to replace Official Orchestrator's same-thread `exit_plan_mode` / `enter_plan_mode` hot-swap with Trunk-to-Native-Subagent lossless interop—specifically across (1) outbound context + `<plan>` delivery, (2) native subagent invocation/resumption, and (3) inbound reporting and final user reply?

## Answer

Locked under Occam's Razor with only three targeted adaptations over [01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md):

1. **Outbound Context ([ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md))**: Inherit the Trunk's `CHECKPOINT`-bounded `Living Memory Window` (Option B: `CHECKPOINT` summary + verbatim `USER_INPUT` + visible `MODEL` replies + prior execution `<report>`s, omitting raw tool outputs and private `thinking`) via `<40 KB` file pages on first spawn, extend via `(last_synced_step, current_step]` incremental slices on `send_message` continuations, and rotate cleanly to a fresh `Execution Subagent` whenever a new Trunk `CHECKPOINT` occurs.
2. **Delegation**: Inherit each client's built-in native subagent primitive (`invoke_subagent` with non-`inherit` execution tier + `send_message` on Antigravity; native equivalents elsewhere), keeping Official Orchestrator's planning, execution, ~30-step checkpoint, and 5 early hand-back rules intact.
3. **Inbound Return ([ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md))**: Unify all exits into Official Orchestrator's execution `<report>` routed into the Trunk's unmodified three-way `[plan review]` gate, inspecting host-persisted `logAbsoluteUri` on demand without custom receipt or error-dump schemas.

## Comments

- **Inbound reporting & final user sign-off (`Q3`) settled (`2026-11-18`)**: Adopted unified `<report>` return into Official Orchestrator's `[plan review]` gate, reusing host-persisted `logAbsoluteUri` on demand instead of custom receipt/error-dump files. Recorded in [ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md).
- **Baseline EGM audit (`Q1`) completed (`2026-11-18`)**: `01-official-orchestrator-system.md` hardened against `egm-codebase-details` and `egm-comprehension` findings.
- **Outbound context transfer (`Q2`) settled (`2026-11-18`)**: Selected Option B after empirical payload measurements (`02-exploratory-notes-and-host-probes.md` §5) and recorded in [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md). Ticket resolved.
