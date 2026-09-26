"""Tests for the structural validity of the generated README HTML.

GitHub renders README HTML through a sanitizer and then a real browser. Invalid
markup does not error there — it is silently reflowed, so a layout can be wrong
with nothing to report it. These tests assert the structure actually survives.
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import render_readme as R  # noqa: E402

THEME = {"background": "#070B17"}
STATS = {"public_repos": 10, "followers": 1, "total_stars": 2, "total_forks": 0,
         "most_used_language": "PHP", "refresh_date": "2026-09-26"}
SOCIAL = {"github": "https://github.com/kulraj025",
          "email": "Kulraj024@gmail.com",
          "_university": {"website": "https://eng.deu.ac.kr/eng/index.do"}}
PROFILE = {"bio": "Builds things.", "location": "Busan, South Korea",
           "university": {"institution": "Dong-eui University"},
           "education": [{"degree": "B.Sc. (Hons)",
                          "specialization": "Intelligence Computing",
                          "level": "3rd Year",
                          "institution": "Dong-eui University",
                          "status": "Currently Enrolled"}]}


class Structure(HTMLParser):
    """Minimal nesting validator — mirrors scripts/qa_structure.py."""

    VOID = {"img", "br", "hr", "meta", "link", "input", "source"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.problems: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        if tag in ("tr", "td", "th") and not any(t == "table" for t in self.stack):
            self.problems.append(f"<{tag}> outside a table")
        if tag == "tr":
            parent = self.stack[-1] if self.stack else ""
            if parent not in ("table", "tbody", "thead", "tfoot"):
                self.problems.append(f"<tr> inside <{parent}>")
        if tag in ("p", "div"):
            if "p" in self.stack:
                self.problems.append(f"<{tag}> inside <p>")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if tag in self.stack:
            i = len(self.stack) - 1 - self.stack[::-1].index(tag)
            for u in self.stack[i + 1:]:
                self.problems.append(f"<{u}> unclosed before </{tag}>")
            del self.stack[i:]
        else:
            self.problems.append(f"</{tag}> unmatched")


def problems_in(html: str) -> list[str]:
    s = Structure()
    s.feed(html)
    s.close()
    for u in s.stack:
        s.problems.append(f"<{u}> never closed")
    return s.problems


ALL_SECTIONS = {
    "identity": lambda: R.build_identity_section(THEME, PROFILE, STATS),
    "technology": lambda: R.build_technology_section(
        THEME, [{"name": "PHP", "bytes": 317306, "percent": 69.6}]),
    "projects": lambda: R.build_projects_section(
        [{"name": "campus_connect_x_v2", "description": "A student platform",
          "language": "PHP", "stars": 0, "forks": 0, "updated": "2026-06-08",
          "url": "https://github.com/kulraj025/campus_connect_x_v2",
          "homepage": "https://kulraj025.github.io/campus_connect_x_v2/"}],
        THEME),
    "activity": lambda: R.build_activity_section(THEME, STATS, PROFILE),
    "contact": lambda: R.build_contact_section(SOCIAL, THEME, STATS),
}


@pytest.mark.parametrize("name", sorted(ALL_SECTIONS))
def test_every_section_is_structurally_valid(name):
    assert problems_in(ALL_SECTIONS[name]()) == []


def test_identity_panel_rows_live_inside_a_table():
    """Regression: the label/value rows were bare <tr> inside a <td>.

    A row must be inside a table. Emitted directly into a cell, the browser
    hoists it into a table of its own and the right-hand column of the identity
    panel stops being a column — with no error anywhere.
    """
    body = ALL_SECTIONS["identity"]()
    assert "<tr><td style=\"padding:10px 18px 10px 0;" in body
    # every <tr> must be preceded by a table opening or a sibling row
    for m in re.finditer(r"<tr>", body):
        before = body[:m.start()]
        assert before.count("<table") > before.count("</table>"), (
            "<tr> appears with no open <table> before it")


def test_no_script_style_or_iframe_anywhere():
    for build in ALL_SECTIONS.values():
        body = build()
        for tag in ("<script", "<style", "<iframe", "<object", "<embed"):
            assert tag not in body


def test_every_image_has_alt_text_and_a_resolvable_src():
    for build in ALL_SECTIONS.values():
        for tag in re.findall(r"<img\b[^>]*>", build()):
            assert "alt=" in tag, tag
            src = re.search(r'src="([^"]+)"', tag).group(1)
            assert src.strip()
            assert (Path(__file__).resolve().parent.parent / src).is_file(), src


def test_eyebrow_is_a_single_line_not_scattered_fragments():
    """One marker line per section, not four 12px fragments plus a note line."""
    import design as D

    html = D.eyebrow("01", "IDENTITY", "Verified from repository configuration")
    assert html.count("<p") == 1, "eyebrow must occupy exactly one paragraph"
    assert html.count("</p>") == 1
    assert "01" in html and "IDENTITY" in html
    assert "Verified from repository configuration" in html


def test_buttons_are_large_enough_to_read_and_tap():
    body = ALL_SECTIONS["contact"]()
    sizes = {int(m) for m in re.findall(r"font-size:(\d+)px;font-weight:600;"
                                         r"letter-spacing:1\.2px", body)}
    assert sizes, "no button found"
    assert min(sizes) >= 15, f"button label only {min(sizes)}px"
    # 16px vertical padding + 1.2 * 15px line box > 44px touch target
    for pad in {int(m) for m in re.findall(r"padding:(\d+)px 28px", body)}:
        assert pad * 2 + round(15 * 1.2) >= 44


def test_no_metric_or_fact_is_repeated_across_sections():
    """The brief forbids restating the same fact in two sections."""
    identity = ALL_SECTIONS["identity"]()
    activity = ALL_SECTIONS["activity"]()
    # the degree line is stated once, in the identity panel
    assert "Intelligence Computing" in identity
    assert "Intelligence Computing" not in activity
    assert "Dong-eui University" not in activity
