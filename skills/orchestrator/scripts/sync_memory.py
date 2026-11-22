#!/usr/bin/env python3
"""Antigravity Living Memory Window synchronization CLI for Orchestrator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
import time
from typing import Any, NoReturn

VALID_TIERS = ("flash", "pro", "flash_lite", "inherit")
MAX_PAGE_BYTES = 40000
MAX_PAGE_LINES = 750
COST_OLD_BASE_TOKENS = 35_627.0
COST_OLD_TOKENS_PER_BYTE = 0.5703
COST_NEW_BASE_TOKENS = 23_730.0
COST_NEW_TOKENS_PER_BYTE = 0.4097
COST_KEEP_MULT = 0.60
COST_SPAWN_MULT = 1.55
COST_SWITCH_FIXED_TOKENS = 15_000.0
CHILD_SCAN_CHUNK_BYTES = 65_536
PAGE_HEADER_DELTA_ADJUST_BYTES = 29
MESSAGE_HEADER_RE = re.compile(
    r"^\[Message\][ \t]+timestamp=\S+[ \t]+sender=(\S+)[ \t]+priority=\S+[ \t]+content=(.*)$",
    re.DOTALL,
)
SUBAGENT_USER_PREFIXES = (
    "[swarm]",
    "[board]",
    "[EXECUTION SUBAGENT — SINGLE PHASE]",
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
        "bound_tier": "flash",
        "execution_subagent_ids": [],
        "retired_subagent_max_step": {},
        "checkpoint_step": -1,
        "last_synced_step": -1,
        "prefix_digest": "",
        "pending_sync": None,
    }


def _validate_pending_sync(pending: Any) -> None:
    if pending is None:
        return
    if not isinstance(pending, dict):
        raise CliError(1, "invalid state.json: pending_sync must be an object or null")
    req = ("tier", "checkpoint_step", "synced_through", "prefix_digest")
    for key in req:
        if key not in pending:
            raise CliError(1, f"invalid state.json: missing pending_sync.{key}")
    if pending["tier"] not in VALID_TIERS:
        raise CliError(1, "invalid state.json: invalid pending_sync.tier")
    if not _is_strict_int(pending["checkpoint_step"]) or pending["checkpoint_step"] < -1:
        raise CliError(1, "invalid state.json: invalid pending_sync.checkpoint_step")
    if not _is_strict_int(pending["synced_through"]) or pending["synced_through"] < -1:
        raise CliError(1, "invalid state.json: invalid pending_sync.synced_through")
    if not isinstance(pending["prefix_digest"], str):
        raise CliError(1, "invalid state.json: invalid pending_sync.prefix_digest")
    if "lmw_bytes" in pending:
        if not _is_strict_int(pending["lmw_bytes"]) or pending["lmw_bytes"] < 0:
            raise CliError(1, "invalid state.json: invalid pending_sync.lmw_bytes")


def validate_state(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise CliError(1, "invalid state.json: root must be a JSON object")
    required = (
        "bound_subagent_id",
        "bound_tier",
        "execution_subagent_ids",
        "retired_subagent_max_step",
        "checkpoint_step",
        "last_synced_step",
        "prefix_digest",
        "pending_sync",
    )
    for key in required:
        if key not in data:
            raise CliError(1, f"invalid state.json: missing key {key!r}")

    bid = data["bound_subagent_id"]
    if bid is not None and (not isinstance(bid, str) or not bid.strip()):
        raise CliError(1, "invalid state.json: bound_subagent_id must be non-empty str or null")
    if data["bound_tier"] not in VALID_TIERS:
        raise CliError(1, "invalid state.json: invalid bound_tier")

    exec_ids = data["execution_subagent_ids"]
    if not isinstance(exec_ids, list) or not all(isinstance(x, str) and x.strip() for x in exec_ids):
        raise CliError(1, "invalid state.json: execution_subagent_ids must be list[non-empty str]")

    retired = data["retired_subagent_max_step"]
    if not isinstance(retired, dict) or not all(
        isinstance(k, str) and k.strip() and _is_strict_int(v) for k, v in retired.items()
    ):
        raise CliError(1, "invalid state.json: invalid retired_subagent_max_step")

    if not _is_strict_int(data["checkpoint_step"]) or data["checkpoint_step"] < -1:
        raise CliError(1, "invalid state.json: invalid checkpoint_step")
    if not _is_strict_int(data["last_synced_step"]) or data["last_synced_step"] < -1:
        raise CliError(1, "invalid state.json: invalid last_synced_step")
    if not isinstance(data["prefix_digest"], str):
        raise CliError(1, "invalid state.json: prefix_digest must be str")
    if "lmw_bytes" in data:
        if not _is_strict_int(data["lmw_bytes"]) or data["lmw_bytes"] < 0:
            raise CliError(1, "invalid state.json: invalid lmw_bytes")

    _validate_pending_sync(data["pending_sync"])
    return data


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


def compute_digest(
    folded: dict[int, tuple[int, dict[str, Any]]],
    window_start: int,
    upto_step: int,
) -> str:
    if upto_step < window_start:
        return ""
    tuples: list[list[Any]] = []
    for step_idx in sorted(folded):
        if window_start <= step_idx <= upto_step:
            rec = folded[step_idx][1]
            created_at = rec.get("created_at")
            created_str = created_at if isinstance(created_at, str) else ""
            raw_content = rec.get("content")
            content_str = raw_content if isinstance(raw_content, str) else ""
            tuples.append([step_idx, rec["type"], created_str, content_str])
    if not tuples:
        return ""
    encoded = json.dumps(tuples, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    allowed_types: frozenset[str] | None = None,
    expand_tool_calls: bool = True,
) -> bool:
    for step_idx, (_, rec) in folded.items():
        if step_idx < min_step:
            continue
        rec_type = rec["type"]
        if allowed_types is not None and rec_type not in allowed_types:
            continue
        trunc = rec.get("truncated_fields") or []
        if "content" in trunc or (
            expand_tool_calls
            and rec_type == "PLANNER_RESPONSE"
            and "tool_calls" in trunc
        ):
            return True
    return False


def expand_with_companion(
    folded: dict[int, tuple[int, dict[str, Any]]],
    companion_path: pathlib.Path,
    min_step: int,
    allowed_types: frozenset[str] | None = None,
    expand_tool_calls: bool = True,
) -> dict[int, tuple[int, dict[str, Any]]]:
    """Expand truncated content (and optionally tool_calls) from folded companion full-log."""
    expanded: dict[int, tuple[int, dict[str, Any]]] = {
        step_idx: (line_idx, dict(rec)) for step_idx, (line_idx, rec) in folded.items()
    }
    if (
        not _needs_companion_expansion(
            expanded,
            min_step,
            allowed_types=allowed_types,
            expand_tool_calls=expand_tool_calls,
        )
        or not companion_path.exists()
    ):
        return expanded

    comp_folded = fold_jsonl_file(companion_path)

    for step_idx, (_, rec) in expanded.items():
        if step_idx < min_step:
            continue
        rec_type = rec["type"]
        if allowed_types is not None and rec_type not in allowed_types:
            continue
        trunc = rec.get("truncated_fields") or []
        want_content = "content" in trunc
        want_tools = (
            expand_tool_calls
            and rec_type == "PLANNER_RESPONSE"
            and "tool_calls" in trunc
        )
        if not (want_content or want_tools):
            continue

        cand = comp_folded.get(step_idx)
        if (
            cand is None
            or cand[1]["type"] != rec_type
            or not _created_at_compatible(rec, cand[1])
        ):
            continue
        comp_rec = cand[1]
        if want_content and isinstance(comp_rec.get("content"), str):
            rec["content"] = comp_rec["content"]
        if want_tools and isinstance(comp_rec.get("tool_calls"), list):
            rec["tool_calls"] = comp_rec["tool_calls"]

    return expanded


def turn1_bound_id_present(
    expanded: dict[int, tuple[int, dict[str, Any]]],
    window_start: int,
    bound_id: str,
) -> bool:
    for step_idx, (_, rec) in expanded.items():
        if step_idx < window_start:
            continue
        rec_type = rec["type"]
        if rec_type in ("GENERIC", "SYSTEM_MESSAGE", "EPHEMERAL_MESSAGE"):
            raw = rec.get("content")
            if isinstance(raw, str) and bound_id in raw:
                return True
        elif rec_type == "PLANNER_RESPONSE":
            tools = rec.get("tool_calls")
            if tools is not None and bound_id in json.dumps(tools, ensure_ascii=False):
                return True
    return False


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


def should_rotate_for_cost(child_bytes_since_ckpt: int, est_lmw_bytes: int) -> bool:
    """Return True when expected 12-step hot reuse of old child exceeds fresh spawn cost."""
    est_old_ctx = COST_OLD_BASE_TOKENS + COST_OLD_TOKENS_PER_BYTE * child_bytes_since_ckpt
    est_new_ctx = COST_NEW_BASE_TOKENS + COST_NEW_TOKENS_PER_BYTE * est_lmw_bytes
    return (COST_KEEP_MULT * est_old_ctx) > (
        COST_SPAWN_MULT * est_new_ctx + COST_SWITCH_FIXED_TOKENS
    )


def _find_last_bound_report_step(
    folded: dict[int, tuple[int, dict[str, Any]]],
    window_start: int,
    bound_id: str,
) -> int:
    for step_idx in sorted(folded, reverse=True):
        if step_idx < window_start:
            break
        rec = folded[step_idx][1]
        if rec.get("type") not in ("SYSTEM_MESSAGE", "EPHEMERAL_MESSAGE"):
            continue
        raw = rec.get("content")
        if not isinstance(raw, str):
            continue
        kind, candidate = _extract_outer_system_message_body(raw)
        if kind != "message":
            continue
        match = MESSAGE_HEADER_RE.match(candidate)
        if match and match.group(1) == bound_id:
            return step_idx
    return -1


def _resolve_subagent_transcript_path(
    trunk_transcript_path: pathlib.Path,
    bound_id: str,
    override_path: str | None,
) -> pathlib.Path | None:
    if override_path:
        return pathlib.Path(override_path)
    if not bound_id or "/" in bound_id or "\\" in bound_id or ".." in bound_id:
        return None
    resolved = trunk_transcript_path.resolve()
    if len(resolved.parts) < 5 or resolved.parts[-3:] != (
        ".system_generated",
        "logs",
        "transcript.jsonl",
    ):
        return None
    return resolved.parents[3] / bound_id / ".system_generated" / "logs" / "transcript.jsonl"


def _iter_lines_reverse(
    fh: Any, file_size: int, chunk_size: int = CHILD_SCAN_CHUNK_BYTES
):
    """Yield (line_start, line_end, raw_line_bytes) in O(N) from EOF back to byte 0."""
    pos = file_size
    line_end = file_size
    carry: list[bytes] = []
    while pos > 0:
        read_start = max(0, pos - chunk_size)
        fh.seek(read_start)
        chunk = fh.read(pos - read_start)
        pos = read_start
        end_in_chunk = len(chunk)
        nl = chunk.rfind(b"\n", 0, end_in_chunk)
        while nl != -1:
            tail = chunk[nl + 1 : end_in_chunk]
            if carry:
                raw_line = tail + b"".join(reversed(carry))
                carry.clear()
            else:
                raw_line = tail
            line_start = read_start + nl + 1
            yield line_start, line_end, raw_line
            line_end = line_start
            end_in_chunk = nl
            nl = chunk.rfind(b"\n", 0, end_in_chunk)
        if end_in_chunk > 0:
            carry.append(chunk[:end_in_chunk])
    if carry:
        yield 0, line_end, b"".join(reversed(carry))


def _measure_child_bytes_since_checkpoint(child_path: pathlib.Path) -> int | None:
    """Fail-open O(N) reverse EOF scan returning bytes from latest valid CHECKPOINT line."""

    def _scan() -> int | None:
        with open(child_path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            file_size = fh.tell()
            if file_size <= 0:
                return None
            effective_eof = file_size
            eof_step_index: int | None = None
            is_first = True
            for line_start, _line_end, raw_line in _iter_lines_reverse(fh, file_size):
                was_first = is_first
                is_first = False
                stripped = raw_line.strip()
                if not stripped:
                    if was_first:
                        effective_eof = line_start
                    continue

                if eof_step_index is None:
                    try:
                        rec = json.loads(stripped.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        if was_first:
                            effective_eof = line_start
                            continue
                        return None
                    if (
                        not isinstance(rec, dict)
                        or not _is_strict_int(rec.get("step_index"))
                        or rec["step_index"] < 0
                    ):
                        if was_first:
                            effective_eof = line_start
                            continue
                        return None
                    eof_step_index = rec["step_index"]
                    if rec.get("type") == "CHECKPOINT":
                        return effective_eof - line_start
                    continue

                if b'"CHECKPOINT"' not in stripped:
                    continue
                rec = json.loads(stripped.decode("utf-8"))
                if not isinstance(rec, dict) or rec.get("type") != "CHECKPOINT":
                    continue
                step_idx = rec.get("step_index")
                if _is_strict_int(step_idx) and 0 <= step_idx <= eof_step_index:
                    return effective_eof - line_start

            return None if eof_step_index is None else effective_eof

    try:
        return _retry_on_permission_error(_scan)
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _extract_blocks(
    expanded: dict[int, tuple[int, dict[str, Any]]],
    slice_start: int,
    max_step: int | None,
    state: dict[str, Any],
) -> list[tuple[int, str, str]]:
    blocks: list[tuple[int, str, str]] = []
    for step_idx in sorted(expanded):
        if step_idx < slice_start:
            continue
        if max_step is not None and step_idx > max_step:
            break
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
    tier: str,
    subagent_id: str | None,
    checkpoint_step: int,
    synced_through: int,
    prefix_digest: str,
    pages: list[str],
) -> None:
    payload = {
        "action": action,
        "tier": tier,
        "subagent_id": subagent_id,
        "checkpoint_step": checkpoint_step,
        "synced_through": synced_through,
        "prefix_digest": prefix_digest,
        "delta_empty": len(pages) == 0,
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
        _emit_action("SKIP_SUBAGENT_SESSION", args.tier, None, -1, -1, "", [])
        return 0

    pages_dir = state_dir / "pages"
    is_empty = (
        not transcript_path.exists()
        or transcript_path.stat().st_size == 0
        or not folded
    )
    if is_empty:
        clear_stale_pages(pages_dir)
        state["pending_sync"] = {
            "tier": args.tier,
            "checkpoint_step": -1,
            "synced_through": -1,
            "prefix_digest": "",
            "lmw_bytes": 0,
        }
        write_state(state_path, state)
        _emit_action("SPAWN_NEW", args.tier, None, -1, -1, "", [])
        return 0

    max_folded_step = max(folded)
    latest_ckpt = find_latest_checkpoint_step(folded)
    window_start = max(0, latest_ckpt)
    staged_digest = compute_digest(folded, window_start, max_folded_step)

    digest_mismatch = (
        state["last_synced_step"] >= window_start
        and compute_digest(folded, window_start, state["last_synced_step"])
        != state["prefix_digest"]
    )
    base_need_spawn = (
        args.force_spawn
        or state["bound_subagent_id"] is None
        or latest_ckpt != state["checkpoint_step"]
        or max_folded_step < state["last_synced_step"]
        or digest_mismatch
        or args.tier != state["bound_tier"]
    )
    companion_path = transcript_path.with_name("transcript_full.jsonl")
    if not base_need_spawn and state["last_synced_step"] == -1:
        expanded = expand_with_companion(
            folded,
            companion_path,
            window_start,
            allowed_types=None,
            expand_tool_calls=True,
        )
    elif base_need_spawn:
        expanded = expand_with_companion(
            folded,
            companion_path,
            window_start,
            allowed_types=_EXTRACTABLE_TYPES,
            expand_tool_calls=False,
        )
    else:
        expanded = expand_with_companion(
            folded,
            companion_path,
            state["last_synced_step"] + 1,
            allowed_types=_EXTRACTABLE_TYPES,
            expand_tool_calls=False,
        )

    turn1_rewind = (
        not base_need_spawn
        and state["last_synced_step"] == -1
        and not turn1_bound_id_present(
            expanded, window_start, state["bound_subagent_id"]
        )
    )
    need_spawn = base_need_spawn or turn1_rewind
    rendered_pages: list[str]
    lmw_bytes: int

    if not need_spawn:
        slice_start = max(window_start, state["last_synced_step"] + 1)
        delta_blocks = _extract_blocks(expanded, slice_start, None, state)
        delta_pages = paginate_blocks(delta_blocks)
        delta_bytes = sum(len(p.encode("utf-8")) for p in delta_pages)
        if state["last_synced_step"] < window_start:
            base_lmw_bytes = 0
        else:
            raw_lmw = state.get("lmw_bytes")
            if _is_strict_int(raw_lmw) and raw_lmw >= 0:
                base_lmw_bytes = raw_lmw
            else:
                base_blocks = _extract_blocks(
                    folded, window_start, state["last_synced_step"], state
                )
                base_lmw_bytes = sum(
                    len(p.encode("utf-8")) for p in paginate_blocks(base_blocks)
                )
        est_lmw_bytes = base_lmw_bytes + (
            max(0, delta_bytes - PAGE_HEADER_DELTA_ADJUST_BYTES)
            if base_lmw_bytes > 0 and delta_bytes > 0
            else delta_bytes
        )
        last_bound_report_step = _find_last_bound_report_step(
            folded, window_start, state["bound_subagent_id"]
        )
        if last_bound_report_step > state["last_synced_step"]:
            child_path = _resolve_subagent_transcript_path(
                transcript_path,
                state["bound_subagent_id"],
                args.subagent_transcript,
            )
            child_bytes = (
                _measure_child_bytes_since_checkpoint(child_path)
                if child_path is not None
                else None
            )
            if child_bytes is not None and should_rotate_for_cost(
                child_bytes, est_lmw_bytes
            ):
                need_spawn = True
                if slice_start == window_start:
                    rendered_pages = delta_pages
                    lmw_bytes = delta_bytes
                else:
                    expanded = expand_with_companion(
                        folded,
                        companion_path,
                        window_start,
                        allowed_types=_EXTRACTABLE_TYPES,
                        expand_tool_calls=False,
                    )
                    blocks = _extract_blocks(expanded, window_start, None, state)
                    rendered_pages = paginate_blocks(blocks)
                    lmw_bytes = sum(len(p.encode("utf-8")) for p in rendered_pages)
        if not need_spawn:
            rendered_pages = delta_pages
            lmw_bytes = est_lmw_bytes
    else:
        blocks = _extract_blocks(expanded, window_start, None, state)
        rendered_pages = paginate_blocks(blocks)
        lmw_bytes = sum(len(p.encode("utf-8")) for p in rendered_pages)

    action = "SPAWN_NEW" if need_spawn else "RESUME_EXISTING"
    out_subagent_id = None if need_spawn else state["bound_subagent_id"]

    clear_stale_pages(pages_dir)
    page_paths: list[str] = []
    if rendered_pages:
        pages_dir.mkdir(parents=True, exist_ok=True)
        for page_num, rendered in enumerate(rendered_pages, start=1):
            page_file = (pages_dir / f"page_{page_num:03d}.md").resolve()
            atomic_write_text(page_file, rendered)
            page_paths.append(str(page_file))

    state["pending_sync"] = {
        "tier": args.tier,
        "checkpoint_step": latest_ckpt,
        "synced_through": max_folded_step,
        "prefix_digest": staged_digest,
        "lmw_bytes": lmw_bytes,
    }
    write_state(state_path, state)
    _emit_action(
        action,
        args.tier,
        out_subagent_id,
        latest_ckpt,
        max_folded_step,
        staged_digest,
        page_paths,
    )
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
    state["bound_tier"] = pending["tier"]
    state["checkpoint_step"] = pending["checkpoint_step"]
    state["last_synced_step"] = pending["synced_through"]
    state["prefix_digest"] = pending["prefix_digest"]
    if "lmw_bytes" in pending:
        state["lmw_bytes"] = pending["lmw_bytes"]
    else:
        state.pop("lmw_bytes", None)
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
        pending_step = (
            state["pending_sync"]["synced_through"]
            if state["pending_sync"] is not None
            else -1
        )
        _retire_bound_id(state, prev_id, max(state["last_synced_step"], pending_step))

    state["bound_subagent_id"] = None
    state["bound_tier"] = "flash"
    state["checkpoint_step"] = -1
    state["last_synced_step"] = -1
    state["prefix_digest"] = ""
    state["lmw_bytes"] = 0
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
    p_sync.add_argument("--tier", default="flash", choices=VALID_TIERS)
    p_sync.add_argument(
        "--force-spawn",
        action="store_true",
        help="Force SPAWN_NEW full-window export while preserving prior bound_subagent_id reports until bind.",
    )
    p_sync.add_argument(
        "--subagent-transcript",
        default=None,
        help="Optional explicit bound Execution Subagent transcript path override for non-Antigravity adapters or replay tests.",
    )

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
