# 04: Trunk Efficiency and Static-Tier Precedence Clarity

**What to build:** Tighten `orchestrator` prompt precedence and `Trunk Session` dispatch and review discipline based on empirical head-to-head telemetry so conversational execution-model requests never stall planning in precedence tug-of-war, `Trunk Session` invokes the synchronization CLI strictly as a black box without reading synchronization source or subagent protocol instructions into trunk context, post-approval hand-offs avoid redundant plan duplication, `[plan review]` favors lightweight footprint checks over redundant full-suite re-execution when verification evidence is clean, and structural contract tests enforce all three invariants.

**Blocked by:** 03: Single-Manifest Pure-Skill Plugin Packaging, Shared-Rule Guide, and Contract Suite

**Status:** resolved

- [x] Clarify in prompt precedence rules and the sub-1000-byte shared adoption snippet that conversational execution-model or tier requests yield strictly to static canonical `orchestrator-tier:` declarations.
- [x] Forbid `Trunk Session` from reading synchronization script source or child execution protocol instructions into trunk context, keep post-approval hand-offs compact when the living window already holds the approved plan, and streamline `[plan review]` to lightweight observational workspace footprint verification on clean reports.
- [x] Add automated `unittest` structural contract assertions locking tier-precedence phrasing, black-box script and protocol read guards, and lightweight `[plan review]` verification while verifying the adoption snippet remains under 1,000 UTF-8 bytes and all hygiene checks pass.
