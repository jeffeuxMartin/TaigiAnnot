from __future__ import annotations

import requests
import streamlit as st


try:
    DATA_API_BASE = st.secrets["DATA_API_BASE"]
except Exception:
    DATA_API_BASE = "http://127.0.0.1:8001"

try:
    AUDIO_API_BASE = st.secrets["AUDIO_API_BASE"]
except Exception:
    AUDIO_API_BASE = "http://127.0.0.1:8002"


def _get(path: str, **params):
    r = requests.get(f"{DATA_API_BASE}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _post(path: str, payload: dict):
    r = requests.post(f"{DATA_API_BASE}{path}", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def get_progress() -> dict:
    return _get("/progress")


def get_next_item(username: str) -> dict | None:
    data = _get("/next", user_id=username)
    return None if data.get("item") is None else data["item"]


def skip_item(username: str, utterance_id: str) -> None:
    _post("/skip", {"user_id": username, "utterance_id": utterance_id})


def submit_result(username: str, item: dict, result: dict) -> None:
    _post(
        "/submit",
        {
            "user_id": username,
            "item": item,
            "result": result,
        },
    )


def audio_url(file_name: str) -> str:
    return f"{AUDIO_API_BASE}/audio?file_name={file_name}"
