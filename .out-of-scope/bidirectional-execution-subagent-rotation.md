# Bidirectional Execution Subagent Rotation

`orchestrator` does not automatically rotate its bound `Execution Subagent` based on child-side self-compaction (`CHECKPOINT`) or inter-dispatch idle TTL timers; `SPAWN_NEW` rotation remains unilaterally driven by `Trunk Session` boundaries (`tier != bound_tier`, trunk `checkpoint_step`, trunk rewind digest/step mismatch, or post-crash `reset`) per [ADR-0002](../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md).

## Why this is out of scope

- **Incremental memory sync already covers uncompacted idle periods:** `RESUME_EXISTING` already exports `(last_synced_step .. max_folded_step]` delta pages of the `Living Memory Window`, so idling across the 300s KV-cache cliff does not cause memory drift on an uncompacted child.
- **Hot-path child compaction rotation causes negative ROI and high-watermark thrashing:** Direct frame-level inspection of `L0-3` child `2581ba32` (`transcript.jsonl`) proved that while immediate post-compaction steps (`335`, `648`, `1009`) had `cache_read_tokens = 0`, subsequent `< 300s` `RESUME_EXISTING` dispatches (`steps 395/396` `79.6%`, `855/856` `98.6%`, and `967/968` `99.2%`—noting `step 967` preceded `CHECKPOINT 1008`) hit hot KV cache cleanly (`~$0.03–$0.04` per step). Rotating unconditionally on child compaction destroys hot caches and—when `Trunk Session` carries a large `Living Memory Window` (`44.1 KB` median / `96.3 KB` max measured in [02-exploratory-notes-and-host-probes.md](../docs/research/02-exploratory-notes-and-host-probes.md); `~100k–140k` tokens in `L0-3`)—creates a cold-start compaction thrashing loop.
- **Disproportionate cost/complexity ratio (Pareto boundary):** Across the `14.4`-hour `L0-3` session (`$57.01` total), cold-reloading the four long-idle events (`steps 1144, 1277, 1299, 1340` at `154k`, `322k`, `344k`, `385k`) versus fresh spawns yields a `$1.68` (`2.95%`) gross counterfactual delta (`~$1.05` prefill-only savings, or `~$1.0–$1.5` / `~2%` estimated net after file re-read overhead; `$0.16` / `0.7%` on `0f48e729`). Adding sibling child-transcript parsing, host-directory coupling, wall-clock non-determinism, and missing/corrupt child-log edge cases to `sync_memory.py` violates the V1 Pareto boundary in [ADR-0006](../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) and creates conflict risk with long-running delegated tasks.
- **Existing Epoch-GC covers routine hygiene:** Following host-managed `Trunk Session` compaction and new-window boundaries already provides clean Epoch-GC for routine stale-log accumulation, while a single oversized continuous dispatch exceeding `512K` remains subject to host compaction regardless of rotation policy.

## Re-evaluation Watch Condition

- Wall-clock idle-TTL rotation remains permanently out of scope.
- After [Ticket 08](../.scratch/orchestrator-v1/issues/08-heavy-and-background-execution-delegation-gate.md) shifts heavy command logs off `Trunk Session` onto `Execution Subagent`, monitor production telemetry for concrete evidence of multi-compaction constraint amnesia or materially elevated dirty-log reload cost before ever reconsidering deterministic, clock-free child-`CHECKPOINT` awareness.

## Prior requests

- [Ticket 07: Bidirectional Execution Subagent Lifecycle Rotation on Self-Compaction and Idle TTL](../.scratch/orchestrator-v1/issues/07-bidirectional-execution-subagent-lifecycle-rotation.md) (closed `wontfix`, `2026-11-20`; telemetry recorded in [05-production-telemetry-ttl-and-lifecycle-audit.md](../docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md))
