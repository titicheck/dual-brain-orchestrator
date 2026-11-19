# 06: Clarify Isolated Subagent User-Rule Tier Orthogonality

**What to build:** Resolve subjectless tier-scoping ambiguities across [SKILL.md](../../../skills/orchestrator/SKILL.md) (lines 12, 41, 48), [README.md](../../../README.md) (lines 26, 73), [spec.md](../spec.md) (lines 35, 85, 154), and [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) (line 23) so `orchestrator`'s static `orchestrator-tier:` lock and conversational-override immunity apply strictly to the single bound `Execution Subagent`, while parallel `Isolated Subagents` remain untouched by `orchestrator-tier:` and free to follow external user, host, or skill model rules without coupling `orchestrator` to any external shared library or specific user-rule key name. Enforce the invariant with minimal literal-substring anti-regression guards in [test_package_contracts.py](../../../tests/test_package_contracts.py).

**Blocked by:** 05: Conditional Host Transcript Schema Probe and Neon Deference Documentation

**Status:** resolved

## Final Converged Scope

1. **[SKILL.md](../../../skills/orchestrator/SKILL.md) (lines 12, 41, 48):**
   - Line 12: Scoped `"conversational execution-model or tier requests"` to `"conversational model or tier requests for the bound Execution Subagent"`.
   - Line 41: Prefixed with `"For the bound Execution Subagent only, ignore conversational model mentions in chat..."`.
   - Line 48: Simplified `Parallel Isolated Subagent Orthogonality` to `"run directly from Trunk Session with zero Living Memory Window injection and untouched by orchestrator-tier:"`, removing subjectless `"on their own native models"` and `"zero tier overrides"`.

2. **[README.md](../../../README.md) (lines 26, 73):**
   - Line 26 (inside the `< 1,000`-byte `## Orchestrator` adoption snippet): Updated `"Lock execution tier strictly..."` to `"Lock the bound Execution Subagent tier strictly..."`.
   - Line 73 (`Seam 2B` check 4): Replaced `"keep their own native or parent model behavior untouched"` with `"remain untouched by orchestrator-tier:"`.

3. **[spec.md](../spec.md) (lines 35, 85, 154) and [ADR-0004](../../../docs/adr/0004-coexistence-boundaries-and-foreman-subagent-delegation.md) (line 23):**
   - Aligned all remaining `"zero model overrides"` / `"or model overrides"` / `"retain 100% of their native skill/host model rules"` phrases to `"untouched by orchestrator-tier:"`.

4. **[test_package_contracts.py](../../../tests/test_package_contracts.py) (`test_trunk_efficiency_and_tier_precedence_guards`):**
   - Added minimal literal-substring anti-regression assertions (avoiding brittle multi-clause regexes):
     - `self.assertNotIn("zero tier overrides", skill_text.lower())`
     - `self.assertIn("untouched by `orchestrator-tier:`", skill_text)`
     - `self.assertIn("untouched by `orchestrator-tier:`", readme_text)`
     - `self.assertIn("bound `execution subagent`", lower)` inside the `adoption_blocks` loop.

5. **Out of scope:**
   - Do not reference or couple `orchestrator` to any external shared library or specific user-rule key name.
   - Do not modify [execution-protocol.md](../../../skills/orchestrator/references/execution-protocol.md), [harnesses.md](../../../skills/orchestrator/references/harnesses.md), or [sync_memory.py](../../../skills/orchestrator/scripts/sync_memory.py).

## Acceptance Checklist

- [x] Scope `SKILL.md` lines 12, 41, and 48 strictly to the bound `Execution Subagent` and mark `Isolated Subagents` as `untouched by orchestrator-tier:`.
- [x] Scope `README.md` line 26 (`< 1,000`-byte adoption snippet) to the bound `Execution Subagent` and align `Seam 2B` check 4 (line 73) to `untouched by orchestrator-tier:`.
- [x] Align `spec.md` (lines 35, 85, 154) and `ADR-0004` (line 23) to `untouched by orchestrator-tier:`.
- [x] Add minimal literal-substring anti-regression guards in `tests/test_package_contracts.py` without brittle multi-clause regexes.
- [x] Run `py -3 -m unittest discover -s tests -v` and confirm all tests, byte-budget checks, relative markdown links, and zero-CJK hygiene checks pass.

## Comments

- 2026-11-19 (EGM Review Resolution — `egm-design`, `egm-zoom-out`, `egm-implementation-readiness` at `flash`):
  - `egm-design` identified missing `bound Execution Subagent` subject scoping at `SKILL.md:12,41` and `README.md:26` as well as residual phrasing in `spec.md:35,154`.
  - `egm-zoom-out` rejected enumerating external resolution taxonomies (`skill, host, or user-rule model resolution`) inside `orchestrator` and rejected brittle natural-language regexes in favor of decoupled boundary phrasing (`untouched by orchestrator-tier:`).
  - Converged on scoping all four trunk/doc sites + `spec.md` + `ADR-0004:23` using decoupled `untouched by orchestrator-tier:` wording paired with four minimal literal-substring contract assertions in `tests/test_package_contracts.py`.
  - Per explicit user ruling, [execution-protocol.md](../../../skills/orchestrator/references/execution-protocol.md) and [harnesses.md](../../../skills/orchestrator/references/harnesses.md) were intentionally left untouched so user-level nested-subagent safety caps remain enforceable without requiring forced `Model="inherit"` overrides inside nested execution workers.
