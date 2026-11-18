# Head-to-Head A/B Benchmark and KV-Cache Telemetry

Empirical primary-source benchmark comparing Antigravity's native `Orchestrator (Carbon)` against the `orchestrator` V1 pure-skill plugin on an aligned `Gemini 4 Carbon (High)` planner (`EFFORT LEVEL: 1.00`), decoded directly from local Antigravity SQLite trajectory databases, JSONL transcripts, and `Living Memory Window` session state on `2026-11-18`–`2026-11-19`.

---

## 1. Controlled 1:1 Setup and Conversation Topology

Both groups ran the identical multi-round Python `ledger` package extension sequence in isolated Git sandboxes (`ab-native` vs `ab-plugin`):

- **Group A — Native `Orchestrator (Carbon)`** (`ab-native`, conversation `d03a7aff-3a99-4c86-9835-57cff50c2f5f`):
  - Planning model: `gemini-pro-orchestrator` (`Orchestrator (Carbon)`, `EFFORT LEVEL: 1.00`).
  - Execution model: `gemini-flash-worker-agy` (`Gemini 4 Hydrogen (Orchestrator)`).
  - Child spawned when asked in Round 2a for `pro`: `be3acef9-d4e7-423a-91b5-46ffd8bbfd20` (`define_subagent("pro-executor")` + `invoke_subagent(Model="pro")` -> `gemini-4-hydrogen-tiered-xhigh`).
- **Group B — Single-Model `Gemini 4 Carbon (High)` + `orchestrator` Plugin** (`ab-plugin`, conversation `2ae3212a-7d91-473e-8822-4ce9eeaa2bc4`):
  - Trunk model: `gemini-4-carbon` (`Gemini 4 Carbon (High)`, identical `Carbon` `High` / `1.00` base).
  - Bound `Execution Subagent` #1 (`flash`): `cee193f2-d1a2-47ea-9912-322f4fbafbd8` (`gemini-4-hydrogen-tiered-high`).
  - Rotated `Execution Subagent` #2 (`pro`): `72e8ba49-5e1c-42cc-8d69-49a658f806a3` (`gemini-4-hydrogen-tiered-xhigh`).
  - Parallel `Isolated Subagent` (`research`): `49cee118-3be0-4be7-a35c-5c5e94cd1419` (`gemini-4-carbon`).

---

## 2. `Seam 2B` Interactive Smoke Verification Matrix

All 7 observed interactive checks passed:

| Check | Primary-Source Evidence Observed | Verdict |
|---|---|---|
| Approve-First halt (R1a) | `d03a7aff` (`step 0..22`) and `2ae3212a` (`step 0..17`) both stopped after plan output with zero edits and zero `state.json` writes | PASS |
| Initial `SPAWN_NEW` + Option B window (R1b) | `2ae3212a` exported `pages/page_001.md`, spawned `cee193f2` (`flash` -> `gemini-4-hydrogen-tiered-high`), and entered `[plan review]` on `<report>` | PASS |
| `RESUME_EXISTING` delta + chat-tier immunity (R2a) | `2ae3212a` ignored conversational `"switch to the pro model"` and resumed `cee193f2` via `send_message` (`step 21..35`) preserving Round 1 rules | PASS |
| Static-rule rotation + retirement quarantine (R2b) | Editing `ab-plugin/AGENTS.md` to `orchestrator-tier: pro` triggered `SPAWN_NEW` to `72e8ba49` (`gemini-4-hydrogen-tiered-xhigh`) and recorded `"retired_subagent_max_step": {"cee193f2-d1a2-47ea-9912-322f4fbafbd8": 60}`; final `page_001.md` measured `14,015` B / `194` lines | PASS |
| Zero-CLI Pure Q&A Fast-Path (R3a) | `2ae3212a` `step 74..75` answered directly in 1 LLM call (`97.4%` cache hit, zero CLI calls, zero subagent wakes) | PASS |
| `Isolated Subagent` orthogonality & non-recursion (R3b) | `49cee118` ran on `Gemini 4 Carbon (High)` with zero window pages; Route 3 skipped `[plan review]`; zero `scratch/orchestrator` dirs in any child | PASS |
| Unconditional Native `Orchestrator` deference (R3c) | Typing `/orchestrator ...` in `d03a7aff` (`step 67..78`) yielded silently to native `exit_plan_mode` with zero `sync_memory.py` calls | PASS |

- Workspace verification outputs after all rounds: `ab-native` `unittest` passed `16` tests (`0.001s`); `ab-plugin` `unittest` passed `18` tests (`0.001s`). `ab-plugin`'s `ledger/formatter.py` additionally used `Decimal` over formatted row strings for exact `TOTAL` consistency.

---

## 3. Decoded Per-Round SQLite `gen_metadata` & Wall-Clock Telemetry

| Round & Phase | Group A (`ab-native`) | Group B (`ab-plugin`) |
|---|---|---|
| **R1a Plan (Approve-First)** | `10` Carbon calls: `in_new=41,657`, `cache=209,607` (`83.4%`), `out=11,118` (`9,374+1,744`), LLM `245.1s`, wall `226.0s` | `7` Carbon calls: `in_new=34,814`, `cache=137,127` (`79.8%`), `out=12,550` (`10,358+2,192`), LLM `229.4s`, wall `108.0s` |
| **R1b Trunk / Hand-off** | `1` Carbon call: `in_new=35,991`, `cache=0` (`0.0%`), `out=1,359` (`238+1,121`), LLM `20.3s` | `7` Carbon calls: `in_new=74,461`, `cache=240,639` (`76.4%`), `out=9,417` (`5,822+3,595`), LLM `200.6s` |
| **R1b Execution (`Hydrogen`)** | `5` calls (`Hydrogen Orchestrator`): `in_new=40,926`, `cache=133,004` (`76.5%`), `out=4,851` (`1,429+3,422`), LLM **`34.8s`**, total wall `67.0s` | `6` calls (`cee193f2` `flash`): `in_new=37,659`, `cache=121,976` (`76.4%`), `out=5,103` (`894+4,209`), LLM **`34.9s`**, total wall `190.0s` |
| **R2a Plan / Dispatch + Review** | `2` Carbon calls: `in_new=60,658`, `cache=48,943` (`44.7%`), `out=12,538` (`11,105+1,433`), LLM `186.6s` | `8` Carbon calls: `in_new=122,145`, `cache=556,790` (`82.0%`), `out=24,959` (`22,124+2,835`), LLM `392.5s` |
| **R2a Execution** | Parent `5` (`34.2s`) + Child `be3acef9` (`Hydrogen XHigh`, `7` calls, `28,075` new / `89,894` cache `76.2%`, `49.4s`), wall `277.0s` | `cee193f2` `RESUME_EXISTING` (`5` calls, `in_new=45,665`, `cache=147,522` `76.4%`, `out=3,435`, LLM **`28.6s`**), wall `396.0s` |
| **R2b Static Rotate (`pro`)** | *(N/A)* | Trunk `6` calls (`153.1s`) + `72e8ba49` `SPAWN_NEW` (`9` calls, `in_new=46,894`, `cache=229,252` **`83.0%`**, `out=3,755`, LLM **`48.9s`**), wall `169.0s` |
| **R3a Pure Q&A** | `1` Carbon call: `in_new=79,325`, `cache=0` (`0.0%` post-idle TTL), LLM `16.2s`, wall `0.0s` | `1` Carbon call: `in_new=2,964`, `cache=110,140` (**`97.4%`**), LLM `36.1s`, wall `1.0s` |
| **R3b / R3c** | R3c (`/orchestrator` deference): `2` Carbon (`28.8s`) + `3` Hydrogen (`20.2s`), wall `54.0s` | R3b (`research` `49cee118`): Trunk `4` (`60.0s`) + Child `4` (`51.8s`), wall `75.0s` |

---

## 4. Three Identified Bottlenecks and Fixes Applied

1. **Prompt Precedence Tug-of-War (`B-Trunk` `step 39..41`) & Black-Box Script Reads**:
   - *Observed symptom*: `SKILL.md`'s generic *"never override ... user instructions"* collided visually with *"Ignore conversational model mentions"*. At `step 39..41`, `Carbon (High)` spent **`16,656` thinking tokens (`218.1s` at `gen[15]`)** resolving rule priority and called `read_file` on `sync_memory.py` (growing cached prompt prefix from `56,724` at `gen[15]` to `84,299` at `gen[17]`), while also reading `execution-protocol.md` into `Trunk Session`.
   - *Fix*: Clarify in `SKILL.md` (`Prompt Precedence`) and the `< 1,000`-byte `README.md` snippet that conversational model requests yield strictly to static `orchestrator-tier:` rules, and forbid `Trunk Session` from calling `read_file` on `sync_memory.py` or `execution-protocol.md`.
2. **Post-Approve-First Plan Duplication & Heavy `[plan review]` Audits**:
   - *Observed symptom*: In R1b (`gen[09]`, `step 22`), after outputting a full plan in R1a (`page_001.md`), `Trunk Session` emitted `4,176` output tokens (`54.7s`) re-expanding the plan; in `[plan review]`, it re-read every modified file and re-ran both `unittest` and `pytest` despite clean `<report>` outputs.
   - *Fix*: Instruct `SPAWN_NEW` to keep post-Approve-First `<plan>` compact when `pages/page_*.md` already exports the just-approved plan, and instruct `[plan review]` to verify clean `<report>` completions with lightweight observational `git status --short` / `git diff --stat` checks.
3. **Asymmetric Control Prompt in Round 2a**:
   - *Observed symptom*: Asking `"switch to the pro model"` on Group A legitimately triggered Official `Orchestrator`'s generic `<subagents>` delegation (`be3acef9`).
   - *Fix*: Remove the conversational tier override string from the shared A/B Round 2a prompt in the test playbook and isolate conversational-tier immunity testing strictly to Group B.

---

## 5. KV-Cache Physics and `SPAWN_NEW` Epoch-GC Analysis

- **Dual-Session Monotonic Prefix vs Native Same-Thread Hot-Swap Resets**: Native same-thread switching between `Carbon` and `Hydrogen` crosses distinct model KV caches and swaps system/tool declarations, causing `cache=0` cold prefills on transitions (`gen[11]`, `gen[16]`, `gen[18]` in `d03a7aff`) while permanently retaining verbose `Hydrogen` tool outputs inside `Carbon`'s thread. Conversely, Option B dual-session scheduling keeps `Trunk Session` free of raw tool output and maintains monotonic single-model prefixes on both threads (`gen[28]` at `97.4%`, `gen[30]` at `98.1%` within server cache TTL in `2ae3212a`, and `87.7%–88.1%` child resumption cache hits in [Probe A](02-exploratory-notes-and-host-probes.md#L48-L50)). Official `Orchestrator` only holds a latency edge on trivial 1–2 turn runs where unobstructed `Hydrogen` answers the user directly without waking `Carbon`.
- **Negligible `SPAWN_NEW` Rotation Cost (`3.45s` / `19.2k` prefill on `72e8ba49`)**: When `72e8ba49` spawned in Round 2b, only `gen[00]` incurred a cold prefill (`in_new=19,183`, `cache=0`, `ttft=3.45s`); `gen[01]` immediately hit `cache=19,184`, reaching **`83.0%`** aggregate cache hit across its 9-step task.
- **Why In-Place Memory Overwriting Degrades Rather Than Helps ([ADR-0002](../adr/0002-checkpoint-bounded-living-memory-inheritance.md))**: Transformer KV caches are append-only; injecting a "replacement window" into an existing `Execution Subagent` cannot evict `200+ KB` of prior raw `GENERIC` tool outputs already in its thread. Keeping a rotated/rewound subagent alive forces every subsequent step to pay cache-read latency and cost on dead tool noise, triggers uncontrollable mid-execution child compaction, and invites recency-bias context poisoning on edited/rewound turns. `SPAWN_NEW` acts as deterministic **Epoch Garbage Collection** across the five deterministic boundaries (first spawn, `tier != bound_tier`, trunk `checkpoint_step` advance, rewind digest/step mismatch, or post-crash `reset`).
