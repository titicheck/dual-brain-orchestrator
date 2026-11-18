# Orchestrator V1 Specification

Status: ready-for-agent

## Problem Statement

Developers working in single-model agent sessions—such as frontier reasoning models selected directly in an IDE or CLI agent—lack the built-in two-phase planning and execution scheduling of the native Antigravity Orchestrator. Without that separation, every mechanical file edit, command run, test iteration, and multi-step implementation turn runs directly inside the primary session on the expensive frontier model, burning scarce quota, bloating the planning context window with raw tool output, and blurring architectural decision-making with execution trial-and-error. Conversely, naive delegation to generic subagents loses the living conversational context that native same-thread model hot-swapping preserves, risks recursive planning loops when workspace or plugin rules propagate into child subagents, and can accidentally downgrade high-stakes blind reviews if review subagents are nested underneath an offloaded execution model.

## Solution

Deliver a portable, unified `orchestrator` plugin and skill package derived directly from the Official Orchestrator protocol by replacing same-thread model hot-swapping with lossless interop between a planning `Trunk Session` and a client-native `Execution Subagent`. Enabling the plugin activates two-phase orchestration globally across top-level sessions (while disabling it incurs zero token cost, and standalone skill installation preserves manual on-demand invocation). Whenever a task requires workspace changes or external side effects, the `Trunk Session` investigates read-only on the user's chosen main model, authors a self-contained `<plan>`, exports its active compaction-bounded `Living Memory Window` through a deterministic zero-LLM synchronization utility, and dispatches execution to a bound `Execution Subagent` running on a fast, cost-efficient execution model. Subsequent turns within the same compaction epoch resume that `Execution Subagent` incrementally to preserve prefix cache hits, while every completion, scheduled ~30-step checkpoint, or early hand-back returns a structured `<report>` into Official Orchestrator's unmodified three-way `[plan review]` gate. All `Isolated Subagents` retain untouched default model inheritance and zero memory injection—keeping heavyweight reviews in the `Trunk Session` on the main model and capping execution-phase nested workers at the execution model.

## User Stories

1. As a developer using a pure single-model session with the `orchestrator` plugin enabled, I want two-phase Plan/Execute scheduling to engage automatically on top-level requests, so that my expensive reasoning model handles planning and review while routine execution runs on a faster, cheaper model without manual setup per chat.
2. As a developer who temporarily wants unmediated single-model execution, I want disabling the `orchestrator` plugin in host settings to unload both its routing rule and skill definitions completely, so that disabled state consumes zero context tokens.
3. As a developer installing `orchestrator` as a standalone skill without plugin rules, I want orchestration to remain strictly opt-in via explicit `/orchestrator` invocation, so that my default agent behavior is unchanged unless I invoke the skill.
4. As a developer already running inside the host's native Orchestrator mode, I want the global `orchestrator` routing rule to detect native two-phase transition tools and yield silently, so that native same-thread hot-swapping runs without redundant subagent layers unless I explicitly invoke `/orchestrator`.
5. As a developer spawning child subagents in a workspace where the `orchestrator` plugin rule is active, I want every session woken by an inter-agent message rather than a direct human prompt to remain strictly single-phase, so that neither an `Execution Subagent` nor an `Isolated Subagent` ever enters recursive Plan/Execute loops.
6. As a developer asking a pure question, requesting an explanation, or running a standalone review, I want the `Trunk Session` to answer or run the review directly in Plan Mode without spawning an `Execution Subagent`, so that read-only turns avoid unnecessary delegation latency.
7. As a developer sending a small follow-up whose decisions are already settled (such as applying an approved tweak, rerunning a check, or fixing a typo), I want the `Trunk Session` to skip redundant codebase exploration and dispatch a concise one-to-two-sentence `<plan>` immediately, so that trivial turns stay fast.
8. As a developer requesting a complex multi-file feature or refactor, I want the `Trunk Session` to investigate strictly read-only, resolve every design ambiguity upfront, and produce a self-contained `<plan>` naming exact targets, changes, verification commands with expected outputs, pitfalls, and explicit `Re-plan if:` conditions, so that the `Execution Subagent` never has to guess architectural intent.
9. As a developer asking to inspect or approve a plan before changes are made, I want the `Trunk Session` to present the plan and stop without spawning an `Execution Subagent`, so that execution waits for my explicit go-ahead.
10. As a developer handing off a `<plan>` mid-conversation, I want the newly spawned `Execution Subagent` to inherit the `Trunk Session`'s active `Living Memory Window`—retaining compaction summaries, verbatim user prompts, visible assistant responses, and prior execution `<report>` blocks while omitting raw exploration tool dumps and private reasoning—so that the `Execution Subagent` has complete conversational context without stale file-snippet bloat.
11. As a developer who edits, retries, or rewinds earlier turns in a conversation, I want the memory synchronization utility to fold append-only conversation logs by canonical step index so that superseded branches are discarded before the `Living Memory Window` is exported.
12. As a developer working in a long session whose initial `Living Memory Window` exceeds a single host file-read byte cap, I want the synchronization utility to split snapshots cleanly into ordered pages under 40,000 bytes on line boundaries, so that the `Execution Subagent` reads every page completely without truncation.
13. As a developer iterating across multiple execution rounds within the same session, I want follow-up dispatches to resume the existing bound `Execution Subagent` and export only the incremental step slice added since the last sync (or nothing when no new dialogue occurred), so that prefix KV caches remain warm and context is never duplicated.
14. As a developer in a marathon session that crosses a host context compaction boundary, I want a new `Trunk Session` compaction checkpoint to automatically retire the previous `Execution Subagent` to zero-cost idle state and spawn a fresh `Execution Subagent` seeded from the new checkpoint window, so that subagent context lifecycles stay bounded without arbitrary turn-count resets.
15. As a developer running a frontier Anthropic or Gemini model in my `Trunk Session`, I want explicit execution-tier model selection to happen exclusively when spawning the bound `Execution Subagent`, so that implementation work offloads to a fast execution pool instead of inheriting my frontier model's quota.
16. As a developer whose selected execution model hits quota exhaustion or unavailability, I want the agent to stop and report the exact failure to me rather than silently switching to another model tier, so that quota spending and model selection stay under my explicit control.
17. As a developer delegating a large `<plan>`, I want the `Execution Subagent` to pause and return a status `<report>` after roughly 30 model/tool turns, so that the `Trunk Session` can audit progress against the plan before drift compounds.
18. As a developer whose `<plan>` encounters a step failing twice, a false codebase assumption, an unmade design decision, unrequested out-of-plan prerequisites, or an external credential/network block, I want the `Execution Subagent` to stop immediately and hand back a `<report>` rather than improvising past the plan.
19. As a developer receiving results back from an `Execution Subagent`, I want every exit—full completion, ~30-step scheduled review, or early hand-back—to enter the `Trunk Session`'s unmodified three-way `[plan review]` gate (continue remaining steps, send a revised plan stating what to undo / do instead / verify, or deliver verified completion to me and stop), so that final verification and user communication stay anchored in the `Trunk Session`.
20. As a developer diagnosing a tricky failure reported by an `Execution Subagent`, I want the `Trunk Session` to inspect the host's native subagent trajectory log on demand only when raw step details are needed, so that normal turns stay lightweight without custom error-dump artifacts.
21. As a developer running standalone blind reviews (such as multi-persona design audits or two-axis code reviews), I want the `Trunk Session` to stay in Plan Mode on my active main model and spawn `Isolated Subagents` with untouched default `inherit` model settings and zero `Living Memory Window` injection, so that blind reviewers evaluate targets unbiased on my top-tier model.
22. As a developer issuing a combined prompt to "implement X and then run a deep review", I want the `Trunk Session` to dispatch only the implementation steps in `<plan>` to the `Execution Subagent` and then launch the heavyweight review directly from the `Trunk Session` upon `[plan review]` return (when the main model is active again), so that I get full main-model review quality in one seamless turn without manually splitting prompts or nesting reviewers under the execution model.
23. As a developer executing parallel implementation slices inside an `Execution Subagent` on a host that supports nested subagents, I want nested workers spawned by the `Execution Subagent` with default `inherit` settings to naturally inherit and cap at the execution model, while single-depth harnesses cleanly hand back via Trigger #5 for `Trunk Session` dispatch.
24. As a developer working across Antigravity, Claude Code, and Codex, I want the `orchestrator` skill to map onto each client's built-in subagent creation and continuation primitives through a clear harness adapter reference, so that one conceptual workflow operates portably across environments.

## Implementation Decisions

### 1. Unified Package Identity and Dual-Mode Activation
- Both the plugin identifier and the skill identifier are standardized as `orchestrator` across all supported client harnesses.
- All operational skill assets—the core orchestration instructions, the deterministic memory synchronization CLI script, the execution-subagent protocol reference, and the cross-harness primitive mapping reference—reside inside a single self-contained skill module so standalone skill distribution requires copying only that directory.
- Thin multi-harness plugin manifests and a thin always-on global routing rule enclose the self-contained skill module at the package root, with zero startup shell hooks and zero persistent background processes.
- Activation supports two clean modes:
  1. **Plugin Mode (Global Default Switch)**: When the `orchestrator` plugin is enabled on hosts supporting plugin rules, the global routing rule activates two-phase orchestration by default on qualifying top-level conversations. Disabling the plugin unloads both the routing rule and the skill at zero token cost.
  2. **Standalone Skill Mode (Manual Opt-In)**: When only the skill module is installed (or on harnesses without plugin-level global rules), orchestration activates on demand when `/orchestrator` is invoked.
- The always-on routing rule must stay concise (well within the host's 24,000-byte per-file rule cap and shared rules token budget), containing only scope guards and a pointer instructing qualifying sessions to follow the `orchestrator` skill protocol.

### 2. Scope Guards, Native Deference, and Subagent Non-Recursion
- **Native Orchestrator Deference**: Before engaging cross-session orchestration under the global routing rule, the agent checks its available tool declarations. If native same-thread phase-transition tools (`exit_plan_mode` or `enter_plan_mode`) are present, the global rule yields silently to the host's native Orchestrator unless the user explicitly invokes `/orchestrator`.
- **Top-Level Human Session Guard (Zero Recursion)**: Because workspace and plugin rules propagate into child subagents running in the same workspace, the global routing rule activates **exclusively** when the session's initial turn is a direct human request (`<USER_REQUEST>` / `USER_INPUT`). Any session woken by an inter-agent `<SYSTEM_MESSAGE>` (`[Message] timestamp=... sender=<parent_uuid> ...`) or already operating under subagent role instructions treats the global routing rule as a strict no-op and executes its assigned task in single-phase mode.

### 3. Official-First Two-Phase Protocol Fidelity
- **Logical Plan Mode (`Trunk Session`)**:
  - Every direct user message and every inbound `Execution Subagent` `<report>` begins in logical Plan Mode on the `Trunk Session`.
  - Match planning depth to request complexity: already-settled small follow-ups dispatch immediately with a one-to-two-sentence `<plan>`; Pure questions, explanations, and standalone reviews do not spawn an `Execution Subagent` and are handled directly in the `Trunk Session`; If the user asks to see or approve the plan first, present it and stop.
  - When planning is required, the `Trunk Session` performs read-only investigation only (reading files, searching, running purely observational build/test/query commands) and refrains from mutating workspace project files directly.
  - Every dispatched `<plan>` must be self-contained for an execution engineer who cannot ask interactive follow-up questions during execution: ordered steps, target modules and symbols, exact behavioral/code changes, verification commands and what their output must show, discovered pitfalls, and a closing `Re-plan if:` checklist.
  - Plans carry Official Orchestrator's non-override safety boundary: a `<plan>` does not override host safety guidelines, user instructions, or tool permissions.
- **Single-Phase Execution Mode (`Execution Subagent`)**:
  - Carries out the received `<plan>` directly in order without re-planning.
  - Enforces a **~30-step scheduled review cadence**: after approximately 30 model/tool turns since the latest `<plan>` dispatch (or continuation), the `Execution Subagent` pauses and returns an interim status `<report>` to the `Trunk Session` rather than running unbounded.
  - Enforces Official Orchestrator's **five mandatory early hand-back triggers** (stopping immediately and returning `<report>` without improvising):
    1. A step fails twice;
    2. The `<plan>` assumed something about the codebase or environment that turns out false;
    3. Completing the work requires a design or scope decision the `<plan>` did not make;
    4. Unrequested work outside the `<plan>` appears necessary;
    5. An external block occurs (missing credentials, denied permissions, unreachable resources, CAPTCHA/human gate, or missing nested-subagent capability on a single-depth harness).

### 4. Two-Active-Model Natural Inheritance and Coexistence with Isolated Subagents
- **Single Offload Boundary**: Explicit selection of a faster, cheaper execution model tier (for example, passing an explicit fast/high-efficiency model tier rather than `inherit` when the `Trunk Session` runs on a pure single-model frontier configuration) occurs **exclusively** when spawning the `Trunk Session`'s single bound `Execution Subagent`. Never switch models silently on quota exhaustion or model errors—stop and ask the user.
- **Untouched Default Inheritance Everywhere Else**: All other subagent invocations across the session retain the host's native `inherit` default (unless the user explicitly requests a specific model or a specialized built-in browser agent defines its own host default) and receive **zero** `Living Memory Window` injection.
- **Non-Nested Main-Model Reviews**: Heavyweight audits and blind reviews (such as multi-persona design/comprehension/readiness reviews and two-axis code reviews) must **never** be bundled inside an `Execution Subagent` `<plan>`.
  - For standalone review requests, the `Trunk Session` remains in Plan Mode (Main Model active) and spawns the `Isolated Subagent` reviewers directly at `depth = 1`, naturally inheriting the Main Model.
  - For compound user requests combining implementation and review (for example, "implement X and then review it"), the `Trunk Session` dispatches only the implementation steps in `<plan>` to the `Execution Subagent`; once the `Execution Subagent` returns its `<report>` to `[plan review]` (restoring control to the Main Model in the `Trunk Session`), the `Trunk Session` launches the `Isolated Subagent` reviewers directly from `depth = 0` so reviewers inherit the Main Model, and dispatches a follow-up revision `<plan>` to the `Execution Subagent` only if review findings require edits.
- **Execution-Phase Foreman Delegation**: For parallel implementation slices or lightweight execution-internal checks inside `<plan>`, the `Execution Subagent` (`depth = 1`) may spawn nested `Isolated Subagents` (`depth = 2`) on nested-capable hosts; under default `inherit`, those nested workers naturally inherit and cap at the `Execution Subagent`'s execution model without consuming `Trunk Session` frontier quota. On single-depth harnesses where child subagents lack subagent-spawning tools, the `Execution Subagent` triggers Hand-back Trigger #5 so the `Trunk Session` can organize slice dispatch directly.

### 5. Checkpoint-Bounded Living Memory Synchronization Contract
- A zero-LLM local Python CLI utility (using only the Python 3 standard library for zero external installation dependencies) deterministically extracts and tracks the `Trunk Session`'s `Living Memory Window` whenever a local conversation log is available:
  - **Canonical Step Folding**: Reads the append-only JSONL conversation log and folds records by canonical `step_index` so that any later record at `step_index = k` invalidates and discards all earlier records at `>= k` from rewound, retried, or edited turns (fetching untruncated step bodies from the companion full-log file only when `truncated_fields` indicates content truncation).
  - **Window Span**: Spans `[latest CHECKPOINT step (or step 0) .. current_step]`.
  - **Step Filtering (Option B)**:
    - *Retained*: Compaction summaries (`CHECKPOINT`), verbatim user inputs (`USER_INPUT` with host metadata tags stripped), visible assistant text replies (`MODEL` / `PLANNER_RESPONSE` visible `content`), and prior inbound subagent `<report>` system messages.
    - *Omitted*: Raw exploration/execution tool outputs (`GENERIC`), internal ephemeral phase prompts, and private chain-of-thought (`thinking`).
  - **Byte-Safe Pagination**: Splits exported Markdown output on clean message/line boundaries into sequential page files strictly under `40,000` bytes each, guaranteeing single-call readability under `46,080`-byte `read_file` limits.
  - **Session Binding & Epoch State Machine** (stored in conversation-local scratch state):
    ```text
    State: { bound_subagent_id: str | null, checkpoint_step: int, last_synced_step: int }

    On sync(transcript_path, state_dir):
      1. Fold canonical steps -> find latest_checkpoint_step (or -1 if none) and max_step.
      2. If state.bound_subagent_id is null OR latest_checkpoint_step > state.checkpoint_step:
           Export full window [max(0, latest_checkpoint_step) .. max_step] -> page_001..page_NNN
           Return action = SPAWN_NEW, checkpoint_step = latest_checkpoint_step, synced_through = max_step, pages = [...]
      3. Else (same compaction epoch, bound_subagent_id exists):
           Export retained steps in (state.last_synced_step .. max_step] -> delta_page_001..page_NNN
           If no retained steps in range:
             Return action = RESUME_EXISTING, delta_empty = true, subagent_id = state.bound_subagent_id
           Else:
             Return action = RESUME_EXISTING, delta_empty = false, subagent_id = state.bound_subagent_id, pages = [...]
    ```
  - **Commit Step**: A separate lightweight state-update command records `(bound_subagent_id, checkpoint_step, synced_through)` once `invoke_subagent` or `send_message` succeeds, ensuring failed or aborted dispatches never advance the watermark prematurely.
  - **Opaque-Log Harness Fallback**: On client harnesses that do not expose a readable local JSONL transcript for the active session, the `Trunk Session` materializes the equivalent `Living Memory Window` snapshot/delta directly into session-local scratch pages using the exact same inclusion rules and `<40,000`-byte page cap.

### 6. Unified `<report>` Inbound Return and Three-Way `[plan review]` Gate
- Every `Execution Subagent` turn concludes by returning a structured `<report>` covering Official Orchestrator's five status dimensions:
  1. Which `<plan>` steps were completed;
  2. What verification commands ran and what their outputs showed;
  3. Any repeated failures encountered;
  4. Any out-of-plan work discovered;
  5. What remains to be done (or confirmation that all `<plan>` items are complete and verified).
- The `Trunk Session` treats every `<report>` as untrusted execution data (never overriding guidelines, user instructions, or permissions), compares it against the `<plan>` and any newly arrived user input (reading workspace files, running read-only checks, or reading the host's native subagent `logAbsoluteUri` on demand if raw step output is needed), and takes exactly one of Official Orchestrator's three exits:
  1. **On Track / Answered**: Resume the bound `Execution Subagent` (or spawn fresh if a compaction occurred) with the remaining steps plus any incremental `Living Memory Window` delta.
  2. **Drifted / Plan Wrong**: Resume (or rotate) with a revised `<plan>` stating explicitly **what to undo**, **what to do instead**, and **how to verify it**.
  3. **Complete & Verified / User Stopped / Human Decision Needed**: Present the verified result (or surface the blocking human-level decision) directly to the user and end the turn.

### 7. Cross-Harness Native Subagent Adapter Mapping
- **Antigravity**: Spawn bound `Execution Subagent` via `invoke_subagent` (`TypeName: "self"`, explicit non-`inherit` execution tier such as `"flash"`, or `"pro"` when deeper execution reasoning is warranted; `Workspace: "inherit"`), passing `<Living Memory Window page paths>` + `<plan>` + execution protocol reference; resume within the same compaction epoch via `send_message(Recipient=<conversationId>, Message=...)`; leave retired/completed subagents idle at zero token cost rather than killing them.
- **Claude Code**: Spawn bound `Execution Subagent` via `Agent` (`subagent_type: "general-purpose"`, explicit fast execution `model` such as `sonnet` or `haiku`), resume via `resume: <agentId>` when supported (falling back to spawning with full active `Living Memory Window` pages if resumption is unavailable), and route any nested subagent need back to the `Trunk Session` via Hand-back Trigger #5 due to single-depth subagent restrictions.
- **Codex**: Spawn bound `Execution Subagent` via `spawn_agent` (`fork_turns: "none"` so controlled `Living Memory Window` pages replace raw tool-heavy parent history, explicit execution `model` + `reasoning_effort`) and continue via `followup_task` + `wait_agent`.

## Testing Decisions

- **What Makes a Good Test**: Tests must verify observable external behavior and public contracts rather than internal helper functions or phrasing minutiae. Deterministic code is tested via black-box CLI execution on realistic transcript fixtures; agent instructions and packaging are tested via structural contract checks and live behavioral pressure scenarios.
- **Seam 1 — Living Memory Synchronization CLI Seam**:
  - Automated black-box test suite invoking the synchronization CLI subprocess against synthetic and empirical-shaped JSONL conversation fixtures covering:
    1. Initial `SPAWN_NEW` snapshot generation retaining `CHECKPOINT`, stripped `USER_INPUT`, visible `MODEL` replies, and prior `<report>` messages while excluding `GENERIC` tool outputs and `thinking`;
    2. Canonical `step_index` folding when turn retries/rewinds reuse earlier step indices (`>= k` invalidation) and `truncated_fields` resolution against companion full-log files;
    3. Deterministic multi-page splitting strictly below `40,000` bytes per page without mid-line corruption when a snapshot exceeds a single read limit;
    4. Incremental `RESUME_EXISTING` delta export `(last_synced_step, current_step]`, `delta_empty = true` elision when no new retained dialogue occurred, and watermark preservation when commit is not called;
    5. Automatic `SPAWN_NEW` rotation when a new `CHECKPOINT` step (`> recorded checkpoint_step`) appears in the `Trunk Session` transcript.
- **Seam 2 — Package Contract & End-to-End Behavioral Compliance Seam**:
  - Automated package validator checking manifest JSON validity across Antigravity, Claude Code, and Codex manifests, identifier consistency (`orchestrator`), zero CJK characters in repository files, and global rule byte size strictly within the 24,000-byte host rule cap.
  - Live end-to-end behavioral verification scenarios testing:
    1. **Scope & Non-Recursion Guard**: Native Orchestrator deference when native phase tools exist, and single-phase non-recursion when woken by `[Message] timestamp=... sender=<parent_uuid>`;
    2. **Full Two-Phase Lifecycle**: Pure-model `Trunk Session` read-only planning -> `Living Memory Window` sync -> offloaded `Execution Subagent` spawn (`Model: "flash"`) -> incremental `send_message` continuation -> unified `<report>` return -> `[plan review]` verification and user sign-off;
    3. **Isolated Subagent & Review Coexistence**: Standalone/post-implementation blind review dispatched from `Trunk Session` with untouched `Model: "inherit"` (inheriting Main Model, zero `Living Memory Window` leakage) alongside execution-phase nested worker inheritance capping at the execution model.
- **Prior Art**: Host SQLite/JSONL trajectory verification probes documented in the repository's research notes and behavioral skill pressure-testing methodology (`writing-skills`).

## Out of Scope

- Swarm message-board multi-peer coordination modes (`/swarm`).
- External headless CLI subprocess orchestration (`agy -p --conversation`).
- Custom disk receipt schemas or `error_<seq>.md` dump formats duplicating host trajectory logs.
- Persistent Node/HTTP UI sidecar panels or telemetry daemons.
- Connecting or pushing the repository to a remote GitHub host before local V1 implementation and verification are complete and explicitly requested by the user.

## Further Notes

- Domain terminology follows the repository's `GLOSSARY` definitions (`Trunk Session`, `Execution Subagent`, `Isolated Subagent`, `Living Memory Window`), and architectural constraints reflect settled decisions `ADR-0001` through `ADR-0004` plus the verified 9-part Official Orchestrator baseline.
- Runtime orchestration behavior is completely decoupled from the local Markdown issue-tracking and ADR workflow used to author this repository.
