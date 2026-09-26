#!/usr/bin/env python3
"""Render the per-project thumbnail cards in assets/work/.

WHY NOT THE GITHUB SOCIAL PREVIEW
--------------------------------
`opengraph.githubassets.com/1/<owner>/<repo>` is a white card. It shows the
account's profile photo, prints the repository description verbatim -- and for
`helping-station-deu` that description is literally the string "x" -- and it
cannot be themed. Three of them in a row on a dark page read as three holes.

These are ours instead, and they are in the same visual language as
`assets/banner.svg`: the same near-black gradient, the same faint grid, the same
cyan, the same monospace. Nothing about the person is in them, deliberately -- a
project card should show the project.

TWO WIDTHS, ONE LANGUAGE
------------------------
The first featured project spans the full grid row; the rest pair up. So the
first card is 900 wide and the others 480. Same height, same palette, same type
sizes, same grid pitch -- the only difference is that the featured card is laid
out in two columns so the extra width is filled rather than left as a dead band.

That last point is not cosmetic. `qa_render.py` fails a scene whose longest
empty column run exceeds 30% of its width, and a 480-wide card dropped into a
900-wide row is exactly that: two thirds of nothing. A wide card therefore
carries the repository name on the right, which is also the one piece of
information the card can add that the cell below it does not already say.

Every `<text>` is pinned with `textLength`, so the advance width of a run is
fixed no matter which font the viewer has and a glyph cannot crop. This is the
same rule `assets/banner.svg` and `assets/typing.svg` follow.

MOTION
------
One slow scan line and one breathing status dot per card, both SMIL, both
subtle. `MAX_ANIMATIONS_PER_ASSET` in `design.py` is the budget and two
animations per card is well inside it. SMIL is used rather than CSS because
GitHub strips `<style>` but does not strip `<animate>` in a served SVG.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from design import MAX_ANIMATIONS_PER_ASSET  # noqa: E402
from metrics import load_config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "work"

# Same palette as assets/banner.svg. Kept as literals rather than imported so
# this file cannot drift from the banner by editing design.py alone.
BG_FROM = "#0B1220"
BG_TO = "#0A1018"
GRID = "#16233A"
CYAN = "#22D3EE"
CYAN_DIM = "#0E7490"
TEXT = "#E2E8F0"
MUTE = "#94A3B8"

H = 200
NARROW = 480      # a cell in a two-up row
WIDE = 900        # the full-width featured row
PAD = 40          # left/right inset, matching assets/banner.svg's language
GRID_PITCH = 40

FONT = "'JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif"

# One hue per project, used only for the status dot and the rule under the
# title, so the three cards are distinguishable at a glance without breaking
# the cyan system. Muted on purpose: these are accents, not headings.
DOT = {"skillbridge": "#A78BFA",
       "helping-station-deu": "#34D399",
       "campus_connect_x_v2": "#F59E0B"}

# Widest a single-column title may be, so a long project name on a narrow card
# has room and a short one on a wide card does not become a stretched smear.
TITLE_MAX = 250
REPO_MAX = 300


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, *, size=12, fill=TEXT, weight=400, anchor="start",
         family=SANS, length=None) -> str:
    """A single <text>, optionally pinned with textLength.

    textLength is what makes cropping structurally impossible rather than
    unlikely. Without it a run is as wide as the font happens to make it, and a
    viewer without the intended font gets a different width.
    """
    pin = f' textLength="{length}" lengthAdjust="spacingAndGlyphs"' if length else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"'
            f'{pin}>{esc(s)}</text>')


def _background(w: int) -> list[str]:
    """Opaque base plus the faint grid, drawn to the card edge on purpose.

    A dead margin would read as an unfinished panel, and the base has to be
    opaque: cyan on transparency is invisible in GitHub's light theme, which is
    where a lot of readers arrive.
    """
    p = [f'<rect width="{w}" height="{H}" rx="10" fill="url(#bg)"/>']
    for x in range(GRID_PITCH, w, GRID_PITCH):
        p.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{GRID}" '
                 f'stroke-width="1" opacity="0.55"/>')
    for y in range(GRID_PITCH, H, GRID_PITCH):
        p.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{GRID}" '
                 f'stroke-width="1" opacity="0.55"/>')
    p.append(f'<rect x="0.75" y="0.75" width="{w - 1.5}" height="{H - 1.5}" rx="10" '
             f'fill="none" stroke="{CYAN_DIM}" stroke-width="1.5" opacity="0.55"/>')
    return p


def card(name: str, title: str, subtitle: str, wide: bool = False) -> str:
    w = WIDE if wide else NARROW
    dot = DOT.get(name, CYAN)

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" '
        f'width="{w}" height="{H}" role="img" '
        f'aria-label="{esc(title)} project card: {esc(subtitle.lower())}">'
    )
    p.append(f"<title>{esc(title)} — {esc(subtitle.title())}</title>")
    p.append(f"<desc>Project card for {esc(title)}: {esc(subtitle.lower())}.</desc>")

    p.append("<defs>")
    p.append('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
             f'<stop offset="0" stop-color="{BG_FROM}"/>'
             f'<stop offset="1" stop-color="{BG_TO}"/></linearGradient>')
    # The scan line fades out at both ends so it never shows a hard edge.
    p.append('<linearGradient id="scan" x1="0" y1="0" x2="1" y2="0">'
             '<stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>'
             '<stop offset="0.5" stop-color="#22D3EE" stop-opacity="0.5"/>'
             '<stop offset="1" stop-color="#22D3EE" stop-opacity="0"/>'
             '</linearGradient>')
    p.append("</defs>")

    p.extend(_background(w))

    # Breathing status dot: 4s, values 0.35 -> 1 -> 0.35. keyTimes must run
    # 0 -> 1 or Chrome discards the whole animation, and the card then simply
    # looks static with nothing reporting an error.
    p.append(f'<circle cx="{PAD}" cy="46" r="5" fill="{dot}">'
             f'<animate attributeName="opacity" values="0.35;1;0.35" dur="4s" '
             f'repeatCount="indefinite" keyTimes="0;0.5;1"/></circle>')
    p.append(text(PAD + 16, 51, "ONLINE" if subtitle == "DEPLOYED" else "BUILDING",
                  size=10, fill=MUTE, weight=600, family=FONT, length=62))

    # Title, rule, subtitle. A wide card has room for the full name; a narrow
    # one is capped so a long name cannot push into the right-hand column.
    p.append(text(PAD, 112, title, size=26, fill=CYAN, weight=700,
                  length=TITLE_MAX if not wide else min(TITLE_MAX, w - PAD * 2 - 60)))
    p.append(f'<rect x="{PAD}" y="128" width="64" height="2" fill="{dot}" opacity="0.9"/>')
    p.append(text(PAD, 156, subtitle, size=12, fill=TEXT, weight=600, family=FONT,
                  length=150))

    if wide:
        # The second column. Without it the right third of a 900px card is an
        # empty band, which is both a dead area and the thing that makes a wide
        # card look like a narrow card that was stretched by accident.
        rx = w - PAD
        p.append(f'<line x1="{rx - REPO_MAX - 24}" y1="40" x2="{rx - REPO_MAX - 24}" '
                 f'y2="160" stroke="{CYAN_DIM}" stroke-width="1" opacity="0.5"/>')
        p.append(text(rx, 96, "REPOSITORY", size=10, fill=MUTE, weight=600,
                      anchor="end", family=FONT, length=REPO_MAX))
        p.append(text(rx, 124, f"kulraj025/{name}", size=14, fill=TEXT, weight=600,
                      anchor="end", family=FONT, length=REPO_MAX))

    # One slow scan, 7s, clipped to the card. The clipPath is what stops it
    # drawing outside the rounded rect and over the page background.
    p.append(f'<clipPath id="clip"><rect width="{w}" height="{H}" rx="10"/></clipPath>')
    p.append('<g clip-path="url(#clip)">')
    p.append(f'<rect x="-120" y="0" width="120" height="{H}" fill="url(#scan)">'
             f'<animate attributeName="x" values="-120;{w}" dur="7s" '
             f'repeatCount="indefinite" keyTimes="0;1"/></rect>')
    p.append("</g>")

    p.append("</svg>")
    svg = "\n  ".join(p)
    n = svg.count("<animate ")
    if n > MAX_ANIMATIONS_PER_ASSET:
        raise SystemExit(f"{name}: {n} animations exceeds the budget "
                         f"of {MAX_ANIMATIONS_PER_ASSET}")
    return svg + "\n"


def build() -> dict[str, str]:
    """One card per featured project, in config order.

    The first one is the wide one, because the grid gives the first project a
    full row. Both are driven from the same list, so adding a fourth project
    keeps working: the grid pairs the remainder and the artwork follows.
    """
    cfg = load_config()
    hidden = set(cfg["projects"].get("hidden_repositories") or [])
    featured = [p for p in cfg["projects"]["featured"] if p["name"] not in hidden]
    return {
        f"{pr['name']}.svg": card(pr["name"], pr["title"], pr["subtitle"],
                                  wide=(i == 0))
        for i, pr in enumerate(featured)
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render assets/work/*.svg")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if a committed thumb is missing or stale")
    args = ap.parse_args(argv)

    files = build()
    if not files:
        print("FAIL  no featured projects to render")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    for name, content in sorted(files.items()):
        path = OUT / name
        if args.check:
            if not path.exists():
                problems.append(f"assets/work/{name} is missing")
            elif path.read_text(encoding="utf-8") != content:
                problems.append(f"assets/work/{name} is stale")
            continue
        path.write_text(content, encoding="utf-8")
        print(f"wrote assets/work/{name} ({len(content.encode()):,} bytes)")

    if args.check:
        # A committed thumb that no longer corresponds to a featured project is
        # clutter, and clutter in a design system is a defect.
        for existing in sorted(OUT.glob("*.svg")):
            if existing.name not in files:
                problems.append(
                    f"assets/work/{existing.name} has no featured project; "
                    f"delete it")
        if problems:
            print(f"FAIL  {len(problems)} problem(s) with the project thumbs:")
            for p in problems:
                print(f"      - {p}")
            print("      run: python3 scripts/render_work_thumbs.py")
            return 1
        print(f"ok    {len(files)} project thumb(s) current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
