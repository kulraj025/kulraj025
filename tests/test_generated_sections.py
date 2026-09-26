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
import metrics  # noqa: E402
from metrics import load_config  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")
SVG_NS = "{http://www.w3.org/2000/svg}"


def section(name: str) -> str:
    """The body of one labelled section, up to the next label.

    Sections are delimited by a small centred `<code>NAME</code>` label rather
    than a markdown heading, because GitHub renders h2 at a size that competes
    with the banner and a numbered "02 - Now" read as a slide deck. The locator
    therefore matches the label, and a section runs until the next one.
    """
    label = re.compile(r"<code[^>]*>" + name + r"</code>")
    starts = [m.start() for m in label.finditer(README)]
    assert starts, f"no '{name}' section label"
    assert len(starts) == 1, f"'{name}' label appears {len(starts)} times"
    start = starts[0]
    nxt = re.search(r"<p align=\"center\"><code", README[start + 1:])
    end = start + 1 + nxt.start() if nxt else len(README)
    return README[start:end]


def featured() -> list[dict]:
    return load_config()["projects"]["featured"]


# --------------------------------------------------------------------------- stats


class TestStats:
    def test_title_is_exactly_stats(self):
        """The label is the heading now, and it is the same shape as every other.

        Markdown headings are gone on purpose: GitHub renders h2 at a size that
        competes with the banner. What must survive is that the section is
        labelled, and that no numbered heading crept back in.
        """
        assert "<code" in section("STATS")[:200]
        assert not re.search(r"^#{1,6} ", README, re.M), (
            "sections must be labelled, not headed; a heading is a different size "
            "from every other section and breaks the rhythm")
        assert not re.search(r"^## \d", README, re.M), "sections must not be numbered"

    def test_first_row_is_stats_beside_languages(self):
        first = section("STATS").split("<tr>")[1]
        assert "assets/stats.svg" in first
        assert "assets/langs.svg" in first
        assert first.count("<td") == 2, "row 1 must be exactly two cells"

    def test_streak_is_centred_on_its_own_row(self):
        rows = section("STATS").split("<tr>")[1:]
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
        row = [r for r in section("STATS").split("<tr>") if "trophies.svg" in r]
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
        cells = re.findall(r'<td width="(\d+%)" align="center"[^>]*>(.*?)</td>',
                           section("NOW"), re.S)
        assert [w for w, _ in cells] == ["33%", "33%", "33%"], (
            f"Now cells must be 33% each, got {[w for w, _ in cells]}")

    def test_each_cell_is_a_bold_label_over_a_short_value(self):
        for width, body in re.findall(
            r'<td width="(\d+%)" align="center"[^>]*>(.*?)</td>', section("NOW"), re.S
        ):
            assert body.count("<b>") == 1, "a Now cell needs one bold value"
            assert body.count("<br />") == 1, "a Now cell is two lines, not a paragraph"
            label, value = body.replace("<b>", "").replace("</b>", "").split("<br />")
            assert "<code" in label, (
                "the label must use the same <code> treatment as the section "
                f"labels, not plain text: {label.strip()!r}")
            assert 0 < len(value.split()) <= 5, f"value is not short: {value.strip()!r}"

    def test_the_three_labels_are_the_briefs(self):
        body = section("NOW")
        for label in ("BUILDING", "LEARNING", "OPEN TO"):
            assert f">{label}</code>" in body, f"{label} is not a Now label"

    def test_no_paragraph_in_the_section(self):
        assert "<p>" not in section("NOW")


# ----------------------------------------------------------------------------- work


class TestWork:
    def test_projects_are_not_markdown_headings(self):
        """Three stacked '### SkillBridge' blocks read as a document, not a page."""
        body = section("WORK")
        assert not re.search(r"^#{1,6} ", body, re.M), "Work still uses headings"
        assert "###" not in body

    def test_one_cell_per_configured_project(self):
        assert section("WORK").count('align="center"') >= len(featured())
        for entry in featured():
            assert entry["title"] in section("WORK"), f"{entry['title']} not rendered"

    def test_every_project_has_the_five_required_parts(self):
        body = section("WORK")
        for entry in featured():
            name = entry["name"]
            # Each cell runs from its own thumbnail to the end of the cell, so a
            # cell cannot borrow another project's name, chips or buttons.
            cell = re.search(
                r'(assets/work/' + re.escape(name)
                + r'\.svg".*?)(?=assets/work/|</td>)',
                body, re.S)
            assert cell, f"no cell for {name}"
            blob = cell.group(1)
            assert f'alt="{entry["title"]} project card"' in blob, \
                f"{name}: thumb alt is not the project name"
            assert 'width="100%"' in blob, f"{name}: thumb must scale with the cell"
            assert re.search(r"<b>[^<]+</b>", blob), f"{name}: name is not bold text"
            assert entry["summary"] in blob, f"{name}: summary line missing"
            for tool in entry["stack"]:
                assert f"badge/{tool}-" in blob, f"{name}: no {tool} chip"
            assert "badge/Repository-" in blob, f"{name}: no Repository button"

    def test_the_thumbnail_is_ours_and_carries_no_photograph(self):
        """The social preview was replaced, so nothing may bring it back.

        `opengraph.githubassets.com` is a white card that stamps the profile
        photo onto every project and prints the repository description verbatim
        -- for helping-station-deu that description is literally the string "x".
        """
        assert "opengraph.githubassets.com" not in README
        for name in (e["name"] for e in featured()):
            thumb = ROOT / "assets" / "work" / f"{name}.svg"
            assert thumb.exists(), f"assets/work/{name}.svg is not committed"
            body = thumb.read_text(encoding="utf-8")
            assert "<image" not in body, (
                f"assets/work/{name}.svg embeds a raster image; a project card "
                "must not contain a photograph of the person")

    def test_thumb_is_responsive_and_sized_from_its_own_viewbox(self):
        """`max-width` must equal the card's real width.

        Hardcoding 480 here would be right for two of the three cards and wrong
        for the featured one, so the assertion is derived: the number in the
        README has to be the number in the SVG. That catches both a stale
        hardcode and a card regenerated at a new width.
        """
        body = section("WORK")
        found = 0
        for m in re.finditer(
            r'assets/work/([A-Za-z0-9_.-]+)\.svg"[^>]*max-width:(\d+)px', body
        ):
            name, declared = m.group(1), int(m.group(2))
            real = int(ET.parse(ROOT / "assets" / "work" / f"{name}.svg")
                       .getroot().get("width"))
            assert declared == real, (
                f"{name}: README says max-width {declared}px, the card is {real}px")
            found += 1
        assert found == len(featured()), (
            f"checked {found} thumb(s), expected {len(featured())}")

    def test_no_unexpanded_placeholder_reaches_the_page(self):
        """A `.format()` missed at one call site is a 200 that serves a literal.

        `thumb_url` exists because the module-level THUMB_BASE template string
        was used unformatted at one site, which produced URLs containing
        `{handle}`. That is not a crash: it is a 404 in a cell on a page whose
        entire promise is that nothing is broken.
        """
        assert "{" not in README, "an unexpanded {placeholder} reached README.md"
        assert "}" not in README, "an unexpanded {placeholder} reached README.md"

    def test_copy_is_one_line_of_at_most_sixteen_words(self):
        for entry in featured():
            summary = entry["summary"]
            assert len(summary.split()) <= 16, f"{entry['title']}: {len(summary.split())} words"
            assert "\n" not in summary, f"{entry['title']}: copy must be a single line"

    def test_exactly_one_browse_all_link(self):
        assert section("WORK").count("tab=repositories") == 1
        assert "Browse all repositories" in README

    def test_hidden_repositories_are_never_featured(self):
        hidden = set(load_config()["projects"].get("hidden_repositories") or [])
        for name in hidden:
            assert f"/{name}\"" not in section("WORK"), f"{name} is hidden but rendered"


class TestLiveBadgeIsConditional:
    """The behaviour that motivated generating this section at all."""

    @staticmethod
    def _repo(name: str, homepage: str = "", pages: bool = False) -> dict:
        return {"name": name, "html_url": f"https://github.com/kulraj025/{name}",
                "homepage": homepage, "has_pages": pages,
                "owner": {"login": "kulraj025"}}

    def _cell(self, repo, monkeypatch, demo):
        monkeypatch.setattr(build_readme, "demo_url", lambda r, a: demo)
        # project_cell refuses to render a project with no card in assets/work/,
        # which is correct for the page but means these badge tests need a stub.
        import render_work_thumbs
        name = repo["name"]
        stub = ROOT / "assets" / "work" / f"{name}.svg"
        assert not stub.exists(), f"{name} collides with a committed thumb"
        stub.write_text(render_work_thumbs.card(name, "T", "BUILDING"), encoding="utf-8")
        try:
            return build_readme.project_cell(
                {"name": name, "title": "T", "summary": "S", "stack": ["Python"]},
                repo, "kulraj025", None)
        finally:
            stub.unlink()

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
        body = section("WORK")
        for href in re.findall(r'href="(https://kulraj025\.github\.io/[^"]*)"', body):
            assert href.startswith("https://"), "a demo link must be https"
        for repo_name in re.findall(r"assets/work/([A-Za-z0-9_.-]+)\.svg", body):
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
            "assets/work/": len(featured()),
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
        header = build_readme.HEADER_RE.match(template)
        assert header, "the template must open with its documentation comment"
        for slot in ("WORK_ROWS", "STATS_ROWS", "QUOTE_TEXT", "THUMB_BASE"):
            assert f"{{{{{slot}}}}}" in header.group(0), (
                f"{{{slot}}} is undocumented in the field map")


class TestTheHeaderStripIsNotFooled:
    """Regression: documenting the markers cut the header short and printed the
    field map across the middle of the page.

    `HEADER_RE` used to be `\\A\\s*<!--.*?-->`, lazy, so it ended at the first
    closing marker anywhere in the file. Adding a complete marker comment to the
    header -- which is exactly what documenting the new generated regions seemed
    to call for -- moved that first marker 130 lines earlier. Everything after it
    became page body, including the field map, whose own `{{STATS_ROWS}}` was
    then replaced with live `<tr>` markup.

    Nothing detected it. The page rendered, the validator found every slot
    filled, the tests passed, and CI was green. The only symptom was a README of
    21KB instead of 8KB with build internals visible on the page.
    """

    def test_a_complete_comment_inside_the_header_does_not_end_it(self):
        decoy = (
            "<!--\n"
            "  The header documents the markers. It mentions one in full:\n"
            "    <!-- BEGIN GENERATED:STATS --> and its partner -->\n"
            "  which must not be mistaken for the end of this comment.\n"
            "-->\n"
            "\n"
            "## Real Section\n\nbody text\n"
        )
        m = build_readme.HEADER_RE.match(decoy)
        assert m, "the header must be recognised"
        assert "must not be mistaken" in m.group(0), (
            "HEADER_RE stopped at the decoy comment instead of the real one")
        assert "Real Section" not in m.group(0), (
            "HEADER_RE swallowed the page body as well as the header")

    def test_the_real_header_ends_on_its_own_line(self):
        template = (ROOT / "templates" / "README.template.md").read_text(encoding="utf-8")
        body = build_readme.HEADER_RE.sub("", template, count=1)
        assert body != template, "the template must open with its documentation comment"
        assert not body.lstrip().startswith("<!--"), (
            "a complete comment before the header's real closing line: the header "
            "is being cut short and the field map is falling into the page")

    def test_the_published_page_contains_no_build_internals(self):
        """The direct symptom of a short header strip, asserted on the output.

        These strings only ever appear in the template's field map. If any of them
        reaches README.md the header strip failed, whatever the reason.

        The `GENERATED:` marker names are deliberately absent from this list: the
        two marker comments *are* published, because `--check` locates the regions
        by them. GitHub strips HTML comments before rendering, so they are free.
        `test_the_published_readme_has_exactly_the_two_regions` pins their count.
        """
        for leak in ("build_readme.py", "the whole block: row 1 is",
                     "Field map", "{{", "}}", "field map"):
            assert leak not in README, (
                f"{leak!r} is in the published page: the template's documentation "
                f"is being rendered as content")

    def test_the_page_is_not_bloated_by_the_header(self):
        """A short header strip tripled the size of this file."""
        assert len(README.encode()) < 12_000, (
            f"README.md is {len(README.encode()):,} bytes, which is roughly what "
            f"a leaked documentation comment looks like")


class TestGeneratedRegions:
    """The marker fences, and the exactly-once rule for the slots inside them."""

    def test_the_published_readme_has_exactly_the_three_regions(self):
        """STATS, WORK and QUOTE.

        The quote is a generated region for one reason: it rotates, so --check
        has to be able to splice the committed one back to stay offline. If it
        were an ordinary slot the check would re-pick today's line and go red
        every time midnight passed.
        """
        regions = build_readme.committed_regions(README)
        assert set(regions) == {"STATS", "WORK", "QUOTE"}, (
            f"expected the STATS, WORK and QUOTE regions, found {sorted(regions)}")
        for name, block in regions.items():
            assert block.strip(), f"the {name} region is empty"

    def test_a_generated_slot_appears_exactly_once_in_the_body(self):
        template = (ROOT / "templates" / "README.template.md").read_text(encoding="utf-8")
        body = build_readme.HEADER_RE.sub("", template, count=1)
        for slot in ("STATS_ROWS", "WORK_ROWS"):
            n = body.count("{{" + slot + "}}")
            assert n == 1, (
                f"{{{{{slot}}}}} appears {n} times in the template body; a second "
                f"occurrence is the field map, and filling it puts live markup in "
                f"the documentation")

    def test_filling_a_duplicated_generated_slot_is_refused(self):
        doc = "{{WORK_ROWS}} appears once here and once in the map: {{WORK_ROWS}}"
        with pytest.raises(SystemExit, match="appears 2 times"):
            build_readme._fill(doc, {"WORK_ROWS": "<tr></tr>"}, strict=True)

    def test_ordinary_slots_may_repeat(self):
        """{{HANDLE}} is once per URL and per badge; counting those is wrong."""
        doc = "{{HANDLE}} {{HANDLE}} {{HANDLE}}"
        out = build_readme._fill(doc, {"HANDLE": "kulraj025"})
        assert out == "kulraj025 kulraj025 kulraj025"

    def test_the_work_region_owns_its_table(self):
        """Splicing only the slot would nest a <table> inside a <table>."""
        block = build_readme.committed_regions(README)["WORK"]
        assert block.lstrip().startswith("<table>"), (
            "the WORK region must include the <table> wrapper, so --check can "
            "splice the whole block")
        assert block.rstrip().endswith("</table>")


class TestLanguageOrderIsDeterministic:
    """Tied languages must not swap places between two runs of the same data.

    `sorted(key=bytes, reverse=True)` leaves ties in dict-insertion order, which
    follows the order the repository listing happened to come back in. HTML and
    JavaScript are both at 3.3% of the bytes here, and they did swap: the card
    listed one order and the README alt text listed the other, because the two
    are rendered by separate calls that each got a different insertion order.
    """

    def test_a_tie_is_broken_alphabetically(self):
        class FakeAPI:
            def repo_languages(self, _name):
                # Same total bytes for two languages, and a third that ties too.
                return {"Zig": 100, "HTML": 100, "JavaScript": 100, "C": 50}

        ranked = metrics.top_languages(
            FakeAPI(), "kulraj025", [{"name": "r"}], limit=6)
        names = [n for n, _ in ranked]
        # The three tied languages come first, alphabetically among themselves.
        # C has fewer bytes, so it sorts last -- the order is by bytes first.
        assert names == ["HTML", "JavaScript", "Zig", "C"], names

    def test_two_runs_agree(self):
        class FakeAPI:
            def repo_languages(self, _name):
                return {"PHP": 200, "Python": 200, "Rust": 900}

        a = metrics.top_languages(FakeAPI(), "h", [{"name": "r"}], limit=6)
        b = metrics.top_languages(FakeAPI(), "h", [{"name": "r"}], limit=6)
        assert a == b, f"{a} != {b}"

    def test_the_committed_card_and_alt_text_agree(self):
        """The invariant the tie-break exists to protect."""
        alt = re.search(r'src="[^"]*assets/langs\.svg" alt="([^"]*)"', README).group(1)
        card = (ROOT / "assets" / "langs.svg").read_text(encoding="utf-8")
        alt_langs = [p.split()[0] for p in alt.split(":", 1)[1].split(",")]
        card_langs = re.findall(r'text-anchor="start">([A-Za-z+#\.]+)</text>', card)
        assert card_langs[:len(alt_langs)] == alt_langs, (
            f"alt says {alt_langs}, card says {card_langs}")


class TestTheCardCheckIsStructural:
    """`render_stats.py --check` verifies what is stable, not what moves.

    It used to re-render and diff, which was red on a cold cache within minutes
    of a green run: `langs.svg` is built from per-repository language byte counts
    and Linguist re-analyses asynchronously after a push. These tests pin the
    replacement, and pin that it can still fail.
    """

    def test_the_committed_cards_pass(self):
        assert render_stats.check_cards() == []

    def test_the_check_does_not_touch_the_network(self, monkeypatch):
        monkeypatch.setattr(render_stats, "GitHubAPI",
                            lambda *_a, **_kw: pytest.fail("--check reached for the API"))
        monkeypatch.setattr(render_stats, "build",
                            lambda *_a, **_kw: pytest.fail("--check re-rendered the cards"))
        assert render_stats.main(["--check"]) == 0

    def _mutate(self, tmp_path, monkeypatch, name, old, new):
        src = (ROOT / "assets" / name).read_text(encoding="utf-8")
        assert old in src, f"fixture text {old!r} not in assets/{name}"
        assets = tmp_path / "assets"
        assets.mkdir()
        for card in ("stats.svg", "langs.svg", "trophies.svg"):
            text = src if card == name else (ROOT / "assets" / card).read_text(encoding="utf-8")
            (assets / card).write_text(text.replace(old, new), encoding="utf-8")
        (tmp_path / "README.md").write_text(README, encoding="utf-8")
        monkeypatch.setattr(render_stats, "ASSETS", assets)
        return render_stats.check_cards()

    def test_a_transparent_card_is_rejected(self, tmp_path, monkeypatch):
        problems = self._mutate(tmp_path, monkeypatch, "langs.svg",
                                'rx="8" fill="#1A1B26"', 'rx="8" fill="none"')
        assert any("opaque background" in p for p in problems), problems

    def test_a_background_smaller_than_the_card_is_rejected(self, tmp_path, monkeypatch):
        problems = self._mutate(tmp_path, monkeypatch, "langs.svg",
                                '<rect width="460"', '<rect width="440"')
        assert any("edges would show through" in p for p in problems), problems

    def test_malformed_xml_is_rejected(self, tmp_path, monkeypatch):
        problems = self._mutate(tmp_path, monkeypatch, "langs.svg", "</svg>", "")
        assert any("not valid XML" in p for p in problems), problems

    def test_placeholder_text_is_rejected(self, tmp_path, monkeypatch):
        problems = self._mutate(tmp_path, monkeypatch, "stats.svg", "Stars", "TODO")
        assert any("placeholder" in p for p in problems), problems

    def test_a_card_that_disagrees_with_its_alt_text_is_rejected(self, tmp_path, monkeypatch):
        """The one cross-file invariant, and it is fully offline.

        The value mutated here is READ OUT of the committed card rather than
        hardcoded. An earlier version replaced the literal `>40<`, which meant
        the test started failing the day the commit count stopped being 40 --
        a test broken by data moving, on a suite whose whole point is that data
        moving must not make anything red. The assertion is about the check
        firing, not about what the count happens to be today.
        """
        card = (ROOT / "assets" / "stats.svg").read_text(encoding="utf-8")
        # The commit count is the first integer rendered as a bare <text> value.
        found = re.search(r">(\d{1,4})</text>", card)
        assert found, "no bare integer in stats.svg to mutate"
        original = found.group(1)
        problems = self._mutate(tmp_path, monkeypatch, "stats.svg",
                                f">{original}<", f">{int(original) + 9999}<")
        assert any("does not mention it" in p for p in problems), problems


class TestTheCheckIsOffline:
    """`--check` must not touch the network, or CI is at the mercy of the API.

    It compares the committed README against a fresh render of the template with
    the two generated regions taken from the committed file. That makes it
    deterministic: GitHub's commit-search index and Linguist both settle
    asynchronously after a push, so the commit count and even the language
    ordering change minutes after an identical build. An earlier strict check
    demanded byte-exact agreement with live data and was red nearly every time.
    """

    def test_check_constructs_no_api_client(self, monkeypatch):
        def explode(*_a, **_kw):
            raise AssertionError("--check tried to reach the GitHub API")

        monkeypatch.setattr(build_readme, "GitHubAPI", explode)
        assert build_readme.main(["--check"]) == 0

    def test_check_tolerates_a_number_that_has_moved(self, monkeypatch, tmp_path):
        """A stale digit inside a generated region must not fail the check.

        This is the whole point of the design, and the reason the numbers are the
        daily job's business rather than this check's.
        """
        readme = tmp_path / "README.md"
        readme.write_text(README.replace("40 commits in 2026", "9999 commits in 2026"),
                          encoding="utf-8")
        monkeypatch.setattr(build_readme, "README", readme)
        monkeypatch.setattr(build_readme, "GitHubAPI",
                            lambda *_a, **_kw: pytest.fail("--check reached for the API"))
        assert build_readme.main(["--check"]) == 0

    def test_check_catches_a_hand_edited_page(self, monkeypatch, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(README.replace("Ship the first version", "Ship it"), encoding="utf-8")
        monkeypatch.setattr(build_readme, "README", readme)
        monkeypatch.setattr(build_readme, "GitHubAPI",
                            lambda *_a, **_kw: pytest.fail("--check reached for the API"))
        assert build_readme.main(["--check"]) == 1


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


# ------------------------------------------------------------------- the quote


class TestTheQuote:
    """The rotating line. It has to be deterministic or --check is worthless."""

    def test_the_same_day_always_gives_the_same_line(self):
        from datetime import date
        quotes = load_config()["content"]["quotes"]
        a = build_readme.quote_of_the_day(quotes, date(2026, 3, 1))
        b = build_readme.quote_of_the_day(quotes, date(2026, 3, 1))
        assert a == b

    def test_consecutive_days_differ(self):
        """Otherwise it is not rotating, it is just a static line."""
        from datetime import date, timedelta
        quotes = load_config()["content"]["quotes"]
        lines = [build_readme.quote_of_the_day(quotes, date(2026, 3, 1) + timedelta(days=i))
                 for i in range(len(quotes))]
        assert len(set(lines)) == len(quotes), (
            "the quote list does not come round within its own length")

    def test_every_line_comes_from_the_config(self):
        from datetime import date, timedelta
        quotes = load_config()["content"]["quotes"]
        start = date(2026, 1, 1)
        for i in range(400):
            got = build_readme.quote_of_the_day(quotes, start + timedelta(days=i))
            assert got in quotes, f"day {i} produced a line that is not in the config"

    def test_no_quote_is_ever_empty(self):
        for q in load_config()["content"]["quotes"]:
            assert q.strip(), "an empty quote renders as a blank line on the page"

    def test_the_published_quote_is_one_of_the_configured_lines(self):
        body = build_readme.committed_regions(README)["QUOTE"]
        text = re.sub(r"<[^>]+>", "", body).strip()
        assert text, "the QUOTE region is empty"
        assert text in load_config()["content"]["quotes"], (
            f"the page shows {text!r}, which is not in the config")

    def test_quotes_claim_nothing_verifiable(self):
        """A quote is a principle, not a testimonial.

        These lines sit under a profile that a recruiter reads as claims. A
        number, a metric or a named employer in a rotating quote would be
        unverifiable decoration on someone else's credibility.
        """
        banned = re.compile(r"\b\d+[%+]?\b|\b(?:clients?|users?|revenue|users)\b",
                            re.I)
        for q in load_config()["content"]["quotes"]:
            assert not banned.search(q), f"quote makes a claim: {q!r}"


# --------------------------------------------------------------- the thumbnails


class TestTheProjectThumbs:
    """assets/work/*.svg, generated by scripts/render_work_thumbs.py."""

    def test_one_card_per_featured_project(self):
        import render_work_thumbs
        on_disk = {p.name for p in (ROOT / "assets" / "work").glob("*.svg")}
        assert on_disk == {f"{e['name']}.svg" for e in featured()}, (
            "a card exists with no featured project, or a project has no card; "
            "either way the grid and the artwork disagree")

    def test_the_check_passes_on_a_clean_tree(self):
        import render_work_thumbs
        assert render_work_thumbs.main(["--check"]) == 0

    def test_each_card_parses_and_carries_its_own_dark_background(self):
        """A transparent card is invisible in GitHub's light theme."""
        for path in sorted((ROOT / "assets" / "work").glob("*.svg")):
            ET.parse(path)
            body = path.read_text(encoding="utf-8")
            assert 'fill="#0B1220"' in body or "url(#bg)" in body, (
                f"{path.name} has no opaque background rect")

    def test_all_cards_share_one_height_and_only_two_widths(self):
        """The featured card is wider; everything else about it is the same.

        One height and one grid pitch across all three is what makes the wide
        card read as the same object rather than a different component. The
        first featured project is the full-width row, so it is the wide one.
        """
        sizes = {}
        for path in sorted((ROOT / "assets" / "work").glob("*.svg")):
            root = ET.parse(path).getroot()
            sizes[path.stem] = (int(root.get("width")), int(root.get("height")))
        heights = {h for _, h in sizes.values()}
        assert len(heights) == 1, f"cards do not share a height: {sizes}"
        widths = sorted({w for w, _ in sizes.values()})
        assert len(widths) == 2, f"expected one wide and one narrow card, got {sizes}"
        first = featured()[0]["name"]
        assert sizes[first][0] == widths[-1], (
            f"the first featured project takes the full row, so its card must be "
            f"the wide one: {sizes}")
        for name, (w, _) in sizes.items():
            if name != first:
                assert w == widths[0], f"{name} is neither the wide nor the narrow card"

    def test_every_text_run_is_pinned_so_it_cannot_crop(self):
        """The rule the hero SVGs already follow.

        Without textLength a run is as wide as whatever font the viewer has, so
        a viewer without the intended font gets a different width -- which is
        how the banner once cropped to "ilding campus products".
        """
        for path in sorted((ROOT / "assets" / "work").glob("*.svg")):
            body = path.read_text(encoding="utf-8")
            for m in re.finditer(r"<text\b[^>]*>([^<]*)</text>", body):
                assert "textLength=" in m.group(0), (
                    f"{path.name}: {m.group(1)[:30]!r} has no textLength pin")
                assert m.group(1).strip(), f"{path.name} has an empty <text>"

    def test_no_text_can_overflow_the_card(self):
        """Bounds are read from each card's own viewBox, not assumed to be 480.

        Two of the three cards are 480 wide and the featured one is 900, so a
        hardcoded width here would be wrong for one of them by construction --
        and would be a test that passes for the wrong reason.

        The anchor is respected, because it decides which way the run extends.
        An earlier version of this test measured every run to the right of x,
        which is only true for `text-anchor="start"`. The right-hand column of
        the wide card is anchored "end", so the test flagged a card that was in
        fact correct, and a test that cries wolf gets deleted rather than fixed.
        """
        for path in sorted((ROOT / "assets" / "work").glob("*.svg")):
            width = int(ET.parse(path).getroot().get("width"))
            body = path.read_text(encoding="utf-8")
            for m in re.finditer(r"<text\b[^>]*>", body):
                tag = m.group(0)
                lm = re.search(r'x="(\d+)"', tag)
                tm = re.search(r'textLength="(\d+)"', tag)
                if not (lm and tm):
                    continue
                x, length = int(lm.group(1)), int(tm.group(1))
                anchor = re.search(r'text-anchor="(\w+)"', tag)
                anchor = anchor.group(1) if anchor else "start"
                left = x - length if anchor == "end" else x
                right = left + length
                assert left >= 0, f"{path.name}: a run starts at {left}, off the card"
                assert right <= width, (
                    f"{path.name}: a {anchor}-anchored run at x={x} of {length}px "
                    f"spans {left}..{right}, past the {width}px card edge")

    def test_a_photo_of_the_person_is_never_embedded(self):
        """A project card shows the project."""
        for path in sorted((ROOT / "assets" / "work").glob("*.svg")):
            body = path.read_text(encoding="utf-8")
            assert "<image" not in body, f"{path.name} embeds a raster image"

    def test_smil_keytimes_run_zero_to_one(self):
        """Chrome discards an <animate> whose keyTimes do not span 0 to 1.

        The animation then simply does not happen, which is a silent failure:
        the card looks static and nothing reports an error.
        """
        for path in sorted((ROOT / "assets" / "work").glob("*.svg")):
            body = path.read_text(encoding="utf-8")
            for m in re.finditer(r"<animate\b[^>]*>", body):
                tag = m.group(0)
                if "keyTimes" in tag:
                    kt = re.search(r'keyTimes="([^"]+)"', tag).group(1)
                    first, last = kt.split(";")[0], kt.split(";")[-1]
                    assert float(first) == 0.0 and float(last) == 1.0, (
                        f"{path.name}: keyTimes {kt!r} do not run 0 to 1")
                assert 'repeatCount="indefinite"' in tag, (
                    f"{path.name}: an animation does not loop")

    def test_the_motion_budget_is_enforced_and_not_merely_declared(self):
        """A guard that has never fired is a comment, not a check.

        Rendered with the budget set below the number of animations the card
        actually emits, so this fails if the guard is deleted or short-circuited.
        """
        import render_work_thumbs
        real = render_work_thumbs.MAX_ANIMATIONS_PER_ASSET
        try:
            render_work_thumbs.MAX_ANIMATIONS_PER_ASSET = 1
            with pytest.raises(SystemExit):
                render_work_thumbs.card("x", "X", "BUILDING")
        finally:
            render_work_thumbs.MAX_ANIMATIONS_PER_ASSET = real

    def test_each_card_stays_inside_the_motion_budget(self):
        import render_work_thumbs
        body = (ROOT / "assets" / "work" / f"{featured()[0]['name']}.svg").read_text()
        assert body.count("<animate ") <= render_work_thumbs.MAX_ANIMATIONS_PER_ASSET


class TestGeneratedURLs:
    """A URL that is wrong in a way only the network can see.

    `thumb_url` was a module-level format string used unformatted at one call
    site, which produced image URLs containing a literal `{handle}`. Nothing
    crashed: the page rendered, every test passed, CI was green, and three cells
    404'd. Only `validate_readme.py --check-external` caught it, which means the
    offline suite had a hole. These close it.
    """

    def test_thumb_url_is_fully_formatted(self):
        url = build_readme.thumb_url("kulraj025", "skillbridge")
        assert "{" not in url and "}" not in url, f"unformatted placeholder in {url}"
        assert url == (
            "https://raw.githubusercontent.com/kulraj025/kulraj025/main/"
            "assets/work/skillbridge.svg")

    @pytest.mark.parametrize("name", [e["name"] for e in featured()])
    def test_no_committed_thumb_url_contains_a_placeholder(self, name):
        entry = next(e for e in featured() if e["name"] == name)
        url = build_readme.thumb_url("kulraj025", entry["name"])
        assert url in README, f"{name}'s card URL is not the one on the page"
