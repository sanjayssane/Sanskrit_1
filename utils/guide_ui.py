"""Render the in-app user guide from docs/USER_GUIDE.md."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

USER_GUIDE_PATH = Path(__file__).resolve().parent.parent / "docs" / "USER_GUIDE.md"


def render_user_guide() -> None:
    st.markdown(USER_GUIDE_PATH.read_text(encoding="utf-8"))
