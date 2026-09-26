"""Tests for the generated Stats, Now and Work sections.

These are deliberately offline. A test that calls the GitHub API can fail on a
rate limit or a network blip, and a test that fails for reasons unrelated to the
code trains everyone to ignore it -- the same lesson as the crop check that
passed locally and failed in CI because it shelled out to ImageMagick. So the
network-dependent staleness check lives in the workflow, where a fresh cache and
a rate-limit budget exist, and everything here works from the committed files.

The behaviour worth locking down is in `TestLiveBadgeIsConditional`: a project
with no deployment must not get a Live button. That is the entire reason the
Work section is generated instead of typed.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_readme  # noqa: E402
import render_stats  # noqa: E402
from metrics import load_config  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")
SVG_NS = "{http://www.w3.org/2000/svg}"


def section(name: str) -> str:
    """The body of one '## Name' section, up to the next heading."""
    m = re.search(rf"^## {name}\s*$(.*?)(?=^## |\Z)", README, re.S | re.M)
    assert m, f"no '## {name}' section"
    return m.group(1)


def featured() -> list[dict]:
    return load_config()["projects"]["featured"]


# --------------------------------------------------------------------------- stats


class TestStats:
    def test_title_is_exactly_stats(self):
        assert "\n## Stats\n" in README
        assert "## Proof" not in README, "the section was called 'Proof' in an earlier draft"
        assert not re.search(r"^## \d", README, re.M), "sections must not be numbered"

    def test_first_row_is_stats_beside_languages(self):
        first = section("Stats").split("<tr>")[1]
        assert "assets/stats.svg" in first
        assert "assets/langs.svg" in first
        assert first.count("<td") == 2, "row 1 must be exactly two cells"

    def test_streak_is_centred_on_its_own_row(self):
        rows = section("Stats").split("<tr>")[1:]
        streak_rows = [r for r in rows if "streak-stats" in r]
        assert len(streak_rows) == 1, "expected exactly one streak row"
        row = streak_rows[0]
        assert 'colspan="2"' in row
        assert "align=\"center\"" in row
        assert "max-width:560px" in row

    def test_trophy_row_is_only_present_with_an_award_behind_it(self):
        """An empty trophy card looks like a broken card, so the row is conditional.

        The check is against the committed card rather than the API: the README
        and the SVG have to agree, and a build that rendered the row while
        writing an empty card is exactly the bug worth catching.
        """
        row = [r for r in section("Stats").split("<tr>") if "trophies.svg" in r]
        card = (ROOT / "assets" / "trophies.svg").read_text(encoding="utf-8")
        if "No award thresholds met yet" in card:
            assert not row, "an empty trophy card is referenced from the README"
        else:
            assert len(row) == 1, "a populated trophy card must be on the page"
            assert 'colspan="2"' in row[0]
            assert "align=\"center\"" in row[0]

    def test_stars_prs_and_issues_are_not_hidden(self):
        """The old card used hide=stars,prs,issues.

        Suppressing the three least flattering columns reads as selective
        reporting. They are small, honest numbers and hiding them costs more
        credibility than showing them.
        """
        assert "hide=stars" not in README
        assert "hide=stars%2Cprs%2Cissues" not in README
        alt = re.search(r'src="[^"]*assets/stats\.svg" alt="([^"]*)"', README)
        assert alt, "stats card is missing"
        for word in ("stars", "pull requests", "issues"):
            assert word in alt.group(1), f"{word} missing from the stats alt text"

    def test_no_third_party_stats_host_is_embedded(self):
        """Both official hosts are down; a 503 renders as a broken image."""
        assert "github-readme-stats.vercel.app" not in README
        assert "github-profile-trophy.vercel.app" not in README

    def test_alt_text_agrees_with_the_card(self):
        """Alt text is generated from the same numbers as the SVG.

        This is the check that catches a card whose figures moved on while its
        description did not. The languages are compared rather than the
        percentages: alt rounds to whole numbers and the card carries one
        decimal, so comparing digits would fail on correct output.
        """
        alt = re.search(r'src="[^"]*assets/langs\.svg" alt="([^"]*)"', README).group(1)
        card = (ROOT / "assets" / "langs.svg").read_text(encoding="utf-8")
        alt_langs = [p.split()[0] for p in alt.split(":", 1)[1].split(",")]
        card_langs = re.findall(r'text-anchor="start">([A-Za-z+#\.]+)</text>', card)
        assert card_langs[:len(alt_langs)] == alt_langs, (
            f"alt says {alt_langs}, card says {card_langs}")


# ----------------------------------------------------------------------------- now


class TestNow:
    def test_three_cells_at_a_third_width(self):
        cells = re.findall(r'<td width="(\d+%)" align="center">(.*?)</td>',
                           section("Now"), re.S)
        assert [w for w, _ in cells] == ["33%", "33%", "33%"], (
            f"Now cells must be 33% each, got {[w for w, _ in cells]}")

    def test_each_cell_is_a_bold_label_over_a_short_value(self):
        for _, body in re.findall(
            r'<td width="(\d+%)" align="center">(.*?)</td>', section("Now"), re.S
        ):
            assert body.count("<b>") == 1, "a Now cell needs one bold label"
            assert body.count("<br />") == 1, "a Now cell is two lines, not a paragraph"
            label, value = body.replace("<b>", "").replace("</b>", "").split("<br />")
            assert label.strip(), "the bold line must be the label"
            assert 0 < len(value.split()) <= 5, f"value is not short: {value.strip()!r}"

    def test_the_three_labels_are_the_briefs(self):
        body = section("Now")
        for label in ("BUILDING", "LEARNING", "OPEN TO"):
            assert f"<b>{label}</b>" in body

    def test_no_paragraph_in_the_section(self):
        assert "<p>" not in section("Now")


# ----------------------------------------------------------------------------- work


class TestWork:
    def test_projects_are_not_markdown_headings(self):
        """Three stacked '### SkillBridge' blocks read as a document, not a page."""
        body = section("Work")
        assert not re.search(r"^#{1,6} ", body, re.M), "Work still uses headings"
        assert "###" not in body

    def test_one_cell_per_configured_project(self):
        assert section("Work").count('align="center"') >= len(featured())
        for entry in featured():
            assert entry["title"] in section("Work"), f"{entry['title']} not rendered"

    def test_every_project_has_the_five_required_parts(self):
        body = section("Work")
        for entry in featured():
            name = entry["name"]
            # Each cell runs from its own preview image to the end of the cell,
            # so a cell cannot borrow another project's name, chips or buttons.
            cell = re.search(
                r'(opengraph\.githubassets\.com/1/[^/"]+/' + re.escape(name)
                + r'".*?)(?=opengraph\.githubassets\.com|</td>)',
                body, re.S)
            assert cell, f"no cell for {name}"
            blob = cell.group(1)
            assert f'alt="{entry["title"]}"' in blob, f"{name}: preview alt is not the name"
            assert 'width="100%"' in blob, f"{name}: preview must scale with the cell"
            assert re.search(r"<b>[^<]+</b>", blob), f"{name}: name is not bold text"
            assert entry["summary"] in blob, f"{name}: summary line missing"
            for tool in entry["stack"]:
                assert f"badge/{tool}-" in blob, f"{name}: no {tool} chip"
            assert "badge/Repository-" in blob, f"{name}: no Repository button"

    def test_preview_is_responsive_not_fixed_width(self):
        body = section("Work")
        for m in re.finditer(r'<img src="https://opengraph[^>]*>', body):
            tag = m.group(0)
            assert 'width="100%"' in tag, "preview must scale with the cell"
            assert "max-width:480px" in tag, "an unscaled 1200px preview blows out the page"

    def test_copy_is_one_line_of_at_most_sixteen_words(self):
        for entry in featured():
            summary = entry["summary"]
            assert len(summary.split()) <= 16, f"{entry['title']}: {len(summary.split())} words"
            assert "\n" not in summary, f"{entry['title']}: copy must be a single line"

    def test_exactly_one_browse_all_link(self):
        assert section("Work").count("tab=repositories") == 1
        assert "Browse all public repositories" in README

    def test_hidden_repositories_are_never_featured(self):
        hidden = set(load_config()["projects"].get("hidden_repositories") or [])
        for name in hidden:
            assert f"/{name}\"" not in section("Work"), f"{name} is hidden but rendered"


class TestLiveBadgeIsConditional:
    """The behaviour that motivated generating this section at all."""

    @staticmethod
    def _repo(name: str, homepage: str = "", pages: bool = False) -> dict:
        return {"name": name, "html_url": f"https://github.com/kulraj025/{name}",
                "homepage": homepage, "has_pages": pages,
                "owner": {"login": "kulraj025"}}

    def _cell(self, repo, monkeypatch, demo):
        monkeypatch.setattr(build_readme, "demo_url", lambda r, a: demo)
        return build_readme.project_cell(
            {"name": repo["name"], "title": "T", "summary": "S", "stack": ["Python"]},
            repo, "kulraj025", None)

    def test_live_badge_when_a_demo_resolves(self, monkeypatch):
        cell = self._cell(self._repo("withdemo"), monkeypatch, "https://example.com/")
        assert "Live%20demo-22D3EE" in cell
        assert 'href="https://example.com/"' in cell

    def test_no_live_badge_when_no_demo_resolves(self, monkeypatch):
        cell = self._cell(self._repo("nodemo"), monkeypatch, None)
        assert "Live%20demo" not in cell
        assert "badge/Repository-" in cell, "the Repository button must still be there"

    def test_buttons_are_emitted_in_a_stable_order(self, monkeypatch):
        both = self._cell(self._repo("a"), monkeypatch, "https://example.com/")
        assert both.index("badge/Repository-") < both.index("badge/Live%20demo-")

    def test_resolution_verifies_the_url(self):
        """verify=True is the only thing stopping a Live button pointing at a 404."""
        import inspect
        from detect_homepages import resolve_demo_url
        assert "verify=True" in inspect.getsource(build_readme.demo_url)
        sig = inspect.signature(resolve_demo_url)
        assert sig.parameters["verify"].kind is inspect.Parameter.KEYWORD_ONLY

    def test_published_readme_has_a_badge_only_for_a_verifiable_host(self):
        body = section("Work")
        for href in re.findall(r'href="(https://kulraj025\.github\.io/[^"]*)"', body):
            assert href.startswith("https://"), "a demo link must be https"
        for repo_name in re.findall(r"opengraph\.githubassets\.com/1/[^/]+/([^/\"]+)", body):
            assert f'badge/Repository-' in body, repo_name


# ------------------------------------------------------------------ the SVG cards


class TestAltTextAgreesWithTheAsset:
    """An alt that describes a different graphic is worse than a duplicated one.

    The typing SVG used to take the pitch as its alt text, which is the visible
    bold line directly beneath it, so a screen reader heard the same sentence
    twice in a row instead of learning what the animation says.
    """

    def test_typing_alt_is_not_the_pitch_shown_below_it(self):
        typing = re.search(r'<img src="[^"]*assets/typing\.svg" alt="([^"]*)"', README)
        assert typing, "typing graphic is missing"
        assert typing.group(1) not in README.split("**")[1], (
            "the typing alt repeats the visible pitch line verbatim")

    def test_typing_alt_matches_the_svgs_own_description(self):
        typing_alt = re.search(
            r'<img src="[^"]*assets/typing\.svg" alt="([^"]*)"', README).group(1)
        label = re.search(r'aria-label="([^"]*)"',
                          (ROOT / "assets" / "typing.svg").read_text(encoding="utf-8")
                          ).group(1)

        def words(s: str) -> set[str]:
            return set(re.findall(r"[a-z0-9]+", s.lower()))

        # The README alt may add a prefix ("Animated text:") that the SVG's own
        # label has no use for, so the check is containment, not equality.
        missing = words(label) - words(typing_alt)
        assert not missing, (
            f"README alt omits {sorted(missing)} from the graphic's own label")

    def test_every_image_alt_is_not_just_its_filename(self):
        for src, alt in re.findall(r'<img src="([^"]*)" alt="([^"]*)"', README):
            if src.endswith(".svg") and "raw.githubusercontent" in src:
                assert len(alt.split()) >= 3, f"{src} has a token alt: {alt!r}"


class TestTheHeaderCommentIsNotPublished:
    """Regression: the generated grid was pasted into the template's doc comment.

    The template opens with a comment that *names* the slots it defines, so a
    naive whole-file substitution replaced those mentions too. The result still
    rendered (it was all inside `<!-- -->`) and the validator still reported
    every slot filled, so nothing went red -- the page was simply 24KB of
    comment wrapping 8KB of content.
    """

    def test_readme_does_not_open_with_the_documentation_comment(self):
        assert not README.lstrip().startswith("<!--"), (
            "the template's documentation comment leaked into the published page")

    def test_no_generated_block_appears_twice(self):
        expected = {
            "opengraph.githubassets.com": len(featured()),
            "assets/stats.svg": 1,
            "streak-stats.demolab.com": 1,
            "assets/langs.svg": 1,
        }
        for marker, want in expected.items():
            got = README.count(marker)
            assert got == want, (
                f"{marker} appears {got} times, expected {want}: a block was "
                "emitted twice, most likely into the comment as well as the page")

    def test_the_template_still_documents_its_own_slots(self):
        """The comment is the field map, and it has to name the slots to be useful."""
        template = (ROOT / "templates" / "README.template.md").read_text(encoding="utf-8")
        header = re.match(r"<!--.*?-->", template, re.S)
        assert header, "the template must open with its documentation comment"
        for slot in ("WORK_ROWS", "STATS_ROWS"):
            assert f"{{{{{slot}}}}}" in header.group(0), (
                f"{{{slot}}} is undocumented in the field map")


class TestStatCards:
    @pytest.mark.parametrize("name", ["stats.svg", "langs.svg", "trophies.svg"])
    def test_card_is_valid_xml_and_carries_its_own_background(self, name):
        root = ET.parse(ROOT / "assets" / name).getroot()
        assert root.tag == f"{SVG_NS}svg"
        rects = root.findall(f"{SVG_NS}rect")
        assert rects, f"{name} has no background rect"
        # A card with a transparent background is invisible in GitHub's light
        # theme, which is where a large share of visitors arrive.
        assert rects[0].get("fill", "").startswith("#"), f"{name} background is not opaque"
        assert rects[0].get("width") == root.get("width")
        assert rects[0].get("height") == root.get("height")

    @pytest.mark.parametrize("name", ["stats.svg", "langs.svg", "trophies.svg"])
    def test_card_is_labelled_for_screen_readers(self, name):
        root = ET.parse(ROOT / "assets" / name).getroot()
        assert root.get("role") == "img"
        assert root.get("aria-label"), f"{name} has no aria-label"

    @pytest.mark.parametrize("name", ["stats.svg", "langs.svg", "trophies.svg"])
    def test_no_text_overflows_the_card(self, name):
        """Checked on the committed file, not on a fresh render.

        Clipping is the bug this repository already shipped once: the heading
        rendered as "ilding campus products and XAI". A card that clips a number
        is quieter and just as wrong.
        """
        root = ET.parse(ROOT / "assets" / name).getroot()
        w = float(root.get("width"))
        for node in root.iter(f"{SVG_NS}text"):
            value = node.text or ""
            size = float(node.get("font-size"))
            width = render_stats.text_w(value, size)
            x = float(node.get("x"))
            anchor = node.get("text-anchor", "start")
            left = x if anchor == "start" else x - width / 2
            if anchor == "end":
                left = x - width
            assert left >= -1, f"{name}: {value!r} starts at {left:.0f}, off the left edge"
            assert left + width <= w + 1, (
                f"{name}: {value!r} ends at {left + width:.0f}px on a {w:.0f}px card")

    def test_stats_card_shows_every_metric_the_alt_text_claims(self):
        card = (ROOT / "assets" / "stats.svg").read_text(encoding="utf-8")
        for label in ("Commits", "Stars", "Pull requests", "Issues", "Repositories"):
            # The commit label carries the year ("Commits 2026"), so match the
            # element's text rather than an exact tag pair.
            assert re.search(r">[^<]*" + label + r"[^<]*</text>", card), (
                f"{label} is missing from the card")

    def test_no_award_is_ever_awarded_without_the_count_for_it(self):
        """The rules are thresholds; nothing may be awarded ahead of its count.

        This is the guard on the bug that rendered "Pull Shark (bronze)" beside
        a stats card reading "0 pull requests", because the PR qualifiers had
        been sent to the commits search index, which ignores them.
        """
        assert render_stats.earned_trophies({}) == []
        for name, key, levels in render_stats.TROPHY_RULES:
            lowest = levels[0]
            below = render_stats.earned_trophies({key: lowest - 1})
            assert all(n != name for n, _, _ in below), (
                f"{name} awarded at {lowest - 1}, below its own threshold {lowest}")
            at = render_stats.earned_trophies({key: lowest})
            assert any(n == name for n, _, _ in at), f"{name} not awarded at its threshold"
