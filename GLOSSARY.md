# Orchestrator

Dual-phase orchestration package optimized in V1 for Antigravity single-model sessions (with a reserved adapter seam for future client harnesses) where a planning `Trunk Session` and a single strongly-bound native `Execution Subagent` logically form one unified primary agent through `Living Memory Window` inheritance, orthogonal to ordinary native subagents.

## Language

**Trunk Session**:
The primary user-facing conversation and planning half of the unified primary agent, operating in logical Plan Mode for requirement alignment, read-only investigation, self-contained `<plan>` authoring, and `[plan review]` adjudication.
_Avoid_: Coordinator, router, wrapper

**Execution Subagent**:
The mounted execution half of the unified primary agent (not a domain or task subagent), using a client-native subagent solely as its physical transport carrier to inherit the `Living Memory Window`, execute `<plan>` steps in single-phase Execution Mode, and return structured execution `<report>`s.
_Avoid_: Domain subagent, Isolated Subagent, background daemon, peer worker

**Isolated Subagent**:
A fresh-context subset within the orthogonal native subagent layer (such as blind review personas in Elephant-Goldfish Model (EGM)) intentionally spawned without `Living Memory Window` inheritance and operating outside `orchestrator` mechanics so it evaluates targets without parent conversation bias.
_Avoid_: Execution Subagent, Right Brain

**Living Memory Window**:
The active, compaction-bounded span of canonical `Trunk Session` dialogue, compaction summaries, and prior execution `<report>`s currently visible to the Trunk model, inherited on `Execution Subagent` creation and extended incrementally until the next `Execution Subagent` rotation (Trunk compaction, rewind, tier change, respawn, or expected-cost rotation).
_Avoid_: Full raw history, hand-written summary
