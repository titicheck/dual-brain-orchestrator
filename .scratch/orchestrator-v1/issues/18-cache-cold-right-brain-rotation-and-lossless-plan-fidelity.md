# 18: Cache-Cold Execution Subagent Rotation and Lossless Active Plan Fidelity

**What to build:** Implement deterministic, clock-free expected-cost right-brain rotation (`Pure q=0`: `0.60 * C_old > 1.55 * C_new + 15,000`) in `v1.2.0` so bloated high-watermark `Execution Subagent` instances rotate cleanly to fresh `SPAWN_NEW` workers while hot post-compaction small children and small-right-brain / large-`LMW` pairs remain on `RESUME_EXISTING`, and track lossless `active_plan.md` externalization (`Option D`) as an `M4`-deferred watch item.

**Blocked by:** None

**Category:** enhancement / architecture

**Status:** resolved

**References:** [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) | [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) | [Ticket 07](07-bidirectional-execution-subagent-lifecycle-rotation.md) | [Ticket 11](11-dual-brain-vs-native-subagent-boundary.md) | [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) | [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) | [Ticket 16](16-soft-cadence-runaway-and-child-self-compaction.md) | [.out-of-scope/bidirectional-execution-subagent-rotation.md](../../../.out-of-scope/bidirectional-execution-subagent-rotation.md)

## Architectural Resolution (Option 1A -- Pure `q=0` Unified Cost Rotation)

Counterfactual replay across `14` bound right-brains and `73` `RESUME_EXISTING` dispatches (`L0-3`, `L0-4`, `S3`, `S9`), followed by a 3-model heterogeneous `/swarm` (`Opus 5.5 High`, `Carbon High`, `Neon XHigh`), rejected idle-time heuristics (`q(t_idle)` lost money on `300-600s` hot hits and added complexity for negligible gain) and converged on **Option 1A (`Pure q=0`)**:

1. **Unified Clock-Free Cost Inequality (`K0 = 12, m = 1x, F = 15,000`):**
   - `C_old = 35,627 + 0.5703 * child_bytes_since_ckpt` (`R^2 = 0.950`, via `< 2 ms` fail-open `O(N)` reverse EOF byte scan from the latest valid `type == "CHECKPOINT"` line inclusive);
   - `C_new = 23,730 + 0.4097 * est_lmw_bytes` (`R^2 = 0.991`, via optional `state.lmw_bytes` with `C1`-preserving incremental updates);
   - Rotate (`RESUME_EXISTING -> SPAWN_NEW`) strictly when `0.60 * C_old > 1.55 * C_new + 15,000` (equivalently `C_old > 2.583 * C_new + 25,000`).
2. **Sim-vs-Sim Empirical Impact (`73` historical dispatches):** Saves `+$12.95` (`1x`, `-11.5%` right-brain spend) / `+$32.52` (`2x`, `-18.3%` right-brain spend), cuts child compactions from `13` to `6` (`-54%`), and reduces `10 KB / N` truncation exposure to `0` observed drift events (`0/9` high-`N` compactions), with zero timestamps and zero changes to `.out-of-scope/`'s idle-TTL exclusion.
3. **All `/swarm` Engineering Safeguards Implemented (`v1.2.0`):**
   - **SKILL.md decoupling (`L55-56`):** Skips redundant `Trunk Session` read-only investigation when `sync` emits `SPAWN_NEW` for already-settled steps (e.g., cost-rotation), authoring a compact self-contained `<plan>` instead;
   - **Concurrent-writer guard:** Cost-rotation is gated strictly on `last_bound_report_step > last_synced_step` so Route 3 wakeups never spawn a second concurrent writer;
   - **Backward-compat & `C1` fast path:** `lmw_bytes` stays optional in `state.json` / `pending_sync`, incremental `RESUME_EXISTING` skips `transcript_full.jsonl`, and second-pass companion hydration runs only when cost-rotation flips `RESUME_EXISTING -> SPAWN_NEW`;
   - **Fail-open child scanner + adapter isolation:** Rejects string-literal `"CHECKPOINT"` matches and invalid `step_index > eof_step_index`, handles `A5` EOF and `> 64 KB` giant lines in `O(N)`, fails open (`RESUME_EXISTING`) on missing/shallow/unreadable child logs, and supports `--subagent-transcript`;
   - **Zero-turn retired worker cleanup:** `bind` emits optional `"retired_subagent_id"` when replacing a different prior bound ID so `Trunk Session` can batch-kill it on the next tool turn.
4. **Option D (`active_plan.md` externalization) Deferred:** Kept deferred to [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md) `M4` (`>= 1` observed post-compaction `<plan>` detail loss in `L0-5+`), because `Pure q=0` cuts child compactions in half and avoids `high-N` truncation without adding per-dispatch file writes.

## Acceptance Criteria

- [x] Resolve Open Triage Decisions 1-4 with counterfactual EV analysis across `L0-3`, `L0-4`, and `0f48e729` (accounting for cold `LMW` prefill and file re-read overhead).
- [x] Update [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md), [.out-of-scope/bidirectional-execution-subagent-rotation.md](../../../.out-of-scope/bidirectional-execution-subagent-rotation.md), `SKILL.md`, `harnesses.md`, and `sync_memory.py` cleanly while preserving [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md).
- [x] Verify contract and regression coverage (`Slice6CostRotationTests` + full `unittest` suite) passing with zero hygiene or link regressions.

## Comments

- 2026-11-22 (Intake): Opened at needs-triage to evaluate deterministic single-transcript cache-cold Execution Subagent rotation (re-examining right-brain context value on pure cache-reload economics without Ticket 07's child-compaction thrashing or sibling-log coupling) alongside lossless active_plan.md recovery under the 10 KB parent-message compaction truncation law.
- 2026-11-22 (Counterfactual Audit, 3-Model /swarm, & Option 1A v1.2.0 Ship -- Resolved): Implemented Option 1A Pure q=0 expected-cost rotation (0.60 * C_old > 1.55 * C_new + 15,000) in sync_memory.py with all /swarm safeguards (SKILL.md settled SPAWN_NEW decoupling, concurrent-writer guard, optional lmw_bytes + C1 fast path + second-pass hydration, fail-open O(N) reverse EOF byte scanner with inclusive CHECKPOINT line sizing, --subagent-transcript override, and conditional bind retired_subagent_id), updated ADR-0002 and .out-of-scope/bidirectional-execution-subagent-rotation.md, and deferred Option D (active_plan.md) to Ticket 13 M4.
