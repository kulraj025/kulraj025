#!/usr/bin/env python3
"""Prove that no glyph in an SVG can be clipped by its own canvas.

The bug this guards against is real: readme-typing-svg concatenates every entry
in `lines` into ONE comma-joined <textPath> and centres it on the path origin, so
any multi-line request puts most of the string off-canvas. The visible result was
a heading reading "ilding campus products and XAI". Measuring beats squinting, so
this renders the text layer alone and reports the true ink margins.

Method: strip the decorative layer (gradients, hairlines, glow) so only glyphs
remain, render on black, then find the leftmost/rightmost lit column. Anything
touching column 0 or the last column is a crop.

Usage: python3 scripts/check_svg_text_fits.py [svg ...]
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from png_decode import decode_grayscale  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# A glyph is "lit" if it is clearly brighter than the darkest panel we use.
LIT_THRESHOLD = 60
# Slack we insist on, in px at 1x. The brief asks for padding so letters cannot
# clip; a couple of px of ink would technically pass a 0px test but still look tight.
REQUIRED_MARGIN_PX = 8


def text_layer(svg: str) -> tuple[str, int, int]:
    """Return (svg with only the text layer, width, height) for ink measurement."""
    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    if not vb:
        raise SystemExit("no viewBox")
    width, height = int(vb.group(1)), int(vb.group(2))

    # Every <text>...</text>, with the presentation attributes that place it. The
    # wipes are dropped: the base state already renders each line at full width,
    # which is the widest this file can ever be and so the worst case to measure.
    # Inherited presentation attributes live on a wrapping <g> in these files, and
    # dropping it leaves the glyphs black-on-black. Carry the font-* set forward.
    inherited = ""
    for g in re.finditer(r"<g\b([^>]*)>", svg):
        keep = re.findall(r'\s(font-[a-z]+|fill|text-anchor)="[^"]*"', g.group(1))
        if keep:
            inherited = g.group(1)
            break

    body = []
    for m in re.finditer(r"<text\b(.*?)>(.*?)</text>", svg, re.S):
        attrs = re.sub(r'\s*clip-path="[^"]*"', "", m.group(1))
        body.append(f"<text{attrs}>{m.group(2)}</text>")
    if not body:
        raise SystemExit("no <text> elements found")

    out = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
        f'<rect width="{width}" height="{height}" fill="#000"/>'
        f"<g{inherited}>"
        + "".join(body)
        + "</g></svg>"
    )
    return out, width, height


def pinned_extent(svg: str, width: int) -> tuple[int, int] | None:
    """Widest horizontal extent a browser will draw, honouring textLength.

    rsvg ignores textLength, so the rendered measurement only covers the natural
    metrics. In a browser textLength is authoritative and the run occupies exactly
    textLength, so check that case too. Returns the tightest (left, right) pair.
    """
    tightest: tuple[int, int] | None = None
    for m in re.finditer(r"<text\b([^>]*)>", svg):
        attrs = m.group(1)
        x = re.search(r'\sx="([\d.]+)"', attrs)
        tl = re.search(r'textLength="([\d.]+)"', attrs)
        if not (x and tl):
            continue
        cx, length = float(x.group(1)), float(tl.group(1))
        left, right = cx - length / 2, width - (cx + length / 2)
        if tightest is None or left < tightest[0] or right < tightest[1]:
            tightest = (left, right)
    return tightest


def lit_columns(gray: bytes, width: int, height: int) -> list[bool]:
    """One flag per column: does it contain a lit pixel?"""
    cols = bytearray(width)
    for y in range(height):
        row = y * width
        for x in range(width):
            if not cols[x] and gray[row + x] > LIT_THRESHOLD:
                cols[x] = 1
    return [bool(c) for c in cols]


def check(path: Path) -> bool:
    svg = path.read_text()
    isolated, width, height = text_layer(svg)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "t.svg").write_text(isolated)
        subprocess.run(
            ["rsvg-convert", "-w", str(width), "-h", str(height),
             str(tmp / "t.svg"), "-o", str(tmp / "t.png")],
            check=True, capture_output=True,
        )
        # Decoded with the stdlib zlib reader rather than ImageMagick. Shelling out
        # to `convert` made this check pass on a developer machine and fail in CI,
        # because only librsvg2-bin was installed on the runner. That is the same
        # trap png_decode.py documents, so it gets no second chance here.
        w, h, gray = decode_grayscale(tmp / "t.png")

    if (w, h) != (width, height):
        raise SystemExit(f"rasterised {w}x{h}, expected {width}x{height}")

    cols = lit_columns(gray, width, height)
    if not any(cols):
        print(f"FAIL {path.name}: no glyphs rendered at all")
        return False

    first = cols.index(True)
    last = len(cols) - 1 - cols[::-1].index(True)
    left, right = first, width - 1 - last

    ok = left >= REQUIRED_MARGIN_PX and right >= REQUIRED_MARGIN_PX
    print(
        f"{'ok  ' if ok else 'FAIL'} {path.name}: canvas {width}px, "
        f"natural ink x={first}..{last} (left={left}px right={right}px)"
    )

    pinned = pinned_extent(svg, width)
    if pinned:
        pl, pr = pinned
        pok = pl >= REQUIRED_MARGIN_PX and pr >= REQUIRED_MARGIN_PX
        ok = ok and pok
        print(
            f"     {'ok  ' if pok else 'FAIL'} textLength-pinned extent "
            f"x={pl:.0f}..{width - pr:.0f} (left={pl:.0f}px right={pr:.0f}px)"
        )
    else:
        print("     warn  no textLength pinning; width depends entirely on the font")

    return ok


def main(argv: list[str]) -> int:
    targets = [Path(a) for a in argv[1:]] or sorted((ROOT / "assets").glob("*.svg"))
    targets = [t for t in targets if t.is_file()]
    if not targets:
        print("no SVG files to check")
        return 0
    results = [check(t) for t in targets]
    failed = results.count(False)
    print()
    print("text-fit check passed." if not failed else f"{failed} file(s) would crop.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
