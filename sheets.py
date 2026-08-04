"""
sheets.py

Appends generated drafts to a Google Sheet tab so you can review and
copy-paste them into Facebook's native post scheduler.

Reuses the same service-account pattern as your Instagram scheduler
(sheets.py in that project) — if you already have a service account
JSON set up for that, you can reuse the same credentials here; just
share this new Sheet with the same service account email.

Sheet columns expected in row 1 (create these headers once, manually):
Date | Post Type | Draft Text | Status | Links | Recommended Day
"""

import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

WORKSHEET_NAME = os.environ.get("FB_SHEET_TAB_NAME", "FB Group Drafts")


def _get_client() -> gspread.Client:
    creds_json = os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_worksheet():
    client = _get_client()
    spreadsheet_id = os.environ["SPREADSHEET_ID"]
    sh = client.open_by_key(spreadsheet_id)

    try:
        ws = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=200, cols=6)
        ws.append_row(
            ["Date", "Post Type", "Draft Text", "Status", "Links", "Recommended Day"]
        )

    return ws


def append_draft(
    date: str,
    post_type: str,
    draft_text: str,
    status: str = "Ready",
    link: str = "",
    recommended_day: str = "",
):
    ws = _get_worksheet()
    ws.append_row([date, post_type, draft_text, status, link, recommended_day])
