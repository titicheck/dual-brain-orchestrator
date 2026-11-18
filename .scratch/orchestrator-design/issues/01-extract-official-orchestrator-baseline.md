# Extract Official Orchestrator Baseline and Archive Exploratory Notes

Type: task
Status: resolved

## Question

Extract the complete underlying Official Orchestrator system (Planning Mode, `exit_plan_mode`, Execution Entry envelope, Execution Mode, `enter_plan_mode`, `[plan review due]`, `[plan review]`, native `<subagents>`/`<messaging>`, and compaction behavior) without custom modifications, and separate all prior exploratory discussions and empirical host probes into non-binding notes while resetting premature `GLOSSARY.md` and `docs/adr/` entries.

## Answer

Completed:
- Complete 9-part official baseline recorded in [01-official-orchestrator-system.md](../../../docs/research/01-official-orchestrator-system.md).
- Prior exploratory discussions and verified host storage/probe data archived as non-binding context in [02-exploratory-notes-and-host-probes.md](../../../docs/research/02-exploratory-notes-and-host-probes.md).
- `GLOSSARY.md` and `docs/adr/` reset clean so only Occam-converged final decisions are recorded going forward.
