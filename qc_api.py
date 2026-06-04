from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from gsheets_backend import (
    STATE_SHEET,
    load_source,
    load_state,
    load_results,
    append_state,
    append_result,
    append_rows,
    replace_state,
)


STATE_COMPACT_THRESHOLD = None  # Set to an integer to enable automatic compaction of state sheet.


def _now() -> str:
    return datetime.now().isoformat(sep=" ", timespec="microseconds")


def _norm_id(value: Any) -> str:
    return str(value or "").strip()


def _latest_state(state: pd.DataFrame) -> pd.DataFrame:
    if state.empty:
        return state

    return state.drop_duplicates(subset=["utterance_id"], keep="last")


def _compact_state_if_needed() -> None:
    if STATE_COMPACT_THRESHOLD is None:
        return

    state = load_state()

    if len(state) <= STATE_COMPACT_THRESHOLD:
        return

    latest = _latest_state(state)
    compact = latest[latest["status"].map(_norm_id) != "removed"].copy()
    replace_state(compact)


def compact_state_now() -> None:
    state = load_state()

    if state.empty:
        return

    latest = _latest_state(state)
    compact = latest[latest["status"].map(_norm_id) != "removed"].copy()
    replace_state(compact)


def _done_ids(results: pd.DataFrame, state: pd.DataFrame | None = None) -> set[str]:
    done = set()

    if not results.empty and "utterance_id" in results.columns:
        done |= {
            _norm_id(x)
            for x in results["utterance_id"].tolist()
            if _norm_id(x)
        }

    if state is not None and not state.empty:
        latest = _latest_state(state)
        done |= {
            _norm_id(row["utterance_id"])
            for _, row in latest.iterrows()
            if _norm_id(row.get("status")) == "done"
        }

    return done


def _state_ids(state: pd.DataFrame, status: str) -> set[str]:
    if state.empty:
        return set()

    latest = _latest_state(state)

    return {
        _norm_id(row["utterance_id"])
        for _, row in latest.iterrows()
        if _norm_id(row.get("status")) == status
    }


def _row_to_item(row: pd.Series | dict) -> dict:
    if not isinstance(row, dict):
        row = row.to_dict()

    return {
        "utterance_id": _norm_id(row.get("utterance_id")),
        "split": _norm_id(row.get("split")),
        "file_name": _norm_id(row.get("file_name")),
        "speaker_id": _norm_id(row.get("speaker_id")),
        "intent": _norm_id(row.get("intent")),
        "transcription_model1": _norm_id(row.get("transcription_model1")),
        "transcription_model2": _norm_id(row.get("transcription_model2")),
        "transcription_model3": _norm_id(row.get("transcription_model3")),
    }



def get_item_by_utterance_id(utterance_id: str) -> dict | None:
    source = load_source()
    target = _norm_id(utterance_id)

    if source.empty or "utterance_id" not in source.columns:
        return None

    matched = source[
        source["utterance_id"].map(_norm_id) == target
    ]

    if matched.empty:
        return None

    return _row_to_item(matched.iloc[0])


def _result_row_to_result(row: pd.Series | dict) -> dict:
    if not isinstance(row, dict):
        row = row.to_dict()

    return {
        "opt_empty": bool(int(row.get("opt_empty") or 0)),
        "opt_incomplete": bool(int(row.get("opt_incomplete") or 0)),
        "opt_intent_mismatch": bool(int(row.get("opt_intent_mismatch") or 0)),
        "opt_weird": bool(int(row.get("opt_weird") or 0)),
        "weird_note": _norm_id(row.get("weird_note")),
    }


def get_prev_item(username: str) -> dict | None:
    results = load_results()

    if results.empty:
        return None

    if "user_id" not in results.columns or "utterance_id" not in results.columns:
        return None

    user_results = results[
        results["user_id"].map(_norm_id) == _norm_id(username)
    ]

    if user_results.empty:
        return None

    last_result = user_results.iloc[-1]
    utterance_id = _norm_id(last_result.get("utterance_id"))

    item = get_item_by_utterance_id(utterance_id)

    if item is None:
        item = {
            "utterance_id": utterance_id,
            "split": _norm_id(last_result.get("split")),
            "file_name": _norm_id(last_result.get("file_name")),
            "speaker_id": _norm_id(last_result.get("speaker_id")),
            "intent": _norm_id(last_result.get("intent")),
            "transcription_model1": "",
            "transcription_model2": "",
            "transcription_model3": "",
        }

    item["_mode"] = "edit"
    item["_result"] = _result_row_to_result(last_result)

    return item


def _snapshot():
    return {
        "source": load_source(),
        "state": load_state(),
        "results": load_results(),
    }


def get_progress() -> dict:
    snap = _snapshot()
    source = snap["source"]
    state = snap["state"]
    results = snap["results"]

    done = _done_ids(results, state)
    working = _state_ids(state, "in_progress") - done
    skipped = _state_ids(state, "skipped") - done
    removed = _state_ids(state, "removed")

    source_ids = {
        _norm_id(x)
        for x in source["utterance_id"].tolist()
        if _norm_id(x)
    }

    fresh_left = len(source_ids - done - working - skipped - removed)

    return {
        "fresh_left": fresh_left,
        "skipped": len(skipped),
        "working": len(working),
        "done": len(done),
        "total": len(source_ids),
    }


def get_next_item(username: str = "") -> dict | None:
    snap = _snapshot()
    source = snap["source"]
    state = snap["state"]
    results = snap["results"]

    done = _done_ids(results, state)
    working = _state_ids(state, "in_progress") - done
    skipped = _state_ids(state, "skipped") - done
    removed = _state_ids(state, "removed")

    # First pass: fresh items only.
    for _, row in source.iterrows():
        utt = _norm_id(row.get("utterance_id"))

        if not utt:
            continue

        if utt in done or utt in working or utt in skipped or utt in removed:
            continue

        append_state([
            utt,
            username,
            "in_progress",
            _now(),
        ])

        _compact_state_if_needed()
        return _row_to_item(row)

    # Second pass: recycle skipped items only when fresh pool is empty.
    for _, row in source.iterrows():
        utt = _norm_id(row.get("utterance_id"))

        if not utt:
            continue

        if utt in done or utt in working or utt in removed:
            continue

        if utt not in skipped:
            continue

        append_state([
            utt,
            username,
            "in_progress",
            _now(),
        ])

        _compact_state_if_needed()
        return _row_to_item(row)

    return None


def skip_item(username: str, utterance_id: str) -> None:
    append_state([
        _norm_id(utterance_id),
        username,
        "skipped",
        _now(),
    ])

    _compact_state_if_needed()


def submit_result(username: str, item: dict, result: dict) -> None:
    utt = _norm_id(item.get("utterance_id"))
    ts = _now()

    result_row = [
        utt,
        _norm_id(item.get("split")),
        _norm_id(item.get("file_name")),
        _norm_id(item.get("speaker_id")),
        _norm_id(item.get("intent")),
        username,
        ts,
        int(bool(result.get("opt_empty", False))),
        int(bool(result.get("opt_incomplete", False))),
        int(bool(result.get("opt_intent_mismatch", False))),
        int(bool(result.get("opt_weird", False))),
        _norm_id(result.get("weird_note")),
    ]

    # One logical button action: append result + append done state.
    # Google Sheets still receives two sheet operations, but the QC layer calls one function.
    append_result(result_row)

    append_state([
        utt,
        username,
        "done",
        _now(),
    ])

    _compact_state_if_needed()


def remove_state(username: str, utterance_id: str) -> None:
    append_state([
        _norm_id(utterance_id),
        username,
        "removed",
        _now(),
    ])

    _compact_state_if_needed()


def audio_url(file_name: str) -> str:
    return _norm_id(file_name)
