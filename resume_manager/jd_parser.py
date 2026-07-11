"""Lightweight, deterministic job-description parsing helpers.

These don't try to *understand* the JD — that's Claude's job in the
conversation. They extract structure (likely company/title, candidate
keywords, requirement-looking lines) so matching has something concrete
to work against and the ATS scan has a keyword target.
"""

from __future__ import annotations

import re
from collections import Counter

# Skills/tools we care about matching. Kept broad; extend freely.
KNOWN_KEYWORDS = [
    "QA", "quality assurance", "test", "testing", "test case", "test plan",
    "regression", "automation", "manual testing", "defect", "bug", "triage",
    "SDLC", "Agile", "Scrum", "Waterfall", "sprint", "backlog",
    "SQL", "Oracle", "database", "ETL", "data", "data analysis", "dashboard",
    "Power BI", "PowerBI", "Tableau", "Databricks", "Great Expectations",
    "Python", "Java", "JavaScript", "HTML", "CSS", "API", "REST",
    "Selenium", "Cypress", "Playwright", "Cactus", "Sikuli", "Jenkins",
    "CI/CD", "Azure DevOps", "Jira", "documentation", "stakeholder",
    "cross-functional", "requirements", "gap analysis", "data quality",
    "validation", "verification", "unit test", "integration test",
]

_TITLE_HINTS = re.compile(
    r"\b(analyst|engineer|developer|qa|quality|tester|specialist|lead|manager|scientist)\b",
    re.I,
)


def extract_keywords(text: str) -> list[dict]:
    """Return known keywords found in the JD with their frequency."""
    lower = text.lower()
    hits = []
    for kw in KNOWN_KEYWORDS:
        count = len(re.findall(r"\b" + re.escape(kw.lower()) + r"\b", lower))
        if count:
            hits.append({"keyword": kw, "count": count})
    hits.sort(key=lambda h: (-h["count"], h["keyword"].lower()))
    return hits


def guess_company(text: str) -> str | None:
    for line in (l.strip() for l in text.splitlines()):
        m = re.search(r"\bat\s+([A-Z][A-Za-z0-9&.\- ]{2,40})", line)
        if m:
            return m.group(1).strip(" .")
    return None


def guess_title(text: str) -> str | None:
    for line in (l.strip() for l in text.splitlines() if l.strip()):
        if 3 <= len(line.split()) <= 8 and _TITLE_HINTS.search(line):
            return line
    return None


def requirement_lines(text: str) -> list[str]:
    """Lines that look like responsibilities/requirements (bulleted or imperative)."""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.match(r"^([\-•\*●▪–o]|\d+[.)])\s+", line):
            out.append(re.sub(r"^([\-•\*●▪–o]|\d+[.)])\s+", "", line))
        elif re.match(r"^(Experience|Required|Responsib|Qualif|Must|You will|Skills)", line, re.I):
            out.append(line)
    return out


def parse(text: str) -> dict:
    """Top-level convenience parse used by the MCP tool."""
    return {
        "company_guess": guess_company(text),
        "title_guess": guess_title(text),
        "keywords": extract_keywords(text),
        "requirements": requirement_lines(text),
        "word_count": len(re.findall(r"\w+", text)),
    }
