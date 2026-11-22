# Host Physical UX and Runtime Ceilings

`orchestrator` accepts host-imposed physical UX and runtime ceilings rather than trying to emulate native host planner mechanics with hooks, sidecars, synthetic keepalive traffic, or unified-governance bypasses, preserving [ADR-0001](../docs/adr/0001-unified-subagent-report-return-into-plan-review.md), [ADR-0006](../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md), and [ADR-0007](../docs/adr/0007-session-bound-command-ownership.md).

## Why this is out of scope

- **`S1` micro-task fixed orchestration overhead (`~$0.03-$0.08`, `~19.2K` Turn-1 cold prefill):** Every execution completion routes back through `Trunk Session` `[plan review]` per [ADR-0001](../docs/adr/0001-unified-subagent-report-return-into-plan-review.md). Bypassing `[plan review]` for tiny edits breaks unified governance; `S1` 1-2 line edits are handled by mode selection (plain single-model or Official Native Orchestrator).
- **No mid-flight soft interrupts (`[plan review due]`):** Without host-enforced lifecycle hooks (rejected in [ADR-0006](../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md)), `Trunk Session` cannot soft-pause an in-flight `Execution Subagent`. Clean `kill + reset + re-plan` remains the sole safe recovery path when steering mid-dispatch.
- **Hidden child execution traces on the main chat canvas:** Streaming live `Execution Subagent` tool calls and diffs onto the primary chat surface requires first-party host UI support outside a pure Skill plugin.
- **No persistent background dev servers or daemons outliving a dispatch:** Per [ADR-0007](../docs/adr/0007-session-bound-command-ownership.md), all commands are session-bound; persistent services must be verified and terminated before returning `<report>`.
- **No agent-level KV-cache keepalive heartbeats:** Forensically disproved across `L0-4` and `264` local transcripts in [Ticket 13](../.scratch/orchestrator-v1/issues/13-v113-empirical-watch-and-residual-boundaries.md) -- zero host heartbeats exist (`gen_metadata` matches visible `PLANNER_RESPONSE` steps `1:1`; `12/12` `>30m` gaps in `L0-4` hit `0.0%`), and synthetic keepalive turns are strictly negative-EV (cache reads cost `5%` of cold prefill, `>80m` waits lose even at `100%` hit, and any mid-wait LRU eviction triggers `100%` cold reload = `2x-3x` spend).

## Re-evaluation Trigger

- Revisit only if Antigravity natively exposes first-party soft-interrupt primitives, inline child-trace streaming, or cross-session background process ownership without custom lifecycle hooks or sidecars.

## Prior requests

- [Ticket 14: Full-Scenario Dual-Axis Evaluation (v1.1.3 vs Official Native Orchestrator vs v1.1.1)](../.scratch/orchestrator-v1/issues/14-v113-vs-official-vs-v111-full-scenario-evaluation.md) (Dim 10 Trade-off #5 & Section 5 mode-selection guide, `2026-11-22`)
- [Ticket 13: Track v1.1.3 Residual Boundaries and L0-5 Production Telemetry Watch](../.scratch/orchestrator-v1/issues/13-v113-empirical-watch-and-residual-boundaries.md) (Boundary 2 no-heartbeat proof & Boundary 3 micro-task overhead)
