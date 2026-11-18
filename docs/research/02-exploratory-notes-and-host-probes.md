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

### Probe C: Native `swarm` Tool (`1e336cab` Clean Worker vs `f84130e1` `fork: "coordinator"`) & Quota-Pool Telemetry

Tested on `2026-11-18` under `8d058da7-262a-4ed6-8991-c3669ee786c0`:

- **Probe C-Clean (`1e336cab-6d51-400c-9492-07e4ce9d5f1f`, `model: "gemini-4-hydrogen-high"` without `fork`)**:
  - **Model Pinning & Latency**: Accurately resolved to `gemini-4-hydrogen` (`MODEL_PLACEHOLDER_M525`, 512k context, `API_PROVIDER_GOOGLE_GEMINI`). Turn 1 took `~16 s`; Turn 2 (`post_message` + `swarm_wait`) took `~26 s` (`SWARM_TURN1_OK_TURN2_OMEGA_772` verified) because every wakeup requires an extra LLM turn calling `read_board` before acting plus `post_message` + `swarm_wait` at exit (and board tools appear on the parent one turn after the initial `swarm add`).
  - **Stripped `invoke_subagent` Toolset**: SQLite `tokenBreakdown` and live execution confirmed clean `swarm` workers do **not** receive `invoke_subagent`, `send_message`, `manage_subagents`, or `define_subagent` (`[blocked] invoke_subagent is not available in my tool declarations`), breaking skills such as `egm-review` or `code-review` inside a `swarm` worker.
  - **Shared Board Namespace**: Occupies the parent conversation's single `.system_generated/swarm/{board.jsonl, members.json}` directory and injects `[swarm]` / `[board]` system notices.
- **Probe C-Fork (`f84130e1-8763-4233-b584-8fb54472ae76`, `model: "gemini-4-hydrogen-high"` with `fork: "coordinator"`)**:
  - **Model-Override Failure**: Although `members.json` recorded `"applied_model": "gemini-4-hydrogen-high"`, SQLite `gen_metadata` (`gen[220..221]`) proved execution actually ran on `MODEL_PLACEHOLDER_M667` (`gemini-pro-orchestrator` / `Orchestrator (Carbon)`), failing to offload from the parent planner model.
  - **Uncached Raw-Tool Bloat**: Cloned all raw `GENERIC` tool outputs from `steps 417..595` (`287,882` Chat Messages tokens -> `296,734` uncached `inputTokens`, `312,580` `estimatedTokensUsed`), ~25x heavier than `Living Memory Window` Option B.
- **Host Quota-Pool Sharing (`swarm{action: "models", all: true}`)**:
  - `claude-opus-5-5-{low,medium,high}`, `claude-sonnet-5-5-{low,medium,high}`, and `gpt-oss-120b-medium` reported identical `quota_remaining: "86%"` and identical `quota_resets: "2026-11-18T10:12:20Z"` (shared third-party quota pool).
  - All `gemini-4-*` and `gemini-3.8-flash-*` models reported identical `quota_remaining: "47%"` and `quota_resets: "2026-11-18T11:39:03Z"` (separate Google Gemini quota pool), confirming that `invoke_subagent`'s `"flash"` / `"pro"` / `"flash_lite"` tiers already cover 100% of genuine cross-pool quota offloading.

---

## 4. Verified Cross-Harness Native Subagent Matrix

Derived from installed harness reference docs (`egm/docs/harnesses.md`, `superpowers/skills/using-superpowers/references/{antigravity,claude-code,codex}-tools.md`, `builtin/skills/migrate-agent-settings/SKILL.md`):

| Harness | Native Subagent & Resume Primitives | Model Selection Support | Nesting Support | Key Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **Antigravity (`invoke_subagent`)** | `invoke_subagent` + `send_message(Recipient)` | 4-tier enum: `inherit \| flash_lite \| flash \| pro` (`agents/*.md` ignores `model:` frontmatter) | Yes | Cross-provider offload via `flash`/`pro` -> Hydrogen; exact non-tier model IDs require `/swarm` (22 models, single-board, poor nesting) |
| **Claude Code** | `Agent` (`Task`) + `resume` parameter | 4-tier alias: `inherit \| haiku \| sonnet \| opus` (tool arg or `.claude/agents/*.md` `model:`) | Yes (default depth 3; `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`) | Same-provider (Anthropic) tiers only |
| **Codex (V2)** | `spawn_agent` (`fork_turns: "none"`) + `followup_task` + `wait_agent` | Exact V2-allowed `model` + `reasoning_effort` (`low \| medium \| high`); `~/.codex/config.toml` `default_subagent_model` | Runtime-dependent (direct fallback) | Specifying `model` alone resets `reasoning_effort` unless both are passed |

---

## 5. Empirical Active-Window & Incremental Payload Sizes

Measured on `2026-11-18` across canonical `step_index`-folded planning trunks of `L0-1` (`n=66` `[CHECKPOINT .. Handoff]` initial windows, `n=18` `(PrevHandoff .. Handoff]` intra-epoch increments) and live session `8d058da7` (`n=8` initial, `n=7` increments), benchmarked against Antigravity `read_file`'s `46,080`-byte (`~45 KB`) single-read limit:

| Payload Mode | `L0-1` Initial Median / Max (`>45 KB`) | `L0-1` Increment Median / Max (`>45 KB`) | `8d058da7` Initial Median / Max | `8d058da7` Increment Median / Max (`>45 KB`) |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (Full + Raw Tools)** | `211.3 KB` / `817.8 KB` (`65/66`, `98%`) | `27.6 KB` / `176.0 KB` (`6/18`, `33%`) | `447.2 KB` / `531.0 KB` (`8/8`) | `28.3 KB` / `75.7 KB` (`3/7`) |
| **Option B (Dialogue + Checkpoint + Report)** | `44.1 KB` / `96.3 KB` (`29/66`, `44%`) | `4.3 KB` / `24.9 KB` (`0/18`, `0%`) | `108.2 KB` / `119.6 KB` (`8/8`) | `5.5 KB` / `10.1 KB` (`0/7`, `0%`) |
| **Option C (Hybrid `<=2 KB` Tools)** | `50.9 KB` / `123.1 KB` (`48/66`, `73%`) | `5.1 KB` / `33.4 KB` (`0/18`, `0%`) | `151.2 KB` / `167.8 KB` (`8/8`) | `6.9 KB` / `16.3 KB` (`0/7`, `0%`) |
