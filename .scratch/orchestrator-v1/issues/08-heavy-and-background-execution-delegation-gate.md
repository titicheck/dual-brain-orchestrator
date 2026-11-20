# 08: Dual-Session Adaptation of Official Part 2.4 Observational Commands

**What to build:** Narrow `Trunk Session`'s direct `run_command` boundary—aligned strictly with Official Orchestrator ([01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md))—so only the single cross-session physical mismatch is adapted: preserve Official Parts 2.1, 2.3 (`rerun a command`), 5.1 (`verify exactly as it specifies`), and 7 intact, while narrowing Official Part 2.4 / Part 7's `observational run_command` in `Trunk Session` strictly to fast, synchronous, lightweight read-only inspection (`git status --short`, `git diff --stat`, lightweight `git log`, quick static queries, and `sync_memory.py` after bypassing `Direct Answer Gate`) and delegating long-running or background-capable read-only commands (builds, test suites, offline benchmarks, diagnostic probe scripts, or daemons) to the bound `Execution Subagent` via `<plan>`—even when zero workspace files are modified. Keep all existing sync, dispatch, and execution mechanics (`sync_memory.py`, `execution-protocol.md`, `harnesses.md` dispatch envelopes, and parallel `Isolated Subagents`) untouched.

**Blocked by:** None (can start immediately)

**Category:** enhancement

**Status:** ready-for-agent

**References:** [GLOSSARY.md](../../../GLOSSARY.md) | [spec.md](../spec.md) | [01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md) | [05-production-telemetry-ttl-and-lifecycle-audit.md](../../../docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md)

## ADR Impact

> _Minimal dual-session adaptation of Official Part 2.4 / Part 7 ([01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md)) with a single-phrase Gate 3 alignment in [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md): in single-thread native Orchestrator, Planning Mode can run observational builds and tests without cross-session wakeups, whereas in dual-session Antigravity any backgrounded run_command binds host keep-alive/heartbeat callbacks (~56–62 min) to the invoking Trunk Session across the 300-second prompt-cache time-to-live (TTL) cliff._

This change remains fully compatible with [ADR-0006](../../../docs/adr/0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md): zero lifecycle hooks, zero sidecars, and zero `sync_memory.py` or `execution-protocol.md` changes.

## Problem & Empirical Evidence

Production telemetry in [05-production-telemetry-ttl-and-lifecycle-audit.md](../../../docs/research/05-production-telemetry-ttl-and-lifecycle-audit.md) and primary-source inspection of production session `L0-3` (`d1e362b3`) isolated a single cross-session defect from copying single-thread Official Part 2.4 directly into a dual-session harness:

1. **Exact Official Alignment Gap:** V1's `SKILL.md` copied Official Part 2.4 (`observational run_command builds, tests, or queries`) verbatim for single-thread parity, while `Direct Answer Gate` (`SKILL.md` / `README.md`) listed only file edits, state mutations, and external side effects as dispatch triggers. As a result, read-only execution scripts requiring no frontier-model reasoning mid-run—merely launching and awaiting completion—legally ran directly inside `Trunk Session`.
2. **Primary-Source `L0-3` (`d1e362b3`) Trace & `300s` Prompt-Cache TTL Cliff:** Immediately after `Execution Subagent` committed code (`96f26f6`, `8a02fee`, `d7b2fa1`, `501f1a8`), `Trunk Session` itself launched multi-hour offline benchmarks (`run_r_chain_36y_offline_bench.py`) and memory probes (`diag_4m_pid_rss.py`) directly via `run_command` at `transcript.jsonl` steps `268`, `318`, `351`, and `378`. Because Antigravity caps synchronous `run_command` waits at `10` seconds (`WaitMsBeforeAsync <= 10000 ms`), commands exceeding `10` seconds auto-background and bind host keep-alive/status heartbeat wakeups (`~56–62 min`) to the invoking `Trunk Session`. Across `04:31–12:40`, `Trunk Session` (`324k–438k` context) woke `7` times (`30` steps, `0` user inputs, `0` subagent reports); every wakeup crossed the `300`-second server KV-cache time-to-live (TTL) cliff (`cache_read_tokens = 0`, `$1.09–$1.67` each), wasting `$9.83` (`35.6%` of trunk spend) and permanently appending `~90k` tokens of polling output into `Trunk Session`'s tool-result context (`~$1.35` secondary wakeup bloat, `~$11.18` total trunk waste).
3. **Same-Session Natural Control (`07:37–08:57`) Proves Existing Execution Mechanics Need Zero Changes:** When an `80`-minute background benchmark in the exact same `L0-3` session was launched by the bound `Execution Subagent` instead—with **zero** modifications to `execution-protocol.md` or `harnesses.md`—`Trunk Session` slept undisturbed for `85` minutes (`0` intermediate wakeups, `$0.00` mid-run trunk cost, waking once on completion), while `Execution Subagent` absorbed `5` shorter host task checks (`~15 min` cadence) at `98.5%–99.2%` cache hit for `$0.73` total (`92%` cheaper) with all logs quarantined in child context.

## Settled Design (Minimal Official Part 2.4 Dual-Session Adaptation)

1. **Keep Existing Execution & Sync Mechanics Intact:** Zero edits to `sync_memory.py`, `execution-protocol.md`, or `harnesses.md` dispatch envelopes (`SPAWN_NEW` / `RESUME_EXISTING`). Deciding whether to chain tests into one command or inspect results stage-by-stage remains strictly `Trunk Session`'s natural planning choice (verified in `L0-3` `d1e362b3` steps `318`, `351`, `378`).
2. **Harness-Neutral Boundary in `SKILL.md` (Category & Execution Mode, No Hardcoded Host Seconds):**
   - **`Direct Answer Gate` (Zero-CLI Fast-Path Preserved):** Pure Q&A, explanations, and lightweight static code reviews still answer directly in `Trunk Session` with **zero** `sync_memory.py` CLI calls or disk writes. Requests requiring workspace edits, state mutations, external side effects, **or long-running / background-capable command executions** (builds, test suites, benchmarks, diagnostic probes, or daemons—even with zero file edits) bypass `Direct Answer Gate` and proceed to dispatch.
   - **`Planning Turn` Read-Only Investigation & `Approve-First`:** Replace `observational run_command builds, tests, or queries` with **fast, synchronous, lightweight read-only inspection** (prefer dedicated non-shell tools like `read_file` and static search over shell scans; restrict shell `run_command` to quick bounded checks such as `git status --short`, `git diff --stat`, lightweight `git log`, and `sync_memory.py`). Delegate builds, test suites, benchmarks, probes, and background/daemon commands to `Execution Subagent` (if an inspection command unexpectedly auto-backgrounds, do not poll/babysit it in `Trunk Session`). Under `Approve-First`, bar dispatching **mutating/edit plans** before user approval while allowing a strictly read-only diagnostic `<plan>` dispatch if planning itself requires build/test/probe output before presenting the fix plan for approval.
   - **`[plan review]` Verification Discipline:** Preserve existing single-line contract phrasing (`git status --short` / `git diff --stat` and `do **not** re-read ... re-run`). When `<report>` is incomplete, ambiguous, or inconsistent, inspect primary host logs (`transcript.jsonl` / `transcript_full.jsonl`) or targeted `read_file` first; delegate any needed heavy/background build or test re-run to `Execution Subagent` (or `reset` + `SPAWN_NEW` if the bound child is unreliable) rather than running background suites directly in `Trunk Session`.
3. **Isolate Antigravity Host Rationale in `harnesses.md` & `spec.md`:** Document Antigravity's `WaitMsBeforeAsync <= 10s` auto-backgrounding and process-owner heartbeat callback binding concisely inside `harnesses.md` (runtime bindings section, leaving `SPAWN_NEW` / `RESUME_EXISTING` envelopes untouched) and `.scratch/orchestrator-v1/spec.md`.
4. **Minimal `ADR-0004`, Bilingual `< 1,000`-Byte Snippets, & Contract Guards:**
   - Update `ADR-0004` with a single-phrase Gate 3 alignment (adding long-running/background command execution to the dispatch gate; do not dump Official Part 2.4 / `WaitMsBeforeAsync` prose into `ADR-0004`).
   - Update both `README.md` (`885` B currently) and `README.zh-CN.md` (`916` B currently) copyable `## Orchestrator` snippets to reflect long-running/background delegation and `"Before dispatch or [plan review]"` (plus its Simplified Chinese equivalent in `README.zh-CN.md`), keeping **both** strictly `< 1,000` UTF-8 bytes and preserving `README.md`'s required substrings (`conversational`, `never override`, ``bound `execution subagent` ``). Leave `Seam 2B`'s 4-point checklist unchanged.
   - Add minimal literal-substring anti-regression guards in `tests/test_package_contracts.py` covering `SKILL.md`, `harnesses.md`, and `README.md` while keeping existing single-line regex checks passing.

## Comments

- 2026-11-20 (Triage — Promoted to `ready-for-agent`):

  ## Agent Brief

  > *This was generated by AI during triage.*

  **Category:** enhancement
  **Summary:** Adapt Official Part 2.4 / Part 7 observational `run_command` boundaries for dual-session Antigravity by restricting `Trunk Session` direct shell execution to fast, synchronous, lightweight read-only inspection and delegating long-running or background-capable commands (builds, test suites, benchmarks, probes, daemons) to the bound `Execution Subagent`.

  **Current behavior:**
  `Trunk Session` orchestration instructions preserve single-thread Official Part 2.4 verbatim, allowing observational builds, tests, and read-only scripts directly in `Trunk Session` while `Direct Answer Gate` lists only edits, state mutations, and external side effects as dispatch triggers. Under Antigravity's `10`-second `WaitMsBeforeAsync` ceiling, any command exceeding `10` seconds transitions to an async background process whose host heartbeat wakeups (`~56–62 min`) and terminal outputs return to the invoking `Trunk Session`, repeatedly forcing cold KV-cache reloads past the `300`-second server time-to-live (TTL) cliff and bloating trunk tool-result context. Meanwhile, `[plan review]` permits re-running test suites directly in `Trunk Session` when a `<report>` is ambiguous or incomplete.

  **Desired behavior:**
  - `Direct Answer Gate` preserves its zero-CLI fast path for pure Q&A, explanations, and lightweight static code reviews, while routing requests that require edits, state mutations, external side effects, or long-running / background-capable command execution (builds, test suites, benchmarks, diagnostic probes, daemons—even with zero workspace edits) to dispatch.
  - During `Planning Turn` investigation, `Trunk Session` prefers dedicated non-shell tools (`read_file`, static search) and limits direct shell `run_command` calls strictly to fast, synchronous, lightweight read-only inspection (such as `git status --short`, `git diff --stat`, lightweight `git log`, and `sync_memory.py`); builds, test suites, benchmarks, probes, and background/daemon commands are delegated via `<plan>` to `Execution Subagent`, and if a shell inspection command unexpectedly auto-backgrounds, `Trunk Session` does not poll or babysit it.
  - Under `Approve-First`, dispatching mutating or edit plans before user approval remains prohibited, while a strictly read-only diagnostic `<plan>` dispatch is permitted when planning itself requires build, test, or probe output before presenting an implementation plan for approval.
  - During `[plan review]`, existing lightweight footprint verification and single-line contract phrasing remain intact; when `<report>` is incomplete, ambiguous, or inconsistent, `Trunk Session` inspects primary host logs (`transcript.jsonl` / `transcript_full.jsonl`) or targeted `read_file` first and delegates any needed heavy/background build or test re-run to `Execution Subagent` (resetting and respawning if the bound child is unreliable) rather than running background suites in `Trunk Session`.
  - Host-specific rationale (`WaitMsBeforeAsync <= 10s` auto-backgrounding and process-owner heartbeat binding) is isolated to the Antigravity runtime bindings documentation and feature spec without leaking host constants into `SKILL.md`, while all existing sync, dispatch envelope, and execution-protocol behaviors remain unchanged.

  **Key interfaces:**
  - `orchestrator` skill entry and planning/review contracts (`Direct Answer Gate`, `Planning Turn`, `Approve-First`, and `[plan review]`): narrow observational `run_command` to fast synchronous lightweight read-only inspection and delegate heavy/background executions via `<plan>` without breaking existing contract regexes.
  - Antigravity runtime bindings documentation and feature specification: document `WaitMsBeforeAsync <= 10s` auto-backgrounding and process-owner heartbeat binding in runtime bindings only, leaving `SPAWN_NEW` / `RESUME_EXISTING` dispatch envelopes unchanged.
  - Coexistence boundary ADR (`ADR-0004` Gate 3): add a single-phrase alignment extending the dispatch gate to long-running or background command execution.
  - Bilingual adoption documentation (`## Orchestrator` copyable adoption snippets in English and Simplified Chinese): update delegation and `"Before dispatch or [plan review]"` wording while keeping both snippets strictly under `1,000` UTF-8 bytes and leaving `Seam 2B`'s 4-point checklist unchanged.
  - Package contract test suite: add minimal literal-substring anti-regression assertions covering the updated skill, runtime bindings, and English adoption snippet alongside existing single-line regex checks.

  **Acceptance criteria:**
  - [ ] `Direct Answer Gate` preserves zero-CLI direct replies for pure Q&A/static reviews while routing long-running or background-capable command requests (even with zero edits) to dispatch, and `Planning Turn` restricts direct `Trunk Session` `run_command` calls to fast synchronous lightweight read-only inspection (no hardcoded host seconds in `SKILL.md`).
  - [ ] `Approve-First` bars mutating/edit dispatches before approval while permitting read-only diagnostic `<plan>` dispatches when planning requires heavy/background command output, and `[plan review]` inspects host transcripts or delegates heavy/background re-runs to `Execution Subagent` while keeping existing contract regexes green.
  - [ ] Runtime bindings documentation and feature spec record Antigravity's `WaitMsBeforeAsync <= 10s` auto-backgrounding and heartbeat-owner binding without modifying `SPAWN_NEW` / `RESUME_EXISTING` dispatch envelopes, and `ADR-0004` Gate 3 receives a minimal single-phrase alignment.
  - [ ] Both English and Simplified Chinese `## Orchestrator` copyable adoption snippets reflect long-running/background delegation and `"Before dispatch or [plan review]"` (and its Simplified Chinese equivalent), each remaining strictly under `1,000` UTF-8 bytes with `Seam 2B` unchanged.
  - [ ] Minimal literal-substring anti-regression guards are added to the package contract test suite, and `py -3 -m unittest discover -s tests -v` passes with zero CJK or relative link regressions.

  **Out of scope:**
  - Modifying `sync_memory.py`, `execution-protocol.md`, or `harnesses.md` `SPAWN_NEW` / `RESUME_EXISTING` dispatch envelopes (or modifying `~30`-turn interim reporting / daemon protocols).
  - Forcing multi-stage verification or benchmark queues to be batched into a single dispatch (chaining vs stage-by-stage inspection remains `Trunk Session`'s natural planning choice).
  - Modifying `Seam 2B`'s 4-point checklist or parallel `Isolated Subagents`.
  - Bidirectional child-side rotation / idle-TTL timers (closed `wontfix` in Ticket `07` and recorded in `.out-of-scope/`).
  - Introducing lifecycle hooks (`PreToolUse`), sidecars, or workflow-carrier swaps (`run_workflow`).
  - Synchronizing downstream `engineering-kit` or project `AGENTS.md` files (tracked as a separate post-merge follow-up).
