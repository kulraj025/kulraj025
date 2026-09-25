"""Tests for SVG asset generation."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.generate_svg_assets import (
    generate_all, build_hero, build_identity_card,
    build_technology_constellation, build_activity_dashboard,
    build_project_gallery, _svg_header, _gradient_defs,
    _build_grid, _sine_wave_path, _esc,
)


THEME = {"background": "#070B17", "surface": "#0D1528", "cyan": "#22D3EE",
         "violet": "#8B5CF6", "white": "#F8FAFC", "muted": "#94A3B8",
         "green": "#34D399", "blue": "#38BDF8"}

STATS = {"name": "TestUser", "location": "Busan, South Korea",
         "public_repos": 10, "followers": 5, "following": 3,
         "total_stars": 20, "total_forks": 5, "refresh_date": "2026-01-01"}

PROFILE = {"display_name": "Test User", "tagline": "Developer",
           "location": "Busan, South Korea", "current_focus": "AI",
           "university": {"institution": "Test University", "website": "https://test.edu"},
           "social": {"github": "https://github.com/testuser"}}


def test_svg_header_well_formed():
    svg = _svg_header(100, 100, "0 0 100 100", "Test label")
    assert svg.startswith("<svg")


def test_svg_header_escapes_apostrophe():
    escaped = _svg_header(100, 100, "0 0 100 100", "O'Brien")
    assert "Brian" not in escaped
    assert "Brien" in escaped or "O&apos;Brien" in escaped


def test_hero_generates_valid_svg():
    svg = build_hero(THEME, STATS, animated=True)
    ET.fromstring(svg)


def test_hero_fallback_generates_valid_svg():
    svg = build_hero(THEME, STATS, animated=False)
    ET.fromstring(svg)


def test_hero_has_animated_elements():
    svg = build_hero(THEME, STATS, animated=True)
    assert "<animate" in svg


def test_hero_no_animated_elements_when_disabled():
    svg = build_hero(THEME, STATS, animated=False)
    assert "<animate" not in svg


def test_identity_card_valid():
    svg = build_identity_card(THEME, PROFILE)
    ET.fromstring(svg)


def test_technology_constellation_valid():
    langs = [{"name": "Python", "percent": 50.0}, {"name": "JavaScript", "percent": 30.0}]
    svg = build_technology_constellation(THEME, langs)
    ET.fromstring(svg)


def test_technology_constellation_empty():
    svg = build_technology_constellation(THEME, [])
    ET.fromstring(svg)


def test_activity_dashboard_valid():
    svg = build_activity_dashboard(THEME, STATS, [])
    ET.fromstring(svg)


def test_project_gallery_valid():
    projects = [{"name": "proj1", "description": "test", "language": "Python",
                 "stars": 5, "forks": 2, "pushed_at": "2025-09-01",
                 "html_url": "https://github.com/test/proj1", "topics": [],
                 "homepage": "https://example.com", "stargazers_count": 5,
                 "forks_count": 2}]
    svg = build_project_gallery(THEME, projects)
    ET.fromstring(svg)


def test_project_gallery_empty():
    svg = build_project_gallery(THEME, [])
    assert "No featured projects" in svg


def test_sine_wave_path_returns_string():
    path = _sine_wave_path(100, 50, 10, 2.5, 0)
    assert path.startswith("M")
    assert "L" in path


def test_generate_all_creates_files(tmp_path, monkeypatch):
    """Test with a temporary output directory to avoid overwriting real assets."""
    monkeypatch.setattr("scripts.generate_svg_assets.ASSETS_DIR", tmp_path / "generated")
    monkeypatch.setattr("scripts.generate_svg_assets.STATIC_DIR", tmp_path / "static")
    written = generate_all(THEME, PROFILE, STATS, [], [], [])
    assert len(written) >= 14


def test_esc_escapes_apostrophe():
    result = _esc("it's")
    assert "it" in result and "s" in result
    assert "'" not in result  # apostrophe should be escaped


def test_grid_generates_lines():
    grid = _build_grid(100, 100, THEME)
    assert "<line" in grid
