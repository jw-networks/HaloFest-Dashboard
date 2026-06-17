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

st.title("🛡️ HaloFest Attendance Registration")
st.header("Admin Dashboard")


@st.cache_data(ttl=300, show_spinner="Loading data from Notion...")
def load_data(token: str, database_id: str) -> pd.DataFrame:
    return fetch_database(token=token, database_id=database_id)


def get_secret(name: str) -> str:
    value = st.secrets.get(name, "")
    return str(value).strip()


def first_existing(row: pd.Series, columns: list[str], default: str = "") -> str:
    for col in columns:
        if col in row and str(row[col]).strip():
            return str(row[col]).strip()
    return default


def yes_count(df: pd.DataFrame, columns: list[str]) -> int:
    for col in columns:
        if col in df.columns:
            return int(df[col].astype(str).str.lower().isin(["yes", "true", "1", "checked"]).sum())
    return 0


def get_photo_url(row: pd.Series) -> str:
    photo_columns = [
        "Photo",
        "Armor Photo",
        "Costume Photo",
        "Image",
        "Picture",
        "Photos",
        "Upload",
    ]

    for col in photo_columns:
        if col in row and str(row[col]).strip():
            return str(row[col]).split(",")[0].strip()

    return ""


def order_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    preferred_columns = [
        "Name",
        "Username",
        "Badge Name",
        "Email",
        "Social Handle",
        "Ticket",
        "Tickets",
        "Handler",
        "Concert",
        "Cosplay",
        "Cosplay Contest",
        "Makers",
        "Makers Contest",
        "Photo",
        "Armor Photo",
        "Submission Date",
        "Created time",
        "Notion URL",
    ]

    preferred = [col for col in preferred_columns if col in dataframe.columns]
    remaining = [col for col in dataframe.columns if col not in preferred and col != "Notion Page ID"]

    return dataframe[preferred + remaining]


with st.sidebar:
    st.header("Settings")
    st.write("Add these in Streamlit Cloud secrets or your local `.streamlit/secrets.toml` file.")

    notion_token = get_secret("NOTION_TOKEN")
    database_id = get_secret("NOTION_DATABASE_ID")

    if st.button("Refresh Notion Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("Required secrets:")
    st.code(
        'NOTION_TOKEN = "your_token"\nNOTION_DATABASE_ID = "your_database_id"',
        language="toml",
    )

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

metric_cols = st.columns(6)
metric_cols[0].metric("Total", len(df))
metric_cols[1].metric("Tickets", yes_count(df, ["Ticket", "Tickets"]))
metric_cols[2].metric("Handlers", yes_count(df, ["Handler"]))
metric_cols[3].metric("Concert", yes_count(df, ["Concert"]))
metric_cols[4].metric("Cosplay", yes_count(df, ["Cosplay", "Cosplay Contest"]))
metric_cols[5].metric("Makers", yes_count(df, ["Makers", "Makers Contest"]))

st.divider()

search_text = st.text_input(
    "Search",
    placeholder="Name, username, email, or social handle",
)

if search_text:
    mask = filtered.astype(str).apply(
        lambda row: row.str.contains(search_text, case=False, na=False).any(),
        axis=1,
    )
    filtered = filtered[mask]

filter_cols = st.columns(4)

with filter_cols[0]:
    ticket_col = "Ticket" if "Ticket" in df.columns else "Tickets" if "Tickets" in df.columns else None
    if ticket_col:
        selected = st.selectbox("Ticket", ["All", "Yes", "No"])
        if selected != "All":
            filtered = filtered[filtered[ticket_col].astype(str).str.lower() == selected.lower()]

with filter_cols[1]:
    if "Handler" in df.columns:
        selected = st.selectbox("Handler", ["All", "Yes", "No"])
        if selected != "All":
            filtered = filtered[filtered["Handler"].astype(str).str.lower() == selected.lower()]

with filter_cols[2]:
    cosplay_col = "Cosplay" if "Cosplay" in df.columns else "Cosplay Contest" if "Cosplay Contest" in df.columns else None
    if cosplay_col:
        selected = st.selectbox("Cosplay Contest", ["All", "Yes", "No"])
        if selected != "All":
            filtered = filtered[filtered[cosplay_col].astype(str).str.lower() == selected.lower()]

with filter_cols[3]:
    makers_col = "Makers" if "Makers" in df.columns else "Makers Contest" if "Makers Contest" in df.columns else None
    if makers_col:
        selected = st.selectbox("Makers Contest", ["All", "Yes", "No"])
        if selected != "All":
            filtered = filtered[filtered[makers_col].astype(str).str.lower() == selected.lower()]

st.divider()

st.subheader("Export")

export_cols = st.columns([1, 3])
with export_cols[0]:
    excel_file = dataframe_to_excel(order_columns(filtered))

    st.download_button(
        label="Download Excel Export",
        data=excel_file,
        file_name="halofest_notion_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.divider()

st.subheader(f"Registrations ({len(filtered)})")

for _, row in filtered.iterrows():
    name = first_existing(row, ["Name", "Full Name"], "Unknown")
    username = first_existing(row, ["Username", "Badge Name", "Handle", "Social Handle"])
    email = first_existing(row, ["Email"])
    photo_url = get_photo_url(row)

    ticket = first_existing(row, ["Ticket", "Tickets"], "—")
    handler = first_existing(row, ["Handler"], "—")
    concert = first_existing(row, ["Concert"], "—")
    cosplay = first_existing(row, ["Cosplay", "Cosplay Contest"], "—")
    makers = first_existing(row, ["Makers", "Makers Contest"], "—")

    submitted = first_existing(row, ["Submission Date", "Submitted", "Created time", "Created Time"])
    notion_url = first_existing(row, ["Notion URL"])

    with st.container(border=True):
        img_col, info_col = st.columns([1, 3])

        with img_col:
            if photo_url:
                st.image(photo_url, use_container_width=True)
            else:
                st.caption("No photo")

        with info_col:
            title = f"### {name}"
            if username:
                title += f" — `{username}`"
            st.markdown(title)

            if email:
                st.markdown(f"**Email:** [{email}](mailto:{email})")

            st.markdown(
                f"**Ticket:** {ticket} | "
                f"**Handler:** {handler} | "
                f"**Concert:** {concert} | "
                f"**Cosplay:** {cosplay} | "
                f"**Makers:** {makers}"
            )

            caption_parts = []
            if submitted:
                caption_parts.append(f"Submitted: {submitted}")
            if photo_url:
                caption_parts.append(f"Photo: {photo_url.split('/')[-1]}")

            if caption_parts:
                st.caption(" | ".join(caption_parts))

            if notion_url:
                st.link_button("Open in Notion", notion_url)
