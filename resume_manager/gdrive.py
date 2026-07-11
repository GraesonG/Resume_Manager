"""Google integration (Option A: service account).

Uploads finished PDFs to the "2026" Drive folder and logs applications to the
tracker Sheet (with a pinned, bold header row). All functions degrade with a
clear, actionable error until the service-account key is in place — so the rest
of the MCP works offline.
"""

from __future__ import annotations

from pathlib import Path

from . import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_SETUP_MSG = (
    "Google credentials not ready. Place the service-account JSON key at:\n"
    f"  {config.SERVICE_ACCOUNT_PATH}\n"
    "and share BOTH the tracker Sheet and the '2026' Drive folder with the "
    "service account's email (Editor). See README 'Google setup'."
)


def credentials_status() -> dict:
    """Quick check used by tools so they can fail gracefully."""
    exists = config.SERVICE_ACCOUNT_PATH.exists()
    return {"ready": exists, "key_path": str(config.SERVICE_ACCOUNT_PATH),
            "message": "OK" if exists else _SETUP_MSG}


def _creds():
    if not config.SERVICE_ACCOUNT_PATH.exists():
        raise RuntimeError(_SETUP_MSG)
    from google.oauth2.service_account import Credentials

    return Credentials.from_service_account_file(str(config.SERVICE_ACCOUNT_PATH), scopes=SCOPES)


def upload_pdf(pdf_path: str | Path) -> dict:
    """Upload a PDF into the '2026' Drive folder. Returns id + link."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    drive = build("drive", "v3", credentials=_creds())
    meta = {"name": path.name, "parents": [config.DRIVE_FOLDER_ID]}
    media = MediaFileUpload(str(path), mimetype="application/pdf")
    f = drive.files().create(body=meta, media_body=media,
                             fields="id, webViewLink").execute()
    return {"file_id": f["id"], "link": f.get("webViewLink")}


def _worksheet():
    import gspread

    gc = gspread.authorize(_creds())
    return gc.open_by_key(config.TRACKER_SHEET_ID).sheet1


def ensure_tracker_setup() -> dict:
    """Make sure row 1 holds the headers, is bold, and is frozen."""
    ws = _worksheet()
    if ws.row_values(1) != config.TRACKER_HEADERS:
        ws.update([config.TRACKER_HEADERS], "A1")
    ws.freeze(rows=1)
    ws.format("A1:E1", {"textFormat": {"bold": True}})
    return {"headers": config.TRACKER_HEADERS, "frozen": True}


def log_application(company: str, job_title: str, job_description: str,
                    application_date: str, resume_name: str) -> dict:
    """Append one application row to the tracker Sheet."""
    ensure_tracker_setup()
    ws = _worksheet()
    # Keep the JD cell from bloating the sheet.
    jd = (job_description or "").strip()
    if len(jd) > 5000:
        jd = jd[:5000] + " …[truncated]"
    ws.append_row([company, job_title, jd, application_date, resume_name],
                  value_input_option="USER_ENTERED")
    return {"logged": True, "row": [company, job_title, application_date, resume_name]}
