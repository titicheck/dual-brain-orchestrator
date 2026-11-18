# Orchestrator V1 Specification

Status: ready-for-agent

## Problem Statement

Developers working in single-model agent sessions—such as frontier reasoning models selected directly in an IDE or CLI agent—lack the built-in two-phase planning and execution scheduling of the native Antigravity Orchestrator. Without that separation, every mechanical file edit, command run, test iteration, and multi-step implementation turn runs directly inside the primary session on the expensive frontier model, burning scarce quota, bloating the planning context window with raw tool output, and blurring architectural decision-making with execution trial-and-error. Conversely, naive delegation to generic subagents loses the living conversational context that native same-thread model hot-swapping preserves, risks recursive planning loops when workspace or plugin rules propagate into child subagents, and risks execution-tier drift if global conversational mentions alter the execution model.

## Solution

Deliver a portable, unified `orchestrator` plugin and skill package that preserves the Official Orchestrator system verbatim everywhere except the single structural change forced by cross-session separation: replacing same-thread model hot-swapping with lossless interop between a planning `Trunk Session` and a client-native `Execution Subagent`. On hosts supporting plugin-level rules, enabling the plugin activates two-phase orchestration globally across top-level sessions with the `Execution Subagent` strictly locked to the default `flash` execution tier (while disabling it incurs zero token cost); manual `/orchestrator` invocation across all supported harnesses defaults to the fast execution tier and permits scoped execution-tier overrides for that invocation. Whenever a request requires workspace edits or external side effects, the `Trunk Session` investigates read-only on the user's main model, authors an Official-compliant `<plan>`, synchronizes its compaction-bounded `Living Memory Window` via a zero-LLM standard-library CLI where local transcripts exist, and dispatches execution to its bound `Execution Subagent`. Every completion, ~30-step checkpoint, or early hand-back returns Official Orchestrator's five-part `<report>` into the unmodified three-way `[plan review]` gate, while parallel `Isolated Subagents` invoked by other plugins or skills remain completely untouched.

## User Stories

1. As a developer using a pure single-model session on Antigravity with the `orchestrator` plugin enabled, I want two-phase Plan/Execute scheduling to engage automatically on top-level requests with the `Execution Subagent` strictly locked to `flash`, so that global behavior matches Official Orchestrator without conversational model drift.
2. As a developer who temporarily wants unmediated single-model execution, I want disabling the `orchestrator` plugin in host settings to unload both its routing rule and skill definitions completely, so that disabled state consumes zero context tokens.
3. As a developer invoking `/orchestrator` manually (on standalone skill installs, on Claude Code or Codex, or for a single turn), I want execution to default to the fast tier while allowing explicit tier selection (`pro`, `flash_lite`, `inherit`, or harness equivalents) scoped strictly to that invocation, so that custom tier overrides occur only when intentionally requested and automatically rotate back on subsequent global turns.
4. As a developer already running inside the host's native Orchestrator mode, I want the global routing rule to detect exact lowercase `exit_plan_mode` or `enter_plan_mode` tools and yield silently, so that native same-thread hot-swapping runs without redundant subagent layers unless I explicitly invoke `/orchestrator`.
5. As a developer spawning child subagents in a workspace where the `orchestrator` plugin rule is active, I want activation anchored strictly to human-initiated session origin (`step 0`) and absent from subagent role prompts, so that child subagents never recurse into Plan/Execute loops while `Trunk Session` return wakeups still enter `[plan review]` normally.
6. As a developer asking a pure question, requesting an explanation, or asking for a read-only review that modifies nothing, I want the `Trunk Session` to answer directly in Plan Mode without spawning an `Execution Subagent`, matching Official Orchestrator's Direct Answer Gate.
7. As a developer sending a small follow-up whose steps are already settled in conversation (applying an approved tweak, rerunning a command, fixing a typo), I want the `Trunk Session` to skip redundant investigation and dispatch a concise one-to-two-sentence `<plan>` immediately, matching Official Orchestrator's Depth Matching rule.
8. As a developer requesting a non-trivial feature or refactor, I want the `Trunk Session` to investigate strictly read-only, resolve every ambiguity upfront, and author a complete `<plan>` (ordered steps, exact targets and changes, verification commands and expected outputs, pitfalls, and a task-specific `Re-plan if:` list), so that the `Execution Subagent` never guesses design decisions.
9. As a developer asking to inspect or approve a plan before changes are made, I want the `Trunk Session` to present the plan and stop without spawning an `Execution Subagent`, matching Official Orchestrator's Approve-First Exception.
10. As a developer handing off a `<plan>` on Antigravity, I want a newly spawned `Execution Subagent` to inherit the `Trunk Session`'s active `Living Memory Window`—retaining compaction summaries, stripped user prompts, visible assistant replies, and prior `<report>` blocks while omitting raw tool outputs, non-report system notices, and private reasoning—stored inside a session-isolated scratch directory outside my git repository.
11. As a developer who edits, retries, or rewinds earlier turns in a conversation, I want the synchronization CLI to fold append-only logs by canonical `step_index` and detect prefix-digest or watermark regressions, so that rewound sessions automatically rotate to a fresh `Execution Subagent` instead of resuming a poisoned conversation branch.
12. As a developer whose `Living Memory Window` contains large messages or exceeds host single-read limits, I want exported pages cleared per sync and split deterministically under 40,000 UTF-8 bytes (falling back from message/line splits to valid UTF-8 character boundaries on oversized single lines), so that every page reads cleanly in one call without stale leftover pages.
13. As a developer iterating across multiple execution turns within the same compaction epoch and tier, I want `RESUME_EXISTING` to advance watermarks in a single CLI call and export only `(last_synced_step .. current_step]` (or `delta_empty = true`), while offering a `reset` command if a bound subagent was terminated externally.
14. As a developer crossing a host context compaction boundary, I want any change in `checkpoint_step` to leave the previous `Execution Subagent` idle at zero token cost and spawn a fresh `Execution Subagent` seeded from `[latest CHECKPOINT .. current_step]`.
15. As a developer running a frontier model in my `Trunk Session`, I want model offloading applied exclusively to the bound `Execution Subagent`, and if that execution model hits quota exhaustion or an error, I want the `Trunk Session` to inspect workspace status and subagent logs and report to me rather than silently switching models.
16. As a developer delegating execution, I want the `Execution Subagent` to handle minor mechanical deviations autonomously (slightly moved target, obvious missing import, rerunning a flaky test once) while treating an initial failure plus one failed retry as "failed twice" that belongs back on the `Trunk Session`.
17. As a developer delegating a long `<plan>`, I want the `Execution Subagent` to self-count roughly 30 LLM turns per dispatch and pause with an interim five-part status `<report>`, matching Official Orchestrator's scheduled review cadence.
18. As a developer whose `<plan>` hits any of Official Orchestrator's five early hand-back conditions—step/verification failed twice, false plan assumption, unchosen approach decision, unrequested out-of-plan edits/work, or any sign listed in `Re-plan if:`—I want the `Execution Subagent` to stop immediately and return `<report>` without improvising.
19. As a developer receiving an `Execution Subagent` `<report>`, I want the `Trunk Session` in `[plan review]` to review without carrying out the plan itself and take Official Orchestrator's exact three-way exit (continue remaining steps, send a revised plan stating what to undo / do instead / verify, or report verified completion/stop to me).
20. As a developer diagnosing a subtle execution issue, I want the `Trunk Session` to read the host's native subagent trajectory log URI on demand only when raw command output is needed.
21. As a developer invoking other plugins or skills that spawn `Isolated Subagents` from the `Trunk Session`, I want `orchestrator` to leave them completely parallel and untouched—zero `Living Memory Window` injection and zero model overrides—while nested workers spawned inside an active `Execution Subagent` naturally inherit and cap at the execution tier.
22. As a developer explicitly invoking `/swarm` in a conversation, I want `orchestrator` to yield for that active `/swarm` workflow without checking or being permanently blocked by leftover swarm files on disk (which can simply be deleted).
23. As a developer using `/orchestrator` on Claude Code or Codex where Antigravity's transcript log is absent, I want orchestration to rely cleanly on the self-contained `<plan>` plus native stateful subagent resumption without wasting frontier tokens rewriting conversation history by hand.
24. As a maintainer validating the repository, I want zero-dependency Python standard-library `unittest` suites covering both the synchronization CLI (`Seam 1`) and multi-harness package/rule contracts (`Seam 2`).

## Implementation Decisions

### 1. Unified Package Identity and Dual-Mode Tier Authority
- Both the plugin identifier and skill identifier are `orchestrator`. All runtime skill assets reside inside one self-contained skill directory enclosed by root multi-harness manifests, user documentation, a concise global routing rule, and standard-library test suites, with zero startup shell hooks and zero background processes.
- Activation modes and tier governance:
  1. **Antigravity Plugin Mode (Global Default Switch — Locked `flash` Tier)**: Enabling the plugin automatically loads the global routing rule (`<24,000` bytes), engaging two-phase orchestration on qualifying top-level conversations with the bound `Execution Subagent` **strictly locked** to `Model: "flash"` and ignoring conversational model mentions to prevent drift; disabling unloads all assets at zero token cost.
  2. **Manual `/orchestrator` Skill Mode (All Harnesses — Scoped Tier Override)**: Standalone skill installs and Claude Code / Codex plugin installs (which do not auto-inject plugin rules globally without hooks) activate on demand via `/orchestrator`. Manual invocation defaults to the fast execution tier (`"flash"` on Antigravity, `"sonnet"` on Claude Code, allowlisted fast execution model + `reasoning_effort: "medium"` on Codex) and permits explicit tier overrides (`"pro"`, `"flash_lite"`, `"inherit"`, or harness equivalents) scoped strictly to that invocation.

### 2. Scope Guards, Native Deference, and Session-Origin Non-Recursion
- **Prompt Precedence (Official Part 1)**: Where two-phase orchestration rules conflict with generic investigate-then-edit habits, two-phase orchestration wins; it **never** overrides safety guidelines, user instructions, or tool permissions.
- **Native Orchestrator & Active `/swarm` Deference**: Under the global routing rule, if exact lowercase `exit_plan_mode` or `enter_plan_mode` tools are declared (distinguished case-sensitively from Claude Code's `EnterPlanMode`/`ExitPlanMode`), yield silently to native Orchestrator unless the user explicitly invoked `/orchestrator` (in which case dispatch directly to the `Execution Subagent` without calling `exit_plan_mode`). Yield likewise when the user explicitly invokes `/swarm` for the active task; never inspect leftover swarm directories on disk to suppress orchestration (stale swarm directories may simply be deleted).
- **Session-Origin Non-Recursion Guard (`step 0`)**: Global activation checks the conversation's **initial turn (`step 0`)**, NOT mid-session return wakeups:
  - A session whose `step 0` is a direct human `<USER_REQUEST>` (`USER_INPUT`) is a `Trunk Session`—subsequent inter-agent `<SYSTEM_MESSAGE>` wakeups returning `<report>` enter `[plan review]` normally.
  - Any session whose `step 0` is an inter-agent `<SYSTEM_MESSAGE>` (`[Message] timestamp=... sender=<parent_uuid> ...` or `[swarm]`/`[board]` assignment), or whose prompt carries the single-phase `[EXECUTION SUBAGENT — SINGLE PHASE]` header (used across all harnesses), treats the global rule as a strict no-op and runs single-phase.

### 3. Verbatim Official Orchestrator Planning and Execution Protocol
- **Planning Turn (`Trunk Session` — Official Part 2)**:
  - Starts on every user message and every inbound `<report>`.
  - **Direct Answer Gate**: Do not spawn an `Execution Subagent` when the request needs nothing done (a question, a read-only review, an explanation)—answer directly and stop. Anything that edits files, mutates state, or causes external effects goes to the `Execution Subagent`, however small.
  - **Approve-First Exception**: If the user asked to see or approve the plan first, present it and stop.
  - **Depth Matching**: Settled small follow-ups skip investigation and dispatch a 1–2 sentence `<plan>` immediately; non-trivial tasks investigate strictly read-only (`read_file`, search, observational `run_command` builds/tests/queries) and produce a full self-contained `<plan>` (ordered steps, target symbols/locations, exact changes, verification commands + expected outputs, pitfalls, Non-Override Safety Clause, and closing `Re-plan if:` list).
- **Execution Turn (`Execution Subagent` — Official Parts 4, 5, 6)**:
  - Carries out the most recent `<plan>` in order without re-planning.
  - **Small Deviations (Official Part 5.2)**: Handles minor mechanical deviations autonomously (slightly moved target, obvious missing import, rerunning a flaky test **once**). First failed attempt belongs to the `Execution Subagent`; **the second belongs to the `Trunk Session`** (initial failure + one failed retry = "failed twice").
  - **Five Early Hand-Back Triggers (Official Part 5.3 Verbatim)**: Stop immediately and return `<report>` whenever:
    1. A verification or step specified by the plan has failed twice;
    2. Something the plan assumed is missing or behaves differently;
    3. Continuing requires choosing between approaches the plan did not choose;
    4. Continuing requires editing files or doing work the plan did not name;
    5. Any sign in the plan's own `Re-plan if:` list appears.
  - **Scheduled Review Cadence (Official Part 6)**: Self-counts LLM turns per dispatch and pauses after ~30 turns to return an interim five-part status `<report>`.

### 4. Parallel Orthogonality with Isolated Subagents
- `Execution Subagent` and plugin/skill `Isolated Subagents` are parallel channels from the `Trunk Session`: `orchestrator` applies `Living Memory Window` synchronization and execution-tier locking **solely** to its single bound `Execution Subagent`, imposing zero memory injection, zero model overrides, and zero special-case routing on `Isolated Subagents`.
- Nested subagents spawned from inside an active `Execution Subagent` (`depth = 1`) on nested-capable hosts (Antigravity `self` and Claude Code default depth 3) naturally inherit and cap at the execution model via `inherit`; if a runtime environment disables nested subagent tools inside a child subagent, Trigger #2 hands back to the `Trunk Session`.

### 5. Deterministic Living Memory Synchronization CLI Contract
- Implemented using only the Python 3 standard library; session state lives inside the Antigravity conversation's isolated per-session scratch subdirectory outside git workspaces.
- **CLI Subcommands & Exit Codes** (`0` = success; `1` = invalid CLI arguments/state; `2` = missing/unreadable transcript):
  1. `sync --transcript <path> --state-dir <dir> [--tier <str>]` (default `--tier flash`):
     - Folds JSONL records (`step_index: int`, `type: str`, `source: str`, `content: str`, optional `truncated_fields: list[str]`) by canonical `step_index` (later record at `k` invalidates earlier records at `>= k`, skipping trailing partial lines if mid-flush).
     - Resolves the sibling companion full-log JSONL file **only** when `"content"` is in `truncated_fields` on a retained step (ignoring `thinking`/`tool_calls` truncation), matching by line index first then `(step_index, type)` fallback.
     - Retains within `[max(0, latest_checkpoint_step) .. max_step]`: `CHECKPOINT` `content`; `USER_INPUT` inner `<USER_REQUEST>` body (stripping `<ADDITIONAL_METADATA>` and `<USER_SETTINGS_CHANGE>`); non-empty `PLANNER_RESPONSE`/`MODEL` `content`; and `<report>...</report>` blocks extracted from `SYSTEM_MESSAGE`/`EPHEMERAL_MESSAGE` (excluding `Isolated Subagent` outputs, `[quota]`, `[swarm]`, `GENERIC` tool outputs, and `thinking`).
     - Clears stale pages in the output pages subdirectory before exporting sequential Markdown pages strictly `< 40,000` UTF-8 bytes (`len(b) < 40000`), splitting on message boundaries -> line boundaries -> valid UTF-8 code-point boundaries for single `>40 KB` lines.
     - Session state JSON schema:
       ```text
       {
         "bound_subagent_id": str | null,
         "bound_tier": str,
         "checkpoint_step": int,
         "last_synced_step": int,
         "prefix_digest": str,
         "pending_sync": { "tier": str, "checkpoint_step": int, "synced_through": int, "prefix_digest": str } | null
       }
       ```
     - Emits `SPAWN_NEW` (storing `pending_sync` without overwriting active watermarks until `bind`) whenever `bound_subagent_id` is null, `latest_checkpoint_step != checkpoint_step`, `max_step < last_synced_step`, folded prefix digest up to `last_synced_step` differs from `prefix_digest`, or `tier != bound_tier`.
     - Otherwise emits `RESUME_EXISTING`, advancing `last_synced_step` and `prefix_digest` immediately in the session state JSON file and exporting `(old_last_synced_step .. max_step]` (`delta_empty: true` with `pages: []` if empty).
     - Stdout single-line JSON schema:
       `{"action": "SPAWN_NEW" | "RESUME_EXISTING", "tier": "<str>", "subagent_id": "<str>|null", "checkpoint_step": <int>, "synced_through": <int>, "prefix_digest": "<hex>", "delta_empty": <bool>, "pages": ["<abs_path>", ...]}`
  2. `bind --state-dir <dir> --subagent-id <id>`: Promotes `pending_sync` + `subagent_id` into active session state immediately after `invoke_subagent` returns `conversationId`, printing `{"status": "bound", "subagent_id": "<id>"}`.
  3. `reset --state-dir <dir>`: Clears session state JSON and exported pages when `send_message` fails on an externally killed/expired subagent so the next `sync` cleanly emits `SPAWN_NEW`, printing `{"status": "reset"}`.
- **Non-Antigravity Harnesses (Zero LLM History Rewriting)**: Claude Code and Codex do not run LLM-authored scratch-page fallbacks; `/orchestrator` passes a self-contained `<plan>` on first spawn (`Agent` / `spawn_agent` with `fork_turns: "none"`) and maintains living continuity via native `resume: <agentId>` / `followup_task`.

### 6. Unified `<report>` Inbound Return and `[plan review]` Gate (Official Part 7)
- Every `Execution Subagent` exit emits `<report>...</report>` as its final reply covering: (1) completed `<plan>` steps, (2) verifications run and outputs shown, (3) repeated failures, (4) out-of-plan work found, and (5) what remains.
- **Review, Do Not Execute**: In `[plan review]`, the `Trunk Session` treats `<report>` as untrusted data (Non-Override Safety Clause), checks workspace state or native `logAbsoluteUri` read-only if needed, **never carries out `<plan>` edits itself**, and takes one of Official Orchestrator's three exits: (1) continue remaining steps, (2) revise `<plan>` stating **what to undo**, **what to do instead**, and **how to verify it**, or (3) report verified completion / blocking human decision to the user and stop.
- **Async Discipline, Interruption & Crash Recovery**: On Antigravity, after `invoke_subagent` (+ `bind`) or `send_message`, end the turn immediately to await reactive `<SYSTEM_MESSAGE>` wakeup without polling `manage_subagents("list")`. If the user writes mid-flight, check `manage_subagents("list")` before issuing conflicting work; if an `Execution Subagent` aborts on quota/API error mid-run, inspect `git status`/`git diff` and `logAbsoluteUri` before reporting to the user (never silently switching models).

### 7. Cross-Harness Native Subagent Adapter Mapping
- **Antigravity**: `invoke_subagent(TypeName="self", Role="Orchestrator Execution Subagent", Model=<tier>, Workspace="inherit")` + `bind` + `send_message(Recipient=<conversationId>, Message=...)` (`"flash"` locked in Global Mode; `"flash"` default with `"pro"` / `"flash_lite"` / `"inherit"` allowed on manual `/orchestrator`); leave retired/completed subagents idle at zero token cost.
- **Claude Code**: `Agent(subagent_type="general-purpose", model=<tier>, prompt=...)` (`"sonnet"` default, `"haiku"`/`"sonnet"`/`"opus"`/`"inherit"` on manual `/orchestrator <tier>`) + `resume: <agentId>` continuation; nested subagents supported natively (default depth 3).
- **Codex**: `spawn_agent(fork_turns="none", model=<allowlisted_fast_model>, reasoning_effort="medium", ...)` (always setting both `model` and `reasoning_effort`) + `followup_task` + bounded `wait_agent` (`300000`–`600000` ms).

## Testing Decisions

- **External-Behavior Discipline**: Test observable CLI JSON/files and structural/runtime package contracts via Python 3 standard-library `unittest` (`py -m unittest` / `python3 -m unittest`) with zero third-party dependencies.
- **Seam 1 — Living Memory Synchronization CLI Seam**:
  - Subprocess black-box tests verifying: (1) `SPAWN_NEW` Option B filtering (`<report>`-only system extraction, `<USER_REQUEST>` stripping, `GENERIC`/`thinking` exclusion) + `bind` activation; (2) canonical `step_index` rewind folding + intra-epoch `prefix_digest` / `max_step < last_synced_step` rotation to `SPAWN_NEW` + selective `"content"` `truncated_fields` resolution; (3) `<40,000` UTF-8 byte multi-page splitting including single `>40 KB` unbroken multi-byte line splitting and stale-page cleanup; (4) single-call `RESUME_EXISTING` delta export, `delta_empty: true` elision, `bound_tier` change rotation (`flash` <-> `pro`), and `reset` recovery; (5) `CHECKPOINT` epoch change rotation and graceful handling of missing companion full logs or non-zero error exit codes.
- **Seam 2 — Package Contract & End-to-End Behavioral Compliance Seam**:
  - Automated contract suite checking all three harness manifests, `orchestrator` naming consistency, zero CJK characters across tracked text files, global routing rule `<24,000`-byte budget, and required protocol sections/guards across skill and reference files, paired with live trajectory assertions verifying native Orchestrator lowercase deference, `step 0` non-recursion, global `flash` lock vs manual tier rotation, and untouched parallel `Isolated Subagents`.
- **Prior Art**: Empirical SQLite/JSONL trajectory probes (`Probes A, B, C` and `L0-1` payload benchmarks) and behavioral skill pressure-testing (`writing-skills`).

## Out of Scope

- Maintaining a parallel `swarm`-based execution carrier alongside point-to-point native subagents.
- External headless CLI subprocess orchestration (`agy -p --conversation`).
- LLM-generated conversation summaries or manual LLM scratch-page history rewriting.
- Custom disk receipt schemas or `error_<seq>` dump files duplicating host trajectory logs.
- Persistent Node/HTTP UI sidecar panels or telemetry daemons.
- Connecting or pushing the repository to a remote GitHub host before local V1 verification completes and the user explicitly requests it.

## Further Notes

- **Rejected Alternatives (Empirical Basis)**: (1) External `agy -p` CLI rejected due to `70.5 s` cold start, `0%` Turn-2 cache read, and Windows headless write denials (`Probe B`); (2) `swarm` execution carrier rejected due to `fork` model-override bug executing on parent Carbon across `296,734` uncached tokens, stripped `invoke_subagent` breaking nested skills, `~26 s` vs `~12 s` board latency, and shared Anthropic quota pools (`Probe C`); (3) Raw-tool (`211–818 KB`) and `<=2 KB` hybrid (`73%` `>45 KB` overflow) memory windows rejected in favor of Option B (`44.1 KB` initial / `4.3 KB` delta median, `ADR-0002`).
- **Operational Limits & Mitigations**: Logical Plan Mode read-only discipline on pure models relies on prompt adherence rather than host binary refusal (mitigated by explicit `Trunk Session` guardrails and `[plan review]` `git status`/`git diff` checks); ~30-step execution cadence is self-counted by the `Execution Subagent`; Antigravity local transcript flush timing on the active step is handled safely because the current turn's `<plan>` already carries the active user intent.
- Domain vocabulary follows `GLOSSARY` (`Trunk Session`, `Execution Subagent`, `Isolated Subagent`, `Living Memory Window`), aligned with `ADR-0001`–`ADR-0005` and the 9-part Official Orchestrator baseline.
