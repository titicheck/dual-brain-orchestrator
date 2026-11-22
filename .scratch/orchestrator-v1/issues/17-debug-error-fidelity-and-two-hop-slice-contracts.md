# 17: Improve S7 Failure Error Fidelity and S8a Two-Hop Slice Contracts

**What to build:** Intake for narrow protocol refinement -- no runtime code or protocol edits yet. Address Trade-off #4 (`E6` from [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md)) strictly for `S7` failure error fidelity and `S8a` two-hop delegation contracts while preserving `Living Memory Window` signal-to-noise ratio.

**Blocked by:** None

**Category:** enhancement

**Status:** resolved

**References:** [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) | [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) | [Ticket 11](11-dual-brain-vs-native-subagent-boundary.md) | [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) | [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md)

## Problem & Empirical Evidence

Dimension 1 (`E6`) in [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) highlighted context-fidelity and two-hop attenuation risks with a strict architectural boundary:

1. **Non-Negotiable Invariant (`Living Memory Window` SNR):** Per [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md), `sync_memory.py` intentionally strips `GENERIC` tool outputs, `tool_calls`, and `thinking` from `Living Memory Window` pages. That filtering is the core mechanism delivering `~95%` KV-cache hit rate and clean `Trunk Session` planning SNR, so raw tool logs must **never** be flooded back into `Trunk Session`.
2. **`S7` Deep Debugging / Slow-Bench Failure Fidelity:** On Trigger #1 ("failed twice") and Trigger #2 (unexpected environment or dependency blocker), over-summarized `<report>`s can drop exact failing commands, compiler/stack-trace tails, or non-zero exit codes, forcing extra Tier-2 log reads or blind re-plans.
3. **`S8a` Two-Hop Attenuation (`Trunk -> Execution Subagent -> depth=2 worker -> <report>`):** When `Trunk Session` omits explicit interface contracts and disjoint file-ownership boundaries in `<plan>`, two-hop delegation risks cross-slice merge or interface defects that can erode `S8a`'s `+25.8%` rework buffer (`M3`). *(Note: `S4` serial short-loop DevOps CLI UX is intentionally handled via mode selection in [Ticket 14 §5](14-v113-vs-official-vs-v111-full-scenario-evaluation.md#5-practical-mode-selection-guide), not protocol changes.)*

## Open Triage Decisions

1. **Bounded verbatim error tail on Trigger #1/#2 hand-backs:** Require `<report>` §2/§3 on Trigger #1 and Trigger #2 early hand-backs to include the exact failing command, exit code, and a bounded verbatim error excerpt (e.g., concise tail of stderr/stack trace) without changing clean-completion reports or `Living Memory Window` filtering.
2. **Lightweight `<plan>` interface and ownership guidance for parallelizable waves:** Add one-line `<plan>` guidance in `SKILL.md` for `S8a` waves to specify disjoint file ownership and explicit interface contracts, without reintroducing the rigid `Parallel:` DSL syntax rejected in [Ticket 11](11-dual-brain-vs-native-subagent-boundary.md).
3. **Ship vs defer pending `L0-5` telemetry:** Ship now as a lightweight refinement or defer pending `L0-5` data on `M1` (net rework ratio) and `M3` (`depth=2` activation vs merge-defect rate).

## Acceptance Criteria

- [x] Decide on Open Triage Decisions 1-3 without weakening [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) `Living Memory Window` filtering or reintroducing `Parallel:` DSL syntax. (Shipped Decision 1 in `v1.1.4`; explicitly deferred Decision 2 to [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) `M3`/`M1`.)
- [x] Apply approved lightweight doc/protocol edits (if any) cleanly across `SKILL.md` / `execution-protocol.md`. (Applied in-place `<=15 verbatim lines` failure excerpt ceiling in `execution-protocol.md` L52; `SKILL.md` untouched.)
- [x] Confirm `py -3 -m unittest discover -s tests -v` passes with zero hygiene or link regressions.

## Comments

- 2026-11-22 (Intake): Opened at needs-triage from [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) (Dim 1 Context Fidelity & Two-Hop Attenuation, E6) scoped strictly to narrow S7 failure-report fidelity and S8a slice contracts without weakening ADR-0002 Living Memory Window filtering.
- 2026-11-22 (3-Model Heterogeneous /swarm Triage & v1.1.4 Ship -- Resolved): Shipped Decision 1 in v1.1.4 via in-place ceiling at execution-protocol.md L52 (on failure: exact command, exit code, <=15 verbatim lines (first error + final summary)), which upper-bounds verbatim Living Memory Window exports (`sync_memory.py` `<report>` export) while preventing blind re-plans and extra Tier-2 log reads (+84 B, +0 net lines, 0 B Trunk prefix). Locked as wontfix: unbounded failure log dumps into <report> (ADR-0002) and Parallel: DSL (Ticket 11). Deferred Decision 2 (S8a slice-ownership/interface contract pass-through) to Ticket 13 M3 (< 30% spontaneous depth=2 on explicit DAGs or > 20% merge rework) / M1 (> 25% rework or Exit 2 > 30%).
