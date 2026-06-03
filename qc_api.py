from __future__ import annotations

from typing import Any

import pandas as pd

# data_api.py is expected to be a thin alias, e.g.
# from data_api__v3__gsheets import *
import data_api as api


def _coerce_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _row_to_item(row: dict) -> dict:
    item_id = _coerce_int(row.get("item_id"))

    item = dict(row)
    item["item_id"] = item_id
    item.setdefault("utterance_id", str(item_id) if item_id is not None else "")
    item.setdefault("file_name", str(item.get("utterance_id", item_id or "")))
    item.setdefault("split", "")
    item.setdefault("speaker_id", "")
    item.setdefault("intent", "")

    item.setdefault("transcription_model1", "")
    item.setdefault("transcription_model2", "")
    item.setdefault("transcription_model3", "")

    return item


def _minimal_item(item_id: int | None) -> dict | None:
    if item_id is None:
        return None

    return {
        "item_id": item_id,
        "utterance_id": str(item_id),
        "file_name": str(item_id),
        "split": "",
        "speaker_id": "",
        "intent": "",
        "transcription_model1": "",
        "transcription_model2": "",
        "transcription_model3": "",
    }


def _lookup_source_item(item_id: int | None) -> dict | None:
    if item_id is None:
        return None

    # data_api__v3__gsheets imports load_source from gsheets_backend,
    # so data_api.py may expose it through `from ... import *`.
    load_source = getattr(api, "load_source", None)

    if load_source is None:
        return _minimal_item(item_id)

    try:
        source = load_source()
    except Exception:
        return _minimal_item(item_id)

    if source is None or len(source) == 0 or "item_id" not in source.columns:
        return _minimal_item(item_id)

    ids = pd.to_numeric(source["item_id"], errors="coerce")
    matched = source.loc[ids == item_id]

    if matched.empty:
        return _minimal_item(item_id)

    return _row_to_item(matched.iloc[0].to_dict())


def get_progress() -> dict:
    progress = api.get_progress()

    # pages_qc expects old-style keys.
    if {"fresh_left", "skipped", "working"} <= set(progress.keys()):
        return progress

    return {
        "fresh_left": progress.get("remaining", 0),
        "skipped": progress.get("skipped", 0),
        "working": progress.get("working", 0),
        "done": progress.get("done", 0),
        "total": progress.get("total", 0),
    }


def get_next_item(username: str = "") -> dict | None:
    data = api.get_next_item()

    if data is None:
        return None

    item_id = _coerce_int(data.get("item_id"))

    if item_id is None:
        return None

    return _lookup_source_item(item_id)


def skip_item(username: str, utterance_id: str) -> None:
    item_id = _coerce_int(utterance_id)

    if item_id is None:
        return

    # v3 has no state/skip table yet.
    # Mark skipped as a result row so /next will advance.
    api.submit_result(
        item_id=item_id,
        opt_empty=False,
        opt_incomplete=False,
        opt_intent_mismatch=False,
        opt_weird=True,
        weird_note="__SKIP__",
    )


def submit_result(username: str, item: dict, result: dict) -> None:
    item_id = _coerce_int(item.get("item_id") or item.get("utterance_id"))

    if item_id is None:
        raise ValueError(f"Cannot submit item without numeric item_id: {item!r}")

    api.submit_result(
        item_id=item_id,
        opt_empty=bool(result.get("opt_empty", False)),
        opt_incomplete=bool(result.get("opt_incomplete", False)),
        opt_intent_mismatch=bool(result.get("opt_intent_mismatch", False)),
        opt_weird=bool(result.get("opt_weird", False)),
        weird_note=result.get("weird_note", "") or "",
    )


def audio_url(file_name: str) -> str:
    # For this temporary cloud test, only display the URL/text.
    # Replace this later with HF URL construction or wave/audio integration.
    return str(file_name or "")
