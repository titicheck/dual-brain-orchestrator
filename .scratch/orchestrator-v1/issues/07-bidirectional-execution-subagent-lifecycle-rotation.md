# 07: Bidirectional Execution Subagent Lifecycle Rotation on Self-Compaction and Idle TTL

**What to build:** Expand `Living Memory Window` synchronization from unilateral `Trunk Session`-driven rotation to bidirectional lifecycle awareness so that before reusing a bound `Execution Subagent`, synchronization inspects the bound child's sibling transcript and forces clean `SPAWN_NEW` rotation whenever the child has undergone silent self-compaction or exceeded the pre-TTL idle silence threshold, while preserving hot `RESUME_EXISTING` reuse during rapid, uncompacted follow-ups.

**Blocked by:** None (can start immediately)

**Category:** enhancement

**Status:** wontfix

## ADR Impact

> _Extends and reopens [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) (checkpoint-bounded living memory inheritance), because V1 rotation triggers depend solely on Trunk Session epoch/tier/rewind state and do not inspect the bound Execution Subagent's sibling transcript for child-side self-compaction or KV-cache TTL expiry._

This change remains fully compatible with [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md): rotation detection stays inside the pure Python standard-library synchronization CLI with zero lifecycle hooks, sidecars, or workflow-carrier swaps.

## Problem & Empirical Evidence

Production telemetry from `all_steps_detail.csv` (`13,876` steps across `12` active root sessions / `194` threads, `2026-11-13` to `2026-11-20`) and deep inspection of `L0-3` (`695` CSV steps, `12` dispatches, `479` CSV inference steps on bound `Execution Subagent` `2581ba32`, corresponding to `1,363` raw `transcript.jsonl` records) exposed two lifecycle blind spots in unilateral `Trunk Session`-driven synchronization:

1. **Silent Child Self-Compaction Drift:** While the `L0-3` `Trunk Session` experienced `0` compactions, the bound `Execution Subagent` (`2581ba32`) repeatedly hit Antigravity's `512K` context ceiling and silently self-compacted `3` times (at steps `334`, `647`, and `1008`, dropping from `516.0k–521.9k` down to `26.7k–27.3k`). Because synchronization currently tracks only `Trunk Session` `CHECKPOINT`s, it continued sending incremental deltas assuming the child still held lossless earlier `Living Memory Window` pages.
2. **Post-Compaction Low-Cost Trap:** Gating rotation on "high reload cost" fails for self-compaction because a freshly compacted child collapses to `~27k` tokens (`~$0.04` reload), fooling a cost-based threshold into reusing a lossily summarized instance across chained compactions. Unconditional rotation on any child compaction (`>= 1` `CHECKPOINT`) ensures no new dispatch starts on a compacted child and caps any instance at `<= 1` self-compaction (possible only if a single continuous dispatch itself exceeds `512K`).
3. **300-Second Server Idle TTL Cliff & Stale Dirty-Log Reload Tax:** Regression over `12,856` same-model consecutive steps disproved the hypothesis that context size alone drives cache evictions (`0.9%–1.3%` zero-cache rate across `0–300k+` when `idle_gap <= 15s`). The actual cliff sits at `300s` (`5 min`) of inter-step silence (`1.09%` misses at `0–60s`, jumping to `41.2%–80.0%` around `295–315s` and `76.3%` beyond `10 min`). In `L0-3`, `10` of `22` child zero-cache events occurred after idling `> 300s` at `255k–380k` context (`$0.44–$0.57` each to re-prefill stale build logs). Rotating on idle `> 270s` (a `30s` safety margin before the `300s` cliff) replaces stale-log cold prefills with a clean `Living Memory Window` sync (`~65k–140k`) while also catching up any `Trunk Session` discussions or `Isolated Subagent` reviews that occurred during the pause.
4. **Primary-Source Local Host Transcript Schema Verification (`2026-11-20`):** Direct inspection of local Antigravity `transcript.jsonl` files (including `L0-3` child `2581ba32`) confirmed that `is_compaction_step`, `response_model`, and `subagent_last_step_end_ms` are usage-monitor SQLite export fields, **not** `transcript.jsonl` keys. Native `transcript.jsonl` records child compactions as `type: "CHECKPOINT"` (verified at steps `334`, `647`, `1008` in `2581ba32`, omitting `model`) and stores step timestamps via ISO 8601 UTC `created_at` (alongside file `mtime`).
5. **Counterfactual Backtest Impact:** On `L0-3`, bidirectional rotation (`>= 1` child `CHECKPOINT` or `idle > 270s`) eliminates cross-dispatch chained compactions (`3` compactions on `1` instance -> `<= 1` per instance, eliminating the 3rd compaction entirely) while preserving `6/12` hot `RESUME_EXISTING` dispatches (`97%+` cache hit) and lowering child cost by `~$1.05`. On high-frequency session `0f48e729` (`11` dispatches), `6` rapid micro-edits stay hot while `4` long pauses rotate cleanly (`$2.31` -> `~$2.15`).

## Proposed Behavior

- Before emitting `RESUME_EXISTING` for a bound `Execution Subagent`, synchronization inspects the bound child's deterministic sibling transcript path (derived per [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md)).
- Emit `SPAWN_NEW` (and export full current-epoch `Living Memory Window` pages) if the folded child transcript contains any `type == "CHECKPOINT"` record (unconditional compaction cutover).
- Emit `SPAWN_NEW` if elapsed idle silence since the bound child's latest activity exceeds the pre-TTL threshold (proposed default `270` seconds).
- Otherwise preserve `RESUME_EXISTING` and incremental delta export, keeping short-interval follow-ups on hot KV cache.
- Preserve existing retirement quarantine (`retired_subagent_max_step`) and zero-side-effect pre-mutation validation invariants from [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md).

## Open Triage Decisions (Resolve Before Moving to ready-for-agent)

1. **Idle-time measurement source:** Use `created_at` on the final folded child record vs sibling `transcript.jsonl` `st_mtime` vs `max(created_at, st_mtime)`, plus deterministic clock injection for `Seam 1` replay tests.
2. **Missing, empty, or temporarily unreadable sibling child transcript behavior:** Fail-open (`RESUME_EXISTING`), fail-closed (`SPAWN_NEW`), or hard error (exit `2`) when the bound child log is absent on disk.
3. **CLI surface:** Derive sibling transcript path implicitly from `--transcript` parent and `bound_subagent_id` vs add optional test override flags (`--now`, `--idle-ttl-seconds`, `--subagent-transcript`), while ensuring non-Antigravity future adapters remain decoupled.
4. **JSON output compatibility:** Keep the strict 8-field `sync` stdout schema vs add an optional diagnostic `rotation_reason` field.

## Acceptance Criteria

- [ ] Finalize open triage decisions and update [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) and [spec.md](../spec.md) to document bidirectional `Execution Subagent` rotation boundaries.
- [ ] Detect folded `type == "CHECKPOINT"` records in the bound `Execution Subagent`'s sibling transcript and unconditionally emit `SPAWN_NEW` with full current-epoch `Living Memory Window` pages.
- [ ] Detect idle silence exceeding the configured pre-TTL threshold (default `270s`) on the bound `Execution Subagent` and emit `SPAWN_NEW`, while preserving `RESUME_EXISTING` when uncompacted and within the idle window.
- [ ] Quarantine rotated-out child IDs cleanly via existing retirement rules without mutating state before validation or breaking Turn-1 / rewind / tier-change invariants.
- [ ] Cover child compaction rotation, idle-TTL rotation, hot-path `RESUME_EXISTING` retention, missing/corrupt child transcript edge cases, and deterministic clock replay in the `Seam 1` automated test suite, and confirm `py -3 -m unittest discover -s tests -v` passes with zero CJK or link hygiene regressions.

## Comments

- 2026-11-20: Opened from full-dataset telemetry audit (`all_steps_detail.csv`, 13,876 steps) and direct local host `transcript.jsonl` schema verification on `L0-3` child `2581ba32` (confirming `type == "CHECKPOINT"` at steps `334`, `647`, `1008` and ISO 8601 `created_at` / file `mtime`).

- 2026-11-20 (Triage — Closed `wontfix`):

  > *This was generated by AI during triage.*

  Closed as `wontfix` and recorded in [.out-of-scope/bidirectional-execution-subagent-rotation.md](../../../.out-of-scope/bidirectional-execution-subagent-rotation.md) after frame-level verification of `2581ba32` and Pareto cost/benefit review:
  1. `RESUME_EXISTING` already exports incremental `Living Memory Window` deltas, so uncompacted idle children do not lose new `Trunk Session` dialogue.
  2. Direct `2581ba32` frame inspection confirmed immediate post-compaction steps (`335`, `648`, `1009`) had `cache_read_tokens = 0`, whereas subsequent `< 300s` `RESUME_EXISTING` dispatches (`steps 395/396` `79.6%`, `855/856` `98.6%`, and `967/968` `99.2%`—noting `step 967` preceded `CHECKPOINT 1008`) hit hot KV cache cleanly (`~$0.03–$0.04`), while unconditional rotation on child `CHECKPOINT` destroys hot caches and triggers cold-start thrashing when `Trunk Session` holds a large `Living Memory Window`.
  3. Cold-reloading the four long-idle events (`steps 1144, 1277, 1299, 1340`) yields a `$1.68` counterfactual delta before file re-read overhead (`~$1.05` prefill-only savings, `~$1.0–$1.5` or `~2%` estimated net of `$57.01` total; `$0.16` / `0.7%` on `0f48e729`), which does not justify breaking `sync_memory.py`'s deterministic, clock-free, single-transcript boundary or introducing state-machine coupling against [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md). Routine `Trunk Session` compaction and new-window epochs already provide sufficient Epoch-GC for stale child logs, and a post-Ticket-08 telemetry watch condition is recorded in `.out-of-scope/`.
- 2026-11-22 (`v1.2.0` Cross-Note): [Ticket 18](18-cache-cold-right-brain-rotation-and-lossless-plan-fidelity.md) (`v1.2.0`) resolved the `.out-of-scope/` watch via clock-free `Pure q=0` expected-cost rotation (`0.60 * C_old > 1.55 * C_new + 15,000`), while wall-clock idle-TTL and unconditional child-`CHECKPOINT` rotation remain `wontfix`.
