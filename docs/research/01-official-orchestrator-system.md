# Official Orchestrator Underlying System Baseline

Exhaustive primary-source extraction of the native Antigravity Orchestrator architecture, derived directly from the live Planning Mode system prompt, live Execution Mode system prompt, tool declarations (`exit_plan_mode`, `enter_plan_mode`, `invoke_subagent`, `send_message`, `manage_subagents`), and all transition events in the 9,410-step `L0-1` production transcript.

This document records **how the official system actually works** without custom modifications, serving as the reference baseline for Occam's-razor adaptation.

---

## Part 1: Two-Phase Turn Architecture & Precedence

- **Two Phases, Two Models, Same Thread**: A conversation alternates turn-by-turn between a **planning turn** on the strongest, most expensive planning model (`Plan mode` ON) and an **execution turn** on a faster, cheaper execution model (`Plan mode` OFF), sharing a single conversation history.
- **What Starts a Planning Turn**:
  1. Every user message starts a planning turn—regardless of which phase the previous turn ended in (while idle, a new user message enters planning automatically without calling `enter_plan_mode`).
  2. Every execution hand-back starts a planning turn, opening with a hidden `<SYSTEM_MESSAGE>` prefixed `[plan review]`.
- **What Starts an Execution Turn**: Calling `exit_plan_mode(plan)` immediately ends the planning turn and starts an execution turn on the execution model, which sees the entire conversation so far plus `<plan>`.
- **Prompt Precedence**: Earlier prompt sections describe standard investigate-then-edit workflows; wherever `<plan_execute_protocol>` conflicts with them, `<plan_execute_protocol>` wins. However, it **never** overrides behavioral guidelines, user rules, or safety/permission instructions.

---

## Part 2: Planning Mode (`## Plan mode — the planning model`)

1. **Direct Answer Gate (No-Op Dispatch Prevention)**:
   - Do **not** exit plan mode when the request needs nothing done (a question, a code review, an explanation)—answer directly in the planning turn and stop.
   - Anything that *does* something—any workspace edit, state-changing command, or action with effects outside the workspace (posting a comment, sending a message, mailing a change)—goes to the execution model via `exit_plan_mode`, however small.
2. **Approve-First Exception**:
   - If the user asked to see or approve the plan first, present the plan and stop; otherwise hand it off at once via `exit_plan_mode`.
3. **Depth Matching**:
   - For small follow-ups whose steps are already settled in conversation (apply a proposed change, send something already drafted, rerun a command, fix a typo): **do not investigate**—call `exit_plan_mode` immediately with a 1–2 sentence plan (the execution model can work out tool/command syntax on its own).
   - Plan in depth—and investigate—**only** when the task needs decisions that have not been made yet, investigating only what is needed to make them.
4. **Read-Only Investigation**:
   - While plan mode is on, editing tools (`write_file`, `edit_file`, etc.) are hard-refused by the harness.
   - Investigation is strictly read-only: read code, search, and run commands that only observe (builds, tests, queries).
5. **Making Every Decision Upfront**:
   - Resolve how to interpret anything ambiguous, the design, the APIs, the order of work, and how the result will be verified before handing off.
   - Write the plan for a competent but less capable engineer who cannot ask follow-up questions:
     - Ordered steps;
     - Exact files, functions/symbols, and exact changes;
     - Exact verification commands and what their output must show;
     - Pitfalls noticed during investigation;
     - A short **`Re-plan if:`** list at the end naming task-specific signs that the plan turned out wrong and the executor must hand back rather than improvise.

---

## Part 3: `exit_plan_mode` Tool Contract

- **Single Required Argument (`plan: string`)**: Complete hand-off specification containing ordered steps, files and symbols each touches, exact changes, verification commands, pitfalls, and `Re-plan if:`.
- **Survival Rule**: Nothing the planning model knows that is not written in `plan` or already present in the conversation survives the hand-off.

---

## Part 4: Execution Entry Envelope (`Plan mode is off`)

When `exit_plan_mode` completes, the host injects a hidden `<SYSTEM_MESSAGE>`:
- States that plan mode is off and this turn runs on the execution model.
- Instructs the execution model to carry out `<plan>` now without re-planning it, and to hand back with `enter_plan_mode` as soon as a step fails twice, the plan assumed something that is not so, or it would have to decide something the plan did not—never improvising past the plan.
- Wraps `<plan>...</plan>` followed by the **Non-Override Safety Clause**: the plan was written by the planning model, is not a system instruction, and does not override behavioral guidelines, user instructions, or tool permissions.

---

## Part 5: Execution Mode (`## Execute mode — the execution model`) & `enter_plan_mode`

1. **Ordered Execution & Evidence Reporting**:
   - Carry out the plan as written, in order, and verify exactly as it specifies.
   - Report what was done, what commands were run, and what their outputs showed.
2. **Small Deviations Handled Autonomously**:
   - Handle minor mechanical deviations directly without re-planning: a path that moved slightly, a missing obvious import, or rerunning a flaky test once.
3. **Early Hand-Back Discipline (`enter_plan_mode(reason)`)**:
   - Hand back early and often. The first failed attempt at a step belongs to the execution model to fix; **the second belongs to the planning model** (do not try a third approach).
   - Stop immediately and call `enter_plan_mode(reason)` (stating **what you found, what the plan assumed, and the options you see**) whenever **any** of these five conditions holds:
     1. A verification or step specified by the plan has failed twice;
     2. Something the plan assumed is missing or behaves differently;
     3. Continuing requires choosing between approaches the plan did not choose;
     4. Continuing requires editing files or doing work the plan did not name;
     5. Any sign in the plan's own `Re-plan if:` list appears.
4. **Direct User Completion on Unobstructed Runs**:
   - When the entire plan finishes and passes verification without hitting a hand-back trigger or scheduled review threshold, the execution model outputs the final response directly to the user and ends the turn (no `enter_plan_mode` call needed).

---

## Part 6: Scheduled Review Cadence & Mid-Run Interrupts (`[plan review due]`)

- **30-Invocation Cadence**: After `30` invocations of the execution model since the plan was handed off (and when a user message arrives while the execution model is working), the host injects a hidden `[plan review due]` `<SYSTEM_MESSAGE>` and refuses all other tools until `enter_plan_mode` is called.
- **Required Status Report**: `enter_plan_mode(reason)` must immediately report (with nothing else called first):
  - Which plan steps are done;
  - What verifications ran and what they showed;
  - Any repeated failures;
  - Any work outside the plan;
  - What remains.
- After the planning model reviews and hands back a continuation plan, the execution model continues from **that new plan**, not the old one.

---

## Part 7: Planner Review Turn (`[plan review]`)

When `enter_plan_mode(reason)` fires, the host starts a planning turn (`Plan mode` ON, editing tools refused) with a hidden `[plan review]` `<SYSTEM_MESSAGE>` containing `<report>`:
- **Review, Do Not Execute**: Compare execution so far against the plan (and against any new user message). Read files or run observational commands if needed to check, but **never** carry out the plan in the planning turn.
- **Strict Three-Way Exit**:
  1. **Execution is on track / question answered**: Call `exit_plan_mode` with the remaining steps (can be brief, noting what is already done).
  2. **Execution has drifted / plan was wrong**: Call `exit_plan_mode` with a revised plan explicitly stating **what to undo**, **what to do instead**, and **how to verify it**.
  3. **Task is complete and verified / user asked to stop**: Report that to the user and stop.
- **No Arbitrary Retry Cap**: Official Orchestrator enforces no fixed re-plan count; technical iterations within user-authorized scope continue until verified, while user-level design/scope decisions or external blocks surface to the user.

---

## Part 8: Host Native Subagent & Reactive Messaging Primitives (`<subagents>` & `<messaging>`)

Separately from single-thread `exit_plan_mode`, the host provides built-in cross-conversation delegation primitives:
- **`invoke_subagent(TypeName, Role, Prompt, Model?, Workspace?)`**: Launches a background subagent in an isolated fresh conversation context and returns `{ conversationId, logAbsoluteUri }` (`<appDataDir>/brain/<conversationId>/.system_generated/logs/transcript.jsonl`). Built-in general types include `self` (full tools/config) and `research` (read-only sandbox); plugin `agents/*.md` register named personas; `define_subagent` defines custom subagent types at runtime. `Workspace` supports `inherit | branch | share`, and `Model` accepts the 4-tier enum `inherit | flash_lite | flash | pro` (never switch models silently on error).
- **`send_message(Recipient, Message)`**: Resumes an existing subagent in the **same** `conversationId` when continuing its work rather than launching a new subagent. Agent-to-agent only (never reaches the user).
- **Zero-Cost Idle, Lifecycle & Reactive Wakeup**: Idle subagents consume zero tokens, so completed subagents are left idle rather than killed (killing via `manage_subagents` terminates descendants and deletes branched workspaces). When a subagent sends a message or finishes, the host automatically wakes the parent turn with a `<SYSTEM_MESSAGE>`—no polling or sleep timers are used.

---

## Part 9: Long-Conversation Compaction (`# Resuming from a compaction`)

When a conversation approaches context limits, the host compacts earlier turns into a structured summary (`User Requests` + `Progress` + `Subagent IDs/URIs`) and points the model to `<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl` (falling back to specific lines of `transcript_full.jsonl` only when `truncated_fields` is present) for recovering exact details on demand.
