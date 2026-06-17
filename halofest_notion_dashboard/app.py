from __future__ import annotations

import pandas as pd
import streamlit as st

from src.excel_export import dataframe_to_excel
from src.notion_utils import fetch_database

st.set_page_config(
    page_title="HaloFest Notion Dashboard",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ HaloFest Notion Dashboard")
st.caption("Pull submissions from Notion, review them in Streamlit, and export a clean spreadsheet.")


@st.cache_data(ttl=300, show_spinner="Loading data from Notion...")
def load_data(token: str, database_id: str) -> pd.DataFrame:
    return fetch_database(token=token, database_id=database_id)


def get_secret(name: str) -> str:
    value = st.secrets.get(name, "")
    return str(value).strip()


with st.sidebar:
    st.header("Settings")
    st.write("Add these in Streamlit Cloud secrets or your local `.streamlit/secrets.toml` file.")

    notion_token = get_secret("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")
    database_id = get_secret("382c3b0f81e580f9a7ffcf494286a49c?v=382c3b0f81e5803baee9000c0909baa8")

    if st.button("Refresh Notion Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("Required secrets:")
    st.code("NOTION_TOKEN\nNOTION_DATABASE_ID", language="toml")

if not notion_token or not database_id:
    st.warning("Missing Notion secrets. Add `NOTION_TOKEN` and `NOTION_DATABASE_ID` to continue.")
    st.stop()

try:
    df = load_data(notion_token, database_id)
except Exception as exc:
    st.error("Could not load data from Notion.")
    st.exception(exc)
    st.stop()

if df.empty:
    st.info("No records found in this Notion database.")
    st.stop()

filtered = df.copy()

metric_cols = st.columns(4)
metric_cols[0].metric("Total Records", len(df))

if "Status" in df.columns:
    metric_cols[1].metric("Approved", int((df["Status"] == "Approved").sum()))
    metric_cols[2].metric("Needs Info", int((df["Status"] == "Needs Info").sum()))
    metric_cols[3].metric("Pending", int(df["Status"].isin(["Submitted", "Under Review", "Pending"]).sum()))
else:
    metric_cols[1].metric("Approved", "—")
    metric_cols[2].metric("Needs Info", "—")
    metric_cols[3].metric("Pending", "—")

st.divider()

filter_cols = st.columns(3)

with filter_cols[0]:
    if "Status" in df.columns:
        options = sorted([x for x in df["Status"].dropna().unique() if str(x).strip()])
        selected = st.multiselect("Status", options)
        if selected:
            filtered = filtered[filtered["Status"].isin(selected)]

with filter_cols[1]:
    if "Regiment" in df.columns:
        options = sorted([x for x in df["Regiment"].dropna().unique() if str(x).strip()])
        selected = st.multiselect("Regiment", options)
        if selected:
            filtered = filtered[filtered["Regiment"].isin(selected)]

with filter_cols[2]:
    search_text = st.text_input("Search")
    if search_text:
        mask = filtered.astype(str).apply(
            lambda row: row.str.contains(search_text, case=False, na=False).any(),
            axis=1,
        )
        filtered = filtered[mask]

st.subheader("Submissions")
st.caption(f"Showing {len(filtered)} of {len(df)} records")

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True,
)

st.divider()

excel_file = dataframe_to_excel(filtered)

st.download_button(
    label="Download Excel Export",
    data=excel_file,
    file_name="halofest_notion_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
