"""Tests for README template rendering."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.render_readme import render_template, _MARKER


TEMPLATE_WITH_MARKERS = """\\
<!-- GENERATED:HERO:START -->
placeholder-hero
<!-- GENERATED:HERO:END -->

---

<!-- GENERATED:PROJECTS:START -->
placeholder-projects
<!-- GENERATED:PROJECTS:END -->
"""


def test_render_replaces_markers():
    sections = {"HERO": "<p>Hero content</p>", "PROJECTS": "<p>Projects</p>"}
    result = render_template(TEMPLATE_WITH_MARKERS, sections)
    assert "<p>Hero content</p>" in result
    assert "<p>Projects</p>" in result
    assert "placeholder-hero" not in result
    assert "placeholder-projects" not in result


def test_render_preserves_non_marker_content():
    template = "<!-- GENERATED:HERO:START -->\\nold\\n<!-- GENERATED:HERO:END -->\\n\\n---\\n\\nEnd"
    sections = {"HERO": "new"}
    result = render_template(template, sections)
    assert "End" in result
    assert "new" in result
    assert "old" not in result


def test_render_missing_section_replaces_with_empty():
    template = "<!-- GENERATED:HERO:START -->\\nold\\n<!-- GENERATED:HERO:END -->"
    sections = {"PROJECTS": "new"}
    result = render_template(template, sections)
    assert "old" not in result


def test_marker_regex_matches():
    template = "<!-- GENERATED:TEST:START -->x<!-- GENERATED:TEST:END -->"
    matches = _MARKER.findall(template)
    assert len(matches) == 1
    assert matches[0][0] == "TEST"
