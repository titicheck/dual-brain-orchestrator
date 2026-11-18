# 01: Living Memory Window Synchronization CLI

**What to build:** A standalone, zero-dependency Python 3 command-line utility and black-box replay test suite that deterministically extracts, paginates, and watermarks a `Trunk Session`'s active `Living Memory Window` from append-only conversation transcripts so an `Execution Subagent` inherits complete conversational context on first spawn, receives only newly appended dialogue on continuations, and automatically rotates when a new compaction checkpoint occurs.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Folds append-only JSONL conversation logs by canonical `step_index` so any later record at step `k` invalidates and discards earlier records at `>= k` from rewound, retried, or edited turns, resolving truncated step bodies from the companion full-log stream whenever `truncated_fields` indicates content truncation.
- [ ] Extracts the active compaction-bounded `Living Memory Window` (`[latest CHECKPOINT (or step 0) .. current_step]`), retaining compaction summaries (`CHECKPOINT`), verbatim user prompts stripped of host metadata envelopes (`USER_INPUT`), visible assistant replies (`MODEL` / `PLANNER_RESPONSE`), and prior inbound subagent `<report>` messages while omitting raw tool outputs (`GENERIC`), ephemeral system prompts, and private chain-of-thought (`thinking`).
- [ ] Splits exported Markdown snapshots and incremental slices on clean message/line boundaries into sequential pages strictly under `40,000` bytes per page so every page fits within a single `46,080`-byte host file read without truncation or mid-line corruption.
- [ ] Implements explicit two-step session state tracking (`sync` preview + `commit` watermark update): emits `SPAWN_NEW` with full active-window pages when no `Execution Subagent` is bound or when `latest_checkpoint_step > recorded_checkpoint_step`, emits `RESUME_EXISTING` with `(last_synced_step .. current_step]` delta pages (or `delta_empty = true` when no new retained steps exist) within the same compaction epoch, and leaves watermarks untouched if `commit` is not called.
- [ ] Passes an automated black-box subprocess test suite (`Seam 1`) exercising initial snapshot filtering, canonical `step_index` rewind folding, `truncated_fields` resolution, `<40,000`-byte pagination, incremental delta export, empty-delta elision, uncommitted-dispatch rollback safety, and `CHECKPOINT` epoch rotation against synthetic and empirical-shaped transcript fixtures using only the Python 3 standard library.
