"""Central configuration: paths, IDs, and default formatting.

Anything environment-specific can be overridden with an env var so the code
stays portable if the user moves folders or accounts later.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Repo + working locations -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_PATH = Path(os.environ.get("RESUME_PROFILE_PATH", DATA_DIR / "profile.json"))

# Where the user's resume source + generated PDFs live (see project spec).
RESUME_BUILDER_DIR = Path(
    os.environ.get(
        "RESUME_BUILDER_DIR",
        Path.home() / "Documents" / "GitHub" / "Resume-Builder",
    )
)
OUTPUT_DIR = Path(os.environ.get("RESUME_OUTPUT_DIR", RESUME_BUILDER_DIR / "output"))

# --- Google (Option A: service account) --------------------------------------
SERVICE_ACCOUNT_PATH = Path(
    os.environ.get(
        "RESUME_SERVICE_ACCOUNT",
        RESUME_BUILDER_DIR / "service-account.json",
    )
)
# "2026" output folder + application tracker sheet (from the project spec).
DRIVE_FOLDER_ID = os.environ.get("RESUME_DRIVE_FOLDER_ID", "1EE5OQ7DGx7kPKf6rAtYpVI3KDdr2Tp4s")
TRACKER_SHEET_ID = os.environ.get(
    "RESUME_TRACKER_SHEET_ID", "1fcbFFfMR6hyLRbBRqj13nGolnKxC9GGUtU_1PoYYPUs"
)
TRACKER_HEADERS = [
    "Company",
    "Job Title",
    "Job Description",
    "Application Date",
    "Resume Name",
]

# --- Fonts (embed the real Times New Roman from macOS) ------------------------
_FONT_DIR = Path("/System/Library/Fonts/Supplemental")
FONT_FILES = {
    "": _FONT_DIR / "Times New Roman.ttf",
    "B": _FONT_DIR / "Times New Roman Bold.ttf",
    "I": _FONT_DIR / "Times New Roman Italic.ttf",
    "BI": _FONT_DIR / "Times New Roman Bold Italic.ttf",
}
FONT_FAMILY = "Times New Roman"

# --- Default text settings (from the project spec) ---------------------------
PAGE_FORMAT = "Letter"  # US resume
MARGIN_IN = 1.0  # 1 inch on all sides
BODY_PT = 12
NAME_PT = 22
SECTION_PT = 13
LINE_SPACING = 1.0  # single
PARA_AFTER_PT = 8  # 8 pt after paragraphs (newer Word default)

# Two base resume versions.
RESUME_VERSIONS = ("software_qa", "data_analyst")
