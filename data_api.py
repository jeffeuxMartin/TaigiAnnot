from __future__ import annotations

from datetime import datetime

import pandas as pd

from gsheets_backend import (
    load_source,
    load_results,
    append_result,
)


def health():
    return {
        "ok": True,
    }


def get_next_item():
    source = load_source()
    results = load_results()

    done_ids = set(
        pd.to_numeric(
            results.get("utterance_id", pd.Series(dtype=str)),
            errors="coerce",
        )
        .dropna()
        .astype(str)
    )

    for utterance_id in source["utterance_id"]:
        if utterance_id not in done_ids:
            return {
                "utterance_id": utterance_id,
            }

    return {
        "utterance_id": None,
    }


def submit_result(
    utterance_id: str,
    opt_empty: bool = False,
    opt_incomplete: bool = False,
    opt_intent_mismatch: bool = False,
    opt_weird: bool = False,
    weird_note: str = "",
):
    row = [
        utterance_id,
        datetime.now().isoformat(timespec="seconds"),
        int(opt_empty),
        int(opt_incomplete),
        int(opt_intent_mismatch),
        int(opt_weird),
        weird_note or "",
    ]

    append_result(row)

    return {
        "ok": True,
        "utterance_id": utterance_id,
    }


def get_progress():
    source = load_source()
    results = load_results()

    total = len(source)
    done = len(results)

    return {
        "done": done,
        "total": total,
        "remaining": max(0, total - done),
    }


def get_results():
    return load_results()