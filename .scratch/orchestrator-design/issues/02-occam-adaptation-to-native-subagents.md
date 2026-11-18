# Occam's-Razor Adaptation from Same-Thread Hot-Swap to Native Subagent Interop

Type: grilling
Status: claimed
Blocked by: 01

## Question

Auditing `docs/research/01-official-orchestrator-system.md` part by part under Occam's Razor ("introduce nothing beyond what thread separation strictly forces"), what is the minimal set of modifications needed to replace Official Orchestrator's same-thread `exit_plan_mode` / `enter_plan_mode` hot-swap with Trunk-to-Native-Subagent lossless interop—specifically across (1) outbound context + `<plan>` delivery, (2) native subagent invocation/resumption, and (3) inbound reporting and final user reply?
