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

st.markdown(
    """
    <style>
    .stApp {
        background: #070b1a;
        color: #f8fafc;
    }

    [data-testid="stSidebar"] {
        background: #090f24;
        border-right: 1px solid rgba(148, 163, 184, 0.15);
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        color: #94a3b8;
        margin-top: 0.25rem;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: #0d1733;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }

    .metric-label {
        color: #a5b4fc;
        font-size: 0.85rem;
        margin-bottom: 0.35rem;
    }

    .metric-value {
        color: #ffffff;
        font-size: 1.9rem;
        font-weight: 800;
    }

    .panel {
        background: #0b1228;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 18px;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
    }

    .registration-card {
        background: #0d1733;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 14px 34px rgba(0,0,0,0.22);
    }

    .armor-img img {
        width: 220px !important;
        height: 220px !important;
        object-fit: cover !important;
        border-radius: 14px !important;
        border: 1px solid rgba(148, 163, 184, 0.25);
    }

    .name-line {
        font-size: 1.35rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }

    .tag {
        display: inline-block;
        background: rgba(203, 69, 255, 0.16);
        color: #e879f9;
        border: 1px solid rgba(203, 69, 255, 0.35);
        border-radius: 8px;
        padding: 0.12rem 0.45rem;
        margin-left: 0.35rem;
        font-size: 0.95rem;
    }

    .muted {
        color: #94a3b8;
    }

    .pill {
        display: inline-block;
        border-radius: 999px;
        padding: 0.22rem 0.6rem;
        margin: 0.18rem 0.25rem 0.18rem 0;
        font-size: 0.85rem;
        border: 1px solid rgba(148, 163, 184, 0.22);
        background: rgba(15, 23, 42, 0.7);
    }

    .yes {
        color: #34d399;
        border-color: rgba(52, 211, 153, 0.35);
        background: rgba(52, 211, 153, 0.09);
    }

    .no {
        color: #f87171;
        border-color: rgba(248, 113, 113, 0.35);
        background: rgba(248, 113, 113, 0.09);
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid rgba(203, 69, 255, 0.45);
        background: linear-gradient(90deg, #c026d3, #7c3aed);
        color: white;
        font-weight: 700;
    }

    div[data-testid="stPopover"] button {
        background: #111a36 !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
        color: #e2e8f0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🛡️ HaloFest Attendance Registration</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Admin dashboard powered by Notion data.</div>', unsafe_allow_html=True)


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

    value = str(row.get(column, "")).strip()
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

    st.markdown('<div class="main-title">🔒 HaloFest Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Enter the dashboard password to continue.</div>', unsafe_allow_html=True)

    password = st.text_input("Password", type="password", key="password_input")

    if st.button("Login", use_container_width=True):
        if password == app_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()


def pill(label: str, value: str) -> str:
    normalized = normalize_yes_no(value)
    css = "yes" if normalized == "yes" else "no" if normalized == "no" else ""
    return f'<span class="pill {css}"><strong>{label}:</strong> {value}</span>'


with st.sidebar:
    st.header("HaloFest")
    st.caption("Notion-powered dashboard")

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

metrics = [
    ("Total", len(df)),
    ("Tickets", yes_count(df, COLUMN_MAP["ticket"])),
    ("Handlers", yes_count(df, COLUMN_MAP["handler"])),
    ("Cosplay", yes_count(df, COLUMN_MAP["cosplay"])),
    ("Makers", yes_count(df, COLUMN_MAP["makers"])),
    ("Forge", yes_count(df, COLUMN_MAP["forge"])),
    ("Video", yes_count(df, COLUMN_MAP["videographer"])),
]

metric_cols = st.columns(7)

for col, (label, value) in zip(metric_cols, metrics):
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="panel">', unsafe_allow_html=True)

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

st.markdown("</div>", unsafe_allow_html=True)

export_cols = st.columns([1, 4])

with export_cols[0]:
    excel_file = dataframe_to_excel(order_columns(filtered))

    st.download_button(
        label="Export Excel",
        data=excel_file,
        file_name="halofest_notion_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.markdown(f"### Registrations ({len(filtered)})")

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

    st.markdown('<div class="registration-card">', unsafe_allow_html=True)

    img_col, info_col, action_col = st.columns([1.1, 3.4, 0.9])

    with img_col:
        if armor_photo_url:
            st.markdown('<div class="armor-img">', unsafe_allow_html=True)
            st.image(armor_photo_url)
            st.markdown("</div>", unsafe_allow_html=True)

            with st.popover("Zoom"):
                st.image(armor_photo_url, use_container_width=True)
        else:
            st.caption("No armor photo")

    with info_col:
        tag = f'<span class="tag">{forum_name}</span>' if forum_name else ""
        st.markdown(
            f'<div class="name-line">{full_name}{tag}</div>',
            unsafe_allow_html=True,
        )

        contact_line = []
        if email:
            contact_line.append(f"Email: {email}")
        if discord:
            contact_line.append(f"Discord: {discord}")
        if social:
            contact_line.append(f"Social: {social}")

        if contact_line:
            st.markdown(
                f'<div class="muted">{" • ".join(contact_line)}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            pill("Ticket", ticket)
            + pill("Handler", handler)
            + pill("Cosplay", cosplay)
            + pill("Makers", makers)
            + pill("Forge", forge)
            + pill("Video", video),
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="muted">Shirt Size: {shirt} • DIN: {din}</div>',
            unsafe_allow_html=True,
        )

    with action_col:
        if notion_url:
            st.link_button("Notion", notion_url, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
