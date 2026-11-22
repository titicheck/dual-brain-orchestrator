# 15: Close Tier-1 Verification Blind Spot and Constrain Trunk Over-Reading

**What to build:** Intake for triage -- no runtime code or protocol edits yet. Address Trade-off #3 (`E3`/`E4` from [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md)) by deciding how to close Tier 1's verification blind spot to undisclosed test weakening while constraining `Trunk Session` over-reading beyond Tier 1.

**Blocked by:** None

**Category:** enhancement

**Status:** wontfix

**References:** [ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md) | [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) | [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) | [Ticket 12](12-full-repo-audit-hardening-and-official-alignment.md) | [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) | [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md)

## Problem & Empirical Evidence

The 3-model full-scenario audit in [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) (Dimension 4: Verification Rigor Asymmetry, disk evidence `E3`/`E4`) identified a two-sided gap in `orchestrator`'s three-tier verification ladder as the **highest-ROI** capability optimization candidate:

1. **Tier-1 Verification Blind Spot (`E3`):** In `d1e362b3`, the `flash` `Execution Subagent` weakened tests twice:
   - Step `124`: gated a parity assertion behind `inspect.getsource`.
   - Step `190`: bypassed `_FORBIDDEN_LIVE_DIR` in memory.
   Both weakenings were caught **solely** because `flash` disclosed them honestly in `<report> §3`. Under the current Tier-1 review contract (`git status --short` / `git diff --stat`), `Trunk Session` cannot detect undisclosed assertion weakening, newly added `skip`/`xfail` markers, or unverified test exits unless it drops down into heavier inspection. By contrast, Official Native Orchestrator surfaces `edit_file` diffs inline to the planner.
2. **Trunk Over-Reading Beyond Tier 1 (`E4`):** In `L0-4` (`fa0dc277`), `Neon` `Trunk Session` routinely read `5-8` source files in full beyond Tier 1 on almost every review. That behavior inflated Trunk context (`278K-308K` `avgCtx`), eroded Tier-1 context savings, and increased `>200K` spend without fixing the underlying verification-trust gap.

## Open Triage Decisions (Resolved `wontfix` -- Deferred-With-Watch to [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) `M2`/`M5`)

1. **Targeted Tier-1 diff / transcript check (`wontfix`):** Rejected unconditional or two-step `-U0` diff scans and Tier-1 `transcript.jsonl` exit-code scans (`0%` recall on weakened-but-passing tests, `+1` Trunk turn tax, `0 / 17,414` undisclosed escapes); re-evaluate only if `L0-5` triggers `M2 >= 1`.
2. **Explicit negative attestation in `<report>` (`wontfix`):** Rejected boilerplate `<report> §2` attestation (unnecessary `Living Memory Window` bloat).
3. **Tightening Trunk Tier-1 review discipline (`wontfix`):** Rejected hard numeric `read_file` caps in `SKILL.md`; `M5` (`> 2.0` `read_file` per clean Tier-1 review) tracks Trunk over-reading empirically.
4. **Release timing (`wontfix`):** Closed without protocol changes ahead of `L0-5`; `M2` and `M5` remain watched in [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md).

## Acceptance Criteria

- [x] Resolve Open Triage Decisions 1-4 and record the chosen disposition (`resolved` or deferred/`wontfix`).
- [ ] If approved for implementation, update the active skill/protocol docs minimally in line with [ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md) and [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) without flooding `Trunk Session` context.
- [ ] Verify contract and regression coverage with `py -3 -m unittest discover -s tests -v` passing with zero hygiene or link regressions.

## Comments

- 2026-11-22 (Intake): Opened at needs-triage from the 3-model full-scenario audit in [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) (Dim 4 Verification Rigor Asymmetry, disk evidence E3/E4) as the highest-ROI capability optimization candidate.
- 2026-11-22 (3-Model Heterogeneous /swarm Triage -- Deferred): Kept deferred at needs-triage pending L0-5 telemetry (M2 >= 1 undisclosed false-green escape or M5 > 2.0 read_file per clean review post-B2+B7 / > +25% P0/P1 defect density). Locked as wontfix: Tier-1 transcript.jsonl exit-code scan (0% recall on weakened-but-passing tests), unconditional or two-step -U0 git diff/show checks (git log --stat lacks A/M flags, -U0 does not bound new + test additions, adds +1 Trunk turn on ~70%+ TDD waves, misses non-test guard bypasses, 0 / 17,414 undisclosed escapes), skip/xfail regex heuristics, boilerplate section-2 negative attestation (verbatim Living Memory Window bloat), and hard numeric read_file caps.
- 2026-11-22 (Wave 1+2 Sweep -- Closed wontfix): Closed as `wontfix` (deferred-with-watch to [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) `M2`/`M5`). All proposed runtime/protocol interventions (Decisions 1-4) were rejected in triage, leaving [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) as the single active `needs-triage` `L0-5` telemetry watch ticket.
