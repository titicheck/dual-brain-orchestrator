# Production Telemetry, KV-Cache TTL Physics, and Subagent Lifecycle Audit

Empirical production audit conducted on `2026-11-20` against an exported `antigravity-usage-monitor` multi-session telemetry dataset (`all_steps_detail.csv`, covering `13,876` inference and compaction steps across `12` active root sessions / `14` total root sessions and `194` active threads from `2026-11-13` to `2026-11-20`, totaling `2.777B` tokens, `$919.18` list-price cost, and `$3,833.59` cache savings) paired with direct local Antigravity `transcript.jsonl` schema inspection on `2026-11-20`.

> **Scope & Status Note:** Sections 1 through 5 record observed empirical measurements and verified host schema facts. Section 6 records the `2026-11-20` triage resolution for [Ticket 07](../../.scratch/orchestrator-v1/issues/07-bidirectional-execution-subagent-lifecycle-rotation.md) (closed `wontfix` and recorded in [bidirectional-execution-subagent-rotation.md](../../.out-of-scope/bidirectional-execution-subagent-rotation.md)) and [Ticket 08](../../.scratch/orchestrator-v1/issues/08-heavy-and-background-execution-delegation-gate.md) (converged on a minimal Official Part 2.4 dual-session adaptation at `Status: ready-for-agent`, implementation deferred). External commercial subscription billing multipliers noted for context are volatile host observations outside `orchestrator`'s core contract.

---

## 1. Server KV-Cache Physics — The 300-Second Idle TTL Cliff

Regression across `12,856` same-model consecutive non-compaction steps (`12,801` in the Gemini family), stripping Step-1 cold starts, compaction resets, and model/effort-tier switches, isolates inter-step silence—not context size—as the primary driver of server KV-cache eviction:

- **Context size alone does not trigger cache eviction:** When `idle_gap_sec <= 15s`, zero-cache (`cache_read_tokens = 0`) rates across `0–100k` (`3,139` steps), `100k–200k` (`3,761` steps), `200k–300k` (`2,715` steps), and `> 300k` (`2,430` steps) stayed flat at `1.3%`, `0.9%`, `1.1%`, and `0.9%` respectively (and `3.1%` across `65` steps at `> 300k` within `15–60s`).
- **Hard cliff at `300s` (`5 min`) inter-step silence:** The zero-cache miss rate is `1.09%` (`134 / 12,329`) for `0–60s`, rises gradually to `8.4%–20.0%` at `1–4.8 min`, jumps sharply to `41.2%–80.0%` across the `295–315s` boundary, reaches `61.5%` at `6–10 min`, and hits `76.3%` beyond `10 min` (`95.0%` on `neon-4-high`, `19/20` misses).

### Dataset-Wide Cache-Miss Decomposition (`13,426` Post-Step-1 Steps; `826` Zero-Cache Events)

| Cause Category | Sample Steps | Zero-Cache Events | Miss Rate | Uncached Input Burned | Notes |
|---|---|---|---|---|---|
| **Compaction resets** | `256` | `256` | `100.0%` | `6.65M` (`$14.24` list) | Low per-event cost because context shrinks back down |
| **Same-session model/effort-tier switches** | `314` | `210` (`223` severe mismatch) | `66.88%` (`71.02%` severe) | `56.16M` (`$111.09` list) | `298` steps from native Orchestrator hand-offs plus `16` non-native steps including `9ef431b6` effort-tier variant-switch probes (`neon-4-low -> neon-4 -> neon-4-high`) |
| **Same-model continuous steps** | `12,856` | `360` | `2.80%` | `79.09M` | Concentrated at `> 300s` cross-turn pauses |

---

## 2. Model Latency, Throughput, Compaction Ceiling, and Host Schema Verification

### Non-Compaction Production Metrics (`13,620` Steps)

| Model Identifier | Steps | TTFT (Mean / Median) | TPS (Mean / Median) | Cache Hit Rate | Observed Notes |
|---|---|---|---|---|---|
| `worker-agy-hydrogen` | `9,697` | `6.04s / 4.47s` | `103.1 / 94.5` | `90.90%` | Native Orchestrator worker pool |
| `orchestrator-carbon` | `2,483` | `15.85s / 11.28s` | `40.0 / 37.4` | `84.96%` | Native Orchestrator planner (`3.0x` pool weight reported) |
| `hydrogen-4-high` | `908` | `5.69s / 4.59s` | `89.6 / 71.4` | `92.00%` | `orchestrator-tier: flash` resolved target |
| `neon-4-high` | `299` | `9.06s / 7.94s` | `59.6 / 53.8` | `84.54%` | `Trunk Session` baseline in `L0-3` |
| `hydrogen-4-xhigh` | `94` | `5.34s / 5.24s` | `110.2 / 107.1` | `89.75%` | `orchestrator-tier: pro` resolved target |
| `carbon-4-high` | `37` | `12.56s / 9.31s` | `39.5 / 38.5` | `75.65%` | Standalone high-context fallback |
| `opus-5.5-high` | `35` | `9.29s / 6.45s` | — | `82.91%` | Third-party Claude pool |
| `neon-4-xhigh` | `28` | `7.42s / 6.65s` | `61.5 / 56.6` | `90.63%` | Mean `640` thought tokens; `0.0%` misses across `26` steps `<= 15s` |
| `sonnet-5.5` | `22` | `5.29s / 3.34s` | — | `88.21%` | Third-party Claude pool |

*Note: The 9 primary models listed sum to `13,603` steps; `17` steps across minor/auxiliary models are omitted from this summary table.*

### `MODEL_PLACEHOLDER_M530` & `512K` Compaction Ceiling

Cross-referencing `model_key` against `response_model` confirmed that the `6` unmapped `MODEL_PLACEHOLDER_M530` calls (`3` in `L0-2`, `3` in `L0-3`) share the exact `model_key` of `hydrogen-4-high` (`858` normal steps) and correspond exclusively to `is_compaction_step = True` child compaction calls where the server omits `response_model`. Compaction trigger sizes also tracked Antigravity's context window expansion from `257k–284k` (`256K` cap in `L0-1`, `184` compactions) to `516k–548k` (`512K` cap in late `L0-2` and `L0-3`).

### Primary-Source `transcript.jsonl` Schema Verification (`2026-11-20`)

Direct inspection of `30` recent local Antigravity `transcript.jsonl` files—including `L0-3` bound `Execution Subagent` `2581ba32` (`1,363` records)—established the exact host log contract:

- **Native JSONL keys:** `['cache_read_tokens', 'content', 'created_at', 'error', 'input_tokens', 'media', 'model', 'output_tokens', 'source', 'status', 'step_index', 'thinking', 'tool_calls', 'truncated_fields', 'type']`.
- **SQLite export fields absent on disk:** Usage-monitor fields (`is_compaction_step`, `response_model`, `idle_gap_sec`, `subagent_last_step_end_ms`) do **not** exist in native `transcript.jsonl`.
- **Child compaction representation:** Native child compactions are recorded as `type == "CHECKPOINT"` omitting `model` (verified at `step_index` `334`, `647`, and `1008` in `2581ba32`; `8` of `30` inspected local subagents contained `CHECKPOINT` records).
- **Timestamps:** Each step carries ISO 8601 UTC `created_at` (e.g., final step `1362` of `2581ba32` at `2026-11-20T06:10:03Z` vs file `mtime` `2026-11-20T06:10:09.107953+00:00`), and Antigravity's `manage_subagents(Action="list")` also exposes `lastStepTime` alongside `state`.

---

## 3. Native Orchestrator vs. Custom `orchestrator` Production Comparison

| Session | Mode | Steps | Subagents | Compactions | Runtime Anomalies | Total Tokens | List Cost / Sub-Eq | Sub-Eq per 1M |
|---|---|---|---|---|---|---|---|---|
| `L0-1` | Native Orchestrator (`256K` era) | `8,138` | `92` | `184` | `0` | `1,356.02M` | `$424.61 / $655.04` | `$0.483 / 1M` |
| `L0-2` | Native-dominant | `3,751` | `39` | `64` | `0` | `1,016.24M` | `$317.86 / $475.56` | `$0.468 / 1M` |
| `Orchestrator-skill` | Native Orchestrator | `775` | `34` | `4` (trunk) | `4` (incl. `632.8s` timeout) | `163.05M` | `$80.85 / $154.18` | `$0.946 / 1M` |
| `L0-3` | Custom `orchestrator` | `695` | `4` (`1` bound + `3` read-only audits) | `0` trunk / `3` child | `0` | `182.20M` | `$56.72 / $57.01` | `$0.313 / 1M` |
| `0f48e729` | Custom `orchestrator` | `254` | `9` | `0` | `0` | `36.46M` | `$22.53 / $22.53` | `$0.618 / 1M` |

*Billing caveat:* Subscription-equivalent figures reflect community-reported `3.0x` pool weighting on `Carbon` versus `1.0x` on `Neon` and `Hydrogen`. Even on an apples-to-apples `1.0x` `Neon` substitution (`~$99.33` native vs `$56.72` custom), `L0-3` saved `~42.9%` strictly from architectural isolation.

### Three Structural Native Bottlenecks Exposed by Telemetry

1. **Single-Thread Dual-Bucket Ping-Pong Expiry:** Model hand-offs within `< 60s` achieved `93.92%` cache hit (`8` steps, `0` misses), proving separate KV buckets per model. However, in `170 / 234` (`72.6%`) same-epoch hand-offs the inactive model's bucket sat idle `> 300s`, causing `71.71%` misses on `Hydrogen -> Carbon` (`152` switches, `29.54M` uncached) and `62.33%` on `Carbon -> Hydrogen` (`146` switches, `23.06M` uncached).
2. **Default `inherit` Subagent Recursion:** In `L0-1` and `L0-2`, subagents spawned from native Orchestrator inherited dual-model orchestrator behavior (`278` child `orchestrator-carbon` steps, `7,015` child `worker-agy-hydrogen` steps, `172` child compactions). Custom `orchestrator`'s `step 0` guard and static `flash` lock kept `L0-3` to `4` clean subagents.
3. **Long-Stream Fragility & Micro-Task Tradeoff:** All `4` streaming timeouts/disconnects occurred on native `orchestrator-carbon` (`37.4 tok/s` median). Conversely, on `1–2`-turn trivial runs (`~19.2k` / `19,183` tokens child cold prefill on `72e8ba49`, established in [03-ab-benchmark-and-kv-cache-telemetry.md](03-ab-benchmark-and-kv-cache-telemetry.md)) and `< 50`-step micro-tasks (`Ledger` `36` vs `57` steps in `all_steps_detail.csv`, where child `2581ba32` starts with `~26.7k` base overhead), native same-thread hand-offs avoid the fixed child cold-start overhead plus `sync_memory.py`.

---

## 4. Two High-Impact Operational Failure Modes Observed in `L0-3`

### Failure Mode A — Bound `Execution Subagent` Silent Self-Compaction & Stale-Log Idle Reloads

Tracked in [Ticket 07](../../.scratch/orchestrator-v1/issues/07-bidirectional-execution-subagent-lifecycle-rotation.md):

- Across `479` `all_steps_detail.csv` inference steps on bound `Execution Subagent` `2581ba32`, the child self-compacted `3` times (at raw `transcript.jsonl` `step_index` values `334`, `647`, and `1008` out of `1,363` records, collapsing `516.0k–521.9k -> 26.7k–27.3k`) while `Trunk Session` had `0` compactions, leaving incremental delta sync unaware of lossy child summarization.
- `10` of `22` child zero-cache misses occurred after `> 300s` silence at `255k–380k` context (`$0.44–$0.57` each to re-prefill stale build logs).
- **Post-compaction low-cost trap:** After self-compacting, child context shrinks to `~27k` (`~$0.04` reload), so cost-threshold rotation heuristics fail to evict a lossily compacted child.

### Failure Mode B — `Trunk Session` Owning Long-Running Background Commands

Tracked in [Ticket 08](../../.scratch/orchestrator-v1/issues/08-heavy-and-background-execution-delegation-gate.md):

- Under V1's literal adoption of single-thread Official Part 2.4 (`observational run_command builds, tests, or queries`) and Part 7 (`run observational commands if needed to check`), `Trunk Session` launched `run_r_chain_36y_offline_bench.py` directly (using `WaitMsBeforeAsync: 500`, under Antigravity's `10000 ms` synchronous cap) inside four Route 1 `[plan review]` turns—`Trunk Session` steps `268` (`00:57:15Z`, matching child `1276`), `318` (`03:03:27Z`, matching child `1298`), `347..351` (`04:40:26Z` `git show --stat d7b2fa1` after child `1339`, then `04:40:59Z` benchmark launch at `351`), and `378` (`06:10:03Z`, matching child `1362`)—plus memory probes (`diag_m202610.py`, `diag_4m_pid_rss.py`) in separate post-failure turns (`steps 273, 326, 331`).
- Antigravity delivers completion/status wakeups for a background OS process only to the session that started it. Between `04:31` and `12:40 +08:00`, these launches produced `7` post-TTL (`> 300s`) cold-cache `Trunk Session` wakeups (including benchmark completion/failure wakeups after `~56m`, `~63m`, and `~78m`), hitting `cache_read_tokens = 0` every time (`$1.09–$1.67` each, `$9.83` total = `35.6%` of trunk spend) and appending `~90k` polling/tool tokens into `ctx_tool_results_tokens` (`177.8k` final, `41.8%` of `425.3k` trunk context).
- **Same-session natural control (`2026-11-19T23:37Z` to `2026-11-20T00:57Z`, i.e., `07:37–08:57 +08:00`, child `2581ba32` steps `1222..1276`, prior to trunk step `268`):** An `80`-minute series of `~15-min` `pytest` suites and debugging edits (`task-1222` through `task-1268`) owned by `Execution Subagent`—running under completely unmodified `execution-protocol.md` and `harnesses.md`—produced `0` intermediate `Trunk Session` wakeups (`$0.00` mid-run trunk cost) and cost `$0.73` across `5` child checks (`98.5%–99.2%` cache hit, `92%` cheaper, with all logs quarantined in child context).

---

## 5. Explicit Non-Goals Confirmed by Telemetry

- **Synchronizing parallel `Isolated Subagent` async wakeups:** In `L0-3`, staggered dual code-review wakeup cost delta was `$0.83` in exchange for real wall-clock parallelism; adding synchronization barriers increases state-machine fragility.
- **Constraining external read-only audit subagent prompts/budgets:** `L0-3`'s `3` audit subagents totaled `$4.61` (`8.1%` of session spend), and `0f48e729`'s `7` EGM reviewers totaled `$1.54` (`6.8%`). Keeping `Isolated Subagents` orthogonal preserves zero-coupling compatibility per [ADR-0004](../adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md).

---

## 6. Triage Resolution & Counterfactual Backtests (2026-11-20)

The table below preserves the counterfactual backtest comparison evaluated during triage alongside the converged `2026-11-20` decisions for [Ticket 07](../../.scratch/orchestrator-v1/issues/07-bidirectional-execution-subagent-lifecycle-rotation.md) and [Ticket 08](../../.scratch/orchestrator-v1/issues/08-heavy-and-background-execution-delegation-gate.md):

| Lifecycle Strategy | `L0-3` Child Spend (`12` Dispatches) | `L0-3` Child Compactions | `0f48e729` Child Spend (`11` Dispatches) | Operational Tradeoff |
|---|---|---|---|---|
| **Current permanent reuse** | `$24.50` (actual) | `3` (chained) | `$2.31` (actual) | Hot follow-ups stay fast; `Trunk Session` compaction/new-window epochs provide routine Epoch-GC |
| **Unconditional always-new** | `$22.36–$24.37` | `1` | `$2.58` | Zero chained compaction, but doubles cold-start tax on rapid micro-edits |
| **Evaluated conditional (`CHECKPOINT` or `idle > 270s`)** | `$22.82` | `1` | `~$2.15` | Rejected during triage (`wontfix`); `$1.68` (`2.95%`) gross delta (`~$1.05` prefill-only, `~$1.0–$1.5` net after re-reads) does not justify breaking `sync_memory.py` simplicity |

### Triage Decisions (`2026-11-20`)

- **Ticket 07 (`wontfix`):** Direct frame-level audit of `2581ba32` (`transcript.jsonl`) established that immediate post-compaction steps (`335`, `648`, `1009`) had `cache_read_tokens = 0` (matching §1's `100.0%` compaction reset rate), whereas subsequent `< 300s` `RESUME_EXISTING` dispatches (`steps 395/396` `79.6%`, `855/856` `98.6%`, and `967/968` `99.2%`—noting `step 967` preceded `CHECKPOINT 1008`) hit hot KV cache cleanly, while unconditional rotation on child compaction destroys hot caches and risks high-watermark thrashing. Furthermore, `RESUME_EXISTING` already exports incremental `Living Memory Window` deltas (invalidating the uncompacted idle-drift premise), and cold-reloading the four long-idle events (`steps 1144, 1277, 1299, 1340`) yields a `$1.68` (`2.95%`) gross counterfactual delta before file re-read overhead (`~$1.05` prefill-only savings, `~$1.0–$1.5` / `~2%` estimated net of `$57.01` on `L0-3`; `$0.16` / `0.7%` on `0f48e729`), failing the [ADR-0006](../adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md) Pareto boundary. Recorded permanently in [bidirectional-execution-subagent-rotation.md](../../.out-of-scope/bidirectional-execution-subagent-rotation.md), alongside a post-Ticket-08 telemetry watch condition for multi-compaction constraint amnesia or materially elevated dirty-log reload cost before ever reconsidering deterministic, clock-free child-`CHECKPOINT` awareness.
- **Ticket 08 (`ready-for-agent`, implementation deferred):** Aligned to [01-official-orchestrator-system.md](01-official-orchestrator-system.md) and formalized as the fourth dual-session physical adaptation in [ADR-0007](../adr/0007-session-bound-command-ownership.md): pure symmetric invariant (no session yields control while a command it started is still running) leaving Official Part 2.1 (`Direct Answer Gate`), `README.md` / `README.zh-CN.md` snippets, `ADR-0004`, and `sync_memory.py` untouched, isolating Antigravity's `10s` synchronous-wait consequence to `harnesses.md`, and adding the three-tier `[plan review]` verification ladder (with optional `Isolated Subagent` independent long verification). Citing verified `L0-3` Route 1 `[plan review]` launches at `steps 268, 318, 347..351, 378` (plus `steps 273, 326, 331` probes) and the untouched-protocol control (`23:37Z–00:57Z`); implementation is deferred to Ticket 08.
