from __future__ import annotations

from typing import Any

import pandas as pd
from notion_client import Client


def _plain_text(items: list[dict[str, Any]]) -> str:
    return " ".join(item.get("plain_text", "") for item in items).strip()


def notion_property_to_value(prop: dict[str, Any]) -> Any:
    """Convert common Notion property types into spreadsheet-friendly values."""
    prop_type = prop.get("type")

    if prop_type == "title":
        return _plain_text(prop.get("title", []))

    if prop_type == "rich_text":
        return _plain_text(prop.get("rich_text", []))

    if prop_type == "select":
        value = prop.get("select")
        return value.get("name", "") if value else ""

    if prop_type == "multi_select":
        return ", ".join(item.get("name", "") for item in prop.get("multi_select", []))

    if prop_type == "status":
        value = prop.get("status")
        return value.get("name", "") if value else ""

    if prop_type == "email":
        return prop.get("email") or ""

    if prop_type == "phone_number":
        return prop.get("phone_number") or ""

    if prop_type == "url":
        return prop.get("url") or ""

    if prop_type == "checkbox":
        return bool(prop.get("checkbox", False))

    if prop_type == "number":
        return prop.get("number")

    if prop_type == "date":
        value = prop.get("date")
        if not value:
            return ""
        start = value.get("start", "")
        end = value.get("end")
        return f"{start} - {end}" if end else start

    if prop_type == "created_time":
        return prop.get("created_time", "")

    if prop_type == "last_edited_time":
        return prop.get("last_edited_time", "")

    if prop_type == "people":
        people = prop.get("people", [])
        return ", ".join(person.get("name", "") for person in people)

    if prop_type == "files":
        links: list[str] = []
        for file_item in prop.get("files", []):
            file_type = file_item.get("type")
            if file_type == "external":
                links.append(file_item.get("external", {}).get("url", ""))
            elif file_type == "file":
                links.append(file_item.get("file", {}).get("url", ""))
        return ", ".join(link for link in links if link)

    if prop_type == "formula":
        formula = prop.get("formula", {})
        formula_type = formula.get("type")
        return formula.get(formula_type, "") if formula_type else ""

    if prop_type == "rollup":
        rollup = prop.get("rollup", {})
        rollup_type = rollup.get("type")
        value = rollup.get(rollup_type, "") if rollup_type else ""
        return str(value)

    if prop_type == "relation":
        relations = prop.get("relation", [])
        return ", ".join(item.get("id", "") for item in relations)

    return ""


def fetch_database(token: str, database_id: str) -> pd.DataFrame:
    """Fetch all rows from a Notion database using pagination."""
    notion = Client(auth=token)
    rows: list[dict[str, Any]] = []
    next_cursor: str | None = None

    while True:
        kwargs: dict[str, Any] = {"database_id": database_id}
        if next_cursor:
            kwargs["start_cursor"] = next_cursor

        response = notion.data_sources.query(**kwargs)

        for page in response.get("results", []):
            row: dict[str, Any] = {}
            for name, prop in page.get("properties", {}).items():
                row[name] = notion_property_to_value(prop)
            row["Notion Page ID"] = page.get("id", "")
            row["Notion URL"] = page.get("url", "")
            rows.append(row)

        if not response.get("has_more"):
            break

        next_cursor = response.get("next_cursor")

    return pd.DataFrame(rows)
