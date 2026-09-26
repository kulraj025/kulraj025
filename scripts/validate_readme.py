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

    # 11. external reachability (non-fatal)
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
            except urllib.error.HTTPError as e:
                bad_urls.append(f"{u} -> HTTP {e.code}")
            except Exception as e:  # noqa: BLE001
                bad_urls.append(f"{u} -> {type(e).__name__}")
        if bad_urls:
            warnings.append("external image(s) unreachable:")
            for b in bad_urls:
                warnings.append("    " + b)
        else:
            print(f"ok    all {len(urls)} external images returned 200")

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
