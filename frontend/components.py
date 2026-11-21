"""
Reusable Frontend Components for Streamlit UI.
Enhanced with modern headers, status cards, and formatted metric rows.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import uuid
import time
from typing import Any, Optional


def render_header(title: str, subtitle: str) -> None:
    """Renders a polished, modern gradient card header."""
    st.markdown(
        f"""
        <div class="main-header-container">
            <div class="main-title">{title}</div>
            <div class="sub-title">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_metric_row(metrics: list[tuple[str, str]]) -> None:
    """Renders metric cards with consistent styling."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label=label, value=value)


def render_explanation(explanation: str, assumptions: Optional[list[str]] = None) -> None:
    """Renders explanation panel with collapsible technical assumptions."""
    with st.expander("🔍 Query Pipeline Trace & Explanation", expanded=True):
        st.markdown(explanation)
        if assumptions:
            st.markdown("---")
            st.caption("Assumptions & Notes:")
            for a in assumptions:
                st.markdown(f"- {a}")


def render_results_table(df: pd.DataFrame, execution_time_ms: float) -> None:
    """Render execution results safely with deduplicated column names and download button."""
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

    st.markdown(f"#### 📊 Query Execution Results ({len(df)} rows in `{execution_time_ms:.1f} ms`)")
    if df.empty:
        st.warning("Query executed successfully, but returned 0 matching records.")
    else:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv",
            key=f"dl_{time.time()}_{uuid.uuid4().hex[:8]}"
        )
