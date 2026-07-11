# Resume_Manager

An MCP server that helps tailor a 1–1.5 page PDF resume to a specific job
description — matching Graeson's real experience against the role, never
inventing experience, running an ATS check before finalizing, saving the PDF to
Google Drive, and logging the application to a tracker Sheet.

## How it works

The **intelligence** lives with Claude in the conversation (reading the JD,
selecting and rewording bullets in Graeson's voice). The **MCP tools** provide
the deterministic scaffolding:

| Tool | Purpose |
|------|---------|
| `get_profile` | Returns the work history, skills, phrasing bank, resume versions, and unresolved items (from `data/profile.json`). |
| `parse_job_description` | Extracts likely company/title, keywords, and requirement lines from a pasted JD. |
| `build_resume` | Renders tailored content to a PDF (Times New Roman 12pt, 1" margins, single spaced). |
| `ats_scan` | Keyword-coverage % + format checks + verdict. Run before finalizing. |
| `google_status` | Reports whether the Google key is in place. |
| `save_to_drive` | Uploads the PDF to the "2026" Drive folder. |
| `log_application` | Appends a row to the tracker Sheet (header pinned + bold). |

**Typical flow:** `get_profile` → `parse_job_description` → *(compose content)* →
`build_resume` → `ats_scan` → *(revise)* → `save_to_drive` → `log_application`.

Two base versions: **`software_qa`** and **`data_analyst`**.
Output PDFs are named `Gehringer_CompanyName_JobTitle.pdf`.

## Setup

### 1. Python (3.10+ required)

The system Python on this Mac is 3.9, but the MCP SDK needs 3.10+. Install a
newer one and create a virtual environment:

```bash
brew install python@3.11
cd ~/Documents/GitHub/Resume_Manager
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .          # installs deps + the resume_manager package
```

(No system libraries needed — PDF rendering uses `fpdf2` and embeds the real
Times New Roman from `/System/Library/Fonts/Supplemental/`.)

### 2. Google setup (service account)

1. In Google Cloud Console (signed in as the account that owns the Drive folder
   + Sheet), create a project and enable the **Google Sheets API** and
   **Google Drive API**.
2. Create a **service account**, then create a **JSON key** and download it.
3. Save the key to: `~/Documents/GitHub/Resume-Builder/service-account.json`
   (git-ignored — never commit it).
4. **Share** both the tracker Sheet and the "2026" Drive folder with the service
   account's email (Editor).

Run `google_status` to confirm the key is found.

### 3. Register the MCP with Claude

```bash
claude mcp add resume-manager -- ~/Documents/GitHub/Resume_Manager/.venv/bin/resume-manager
```

## Default formatting

Times New Roman · 12 pt body · 1" margins · single spaced · 8 pt after
paragraphs · left aligned · black · bold headings.

## Configuration

IDs and paths live in `resume_manager/config.py` and can be overridden with env
vars (`RESUME_SERVICE_ACCOUNT`, `RESUME_DRIVE_FOLDER_ID`,
`RESUME_TRACKER_SHEET_ID`, `RESUME_OUTPUT_DIR`, …).

## Security

`service-account.json` and `.env` are git-ignored. Never commit credentials.
