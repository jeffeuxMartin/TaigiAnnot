from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import pandas as pd

from gsheets_backend import (
    load_source,
    load_state,
    load_results,
    append_state,
    append_result,
)


def _now() -> str:
    return datetime.now().isoformat(sep=" ", timespec="microseconds")


def _norm_id(value: Any) -> str:
    return str(value or "").strip()


def _latest_state(state: pd.DataFrame) -> pd.DataFrame:
    if state.empty:
        return state

    # Google Sheets rows are already chronological by append order.
    return state.drop_duplicates(subset=["utterance_id"], keep="last")


def _done_ids(results: pd.DataFrame) -> set[str]:
    if results.empty or "utterance_id" not in results.columns:
        return set()

    return {
        _norm_id(x)
        for x in results["utterance_id"].tolist()
        if _norm_id(x)
    }


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

    item = {
        "utterance_id": _norm_id(row.get("utterance_id")),
        "split": _norm_id(row.get("split")),
        "file_name": _norm_id(row.get("file_name")),
        "speaker_id": _norm_id(row.get("speaker_id")),
        "intent": _norm_id(row.get("intent")),
        "transcription_model1": _norm_id(row.get("transcription_model1")),
        "transcription_model2": _norm_id(row.get("transcription_model2")),
        "transcription_model3": _norm_id(row.get("transcription_model3")),
    }

    return item


def get_progress() -> dict:
    source = load_source()
    state = load_state()
    results = load_results()

    done = _done_ids(results)
    working = _state_ids(state, "in_progress") - done
    skipped = _state_ids(state, "skipped") - done

    source_ids = {
        _norm_id(x)
        for x in source["utterance_id"].tolist()
        if _norm_id(x)
    }

    fresh_left = len(source_ids - done - working - skipped)

    return {
        "fresh_left": fresh_left,
        "skipped": len(skipped),
        "working": len(working),
        "done": len(done),
        "total": len(source_ids),
    }


def get_next_item(username: str = "") -> dict | None:
    source = load_source()
    state = load_state()
    results = load_results()

    done = _done_ids(results)
    working = _state_ids(state, "in_progress") - done
    skipped = _state_ids(state, "skipped") - done

    # First pass: fresh items only.
    for _, row in source.iterrows():
        utt = _norm_id(row.get("utterance_id"))

        if not utt:
            continue

        if utt in done or utt in working or utt in skipped:
            continue

        append_state([
            utt,
            username,
            "in_progress",
            _now(),
        ])

        return _row_to_item(row)

    # Second pass: recycle skipped items only when fresh pool is empty.
    for _, row in source.iterrows():
        utt = _norm_id(row.get("utterance_id"))

        if not utt:
            continue

        if utt in done or utt in working:
            continue

        if utt not in skipped:
            continue

        append_state([
            utt,
            username,
            "in_progress",
            _now(),
        ])

        return _row_to_item(row)

    return None


def skip_item(username: str, utterance_id: str) -> None:
    append_state([
        _norm_id(utterance_id),
        username,
        "skipped",
        _now(),
    ])


def submit_result(username: str, item: dict, result: dict) -> None:
    row = [
        _norm_id(item.get("utterance_id")),
        _norm_id(item.get("split")),
        _norm_id(item.get("file_name")),
        _norm_id(item.get("speaker_id")),
        _norm_id(item.get("intent")),
        username,
        _now(),
        int(bool(result.get("opt_empty", False))),
        int(bool(result.get("opt_incomplete", False))),
        int(bool(result.get("opt_intent_mismatch", False))),
        int(bool(result.get("opt_weird", False))),
        _norm_id(result.get("weird_note")),
    ]

    append_result(row)

    append_state([
        _norm_id(item.get("utterance_id")),
        username,
        "done",
        _now(),
    ])


def audio_url(file_name: str) -> str:
    # Temporary: pages_qc only displays this string.
    return _norm_id(file_name)
