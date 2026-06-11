"""CSV/Excel export helpers (FR-7.4). UTF-8 BOM so Devanagari opens correctly
in Excel; Excel export via openpyxl."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Report") -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()


def download_buttons(df: pd.DataFrame, base_name: str, key: str) -> None:
    """Render side-by-side CSV and Excel download buttons for a DataFrame."""
    import streamlit as st

    col_csv, col_xlsx, _ = st.columns([1, 1, 4])
    col_csv.download_button(
        "Download CSV", df_to_csv_bytes(df), file_name=f"{base_name}.csv",
        mime="text/csv", key=f"{key}_csv")
    col_xlsx.download_button(
        "Download Excel", df_to_excel_bytes(df), file_name=f"{base_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"{key}_xlsx")
