"""Tests for the layout/contrast helpers, the type scale, and the geometry QA script."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import qa_layout  # noqa: E402
import design as D  # noqa: E402
from generate_svg_assets import (  # noqa: E402
    contrast_ratio,
    ensure_contrast,
    fit_text,
    _build_orbit,
    _build_hero,
    _build_project_art,
    _lang_color,
)


THEME = {
    "background": "#070B17", "surface": "#0E1830", "surface_light": "#13213B",
    "cyan": "#22D3EE", "blue": "#38BDF8", "violet": "#8B5CF6", "purple": "#A78BFA",
    "white": "#F8FAFC", "muted": "#94A3B8", "green": "#34D399",
}

PROFILE = {
    "display_name": "Kulraj Neupane", "handle": "kulraj025",
    "location": "Busan, South Korea",
    "university": {"institution": "Dong-eui University"},
    "education": [], "social": {},
}

STATS = {"name": "Kulraj Neupane", "location": "Busan, South Korea"}

LANGUAGES = [
    {"name": "PHP", "bytes": 317306, "percent": 69.6},
    {"name": "C++", "bytes": 51479, "percent": 11.3},
    {"name": "CSS", "bytes": 48358, "percent": 10.6},
    {"name": "HTML", "bytes": 34953, "percent": 7.7},
    {"name": "JavaScript", "bytes": 3873, "percent": 0.8},
]


class TestContrast:
    def test_known_ratio(self):
        assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0, abs=0.01)

    def test_identical_colours_have_no_contrast(self):
        assert contrast_ratio("#38BDF8", "#38BDF8") == pytest.approx(1.0, abs=0.01)

    def test_invalid_colour_returns_zero(self):
        assert contrast_ratio("not-a-colour", "#000000") == 0.0

    def test_ensure_contrast_lifts_a_failing_colour(self):
        """C++ at #006699 is 2.6:1 on the canvas and must be lifted."""
        assert contrast_ratio("#006699", D.CONTRAST_BG) < 4.5
        lifted = ensure_contrast("#006699", D.CONTRAST_BG, 4.5)
        assert contrast_ratio(lifted, D.CONTRAST_BG) >= 4.5

    def test_ensure_contrast_leaves_a_passing_colour_alone(self):
        assert ensure_contrast("#F8FAFC", D.CONTRAST_BG, 4.5) == "#F8FAFC"

    def test_every_language_colour_is_readable(self):
        for lang in LANGUAGES:
            color = _lang_color(lang["name"])
            assert contrast_ratio(color, D.CONTRAST_BG) >= 4.5, \
                f"{lang['name']} resolves to {color}, which fails AA"

    def test_unknown_language_falls_back_to_cyan(self):
        assert _lang_color("Brainfuck") == D.PALETTE["cyan"]


class TestFitText:
    def test_wraps_to_fit(self):
        lines = fit_text("one two three four five six", 200, 20, max_lines=3)
        assert len(lines) > 1
        assert all(len(l) <= 200 / (20 * 0.52) for l in lines)

    def test_respects_max_lines(self):
        lines = fit_text("a b c d e f g h i j k l m n o p", 100, 20, max_lines=2)
        assert len(lines) <= 2

    def test_ellipsises_when_truncated(self):
        lines = fit_text("alpha beta gamma delta epsilon", 100, 20, max_lines=1)
        assert lines[0].endswith("\u2026")

    def test_empty_input(self):
        assert fit_text("", 200, 20) == []

    def test_no_off_by_one_overflow(self):
        """Regression: appending an ellipsis must not exceed the char budget."""
        budget = int(120 / (18 * 0.52))
        for text in ("alpha beta gamma delta epsilon zeta eta theta",
                     "x" * 200, "one two three"):
            for line in fit_text(text, 120, 18, max_lines=2):
                assert len(line) <= budget, \
                    f"{line!r} is {len(line)} chars, budget is {budget}"


class TestTypeScale:
    def test_no_generated_asset_breaks_the_floor(self):
        """The invariant that keeps the redesign from regressing.

        Glyphs in a full-width SVG scale with the viewport. The previous
        generation had 92 of 168 text elements below 13px on desktop and all
        of them illegible on a phone.
        """
        offenders = []
        for d in ("assets/generated", "assets/static"):
            for path in sorted((ROOT / d).rglob("*.svg")):
                for size in re.findall(r"font-size='([0-9.]+)'",
                                       path.read_text(encoding="utf-8")):
                    if float(size) < D.MIN_SVG_FONT_SIZE:
                        offenders.append(f"{path.name}: {size}")
        assert not offenders, f"text below the {D.MIN_SVG_FONT_SIZE}px floor: {offenders}"

    def test_every_svg_text_survives_desktop_reading(self):
        """At the floor, text must still be >= 14px when rendered on desktop."""
        assert D.MIN_SVG_FONT_SIZE * D.DESKTOP_SCALE >= 14.0

    def test_text_width_model_matches_qa_layout(self):
        """The generator and the QA check must agree on what overflows."""
        text = "KULRAJ NEUPANE"
        for size in (18, 24, 32, 100):
            assert D.text_width(text, size) == pytest.approx(
                qa_layout._text_width(ET.fromstring(
                    f"<text font-size='{size}' font-weight='400' "
                    f"font-family='sans-serif'>{text}</text>")),
                rel=0.12,
            )

    def test_fit_font_size_never_exceeds_target(self):
        assert D.fit_font_size("KULRAJ NEUPANE", 900, 100) <= 100

    def test_fit_font_size_shrinks_long_text(self):
        long_text = "A VERY LONG PROJECT NAME INDEED"
        assert (D.fit_font_size(long_text, 300, 100)
                < D.fit_font_size("Short", 300, 100))

    def test_fit_font_size_respects_floor(self):
        assert D.fit_font_size("X" * 200, 50, 100, floor=18) >= 18


class TestQaScriptCatchesRegressions:
    """The QA script has to actually fail on the things it claims to catch."""

    def _write(self, tmp_path, body):
        p = tmp_path / "bad.svg"
        p.write_text(body, encoding="utf-8")
        return p

    def test_flags_text_below_the_floor(self, tmp_path):
        p = self._write(tmp_path,
                        "<svg xmlns='http://www.w3.org/2000/svg' width='100' "
                        "height='40' viewBox='0 0 100 40'>"
                        "<text x='4' y='20' font-size='9' fill='#FFFFFF'>tiny</text>"
                        "</svg>")
        issues = qa_layout.check_file(p)
        assert any("below the" in i for i in issues), issues

    def test_flags_text_overflowing_the_canvas(self, tmp_path):
        p = self._write(tmp_path,
                        "<svg xmlns='http://www.w3.org/2000/svg' width='100' "
                        "height='40' viewBox='0 0 100 40'>"
                        "<text x='4' y='20' font-size='18' fill='#FFFFFF'>"
                        "a very long line of text that must overflow the canvas edge"
                        "</text></svg>")
        assert any("overflows right edge" in i for i in qa_layout.check_file(p))

    def test_flags_low_contrast_text(self, tmp_path):
        p = self._write(tmp_path,
                        "<svg xmlns='http://www.w3.org/2000/svg' width='200' "
                        "height='60' viewBox='0 0 200 60'>"
                        "<rect width='200' height='60' fill='#070B17'/>"
                        "<text x='4' y='30' font-size='18' fill='#1E3A5F'>dim</text>"
                        "</svg>")
        assert any("low contrast" in i for i in qa_layout.check_file(p))

    def test_flags_script_elements(self, tmp_path):
        p = self._write(tmp_path,
                        "<svg xmlns='http://www.w3.org/2000/svg' width='100' "
                        "height='40' viewBox='0 0 100 40'>"
                        "<script>alert(1)</script></svg>")
        assert any("forbidden" in i for i in qa_layout.check_file(p))

    def test_flags_external_references(self, tmp_path):
        p = self._write(tmp_path,
                        "<svg xmlns='http://www.w3.org/2000/svg' width='100' "
                        "height='40' viewBox='0 0 100 40'>"
                        "<image href='https://evil.example/x.png'/></svg>")
        assert any("external reference" in i for i in qa_layout.check_file(p))

    def test_flags_motion_budget_overrun(self, tmp_path):
        anims = "".join(
            f"<circle r='2'><animate attributeName='r' values='1;2' dur='2s' "
            f"repeatCount='indefinite'/></circle>" for _ in range(45))
        p = self._write(tmp_path,
                        "<svg xmlns='http://www.w3.org/2000/svg' width='100' "
                        f"height='40' viewBox='0 0 100 40'>{anims}</svg>")
        assert any("exceeds budget" in i for i in qa_layout.check_file(p))

    def test_flags_text_collision(self, tmp_path):
        p = self._write(tmp_path,
                        "<svg xmlns='http://www.w3.org/2000/svg' width='200' "
                        "height='80' viewBox='0 0 200 80'>"
                        "<text x='4' y='30' font-size='20' fill='#FFFFFF'>AAAA BBBB</text>"
                        "<text x='4' y='32' font-size='20' fill='#FFFFFF'>CCCC DDDD</text>"
                        "</svg>")
        assert any("text overlap" in i for i in qa_layout.check_file(p))

    def test_does_not_flag_path_animated_shapes(self, tmp_path):
        """A shape driven by animateMotion has no meaningful x/y to bounds-check."""
        p = self._write(tmp_path,
                        "<svg xmlns='http://www.w3.org/2000/svg' width='200' "
                        "height='80' viewBox='0 0 200 80'>"
                        "<circle r='16' fill='#fff'><animateMotion dur='4s' "
                        "repeatCount='indefinite' path='M0,0 H200'/></circle></svg>")
        issues = qa_layout.check_file(p)
        assert not any("escapes" in i for i in issues), issues

    def test_does_not_require_static_fallbacks_to_animate(self, tmp_path):
        p = tmp_path / "assets" / "static"
        p.mkdir(parents=True)
        f = p / "s.svg"
        f.write_text("<svg xmlns='http://www.w3.org/2000/svg' width='10' "
                     "height='10' viewBox='0 0 10 10'></svg>", encoding="utf-8")
        assert not any("no animation" in i for i in qa_layout.check_file(f))


class TestRealAssetsPass:
    def test_every_shipped_asset_is_clean(self):
        files = list((ROOT / "assets" / "generated").rglob("*.svg"))
        files += list((ROOT / "assets" / "static").rglob("*.svg"))
        assert files, "no assets found"
        problems = []
        for f in files:
            problems.extend(qa_layout.check_file(f))
        assert not problems, "\n".join(problems)

    def test_every_shipped_asset_is_valid_xml(self):
        for d in ("assets/generated", "assets/static"):
            for f in (ROOT / d).rglob("*.svg"):
                try:
                    ET.fromstring(f.read_text(encoding="utf-8"))
                except ET.ParseError as exc:
                    raise AssertionError(f"{f} is malformed: {exc}") from exc

    def test_no_asset_uses_javascript(self):
        for d in ("assets/generated", "assets/static"):
            for f in (ROOT / d).rglob("*.svg"):
                text = f.read_text(encoding="utf-8")
                assert "<script" not in text, f"{f} contains <script>"

    def test_every_asset_has_alt_text(self):
        for d in ("assets/generated", "assets/static"):
            for f in (ROOT / d).rglob("*.svg"):
                root = ET.fromstring(f.read_text(encoding="utf-8"))
                assert root.get("aria-label"), f"{f} has no aria-label"


class TestOrbitGeometry:
    def test_all_nodes_stay_inside_the_canvas(self):
        """Regression: the previous orbit used a fixed radius larger than the
        canvas half-height, putting nodes at negative y."""
        svg = _build_orbit(THEME, LANGUAGES, animated=False)
        root = ET.fromstring(svg)
        w = float(root.get("width"))
        h = float(root.get("height"))
        for el in root.iter("{http://www.w3.org/2000/svg}circle"):
            cx, cy, r = float(el.get("cx")), float(el.get("cy")), float(el.get("r"))
            assert cx - r >= -6, f"node at cx={cx} r={r} escapes left"
            assert cx + r <= w + 6, f"node at cx={cx} r={r} escapes right"
            assert cy - r >= -6, f"node at cy={cy} r={r} escapes top (was the old bug)"
            assert cy + r <= h + 6, f"node at cy={cy} r={r} escapes bottom"

    def test_orbit_handles_a_single_language(self):
        ET.fromstring(_build_orbit(THEME, [{"name": "Go", "bytes": 5, "percent": 100}],
                                   animated=False))

    def test_orbit_handles_many_languages(self):
        many = [{"name": f"L{i}", "bytes": 1000 - i, "percent": 10} for i in range(12)]
        ET.fromstring(_build_orbit(THEME, many, animated=False))

    def test_node_size_tracks_usage(self):
        """The largest language must draw the largest node."""
        svg = _build_orbit(THEME, LANGUAGES, animated=False)
        root = ET.fromstring(svg)
        radii = sorted((float(c.get("r")) for c in
                        root.iter("{http://www.w3.org/2000/svg}circle")), reverse=True)
        assert radii[0] > 60, "the dominant language node is not visually dominant"


class TestProjectArtGeometry:
    def test_art_has_no_text(self):
        """Artwork is decorative; all copy belongs in the HTML card."""
        for size in ("featured", "secondary"):
            svg = _build_project_art(THEME, {"name": "Proj", "accent": "#38BDF8"},
                                     animated=True, size=size)
            assert "<text" not in svg, f"{size} art contains text"

    def test_art_is_small_enough_to_load_quickly(self):
        svg = _build_project_art(THEME, {"name": "Proj", "accent": "#38BDF8"},
                                 animated=True, size="featured")
        assert len(svg.encode()) < 12_000, "project artwork is unexpectedly large"


class TestHeroGeometry:
    def test_hero_masthead_fits_the_canvas(self):
        svg = _build_hero(THEME, PROFILE, STATS, animated=False)
        root = ET.fromstring(svg)
        w = float(root.get("width"))
        for el in root.iter("{http://www.w3.org/2000/svg}text"):
            if "KULRAJ" in (el.text or "") and el.get("font-weight") == "800":
                size = float(el.get("font-size"))
                width = D.text_width(el.text, size, weight="800", tracking=1.2)
                assert width <= w, f"masthead is {width}px wide in a {w}px canvas"

    def test_hero_name_is_the_dominant_element(self):
        """Nothing else on the page may compete with the name."""
        svg = _build_hero(THEME, PROFILE, STATS, animated=False)
        sizes = [float(s) for s in re.findall(r"font-size='([0-9.]+)'", svg)]
        assert max(sizes) >= 60
        assert max(sizes) >= sorted(sizes)[-2] * 1.8, \
            "the masthead does not clearly dominate the other type"
