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

st.markdown(
    """
    <style>
    .armor-card-img img {
        width: 220px !important;
        height: 220px !important;
        object-fit: cover !important;
        border-radius: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

COLUMN_MAP = {
    "forum_name": "Forum Name",
    "discord": "Discord Handle",
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "Email",
    "ticket": "Purchased Ticket?",
    "handler": "Are you a Handler?",
    "cosplay": "Are you Participating in the Cosplay Contest?",
    "makers": "Are you Participating in the Makers Contest?",
    "forge": "Are you Participating in the Forge Contest?",
    "videographer": "Are you Participating in the Videographer Contest?",
    "prop_photos": "(OPTIONAL) Prop Photos",
    "social": "Social Media Handle",
    "armor_photos": "(OPTIONAL) Armor Photos",
    "shirt": "Shirt Size",
    "din": "(OPTIONAL) DIN",
}


@st.cache_data(ttl=300, show_spinner="Loading data from Notion...")
def load_data(token: str, database_id: str) -> pd.DataFrame:
    return fetch_database(token=token, database_id=database_id)


def get_secret(name: str) -> str:
    return str(st.secrets.get(name, "")).strip()


def normalize_yes_no(value: object) -> str:
    text = str(value).strip().lower()
    return text.rstrip(".!?,;:")


def yes_count(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0

    return int(
        df[column]
        .apply(normalize_yes_no)
        .isin(["yes", "true", "1", "checked"])
        .sum()
    )


def get_value(row: pd.Series, column: str, default: str = "") -> str:
    if column not in row:
        return default

    raw = row.get(column)

    if pd.isna(raw):
        return default

    if isinstance(raw, float) and raw.is_integer():
        return str(int(raw))

    value = str(raw).strip()

    if value.endswith(".0") and value[:-2].isdigit():
        return value[:-2]

    return value if value else default


def get_armor_photo_url(row: pd.Series) -> str:
    column = COLUMN_MAP["armor_photos"]

    if column in row and str(row[column]).strip():
        return str(row[column]).split(",")[0].strip()

    return ""


def order_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    preferred_columns = [
        COLUMN_MAP["forum_name"],
        COLUMN_MAP["discord"],
        COLUMN_MAP["first_name"],
        COLUMN_MAP["last_name"],
        COLUMN_MAP["email"],
        COLUMN_MAP["ticket"],
        COLUMN_MAP["handler"],
        COLUMN_MAP["cosplay"],
        COLUMN_MAP["makers"],
        COLUMN_MAP["forge"],
        COLUMN_MAP["videographer"],
        COLUMN_MAP["prop_photos"],
        COLUMN_MAP["social"],
        COLUMN_MAP["armor_photos"],
        COLUMN_MAP["shirt"],
        COLUMN_MAP["din"],
        "Notion URL",
    ]

    preferred = [col for col in preferred_columns if col in dataframe.columns]
    remaining = [
        col for col in dataframe.columns
        if col not in preferred and col != "Notion Page ID"
    ]

    return dataframe[preferred + remaining]


def require_password() -> None:
    app_password = get_secret("APP_PASSWORD")

    if not app_password:
        st.error("Missing APP_PASSWORD secret.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return

    st.title("🔒 HaloFest Dashboard")
    st.markdown("Please enter the dashboard password to continue.")

    password = st.text_input("Password", type="password", key="password_input")

    if st.button("Login", use_container_width=True):
        if password == app_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()


with st.sidebar:
    st.header("Settings")
    st.write("Add these in Streamlit Cloud secrets or your local `.streamlit/secrets.toml` file.")

    notion_token = get_secret("NOTION_TOKEN")
    database_id = get_secret("NOTION_DATABASE_ID")

    if st.session_state.get("authenticated", False):
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    if st.button("Refresh Notion Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("Required secrets:")
    st.code(
        'NOTION_TOKEN = "your_token"\nNOTION_DATABASE_ID = "your_database_id"\nAPP_PASSWORD = "your_password"',
        language="toml",
    )

require_password()

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

metric_cols = st.columns(7)
metric_cols[0].metric("Total", len(df))
metric_cols[1].metric("Tickets", yes_count(df, COLUMN_MAP["ticket"]))
metric_cols[2].metric("Handlers", yes_count(df, COLUMN_MAP["handler"]))
metric_cols[3].metric("Cosplay", yes_count(df, COLUMN_MAP["cosplay"]))
metric_cols[4].metric("Makers", yes_count(df, COLUMN_MAP["makers"]))
metric_cols[5].metric("Forge", yes_count(df, COLUMN_MAP["forge"]))
metric_cols[6].metric("Video", yes_count(df, COLUMN_MAP["videographer"]))

st.divider()

search_text = st.text_input(
    "Search",
    placeholder="Name, forum name, email, Discord, or social handle",
)

if search_text:
    mask = filtered.astype(str).apply(
        lambda row: row.str.contains(search_text, case=False, na=False).any(),
        axis=1,
    )
    filtered = filtered[mask]

filter_cols = st.columns(6)

filter_fields = [
    ("Ticket", COLUMN_MAP["ticket"]),
    ("Handler", COLUMN_MAP["handler"]),
    ("Cosplay", COLUMN_MAP["cosplay"]),
    ("Makers", COLUMN_MAP["makers"]),
    ("Forge", COLUMN_MAP["forge"]),
    ("Video", COLUMN_MAP["videographer"]),
]

for col, (label, field) in zip(filter_cols, filter_fields):
    with col:
        selected = st.selectbox(label, ["All", "Yes", "No"])
        if selected != "All" and field in filtered.columns:
            filtered = filtered[
                filtered[field].apply(normalize_yes_no) == selected.lower()
            ]

st.divider()

st.subheader("Export")

excel_file = dataframe_to_excel(order_columns(filtered))

st.download_button(
    label="Download Excel Export",
    data=excel_file,
    file_name="halofest_notion_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.divider()

st.subheader(f"Registrations ({len(filtered)})")

for _, row in filtered.iterrows():
    first = get_value(row, COLUMN_MAP["first_name"])
    last = get_value(row, COLUMN_MAP["last_name"])
    full_name = f"{first} {last}".strip() or "Unknown"

    forum_name = get_value(row, COLUMN_MAP["forum_name"])
    discord = get_value(row, COLUMN_MAP["discord"])
    email = get_value(row, COLUMN_MAP["email"])
    social = get_value(row, COLUMN_MAP["social"])

    ticket = get_value(row, COLUMN_MAP["ticket"], "—")
    handler = get_value(row, COLUMN_MAP["handler"], "—")
    cosplay = get_value(row, COLUMN_MAP["cosplay"], "—")
    makers = get_value(row, COLUMN_MAP["makers"], "—")
    forge = get_value(row, COLUMN_MAP["forge"], "—")
    video = get_value(row, COLUMN_MAP["videographer"], "—")
    shirt = get_value(row, COLUMN_MAP["shirt"], "—")
    din = get_value(row, COLUMN_MAP["din"], "—")

    armor_photo_url = get_armor_photo_url(row)
    notion_url = get_value(row, "Notion URL")

    with st.container(border=True):
        img_col, info_col, action_col = st.columns([1, 3, 0.8])

        with img_col:
            if armor_photo_url:
                st.markdown('<div class="armor-card-img">', unsafe_allow_html=True)
                st.image(armor_photo_url)
                st.markdown("</div>", unsafe_allow_html=True)

                with st.popover("View Armor Photo"):
                    st.image(armor_photo_url, use_container_width=True)
            else:
                st.caption("No armor photo")

        with info_col:
            title = f"### {full_name}"
            if forum_name:
                title += f" — `{forum_name}`"
            st.markdown(title)

            if email:
                st.markdown(f"**Email:** [{email}](mailto:{email})")

            if discord or social:
                st.markdown(
                    f"**Discord:** {discord or '—'} | "
                    f"**Social:** {social or '—'}"
                )

            st.markdown(
                f"**Ticket:** {ticket} | "
                f"**Handler:** {handler} | "
                f"**Cosplay:** {cosplay} | "
                f"**Makers:** {makers} | "
                f"**Forge:** {forge} | "
                f"**Video:** {video}"
            )

            st.markdown(
                f"**Shirt Size:** {shirt} | "
                f"**DIN:** {din}"
            )

        with action_col:
            if notion_url:
                st.link_button("Open in Notion", notion_url, use_container_width=True)
