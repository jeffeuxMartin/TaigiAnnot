from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1CqJKIASylPiza2ftFki4EzwKigj0kheK_fn0nKCSog4"

SOURCE_SHEET = "sourceData"
RESULT_SHEET = "results"

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


def _sheet(name):
    return (
        _gc()
        .open_by_key(SPREADSHEET_ID)
        .worksheet(name)
    )


def load_source():
    ws = _sheet(SOURCE_SHEET)
    return pd.DataFrame(ws.get_all_records())


def load_results():
    ws = _sheet(RESULT_SHEET)

    rows = ws.get_all_records()

    if not rows:
        return pd.DataFrame(columns=["item_id"])

    return pd.DataFrame(rows)


def append_result(row):
    ws = _sheet(RESULT_SHEET)
    ws.append_row(row, value_input_option="RAW")