# 08: Session-Bound Command Ownership (Official Baseline Alignment)

**What to build:** Implement [ADR-0007](../../../docs/adr/0007-session-bound-command-ownership.md) across `SKILL.md`, `execution-protocol.md`, `harnesses.md`, `spec.md`, and `tests/test_package_contracts.py` by enforcing one symmetric invariant—no session yields control while a command it started is still running—plus the three-tier `[plan review]` verification ladder within the pure Three-Way Exit, while leaving Official Part 2.1 (`Direct Answer Gate`), `README.md` / `README.zh-CN.md` snippets, `ADR-0004`, `Approve-First`, `sync_memory.py`, and `Seam 2B` untouched.

**Blocked by:** None (can start immediately)

**Category:** enhancement

**Status:** resolved

**References:** [GLOSSARY.md](../../../GLOSSARY.md) | [spec.md](../spec.md) | [ADR-0007](../../../docs/adr/0007-session-bound-command-ownership.md) | [01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md) | [05-production-telemetry-ttl-and-lifecycle-audit.md](../../../docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md) | [SKILL.md](../../../skills/orchestrator/SKILL.md) | [execution-protocol.md](../../../skills/orchestrator/references/execution-protocol.md) | [harnesses.md](../../../skills/orchestrator/references/harnesses.md) | [test_package_contracts.py](../../../tests/test_package_contracts.py)

*Terminology note:* `Seam 2B` refers to the 4-point live smoke checklist in [README.md](../../../README.md).

## Problem & Verified Evidence

1. Official Orchestrator ([01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md)) runs planning and execution inside one thread, where Part 2.4 (`observational run_command builds, tests, or queries`) and Part 7 (`run observational commands if needed to check`) never create cross-session process ownership issues. Across two sessions, leaving a command running when a session yields binds host completion or status wakeups to the invoking session.
2. Verified `L0-3` (`d1e362b3` + child `2581ba32`): inside four Route 1 `[plan review]` turns—`Trunk Session` steps `268` (`00:57:15Z`, matching child `1276`), `318` (`03:03:27Z`, matching child `1298`), `347..351` (`04:40:26Z` `git show --stat d7b2fa1` after child `1339`, then `04:40:59Z` benchmark launch at step `351`), and `378` (`06:10:03Z`, matching child `1362`)—`Trunk Session` launched `offline_bench.py` directly (using `WaitMsBeforeAsync: 500`, under Antigravity's `10000 ms` synchronous cap), and in separate post-failure turns (`steps 273, 326, 331`) launched memory probes (`diag_memory_probe.py`, `diag_pid_rss.py`). Across `04:31–12:40 +08:00`, these launches produced `7` post-TTL (`> 300s`) cold-cache `Trunk Session` wakeups (including benchmark completion/failure wakeups after `~56m`, `~63m`, and `~78m`), wasting `$9.83` (`cache_read_tokens = 0`) plus `~90k` polling/tool tokens (`~$11.18` total trunk waste).
3. Verified same-session control (`2026-11-19T23:37Z` to `2026-11-20T00:57Z`, i.e., `07:37–08:57 +08:00`, child `2581ba32` steps `1222..1276`, prior to `Trunk Session` step `268`): while `Execution Subagent` owned an `80`-minute series of `~15-min` `pytest` suites and debugging edits (`task-1222` through `task-1268`), `Trunk Session` saw `0` intermediate wakeups (`$0.00` mid-run trunk cost) and child checks cost `$0.73` (`98.5%–99.2%` cache hit).

## Official Part 1–9 Alignment

| Official Part | Status / Dual-Session Adaptation |
|---|---|
| **1. Reactive wakeup & control loop** | **Ticket `08` delta:** Fourth cross-session physical rule (ADR-0007): declare the global `Trunk Session` command-ownership invariant at top-level `SKILL.md` scope (covering Step 6, Planning Turn, and `[plan review]`): neither session yields while a command it started is still running. |
| **2.1 Direct Answer Gate** | **Unchanged:** `SKILL.md` Step 6 already keeps zero CLI calls on pure Q&A and routes state-changing or command-executing requests into Planning Mode; the top-level invariant covers Step 6 as well. `README.md` / `README.zh-CN.md` snippets stay untouched. |
| **2.2 Approve-First** | **Unchanged.** |
| **2.3 Depth Matching** | **Unchanged.** |
| **2.4 Investigation** | **Ticket `08` delta:** Keep Official Part 2.4 observational read-only commands in `Trunk Session` constrained strictly by the invariant—every command `Trunk Session` starts must complete before `Trunk Session` yields (terminate any started command that does not finish before yielding, and delegate instead). Note under `<plan>` authoring that work expected not to finish before yielding goes into `<plan>` and persistent services cannot outlive a dispatch. |
| **2.5 Asking questions** | **Ticket `08` delta (covered by top-level invariant):** Never leave a started observational command running when `Trunk Session` stops to ask the user a question. |
| **3. Handoff / `exit_plan_mode`** | **Adapted in V1 (`ADR-0001` / `ADR-0002`); Ticket `08` note:** Native dispatch replaces same-thread handoff; `ADR-0007` notes persistent services cannot outlive a dispatch. |
| **4. Subagent entry & safety** | **Ticket `08` delta:** Reinforce under `execution-protocol.md` that `Execution Subagent` awaits terminal states of started commands (or terminates them on hand-back) before exiting to parent. |
| **5.1 Ordered execution & reporting** | **Ticket `08` delta:** Report only after every started command reaches a terminal state (terminating any still-running or persistent service before reporting); waiting on an active command is not an exit to parent. |
| **5.2 Small deviations** | **Unchanged.** |
| **5.3 Early hand-back triggers** | **Ticket `08` delta:** Replace `"Stop immediately and deliver <report>"` with `"Stop plan work immediately, terminate any still-running command you started, and deliver <report>"`. |
| **5.4 `<report>` contract** | **Adapted in V1 (`ADR-0001`); Ticket `08` note:** Unchanged format; `<report>` is emitted only once started commands have reached a terminal state or been terminated. |
| **5.5 User reply / return** | **Adapted in V1 (`ADR-0001`); unchanged in Ticket `08`.** |
| **6. `~30`-turn cadence** | **Ticket `08` delta (counting unchanged):** A still-running command is never a safe boundary for pausing to send an interim `~30`-turn `<report>`. |
| **7. `[plan review]`** | **Ticket `08` delta:** Three-tier verification ladder within the pure Three-Way Exit: Tier 1 (clean `<report>`) runs lightweight footprint check only; Tier 2 (incomplete/ambiguous/inconsistent) inspects child `transcript.jsonl` per `harnesses.md` plus targeted reads first; Tier 3 (confirmed missing/wrong/unverified) runs sync-finishing check in `Trunk Session` or dispatches via Exit 1/2 to `Execution Subagent` (using `harnesses.md` §4 `reset` + respawn if unresponsive/unrevivable). Same never-yield-with-running-command invariant applies. |
| **8. Host primitives** | **Ticket `08` delta:** `harnesses.md` Section 1 records Antigravity's `WaitMsBeforeAsync <= 10000 ms` cap, auto-backgrounding, session-owned wakeups, practical consequence for `Trunk Session`, tool-agnostic termination, and sibling `transcript_full.jsonl` template; Section 3 mirrors the terminal-state / terminate-before-report reminder in **both** `SPAWN_NEW` and `RESUME_EXISTING`; Section 5 notes client-specific command timeout limits belong in `harnesses.md`. |
| **9. Storage & compaction** | **Adapted in V1 (`ADR-0002`); unchanged in Ticket `08`** (`harnesses.md` Section 3 notes child may not re-read protocol after compaction). |

## Comments

- 2026-11-20 (Triage):

  > *This was generated by AI during triage.*

  ## Agent Brief

  **Category:** enhancement
  **Summary:** Implement [ADR-0007](../../../docs/adr/0007-session-bound-command-ownership.md) symmetric session-bound command ownership and the three-tier `[plan review]` verification ladder within the pure Three-Way Exit while keeping Official Part 2.1, `README` snippets, `ADR-0004`, and `sync_memory.py` untouched.

  **Current behavior:**
  `Trunk Session` investigation and `[plan review]` permit leaving observational commands running past turn exit (binding Antigravity completion/status wakeups to `Trunk Session`) and leave an `"unless <report> is incomplete, ambiguous, or inconsistent"` loophole encouraging direct test re-runs before inspecting host-recorded child logs. `Execution Subagent` protocol instructs `"Stop immediately and deliver <report>"` without requiring started commands to reach a terminal state or be terminated before reporting, and `harnesses.md` does not record Antigravity's `WaitMsBeforeAsync <= 10000 ms` command-ownership behavior or sibling `transcript_full.jsonl` path.

  **Desired behavior:**
  1. **`Trunk Session` (`SKILL.md` top-level invariant, Planning Turn & `<plan>` authoring):** Declare the global `Session-Bound Command Ownership Invariant` at top-level `SKILL.md` scope under `Prompt Precedence` (covering all `Trunk Session` turns: Step 6, Planning Turn, and `[plan review]`). Retain Official Part 2.4 observational read-only commands constrained strictly by the invariant—`Trunk Session` never yields its turn while a command it started is still running (terminate any started command that does not finish before yielding, and delegate instead). Note under `<plan>` authoring that work expected not to finish before yielding goes into `<plan>` and persistent services cannot outlive a dispatch. Keep `Direct Answer Gate` (Step 6) and `Approve-First` unchanged.
  2. **`Trunk Session` (`SKILL.md` `[plan review]` three-tier verification ladder):**
     - Tier 1 (clean `<report>`): lightweight footprint check only (`git status --short` / `git diff --stat`), never re-reading every modified file or re-running passing test suites;
     - Tier 2 (incomplete, ambiguous, or inconsistent `<report>`): inspect the bound child's host-recorded `transcript.jsonl` per `references/harnesses.md` plus targeted file reads first—zero re-runs if host logs confirm execution passed;
     - Tier 3 (confirmed missing, wrong, or unverified work): run an observational check in `Trunk Session` only if it finishes before yielding, or dispatch missing/additional verification via Exit 1/2 to `Execution Subagent` (using existing `harnesses.md` §4 `reset` + respawn recovery if the bound child is unresponsive or unrevivable). Maintain the invariant (never yield with a started command still running) and keep existing single-line contract phrases (`git status --short ... git diff --stat` and `do **not** re-read ... re-run`) on one line.
  3. **`Execution Subagent` (`execution-protocol.md` Sections 2, 4, 5, 6):** Clarify that awaiting an active command's completion is not an exit to the parent; send `<report>` only after every started command reaches a terminal state (terminating any still-running or persistent service before reporting); in Section 4, reword `"Stop immediately and deliver <report>"` to `"Stop plan work immediately, terminate any still-running command you started, and deliver <report>"`; in Section 5, state that a still-running command is never a safe boundary for the `~30`-turn interim report (keep counting mechanics unchanged). Keep termination phrasing tool-agnostic.
  4. **Antigravity runtime bindings (`harnesses.md` Sections 1, 3, 5):** Broaden Section 1 heading (`Path, Python & Command Ownership on Antigravity`), document Antigravity's `WaitMsBeforeAsync <= 10000 ms` synchronous wait cap, auto-backgrounding, session-owned completion/status wakeups, practical consequence for `Trunk Session` (longer builds, test suites, benchmarks, and probes go into `<plan>`), tool-agnostic termination before yield, and sibling `transcript_full.jsonl` template alongside `transcript.jsonl` (preserving the two single-line `never read_file` regex guards). Mirror the concise terminal-state / terminate-before-report reminder in **both** `SPAWN_NEW` and `RESUME_EXISTING` envelopes (Section 3). Add one phrase in Section 5 noting client-specific command timeout/async limits stay in `harnesses.md`.
  5. **Specification (`.scratch/orchestrator-v1/spec.md`):** Align `Solution`, `9-Part Structural Preservation`, `Planning Turn`, `Execution Turn`, `[plan review]`, and `Further Notes` with `ADR-0007` (recording the fourth dual-session physical adaptation and Antigravity's `WaitMsBeforeAsync <= 10000 ms` limit in `Further Notes`).
  6. **Contract tests (`tests/test_package_contracts.py`):** Add minimal literal-substring guards verifying: `SKILL.md` and `execution-protocol.md` contain no host constants (`WaitMsBeforeAsync`, `10000`); `harnesses.md` contains `WaitMsBeforeAsync`; `SKILL.md` encodes the top-level never-yield-with-running-command invariant and three-tier `[plan review]` verification; `execution-protocol.md` and `harnesses.md` encode terminal-state / terminate-before-report; all existing single-line regexes, frontmatter single-line `description:`, zero-CJK (outside `README.zh-CN.md`), and relative-link hygiene checks pass. Do not add links pointing outside `skills/orchestrator/` from files inside `skills/orchestrator/`.

  **Key interfaces:**
  - `SKILL.md`: top-level `Prompt Precedence` invariant, Planning Turn investigation + `<plan>` authoring note, `[plan review]` three-tier ladder + invariant.
  - `execution-protocol.md`: Sections 2, 4, 5, and 6.
  - `harnesses.md`: Section 1 host command ownership & sibling logs, Section 3 both `SPAWN_NEW` and `RESUME_EXISTING` envelopes, and Section 5 adapter seam.
  - `spec.md`: `Solution`, `9-Part Structural Preservation`, `Planning Turn`, `Execution Turn`, `[plan review]`, and `Further Notes`.
  - `tests/test_package_contracts.py`: `EXECUTION_PROTOCOL_MD` + `test_session_bound_command_ownership_contracts`.

  **Acceptance criteria:**
  - [x] `SKILL.md` preserves Official Part 2.1 (`Direct Answer Gate`), `Approve-First`, and single-line contract regex phrases (`git status --short ... git diff --stat`, `do **not** re-read ... re-run`, single-line `description:`), while encoding the top-level never-yield-with-running-command invariant, `<plan>` persistent-service note, and the three-tier `[plan review]` verification ladder within the pure Three-Way Exit.
  - [x] `execution-protocol.md` Sections 2, 4, 5, and 6 state terminal-state-before-report, tool-agnostic terminate-before-hand-back, waiting-is-not-an-exit, and that a still-running command is not a safe `~30`-turn boundary (with `~30`-turn counting unchanged).
  - [x] `harnesses.md` Section 1 records `WaitMsBeforeAsync <= 10000 ms`, session-owned wakeups, practical `Trunk Session` consequence, tool-agnostic termination, and sibling `transcript_full.jsonl` template (keeping existing `never read_file` regexes intact); Section 3 adds the terminal-state / terminate-before-report reminder to **both** `SPAWN_NEW` and `RESUME_EXISTING`; Section 5 notes host command timeout/async limits stay in `harnesses.md`.
  - [x] `SKILL.md` and `execution-protocol.md` contain no host constants (`WaitMsBeforeAsync`, `10000`) and no relative links escaping `skills/orchestrator/`.
  - [x] `spec.md` (`Solution`, `9-Part Structural Preservation`, `Planning Turn`, `Execution Turn`, `[plan review]`, `Further Notes`) is aligned with `ADR-0007`.
  - [x] `tests/test_package_contracts.py` adds minimal literal-substring guards for the contracts above, and `py -3 -m unittest discover -s tests -v` passes with zero CJK (outside `README.zh-CN.md`) and zero broken relative links.

  **Out of scope:**
  - `SKILL.md` Step 6 (`Direct Answer Gate`), `Approve-First`, `README.md` / `README.zh-CN.md` adoption snippets, `Seam 2B` checklist, and `ADR-0004`.
  - `sync_memory.py`.
  - Redefining `~30`-turn counting mechanics.
  - Any new subagent rotation or reset path (Ticket `07` is `wontfix`).
  - `Isolated Subagent` tier/memory changes.
  - Lifecycle hooks, sidecars, or workflow carriers.
  - Downstream `engineering-kit` or project `AGENTS.md` edits.

- 2026-11-20 (Implementation & Verification): Converged on Choice 2 (pure Three-Way Exit `[plan review]` without an `Isolated Subagent` branch in Tier 3, paired with top-level `Session-Bound Command Ownership Invariant` in `SKILL.md`). Implemented across `SKILL.md`, `execution-protocol.md`, `harnesses.md`, `spec.md`, and `tests/test_package_contracts.py`, updated `ADR-0007` and `docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md`, and verified with `py -3 -m unittest discover -s tests -v` (`19/19` passing).
