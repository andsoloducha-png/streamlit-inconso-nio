from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

from .config import DEFAULT_CSV, REQUIRED_COLUMNS
from .time_filters import assign_bucket, assign_shift


def clean_excel_cell(value: object) -> object:
    """Normalize one cell exported from Excel-style CSV."""
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if text.startswith('="') and text.endswith('"'):
        text = text[2:-1]
    elif text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text.strip()


@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes | None, default_mtime: float | None) -> pd.DataFrame:
    """Load the uploaded or default Blocklist CSV and add analysis columns."""
    if file_bytes is not None:
        try:
            csv_text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            csv_text = file_bytes.decode("cp1250")
    else:
        csv_text = DEFAULT_CSV.read_text(encoding="utf-8-sig")

    csv_text = csv_text.replace('="', '"')
    df = pd.read_csv(StringIO(csv_text), sep=";", dtype="string")

    for column in df.columns:
        df[column] = df[column].map(clean_excel_cell)

    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        missing_txt = ", ".join(sorted(missing))
        raise ValueError(f"Brakuje wymaganych kolumn: {missing_txt}")

    df["Timestamp"] = pd.to_datetime(df["TimeTele"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Timestamp"]).copy()

    df["Data"] = df["Timestamp"].dt.date
    df["Godzina"] = df["Timestamp"].dt.time
    df["Tray Tray"] = pd.to_numeric(df["Tray Tray"], errors="coerce").astype("Int64")
    df["Station"] = pd.to_numeric(df["Station"], errors="coerce").astype("Int64")
    df["Tray Sorter"] = df["Tray Sorter"].astype("string")
    df["NokReason"] = df["NokReason"].astype("string")
    df["Shift"] = df["Godzina"].map(assign_shift)
    df["Przedzial"] = df["Godzina"].map(assign_bucket)

    return df
