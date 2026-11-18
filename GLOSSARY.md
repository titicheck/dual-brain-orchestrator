# Orchestrator

Dual-phase orchestration package optimized in V1 for Antigravity single-model sessions (with a reserved adapter seam for future client harnesses) that pairs a planning `Trunk Session` with a bound native `Execution Subagent` through `Living Memory Window` inheritance.

## Language

**Trunk Session**:
The primary user-facing conversation operating in logical Plan Mode, responsible for requirement alignment, read-only investigation, self-contained `<plan>` authoring, and `[plan review]` adjudication.
_Avoid_: Coordinator, router, wrapper

**Execution Subagent**:
A client-native subagent attached to a `Trunk Session` that inherits its `Living Memory Window`, executes `<plan>` steps in single-phase Execution Mode, and returns structured execution `<report>`s.
_Avoid_: Isolated Subagent, background daemon, peer worker

**Isolated Subagent**:
A fresh-context subagent intentionally spawned without `Living Memory Window` inheritance (such as blind review personas in EGM) so it evaluates targets without parent conversation bias.
_Avoid_: Execution Subagent, Right Brain

**Living Memory Window**:
The active, compaction-bounded span of canonical `Trunk Session` dialogue, compaction summaries, and prior execution `<report>`s currently visible to the Trunk model, inherited on `Execution Subagent` creation and extended incrementally until the next Trunk compaction.
_Avoid_: Full raw history, hand-written summary
