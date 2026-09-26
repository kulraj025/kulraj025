#!/usr/bin/env python3
"""Validate the hand-maintained profile README.

This is deliberately independent of the retired SVG/README generator. It checks
the things that actually break a profile page:

  * leftover placeholders from the draft
  * images with no alt text (GitHub renders nothing useful when this is missing)
  * tags GitHub silently strips, or does not allow at all
  * <tr>/<td> outside a <table>, which browsers drop and which broke a column once
  * relative image paths and links that point at files which do not exist
  * a bare email address instead of a mailto: link
  * a README large enough to be slow to render through GitHub's image proxy

Standard library only, so it runs in CI with no install step.

    python3 scripts/validate_readme.py [--check-external]

--check-external additionally requests every https:// URL. Those are third-party
services, so an outage is not a defect in this repository; the workflow runs that
mode with continue-on-error and reports the result without failing the build.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"

MAX_BYTES = 120_000

PLACEHOLDERS = [
    (r"\bREPLACE\b", "unfilled REPLACE placeholder"),
    (r"\blorem ipsum\b", "lorem ipsum"),
    (r"\bFIXME\b", "FIXME marker"),
    (r"\byour[-_ ]username\b", "your-username placeholder"),
    (r"\bTODO\b", "TODO marker"),
    (r"\bXXX\b", "XXX marker"),
    (r"example\.com", "example.com placeholder"),
    (r"localhost", "localhost URL"),
]

# Strings a badge/image host uses to say "I could not make this", returned with
# HTTP 200 and a valid image body.
#
# This list exists because of a bug that survived many verification passes.
# shields.io answers an unparseable badge path with HTTP 200 and a 132x20 SVG
# whose only content is `aria-label="404: badge not found"`. Every status-code
# check reported the badge row as healthy while the rendered page showed red
# placeholders, and the cause -- `&style=` where shields requires `?style=` -- is
# invisible unless the body is read.
#
# Keep this list in sync with the hosts actually used on the page. A new host
# gets an entry the day it is added, not after it has shipped a broken image.
ERROR_BODY_MARKERS = (
    "badge not found",            # shields.io: 200 with a 404 placeholder
    "404: not found",             # generic
    "image not found",
    "error obtaining badge",      # shields.io alternate wording
    "invalid badge",
    "decommissioned",
    "deployment paused",          # vercel 503 body, in case it ever answers 200
    "deployment disabled",
    "this project is currently",  # vercel 402 "deployment disabled" preamble
)

# GitHub strips or forbids these outright.
BANNED_TAGS = {
    "script", "style", "iframe", "object", "embed", "form", "video", "audio",
    "input", "button", "canvas",
}

VOID_OK = {"br", "hr", "img", "meta", "link", "source", "col", "area", "base"}


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.images: list[tuple[str, str]] = []
        self.links: list[str] = []
        self.stack: list[str] = []
        self.stray_cells: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        self.tags.append(tag)
        if tag not in VOID_OK:
            self.stack.append(tag)
        if tag == "img":
            self.images.append((a.get("src", ""), a.get("alt", "")))
        if tag == "a":
            self.links.append(a.get("href", ""))
        # <picture><source srcset="..."> is a real image reference too, and an
        # unverified one is exactly how a dark-mode asset ends up broken.
        for key in ("srcset", "data-src"):
            if a.get(key):
                for part in a[key].split(","):
                    u = part.strip().split(" ")[0]
                    if u:
                        self.images.append((u, a.get("alt", "") or "variant"))
        if tag in {"tr", "td", "th"} and "table" not in self.stack:
            self.stray_cells.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        self.tags.append(tag)
        if tag == "img":
            self.images.append((a.get("src", ""), a.get("alt", "")))


def collect(text: str) -> Collector:
    c = Collector()
    c.feed(text)
    return c


def md_images(text: str) -> list[tuple[str, str]]:
    """Markdown images: ![alt](src "title")"""
    out = []
    for m in re.finditer(r"!\[([^\]]*)\]\(\s*<?([^)\s]+)>?[^)]*\)", text):
        out.append((m.group(2), m.group(1)))
    return out


def md_links(text: str) -> list[str]:
    out = []
    for m in re.finditer(r"(?<!!)\[([^\]]*)\]\(\s*<?([^)\s]+)>?[^)]*\)", text):
        out.append(m.group(2))
    return out


def is_external(url: str) -> bool:
    return url.startswith(("https://", "http://"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-external", action="store_true")
    ap.add_argument(
        "--check-workflows",
        action="store_true",
        help="also parse .github/workflows/*.yml (needs PyYAML)",
    )
    args = ap.parse_args()

    if not README.exists():
        print(f"FAIL  {README} does not exist")
        return 1

    raw = README.read_text(encoding="utf-8")
    text = raw
    # Ignore fenced code and HTML comments: they legitimately contain example URLs.
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. size
    n = len(raw.encode("utf-8"))
    if n > MAX_BYTES:
        errors.append(f"README is {n:,} bytes, over the {MAX_BYTES:,} cap")
    else:
        print(f"ok    README size {n:,} bytes (cap {MAX_BYTES:,})")

    # 2. placeholders
    hits = [why for pat, why in PLACEHOLDERS if re.search(pat, text, re.I)]
    if hits:
        errors.append("placeholder text present: " + ", ".join(sorted(set(hits))))
    else:
        print("ok    no unfilled placeholders")

    # 3. banned tags
    c = collect(text)
    bad = sorted(set(c.tags) & BANNED_TAGS)
    if bad:
        errors.append("tags GitHub strips or forbids: " + ", ".join(bad))
    else:
        print("ok    no script/style/iframe/embed/form/video tags")

    # 4. stray table cells
    if c.stray_cells:
        errors.append(
            f"{len(c.stray_cells)} table cell(s) outside a <table> "
            f"({', '.join(sorted(set(c.stray_cells)))}); browsers drop these"
        )
    else:
        print("ok    no table cells outside a <table>")

    # 5. every image has alt text
    all_imgs = c.images + md_images(text)
    no_alt = [src for src, alt in all_imgs if not alt.strip()]
    if no_alt:
        errors.append(f"{len(no_alt)} image(s) without alt text: {no_alt[:3]}")
    else:
        print(f"ok    all {len(all_imgs)} images have alt text")

    # 6. relative images exist
    missing_img = []
    for src, _ in all_imgs:
        if src and not is_external(src) and not src.startswith("data:"):
            p = (REPO / src).resolve()
            if not p.exists():
                missing_img.append(src)
    if missing_img:
        errors.append(f"image path(s) not found: {missing_img[:5]}")
    elif any(not is_external(s) for s, _ in all_imgs if s):
        print("ok    relative image paths exist")
    else:
        print("ok    no relative image paths to check")

    # 7. relative links exist
    all_links = c.links + md_links(text)
    missing_link = []
    for href in all_links:
        if not href or is_external(href) or href.startswith(("#", "mailto:")):
            continue
        target = href.split("#", 1)[0]
        if not target:
            continue
        p = (REPO / target).resolve()
        if not (p.exists() or p.with_suffix(".md").exists()):
            missing_link.append(href)
    if missing_link:
        errors.append(f"link target(s) not found: {missing_link[:5]}")
    else:
        print("ok    relative link targets exist")

    # 8. email only as mailto, or as a readable alt label on a linked image
    alt_spans = [
        (m.start(), m.end()) for m in re.finditer(r'alt\s*=\s*"([^"]*)"', text)
    ]
    def in_alt(pos: int) -> bool:
        return any(s <= pos < e for s, e in alt_spans)

    bare = []
    for m in re.finditer(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        if text[max(0, m.start() - 7):m.start()] == "mailto:":
            continue
        # A readable address in alt text is deliberate: it is the label a screen
        # reader announces, and the image is wrapped in a mailto: link.
        if in_alt(m.start()):
            continue
        bare.append(m.group(0))
    if bare:
        errors.append(f"bare email address (not a mailto: link): {sorted(set(bare))}")
    else:
        print("ok    email addresses are mailto: links or alt labels")

    # 9. no vanity counters in display type
    big = re.findall(r"(?:font-size:\s*(\d+)px|>\s*(\d)\s*<)", text, re.I)
    huge = [a or b for a, b in big if int(a or b) >= 32]
    if huge:
        errors.append(f"possible display-size numbers (>=32): {huge[:5]}")
    else:
        print("ok    no display-size numbers")

    # 11. no nested HTML comments
    # A comment inside a comment closes the outer one early, and the remainder of
    # the block renders as visible body text on the profile page.
    depth = 0
    nested_at = []
    for m in re.finditer(r"<!--|-->", raw):
        if m.group(0) == "<!--":
            if depth > 0:
                nested_at.append(raw[: m.start()].count("\n") + 1)
            depth += 1
        else:
            depth = max(0, depth - 1)
    if depth != 0:
        errors.append(f"{depth} unclosed HTML comment(s)")
    if nested_at:
        errors.append(
            f"nested HTML comment(s) on line(s) {nested_at}; the outer comment "
            f"closes early and the rest renders as visible text"
        )
    if not nested_at and depth == 0:
        print("ok    HTML comments balanced, none nested")

    # 12. the self-generated graphics are referenced and documented
    #
    # The 3D theme is read out of .gitignore rather than hardcoded. It used to be
    # spelled out here, so renaming the tracked theme left this check asserting a
    # file the README had correctly stopped referencing -- a warning that trains
    # everyone to ignore warnings.
    if "github-contribution-grid-snake" in raw:
        print("ok    references self-generated graphic github-contribution-grid-snake*.svg")
    else:
        warnings.append("does not reference the contribution snake")

    gitignore = REPO / ".gitignore"
    themes = []
    if gitignore.exists():
        themes = re.findall(
            r"^!(profile-3d-contrib/[\w.-]+\.svg)\s*$", gitignore.read_text(), re.M
        )
    if not themes:
        warnings.append("no tracked 3D theme found in .gitignore")
    for theme in themes:
        if Path(theme).name in raw:
            print(f"ok    references self-generated graphic {theme}")
        else:
            warnings.append(f"does not reference the tracked 3D graphic {theme}")

    # 13. locally rendered cards exist, are referenced, and are not dead weight
    #
    # stats.svg and langs.svg are generated by scripts/render_stats.py and
    # committed, because the official hosts answer 503 and 402. That only helps
    # if they are actually on the page and actually present, so both halves are
    # checked. trophies.svg is exempt: the Work grid drops it when no award
    # threshold is met, and the test suite asserts the row and the card agree.
    for card in ("stats.svg", "langs.svg"):
        path = REPO / "assets" / card
        if not path.exists():
            errors.append(f"assets/{card} is referenced by the build but not committed")
        elif card not in raw:
            warnings.append(f"assets/{card} exists but the README does not reference it")
        else:
            print(f"ok    references committed card assets/{card}")

    # A card with a transparent background is invisible in GitHub's light theme.
    for card in ("stats.svg", "langs.svg", "trophies.svg"):
        path = REPO / "assets" / card
        if not path.exists():
            continue
        head = path.read_text(encoding="utf-8")[:400]
        if not re.search(r'<rect[^>]*fill="#', head):
            errors.append(f"assets/{card} has no opaque background rect; "
                          "cyan text on transparency is invisible in light theme")

    # 14. the design system is actually followed
    #
    # These are the rules the page is supposed to hold to. Each one exists
    # because the page broke it at least once, and because "looks consistent" is
    # not something a reader can check for you.
    ds_problems: list[str] = []

    # 14a. No GitHub social preview in the Work grid.
    # It is a white card, it stamps the profile photo onto every project, it
    # prints the repository description verbatim -- for helping-station-deu that
    # description is literally the string "x" -- and it cannot be themed. Three
    # of them on a dark page read as three holes.
    if "opengraph.githubassets.com" in raw:
        ds_problems.append(
            "Work section uses opengraph.githubassets.com: white cards that show "
            "the profile photo and the raw repository description. Use "
            "assets/work/*.svg"
        )

    # 14b. Every shields.io URL starts its query string with "?".
    # This is the bug that kept the whole badge row red. shields.io returns
    # HTTP 200 for an unparseable path with a body reading "404: badge not
    # found", so it is only catchable by looking at the path itself. "&style="
    # is a 200 that renders as a 404; "?style=" is the real thing.
    #
    # Only the FIRST separator matters. "&logo=" after a "?" is correct and is
    # how the working badges are written, so the test is whether an "&"
    # appears before any "?".
    amp_first = []
    for m in re.finditer(r"https://img\.shields\.io/([^\s\"')]+)", raw):
        path_and_query = m.group(1)
        amp = path_and_query.find("&")
        q = path_and_query.find("?")
        if amp != -1 and (q == -1 or amp < q):
            amp_first.append(m.group(0))
    if amp_first:
        ds_problems.append(
            f"{len(amp_first)} shields.io URL(s) start their query with '&' "
            "instead of '?':\n           "
            + "\n           ".join(sorted(set(amp_first))[:3])
            + "\n         each renders a 200 whose body says '404: badge not found'"
        )

    # 14c. No dash inside a shields.io label. The path is split on "-", so a
    # message containing one is unparseable. "Dong-eui%20University" is the
    # shape of this bug; it is why the university badge needed dashes turned
    # into spaces before rendering.
    for m in re.finditer(r"https://img\.shields\.io/badge/([^\s\"')]+)", raw):
        parts = m.group(1).split("-")
        if len(parts) < 3:
            ds_problems.append(
                f"shields.io badge path has no colour segment: {m.group(1)}")

    # 14d. One skillicons row, no orphan. Sixteen icons made skillicons emit a
    # 556-unit-tall viewBox instead of 256, because the `githubactions` badge is
    # two lines tall and drags the whole strip to double height. The rendered
    # result is a second line with one icon on it.
    icons = re.search(r"skillicons\.dev/icons\?i=([a-z0-9,+]+)", raw)
    if not icons:
        ds_problems.append("no skillicons row found")
    else:
        names = [n for n in icons.group(1).split(",") if n]
        if "githubactions" in names or "linux" in names:
            ds_problems.append(
                f"skillicons row includes a two-line badge ({names}), which "
                "doubles the strip height and leaves an orphan second line")
        if len(names) % 2 and len(names) > 1:
            ds_problems.append(
                f"skillicons row has an odd count ({len(names)}), so the last "
                "icon is an orphan")

    # 14e. The project thumbs exist. A featured project with no card is a hole
    # in the grid, which is the exact defect the social preview was replaced to
    # fix, moved rather than solved.
    thumbs = re.findall(r"assets/work/([A-Za-z0-9_.-]+\.svg)", raw)
    if not thumbs:
        ds_problems.append(
            "no assets/work/*.svg thumbnail is referenced; the Work grid would "
            "fall back to the social preview")
    for name in sorted(set(thumbs)):
        if not (REPO / "assets" / "work" / name).exists():
            errors.append(
                f"assets/work/{name} is referenced by README.md but not committed")

    # 14f. Every section carries the same label. The rhythm is the design; a
    # section that loses its label is the one that reads as bolted on.
    labels = re.findall(r"<code[^>]*>([A-Z][A-Z ]{1,11})</code>", raw)
    required = ["STATS", "NOW", "WORK", "STACK", "ACTIVITY", "NOTE", "CONTACT"]
    absent = [r for r in required if r not in labels]
    if absent:
        ds_problems.append(f"section label(s) missing: {', '.join(absent)}")

    # 14g. No `## ` headings. They render at a size that competes with the
    # banner, and the numbered "02 - Now" style read as a slide deck.
    headings = re.findall(r"^#{1,6} ", raw, re.M)
    if headings:
        ds_problems.append(
            f"{len(headings)} markdown heading(s) present; sections are labelled "
            "with <code> so every one is identical")

    # 14h. No terminal cosplay or placeholder personal URLs.
    for pat, why in (
        (r"user@\w+", "user@host prompt"),
        (r"\$\s", "shell prompt"),
        (r"```\s*(?:bash|sh|shell|console)", "fenced terminal block"),
        (r"cowsay", "cowsay"),
    ):
        if re.search(pat, raw, re.I | re.M):
            ds_problems.append(f"contains a {why}")

    if ds_problems:
        for p in ds_problems:
            errors.append(f"design system: {p}")
    else:
        print("ok    design system: no social previews, all badges well-formed, "
              "one icon row, all sections labelled")

    # 11. external reachability (non-fatal)
    #
    # A STATUS CODE IS NOT ENOUGH, and that is the whole reason this check
    # existed for months while every badge on the page was broken.
    #
    # shields.io answers an unparseable badge path with HTTP 200 and an SVG
    # whose aria-label is `404: badge not found`. The reader sees a red
    # placeholder. A check that only looks at the status reports the row as
    # healthy, which is exactly what happened: "all 31 external images returned
    # 200" was printed while eight badges rendered as 404s.
    #
    # So the body is read too, and the strings a service uses to say "I could
    # not make this" are matched explicitly.
    if args.check_external:
        urls = sorted({s for s, _ in all_imgs if is_external(s)})
        bad_urls = []
        for u in urls:
            try:
                req = urllib.request.Request(
                    u, method="GET", headers={"User-Agent": "profile-readme-validator"}
                )
                with urllib.request.urlopen(req, timeout=25) as r:
                    if r.status != 200:
                        bad_urls.append(f"{u} -> HTTP {r.status}")
                        continue
                    ctype = (r.headers.get("Content-Type") or "").split(";")[0]
                    # Only text-ish payloads are worth reading. A 2MB PNG has
                    # no aria-label and reading it would be pointless.
                    if ctype in ("image/svg+xml", "text/plain", "text/html",
                                 "application/json", "text/html; charset=utf-8"):
                        body = r.read(4096).decode("utf-8", "replace").lower()
                        for marker in ERROR_BODY_MARKERS:
                            if marker in body:
                                bad_urls.append(
                                    f"{u} -> HTTP 200 but body says {marker!r}")
                                break
            except urllib.error.HTTPError as e:
                bad_urls.append(f"{u} -> HTTP {e.code}")
            except Exception as e:  # noqa: BLE001
                bad_urls.append(f"{u} -> {type(e).__name__}")
        if bad_urls:
            warnings.append("external image(s) broken or unreachable:")
            for b in bad_urls:
                warnings.append("    " + b)
        else:
            print(f"ok    all {len(urls)} external images render (status and body)")

    # 13. workflow YAML parses
    if args.check_workflows:
        try:
            import yaml  # type: ignore
        except ImportError:
            warnings.append("PyYAML not installed; skipped workflow YAML check")
        else:
            wf_dir = REPO / ".github" / "workflows"
            bad = []
            files = sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml"))
            for f in files:
                try:
                    yaml.safe_load(f.read_text(encoding="utf-8"))
                except Exception as e:  # noqa: BLE001
                    bad.append(f"{f.name}: {e}")
            if bad:
                errors.append("workflow YAML does not parse: " + "; ".join(bad))
            else:
                print(f"ok    {len(files)} workflow file(s) parse as YAML")

    print()
    for w in warnings:
        print(f"WARN  {w}")
    if errors:
        for e in errors:
            print(f"FAIL  {e}")
        print(f"\n{len(errors)} problem(s) found.")
        return 1
    print("README validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
