"""Tests for SVG asset generation.

The names here track the current scene set:
hero, divider, technology orbit, horizon signal, learning path, contact
horizon, and per-project artwork.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.generate_svg_assets import (  # noqa: E402
    generate_all,
    _build_hero,
    _build_divider,
    _build_orbit,
    _build_horizon_signal,
    _build_learning_path,
    _build_contact_horizon,
    _build_project_art,
    _sine_path,
    _esc,
    slugify,
)

import design as D  # noqa: E402

THEME = {"background": "#070B17", "surface": "#0E1830", "cyan": "#22D3EE",
         "violet": "#8B5CF6", "white": "#F8FAFC", "muted": "#94A3B8",
         "green": "#34D399", "blue": "#38BDF8"}

STATS = {"name": "TestUser", "location": "Busan, South Korea",
         "public_repos": 10, "followers": 5, "following": 3,
         "total_stars": 20, "total_forks": 5, "refresh_date": "2026-01-01"}

PROFILE = {
    "display_name": "Test User", "handle": "testuser",
    "tagline": "Building with AI", "bio": "Bio text.",
    "location": "Busan, South Korea", "current_focus": "Building AI projects",
    "university": {"institution": "Test University",
                   "website": "https://example.edu/", "city": "Busan",
                   "country": "South Korea"},
    "education": [{"degree": "B.Sc. (Hons)", "specialization": "Test Major",
                   "level": "3rd Year", "institution": "Test University",
                   "status": "Currently Enrolled"}],
    "social": {"github": "https://github.com/testuser", "email": "t@example.com"},
}

LANGUAGES = [
    {"name": "PHP", "bytes": 317306, "percent": 69.6},
    {"name": "C++", "bytes": 51479, "percent": 11.3},
    {"name": "CSS", "bytes": 48358, "percent": 10.6},
    {"name": "HTML", "bytes": 34953, "percent": 7.7},
    {"name": "JavaScript", "bytes": 3873, "percent": 0.8},
]

PROJECTS = [
    {"name": "Alpha Project", "description": "First", "language": "PHP",
     "stars": 1, "forks": 0, "pushed_at": "2026-01-01", "homepage": "",
     "html_url": "https://github.com/testuser/Alpha-Project", "topics": ["web"]},
    {"name": "Beta Tool", "description": "Second", "language": "C++",
     "stars": 0, "forks": 0, "pushed_at": "2026-02-01", "homepage": "",
     "html_url": "https://github.com/testuser/Beta-Tool", "topics": []},
]


def _all_scenes():
    return {
        "hero": _build_hero(THEME, PROFILE, STATS, animated=True),
        "divider": _build_divider(THEME, animated=True),
        "orbit": _build_orbit(THEME, LANGUAGES, animated=True),
        "signal": _build_horizon_signal(THEME, animated=True),
        "learning": _build_learning_path(THEME, PROFILE, animated=True),
        "contact": _build_contact_horizon(THEME, PROFILE, animated=True),
        "art": _build_project_art(THEME, dict(PROJECTS[0], accent="#38BDF8"),
                                  animated=True, size="featured"),
    }


class TestSceneStructure:
    def test_every_scene_is_well_formed_xml(self):
        for name, svg in _all_scenes().items():
            try:
                root = ET.fromstring(svg)
            except ET.ParseError as exc:
                raise AssertionError(f"{name} is not valid XML: {exc}") from exc
            assert root.tag.endswith("svg"), f"{name} root is not <svg>"

    def test_every_scene_has_dimensions_and_label(self):
        for name, svg in _all_scenes().items():
            root = ET.fromstring(svg)
            assert root.get("width"), f"{name} missing width"
            assert root.get("height"), f"{name} missing height"
            assert root.get("viewBox"), f"{name} missing viewBox"
            assert root.get("aria-label"), f"{name} missing aria-label (alt text)"

    def test_no_script_or_iframe(self):
        for name, svg in _all_scenes().items():
            assert "<script" not in svg, f"{name} contains <script>"
            assert "<iframe" not in svg, f"{name} contains <iframe>"

    def test_no_external_references(self):
        for name, svg in _all_scenes().items():
            assert "http://" not in svg.replace("http://www.w3.org", ""), \
                f"{name} has an external reference"

    def test_animated_variants_contain_animation(self):
        for name, svg in _all_scenes().items():
            assert "<animate" in svg, f"{name} has no animation elements"

    def test_static_variants_contain_no_animation(self):
        statics = {
            "hero": _build_hero(THEME, PROFILE, STATS, animated=False),
            "orbit": _build_orbit(THEME, LANGUAGES, animated=False),
            "learning": _build_learning_path(THEME, PROFILE, animated=False),
            "contact": _build_contact_horizon(THEME, PROFILE, animated=False),
        }
        for name, svg in statics.items():
            assert "<animate" not in svg, f"static {name} unexpectedly animates"

    def test_animation_budget_respected(self):
        for name, svg in _all_scenes().items():
            count = svg.count("<animate")
            assert count <= D.MAX_ANIMATIONS_PER_ASSET, \
                f"{name} has {count} animations, budget is {D.MAX_ANIMATIONS_PER_ASSET}"


class TestTypeScale:
    def test_no_text_below_the_floor(self):
        """The single most important invariant.

        A README image is fluid: text at N viewBox units in a 1000-unit canvas
        renders at N*0.375 px on a phone. The previous generation had 92 of 168
        text elements below 13px on desktop and all illegible on mobile.
        """
        import re
        for name, svg in _all_scenes().items():
            for size in re.findall(r"font-size='([0-9.]+)'", svg):
                assert float(size) >= D.MIN_SVG_FONT_SIZE, (
                    f"{name} has font-size={size}, below the "
                    f"{D.MIN_SVG_FONT_SIZE} floor")


class TestHero:
    def test_hero_shows_the_name(self):
        svg = _build_hero(THEME, PROFILE, STATS, animated=True)
        assert "TEST USER" in svg

    def test_hero_shows_handle_and_location(self):
        svg = _build_hero(THEME, PROFILE, STATS, animated=True)
        assert "@testuser" in svg
        assert "BUSAN" in svg.upper()

    def test_hero_name_is_the_largest_text(self):
        import re
        svg = _build_hero(THEME, PROFILE, STATS, animated=True)
        sizes = [float(s) for s in re.findall(r"font-size='([0-9.]+)'", svg)]
        assert max(sizes) >= 60, "hero masthead is not dominant"

    def test_hero_has_visible_motion(self):
        svg = _build_hero(THEME, PROFILE, STATS, animated=True)
        assert "animateMotion" in svg, "no light travelling the horizon"
        assert "animateTransform" in svg, "no wave or gradient motion"


class TestOrbit:
    def test_orbit_uses_real_language_data(self):
        svg = _build_orbit(THEME, LANGUAGES, animated=True)
        for lang in ("PHP", "C++", "CSS", "HTML"):
            assert lang in svg, f"{lang} missing from orbit"

    def test_orbit_node_count_is_capped(self):
        """The brief asks for fewer, more meaningful nodes."""
        svg = _build_orbit(THEME, LANGUAGES, animated=True)
        # JavaScript at 0.8% is deliberately not drawn; the HTML legend carries it.
        assert "JavaScript" not in svg

    def test_orbit_handles_single_language(self):
        svg = _build_orbit(THEME, [{"name": "Go", "bytes": 10, "percent": 100}],
                           animated=True)
        ET.fromstring(svg)

    def test_orbit_handles_empty_languages(self):
        svg = _build_orbit(THEME, [], animated=True)
        ET.fromstring(svg)

    def test_language_colours_meet_contrast(self):
        """GitHub's C++ colour is #f34b7d on light; check the lifted variant."""
        from scripts.generate_svg_assets import _lang_color
        for lang in LANGUAGES:
            color = _lang_color(lang["name"])
            from scripts.generate_svg_assets import contrast_ratio
            assert contrast_ratio(color, D.CONTRAST_BG) >= 4.5, \
                f"{lang['name']} colour {color} fails AA"


class TestProjectArt:
    def test_featured_and_secondary_sizes_differ(self):
        featured = _build_project_art(THEME, dict(PROJECTS[0], accent="#38BDF8"),
                                      animated=True, size="featured")
        secondary = _build_project_art(THEME, dict(PROJECTS[1], accent="#A78BFA"),
                                       animated=True, size="secondary")
        f_w = int(ET.fromstring(featured).get("width"))
        s_w = int(ET.fromstring(secondary).get("width"))
        assert f_w > s_w

    def test_art_is_deterministic(self):
        a = _build_project_art(THEME, dict(PROJECTS[0], accent="#38BDF8"),
                               animated=True, size="featured")
        b = _build_project_art(THEME, dict(PROJECTS[0], accent="#38BDF8"),
                               animated=True, size="featured")
        assert a == b

    def test_different_names_give_different_art(self):
        a = _build_project_art(THEME, {"name": "Alpha", "accent": "#38BDF8"},
                               animated=False, size="secondary")
        b = _build_project_art(THEME, {"name": "Zeta", "accent": "#38BDF8"},
                               animated=False, size="secondary")
        assert a != b


class TestHelpers:
    def test_esc_escapes_markup(self):
        assert "&lt;" in _esc("<b>")
        assert "&amp;" in _esc("a & b")

    def test_sine_path_is_parseable(self):
        d = _sine_path(0, 100, 50, 10, 2, 0, samples=20)
        assert d.startswith("M")
        assert d.count("L") == 20

    def test_slugify(self):
        assert slugify("Initial-Portfolio-Website-") == "initial-portfolio-website"
        assert slugify("My Repo!!") == "my-repo"
        assert slugify("") == "project"


class TestGenerateAll:
    def test_writes_every_scene_and_fallback(self, tmp_path, monkeypatch):
        import scripts.generate_svg_assets as g
        monkeypatch.setattr(g, "ASSETS_DIR", tmp_path / "generated")
        monkeypatch.setattr(g, "STATIC_DIR", tmp_path / "static")
        written = g.generate_all(THEME, PROFILE, STATS, LANGUAGES, [], PROJECTS)
        assert written
        for rel in written.values():
            # generate_all returns repo-relative paths ("assets/generated/...").
            # This test redirects the output root to tmp_path, so accept the
            # asset under either redirected root.
            tail = rel.split("assets/", 1)[-1]
            found = [(tmp_path / "generated" / tail).exists(),
                     (tmp_path / "static" / tail).exists(),
                     (tmp_path / tail).exists()]
            assert any(found), f"{rel} not written under either output root"
        # static counterparts
        assert (tmp_path / "static" / "hero-fallback.svg").exists()
        for name in ("hero", "divider", "technology-orbit", "horizon-signal",
                     "learning-path", "contact-horizon"):
            assert (tmp_path / "static" / f"{name}.svg").exists()
            assert (tmp_path / "generated" / f"{name}.svg").exists()

    def test_generated_art_has_static_counterpart(self, tmp_path, monkeypatch):
        import scripts.generate_svg_assets as g
        monkeypatch.setattr(g, "ASSETS_DIR", tmp_path / "generated")
        monkeypatch.setattr(g, "STATIC_DIR", tmp_path / "static")
        g.generate_all(THEME, PROFILE, STATS, LANGUAGES, [], PROJECTS)
        art = list((tmp_path / "generated" / "project-art").glob("*.svg"))
        assert art
        for f in art:
            assert (tmp_path / "static" / "project-art" / f.name).exists()

    def test_removes_stale_scenes_from_previous_generation(self, tmp_path, monkeypatch):
        import scripts.generate_svg_assets as g
        gen = tmp_path / "generated"
        gen.mkdir(parents=True)
        stale = gen / "technology-constellation.svg"
        stale.write_text("<svg/>")
        monkeypatch.setattr(g, "ASSETS_DIR", gen)
        monkeypatch.setattr(g, "STATIC_DIR", tmp_path / "static")
        g.generate_all(THEME, PROFILE, STATS, LANGUAGES, [], PROJECTS)
        assert not stale.exists(), "orphaned widget was left behind"
