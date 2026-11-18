# Orchestrator Adaptation Map

Label: `wayfinder:map`

## Destination

A minimal, Occam's-razor specification (`.scratch/orchestrator-v1/spec.md`) and settled domain decisions (`GLOSSARY.md`, `docs/adr/`) derived directly from the verbatim Official Orchestrator system—modifying only what is strictly necessary to replace same-thread model hot-swap with Trunk-to-Native-Subagent lossless interop across client harnesses.

## Notes

- Authoritative official baseline: [Official Orchestrator Underlying System Baseline](../../docs/research/01-official-orchestrator-system.md).
- Settled domain model & decisions: [GLOSSARY.md](../../GLOSSARY.md), [ADR-0001](../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md), and [ADR-0002](../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md).
- Non-binding exploratory history & host measurements: [Exploratory Discussions and Host Empirical Probes](../../docs/research/02-exploratory-notes-and-host-probes.md).
- Skills to consult: `grilling`, `domain-modeling`, `prototype`, and `writing-for-agents`.
- Standing preferences: Pure English repository files; preserve Official Orchestrator wording and behavior everywhere thread separation does not force a change; resolve one ticket at a time.

## Decisions so far

- [Extract Official Orchestrator Baseline and Archive Exploratory Notes](issues/01-extract-official-orchestrator-baseline.md): Extracted the complete 9-part Official Orchestrator and native subagent baseline into `docs/research/01-official-orchestrator-system.md` and archived all prior explorations and host probes as non-binding reference in `docs/research/02-exploratory-notes-and-host-probes.md`.
- [Occam's-Razor Adaptation from Same-Thread Hot-Swap to Native Subagent Interop](issues/02-occam-adaptation-to-native-subagents.md): Locked the 3 minimal surgical adaptations—client-native subagents, `CHECKPOINT`-bounded Living Memory Window inheritance + incremental continuation + compaction-synced rotation ([ADR-0002](../../docs/adr/0002-checkpoint-bounded-living-memory-inheritance.md)), and unified `<report>` return into Official `[plan review]` ([ADR-0001](../../docs/adr/0001-unified-subagent-report-return-into-plan-review.md)).

## Not yet specified

- Minimal prototype check if any adapted interop mechanic remains empirically unproven after Ticket `02`.
- End-to-end compliance test scenarios (`writing-skills`) once V1 `SKILL.md` is authored.

## Out of scope

- Publishing to a remote GitHub repository before local V1 verification completes.
