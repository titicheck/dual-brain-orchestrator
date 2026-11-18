# Orchestrator Adaptation Map

Label: `wayfinder:map`

## Destination

A minimal, Occam's-razor specification (`.scratch/orchestrator-v1/spec.md`) and settled domain decisions (`GLOSSARY.md`, `docs/adr/`) derived directly from the verbatim Official Orchestrator system—modifying only what is strictly necessary to replace same-thread model hot-swap with Trunk-to-Native-Subagent lossless interop optimized in V1 for Antigravity with a reserved cross-harness adapter seam.

## Notes

- Authoritative official baseline: [Official Orchestrator Underlying System Baseline](../../docs/research/01-official-orchestrator-system.md).
- Settled domain model & decisions: [GLOSSARY.md](../../GLOSSARY.md), [ADR-0001](../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md), [ADR-0002](../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md), [ADR-0003](../../docs/adr/0003-matt-pure-skill-packaging-and-shared-rule-adoption.md), [ADR-0004](../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md), and [ADR-0005](../../docs/adr/0005-universal-native-subagent-carrier-and-swarm-deference.md).
- Non-binding exploratory history & host measurements: [Exploratory Discussions and Host Empirical Probes](../../docs/research/02-exploratory-notes-and-host-probes.md).
- Skills to consult: `grilling`, `domain-modeling`, `prototype`, and `writing-for-agents`.
- Standing preferences: Pure English repository files; preserve Official Orchestrator wording and behavior everywhere thread separation does not force a change; resolve one ticket at a time.

## Decisions so far

- [Extract Official Orchestrator Baseline and Archive Exploratory Notes](issues/01-extract-official-orchestrator-baseline.md): Extracted the complete 9-part Official Orchestrator and native subagent baseline into `docs/research/01-official-orchestrator-system.md` and archived all prior explorations and host probes as non-binding reference in `docs/research/02-exploratory-notes-and-host-probes.md`.
- [Occam's-Razor Adaptation from Same-Thread Hot-Swap to Native Subagent Interop](issues/02-occam-adaptation-to-native-subagents.md): Locked the 3 minimal surgical adaptations—client-native subagents, `CHECKPOINT`-bounded Living Memory Window inheritance + symmetric two-phase `pending_sync` -> `bind` + compaction-synced rotation ([ADR-0002](../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md)), and unified `<report>` return into Official `[plan review]` ([ADR-0001](../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md)).
- [Activation Modes, Coexistence Boundaries, and Package Structure](issues/03-activation-coexistence-and-packaging.md): Locked single-manifest pure-skill `plugin.json` packaging (deferring `.claude-plugin/` and `.codex-plugin/` until targeted, zero top-level `rules/` directory) + `README.md` shared-library/project adoption snippet + unified single Official Orchestrator mode across rule adoption and `/orchestrator` chat invocations + static scope-precedence tiering (`workspace-local AGENTS.md/GEMINI.md > direct global ~/.gemini/GEMINI.md > @[...]-imported shared engineering rules > built-in default "flash"`) ([ADR-0003](../../docs/adr/0003-matt-pure-skill-packaging-and-shared-rule-adoption.md)), along with unconditional native Orchestrator deference, prompt + disk `step 0` subagent non-recursion, zero-memory `Isolated Subagent` passthrough, and `Execution Subagent` delegation ([ADR-0004](../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md), [ADR-0005](../../docs/adr/0005-universal-native-subagent-carrier-and-swarm-deference.md)).

## Synthesized Specification

- [Orchestrator V1 Specification](../orchestrator-v1/spec.md) (`Status: ready-for-agent`): Complete V1 feature specification synthesized from [01-official-orchestrator-system.md](../../docs/research/01-official-orchestrator-system.md), [GLOSSARY.md](../../GLOSSARY.md), and `ADR-0001`–`ADR-0005`.

## Out of scope

- Publishing to a remote GitHub repository before local V1 verification completes.
