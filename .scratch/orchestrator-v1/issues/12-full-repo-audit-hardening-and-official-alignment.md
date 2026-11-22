# 12: Full-Repo Holistic Audit Hardening and Official Orchestrator Alignment

**What to build:** Resolve the verified runtime script bugs, protocol contradictions/loopholes, performance/test gaps, and historical ADR/spec drift identified by the clean-slate 3-model holistic `/swarm` audit (`HEAD = a808ede`, `v1.1.2`), aligning all protocol/architectural fixes strictly with the Official Native Orchestrator baseline (`docs/research/01-official-orchestrator-system.md`) rather than introducing bespoke mechanics.

**Blocked by:** None

**Category:** bug / hardening

**Status:** resolved

**References:** [01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md) | [SKILL.md](../../../skills/orchestrator/SKILL.md) | [execution-protocol.md](../../../skills/orchestrator/references/execution-protocol.md) | [harnesses.md](../../../skills/orchestrator/references/harnesses.md) | [sync_memory.py](../../../skills/orchestrator/scripts/sync_memory.py) | [ADR-0003](../../../docs/adr/0003-matt-pure-skill-packaging-and-shared-rule-adoption.md) | [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) | [ADR-0007](../../../docs/adr/0007-session-bound-command-ownership.md) | [spec.md](../spec.md) | [test_sync_memory.py](../../../tests/test_sync_memory.py) | [test_package_contracts.py](../../../tests/test_package_contracts.py)

## Audit Scope & Provenance

- Clean-slate read-only 3-model `/swarm` review (`gemini-4-carbon-high` code/transcripts, `claude-opus-5-5-high` full-lifecycle protocol red-team, `gemini-4-neon-xhigh` architecture/ADRs/docs/cross-repo seam) against `orchestrator` `a808ede` (`v1.1.2`) and `engineering-kit` `b38248e`.
- Cross-probed read-only against all `255` local host `transcript.jsonl` / `transcript_full.jsonl` pairs under `~/.gemini/antigravity/brain/`.
- **P0 Blockers:** `0`. **`engineering-kit` (`b38248e`):** confirmed clean (zero defects, zero redundancy, zero link/CRLF issues; only downstream sync needed if `B4` updates the adoption snippet override hint and/or re-pins a new `orchestrator` SHA).

## Findings Catalog

### Group A: `sync_memory.py` Implementation & State-Machine Bugs (P1)

1. **A1 (`P1`) - Unanchored `<ADDITIONAL_METADATA>` stripping corrupts `USER_INPUT` on `@[ITEM]` mentions** (`skills/orchestrator/scripts/sync_memory.py:235-272, 291-296`):
   - All `476` observed host `USER_INPUT` records place `@[ITEM]` content inside trailing `<ADDITIONAL_METADATA>`. `_pop_trailing_envelope` / `_pop_leading_envelope` use unanchored substring `rfind` / `find`, which breaks or slices content in half when a mentioned file itself contains `<ADDITIONAL_METADATA>` (e.g., `@[sync_memory.py]` or `@[test_sync_memory.py]`).
   - *Candidate fix:* Anchor outer envelopes strictly on standalone tag lines with balanced depth scanning.
2. **A2 (`P1`) - `expand_with_companion` `comp_by_line` skips `_created_at_compatible`** (`skills/orchestrator/scripts/sync_memory.py:379, 390-406`, `spec.md:97`):
   - On unshifted in-place rewinds where `transcript_full.jsonl` lags `transcript.jsonl`, `comp_by_line` hydrates stale abandoned-branch `content`/`tool_calls` (0 valid `created_at` mismatches across `255` host transcripts).
   - *Candidate fix:* Remove `comp_by_line`; always resolve via `comp_folded.get(step_idx)` and enforce `type` + `_created_at_compatible` unconditionally.
3. **A3 (`P1`, Opus + Carbon dual-confirmed) - Respawn via `reset -> sync` when `pending_sync is None` silently quarantines the last valid `<report>`** (`skills/orchestrator/scripts/sync_memory.py:781-788, 470-473`, `SKILL.md:68`, `harnesses.md:110`):
   - After Exit 3 or Tier 3 respawn with `pending_sync = None`, `reset` retires `prev_id` at old `last_synced_step`, causing the next `sync` to quarantine the newly arrived valid `<report>`.
   - *Candidate fix:* Add `sync --force-spawn` for non-cancel respawns (preserving `kill -> reset` strictly for mid-flight cancel so canceled race-condition reports stay quarantined), or specify `sync -> reset -> sync` before respawn.
4. **A4 (`P1`, Opus + Carbon dual-confirmed) - Origin classification gaps on (a) middle-truncated `step 0` `USER_INPUT` and (b) non-zero-start branched chats** (`skills/orchestrator/scripts/sync_memory.py:299-313, 604-605, 622-624`, `SKILL.md:36`):
   - *(4a)* When `step 0` `USER_INPUT` is middle-truncated by `>46 KB` metadata, `<USER_REQUEST>\n` stays attached, misclassifying `[swarm]`/`[EXECUTION SUBAGENT]` children as `TRUNK`.
   - *(4b)* Branched human chats starting at `step_index > 0` (observed in host `5c03c8fc`, starting at `step 960` `USER_INPUT`) fail open in `sync` (`classify_step_zero == "SUBAGENT"`) pre-compaction, then fail closed (`UNKNOWN`) in `check-origin` post-compaction.
   - *Candidate fix:* *(4a)* Strip leading `<USER_REQUEST>` + whitespace on truncated `step 0` before checking subagent prefixes. *(4b)* Unify `sync` and `check-origin` semantics (decision needed: fail closed uniformly with existing non-empty `state.json` `execution_subagent_ids` as `TRUNK` proof, vs inspecting `folded[min(folded)]`).
5. **A5 (`P1`) - Partial multi-byte UTF-8 EOF flush crashes `fold_jsonl_file` & bare `\r` bypasses `normalize_lf` / `MAX_PAGE_LINES`** (`skills/orchestrator/scripts/sync_memory.py:46-47, 180-182, 196-198, 498, 550`):
   - Concurrent host writes can split a 3-byte CJK character at EOF, causing `UnicodeDecodeError` (`exit 2`); bare `\r` (observed in `5c03c8fc` steps `964-965`) leaks `0x0d` into LF-only pages and evades line-cap counting.
   - *Candidate fix:* Read bytes and decode strictly up to the last `b"\n"`, dropping an incomplete UTF-8 EOF tail; replace `\r` in `normalize_lf`.

### Group B: Runtime Protocol Architecture & Official-Alignment Issues (P1 & P2)

1. **B1 (`P1`, Protocol / Official Alignment) - Command Ownership polling loophole observed live in `fa0dc277`** (`SKILL.md:14,55,62,68`, `harnesses.md:21`):
   - Wording ("finish before Trunk yields" + "work *expected* not to finish") allowed `fa0dc277` (`v1.1.1`) to launch probe scripts in-Trunk and poll `manage_task(status)` to finish before yielding; also lacks a failure branch if `sync_memory.py` itself backgrounds.
   - *Candidate fix:* Define synchronous completion strictly as returning inside one `run_command(WaitMsBeforeAsync <= 10000)` (if it backgrounds, kill immediately and never poll `manage_task`); move builds, test suites, benchmarks, and probe scripts unconditionally into `<plan>`; if `sync_memory.py` backgrounds, kill it, halt dispatch, and report to user.
2. **B2 (`P1`, Official Part 7 Alignment) - `[plan review]` Tier 1 vs Exit 3 direct-observation contradiction** (`SKILL.md:68` vs `L72`):
   - Tier 1 treats `<report>` as untrusted and forbids re-running passing suites, while Exit 3 requires reporting only from direct observations/tool outputs.
   - *Candidate fix:* Align with Official Part 7 (`01-official-orchestrator-system.md:106-111`) + host transcript verification: either clarify Tier 1 verifies cited test command + exit code in the bound child's host-recorded `transcript.jsonl` (direct observation, zero re-runs) or align Exit 3's phrasing explicitly with Tier-1 host-verified outputs.
3. **B3 (`P1`, Official Part 4 Alignment) - Active `<plan>` selection ambiguity vs `Living Memory Window` pages** (`execution-protocol.md:12` vs `harnesses.md:73-74,93-94`):
   - Official Part 4 (`01-official-orchestrator-system.md:60`) pins the active plan strictly to the most recent `"Plan mode is off"` `<SYSTEM_MESSAGE>`. Our `execution-protocol.md:12` says "the most recent `<plan>` in your conversation", yet the executor reads exported `page_*.md` *after* receiving the dispatch message; if a page quotes an older `<plan>` (e.g., Approve-First or echoed text), a `flash` executor can re-run a superseded plan.
   - *Candidate fix:* Mirror Official Part 4 directly: only the `<plan>` in the latest parent dispatch message is executable; any `<plan>` text inside `Living Memory Window` pages is historical context and never executable.
4. **B4 (`P1`, Host Rule Injection Mechanics) - `@[...]` inline expansion makes workspace `orchestrator-tier:` override ambiguous** (`SKILL.md:43`, `README.md:28,42-46`, `README.zh-CN.md:28,42-46`, `engineering-kit/rules/AGENTS.md:15`):
   - Antigravity renders `@[...]` includes inline inside one `<RULE>` block without source markers, so two `orchestrator-tier:` lines in one block cannot be distinguished by file provenance alone.
   - *Candidate fix:* Add last-declaration-wins within a single rules block to `SKILL.md:43` and note placing project overrides after the `@[...]` include line (note: moving shared rules to global `~/.gemini/GEMINI.md` also cleanly separates global vs workspace blocks).
5. **B5 (`P2`, Opus + Carbon dual-confirmed) - Overloaded exit `1` risks destructive `reset --purge` + unhandled `bind` failure**:
   - Narrow `reset --purge` strictly to `corrupt|invalid state.json` stderr (or dedicated exit code), kill just-spawned ID if `bind` fails, add 3-try `15ms` `PermissionError` retry around Windows `os.replace`, and wrap `OSError` as exit `2`.
6. **B6 (`P2`) - Uncapped respawn & quota-error stall misclassification** (`harnesses.md:110,112`):
   - Route quota/API errors detected in child transcript straight to `L112`, and cap automatic respawns at `1` per user turn before reporting to user.
7. **B7 (`P2`) - Tier 1 misses already-committed executor work** (`SKILL.md:68`):
   - Include `git log --stat` for commits claimed in `<report>` alongside `git status --short` / `git diff --stat`.
8. **B8 (`P2`, Official Part 2.1 Alignment) - Direct Answer wording forbids read-only shell queries** (`SKILL.md:34` vs `L55`):
   - Narrow "zero CLI subprocess calls" to "zero `sync_memory.py` calls or disk writes" (allowing synchronous read-only commands per `B1`).
9. **B9 (`P2`, Official Part 5 Alignment) - Optional nested delegation blocked forces needless Trigger #2 hand-back** (`execution-protocol.md:58`):
   - Trigger #2 hand-back only when `<plan>` required delegation; otherwise execute the slice directly in `Execution Subagent`.
10. **B10 (`P2`) - Activation scope parity & `"waiting_for_dependents"` host state** (`SKILL.md:3` vs `L24`, `L28` vs `engineering-kit/rules/AGENTS.md:15`, `harnesses.md:86,108-110`):
    - Align `SKILL.md:3` frontmatter continuation trigger with Gate 0(b) (`L24`), align `/swarm` deference wording cleanly across `SKILL.md:28` and adoption snippets, and incorporate newly verified host `"waiting_for_dependents"` state from `manage_subagents(Action="list")` (see live probe below) into `harnesses.md` §3 & §4.

### Group C: Performance, Tests & Manifest Hardening (P2)

1. **C1 (`P2`) - `2.61s` / `50 MB` full-companion re-folding on `RESUME_EXISTING`** (`sync_memory.py:351-363, 648-675`):
   - Truncated `GENERIC` tool outputs trigger `transcript_full.jsonl` hydration even though `GENERIC` is never exported. Restrict `RESUME_EXISTING` expansion check to extractable record types at `step_idx > last_synced_step`.
2. **C2 (`P2`) - Test blind spots, relative-path validation & `plugin.json` manifest**:
   - Resolve relative `--transcript` in `transcript_location_valid` (`sync_memory.py:166-174`).
   - Add regression tests for `A1-A5` in `test_sync_memory.py`.
   - Harden `test_package_contracts.py`: assert `skills/orchestrator/SKILL.md` directly (evaluate whether to keep or drop unsupported `plugin.json` `"skills"` field), delegate host schema probe (`L201-212`) to `fold_jsonl_file`, validate `#anchor` fragments in `link_re`, and add `README.zh-CN.md` parity assertions.

### Group D: Historical Docs & ADR Drift (P1/P2)

1. **D1 (`P1`) - `ADR-0003` & `ADR-0004` drift + `ADR-0007` amendment pointer**:
   - `ADR-0003:9,11`: remove dead `tests/fixtures/`, generalize `"version"` + `"repository"`, list `README.zh-CN.md`.
   - `ADR-0004:13,17`: exclude Route 2 orphaned `execution_subagent_ids` from Direct Answer fast-path; add `"waiting_for_dependents"` / `"idle"` active-wait parity to additive user prompt guard (optionally broaden H1 without renaming file).
   - `ADR-0007:3`: add 1-line `Amendments:` note citing Ticket `10` (`v1.1.1`) and `ADR-0004` §3 / Ticket `11` (`v1.1.2`).
2. **D2 (`P1/P2`) - `spec.md` & `map.md` stale sync debt**:
   - Fix stale lines in `spec.md:73,75,81,132,140,152,164`, mark `spec.md:3` `Status: implemented (v1.1.2)` and add a frozen-archive note to `.scratch/orchestrator-design/map.md`, establishing `skills/orchestrator/* + docs/adr/ + tests/` as the single living SSOT without maintaining a 4th mirror copy.
3. **D3 (Completed in Intake) - Portable public `orchestrator/AGENTS.md`**:
   - Migrated machine-local `<local>/engineering-kit` include from public `orchestrator/AGENTS.md` to global `~/.gemini/GEMINI.md` (and evaluate dropping the `C:` link-check exemption in `test_package_contracts.py:180` during implementation).

## Open Triage Questions

1. Which protocol/architecture items (`B1-B4`, `B6-B10`) should strictly mirror Official Native Orchestrator vs remain Antigravity single-model adaptations?
2. Should `A4(b)` (non-zero-start branched chats like `5c03c8fc`) unify on fail-closed + `state.json` proof, or support inspecting `folded[min(folded)]`?
3. Should a targeted `/swarm` design review verify the exact fix design for `A1-A5` + `B1-B4` before implementing and bumping to `v1.1.3` (or squashing into `v1.1.2`)?

## Comments

- 2026-11-22 (Intake): Ticket opened at `needs-triage` following clean-slate 3-model holistic `/swarm` audit (`gemini-4-carbon-high`, `claude-opus-5-5-high`, `gemini-4-neon-xhigh`). Public `orchestrator/AGENTS.md` machine-local include migrated to global `~/.gemini/GEMINI.md`.
- 2026-11-22 (Live Host Probe - `depth=2` Cascade `kill` & `waiting_for_dependents` State): Verified **PASS** via strictly read-only live Antigravity host probes (zero workspace mutations):
  - **Probe 1 (`6b9d9b6d`, `depth=1` -> `c75619d1`, `depth=2`):** Confirmed `manage_subagents(Action="list")` natively reports **`"state": "waiting_for_dependents"`** (not `"idle"`) while a parent subagent is reactively awaiting a pending child subagent / `schedule` background task (`lastStepTime: 2026-11-22T05:30:41Z`).
  - **Probe 2 (`ef421003`, `depth=1`, `parent=7623344f` -> `4120dffe`, `depth=2`, `parent=ef421003`):**
    - `4120dffe` armed background timer `4120dffe/task-2` (`DurationSeconds=25`, `Prompt="PROBE2_CHILD_TIMER_FIRED"`) at `05:31:40Z` (deadline `05:32:05Z`) and yielded `CHILD2_ARMED` (`step_count=5`).
    - `ef421003` armed `ef421003/task-6` (`DurationSeconds=40`) at `05:31:42Z` and yielded `PARENT2_ARMED` (`step_count=9`).
    - Parent executed `manage_subagents(Action="kill", ConversationIds=["ef421003-bb46-40db-938f-acf1badaee4d"])` at `05:32:03Z -> 05:32:04Z` (before the `05:32:05Z` child deadline); host returned `"Successfully killed 1 subagent(s) and their descendants."`.
    - Audited at `05:32:32Z` (`+27s` past child deadline): `4120dffe` remained frozen at `step_count=5` (`CASCADE_RUN_STATUS_IDLE`), `4120dffe/.system_generated/tasks/task-2.log` was `0` bytes, with **zero** `PROBE2_CHILD_TIMER_FIRED` wakeup and **zero** `CHILD2_SURVIVED_PARENT_KILL` step; `ef421003` remained frozen at `step_count=9` with zero timeout wakeup.
    - **Conclusion:** Antigravity `manage_subagents(Action="kill")` empirically **does** cascade-kill `depth=2` descendants and cancel their armed background tasks (closing Opus P2 `#8`), and `manage_subagents(Action="list")` exposes native `"waiting_for_dependents"` state for reactively-waiting subagents.
- 2026-11-22 (Live Host Probe - `BgCmd` `"waiting_for_dependents"` State): Verified **PASS** via read-only live probe (`1baa9297`, running a 30s read-only `run_command` with zero child subagents and zero `schedule` timers, sampled at `t+19s`, then terminated cleanly via `kill`): `manage_subagents(Action="list")` natively reports `"state": "waiting_for_dependents"` for backgrounded commands as well, unifying all three host async wait classes (child subagents, `schedule` timers, and backgrounded `run_command`) under deterministic `"waiting_for_dependents"` vs `"idle"`/`"stopped"` detection in `harnesses.md` Sections 3 and 4.
- 2026-11-22 (Design Convergence & User Sign-Off): Following 3-model `/swarm` design convergence (`official-align-judge` `gemini-4-neon-xhigh`, `sm-seams-architect` `gemini-4-carbon-high`, `design-redteam-critic` `claude-opus-5-5-high`), locked all fixes for release `v1.1.3`: `B1` pure principle-based single-call synchronous completion (dropping rigid command-type blacklists), `B2+B7` honest attribution in Exit 3 + `git log --stat` in Tier 1 (avoiding mandatory per-turn transcript grep), `B3` latest-parent-dispatch `<plan>` rule, `B4` last-declaration-wins in single rendered rule blocks (zero edits to `engineering-kit/rules/AGENTS.md`), `B6` Option (a) (quota/API check before stall recovery or respawn, zero numeric respawn caps), `A3` `--force-spawn` for non-cancel respawns (keeping `kill -> reset` dedicated to cancel quarantine), `A4(b)` Option C (unspoofable swarm/fork `SYSTEM_MESSAGE` guard + `folded[min(folded)]` + unified fail-closed `sync`), `A5` strict-first UTF-8 EOF trim + bare `\r` normalization, `B5` `OSError` -> exit `2` + `os.replace` retry + `bind` failure kill guard, `C1` incremental `RESUME_EXISTING` companion skip, `C2` relative `--transcript` resolution + manifest/contract hardening, and `D1/D2` ADR sync + archived header markers on `spec.md`/`map.md`.
- 2026-11-22 (Implementation & Verification): Implemented all Ticket `12` (`v1.1.3`) fixes across `skills/orchestrator/scripts/sync_memory.py`, `skills/orchestrator/SKILL.md`, `skills/orchestrator/references/execution-protocol.md`, `skills/orchestrator/references/harnesses.md`, `plugin.json`, `README.md`, `README.zh-CN.md`, `docs/adr/0002`, `0003`, `0004`, `0007`, `.scratch/orchestrator-v1/spec.md`, `.scratch/orchestrator-design/map.md`, `tests/test_sync_memory.py`, and `tests/test_package_contracts.py` (leaving `README*.md` L25-31 `553 B` SSOT adoption snippets and `engineering-kit` untouched). Verified `27/27` unit tests passing (`OK`, exit `0`), `crlf=0` across all `46` repo files, `0` CJK outside `README.zh-CN.md` (and `README.md` switcher), `0` broken links/anchors, `553 B` byte parity between `README.zh-CN.md:26-30` and `engineering-kit/rules/AGENTS.md:13-17`, and `0` errors across `264` live local host transcripts (`252 SUBAGENT`, `12 TRUNK`; `5c03c8fc` -> `TRUNK`, `f84130e1` -> `SUBAGENT`).
- 2026-11-22 (Post-Implementation `/swarm` Verification): 3-model verification (`v113-code-verifier` SHIP across `267` host transcripts & `398` `USER_INPUT`s + `-52.5%` `24cd98b2` `RESUME_EXISTING` latency; `v113-protocol-redteam` Approve-First incorporated-reference exception fix in `execution-protocol.md`; `v113-doc-parity-check` `ADR-0007` `Amendments:` extension + Ticket `10` link + Ticket `12` line 85 `<local>/engineering-kit` redaction + local-path link regex guard in `test_package_contracts.py`).
