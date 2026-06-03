from __future__ import annotations

from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

import streamlit as st

SPREADSHEET_ID = "1CqJKIASylPiza2ftFki4EzwKigj0kheK_fn0nKCSog4"

SOURCE_SHEET = "sourceData"
STATE_SHEET = "currState"
RESULT_SHEET = "results"

SOURCE_COLUMNS = [
    "utterance_id",
    "split",
    "file_name",
    "speaker_id",
    "intent",
    "transcription_model1",
    "transcription_model2",
    "transcription_model3",
]

STATE_COLUMNS = [
    "utterance_id",
    "user_id",
    "status",
    "updated_at",
]

RESULT_COLUMNS = [
    "utterance_id",
    "split",
    "file_name",
    "speaker_id",
    "intent",
    "user_id",
    "created_at",
    "opt_empty",
    "opt_incomplete",
    "opt_intent_mismatch",
    "opt_weird",
    "weird_note",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def _credentials():
    if Path("service_account.json").exists():
        return Credentials.from_service_account_file(
            "service_account.json",
            scopes=SCOPES,
        )

    import streamlit as st

    return Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )


def _gc():
    return gspread.authorize(_credentials())


def _sheet(name: str):
    return (
        _gc()
        .open_by_key(SPREADSHEET_ID)
        .worksheet(name)
    )


def _load_sheet(name: str, columns: list[str]) -> pd.DataFrame:
    ws = _sheet(name)
    rows = ws.get_all_records()

    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(rows)

    for col in columns:
        if col not in df.columns:
            df[col] = ""

    return df[columns]


@st.cache_data(ttl=15)
def load_source() -> pd.DataFrame:
    return _load_sheet(SOURCE_SHEET, SOURCE_COLUMNS)


@st.cache_data(ttl=5)
def load_state() -> pd.DataFrame:
    return _load_sheet(STATE_SHEET, STATE_COLUMNS)


@st.cache_data(ttl=5)
def load_results() -> pd.DataFrame:
    return _load_sheet(RESULT_SHEET, RESULT_COLUMNS)


def append_state(row: list) -> None:
    _sheet(STATE_SHEET).append_row(row, value_input_option="RAW")
    st.cache_data.clear()


def append_result(row: list) -> None:
    _sheet(RESULT_SHEET).append_row(row, value_input_option="RAW")
    st.cache_data.clear()
