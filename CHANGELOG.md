# Changelog

All notable changes to `orchestrator` (`dual-brain-orchestrator`) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2026-11-22

### Fixed
- **`P2-1` pre-`sync` active-child ordering ([skills/orchestrator/SKILL.md](skills/orchestrator/SKILL.md), [skills/orchestrator/references/harnesses.md](skills/orchestrator/references/harnesses.md)):** Moved the non-Route-1 `manage_subagents(Action="list")` running check before `sync` so an active child never overlaps and `pages/` or `pending_sync` are never staged prior to a §4 yield or `kill` + `reset` (preserving `cmd_reset` `-1` UI-rewind isolation).
- **Wording cleanups:** Removed two stale `v1.x` continuation phrases (`harnesses.md` §4 `reset` parenthetical and `execution-protocol.md` §1 `"or continuation"`).

### Added
- **Public benchmark & Pareto consolidation:** Added [docs/research/06-v2-stateless-benchmark-and-pareto-evaluation.md](docs/research/06-v2-stateless-benchmark-and-pareto-evaluation.md) synthesizing the `281`-trajectory / `17,414`-step telemetry corpus, `314` Official Native switch measurements, `75`-dispatch right-brain memory probe and `sim-vs-sim` backtests, `10`-scenario Pareto evaluation, cross-model scaling, honest trade-offs, and `L0-5` rollback criteria; added a superseded pointer note in [docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md](docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md) §6.
- **Repository & CI polish:** Added [LICENSE](LICENSE) (MIT), [CHANGELOG.md](CHANGELOG.md), [.github/workflows/test.yml](.github/workflows/test.yml) (Python `3.10`–`3.13` on `ubuntu-latest`), upgraded bilingual showcase [README.md](README.md) and [README.zh-CN.md](README.zh-CN.md), refreshed [plugin.json](plugin.json) metadata, and locked `P2-1` ordering in [tests/test_package_contracts.py](tests/test_package_contracts.py).

## [2.0.0] - 2026-11-22

### Changed (Breaking Architectural Simplification)
- **Stateless `Always-New` `Execution Subagent` (`SPAWN_NEW` on every dispatch, `N_max = 1`):** Removed `RESUME_EXISTING`, `Pure q=0` child-log scanning, `prefix_digest`, incremental `delta pages`, `--tier`, `--force-spawn`, `--subagent-transcript`, `~30`-turn self-counted interim cadence, dual-track `<plan>` phrasing, and `idle` nudges—cutting [skills/orchestrator/scripts/sync_memory.py](skills/orchestrator/scripts/sync_memory.py) by `-32.0%` (`1,237 -> 841` lines) and removing `879` net lines across `19` tracked files.
- **Minimal `state.json` schema with zero-purge hot upgrade:** Reduced `state.json` from `14` fields to `5` (`4` top-level keys plus `pending_sync.synced_through`) while cleanly tolerating and stripping legacy `v1.1.x` / `v1.2.x` keys on upgrade.
- **Eliminated `10 KB / N` cross-dispatch compaction truncation:** Because `N_max = 1` holds on every dispatch, active `<plan>` bodies preserve `~8.6–8.8 KB` across child compaction rather than shrinking to `~(10240/N - 127)` bytes.

### Added
- **Five red-team safety guardrails:** Pre-dispatch running-child guard and post-compaction retired-child cleanup, §4 child `transcript.jsonl` salvage check before respawn (preventing duplicate non-idempotent commits/pushes), Exit 1/2 `<plan>` restatement of prior failed attempts, `R1` self-contained `<plan>` guard, and `cmd_reset` `-1` retirement watermark when `pending_sync is None` (closing UI-rewind cancel races).
- **L0-5 watch & rollback anchor:** Updated [Ticket 13](.scratch/orchestrator-v1/issues/13-v113-empirical-watch-and-residual-boundaries.md) with `v2.0.0` projections and `3` objective `L0-5` rollback criteria against tagged `v1.2.1` (`1511ee5`).

## [1.2.1] - 2026-11-22 *(Tagged Rollback Baseline for Stateful `RESUME_EXISTING`: `1511ee5`)*

### Fixed
- **Self-contained `<plan>` restatement (`R1`):** Explicitly prevented `Trunk Session` from omitting remaining paths, verification commands, or `Re-plan if:` triggers based on prior dispatches (which are never exported to `pages/page_*.md`).
- **Envelope & rotation hardening:** Tightened `RESUME_EXISTING` `send_message` reminder offset below `1,100` UTF-8 bytes (`N <= 8/9` resilience), fixed Turn-1 Empty-Grace `last_synced_step == -1` cost rotation bypass, popped stale `lmw_bytes` in `cmd_bind`, pruned `-29` dead LOC and `~1.44 KB` redundant prompt prose, and closed `Ticket 15` into `M2`/`M5`.

## [1.2.0] - 2026-11-22

### Added
- **Clock-free `Pure q=0` expected-cost right-brain rotation:** Added `0.60 * C_old > 1.55 * C_new + 15,000` rotation via EOF reverse child-`CHECKPOINT` scanning, zero-extra-turn batched `kill` of `retired_subagent_id`, settled-dispatch investigation skip in `SKILL.md`, and `< 600` UTF-8 byte `SPAWN_NEW` re-read offset pinning.

## [1.1.4] - 2026-11-22

### Added
- **Post-compaction protocol re-read & failure excerpt cap:** Added silent one-time post-compaction re-read of [skills/orchestrator/references/execution-protocol.md](skills/orchestrator/references/execution-protocol.md) (`Ticket 16`) and capped failure excerpts in `<report> §3` to `<=15` verbatim lines (`first error + final summary`, `Ticket 17`).

## [1.1.3] - 2026-11-22

### Fixed & Added
- **State machine & Official alignment:** Hardened `sync_memory.py` (`C1` fast-path/companion handling, rewind/corrupt-state guards), aligned Official `Direct Answer Gate`, `Approve-First`, and `git log --stat` checks, adopted native `waiting_for_dependents` guard (`Ticket 12`), and established `L0-5` watch (`Ticket 13`) + full-corpus dual-axis evaluation (`Ticket 14`).

## [1.1.2] - 2026-11-22

### Changed
- **Unified Dual-Brain Scope & orthogonal native subagents:** Clarified that `orchestrator` governs strictly the single bound `Execution Subagent`, while `Isolated Subagents` (`research`, `egm-*`, `code-review`) remain orthogonal and untouched by `orchestrator-tier:`, and unblocked `depth=2` in-plan child delegation (`Ticket 11`, [ADR-0004](docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md)).

## [1.1.1] - 2026-11-20

### Fixed
- **Reactive async command ownership:** Enforced non-polling reactive await for started commands and child subagents (`Ticket 10`).

## [1.1.0] - 2026-11-20

### Added
- **Session-bound command ownership ([ADR-0007](docs/adr/0007-session-bound-command-ownership.md)):** Enforced symmetric no-yield-while-running invariant across `Trunk Session` and `Execution Subagent`, Antigravity `10,000 ms` wait cap isolation, and three-tier `[plan review]` verification ladder (`Ticket 08`).
- **SSOT thin-pointer adoption & telemetry audit:** Slimmed `README.md` and `README.zh-CN.md` adoption snippets `< 1,000` bytes (`Ticket 09`) and published [docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md](docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md).

## [1.0.0] - 2026-11-19

### Added
- **Initial Antigravity V1 pure-skill release:** Published root [plugin.json](plugin.json), `skills/orchestrator/` (`SKILL.md`, `execution-protocol.md`, `harnesses.md`, zero-dependency stdlib `sync_memory.py`), `Seam 1` + `Seam 2A` test suites, [ADR-0001](docs/adr/0001-unified-subagent-report-return-into-plan-review.md)–[ADR-0006](docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md), and foundational research `01`–`04`.
