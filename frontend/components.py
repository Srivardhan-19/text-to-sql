"""
Reusable Frontend Components for Streamlit UI.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import uuid


def render_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">{subtitle}</div>', unsafe_allow_html=True)


def render_metric_row(metrics: list[tuple[str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label=label, value=value)


def render_explanation(explanation: str, assumptions: Optional[list[str]] = None) -> None:
    st.markdown("#### Query Explanation")
    st.info(explanation)
    if assumptions:
        with st.expander("Assumptions & Notes", expanded=False):
            for a in assumptions:
                st.markdown(f"- {a}")


def render_results_table(df: pd.DataFrame, execution_time_ms: float) -> None:
    """Render execution results safely.

    Streamlit's ``st.dataframe`` (via pyarrow) does not accept DataFrames with duplicate
    column names. This can happen when the generated SQL query selects the same column
    multiple times (e.g., ``SELECT booking_id, booking_id FROM …``). We normalise the
    column names here to guarantee uniqueness before rendering.
    """
    # Ensure column names are unique – append a numeric suffix to duplicates.
    if not df.columns.is_unique:
        seen: dict[str, int] = {}
        new_cols = []
        for col in df.columns:
            count = seen.get(col, 0)
            if count == 0:
                new_cols.append(col)
            else:
                new_cols.append(f"{col}_{count}")
            seen[col] = count + 1
        df = df.copy()
        df.columns = new_cols




