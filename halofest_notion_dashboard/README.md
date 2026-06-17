# HaloFest Notion Dashboard

A simple Streamlit app that pulls records from a Notion database, displays them in a dashboard, and exports a clean Excel spreadsheet.

## Features

- Pulls all Notion database rows with pagination
- Handles common Notion property types
- Streamlit dashboard with quick stats
- Filters by Status and Regiment when those columns exist
- Search across all visible columns
- Styled Excel export using `openpyxl`
- Ready for GitHub + Streamlit Cloud

## Local Setup

### 1. Clone or download this repo

```bash
git clone YOUR_REPO_URL
cd halofest_notion_dashboard
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add Streamlit secrets

Copy the example secrets file:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
NOTION_TOKEN = "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
NOTION_DATABASE_ID = "your_notion_database_id_here"
```

Do not commit the real `secrets.toml` file.

### 4. Give your Notion integration database access

In Notion:

1. Open your database.
2. Click the `•••` menu.
3. Go to connections/integrations.
4. Add your Notion integration.

### 5. Run the app

```bash
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Push this folder to GitHub.
2. Go to Streamlit Cloud.
3. Create a new app from your GitHub repo.
4. Set the main file path to:

```text
app.py
```

5. Add your secrets in Streamlit Cloud:

```toml
NOTION_TOKEN = "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
NOTION_DATABASE_ID = "your_notion_database_id_here"
```

6. Deploy.

## Recommended Notion Columns

The app works with flexible Notion columns, but these names unlock the default metrics and filters:

- Name
- Status
- Regiment
- Email
- Discord
- Costume Name
- Armor Photo
- Notes

Suggested Status options:

- Submitted
- Under Review
- Approved
- Needs Info
- Rejected

## Notes

Notion file URLs can expire if they are internal Notion-hosted files. For long-term photo exports, Google Drive, Cloudflare R2, or another storage provider is better. Store the public/shareable URL in Notion for cleaner exports.
