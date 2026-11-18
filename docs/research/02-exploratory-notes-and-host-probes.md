# Exploratory Discussions and Empirical Host Probes

> **Non-Binding Exploratory Context & Empirical Facts**: This file archives our earlier architectural explorations and empirical machine probes gathered on `2026-11-18`. Everything in Section 1 reflects superseded or open brainstorming rather than settled decisions; Sections 2–4 record observed host behavior and tool constraints.

---

## 1. Summary of Prior Architectural Explorations (Non-Binding)

1. **Why `SKILL.md` Cannot Hot-Swap Models Inside One Thread**: A `SKILL.md` file injects instructions into the active session's prompt, whereas Antigravity locks the session's cloud `model` routing in the host process (and `exit_plan_mode` / `enter_plan_mode` are host-level tools only exposed on `Orchestrator` virtual models). Pure models such as Claude Opus 5.5 or Sonnet 5.5 therefore cannot switch models within the same thread via prompt rules alone.
2. **Carrier Candidates Considered and Superseded**:
   - *External `agy -p --conversation` CLI wrapper*: Considered for exact `--model` pinning and cross-harness reuse, then superseded after Probe B showed 17–70 s startup latency, 0% Turn 2 cache hits, headless Windows permission denials, and isolated `~/.gemini/antigravity-cli/` storage.
   - *Built-in `/swarm` plugin*: Considered for exact selection across all 22 host models and built-in sidecar board, then dropped as a core dependency because `/swarm` is an Antigravity-specific plugin with a single shared `board.jsonl` per session that does not compose cleanly with nested subagents or other harnesses.
   - *Built-in client-native subagents (`invoke_subagent` + `send_message`)*: Selected for exploration and verified by Probe A.
3. **Optional Sidecar UI Panel Deferral**: Explored adding a Swarm-like auxiliary pane sidecar; deferred out of V1 to avoid running a daemon process or locking the core protocol to Antigravity UI APIs while keeping machine-readable local files available if visual tooling is ever desired later.
4. **Reset to Official-First Occam's Razor (`2026-11-18`)**: Rather than inventing custom schemas, file formats, or speculative lifecycle policies upfront, we reset to extracting the complete Official Orchestrator system (`01-official-orchestrator-system.md`) and making only the minimal modifications strictly required by cross-session subagent separation.

---

## 2. Verified Antigravity Local Session Storage Topology

Inspected directly on Windows (`~/.gemini/antigravity/` and `~/.gemini/antigravity-cli/`):

1. **Three-Part Per-Session Storage**:
   - **Trajectory SQLite DB** (`conversations/<ConvID>.db`): `steps`, `gen_metadata` (exact `responseModel`, `modelDisplayName`, `apiProvider`, `inputTokens`, `cacheReadTokens`, `outputTokens`, `timeToFirstToken`, `streamingDuration`, and 10-group `tokenBreakdown`), `trajectory_meta`, and `parent_references`.
   - **Brain Directory** (`brain/<ConvID>/`): `.system_generated/logs/transcript.jsonl` (compact) and `transcript_full.jsonl` (untruncated) plus `chunks/`, `.system_generated/steps/<idx>/output.txt`, `.system_generated/messages/`, and root `*.md` + `*.md.metadata.json` (`summary`, `updatedAt`, `userFacing: true`) for UI Artifacts.
   - **Global Summary Index** (`conversation_summaries.db`): User-created main conversations have `parent_conversation_id = ""`, `nesting_depth = 0`, and `annotations/<ConvID>.pbtxt` (shown in sidebar history). Native `invoke_subagent` children live in **sibling** `brain/<SubID>/` and `conversations/<SubID>.db` paths linked via `parent_conversation_id = "<TrunkID>"` and `nesting_depth = 1`, with empty `title` and no `annotations` file (shown in the parent's `Subagents` pane rather than main history).
2. **Append-Only Duplicate `step_index` on Rewind / Edit / Retry**:
   - Live inspection of `8d058da7-262a-4ed6-8991-c3669ee786c0` confirmed that when a turn is edited, retried, or rewound, the host does **not** truncate old lines from `transcript.jsonl`; it appends new lines reusing the same `step_index` (e.g., `217..223` followed by a new `217..219`).
   - Any reader extracting dialogue history from `transcript.jsonl` must fold lines by `step_index` (latest occurrence at index `k` supersedes prior lines at `>= k` from earlier aborted branches).

---

## 3. Verified Carrier Probe Measurements (Probes A & B)

### Probe A: Native `invoke_subagent` + `send_message`

Tested under both `Orchestrator (Carbon)` and `Claude Opus 5.5 (Medium)` main conversations:

| Main Session Model | `invoke_subagent` `Model` Arg | Resolved `responseModel` (`gen_metadata`) | API Provider | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `Orchestrator (Carbon)` | `"flash_lite"` | `gemini-3.5-flash-lite` | `API_PROVIDER_GOOGLE_GEMINI` | 128k max context |
| `Orchestrator (Carbon)` | `"flash"` | `gemini-4-hydrogen-tiered-high` | `API_PROVIDER_GOOGLE_GEMINI` | 512k max context |
| `Orchestrator (Carbon)` | `"pro"` | `gemini-4-hydrogen-tiered-xhigh` | `API_PROVIDER_GOOGLE_GEMINI` | 512k max context |
| `Claude Opus 5.5 (Medium)` | `"flash"` | `gemini-4-hydrogen-tiered-high` | `API_PROVIDER_GOOGLE_GEMINI` | Offloads execution to Google Gemini pool |
| `Claude Opus 5.5 (Medium)` | `"pro"` | `gemini-4-hydrogen-tiered-xhigh` | `API_PROVIDER_GOOGLE_GEMINI` | Offloads execution to Google Gemini pool |
| `Claude Opus 5.5 (Medium)` | `"inherit"` | `claude-opus-5-5-medium` | `API_PROVIDER_ANTHROPIC` | Consumes parent Anthropic quota pool |

- **Two-Turn Resumption (`90c3ef09-fe59-4916-821d-2ae46b0fa96a`, `Model: "flash"`)**:
  - Turn 1 (`invoke_subagent`): Wrote `TURN1_OK` without permission prompts (~13 s), 85.9%–87.3% cache read on internal steps.
  - Turn 2 (`send_message`): Recalled Turn 1 token (`DELTA_991`) and appended `_TURN2` (~12 s), achieving **87.7%–88.1% prefix cache hit** (`16,252`–`16,804` `cacheReadTokens` vs `2,273`–`2,287` new `inputTokens`).

### Probe B: External `agy` CLI (`agy -p --conversation`)

Tested with `--model gemini-4-hydrogen-high --mode auto` (`80404dda-4205-4c19-9d51-159e3741f164`):

- **Latency**: Turn 1 `70.48 s` wall-clock (`3.25 s` model generation + ~67 s embedded Language Server cold start); Turn 2 `17.19 s`.
- **Headless Windows Permissions**: `--mode auto` fell back to `request-review` (`terminal sandbox is not available on this host`), auto-denying `write_file` unless `--dangerously-skip-permissions` or `settings.json` allow-rules are configured.
- **Prefix Cache & Isolation**: Turn 2 reported `cache_read_tokens: 0` (`input_tokens: 13,895`), stored under `~/.gemini/antigravity-cli/` with `parentConversationId = ""`.

---

## 4. Verified Cross-Harness Native Subagent Matrix

Derived from installed harness reference docs (`egm/docs/harnesses.md`, `superpowers/skills/using-superpowers/references/{antigravity,claude-code,codex}-tools.md`, `builtin/skills/migrate-agent-settings/SKILL.md`):

| Harness | Native Subagent & Resume Primitives | Model Selection Support | Nesting Support | Key Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **Antigravity (`invoke_subagent`)** | `invoke_subagent` + `send_message(Recipient)` | 4-tier enum: `inherit \| flash_lite \| flash \| pro` (`agents/*.md` ignores `model:` frontmatter) | Yes | Cross-provider offload via `flash`/`pro` -> Hydrogen; exact non-tier model IDs require `/swarm` (22 models, single-board, poor nesting) |
| **Claude Code** | `Agent` (`Task`) + `resume` parameter | 4-tier alias: `inherit \| haiku \| sonnet \| opus` (tool arg or `.claude/agents/*.md` `model:`) | Yes (default depth 3; `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`) | Same-provider (Anthropic) tiers only |
| **Codex (V2)** | `spawn_agent` (`fork_turns: "none"`) + `followup_task` + `wait_agent` | Exact V2-allowed `model` + `reasoning_effort` (`low \| medium \| high`); `~/.codex/config.toml` `default_subagent_model` | Runtime-dependent (direct fallback) | Specifying `model` alone resets `reasoning_effort` unless both are passed |
