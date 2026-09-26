"""Tests for README rendering.

These cover the architectural rule of the rebuild: information-bearing text is
emitted as native HTML, never inside a full-width SVG, because a README image is
fluid and its glyphs shrink with the viewport.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.render_readme import (  # noqa: E402
    render_template, build_hero_section, build_identity_section,
    build_technology_section, build_projects_section, build_activity_section,
    build_contact_section, _button, divider,
)
import design as D  # noqa: E402

THEME = {"background": "#070B17"}

STATS = {"public_repos": 10, "followers": 5, "total_stars": 20,
         "total_forks": 5, "most_used_language": "PHP",
         "refresh_date": "2026-09-26"}

PROFILE = {
    "display_name": "Kulraj Neupane", "handle": "kulraj025",
    "bio": "I build useful digital experiences.",
    "location": "Busan, South Korea",
    "university": {"institution": "Dong-eui University",
                   "website": "https://eng.deu.ac.kr/eng/index.do"},
    "education": [{"degree": "B.Sc. (Hons)", "specialization": "Intelligence Computing",
                   "level": "3rd Year · 6th Semester",
                   "institution": "Dong-eui University",
                   "status": "Currently Enrolled"}],
    "social": {"github": "https://github.com/kulraj025",
               "email": "Kulraj024@gmail.com"},
}

SOCIAL = {"github": "https://github.com/kulraj025",
          "email": "Kulraj024@gmail.com",
          "_university": {"website": "https://eng.deu.ac.kr/eng/index.do"}}

LANGUAGES = [
    {"name": "PHP", "bytes": 317306, "percent": 69.6},
    {"name": "C++", "bytes": 51479, "percent": 11.3},
    {"name": "JavaScript", "bytes": 3873, "percent": 0.8},
]

PROJECTS = [
    {"name": "Dynamic-Cv", "description": "Dynamic resume", "language": "PHP",
     "stars": 1, "forks": 0, "pushed_at": "2026-05-22",
     "homepage": "https://kulraj025.github.io/Dynamic-Cv/",
     "html_url": "https://github.com/kulraj025/Dynamic-Cv", "topics": ["cv"],
     "accent": "#38BDF8"},
    {"name": "campus_connect_x_v2", "description": "Campus platform", "language": "PHP",
     "stars": 0, "forks": 0, "pushed_at": "2026-06-08", "homepage": "",
     "html_url": "https://github.com/kulraj025/campus_connect_x_v2", "topics": [],
     "accent": "#A78BFA"},
    {"name": "Bankingmanagementsys", "description": "Banking system", "language": "C++",
     "stars": 1, "forks": 0, "pushed_at": "2025-12-09", "homepage": "",
     "html_url": "https://github.com/kulraj025/Bankingmanagementsys", "topics": [],
     "accent": "#34D399"},
    {"name": "Extra-Repo", "description": "Fourth", "language": "PHP",
     "stars": 0, "forks": 0, "pushed_at": "2026-01-01", "homepage": "",
     "html_url": "https://github.com/kulraj025/Extra-Repo", "topics": [],
     "accent": "#F0A868"},
]


class TestRenderTemplate:
    def test_replaces_markers(self):
        template = ("<!-- GENERATED:HERO:START -->\nold\n"
                    "<!-- GENERATED:HERO:END -->\n")
        out = render_template(template, {"HERO": "<p>new</p>"})
        assert "<p>new</p>" in out and "old" not in out

    def test_preserves_surrounding_content(self):
        template = "before\n<!-- GENERATED:HERO:START -->\nold\n<!-- GENERATED:HERO:END -->\nafter"
        out = render_template(template, {"HERO": "new"})
        assert "before" in out and "after" in out

    def test_raises_on_missing_marker(self):
        try:
            render_template("no markers here", {"HERO": "x"})
        except ValueError:
            return
        raise AssertionError("expected ValueError for missing markers")

    def test_published_readme_has_no_template_scaffolding(self):
        """README.md is the filled copy of templates/README.template.md.

        The invariant that matters is that the published page carries no
        scaffolding: no unfilled slot, no generator scene marker. A reader
        should never see `{{WORK_ROWS}}`.
        """
        import re

        root = Path(__file__).resolve().parent.parent
        readme = (root / "README.md").read_text(encoding="utf-8")
        assert "{{" not in readme, "README.md still contains {{FIELD}} scaffolding"
        assert not re.search(r"<!--\s*GENERATED:", readme), (
            "README.md still contains generator scene markers"
        )


class TestTextIsNativeHtml:
    def test_no_svg_carries_body_copy(self):
        """Key architectural invariant.

        Every value a reader must read has to be HTML, because glyphs inside a
        full-width SVG shrink below legibility on a phone.
        """
        for name, body in (
            ("identity", build_identity_section(THEME, PROFILE, STATS)),
            ("technology", build_technology_section(THEME, LANGUAGES)),
            ("projects", build_projects_section(PROJECTS, THEME)),
            ("activity", build_activity_section(THEME, STATS, PROFILE)),
        ):
            for m in re.finditer(r"<img[^>]*alt=\"([^\"]*)\"", body):
                alt = m.group(1)
                assert " · " not in alt, f"{name} image alt packs data into SVG: {alt!r}"

    def test_identity_values_are_readable_html(self):
        body = build_identity_section(THEME, PROFILE, STATS)
        assert "Intelligence Computing" in body
        assert "Busan, South Korea" in body
        assert "Machine learning" in body
        # Values, not labels, are the large type.
        assert "font-size:16px" in body

    def test_project_description_is_html_text(self):
        body = build_projects_section(PROJECTS, THEME)
        assert "Dynamic resume" in body
        assert "Banking system" in body


class TestButtons:
    def test_button_exceeds_44px_touch_target(self):
        html = _button("VIEW GITHUB", "https://github.com/kulraj025")
        m = re.search(r"padding:(\d+)px (\d+)px", html)
        assert m, "button has no padding"
        vertical, horizontal = int(m.group(1)), int(m.group(2))
        assert vertical * 2 + 16 >= 44, f"touch target too small: {vertical * 2 + 16}px"

    def test_button_is_obviously_a_link(self):
        html = _button("VIEW GITHUB", "https://github.com/kulraj025", primary=True)
        assert "border:1px solid" in html
        assert "text-decoration:none" in html

    def test_button_escapes_href(self):
        html = _button("X", 'https://e.com/"onmouseover="alert(1)')
        assert 'onmouseover="alert' not in html

    def test_identity_includes_all_three_actions(self):
        body = build_identity_section(THEME, PROFILE, STATS)
        assert "VIEW GITHUB" in body
        assert "UNIVERSITY" in body
        assert "EMAIL ME" in body

    def test_email_uses_mailto(self):
        body = build_identity_section(THEME, PROFILE, STATS)
        assert "mailto:Kulraj024@gmail.com" in body


class TestProjects:
    def test_live_demo_only_with_homepage(self):
        body = build_projects_section(PROJECTS, THEME)
        # Dynamic-Cv has a homepage -> two buttons
        assert "LIVE DEMO" in body
        # The two without one must not get a demo button
        assert body.count("LIVE DEMO") == 1, "a LIVE DEMO button appeared without a homepage"

    def test_one_featured_and_two_secondary(self):
        body = build_projects_section(PROJECTS, THEME)
        assert "Dynamic-Cv" in body
        assert "More work" in body, "the fourth project should be a compact link, not a card"
        assert "Extra-Repo" in body

    def test_each_project_shows_required_metadata(self):
        body = build_projects_section(PROJECTS, THEME)
        assert "★" in body and "⑂" in body and "updated" in body

    def test_projects_section_empty_without_projects(self):
        assert build_projects_section([], THEME) == ""


class TestTechnologySection:
    def test_lists_every_detected_language(self):
        body = build_technology_section(THEME, LANGUAGES)
        for lang in LANGUAGES:
            assert lang["name"] in body, f"{lang['name']} missing from legend"

    def test_includes_real_percentages(self):
        body = build_technology_section(THEME, LANGUAGES)
        assert "69.6%" in body

    def test_labels_data_as_detected_not_expertise(self):
        body = build_technology_section(THEME, LANGUAGES)
        assert "Detected from public repositories" in body
        assert "expertise" not in body.lower()


class TestActivitySection:
    def test_shows_the_four_numeric_metrics(self):
        body = build_activity_section(THEME, STATS, PROFILE)
        for label in ("REPOSITORIES", "FOLLOWERS", "STARS", "FORKS"):
            assert label in body, f"{label} missing"

    def test_main_language_reads_as_its_own_line(self):
        """A word is not a number: it must not become a fifth metric column.

        Five 20%-wide columns forced the labels to wrap on a phone, which
        knocked the big values out of baseline alignment.
        """
        body = build_activity_section(THEME, STATS, PROFILE)
        assert "MOST DETECTED LANGUAGE" in body
        assert ">PHP<" in body
        assert body.count('width="25%"') == 4

    def test_metric_labels_never_wrap(self):
        body = build_activity_section(THEME, STATS, PROFILE)
        assert "white-space:nowrap" in body

    def test_metrics_are_large(self):
        """Values must be visually dominant over their labels."""
        body = build_activity_section(THEME, STATS, PROFILE)
        value = int(re.search(r"font-size:(\d+)px;font-weight:700;color:#", body).group(1))
        label = int(re.search(r"font-size:(\d+)px;font-weight:600;letter-spacing:1\.2px",
                              body).group(1))
        assert value >= 28, f"metric value only {value}px"
        assert value >= label * 2, "metric values must dominate their labels"

    def test_learning_milestones_are_stated(self):
        """The learning path is a graphic; the words that explain it are HTML."""
        body = build_activity_section(THEME, STATS, PROFILE)
        assert "learning-path.svg" in body
        alt = re.search(r'learning-path\.svg" width="100%" alt="([^"]*)"', body).group(1)
        for phrase in ("currently enrolled", "building AI projects",
                       "learning machine learning"):
            assert phrase in alt, f"{phrase!r} not stated"

    def test_does_not_repeat_the_identity_education_line(self):
        """The brief forbids repeating the same fact in two sections.

        The degree line is stated once, at readable size, in the identity
        panel. Repeating it as small caption text under the metrics was noise.
        """
        body = build_activity_section(THEME, STATS, PROFILE)
        assert "6th Semester" not in body
        assert "Dong-eui University" not in body


class TestHeroAndContact:
    def test_hero_uses_animation_and_has_alt_text(self):
        body = build_hero_section()
        assert "assets/generated/hero.svg" in body
        assert 'alt="' in body and 'alt=""' not in body

    def test_contact_has_real_buttons_and_refresh_stamp(self):
        body = build_contact_section(SOCIAL, THEME, STATS)
        assert "mailto:Kulraj024@gmail.com" in body
        assert "2026-09-26" in body

    def test_no_empty_social_links(self):
        body = build_contact_section({"github": "https://github.com/kulraj025"},
                                     THEME, STATS)
        assert 'href=""' not in body


class TestDivider:
    def test_divider_is_an_image_not_a_markdown_rule(self):
        assert "divider.svg" in divider()
        assert "---" not in divider()
