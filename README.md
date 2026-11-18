# Orchestrator

Dual-phase Plan and Execute orchestration for **Antigravity single-model sessions** (pairing a Planning `Trunk Session` with a bound native `Execution Subagent` via lossless compaction-bounded `Living Memory Window` inheritance).

---

## Installation (Pure-Skill Package)

`orchestrator` ships **only** a root [plugin.json](plugin.json) and the self-contained skill under [skills/orchestrator/](skills/orchestrator/SKILL.md)—with zero bundled `rules/`, startup hooks, persistent sidecars, or non-Antigravity manifest directories in V1.

- **As an Antigravity Pure-Skill Plugin**: Clone directly into your Antigravity plugins directory (`git clone https://github.com/titicheck/dual-brain-orchestrator.git ~/.gemini/config/plugins/orchestrator`) or run `agy plugin install <path>`.
- **As a Standalone Skill**: Symlink or copy `skills/orchestrator` into your Antigravity skills folder.
- **Zero-Config Chat Invocation**: Type `/orchestrator` directly in any unconfigured Antigravity chat bar to run the exact same unified workflow on built-in default `flash`.

---

## Shared Engineering Rule Adoption & Tier Precedence

### Canonical Rule Adoption Snippet (`< 1,000` bytes)

Add this snippet once in your shared engineering library `AGENTS.md` (or `~/.gemini/GEMINI.md`); everyday projects importing the shared library need **zero** `orchestrator`-specific entries:

```markdown
## Orchestrator

Adopt `orchestrator` for planning-and-execution scheduling unless this session exposes exact lowercase `exit_plan_mode` or `enter_plan_mode`, runs `/swarm` or `[swarm]`/`[board]` worker turns, or originated at `step 0` as a child subagent. Answer pure Q&A and zero-edit reviews directly (zero CLI calls even after compaction). Lock execution tier strictly to static `orchestrator-tier:` rules (conversational model requests never override `--tier`). Route inbound `[Message]` wakeups three ways (`bound_subagent_id` -> `[plan review]`; superseded executor -> ignore/kill; `Isolated Subagent` -> untouched). On edits or `[plan review]` post-compaction, run `check-origin` first (fail-closed on `SUBAGENT`/`UNKNOWN`) and verify `invoke_subagent`/`send_message` exist (halt cleanly with one line if absent).

orchestrator-tier: flash
```

### Static Tier Scope Precedence (`orchestrator-tier:`)

Execution tier accepts only `flash`, `pro`, `flash_lite`, or `inherit` and resolves strictly from static rules in descending specificity (conversational prompts never change the tier):

1. Workspace-local `AGENTS.md` / `GEMINI.md`
2. Direct global `~/.gemini/GEMINI.md`
3. `@[...]`-imported shared engineering rules (such as `engineering-kit/rules/AGENTS.md`)
4. Built-in default `"flash"`

To override one project only, add a single line to that project's `AGENTS.md`:

```markdown
orchestrator-tier: pro
```

---

## Architecture & Future Client Extension Boundary

- [skills/orchestrator/SKILL.md](skills/orchestrator/SKILL.md) — `Trunk Session` control loop, ordered Entry Gate, Three-Way Routing, Official Part 2 Planning & Part 7 `[plan review]`.
- [skills/orchestrator/references/execution-protocol.md](skills/orchestrator/references/execution-protocol.md) — Harness-neutral single-phase `Execution Subagent` rules (Official Parts 4, 5, and adapted Part 6).
- [skills/orchestrator/references/harnesses.md](skills/orchestrator/references/harnesses.md) — Antigravity V1 bindings (`invoke_subagent`, `send_message`, `manage_subagents`, sibling `logAbsoluteUri`, `sync_memory.py` CLI) and reserved Future Client Adapter Seam for Claude Code / Codex when targeted.
- [skills/orchestrator/scripts/sync_memory.py](skills/orchestrator/scripts/sync_memory.py) — Zero-dependency Python 3 standard-library CLI (`check-origin`, `sync`, `bind`, `reset`).

---

## Verification

### Automated Suites (`Seam 1` + `Seam 2A`)

```powershell
py -3 -m unittest discover -s tests -v
```
*(Use `python3 -m unittest discover -s tests -v` on POSIX.)*

### `Seam 2B` — Antigravity Live Smoke Verification & Native Comparison Checklist

Run these 4 interactive Antigravity checks on V1 and compare side-by-side against Native `Orchestrator`:

1. **Unconditional Native Orchestrator Deference**: Inside an `Orchestrator (Carbon)` / `Orchestrator (Argon)` session exposing exact lowercase `exit_plan_mode` / `enter_plan_mode`, invoke a coding task and `/orchestrator ...`; confirm native same-thread hot-swap runs untouched with zero `sync_memory.py` calls or spawned `Execution Subagent`.
2. **Non-Recursion, Post-Compaction Q&A, & Three-Way Routing**: Confirm child subagents and `[swarm]`/`[board]` workers stay single-phase across live and compacted sessions (`check-origin` fail-closed on `"SUBAGENT"` or `"UNKNOWN"`), pure Q&A turns post-compaction execute zero CLI subprocess calls, parallel `Isolated Subagent` `[Message]` replies stay on `Trunk Session`, and orphaned superseded `Execution Subagents` are ignored/killed.
3. **Static Tier Lock & Continuity Across Approve-First / `[plan review]`**: Confirm shared-rule adoption and unconfigured `/orchestrator` lock to `"flash"` (ignoring `"use pro"` in chat), adding `orchestrator-tier: pro` in workspace `AGENTS.md` triggers `tier != bound_tier` `SPAWN_NEW` rotation, and Approve-First / mid-flight cancel / `[plan review]` continue smoothly without losing active state.
4. **Parallel `Isolated Subagent` Orthogonality**: From a frontier single-model `Trunk Session` running `Execution Subagent` on `flash`, invoke `egm-*` / `research` / `code-review` and confirm those `Isolated Subagents` receive zero `Living Memory Window` injection and keep their own native or parent model behavior untouched.
