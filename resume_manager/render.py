"""Render a resume to PDF with fpdf2, embedding the real Times New Roman.

Layout mirrors Graeson's real 2023 resume template:
  - contact block first (stacked, small), then a large name, then a heavy rule
  - section headers: bold, UPPERCASE, with a thin full-width rule beneath
  - each entry: **Company - Location** — *Title* on one line, dates on the next,
    then bullets
  - skills as a single comma-separated line (no grouped categories)

Honors the project defaults: Times New Roman, 12pt body, 1-inch margins, single
line spacing, left aligned, black, headings bold. Claude composes the tailored
bullets; this module only lays them out.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from . import config

# fpdf2 subsets embedded fonts via fontTools, which logs verbosely at INFO.
# Quiet it so the MCP's stderr stays readable.
logging.getLogger("fontTools").setLevel(logging.ERROR)

PT = 25.4 / 72  # points -> mm
BODY_H = config.BODY_PT * PT * 1.12  # single line height with light leading
PARA_AFTER = config.PARA_AFTER_PT * PT
BULLET = "•"  # • filled bullet (guaranteed glyph in Times New Roman)
EMDASH = "—"  # — between Company-Location and Title


class ResumePDF(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format=config.PAGE_FORMAT)
        m = config.MARGIN_IN * 25.4
        self.set_margins(m, m, m)
        self.set_auto_page_break(True, margin=m)
        for style, path in config.FONT_FILES.items():
            self.add_font(config.FONT_FAMILY, style, str(path))
        self.set_text_color(0, 0, 0)
        self.add_page()

    @property
    def content_width(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def _text(self, txt: str, *, size: int = config.BODY_PT, style: str = "",
              h: float = BODY_H, indent: float = 0.0) -> None:
        """One wrapped paragraph, left aligned, ending on its own line."""
        self.set_font(config.FONT_FAMILY, style, size)
        self.set_x(self.l_margin + indent)
        self.multi_cell(self.content_width - indent, h, txt,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

    def _inline(self, runs: list[tuple[str, str]], h: float = BODY_H,
                size: int = config.BODY_PT) -> None:
        """Write several styled runs on the same wrapped line, e.g.
        [("General Motors - Chandler, AZ", "B"), (" — ", ""), ("Title", "I")]."""
        self.set_x(self.l_margin)
        for text, style in runs:
            self.set_font(config.FONT_FAMILY, style, size)
            self.write(h, text)
        self.ln(h)

    def heavy_rule(self, gap: float = 2.0) -> None:
        y = self.get_y() + 0.6
        self.set_line_width(0.6)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.set_line_width(0.2)
        self.set_y(y + gap)

    def thin_rule(self, gap: float = 1.5) -> None:
        y = self.get_y() + 0.4
        self.set_line_width(0.2)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.set_y(y + gap)

    def section(self, title: str) -> None:
        self.ln(PARA_AFTER * 0.6)
        self._text(title.upper(), size=config.SECTION_PT, style="B",
                   h=config.SECTION_PT * PT * 1.1)
        self.thin_rule()
        self.ln(PARA_AFTER * 0.3)

    def header_block(self, content: dict) -> None:
        # Contact block first, stacked and small, then the large name.
        c = content.get("contact", {})
        for part in (c.get("address"), c.get("city"), c.get("phone"), c.get("email")):
            if part:
                self._text(part, h=config.BODY_PT * PT * 1.05)
        self.ln(1.0)
        self._text(content.get("name", c.get("name", "")),
                   size=config.NAME_PT, h=config.NAME_PT * PT * 1.05)
        self.heavy_rule()

    def entry_heading(self, primary: str, title: str) -> None:
        runs = [(primary, "B")]
        if title:
            runs += [(f"  {EMDASH} ", ""), (title, "I")]
        self._inline(runs)

    def experience_entry(self, job: dict) -> None:
        primary = " - ".join(p for p in (job.get("company"), job.get("location")) if p)
        self.entry_heading(primary, job.get("title", ""))
        if job.get("dates"):
            self._text(job["dates"])
        for bullet in job.get("bullets", []):
            self._text(f"{BULLET}  {bullet}", indent=6.0)
        self.ln(PARA_AFTER * 0.7)


def build_resume(content: dict, output_path: str | Path) -> str:
    """Render `content` to a PDF at `output_path`. Returns the path."""
    pdf = ResumePDF()
    pdf.header_block(content)

    # No summary by default (matches the template); render only if supplied.
    if content.get("summary"):
        pdf.section("Summary")
        pdf._text(content["summary"])

    if content.get("experience"):
        pdf.section("Experience")
        for job in content["experience"]:
            pdf.experience_entry(job)

    if content.get("education"):
        pdf.section("Education")
        for ed in content["education"]:
            primary = ", ".join(p for p in (ed.get("school"), ed.get("location")) if p)
            degree = ed.get("degree")
            detail = ed.get("detail", "")
            title = f"{degree} {detail}".strip() if degree else detail
            pdf.entry_heading(primary, title)
            if ed.get("dates"):
                pdf._text(ed["dates"])
            pdf.ln(PARA_AFTER * 0.5)

    if content.get("skills"):
        pdf.section("Skills")
        skills = content["skills"]
        pdf._text(", ".join(skills) if isinstance(skills, list) else str(skills))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    return str(out)


def to_text(content: dict) -> str:
    """Flatten content to plain text for ATS scanning (mirrors the PDF)."""
    c = content.get("contact", {})
    lines = [content.get("name", c.get("name", ""))]
    lines.append(" | ".join(p for p in (c.get("address"), c.get("city"),
                                         c.get("phone"), c.get("email")) if p))
    if content.get("summary"):
        lines += ["SUMMARY", content["summary"]]
    if content.get("experience"):
        lines.append("EXPERIENCE")
        for job in content["experience"]:
            lines.append(" | ".join(p for p in (job.get("company"), job.get("location"),
                                                job.get("title"), job.get("dates")) if p))
            lines += job.get("bullets", [])
    if content.get("education"):
        lines.append("EDUCATION")
        for ed in content["education"]:
            lines.append(" | ".join(p for p in (ed.get("school"), ed.get("degree"),
                                                ed.get("detail"), ed.get("location"),
                                                ed.get("dates")) if p))
    if content.get("skills"):
        skills = content["skills"]
        lines += ["SKILLS", ", ".join(skills) if isinstance(skills, list) else str(skills)]
    return "\n".join(lines)
