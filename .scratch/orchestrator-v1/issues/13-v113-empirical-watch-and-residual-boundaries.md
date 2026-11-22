# 13: Track v1.1.3 Residual Boundaries and L0-5 Production Telemetry Watch

**What to build:** No code or protocol changes yet. Record the three known theoretical residual boundaries of `orchestrator v1.1.3` alongside empirical `usage-monitor` baselines (`L0-1` through `L0-4`) and the `L0-5` observation criteria so future optimization decisions are strictly driven by production telemetry rather than speculation.

**Blocked by:** None

**Category:** research / telemetry-watch

**Status:** needs-triage

**References:** [01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md) | [03-ab-benchmark-and-kv-cache-telemetry.md](../../../docs/research/03-ab-benchmark-and-kv-cache-telemetry.md) | [05-production-telemetry-ttl-and-lifecycle-audit.md](../../../docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md) | [ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md) | [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) | [Ticket 07](07-bidirectional-execution-subagent-lifecycle-rotation.md) | [Ticket 11](11-dual-brain-vs-native-subagent-boundary.md) | [Ticket 12](12-full-repo-audit-hardening-and-official-alignment.md) | [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) | [Ticket 15](15-tier1-verification-blind-spot-and-trunk-overread.md) | [Ticket 16](16-soft-cadence-runaway-and-child-self-compaction.md) | [Ticket 17](17-debug-error-fidelity-and-two-hop-slice-contracts.md) | [.out-of-scope/host-physical-ux-and-runtime-ceilings.md](../../../.out-of-scope/host-physical-ux-and-runtime-ceilings.md)

## Baseline Anchors (Same `usage-monitor` Dataset, Normalized to `L0-4` `1,074` Steps / `1,603K` Output)

- **`v1.0.0` (`L0-3` pre-opt rate):** `271K` avgCtx (`68.6%` `>200K`), `90.62%` cache hit, `1/183` compactions, `$99.04` Neon / `$80.84` Carbon (`$183.61` Neon at `>200K = 2x`).
- **Official Native — depth-matched (`L0-2` `d89020d4`):** `268K` avgCtx (`65.0%` `>200K`), `89.22%` cache hit (`77.4%` model-switch cache miss), `1/58` compactions, `$100.81` Neon-eq / `$89.00` Carbon (`$181.65` Neon-eq at `>200K = 2x`).
- **Official Native — shallow sliced (`L0-1` `24cd98b2`, `56` `self` + `11` `research` + `25` `egm-*`):** `164K` avgCtx (`32.7%` `>200K`), `90.49%` cache hit (`82.7%` model-switch cache miss), `1/44` compactions, `$63.23` Neon-eq / `$55.43` Carbon (`$95.31` Neon-eq at `>200K = 2x`).
- **`v1.1.1` (`L0-4` `fa0dc277` actual):** `278K` avgCtx (`67.0%` steps / `81.6%` spend `>200K`), `95.02%` cache hit, `1/134` compactions, `$66.19` Neon / `$59.18` Carbon-eq (`$0.2202/1M`, `$0.0413/1k out`, `$120.19` Neon at `>200K = 2x`).
- **`v1.1.3` theoretical projection:**
  - *Expected active-slicing regime (`avgCtx ~165K-195K`, `>200K ~35%-45%`):* `~$47-$54` Neon / `~$42-$48` Carbon (`~$68-$82` Neon at `>200K = 2x`).
  - *Worst-case no-delegation fallback:* `~$62-$65` Neon (still beating `v1.1.1` and `~36%` cheaper than depth-matched Official `L0-2`).

## Three Theoretical Residual Boundaries to Watch in Production (`L0-5+`)

1. **Boundary 1 (Behavioral Activation Rate — Highest Priority):**
   - Ticket `11` (`v1.1.2`) unblocked orthogonal `research` offloading from `Trunk Session` and `depth=2` native child-subagent slicing inside `Execution Subagent` while deliberately avoiding rigid file-count thresholds or bespoke `<plan>` `Parallel:` syntax.
   - *Watch question:* In real multi-wave refactors (`L0-5+`), how often do `Trunk Session` and `Execution Subagent` spontaneously use `research` (preventing `308K-497K` Trunk bloat) and `depth=2` parallel `self` slices (preventing `718`-step / `6`-compaction single-executor accumulation)? Only introduce lightweight delegation nudges if empirical `L0-5+` logs prove spontaneous activation stays too low.
2. **Boundary 2 (Platform Server KV-Cache TTL Physics & Child Compaction Aging):**
   - Server implicit KV-cache transitions from guaranteed-hot (`~99%` `<= 60s`) into opportunistic LRU (`~50%` at `5-10 min`, `~35%-41%` at `10-30 min`) and hard-expires past `30 min` (`3.6%-4.0%`). Cross-`5-min` execution waits still expose `Trunk Session` to cold prefill on wakeup, and Ticket `07` (`wontfix`) leaves multi-compaction child rotation under observation.
   - *Empirical finding on silent keepalive heartbeats (`2026-11-22`):* Forensic inspection of `L0-4` (`fa0dc277`, `53240da8`, `b6f60460`) and all `264` local transcripts confirmed Antigravity sends **zero** silent keepalive packets (`gen_metadata` rows match visible `PLANNER_RESPONSE` steps `1:1`; `>= 300s` hit rate on `SYSTEM_MESSAGE` active waits is `49.1% / 35.5% / 3.6%` vs `51.2% / 41.2% / 4.0%` on pure human-idle `USER_INPUT`, and `12/12` `> 30 min` gaps in `L0-4` hit `0.0%`). Agent-level DIY keepalive heartbeats are **explicitly rejected**: any mid-wait eviction forces a `100%` cold prefill (`20x` cache-read price), waits `> 60-80 min` lose money even at `100%` hit rate, and synthetic turns bloat context toward compaction.
   - *Watch question:* Track whether `research` offloading (`Trunk < 180K`) + `depth=2` slicing sufficiently contain `300s+` cold-reload cost and child self-compaction without reopening Ticket `07`.
3. **Boundary 3 (Micro-Task `[plan review]` Fixed Overhead):**
   - Per [ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md), every execution completion returns through `Trunk Session` `[plan review]` (plus initial `~19.2K` cold prefill on Turn 1), whereas Official Native `Orchestrator` lets unobstructed `1-2`-turn edits answer the user directly from `Hydrogen`.
   - *Watch question:* Confirm this `~$0.03-$0.08` micro-task fixed tax remains negligible in real multi-step engineering sessions and does not warrant breaking unified `[plan review]` governance.

## `L0-5` Production Watch Metrics (Same `usage-monitor` Panel)

1. `avgCtx` and `>200K` step/spend share (compare vs `L0-4` `278K` / `67.0%` steps / `81.6%` spend; target `< 200K` / `< 45%`).
2. Spontaneous delegation counts: `research` calls from `Trunk Session` and `depth=2` `self` slice calls from `Execution Subagent`.
3. Engine invariants: aggregate `cache hit >= 93%`, `schedule = 0`, `manage_task(status) = 0`, `0` Trunk background command leaks, `sync_memory.py` runtime `< 2s`.
4. Effective output unit cost `$/1k out` (compare vs `L0-4` `$0.0413` and Official `L0-1` `$0.0329`) and `>200K = 2x` weighted spend.

### Capability & Rework Falsification Metrics (`M1-M6`, per [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md))

1. **`M1` (Net Rework & Re-Plan Ratio):** `Exit 2 / Total [plan review]` and `%` execution steps spent reverting/fixing prior waves (falsification trigger: `> 25%` rework share erasing `S8a` `+25.8%` buffer, or `Exit 2 > 30%`).
2. **`M2` (Tier-1 Verification Escape Rate):** Audit wave-boundary test diffs (`skip`/`xfail`/`inspect.getsource`/weakened asserts) and child `transcript.jsonl` exit codes vs `<report> §2-§3` (falsification trigger: `>= 1` undisclosed false-green escape -> add transcript exit-code check to Tier 1).
3. **`M3` (`depth=2` Activation vs Merge-Defect Rate):** Track `delegated / eligible DAG waves` alongside cross-slice merge/interface fix rounds (falsification trigger: activation `< 30%` on explicit DAGs, **or** merge rework `> 20%` -> escalate foreman to `orchestrator-tier: pro`).
4. **`M4` (Soft-Constraint Compliance Decay & Cadence Runaway):** Track p50/p95/max tool calls between consecutive `<report>`s (baseline `L0-4` max was `446`), child `CHECKPOINT`s per dispatch, `Re-plan if:` retention post-compaction, and Trigger #1 (`>= 3` identical retries) violations (falsification trigger: p95 `> 45` with drift, or `>= 2x` violation jump past child `CHECKPOINT >= 2` -> reopen [Ticket 07](07-bidirectional-execution-subagent-lifecycle-rotation.md)).
5. **`M5` (Post-Wave Defect Density & Tier-1 Review Discipline):** Count `P0/P1` bugs found by independent Route 3 `code-review`/`egm-*`/`/swarm` per `1k` changed LOC (`> 25%` above `L0-4`/`L0-1` triggers investigation) and Trunk `read_file` count per clean Tier-1 review (`> 2` signals Trunk over-reading).
6. **`M6` (Steering Friction & Recovery Blast Radius):** Track `%` spend discarded on mid-flight `kill + reset` (`> 10%` trigger), stall recoveries per `1k` steps (`>= 2` trigger), and `S1` 1-line side-effect edit latency ratio vs Official.

## Comments

- 2026-11-22 (Intake): Opened at `needs-triage` immediately following `v1.1.3` verification (`2d2b926`) to record theoretical residual boundaries, the empirical fleet-wide no-heartbeat KV-cache audit, and `L0-5` empirical watch metrics without making speculative pre-telemetry changes.
- 2026-11-22 (Ticket 14 Cross-Link): Added capability & rework falsification metrics (`M1-M6`) derived from the 3-model full-corpus audit in [Ticket 14](14-v113-vs-official-vs-v111-full-scenario-evaluation.md) so `L0-5` validates quality alongside quota.
- 2026-11-22 (Capability Triage Intake): Opened actionable capability-optimization tickets [Ticket 15](15-tier1-verification-blind-spot-and-trunk-overread.md), [Ticket 16](16-soft-cadence-runaway-and-child-self-compaction.md), and [Ticket 17](17-debug-error-fidelity-and-two-hop-slice-contracts.md) at `needs-triage`, and documented Dim 10 host physical ceilings in [.out-of-scope/host-physical-ux-and-runtime-ceilings.md](../../../.out-of-scope/host-physical-ux-and-runtime-ceilings.md).
- 2026-11-22 (v1.1.4 Triage Sync): Shipped ultra-surgical v1.1.4 (+335 B / +0 net lines across harnesses.md L74/L98 and execution-protocol.md L52; 0 B SKILL.md, 0 B sync_memory.py), closing Ticket 16 (silent post-compaction protocol re-read) and Ticket 17 (<=15-line failure excerpt ceiling; Decision 2 deferred to M3/M1) while keeping Ticket 15 deferred to M2/M5. L0-5 production validation will therefore run cleanly against v1.1.4 with SKILL.md, B2+B7, depth=2, and sync_memory.py 100% isolated.
