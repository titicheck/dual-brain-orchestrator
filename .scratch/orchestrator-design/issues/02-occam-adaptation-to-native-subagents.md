# Occam's-Razor Adaptation from Same-Thread Hot-Swap to Native Subagent Interop

Type: grilling
Status: claimed
Blocked by: 01

## Question

Auditing `docs/research/01-official-orchestrator-system.md` part by part under Occam's Razor ("introduce nothing beyond what thread separation strictly forces"), what is the minimal set of modifications needed to replace Official Orchestrator's same-thread `exit_plan_mode` / `enter_plan_mode` hot-swap with Trunk-to-Native-Subagent lossless interop—specifically across (1) outbound context + `<plan>` delivery, (2) native subagent invocation/resumption, and (3) inbound reporting and final user reply?

## Comments

- **Inbound reporting & final user sign-off (`Q3`) settled (`2026-11-18`)**: Adopted unified `<report>` return into Official Orchestrator's `[plan review]` gate, reusing host-persisted `logAbsoluteUri` on demand instead of custom receipt/error-dump files. Recorded in [ADR-0001](../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md).
- **Baseline EGM audit (`Q1`) completed (`2026-11-18`)**: `01-official-orchestrator-system.md` hardened against `egm-codebase-details` and `egm-comprehension` findings.
- **Outbound context transfer (`Q2`) open**: Discussing how to inherit the main model's active `CHECKPOINT`-bounded context window ("living memory") plus async continuation, specifically how raw tool outputs in the active window should be handled. Ticket remains `claimed`.
