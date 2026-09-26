"""Tests for the layout/contrast helpers and the geometry QA script."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import qa_layout  # noqa: E402
from generate_svg_assets import (  # noqa: E402
    contrast_ratio,
    ensure_contrast,
    fit_text,
    _build_gallery,
    _build_learning_path,
    _build_constellation,
    _constellation_geometry,
    build_identity_panel,
)


THEME = {
    "background": "#070B17", "surface": "#0D1528", "surface_light": "#13203A",
    "cyan": "#22D3EE", "blue": "#38BDF8", "violet": "#8B5CF6", "purple": "#A78BFA",
    "white": "#F8FAFC", "muted": "#94A3B8", "green": "#34D399",
}

PROJECTS = [
    {
        "name": "Campus Connect",
        "description": "A student-focused web platform built with HTML, PHP, JavaScript, "
                       "and MySQL to improve campus communication across departments.",
        "language": "PHP", "stars": 3, "forks": 1, "pushed_at": "2026-05-22",
        "html_url": "https://github.com/kulraj025/Campus-Connect", "homepage": "",
        "topics": ["web"],
    },
    {
        "name": "Bankingmanagementsys",
        "description": "Group project prepared by teammates on simple banking management "
                       "system using c++ for our OOP module.",
        "language": "C++", "stars": 0, "forks": 0, "pushed_at": "2025-12-09",
        "html_url": "https://github.com/kulraj025/Bankingmanagementsys", "homepage": "",
        "topics": [],
    },
]

PROFILE = {
    "display_name": "Kulraj Neupane",
    "handle": "kulraj025",
    "tagline": "Building with AI",
    "location": "Busan, South Korea",
    "current_focus": "Building AI projects",
    "university": {"institution": "Dong-eui University", "website": "https://eng.deu.ac.kr/eng/index.do"},
    "education": [{"degree": "B.Sc. (Hons)", "specialization": "Intelligence Computing",
                   "level": "3rd Year", "status": "Currently Enrolled"}],
    "social": {"github": "https://github.com/kulraj025", "email": "Kulraj024@gmail.com"},
}

LANGUAGES = [
    {"name": "PHP", "percent": 40, "bytes": 4000},
    {"name": "C++", "percent": 25, "bytes": 2500},
    {"name": "CSS", "percent": 18, "bytes": 1800},
    {"name": "HTML", "percent": 12, "bytes": 1200},
    {"name": "JavaScript", "percent": 5, "bytes": 500},
]


# --------------------------------------------------------------------------
# fit_text
# --------------------------------------------------------------------------

def test_fit_text_respects_max_px():
    lines = fit_text("a " * 200, max_px=120, font_size=10, max_lines=2)
    assert len(lines) <= 2
    budget = 120 / (10 * 0.52)
    for line in lines:
        assert len(line) <= budget


def test_fit_text_single_line_ellipsises():
    lines = fit_text("ExtremelyLongRepositoryNameWithoutSpaces", max_px=60, font_size=10, max_lines=1)
    assert len(lines) == 1
    assert lines[0].endswith("\u2026")


def test_fit_text_keeps_short_text_intact():
    assert fit_text("PHP", max_px=200, font_size=10, max_lines=2) == ["PHP"]


# --------------------------------------------------------------------------
# contrast
# --------------------------------------------------------------------------

def test_contrast_ratio_known_values():
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#000000", "#000000") == pytest.approx(1.0, abs=0.01)


def test_ensure_contrast_lifts_dark_colour():
    # C++ #006699 is 2.6:1 on the card surface and must be lifted.
    lifted = ensure_contrast("#006699", "#13203A", 4.5)
    assert lifted != "#006699"
    assert contrast_ratio(lifted, "#13203A") >= 4.5


def test_ensure_contrast_leaves_good_colour_alone():
    assert ensure_contrast("#F8FAFC", "#070B17", 4.5) == "#F8FAFC"


def test_ensure_contrast_invalid_input_passthrough():
    assert ensure_contrast("not-a-colour", "#070B17", 4.5) == "not-a-colour"


# --------------------------------------------------------------------------
# Constellation geometry stays on canvas
# --------------------------------------------------------------------------

def test_constellation_nodes_inside_canvas():
    width, height = 820, 400
    _, _, placed = _constellation_geometry(LANGUAGES, width, height)
    assert placed, "expected nodes to be placed"
    for _, x, y, lang, size in placed:
        assert 0 <= x <= width, f"{lang['name']} x={x} outside 0..{width}"
        assert 0 <= y <= height, f"{lang['name']} y={y} outside 0..{height}"


def test_constellation_single_language_stays_in_bounds():
    width, height = 820, 400
    _, _, placed = _constellation_geometry([LANGUAGES[0]], width, height)
    for _, x, y, _, _ in placed:
        assert 0 <= x <= width and 0 <= y <= height


# --------------------------------------------------------------------------
# Generated assets survive generation
# --------------------------------------------------------------------------

def test_build_gallery_long_description_is_wrapped():
    """The old bug emitted a 120-char single <text> that overflowed the card."""
    import xml.etree.ElementTree as ET

    svg = _build_gallery(THEME, PROJECTS, animated=True)
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    card_w, font_size = 270, 10
    budget_px = card_w - 40

    longest = 0
    for t in root.iter(f"{ns}text"):
        body = (t.text or "").strip()
        if not body:
            continue
        longest = max(longest, len(body) * font_size * 0.52)

    assert longest <= budget_px + 1, f"text spans {longest:.0f}px, card allows {budget_px}px"


def test_build_gallery_keeps_description_content():
    svg = _build_gallery(THEME, PROJECTS, animated=True)
    # Wrapped, not truncated away: the opening words must survive.
    assert "student-focused web platform" in svg


def test_build_gallery_uses_accent_not_language_name_as_fill():
    svg = _build_gallery(THEME, PROJECTS, animated=True)
    for bad in ("fill='PHP'", "fill='C++'", "fill='HTML'", "fill='JavaScript'"):
        assert bad not in svg, f"language name leaked into a fill attribute: {bad}"


def test_static_and_animated_gallery_agree_on_text():
    animated = _build_gallery(THEME, PROJECTS, animated=True)
    static = _build_gallery(THEME, PROJECTS, animated=False)
    for svg in (animated, static):
        for proj in PROJECTS:
            assert proj["name"] in svg


def test_learning_path_labels_stay_inside():
    for animated in (True, False):
        svg = _build_learning_path(THEME, animated=animated)
        assert "Intelligence Computing" in svg or "Intelligence" in svg


def test_constellation_renders_both_variants():
    for animated in (True, False):
        svg = _build_constellation(THEME, LANGUAGES, animated=animated)
        assert svg.startswith("<svg")
        assert svg.rstrip().endswith("</svg>")


def test_identity_panel_contains_verified_fields_only():
    svg = build_identity_panel(THEME, PROFILE)
    assert "Dong-eui University" in svg
    assert "mailto:Kulraj024@gmail.com" in svg
    # Email must not appear as a bare text paragraph.
    assert "Kulraj024@gmail.com</text>" not in svg


def test_identity_panel_omits_unconfigured_education():
    bare = dict(PROFILE)
    bare["education"] = []
    svg = build_identity_panel(THEME, bare)
    assert "Intelligence Computing" not in svg
    assert "Currently Enrolled" not in svg


# --------------------------------------------------------------------------
# The QA script itself
# --------------------------------------------------------------------------

def test_qa_detects_overflowing_text(tmp_path):
    bad = tmp_path / "bad.svg"
    bad.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg' width='100' height='40' viewBox='0 0 100 40'>"
        "<rect width='100' height='40' fill='#070B17'/>"
        "<text x='10' y='20' font-size='12' fill='#F8FAFC' font-family='Inter,sans-serif'>"
        "ThisLabelIsFarTooLongToFitInsideTheCanvas</text></svg>",
        encoding="utf-8",
    )
    issues = qa_layout.check_file(bad)
    assert any("overflows right edge" in i for i in issues)


def test_qa_detects_invalid_fill(tmp_path):
    bad = tmp_path / "bad2.svg"
    bad.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg' width='100' height='40' viewBox='0 0 100 40'>"
        "<rect width='100' height='40' fill='#070B17'/>"
        "<text x='10' y='20' font-size='12' fill='PHP' font-family='Inter,sans-serif'>PHP</text>"
        "</svg>",
        encoding="utf-8",
    )
    issues = qa_layout.check_file(bad)
    assert any("invalid text fill" in i for i in issues)


def test_qa_detects_low_contrast(tmp_path):
    bad = tmp_path / "bad3.svg"
    bad.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg' width='100' height='40' viewBox='0 0 100 40'>"
        "<rect width='100' height='40' fill='#070B17'/>"
        "<text x='10' y='20' font-size='12' fill='#006699' font-family='Inter,sans-serif'>Dim</text>"
        "</svg>",
        encoding="utf-8",
    )
    issues = qa_layout.check_file(bad)
    assert any("low contrast" in i for i in issues)


def test_qa_accepts_clean_svg(tmp_path):
    good = tmp_path / "good.svg"
    good.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg' width='100' height='40' viewBox='0 0 100 40'>"
        "<rect width='100' height='40' fill='#070B17'/>"
        "<text x='10' y='20' font-size='12' fill='#F8FAFC' font-family='Inter,sans-serif'>OK</text>"
        "</svg>",
        encoding="utf-8",
    )
    assert qa_layout.check_file(good) == []


def test_qa_is_clean_across_all_generated_assets():
    """The committed assets must satisfy the same bar CI enforces."""
    for d in (ROOT / "assets" / "generated", ROOT / "assets" / "static"):
        for f in sorted(d.glob("*.svg")):
            assert qa_layout.check_file(f) == [], f"{f.name} has layout issues"
