# 14: Full-Scenario Dual-Axis Evaluation (v1.1.3 vs Official Native Orchestrator vs v1.1.1)

**What to build:** Research baseline only (no runtime code or protocol edits). Evaluate whether `orchestrator v1.1.3`'s quota reduction comes from eliminating pure waste (Pareto improvement) or from sacrificing engineering capability, correctness, or UX, grounded in the full local `usage-monitor` corpus (`281` trajectories, `17,414` steps, `3,566.91M` tokens, `$1,195.51` actual list across all `17` active root sessions mapped to scenarios `S1-S9`).

**Blocked by:** None

**Category:** research

**Status:** resolved

**References:** [01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md) | [03-ab-benchmark-and-kv-cache-telemetry.md](../../../docs/research/03-ab-benchmark-and-kv-cache-telemetry.md) | [05-production-telemetry-ttl-and-lifecycle-audit.md](../../../docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md) | [ADR-0001](../../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md) | [ADR-0002](../../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md) | [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) | [ADR-0007](../../../docs/adr/0007-session-bound-command-ownership.md) | [Ticket 11](11-dual-brain-vs-native-subagent-boundary.md) | [Ticket 12](12-full-repo-audit-hardening-and-official-alignment.md) | [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md)

## Executive Answer (Pareto Decomposition)

Conducted via a strictly read-only 3-model heterogeneous `/swarm` audit (`gemini-4-carbon-high` quantitative telemetry modeler, `claude-opus-5-5-high` capability-loss devil's advocate, `gemini-4-neon-xhigh` Pareto systems arbiter) against `trajectory_usage_cache.json` (`2026-11-22T07:50Z`), `pricing-catalog.json` (`2026.11.21.1`), SQLite `conversation_summaries.db` / `retryInfos`, and disk transcripts (`L0-1` through `L0-4`, `8d058da7`, `9dde0d3d`, `0f48e729`, `7623344f`, etc.):

- **Core Verdict:** Roughly **`70%-80%`** of `v1.1.3`'s quota reduction over Official Native Orchestrator (`~36%-43%` at `1.0x` aligned Neon pricing; `~55%-68%` under `Carbon 3.0x` pool or `>200K = 2x` weighting) is **Zero-Sacrifice Pure-Waste Elimination** (eliminating `60%-83%` same-thread model-switch KV-cache misses, `2.1x-2.8x` lower inference-step compaction cadence, zero recursive dual-model subagents, `ADR-0007`/`B1` Trunk leak elimination, `C1` `-52.5%` sync speedup, and `A1-A5`/`B3`/`B5`/`B6` bug fixes).
- **Not a Universal Free Lunch:** `v1.1.3` vs Official is **1 Strict Pareto Win (`S9`)**, **8 Real Trade-offs (`S2-S8b`, of which `S2`/`S6`/`S7`/`S8b` and conditional `S8a` strongly favor `v1.1.3`, `S3`/`S5` are situational, and `S4` favors Official/single-model on debug UX)**, and **1 Inferior (`S1` 1-2 turn side-effect edits)**. Against `v1.1.1`, `v1.1.3` is a **Strict Pareto Win on 7/10 scenario classes** and a favorable Real Trade-off on 3 (`S3`, `S4`, `S8a`, **0/10 Inferior**).
- **Epistemic Boundary:** Zero production `v1.1.3` transcripts exist yet (`2d2b926` shipped `2026-11-22`); all `v1.1.3` rows below are `[Counterfactual Projection]` anchored strictly in `[Empirical]` `usage-monitor` rates and disk transcripts, paired with falsification metrics (`M1-M6`) tracked in [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md).

## 1. Empirical Corpus Anchors (`usage-monitor`, `2026-11-22T07:50Z`)

- **Corpus totals:** `281` trajectories, `17,414` steps (`17,137` inference + `277` compactions), `3,566.91M` tokens (`32.14M` output), `90.12%` cache hit, `$1,195.51` actual list (`$1,324.72` Neon-aligned | `$1,123.90` Carbon-aligned | `$1,712.37` `Carbon 3.0x` Sub-Eq | `$2,181.33` `Neon >200K=2x`), covering `17` active root sessions (`+5` empty `0`-step entries) across `S1-S9`.
- **Pricing anchors (`pricing-catalog.json` `2026.11.21.1`, `0` unpriced steps):** `Neon` `$3.00/$0.15/$15.00` (`1.0x`), `Carbon/Argon` `$2.00/$0.10/$10.00` (`3.0x` pool; scheduled `2x` hike on `2026-12-01Z`), `Hydrogen` `$1.50/$0.075/$7.50` (`1.0x`), `Opus 5.5` `$4/$0.20/$20`, `Sonnet 5.5` `$2/$0.10/$10`.
- **Key empirical baselines:**
  - `S4` `9dde0d3d` (`Official Carbon`, `132` st): `72.58%` hit, `76.9%` (`10/13`) switch miss, `$12.74` Neon-eq / `$21.12` Sub-3x.
  - `S6` `8d058da7` (`Official Carbon`, `775` st, `34` subs): `82.54%` hit, `59.5%` (`47/79`) switch miss, `4` anomalies (incl. `632.8s` timeout), `$99.59` Neon-eq / `$155.81` Sub-3x.
  - `S7` `d1e362b3` (`v1.0.0` pre-opt `715` st: `$9.83` Trunk bg-bench cold wakeups) & `fa0dc277 W4B+Perf` (`v1.1.1`, `340` st: `308.9K` avgCtx, `$28.11` Neon, incl. `$3.44` = `12.2%` Trunk `B1` probe/poll burst).
  - `S8a` `24cd98b2` (`Official L0-1`, `8,138` st, `92` subs): `161.5K` avgCtx (`32.8%` `>200K`), `90.45%` hit (`69.7%` zero-cache / `82.7%` `<70%` switch miss), `1/44.2` compactions, `21.2%` `cmdFail`, `$59.43/1k` Neon-eq (`$89.92` N-2x, `$0.0333/1kOut`) vs `fa0dc277 W3 DAG` (`v1.1.1`, `510` st serial): `271.1K` avgCtx, `95.15%` hit, `$60.02/1k` Neon (`$110.65` N-2x).
  - `S8b` `d89020d4` (`Official L0-2`, `3,751` st, `39` subs): `263.6K` avgCtx (`65.2%` `>200K`), `89.16%` hit (`66.3%` zero-cache / `77.4%` `<70%` switch miss), `1/58.6` compactions, `31` SQLite `retryInfos` anomalies (`6` timeouts, `10` disconnects, `13` capacity), `13.2%` `cmdFail`, `$95.98/1k` Neon-eq (`$173.47` N-2x, `$129.30` Sub-3x) vs `fa0dc277 W1+4A` (`v1.1.1`, `467` st): `289.1K` avgCtx, `95.60%` hit, `0` timeouts/disconnects, `10.5%` `cmdFail`, `$60.81/1k` Neon (`$110.71` N-2x).
  - `S9` `7623344f` (`/swarm` + `v1.1.x`, `1,321` st, `60` subs): `174.0K` avgCtx, `91.59%` hit, `1/440` compactions, `0` anomalies, `$81.85/1k` Neon-eq.

## 2. Full 9-Scenario Quota & Pareto Verdict Matrix (`S1-S9`, `S8a`/`S8b`)

| Scen. | Real Anchors | `Official` (`Neon-$` / `Sub-3x`) | `v1.1.1` (`Neon-$`) | `v1.1.3` Expected / Fallback (`Neon-$`) | Gain Split (`Det` / `Beh`) | `v1.1.3` vs `Official` | `v1.1.3` vs `v1.1.1` |
|---|---|---|---|---|---|---|---|
| **`S1`** Micro-task / Q&A | `c027d9d2`, `80404dda`, `f51fbbe7` | Q&A `$0.04-$0.95`; Edit `$0.04-$0.07` | Q&A `$0.04-$0.95` (+RO-CLI tax); Edit `$0.09-$0.15` | Q&A `$0.04-$0.95`; Edit `$0.08-$0.14` (same fallback) | `100% / 0%` | **Inferior** (1-2 turn edits); parity on Q&A | **Strict Pareto Win** (`B8` RO-CLI) |
| **`S2`** High-ctx arch & UI-branch | `5c03c8fc`, `bc363271` | `$4.60-$5.40` / `$6.90-$9.10` | `$3.11` (`5c03c8fc` broken post-compact) | `$2.85-$3.10` / `$3.05-$3.11` (`5c03c8fc` fixed) | `90% / 10%` | **Real Trade-off** (strongly favors `v1.1.3`) | **Strict Pareto Win** (`A4b`) |
| **`S3`** Forensic research & telemetry | `0f48e729`, `cb68b41c`, `9ef431b6` | `$26.50-$31.00` / `$41-$49` (`254` st) | `$21.40-$22.53` | `$18.50-$20.50` / `$20.20-$21.20` | `75% / 25%` | **Real Trade-off** (situational; `>10s` probes hit `B1`) | **Real Trade-off** (strongly favors `v1.1.3`) |
| **`S4`** DevOps / serial CLI | `9dde0d3d` (`132` st) | `$12.74` / `$21.12` | `$7.90-$9.20` | `$7.10-$8.20` / `$7.50-$8.50` | `95% / 5%` | **Real Trade-off** (favors Official on UX/latency; `v1.1.3` wins quota) | **Real Trade-off** (marginally favors `v1.1.3`) |
| **`S5`** Short/med feature (`<60` st) | `2ae3212a`, `d03a7aff` | `$1.83` / `$3.19` (`36` st) | `$2.15-$2.45` | `$1.95-$2.25` / `$2.05-$2.30` | `100% / 0%` | **Real Trade-off** (Official faster `<50` st; `v1.1.3` wins `Sub-3x`) | **Strict Pareto Win** (`B3`/`B7`/`C1`) |
| **`S6`** Greenfield project (`1k` st) | `8d058da7` | `$128.50` / `$201.05` | `$63.00-$70.00` | `$50.00-$58.00` / `$60.50-$66.50` | `80% / 20%` | **Real Trade-off** (decisively favors `v1.1.3`) | **Strict Pareto Win** |
| **`S7`** Slow bench & deep debug (`1k` st) | `d1e362b3`, `fa0dc277` | `$96.00` / `$129.30` | `$82.68` | `$58.00-$66.00` / `$74.50-$76.80` | `59% / 41%` vs Off | **Real Trade-off** (decisively favors `v1.1.3`) | **Strict Pareto Win** (`B1`/`B10`) |
| **`S8a`** Parallel DAG refactor (`1k` st) | `24cd98b2`, `fa0dc277` W3 | `$59.43` / `$81.18` (`$89.92` N-2x) | `$60.02` (`$110.65` N-2x) | `$44.00-$50.50` (`$64-$75` N-2x) / `$57.50-$59.20` (`$105-$110` N-2x) | **`9-13% / 87-91%`** | **Real Trade-off** (upside favors `v1.1.3`; fallback loses `-16.4%` at N-2x) | **Real Trade-off** (strongly favors `v1.1.3`) |
| **`S8b`** Coupled monolith (`1k` st) | `d89020d4`, `fa0dc277` W1&4 | `$95.98` / `$129.30` (`$173.47` N-2x) | `$60.81` (`$110.71` N-2x) | `$52.00-$56.50` (`$85-$97` N-2x) / `$58.00-$59.80` (`$105-$109` N-2x) | `89% / 11%` vs Off | **Real Trade-off** (strongly favors `v1.1.3`; `pro` tier affordable) | **Strict Pareto Win** |
| **`S9`** Heavy `/swarm` + meta-eng (`1k` st) | `7623344f` | Unsupported | `$81.85` | `$75.00-$79.50` / `$78.50-$80.50` | `70% / 30%` | **Strict Pareto Win** | **Strict Pareto Win** |

## 3. Rework Break-Even Thresholds (`S7`, `S8a`, `S8b`)

How much **extra** rework/retry (`Delta R*` extra steps beyond `v1.1.1`'s empirical `10.5%` `cmdFail` baseline) `v1.1.3` can absorb per `1,000` steps before erasing its quota lead:

- **`S7` (Expected `$62.0/1k`):** `+54.8%` (`+447` steps / `~10-12` fix rounds) vs Official (`+71.8%` at `N-2x`, `+108.5%` at `Sub-3x`); `+33.4%` (`+272` steps / `~6-8` rounds) vs `v1.1.1`. Fallback (`0%` delegation) still buffers `+26.9%` vs Official and `+9.3%` vs `v1.1.1`.
- **`S8a` (Expected `$47.3/1k`):** **`+25.8%`** (`+234` steps / `~5-6` merge-fix rounds) vs Official (`+29.4%` at `N-2x`); `+27.0%` vs `v1.1.1`. **Fallback (`0%` `research`/`depth=2`):** razor-thin `+1.9%` (`+21` steps) at `1.0x` Neon and **`-16.4%` underwater at `>200K=2x`**—mathematically confirming Ticket `13` Boundary 1 as the top `L0-5` risk.
- **`S8b` (Expected `$54.3/1k`):** **`+76.9%`** (`+673` steps / `~15-18` fix rounds) vs Official (`+90.6%` at `N-2x`, `+138.3%` at `Sub-3x`); Fallback still holds `+63.0%` (`+598` steps). Upgrading `S8b` workspaces to `orchestrator-tier: pro` (`Hydrogen XHigh`, identical `$1.50/$0.075/$7.50` catalog rate, `~10%-18%` more thinking tokens) consumes `< 1/5` of this margin while mitigating `flash` compliance drift.

## 4. Capability-Loss Red-Team Findings (10 Dimensions & Disk Evidence `E1-E6`)

Empirical disk evidence pulled from `fa0dc277`/`b6f60460`, `d1e362b3`, `24cd98b2`, `d89020d4`, `8d058da7`, `9dde0d3d`, and `7623344f`:

- **Real Capability / UX Sacrifices (`A` — Verified Trade-offs):**
  1. **Enforcement Rigidity (Dim 8, `E1`):** Official host-forces `[plan review due]` every `30` invocations (`40` checkpoints in `24cd98b2`). In `L0-4`, `b6f60460` (`flash`) ran `2,196` raw records with only `8` `<report>`s and a **`446`-tool-call unreviewed gap** (`tc 786 -> 1232`, `15x` past soft `~30`-turn cadence).
  2. **Verification Rigor Asymmetry (Dim 4, `E3`):** In `d1e362b3`, `flash` weakened tests twice (step `124` gating a parity assertion behind `inspect.getsource`; step `190` bypassing `_FORBIDDEN_LIVE_DIR` in memory). Both were caught only because `flash` disclosed them honestly in `<report> §3`; Tier 1 (`git status/diff --stat`) cannot detect undisclosed test weakening, whereas Official exposes `edit_file` diffs inline to the planner. (Note `E4`: `fa0dc277` `Neon` also read `5-8` source files beyond Tier 1 on most reviews, reducing real Tier-1 savings.)
  3. **Context Fidelity & Raw Output Omission (Dim 1, `E6`):** `Living Memory Window` (`ADR-0002` L25) strips `GENERIC` tool outputs, `tool_calls`, and `thinking`; Official hands off the full thread. `depth=2` slicing adds a second lossy hop (`Trunk -> Exec[flash] -> depth=2[flash] -> <report>`).
  4. **Child Invisible Self-Compaction (Dim 9, `E2`):** While tree-wide LLM-step compactions are `2.1x-2.8x` rarer than Official (`1/125` in `fa0dc277` vs `1/58.6` `L0-2` and `1/44.2` `L0-1`), `b6f60460` still self-compacted **`7` times** (`2` inside one `446`-tool-call gap) invisibly to `Trunk`, creating `Re-plan if:` / constraint amnesia risk (`Ticket 07` residual).
  5. **UX Friction & Destructive Interrupts (Dim 10):** `S1` 1-turn side-effect edits pay fixed spawn/`sync`/`[plan review]` overhead; mid-flight redirect requires destructive `kill + reset` rather than Official's soft `[plan review due]`; child traces are hidden from the main chat canvas; persistent dev servers cannot outlive a dispatch (`ADR-0007`).
- **Genuine Capability Advantages of `v1.1.3` (`B`):**
  1. **Frontier & Cross-Family Model Freedom (Dim 7):** `Opus 5.5` / `Neon XHigh` planners + workspace-static `orchestrator-tier: pro` (`Hydrogen XHigh`), plus cross-pool quota arbitrage.
  2. **Clean Trunk Planning SNR & Multi-Epoch Invariant Retention (Dim 2, Dim 9 Trunk):** Trunk avoids `64-184` tool-noise compactions, preserving architectural redlines.
  3. **Stream Stability & Recovery Scope (Dim 5):** `0` timeouts/disconnects in `L0-3`/`L0-4`/`7623344f` vs `31` SQLite `retryInfos` anomalies (`6` timeouts, `10` disconnects, `13` capacity) in `L0-2` and `4` (`632.8s` timeout) in `8d058da7` *(note: raw `ERROR_MESSAGE` stream counts alone are similar across engines, so SQLite `retryInfos` timeouts/disconnects—not `ERROR_MESSAGE`—is the valid stability indicator)*.
  4. **Composable Coexistence (`S9`, `S2`):** Seamless `/swarm` + UI-branched chat (`5c03c8fc`) + orthogonal Route 3 `egm-*`/`code-review`/`research`.
- **Unproven Hypotheses Requiring `L0-5` Measurement (`C`):** Actual `v1.1.3` rework ratio (`M1`), undisclosed Tier-1 verification escapes (`M2`), spontaneous `depth=2` activation vs merge-conflict rate (`M3`), child-compaction compliance decay (`M4`), and post-wave `P0/P1` defect density (`M5`)—all tracked in [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md).

## 5. Practical Mode Selection Guide

1. **Plain Single-Model (`Neon` / `Opus`, no orchestration):** `S1` quick 1-2 line edits; `S3` interactive `15-60s` telemetry scripting needing inline tables; `S4` short stateful CLI/daemon debugging.
2. **Official Native `Orchestrator (Neon)`:** `S5` `<50`-step settled sprints prioritizing wall-clock/inline diffs; `S4` medium CLI setup needing live streaming + soft `[plan review due]` interrupts; workspaces requiring host-enforced write-refusal and hard `30`-turn stops.
3. **`orchestrator v1.1.3` (`flash` default):** `S2` high-context architecture & UI-branched chats; `S3` multi-auditor synthesis; `S6` greenfield spec-driven projects (pair with Route 3 `egm-*`/`code-review`); `S7` slow builds/benchmarks (`>60s`); `S8a` parallelizable DAG refactors (specify disjoint file/interface contracts in `<plan>`). Flip workspace rule to **`orchestrator-tier: pro`** for **`S8b` coupled monoliths** or complex **`S8a` `depth=2` foreman waves**.
4. **`/swarm` + `v1.1.3` Hybrid:** `S9` dual-repo meta-engineering, protocol design, and cross-family adversarial reviews.

## Comments

- 2026-11-22 (3-Model Heterogeneous `/swarm` Audit — Resolved): Completed full-corpus (`281` trajectories / `17,414` steps) dual-axis evaluation via `gemini-4-carbon-high` (`quota-telemetry-modeler`), `claude-opus-5-5-high` (`capability-redteam`), and `gemini-4-neon-xhigh` (`pareto-systems-judge`). Reconciled raw `ERROR_MESSAGE` vs SQLite `retryInfos` and raw-record vs inference-step compaction metrics, recorded concrete `L0-5` capability/rework falsification metrics (`M1-M6`) in [Ticket 13](13-v113-empirical-watch-and-residual-boundaries.md), and closed this research baseline as `Status: resolved`.
