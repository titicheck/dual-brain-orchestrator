# Bidirectional Execution Subagent Rotation (Archived — Superseded in `v2.0.0`)

**Status:** archived / superseded (`v2.0.0` stateless `Always-New` architecture). Because every `Execution Subagent` dispatch in `v2.0.0` uses a stateless one-shot `SPAWN_NEW` snapshot (`N_max = 1`), multi-dispatch child aging, cross-dispatch `10 KB / N` compaction truncation, `RESUME_EXISTING` delta pages, and rotation heuristics (`Pure q=0`, idle-TTL, child-`CHECKPOINT`) are completely eliminated.

## Historical Rationale (Pre-`v2.0.0`)

- **Pre-`v2.0.0` `RESUME_EXISTING` constraints (`v1.0.0`–`v1.2.1`):** Before `v2.0.0` eliminated `RESUME_EXISTING` altogether, `v1.0.0`–`v1.1.4` kept a bound child across dispatches and rejected wall-clock idle-TTL / unconditional child-`CHECKPOINT` rotation under [ADR-0006](../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md), while `v1.2.0`–`v1.2.1` added clock-free expected-cost rotation (`0.60 * C_old > 1.55 * C_new + 15,000`) per [Ticket 18](../.scratch/orchestrator-v1/issues/18-cache-cold-right-brain-rotation-and-lossless-plan-fidelity.md).
- **Why `v2.0.0` superseded both:** Empirical audit across `75` real `RESUME_EXISTING` dispatches and `15` `SPAWN_NEW` switches proved zero semantic value in post-report child memory (`0/15` memory-loss failures; `76.3%` re-reads anyway), and `sim-vs-sim` backtests showed stateless `Always-New` beating `Pure q=0` (`+$13.45` `1x` / `+$36.37` `2x` vs `v1.1.x`, with `4.27s` spawn boot and `N_max = 1` reserving `~8.8 KB` of `<plan>` retention across compaction).

## Prior Requests

- [Ticket 07: Bidirectional Execution Subagent Lifecycle Rotation on Self-Compaction and Idle TTL](../.scratch/orchestrator-v1/issues/07-bidirectional-execution-subagent-lifecycle-rotation.md) (closed `wontfix`, `2026-11-20`; telemetry recorded in [05-production-telemetry-ttl-and-lifecycle-audit.md](../docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md))
- [Ticket 18: Cache-Cold Execution Subagent Rotation and Lossless Active Plan Fidelity](../.scratch/orchestrator-v1/issues/18-cache-cold-right-brain-rotation-and-lossless-plan-fidelity.md) (resolved `v1.2.0` `Pure q=0`, `2026-11-22`; superseded by `v2.0.0` `Always-New`)
