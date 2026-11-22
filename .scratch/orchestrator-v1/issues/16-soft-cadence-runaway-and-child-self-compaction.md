# 16: Mitigate Soft-Cadence Runaway and Invisible Child Self-Compaction (Capability Re-Evaluation)

**What to build:** Intake for capability triage -- no runtime code or protocol edits yet. Re-evaluate [Ticket 07](07-bidirectional-execution-subagent-lifecycle-rotation.md) strictly on capability fidelity and constraint retention rather than cache-cost ROI, addressing Trade-offs #1 and #2 (`E1`/`E2` from [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md)).

**Blocked by:** None

**Category:** enhancement

**Status:** resolved

**References:** [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) | [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) | [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) | [Ticket 07](07-bidirectional-execution-subagent-lifecycle-rotation.md) | [Ticket 11](11-dual-brain-vs-native-subagent-boundary.md) | [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) | [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) | [.out-of-scope/bidirectional-execution-subagent-rotation.md](../../../.out-of-scope/bidirectional-execution-subagent-rotation.md)

## Problem & Empirical Evidence

1. **Why this re-evaluates Ticket 07 strictly on capability fidelity:** [Ticket 07](07-bidirectional-execution-subagent-lifecycle-rotation.md) was closed as `wontfix` on `$1.68` KV-cache ROI and documented in [.out-of-scope/bidirectional-execution-subagent-rotation.md](../../../.out-of-scope/bidirectional-execution-subagent-rotation.md) with an explicit re-evaluation watch condition for multi-compaction constraint amnesia. Wall-clock idle-TTL rotation remains permanently out of scope; this ticket evaluates **only** capability-fidelity mitigations for long-running execution trajectories (`E1`/`E2` in [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md)).
2. **Soft-Cadence Runaway (`E1`):** Official Native Orchestrator host-forces `[plan review due]` every `30` invocations (`40` checkpoints in `24cd98b2`). In `L0-4`, the `flash` `Execution Subagent` (`b6f60460`) executed `2,196` raw records with only `8` `<report>`s, including a **`446`-tool-call unreviewed gap** (`tc 786 -> 1232`, `15x` past the soft `~30`-turn cadence).
3. **Invisible Child Self-Compaction (`E2`):** Tree-wide inference-step compaction rate in `L0-4` (`1/125` in `fa0dc277`) is `2.1x-2.8x` lower than Official (`1/58.6` in `L0-2`, `1/44.2` in `L0-1`). Even so, `b6f60460` self-compacted **`7` times** (`2` inside that single `446`-tool-call gap) invisibly to `Trunk Session`, risking `Re-plan if:` amnesia and early-constraint drift across chained dispatches.

## Open Triage Decisions

Compare candidate capability mitigations against [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) (no lifecycle hooks, sidecars, or host-specific workflow swaps):

1. **Trunk `<plan>` milestone wave scoping:** Constrain each dispatch `<plan>` to smaller verifiable milestone waves so uninterrupted tool-call runs stay bounded naturally without adding host hooks.
2. **Spontaneous `depth=2` slicing relief in `L0-5+`:** Wait for [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) telemetry (`M3` `depth=2` activation rate and `M4` cadence/compaction decay) to test whether Ticket 11's `depth=2` parallel slicing already breaks up monolithic child runs in `v1.1.3`.
3. **Deterministic, clock-free child `CHECKPOINT` awareness/visibility:** Evaluate whether lightweight visibility into bound-child `CHECKPOINT` count (strictly clock-free, without wall-clock idle TTL and without recreating Ticket 07's cold-start thrashing on large `Living Memory Window`s) is warranted, or whether child-side reporting on self-compaction suffices.
4. **Static `orchestrator-tier: pro` escalation for coupled monoliths:** Leverage workspace-static `orchestrator-tier: pro` (`Hydrogen XHigh`, same `$1.50/$0.075/$7.50` catalog rate, `~10%-18%` extra thinking tokens, `< 1/5` of `S8b`'s `+76.9%` rework buffer) for heavy coupled refactors where `flash` cadence compliance degrades.

## Acceptance Criteria

- [x] Compare Options 1-4 against [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md), [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md), and Ticket 07's prior evidence, and record the triage decision.
- [x] Keep wall-clock idle-TTL rotation permanently out of scope; if any deterministic change is approved, update affected ADRs/docs cleanly. (Narrowed to silent post-compaction `execution-protocol.md` re-read in `harnesses.md` L74/L98; zero `sync_memory.py` or ADR changes needed.)
- [x] Verify contract and regression coverage with `py -3 -m unittest discover -s tests -v` passing cleanly.

## Comments

- 2026-11-22 (Intake): Opened at needs-triage from [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) (Dim 8 Enforcement Rigidity E1 and Dim 9 Invisible Child Self-Compaction E2) to evaluate capability-fidelity mitigations separately from Ticket 07's closed cache-cost ROI question.
- 2026-11-22 (3-Model Heterogeneous /swarm Triage & v1.1.4 Ship -- Resolved): Direct b6f60460 disk transcript inspection proved host compaction preserves parent <plan> and Re-plan if: verbatim while evicting execution-protocol.md (previously loaded only as read_file tool output) and injecting deterministic marker # Resuming from a compaction. Shipped narrowed v1.1.4 fix in harnesses.md L74 and L98 adding silent one-time re-read of <SkillDir>/references/execution-protocol.md after each # Resuming from a compaction summary ($0 Trunk tax, $0 uncompacted, ~$0.015/compaction, 0 Python changes). Locked as wontfix: sync_memory.py child-CHECKPOINT parsing/rotation (ADR-0002/ADR-0006), forced mid-dispatch interim <report> (+$2-$4 cold Trunk wakeup tax), and wall-clock idle TTL (Ticket 07). Residual E1 cadence runaway remains watched under Ticket 13 M4 (reopen only if p95 > 45 with drift or >= 2x violation jump at child CHECKPOINT >= 2 under v1.1.4); S8b retains zero-code orchestrator-tier: pro.
