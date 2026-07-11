"""Resume_Manager MCP server.

Design: the *intelligence* (reading the JD, choosing and rewording bullets in
Graeson's voice, never inventing experience) lives with Claude in the
conversation. These tools provide the deterministic scaffolding: the profile
data, JD structure, the ATS scan, PDF rendering, and Google I/O.

Typical flow Claude drives:
  get_profile -> parse_job_description -> (compose tailored content) ->
  build_resume -> ats_scan -> (revise) -> save_to_drive -> log_application
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import ats, config, gdrive, jd_parser, render

mcp = FastMCP("Resume_Manager")


def _slug(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text or "")
    return "".join(words) or "Unknown"


def resume_filename(company: str, job_title: str) -> str:
    """Project naming convention: Gehringer_CompanyName_JobTitle.pdf"""
    return f"Gehringer_{_slug(company)}_{_slug(job_title)}.pdf"


@mcp.tool()
def get_profile() -> dict:
    """Return Graeson's full profile (work history, skills, phrasing bank,
    resume versions, and unresolved items that must be confirmed before use)."""
    return json.loads(Path(config.PROFILE_PATH).read_text())


@mcp.tool()
def parse_job_description(jd_text: str) -> dict:
    """Extract structure from a pasted job description: likely company/title,
    matched keywords with frequency, and requirement-looking lines."""
    return jd_parser.parse(jd_text)


@mcp.tool()
def ats_scan(resume_text: str, jd_text: str) -> dict:
    """Run the ATS check: keyword coverage %, matched/missing keywords,
    format warnings, and a verdict. Run this before finalizing any resume."""
    return ats.scan(resume_text, jd_text)


@mcp.tool()
def build_resume(content: dict, company: str, job_title: str,
                 version: str = "software_qa") -> dict:
    """Render tailored resume `content` to a PDF.

    `content` keys: name, contact{address,city,phone,email}, summary,
    experience[{title,company,location,dates,bullets[]}], education[...],
    skills (list or string). Returns the PDF path, filename, and the resume's
    plain text (pass that text straight into ats_scan)."""
    if version not in config.RESUME_VERSIONS:
        return {"error": f"version must be one of {config.RESUME_VERSIONS}"}
    filename = resume_filename(company, job_title)
    out_path = config.OUTPUT_DIR / filename
    pdf_path = render.build_resume(content, out_path)
    return {
        "pdf_path": pdf_path,
        "filename": filename,
        "resume_name": filename.rsplit(".", 1)[0],
        "resume_text": render.to_text(content),
        "version": version,
    }


@mcp.tool()
def google_status() -> dict:
    """Check whether the Google service-account key is in place and where."""
    return gdrive.credentials_status()


@mcp.tool()
def save_to_drive(pdf_path: str) -> dict:
    """Upload a generated PDF to the '2026' Google Drive folder."""
    return gdrive.upload_pdf(pdf_path)


@mcp.tool()
def log_application(company: str, job_title: str, job_description: str,
                   application_date: str, resume_name: str) -> dict:
    """Append an application to the tracker Sheet (Company, Job Title, Job
    Description, Application Date, Resume Name). Ensures the header row exists,
    is bold, and is frozen."""
    return gdrive.log_application(company, job_title, job_description,
                                  application_date, resume_name)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
