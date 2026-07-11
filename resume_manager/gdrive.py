"""Google integration.

Two auth paths, by necessity:
  * Drive uploads use OAuth *user* credentials so the uploaded PDF is owned by
    Graeson and counts against his own storage. (A service account has no
    personal-Drive storage quota, so it cannot own files in My Drive.)
  * Sheets logging uses the service account — editing a user-owned Sheet
    consumes no service-account storage, and it needs no interactive sign-in.

Everything degrades with a clear, actionable message until the relevant
credential is in place, so the rest of the MCP works offline.
"""

from __future__ import annotations

from pathlib import Path

from . import config

_SA_MSG = (
    "Service-account key not found. Place it at:\n"
    f"  {config.SERVICE_ACCOUNT_PATH}\n"
    "and share the tracker Sheet with the service-account email (Editor). "
    "See README 'Google setup'."
)
_OAUTH_CLIENT_MSG = (
    "OAuth client not found. Place the Desktop OAuth client JSON at:\n"
    f"  {config.OAUTH_CLIENT_PATH}\n"
    "See README 'Google setup'."
)
_OAUTH_TOKEN_MSG = (
    "Drive not authorized yet. Run the one-time sign-in:\n"
    "  python -m resume_manager.authorize\n"
    "which opens a browser to grant Drive access and saves the token to:\n"
    f"  {config.OAUTH_TOKEN_PATH}"
)


# --- status -----------------------------------------------------------------

def credentials_status() -> dict:
    """Report readiness of both credential paths so tools can fail gracefully."""
    sa = config.SERVICE_ACCOUNT_PATH.exists()
    client = config.OAUTH_CLIENT_PATH.exists()
    token = config.OAUTH_TOKEN_PATH.exists()
    drive_ready = client and token
    msgs = []
    if not sa:
        msgs.append(_SA_MSG)
    if not client:
        msgs.append(_OAUTH_CLIENT_MSG)
    elif not token:
        msgs.append(_OAUTH_TOKEN_MSG)
    return {
        "ready": sa and drive_ready,
        "sheets_ready": sa,
        "drive_ready": drive_ready,
        "service_account_path": str(config.SERVICE_ACCOUNT_PATH),
        "oauth_client_path": str(config.OAUTH_CLIENT_PATH),
        "oauth_token_path": str(config.OAUTH_TOKEN_PATH),
        "message": "OK" if (sa and drive_ready) else "\n\n".join(msgs),
    }


# --- Sheets (service account) ----------------------------------------------

def _sa_creds():
    if not config.SERVICE_ACCOUNT_PATH.exists():
        raise RuntimeError(_SA_MSG)
    from google.oauth2.service_account import Credentials

    return Credentials.from_service_account_file(
        str(config.SERVICE_ACCOUNT_PATH), scopes=config.SHEETS_SA_SCOPES
    )


def _worksheet():
    import gspread

    gc = gspread.authorize(_sa_creds())
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
    jd = (job_description or "").strip()
    if len(jd) > 5000:
        jd = jd[:5000] + " …[truncated]"
    ws.append_row([company, job_title, jd, application_date, resume_name],
                  value_input_option="USER_ENTERED")
    return {"logged": True, "row": [company, job_title, application_date, resume_name]}


# --- Drive (OAuth user) -----------------------------------------------------

def _oauth_creds(interactive: bool = False):
    """Return valid OAuth user credentials for Drive.

    Loads and refreshes the saved token. If it's missing/invalid and
    `interactive` is True, runs the browser consent flow and saves a new token;
    otherwise raises a clear message telling the user to run the setup once.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = None
    if config.OAUTH_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(
            str(config.OAUTH_TOKEN_PATH), config.DRIVE_OAUTH_SCOPES
        )
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds)
        return creds
    if not interactive:
        raise RuntimeError(_OAUTH_TOKEN_MSG)

    # Interactive one-time consent.
    if not config.OAUTH_CLIENT_PATH.exists():
        raise RuntimeError(_OAUTH_CLIENT_MSG)
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(
        str(config.OAUTH_CLIENT_PATH), config.DRIVE_OAUTH_SCOPES
    )
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    return creds


def _save_token(creds) -> None:
    config.OAUTH_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.OAUTH_TOKEN_PATH.write_text(creds.to_json())
    config.OAUTH_TOKEN_PATH.chmod(0o600)


def authorize(interactive: bool = True) -> dict:
    """Run/validate the one-time Drive sign-in. Returns a status dict."""
    creds = _oauth_creds(interactive=interactive)
    return {"authorized": bool(creds and creds.valid),
            "token_path": str(config.OAUTH_TOKEN_PATH)}


def upload_pdf(pdf_path: str | Path) -> dict:
    """Upload a PDF into the '2026' Drive folder as the signed-in user."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    drive = build("drive", "v3", credentials=_oauth_creds())
    meta = {"name": path.name, "parents": [config.DRIVE_FOLDER_ID]}
    media = MediaFileUpload(str(path), mimetype="application/pdf")
    f = drive.files().create(body=meta, media_body=media,
                             fields="id, webViewLink").execute()
    return {"file_id": f["id"], "link": f.get("webViewLink")}
