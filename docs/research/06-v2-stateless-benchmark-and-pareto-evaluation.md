# `v2.0.x` Stateless `Always-New` Benchmark and Pareto Evaluation

This research report consolidates the multi-session telemetry corpus, empirical switch-physics measurements, right-brain memory-value probes, counterfactual `sim-vs-sim` backtests, cross-model scaling laws, honest trade-offs, and `L0-5` validation criteria supporting `orchestrator v2.0.0` / `v2.0.1` (`Always-New` stateless `Execution Subagent`).

> **Epistemic Tagging Legend:**
> - **`[Measured Production Telemetry]`**: Direct measurements from exported `usage-monitor` SQLite/JSON telemetry and on-disk `transcript.jsonl` logs.
> - **`[Sim-vs-Sim Counterfactual Backtest]`**: Strictly controlled apples-to-apples simulation across historical dispatches (`v1.1.x` `SimBase` vs `v1.2.1` `Pure q=0` vs `v2.0.0` `Always-New`), eliminating raw-vs-simulated baseline bias.
> - **`[Pending L0-5 Live Validation]`**: Production telemetry targets and objective rollback triggers to be verified in the next multi-hour production engineering session (`L0-5`).

---

## 1. Corpus Anchor & Session Glossary `[Measured Production Telemetry]`

All empirical baselines below come from a single exported `antigravity-usage-monitor` corpus (`2026-11-22`) paired with direct `transcript.jsonl` inspection:

- **Full Corpus Totals:** `281` trajectories, `17,414` steps (`17,137` inference steps + `277` compactions), `3,566.91M` total tokens (`32.14M` output tokens), `90.12%` aggregate cache hit rate, `$1,195.51` actual list spend (`$1,324.72` `Neon 1x`-aligned | `$1,123.90` `Carbon`-aligned | `$1,712.37` `Carbon 3.0x` `Sub-3x` | `$2,181.33` `Neon >200K = 2x` `N-2x`) across `17` active root sessions mapped to scenarios `S1`–`S9`.
- **Anonymized Multi-Hour Production Sessions (`L0-1`..`L0-5`):**
  - `L0-1`: Official Native Orchestrator (`256K` era, shallow sliced: `56` `self` + `11` `research` + `25` `egm-*` subagents, `8,138` steps, `161.5K` avgCtx).
  - `L0-2`: Official Native Orchestrator (`512K` era, depth-matched monolith, `3,751` steps, `263.6K` avgCtx).
  - `L0-3`: Early `orchestrator v1.0.0` production session (`695`–`715` steps, `271K` avgCtx pre-`ADR-0007`).
  - `L0-4`: `orchestrator v1.1.1` production session (`1,074` normalized steps / `1,603K` output, `278K` avgCtx, `95.02%` cache hit, `$66.19` Neon vs `$100.81` depth-matched Official `L0-2`).
  - `L0-5`: Upcoming multi-hour live production benchmark `[Pending L0-5 Live Validation]` for `v2.0.x`.

---

## 2. Empirical Official Native Switch Physics `[Measured Production Telemetry]`

Auditing `314` real same-thread planner/executor switches across `5` Official Native Orchestrator sessions established why keeping planning and execution in separate sessions outperforms same-thread model hot-swapping:

| Metric | Measured Official Native (`314` Real Switches) | Measured `orchestrator` (`L0-4` / Production) |
|---|---|---|
| **Cross-Model Switch Cache Miss** | `75.1%` uncached on `EXEC -> PLAN` (`mean 256.6K`); `69.7%` uncached on `PLAN -> EXEC` (`mean 214.5K`) | `Trunk Session` stays warm on one model family (`95.02%` session hit rate on `L0-4`) |
| **Rapid `<180s` Switch Miss (`n = 44`)** | `25.1%–26.5%` uncached even below TTL (`S5` short session hit `4/5` zero-cache switches) | Zero cross-model bucket collisions inside `Trunk Session` |
| **Combined Switch TTFT Overhead** | `23.5s–32.0s` per round-trip prefill | `4.27s` mean `SPAWN_NEW` boot + `3.73s` clean `45K` Step-1 TTFT |
| **Compaction Freeze Cadence** | `68.7s–89.0s` freeze every `44–58` steps (`19.8 min/1k` steps on `L0-1`; `27.1 min/1k` on `L0-2`) | `1/134` compactions on `L0-4`; `v2.0.0` cuts child compactions `-54%` (`13 -> 6` in backtest) |
| **Stream Timeouts / Anomalies (`retryInfos`)** | `31` anomalies on `L0-2` (`6` timeouts, `10` disconnects, `13` capacity); `4` anomalies up to `632.8s` on `S6` | `0` timeouts or disconnects on `L0-3`, `L0-4`, and `S9` |

*(See [05-production-telemetry-ttl-and-lifecycle-audit.md](05-production-telemetry-ttl-and-lifecycle-audit.md) for the underlying `300s` server KV-cache TTL cliff and `transcript.jsonl` schema analysis.)*

---

## 3. Right-Brain Memory-Value Probe (`75` Dispatches) `[Measured Production Telemetry]`

A forensic disk audit of `19` `Execution Subagent` transcripts (`75` real `RESUME_EXISTING` dispatches plus `15` real `SPAWN_NEW` rotations across `L0-3`, `L0-4`, `S3`, and `S9`) tested whether retaining a stateful executor's memory after `<report>` adds semantic value:

- **Left-Brain `<plan>` Self-Containment (`100%`):** Median `<plan>` length across all `75` dispatches was `9,469` chars (`1,487–25,582` chars across all `8` mid-task blocker hand-backs); `0 / 75` (`0.0%`) omitted verification commands; **`0 / 75` (`0.0%`)** referenced a prior `<plan>` (`R1` incidence = `0%`).
- **Zero Memory-Loss Failures on Spawn (`0 / 15`):** Across `15` real `SPAWN_NEW` rotations (`11` Trunk-compaction spawns, `3` live `v1.2.0` cost rotations, `1` `S3` rotation), **`0 / 15` (`0.0%`)** failed, stalled, or reworked due to missing prior right-brain state.
- **Actual Executor Re-Read Behavior:** Even when warm memory was retained (`RESUME_EXISTING`), executors re-read previously read files before editing **`80.2%`** of the time on post-completion waves (`76.3%` overall across `190` edits), and `47.0%` (`578 / 1,556`) of post-resume `read_file` calls repeated earlier reads—consistent with [execution-protocol.md](../../skills/orchestrator/references/execution-protocol.md) requiring direct disk inspection before editing.
- **`~30`-Turn Interim Cadence (`0 / 73`):** `0 / 73` (`0.0%`) dispatches ever triggered self-counted `~30`-turn interim reports (`89.0%` reported upon wave completion; `11.0%` hit early blocker triggers).

**Structural Conclusion:** Once `Execution Subagent` returns `<report>`, its semantic memory value is near zero; `RESUME_EXISTING` existed solely as a KV-cache cost optimization, while stateful reuse exposed multi-dispatch children to Antigravity's `~10,240 B` `# Parent Agent Messages` compaction truncation law (`~(10240/N - 127)` bytes per dispatch).

---

## 4. `75`-Dispatch `sim-vs-sim` Backtest & Runtime Latency

### Counterfactual Spend (`75` Historical Dispatches Across `L0-3`, `L0-4`, `S3`, `S9`) `[Sim-vs-Sim Counterfactual Backtest]`

| Architecture | Rotations (Warm) | `1x` Child Spend (Saved vs `v1.1.x`) | `2x` Child Spend (Saved vs `v1.1.x`) |
|---|---:|---:|---:|
| **`v1.1.x` (`SimBase`, permanent `RESUME_EXISTING`)** | `0` (`0`) | `$122.55` (`+$0.00`) | `$191.07` (`+$0.00`) |
| **`v1.2.1` (`Pure q=0` cost-threshold rotation)** | `24` (`17`) | `$109.67` (`+$12.88`) | `$158.46` (`+$32.61`) |
| **`v2.0.0` / `v2.0.1` (`Always-New`, stateless `N_max = 1`)** | `75` (`45`) | **`$109.09` (`+$13.45`)** | **`$154.70` (`+$36.37`)** |

- **Why `Always-New` edges out `Pure q=0` (`+$0.57` `1x` / `+$3.76` `2x`):** Of the `+51` additional rotations over `v1.2.1`, `23 / 51` were already `cache == 0` (`23/23` wins adding `+$2.29` `1x` / `+$4.02` `2x`), offsetting the `-$1.72` `1x` / `-$0.26` `2x` delta on `28/51` small warm resumes. Accounting for unmodeled Trunk dispatch overhead (`$0.002–$0.006`/spawn, `< $0.31` total; cold prefill `$0.1165`/spawn and file re-reads are already inside the simulator), `Always-New` remains ahead by `+$0.06..+$0.47` (`1x`) and `+$3.25..+$3.66` (`2x`) while eliminating `396` lines of state-machine code (`1,237 -> 841` lines in [sync_memory.py](../../skills/orchestrator/scripts/sync_memory.py)).

### Boot Latency & CLI Overhead `[Measured Production Telemetry]`

- **Empirical `SPAWN_NEW` Boot (`18` clean dispatches):** `4.27s` mean, `4.28s` median (max `5.73s`). Because a clean `45K` child's Step-1 work TTFT (`3.73s`) beats bloated warm resumes (`6.30s–7.08s`) by `2.31s–3.03s`, `+51` spawns across `42h` of multi-session LLM time add only `~83s` (`+1.4 min`, `+0.05%` total; `+1.6s–4.3s` per single follow-up).
- **Single-Pass `sync_memory.py` Speed:** Because Antigravity truncates compact logs at `4 KB`, `C1` fast-path skipped full parsing in only `14.7%` of `RESUME_EXISTING` calls (`64/75` fell back to `transcript_full.jsonl`). Stateless `Always-New` executes a single pass with zero child-log scanning: `37–59 ms` (`S3`), `134–169 ms` (`L0-4`), `298 ms` median / `436 ms` peak (`S9`)—`23x` under Antigravity's `10,000 ms` synchronous wait limit.

---

## 5. Full `10`-Scenario Quota, Latency & Pareto Summary

*(Grounded in `[Measured Production Telemetry]` `S1`–`S9` anchors + `[Sim-vs-Sim Counterfactual Backtest]` projections. `S1`–`S5` per session; `S6`–`S9` per `1,000` steps. Parentheses show `N-2x` / `Sub-3x` where distinct.)*

| Scenario | `Official Native` (`1x` / `N-2x` / `Sub-3x`) | `v1.2.1` (`Pure q=0`) (`1x` / `N-2x`) | `v2.0.x` (`Always-New`) (`1x` / `N-2x`) | `v2.0.x` vs `Official` (`1x` / `N-2x` / `Sub-3x`) | Pareto Verdict (vs `v1.2.1` / vs `Official`) |
|---|---|---|---|---|---|
| **`S1`** First-turn Q&A / 1–2 turn edit | Q&A `$0.04–$0.95`<br>Edit `$0.04–$0.101` | Q&A parity<br>Edit `$0.08–$0.168` | **Same as `v1.2.1`** (`N = 1`) | Q&A `0%`; Edit `+$0.04..+$0.07` | Parity / **Inferior** (first-turn micro-edit tax) |
| **Ongoing short tweaks** (`LMW 20–100 KB, K = 1..12`) | `$0.33–$1.39` (`$0.33–$2.75` / `$0.56–$2.11`) | `$0.12–$0.44` (`$0.12–$0.44`) | **`$0.16–$0.47`** (`$0.16–$0.47`) | **`45/45` grid wins: `-45%..-69%` / `-45%..-84%` / `-62%..-82%`** | Narrow warm-cache delta (`+$0.02–$0.08`) / **Decisive win from `LMW >= 2.8 KB` (Turn 2)** |
| **`S2`** High-ctx arch / UI branch | `$4.60–$5.40` (`$6.8–$8.2` / `$6.9–$9.1`) | `$2.85–$3.90` (`$3.95–$5.60`) | **`$2.86–$3.92`** (`$3.96–$5.62`) | **`-32%` / `-36%` / `-58%`** | Parity / **Decisive win** |
| **`S3`** Forensic research (`254` st) | `$26.5–$31.0` (`$40–$47` / `$41–$49`) | `$18.27–$20.27` (`$26.6–$30.6`) | **`$18.07–$20.07`** (`$26.4–$30.4`) | **`-34%` / `-35%` / `-58%`** (`+51%` rework buffer) | Marginally ahead / **Trade-off** (`>10s` probes) |
| **`S4`** Serial CLI (`132` st) | `$12.74` (`$15.78` / `$21.12`) | `$7.02–$8.12` (`$8.10–$9.70`) | **`$7.06–$8.18`** (`$8.14–$9.76`) | **`-40%` / `-43%` / `-64%`** | Parity / **Trade-off** (quota vs live CLI UX) |
| **`S5`** Standalone short feature (`<60` st) | `$1.83` (`$1.83` / `$3.19`) | `$1.95–$2.25` (`$1.95–$2.25`) | **`$1.98–$2.28`** (`$1.98–$2.28`) | `+16%` (`1x`) / **`-33%` (`Sub-3x`)** | Narrow delta / **Trade-off** (`Official` `3–4m` faster `<50` st) |
| **`S6`** Greenfield project (`1k` st) | `$128.50` (`$216.97` / `$201.05`) | `$48.3–$56.3` (`$67.6–$83.6`) | **`$48.2–$56.2`** (`$66.8–$82.8`) | **`-59%` / `-66%` / `-74%`** | Ahead / **Decisive win** |
| **`S7`** Slow builds / deep debug (`1k` st) | `$96.00` (`$173.47` / `$129.30`) | `$54.6–$62.6` (`$84.2–$102.2`) | **`$54.4–$62.4`** (`$83.7–$101.7`) | **`-39%` / `-47%` / `-55%`** (`+64.4%` / `+87.2%` rework buffer) | Ahead / **Decisive win** (`15–25 min/1k` faster) |
| **`S8a`** Parallel DAG (`80%` delegation expected) | `$59.43` (`$89.92` / `$81.18`) | `$43.2–$49.7` (`$62.3–$73.3`) | **`$43.4–$49.9`** (`$62.3–$73.3`) | **`-22%` / `-25%` / `-43%`** (`+27.5%` / `+32.6%` buffer) | Parity / **Decisive win** |
| **`S8a`** Parallel DAG (`0%` delegation fallback) | `$59.43` (`$89.92` / `$81.18`) | `$54.2–$55.9` (`$98.1–$103.1`) | **`$54.2–$55.9`** (`$98.1–$103.1`) | `-7.4%` (`1x`) / **`-10.6%` behind (`N-2x`)** / `-32%` (`Sub-3x`) | Parity / **Boundary 1 Caveat** (`41.3%` spend on un-offloaded `333K` Trunk) |
| **`S8b`** Coupled monolith (`1k` st) | `$95.98` (`$173.47` / `$129.30`) | `$49.5–$54.0` (`$79.0–$91.0`) | **`$49.7–$54.2`** (`$78.8–$90.8`) | **`-46%` / `-51%` / `-60%`** (`+84.9%` / `+104.6%` buffer) | Parity / **Decisive win** (`pro` tier `<10%` of margin) |
| **`S9`** `/swarm` + meta-engineering (`1k` st) | Unsupported | `$73.8–$78.3` (`$108.4–$116.4`) | **`$73.6–$78.1`** (`$106.2–$114.2`) | **Exclusive capability** (`-$2.25/1k` `2x` vs `v1.2.1`) | Ahead / **Strict Pareto Win** |

**Capability & Reliability Summary (`v2.0.x` vs `v1.2.1`):** Zero regressions across `10` capability dimensions, while improving compaction resilience (`N_max = 1` keeps **`~8.61–8.70 KB`** of active `<plan>` across child compaction vs `~300 B` at `N = 6` in `v1.2.1`), closing `3` concurrency/rewind/salvage edge cases, and simplifying cross-client portability to one stateless worker primitive (`Claude Code` `Agent` / `Codex` `spawn_agent`).

---

## 6. Cross-Model Scaling (`Gemini`, `OpenAI / Codex`, `Claude`)

Because absolute input token price cancels out of the normalized prefix-retention inequality, higher cache-read ratios (`alpha`) penalize bloated retained executor contexts far more severely than Gemini (`alpha = 0.05`):

| Platform / Cache Pricing (`K = 12`) | Cache Read (`alpha`) | Cache Write (`w`) | Theoretical Break-Even Slope (`C_old / C_new`) | Fixed Intercept (`C_0*`) | `v2.0.x` (`Always-New`) Spend Delta vs `v1.2.1` (`75`-Dispatch Backtest) |
|---|---:|---:|---:|---:|---|
| **Gemini 4 (`v1.2.1` baseline)** | `0.05` | `1.00` | `2.583x` | `+25.0K` | **`-$0.57` (`1x`) / `-$3.76` (`2x`)** |
| **OpenAI / Codex (`90%` cache discount)** | `0.10` | `1.00` | `1.750x` | `+13.0K` | **`-$2.15` (`1x`) / `-$7.01` (`2x`)** (`1.5x–1.9x` larger stateless lead) |
| **OpenAI / Codex (`75%` cache discount)** | `0.25` | `1.00` | `1.250x` | `+6.2K` | **`-$6.96` (`1x`) / `-$16.89` (`2x`)** (warm read bleeds `5x` Gemini rate) |
| **Claude (`5m` TTL, `1.25x` write)** | `0.10` | `1.25` | `1.958x` | `+15.3K` | **`-$3.88` (`1x`) / `-$14.33` (`2x`)** (`Sonnet $3/M`, beats tuned `Pure q=0`) |
| **Claude (`1h` TTL, `2.00x` write)** | `0.10` | `2.00` | `2.583x` | `+22.2K` | Identical slope (`2.583x`), stronger intercept (`+22.2K`) |

---

## 7. Honest Trade-Offs & `L0-5` Rollback Triggers

1. **First-Turn Empty-Session Micro-Edits (`S1`):** Paying `sync` + `SPAWN_NEW` + `[plan review]` adds `~$0.04–$0.07` and `+25–40s` on brand-new `1`–`2`-line edits; plain single-model or Official Native remains preferable for trivial one-shot edits.
2. **Host Physical UX Ceilings (`Dim 10`):** No mid-flight soft `[plan review due]` interrupts, no live child diff streaming on the main chat canvas, and no persistent dev servers outliving a dispatch; see [host-physical-ux-and-runtime-ceilings.md](../../.out-of-scope/host-physical-ux-and-runtime-ceilings.md).
3. **Unvalidated Live Margins `[Pending L0-5 Live Validation]`:** Mid-task blocker retries (`8 / 75` historical dispatches) have not yet been stress-tested under stateless `Always-New` in live production (`L0-5`), and rapid `<5m` `K <= 4` follow-ups pay `~$0.02–$0.08` and `+1.6–4.3s` over warm `RESUME_EXISTING`.
4. **Objective `L0-5` Rollback Triggers (vs Tagged `v1.2.1` `1511ee5` in [Ticket 13](../../.scratch/orchestrator-v1/issues/13-v113-empirical-watch-and-residual-boundaries.md)):**
   - Fresh `SPAWN_NEW` boot read failure (`execution-protocol.md` or `pages/page_*.md`) exceeds **`5%`** of dispatches;
   - `M1` memory-loss rework / re-plan share rises **`> +10 pp`** above baseline or exceeds **`25%`**;
   - Daily interactive `K <= 3` follow-ups occur at **`>= 25%`** frequency with measurable user latency/quota friction warranting stateful `RESUME_EXISTING` re-introduction.
