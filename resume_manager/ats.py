"""A self-contained ATS (applicant tracking system) scorer.

It approximates what a keyword-matching ATS does: how many of the job
description's important terms actually appear in the resume, plus a few
format sanity checks resumes commonly fail. It is intentionally strict and
deterministic so the score is reproducible and explainable.
"""

from __future__ import annotations

import re

from .jd_parser import extract_keywords


def _present(term: str, text: str) -> bool:
    return re.search(r"\b" + re.escape(term.lower()) + r"\b", text.lower()) is not None


def scan(resume_text: str, jd_text: str) -> dict:
    """Compare a resume against a JD and return a coverage score + gaps."""
    jd_keywords = extract_keywords(jd_text)
    if not jd_keywords:
        matched, missing = [], []
        coverage = 0.0
    else:
        matched = [k["keyword"] for k in jd_keywords if _present(k["keyword"], resume_text)]
        missing = [k["keyword"] for k in jd_keywords if not _present(k["keyword"], resume_text)]
        coverage = round(100 * len(matched) / len(jd_keywords), 1)

    # Format checks
    warnings = []
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", resume_text):
        warnings.append("No email address detected.")
    if not re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", resume_text):
        warnings.append("No phone number detected.")
    word_count = len(re.findall(r"\w+", resume_text))
    if word_count > 900:
        warnings.append(f"Resume is long ({word_count} words) — may exceed 1–1.5 pages.")
    for section in ("experience", "education", "skills"):
        if section not in resume_text.lower():
            warnings.append(f"Missing a '{section.title()}' section heading.")

    return {
        "coverage_percent": coverage,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "format_warnings": warnings,
        "verdict": _verdict(coverage, warnings),
    }


def _verdict(coverage: float, warnings: list[str]) -> str:
    if coverage >= 75 and not warnings:
        return "STRONG — ready to finalize."
    if coverage >= 60:
        return "OK — consider weaving in the missing keywords before finalizing."
    return "WEAK — significant keyword gaps; revise before finalizing."
