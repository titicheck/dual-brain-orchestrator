#!/usr/bin/env python3
"""Antigravity Living Memory Window synchronization CLI for Orchestrator."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import tempfile
import time
from typing import Any, NoReturn

MAX_PAGE_BYTES = 40000
MAX_PAGE_LINES = 750
MESSAGE_HEADER_RE = re.compile(
    r"^\[Message\][ \t]+timestamp=\S+[ \t]+sender=(\S+)[ \t]+priority=\S+[ \t]+content=(.*)$",
    re.DOTALL,
)
SUBAGENT_USER_PREFIXES = (
    "[swarm]",
    "[board]",
    "[EXECUTION SUBAGENT — SINGLE PHASE]",
)
_STATE_REQUIRED_KEYS = frozenset(
    {
        "bound_subagent_id",
        "execution_subagent_ids",
        "retired_subagent_max_step",
        "pending_sync",
    }
)
_STATE_LEGACY_KEYS = frozenset(
    {
        "bound_tier",
        "checkpoint_step",
        "last_synced_step",
        "prefix_digest",
        "lmw_bytes",
    }
)
_PENDING_REQUIRED_KEYS = frozenset({"synced_through"})
_PENDING_LEGACY_KEYS = frozenset(
    {"tier", "checkpoint_step", "prefix_digest", "lmw_bytes"}
)


class CliError(Exception):
    """Structured CLI error mapped to deterministic exit codes."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class CliArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass overriding parser error exit code from 2 to 1."""

    def error(self, message: str) -> NoReturn:
        sys.stderr.write(f"error: {message}\n")
        raise SystemExit(1)


def normalize_lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _retry_on_permission_error(
    fn: Any, attempts: int = 3, delay_s: float = 0.015
) -> Any:
    for idx in range(attempts):
        try:
            return fn()
        except PermissionError:
            if idx + 1 >= attempts:
                raise
            time.sleep(delay_s)


def _is_strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def default_state() -> dict[str, Any]:
    return {
        "bound_subagent_id": None,
        "execution_subagent_ids": [],
        "retired_subagent_max_step": {},
        "pending_sync": None,
    }


def _validate_pending_sync(pending: Any) -> dict[str, Any] | None:
    if pending is None:
        return None
    if not isinstance(pending, dict):
        raise CliError(1, "invalid state.json: pending_sync must be an object or null")
    for key in pending:
        if key not in _PENDING_REQUIRED_KEYS and key not in _PENDING_LEGACY_KEYS:
            raise CliError(1, f"invalid state.json: unexpected pending_sync key {key!r}")
    if "synced_through" not in pending:
        raise CliError(1, "invalid state.json: missing pending_sync.synced_through")
    if not _is_strict_int(pending["synced_through"]) or pending["synced_through"] < -1:
        raise CliError(1, "invalid state.json: invalid pending_sync.synced_through")
    return {"synced_through": pending["synced_through"]}


def validate_state(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise CliError(1, "invalid state.json: root must be a JSON object")
    for key in data:
        if key not in _STATE_REQUIRED_KEYS and key not in _STATE_LEGACY_KEYS:
            raise CliError(1, f"invalid state.json: unexpected key {key!r}")
    for key in _STATE_REQUIRED_KEYS:
        if key not in data:
            raise CliError(1, f"invalid state.json: missing key {key!r}")

    bid = data["bound_subagent_id"]
    if bid is not None and (not isinstance(bid, str) or not bid.strip()):
        raise CliError(1, "invalid state.json: bound_subagent_id must be non-empty str or null")

    exec_ids = data["execution_subagent_ids"]
    if not isinstance(exec_ids, list) or not all(isinstance(x, str) and x.strip() for x in exec_ids):
        raise CliError(1, "invalid state.json: execution_subagent_ids must be list[non-empty str]")

    retired = data["retired_subagent_max_step"]
    if not isinstance(retired, dict) or not all(
        isinstance(k, str) and k.strip() and _is_strict_int(v) for k, v in retired.items()
    ):
        raise CliError(1, "invalid state.json: invalid retired_subagent_max_step")

    pending = _validate_pending_sync(data["pending_sync"])
    return {
        "bound_subagent_id": bid,
        "execution_subagent_ids": list(exec_ids),
        "retired_subagent_max_step": dict(retired),
        "pending_sync": pending,
    }


def load_state_if_exists(state_path: pathlib.Path) -> tuple[bool, dict[str, Any]]:
    if not state_path.exists():
        return False, default_state()
    try:
        raw = _retry_on_permission_error(
            lambda: state_path.read_text(encoding="utf-8")
        )
        data = json.loads(raw)
    except OSError as exc:
        raise CliError(2, f"unable to read state.json: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CliError(1, f"corrupt state.json: {exc}") from exc
    return True, validate_state(data)


def atomic_write_text(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_", suffix=".tmp")
    tmp_path = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content.encode("utf-8"))
        _retry_on_permission_error(lambda: os.replace(tmp_path, path))
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def write_state(state_path: pathlib.Path, state: dict[str, Any]) -> None:
    atomic_write_text(state_path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def clear_stale_pages(pages_dir: pathlib.Path) -> None:
    if pages_dir.is_dir():
        for item in pages_dir.glob("page_*.md"):
            if item.is_file():
                item.unlink()


def transcript_location_valid(transcript_path: pathlib.Path) -> bool:
    resolved = transcript_path.resolve()
    if resolved.parent.is_dir():
        return True
    parts = resolved.parts
    return (
        len(parts) >= 4
        and parts[-3:] == (".system_generated", "logs", "transcript.jsonl")
        and resolved.parents[2].is_dir()
    )


def fold_jsonl_file(path: pathlib.Path) -> dict[int, tuple[int, dict[str, Any]]]:
    """Read and fold an append-only Antigravity JSONL log by step_index."""
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise CliError(2, f"unable to read log {path}: {exc}") from exc

    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        if raw_bytes.endswith(b"\n"):
            raise CliError(2, f"invalid UTF-8 in {path}: {exc}") from exc
        last_nl = raw_bytes.rfind(b"\n")
        if last_nl == -1:
            raw_text = ""
        else:
            try:
                raw_text = raw_bytes[: last_nl + 1].decode("utf-8")
            except UnicodeDecodeError as exc2:
                raise CliError(2, f"invalid UTF-8 in {path}: {exc2}") from exc2

    raw_lines = raw_text.replace("\r\n", "\n").split("\n")
    last_non_empty_idx = -1
    for i, line in enumerate(raw_lines):
        if line.strip():
            last_non_empty_idx = i

    folded: dict[int, tuple[int, dict[str, Any]]] = {}
    for line_idx, line in enumerate(raw_lines):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            if line_idx == last_non_empty_idx:
                continue
            raise CliError(2, f"corrupt JSONL at line {line_idx}: {exc}") from exc

        if not isinstance(record, dict):
            raise CliError(2, f"non-object JSONL record at line {line_idx}")

        step_index = record.get("step_index")
        if not _is_strict_int(step_index) or step_index < 0:
            raise CliError(2, f"invalid step_index at line {line_idx}: {step_index!r}")

        rec_type = record.get("type")
        if not isinstance(rec_type, str):
            raise CliError(2, f"missing or non-string type at line {line_idx}")

        trunc = record.get("truncated_fields")
        if trunc is not None and not isinstance(trunc, list):
            raise CliError(2, f"non-list truncated_fields at line {line_idx}")

        for existing in [k for k in folded if k >= step_index]:
            del folded[existing]
        folded[step_index] = (line_idx, record)

    return folded


def _clean_additional_metadata(body: str) -> str:
    kept = [
        line
        for line in body.split("\n")
        if not line.strip().startswith("The current local time is:")
    ]
    return "\n".join(kept).strip()


_OUTER_ENVELOPE_TAGS = ("<USER_SETTINGS_CHANGE>", "<ADDITIONAL_METADATA>")
_CLOSE_TO_OPEN_TAG = {f"</{tag[1:]}": tag for tag in _OUTER_ENVELOPE_TAGS}
_EXTRACTABLE_TYPES = frozenset(
    {
        "CHECKPOINT",
        "USER_INPUT",
        "PLANNER_RESPONSE",
        "SYSTEM_MESSAGE",
        "EPHEMERAL_MESSAGE",
    }
)


def _pop_leading_envelope(text: str) -> tuple[str, bool, str] | None:
    lines = text.split("\n")
    first_idx = 0
    while first_idx < len(lines) and lines[first_idx].strip(" \t") == "":
        first_idx += 1
    if first_idx >= len(lines):
        return None
    open_tag = lines[first_idx].strip(" \t")
    if open_tag not in _OUTER_ENVELOPE_TAGS:
        return None
    close_tag = f"</{open_tag[1:]}"
    depth = 1
    for i in range(first_idx + 1, len(lines)):
        tok = lines[i].strip(" \t")
        if tok == open_tag:
            depth += 1
        elif tok == close_tag:
            depth -= 1
            if depth == 0:
                inner = "\n".join(lines[first_idx + 1 : i])
                rest = "\n".join(lines[i + 1 :])
                cleaned = (
                    _clean_additional_metadata(inner)
                    if open_tag == "<ADDITIONAL_METADATA>"
                    else ""
                )
                return rest, open_tag == "<ADDITIONAL_METADATA>", cleaned
    return None


def _pop_trailing_envelope(text: str) -> tuple[str, bool, str] | None:
    lines = text.split("\n")
    last_idx = len(lines) - 1
    while last_idx >= 0 and lines[last_idx].strip(" \t") == "":
        last_idx -= 1
    if last_idx < 0:
        return None
    close_tag = lines[last_idx].strip(" \t")
    open_tag = _CLOSE_TO_OPEN_TAG.get(close_tag)
    if open_tag is None:
        return None
    depth = 1
    for i in range(last_idx - 1, -1, -1):
        tok = lines[i].strip(" \t")
        if tok == close_tag:
            depth += 1
        elif tok == open_tag:
            depth -= 1
            if depth == 0:
                inner = "\n".join(lines[i + 1 : last_idx])
                rest = "\n".join(lines[:i])
                cleaned = (
                    _clean_additional_metadata(inner)
                    if open_tag == "<ADDITIONAL_METADATA>"
                    else ""
                )
                return rest, open_tag == "<ADDITIONAL_METADATA>", cleaned
    return None


def extract_user_input(raw_content: str) -> str:
    """Strip outer envelopes structurally while preserving non-timestamp metadata."""
    text = normalize_lf(raw_content)
    leading_meta: list[str] = []
    trailing_meta_rev: list[str] = []

    while (popped := _pop_leading_envelope(text)) is not None:
        text, _, cleaned = popped
        if cleaned:
            leading_meta.append(cleaned)

    while (popped := _pop_trailing_envelope(text)) is not None:
        text, _, cleaned = popped
        if cleaned:
            trailing_meta_rev.append(cleaned)

    core = text.strip()
    if core.startswith("<USER_REQUEST>") and core.endswith("</USER_REQUEST>"):
        core = core[len("<USER_REQUEST>") : -len("</USER_REQUEST>")].strip()

    parts = [p for p in [core, *leading_meta, *reversed(trailing_meta_rev)] if p]
    return "\n\n".join(parts)


def _extract_outer_system_message_body(raw_content: str) -> tuple[str, str]:
    """Return (kind, candidate) for outermost SYSTEM_MESSAGE envelopes."""
    s = normalize_lf(raw_content).lstrip(" \t\n")
    if s.startswith("[Message] "):
        return "message", s
    if s.startswith("<SYSTEM_MESSAGE>\n"):
        candidate = s[len("<SYSTEM_MESSAGE>\n") :]
    elif s.startswith("The following is a <SYSTEM_MESSAGE>"):
        lines = s.split("\n")
        i = 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if (
            i < len(lines)
            and lines[i].rstrip(" \t") == "<SYSTEM_MESSAGE>"
            and i + 1 < len(lines)
        ):
            candidate = "\n".join(lines[i + 1 :])
        else:
            return "", ""
    else:
        return "", ""

    if candidate.startswith("[Message] "):
        return "message", candidate
    return "headerless", candidate


def classify_origin(folded: dict[int, tuple[int, dict[str, Any]]]) -> str:
    """Classify session origin from folded records: TRUNK, SUBAGENT, or UNKNOWN."""
    if not folded:
        return "UNKNOWN"

    for _, rec in folded.values():
        if rec.get("type") != "SYSTEM_MESSAGE":
            continue
        raw = rec.get("content")
        if not isinstance(raw, str):
            continue
        kind, candidate = _extract_outer_system_message_body(raw)
        if (
            kind == "headerless"
            and candidate.startswith("You are @")
            and "Everything before this turn is @" in candidate
        ):
            return "SUBAGENT"
        if kind == "message":
            match = MESSAGE_HEADER_RE.match(candidate)
            if match and match.group(2).startswith(
                "You have just started. Your assignment (recorded on the board as #"
            ):
                return "SUBAGENT"

    _, rec = folded[min(folded)]
    if rec.get("type") != "USER_INPUT":
        return "SUBAGENT"
    if rec.get("source") not in (None, "USER_EXPLICIT"):
        return "SUBAGENT"
    content = rec.get("content")
    if isinstance(content, str):
        extracted = extract_user_input(content).lstrip()
        if "content" in (rec.get("truncated_fields") or []) and extracted.startswith(
            "<USER_REQUEST>"
        ):
            extracted = extracted[len("<USER_REQUEST>") :].lstrip()
        if any(extracted.startswith(prefix) for prefix in SUBAGENT_USER_PREFIXES):
            return "SUBAGENT"
    return "TRUNK"


def find_latest_checkpoint_step(folded: dict[int, tuple[int, dict[str, Any]]]) -> int:
    ckpts = [idx for idx, (_, rec) in folded.items() if rec["type"] == "CHECKPOINT"]
    return max(ckpts) if ckpts else -1


def _created_at_compatible(primary: dict[str, Any], companion: dict[str, Any]) -> bool:
    p_ts = primary.get("created_at")
    c_ts = companion.get("created_at")
    if isinstance(p_ts, str) and p_ts and isinstance(c_ts, str) and c_ts:
        return p_ts == c_ts
    return True


def _needs_companion_expansion(
    folded: dict[int, tuple[int, dict[str, Any]]],
    min_step: int,
) -> bool:
    for step_idx, (_, rec) in folded.items():
        if step_idx < min_step:
            continue
        if rec["type"] not in _EXTRACTABLE_TYPES:
            continue
        trunc = rec.get("truncated_fields") or []
        if "content" in trunc:
            return True
    return False


def expand_with_companion(
    folded: dict[int, tuple[int, dict[str, Any]]],
    companion_path: pathlib.Path,
    min_step: int,
) -> dict[int, tuple[int, dict[str, Any]]]:
    """Expand truncated extractable content from folded companion full-log."""
    if not _needs_companion_expansion(folded, min_step) or not companion_path.exists():
        return folded

    comp_folded = fold_jsonl_file(companion_path)
    expanded = dict(folded)

    for step_idx, (line_idx, rec) in folded.items():
        if step_idx < min_step or rec["type"] not in _EXTRACTABLE_TYPES:
            continue
        trunc = rec.get("truncated_fields") or []
        if "content" not in trunc:
            continue
        cand = comp_folded.get(step_idx)
        if (
            cand is None
            or cand[1]["type"] != rec["type"]
            or not _created_at_compatible(rec, cand[1])
        ):
            continue
        comp_content = cand[1].get("content")
        if isinstance(comp_content, str):
            copied = dict(rec)
            copied["content"] = comp_content
            expanded[step_idx] = (line_idx, copied)

    return expanded


def extract_system_report(
    raw_content: str,
    step_idx: int,
    state: dict[str, Any],
) -> str:
    """Strictly parse only outermost Antigravity [Message] headers and quarantine retired senders."""
    kind, candidate = _extract_outer_system_message_body(raw_content)
    if kind != "message":
        return ""

    match = MESSAGE_HEADER_RE.match(candidate)
    if not match:
        return ""
    sender, raw_body = match.group(1), match.group(2)
    if sender not in state["execution_subagent_ids"]:
        return ""
    if sender != state["bound_subagent_id"]:
        max_allowed = state["retired_subagent_max_step"].get(sender, step_idx)
        if step_idx > max_allowed:
            return ""

    cleaned = raw_body.rstrip()
    if cleaned.endswith("</SYSTEM_MESSAGE>"):
        cleaned = cleaned.removesuffix("</SYSTEM_MESSAGE>")
    cleaned = cleaned.strip()
    if not cleaned:
        return ""

    open_idx = cleaned.find("<report>")
    close_idx = cleaned.rfind("</report>")
    if open_idx != -1 and close_idx > open_idx:
        return cleaned[open_idx : close_idx + len("</report>")].strip()
    return cleaned


def render_page(page_num: int, chunks: list[str]) -> str:
    header = f"# Living Memory Window — Page {page_num:03d}\n\n"
    return header + "\n\n---\n\n".join(chunks) + "\n"


def _page_fits(page_num: int, chunks: list[str]) -> bool:
    rendered = render_page(page_num, chunks)
    return (
        len(rendered.encode("utf-8")) < MAX_PAGE_BYTES
        and (rendered.count("\n") + 1) <= MAX_PAGE_LINES
    )


def _max_fitting_line_end(
    page_num: int, heading: str, lines: list[str], start: int
) -> int:
    lo, hi, best = start + 1, len(lines), start
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = heading + "\n".join(lines[start:mid])
        if _page_fits(page_num, [candidate]):
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def _max_fitting_char_prefix(page_num: int, heading: str, line: str) -> int:
    lo, hi, best = 1, len(line), 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if _page_fits(page_num, [heading + line[:mid]]):
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return max(1, best)


def paginate_blocks(blocks: list[tuple[int, str, str]]) -> list[str]:
    """Render blocks into LF UTF-8 pages under both byte and line caps."""
    if not blocks:
        return []
    pages: list[str] = []
    current_chunks: list[str] = []

    for step_idx, role, body in blocks:
        full_chunk = f"## [Step {step_idx}] {role}\n{body}"
        if _page_fits(len(pages) + 1, current_chunks + [full_chunk]):
            current_chunks.append(full_chunk)
            continue

        if current_chunks:
            pages.append(render_page(len(pages) + 1, current_chunks))
            current_chunks = []

        if _page_fits(len(pages) + 1, [full_chunk]):
            current_chunks = [full_chunk]
            continue

        lines = body.split("\n")
        pos = 0
        is_cont = False
        while pos < len(lines):
            pnum = len(pages) + 1
            cont_suffix = " (cont.)" if is_cont else ""
            heading = f"## [Step {step_idx}] {role}{cont_suffix}\n"
            end = _max_fitting_line_end(pnum, heading, lines, pos)
            if end > pos:
                piece = heading + "\n".join(lines[pos:end])
                pos = end
            else:
                split_k = _max_fitting_char_prefix(pnum, heading, lines[pos])
                piece = heading + lines[pos][:split_k]
                lines[pos] = lines[pos][split_k:]

            if pos < len(lines):
                pages.append(render_page(pnum, [piece]))
                is_cont = True
            else:
                current_chunks = [piece]

    if current_chunks:
        pages.append(render_page(len(pages) + 1, current_chunks))
    return pages


def _extract_blocks(
    expanded: dict[int, tuple[int, dict[str, Any]]],
    window_start: int,
    state: dict[str, Any],
) -> list[tuple[int, str, str]]:
    blocks: list[tuple[int, str, str]] = []
    for step_idx in sorted(expanded):
        if step_idx < window_start:
            continue
        rec = expanded[step_idx][1]
        rec_type = rec["type"]
        raw = rec.get("content")
        if rec_type == "CHECKPOINT" and isinstance(raw, str):
            text = normalize_lf(raw).strip()
            if text:
                blocks.append((step_idx, "Checkpoint Summary", text))
        elif rec_type == "USER_INPUT" and isinstance(raw, str):
            text = extract_user_input(raw)
            if text.strip():
                blocks.append((step_idx, "User", text))
        elif rec_type == "PLANNER_RESPONSE" and isinstance(raw, str):
            text = normalize_lf(raw).strip()
            if text:
                blocks.append((step_idx, "Planner", text))
        elif rec_type in ("SYSTEM_MESSAGE", "EPHEMERAL_MESSAGE") and isinstance(
            raw, str
        ):
            text = extract_system_report(raw, step_idx, state)
            if text:
                blocks.append((step_idx, "Execution Report", text))
    return blocks


def _emit_action(
    action: str,
    checkpoint_step: int,
    synced_through: int,
    pages: list[str],
) -> None:
    payload = {
        "action": action,
        "checkpoint_step": checkpoint_step,
        "synced_through": synced_through,
        "pages": pages,
    }
    print(json.dumps(payload, ensure_ascii=False))


def cmd_check_origin(args: argparse.Namespace) -> int:
    transcript_path = pathlib.Path(args.transcript)
    if not transcript_path.exists():
        print(json.dumps({"origin": "UNKNOWN"}))
        return 0
    folded = fold_jsonl_file(transcript_path)
    print(json.dumps({"origin": classify_origin(folded)}))
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    state_dir = pathlib.Path(args.state_dir)
    state_path = state_dir / "state.json"
    _, state = load_state_if_exists(state_path)

    transcript_path = pathlib.Path(args.transcript)
    if transcript_path.exists():
        folded = fold_jsonl_file(transcript_path)
    else:
        if not transcript_location_valid(transcript_path):
            raise CliError(2, f"missing logs directory for transcript: {transcript_path}")
        folded = {}

    if folded and classify_origin(folded) != "TRUNK":
        _emit_action("SKIP_SUBAGENT_SESSION", -1, -1, [])
        return 0

    pages_dir = state_dir / "pages"
    is_empty = (
        not transcript_path.exists()
        or transcript_path.stat().st_size == 0
        or not folded
    )
    if is_empty:
        clear_stale_pages(pages_dir)
        state["pending_sync"] = {"synced_through": -1}
        write_state(state_path, state)
        _emit_action("SPAWN_NEW", -1, -1, [])
        return 0

    max_folded_step = max(folded)
    latest_ckpt = find_latest_checkpoint_step(folded)
    window_start = max(0, latest_ckpt)
    companion_path = transcript_path.with_name("transcript_full.jsonl")
    expanded = expand_with_companion(folded, companion_path, window_start)
    blocks = _extract_blocks(expanded, window_start, state)
    rendered_pages = paginate_blocks(blocks)

    clear_stale_pages(pages_dir)
    page_paths: list[str] = []
    if rendered_pages:
        pages_dir.mkdir(parents=True, exist_ok=True)
        for page_num, rendered in enumerate(rendered_pages, start=1):
            page_file = (pages_dir / f"page_{page_num:03d}.md").resolve()
            atomic_write_text(page_file, rendered)
            page_paths.append(str(page_file))

    state["pending_sync"] = {"synced_through": max_folded_step}
    write_state(state_path, state)
    _emit_action("SPAWN_NEW", latest_ckpt, max_folded_step, page_paths)
    return 0


def _retire_bound_id(
    state: dict[str, Any], bound_id: str, retire_through: int
) -> None:
    retired = state["retired_subagent_max_step"]
    retired[bound_id] = max(retired.get(bound_id, -1), retire_through)


def cmd_bind(args: argparse.Namespace) -> int:
    subagent_id = args.subagent_id.strip()
    if not subagent_id:
        raise CliError(1, "--subagent-id must be non-empty")
    state_path = pathlib.Path(args.state_dir) / "state.json"
    exists, state = load_state_if_exists(state_path)
    if not exists or state["pending_sync"] is None:
        raise CliError(1, "bind requires non-null pending_sync in state.json")

    pending = state["pending_sync"]
    prev_id = state["bound_subagent_id"]
    if prev_id is not None and prev_id != subagent_id:
        _retire_bound_id(state, prev_id, pending["synced_through"])

    state["bound_subagent_id"] = subagent_id
    if subagent_id not in state["execution_subagent_ids"]:
        state["execution_subagent_ids"].append(subagent_id)
    state["retired_subagent_max_step"].pop(subagent_id, None)
    state["pending_sync"] = None
    write_state(state_path, state)
    result: dict[str, Any] = {"status": "bound", "subagent_id": subagent_id}
    if prev_id is not None and prev_id != subagent_id:
        result["retired_subagent_id"] = prev_id
    print(json.dumps(result))
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    state_dir = pathlib.Path(args.state_dir)
    state_path = state_dir / "state.json"
    pages_dir = state_dir / "pages"
    if args.purge:
        if state_path.exists():
            state_path.unlink()
        clear_stale_pages(pages_dir)
        print(json.dumps({"status": "reset"}))
        return 0

    exists, state = load_state_if_exists(state_path)
    if not exists:
        clear_stale_pages(pages_dir)
        print(json.dumps({"status": "reset"}))
        return 0

    prev_id = state["bound_subagent_id"]
    if prev_id is not None:
        retire_through = (
            state["pending_sync"]["synced_through"]
            if state["pending_sync"] is not None
            else -1
        )
        _retire_bound_id(state, prev_id, retire_through)

    state["bound_subagent_id"] = None
    state["pending_sync"] = None
    clear_stale_pages(pages_dir)
    write_state(state_path, state)
    print(json.dumps({"status": "reset"}))
    return 0


def build_parser() -> CliArgumentParser:
    parser = CliArgumentParser(prog="sync_memory.py")
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=CliArgumentParser
    )

    p_origin = subparsers.add_parser("check-origin")
    p_origin.add_argument("--transcript", required=True)

    p_sync = subparsers.add_parser("sync")
    p_sync.add_argument("--transcript", required=True)
    p_sync.add_argument("--state-dir", required=True)

    p_bind = subparsers.add_parser("bind")
    p_bind.add_argument("--state-dir", required=True)
    p_bind.add_argument("--subagent-id", required=True)

    p_reset = subparsers.add_parser("reset")
    p_reset.add_argument("--state-dir", required=True)
    p_reset.add_argument("--purge", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check-origin":
            return cmd_check_origin(args)
        if args.command == "sync":
            return cmd_sync(args)
        if args.command == "bind":
            return cmd_bind(args)
        if args.command == "reset":
            return cmd_reset(args)
        raise CliError(1, f"unknown command: {args.command}")
    except CliError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return exc.exit_code
    except OSError as exc:
        sys.stderr.write(f"error: I/O error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
