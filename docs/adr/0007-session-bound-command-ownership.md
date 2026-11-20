# Session-Bound Command Ownership Across the Dual-Session Split

Status: accepted (2026-11-20); implementation tracked in [Ticket 08](../../.scratch/orchestrator-v1/issues/08-heavy-and-background-execution-delegation-gate.md).

## Context

The Occam adaptation ([02-occam-adaptation-to-native-subagents.md](../../.scratch/orchestrator-design/issues/02-occam-adaptation-to-native-subagents.md)) identified three physical differences between Official Orchestrator's same-thread hot-swap and native-subagent dual sessions: outbound `Living Memory Window` sync per [ADR-0002](0002-checkpoint-bounded-living-memory-inheritance.md), native delegation, and inbound `<report>` return per [ADR-0001](0001-unified-subagent-report-return-into-plan-review.md). Production session `L0-3` exposed a fourth physical difference: a host background process belongs to the session that started it, and host status wakeups are delivered only to that session. In a single thread this ownership is invisible; across two sessions, `Trunk Session` launching a long read-only command (under Official Part 2.4 / Part 7 observational `run_command`) binds recurring status wakeups to the high-context `Trunk Session` across the 300-second prompt-cache time-to-live cliff (evidence in [05-production-telemetry-ttl-and-lifecycle-audit.md](../research/05-production-telemetry-ttl-and-lifecycle-audit.md)). Symmetrically, an `Execution Subagent` that sends `<report>` while a command it started is still running wakes `Trunk Session` with an output-less report and is later re-woken by the host when the command exits, emitting a second report under the every-exit return contract.

## Decision

Adopt one symmetric invariant: **no session yields control (`Trunk Session` ending its turn, `Execution Subagent` sending `<report>`) while a command it started is still running.**

1. **`Trunk Session` side:** `Trunk Session` runs only commands that return synchronously, terminates any command it started that unexpectedly does not return before yielding, and delegates that work instead. Typical non-instant work (builds, full test suites, offline benchmarks, diagnostic probe scripts) is written into a `<plan>`.
2. **`Execution Subagent` side:** `Execution Subagent` reports only after every command it started reaches a terminal state, and terminates any still-running command before handing back on any early hand-back trigger. A still-running command is never a safe boundary for the ~30-turn interim report.
3. **Unchanged role split & host isolation:** The Official Orchestrator role split stays intact—`Trunk Session` keeps all judgment (investigation, decisions, choosing verification commands and expected outputs, reading host-recorded child outputs, and `[plan review]` exits), while `Execution Subagent` keeps execution. Host-specific details (Antigravity `run_command` synchronous wait capped at `WaitMsBeforeAsync <= 10000 ms`) live solely in [harnesses.md](../../skills/orchestrator/references/harnesses.md).

## Consequences

- Eliminates `Trunk Session` background babysitting wakeups (`~$11.18` wasted on `L0-3`) and double-report child wakeups.
- Requires zero `sync_memory.py` or state-machine changes and zero hooks or sidecars, remaining fully compatible with [ADR-0006](0006-pareto-boundary-reject-lifecycle-hooks-and-workflow-carrier.md).
- Persistent services cannot outlive a dispatch on either side; a misjudged `Trunk Session` command costs at most one synchronous wait window before termination.
