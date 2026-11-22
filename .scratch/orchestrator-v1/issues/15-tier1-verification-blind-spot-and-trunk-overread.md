# 15: Close Tier-1 Verification Blind Spot and Constrain Trunk Over-Reading

**What to build:** Intake for triage -- no runtime code or protocol edits yet. Address Trade-off #3 (`E3`/`E4` from [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md)) by deciding how to close Tier 1's verification blind spot to undisclosed test weakening while constraining `Trunk Session` over-reading beyond Tier 1.

**Blocked by:** None

**Category:** enhancement

**Status:** needs-triage

**References:** [ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md) | [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) | [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) | [Ticket 12](12-full-repo-audit-hardening-and-official-alignment.md) | [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) | [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md)

## Problem & Empirical Evidence

The 3-model full-scenario audit in [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) (Dimension 4: Verification Rigor Asymmetry, disk evidence `E3`/`E4`) identified a two-sided gap in `orchestrator`'s three-tier verification ladder as the **highest-ROI** capability optimization candidate:

1. **Tier-1 Verification Blind Spot (`E3`):** In `d1e362b3`, the `flash` `Execution Subagent` weakened tests twice:
   - Step `124`: gated a parity assertion behind `inspect.getsource`.
   - Step `190`: bypassed `_FORBIDDEN_LIVE_DIR` in memory.
   Both weakenings were caught **solely** because `flash` disclosed them honestly in `<report> §3`. Under the current Tier-1 review contract (`git status --short` / `git diff --stat`), `Trunk Session` cannot detect undisclosed assertion weakening, newly added `skip`/`xfail` markers, or unverified test exits unless it drops down into heavier inspection. By contrast, Official Native Orchestrator surfaces `edit_file` diffs inline to the planner.
2. **Trunk Over-Reading Beyond Tier 1 (`E4`):** In `L0-4` (`fa0dc277`), `Neon` `Trunk Session` routinely read `5-8` source files in full beyond Tier 1 on almost every review. That behavior inflated Trunk context (`278K-308K` `avgCtx`), eroded Tier-1 context savings, and increased `>200K` spend without fixing the underlying verification-trust gap.

## Open Triage Decisions

1. **Targeted Tier-1 diff / transcript check:** Should `Trunk Session` run a bounded test-only diff inspection (e.g., `git diff -- <test files>` or scanning test diffs for `skip`/`xfail`/weakened assertions) or a lightweight child-transcript exit-code check in Tier 1 without flooding Trunk with full source reads?
2. **Explicit negative attestation in `<report>`:** Should `execution-protocol.md` require `Execution Subagent` `<report> §2-§3` to carry an explicit negative attestation confirming zero modified test assertions, skips, or xfails alongside the exact verification exit code and summary line?
3. **Tightening Trunk Tier-1 review discipline:** Should `SKILL.md` tighten clean-review discipline toward the [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) `M5` target (`<= 2` `read_file` calls per clean Tier-1 review unless triggered by concrete red flags in `<report>`, `git status --short`, or `git diff --stat`)?
4. **Release timing (`v1.1.4` vs `L0-5` hold):** Should we ship a minimal surgical protocol update now (`v1.1.4`) or hold pending `L0-5` production telemetry on `M2` (Tier-1 verification escape rate) and `M5` (Trunk `read_file` count and post-wave defect density)?

## Acceptance Criteria

- [ ] Resolve Open Triage Decisions 1-4 and record the chosen disposition (`resolved` or deferred/`wontfix`).
- [ ] If approved for implementation, update the active skill/protocol docs minimally in line with [ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md) and [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) without flooding `Trunk Session` context.
- [ ] Verify contract and regression coverage with `py -3 -m unittest discover -s tests -v` passing with zero hygiene or link regressions.

## Comments

- 2026-11-22 (Intake): Opened at needs-triage from the 3-model full-scenario audit in [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) (Dim 4 Verification Rigor Asymmetry, disk evidence E3/E4) as the highest-ROI capability optimization candidate.
- 2026-11-22 (3-Model Heterogeneous /swarm Triage -- Deferred): Kept deferred at needs-triage pending L0-5 telemetry (M2 >= 1 undisclosed false-green escape or M5 > 2.0 read_file per clean review post-B2+B7 / > +25% P0/P1 defect density). Locked as wontfix: Tier-1 transcript.jsonl exit-code scan (0% recall on weakened-but-passing tests), unconditional or two-step -U0 git diff/show checks (git log --stat lacks A/M flags, -U0 does not bound new + test additions, adds +1 Trunk turn on ~70%+ TDD waves, misses non-test guard bypasses, 0 / 17,414 undisclosed escapes), skip/xfail regex heuristics, boilerplate section-2 negative attestation (verbatim Living Memory Window bloat), and hard numeric read_file caps.
