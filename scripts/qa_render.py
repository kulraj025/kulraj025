#!/usr/bin/env python3
"""Raster-level visual QA for the generated scenes.

`qa_layout.py` checks geometry. This checks the *rendered pixels*: how much of
each canvas actually carries ink, where the content sits, and whether anything
is clipped or lost. It is the objective stand-in for eyeballing a render, which
matters because "too much unused dark space" and "the hero is not dominant" are
pixel questions, not geometry questions.

Requires rsvg-convert (librsvg). Run:  python scripts/qa_render.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import png_decode  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GENERATED = ROOT / "assets" / "generated"

# Ink is anything meaningfully brighter than the canvas. The page is #070B17
# (luminance ~7/255 in 8-bit terms), so 40 is a safe "this is content" floor
# while still ignoring the faintest grid and particle decoration.
INK_FLOOR = 40

# A scene is "empty" if less than this fraction of its pixels carry ink. The
# horizon scenes are mostly atmosphere by design, so the bar is deliberately low.
MIN_INK_RATIO = 0.012

# Content should not be crammed into a corner: the largest fully-empty band
# (rows or columns with no ink) should stay under this share of the dimension.
MAX_EMPTY_BAND = 0.30

# The hero must actually be the biggest thing on the page.
HERO_MIN_INK_RATIO = 0.05


def _svg_pixels(svg: Path, width: int) -> tuple[int, int, bytes]:
    """Rasterise an SVG to raw grayscale bytes.

    rsvg-convert can only emit png, pdf, ps, eps or svg, so the PNG it produces
    is decoded in-process. This version previously had two bugs stacked on top
    of each other: it asked rsvg-convert to convert its own PNG output to PPM
    (rsvg-convert reads SVG, not PNG), and it wrapped the whole thing in a
    Pillow try/except that happened to be satisfied on a developer machine and
    not in CI. Decoding with png_decode.py removes the round trip and the
    optional dependency, so the check behaves the same everywhere.
    """
    with tempfile.TemporaryDirectory() as td:
        png = Path(td) / "out.png"
        subprocess.run(
            ["rsvg-convert", "-w", str(width), "-o", str(png), str(svg)],
            check=True, capture_output=True)
        return png_decode.decode_grayscale(png)



def analyse(svg: Path) -> dict:
    w, h, px = _svg_pixels(svg, 1000)
    ink = 0
    cols_with_ink = [False] * w
    rows_with_ink = [False] * h
    brightest = 0
    for y in range(h):
        row = y * w
        for x in range(w):
            v = px[row + x]
            if v > brightest:
                brightest = v
            if v >= INK_FLOOR:
                ink += 1
                cols_with_ink[x] = True
                rows_with_ink[y] = True

    def longest_run(flags: list[bool]) -> int:
        best = run = 0
        for f in flags:
            run = 0 if f else run + 1
            best = max(best, run)
        return best

    # Tight bounding box of actual content.
    xs = [i for i, f in enumerate(cols_with_ink) if f]
    ys = [i for i, f in enumerate(rows_with_ink) if f]
    bbox = (xs[0], ys[0], xs[-1], ys[-1]) if xs and ys else None

    return {
        "w": w, "h": h,
        "ink_ratio": ink / float(w * h),
        "max_empty_col_band": longest_run(cols_with_ink) / w,
        "max_empty_row_band": longest_run(rows_with_ink) / h,
        "bbox": bbox,
        "brightest": brightest,
    }


def main() -> int:
    if not shutil.which("rsvg-convert"):
        print("rsvg-convert not available; skipping raster QA.")
        return 0

    files = sorted(GENERATED.rglob("*.svg"))
    if not files:
        print("No generated assets found.")
        return 1

    issues: list[str] = []
    # The divider is a deliberate hairline: it is a rule, not a scene, so dead
    # space above and below it is the point. Every other asset is a composition
    # and is held to the full-bleed standard.
    exempt_max_band = {"divider.svg"}
    print(f"{'asset':<34}{'ink%':>7}{'emptyCol':>10}{'emptyRow':>10}"
          f"{'peak':>7}  content bbox")
    print("-" * 92)
    for f in files:
        try:
            r = analyse(f)
        except Exception as exc:  # noqa: BLE001
            issues.append(f"{f.name}: could not rasterise: {exc}")
            continue
        rel = f.relative_to(GENERATED).as_posix()
        floor = HERO_MIN_INK_RATIO if f.name == "hero.svg" else MIN_INK_RATIO
        print(f"{rel:<34}{r['ink_ratio'] * 100:>6.1f}%"
              f"{r['max_empty_col_band'] * 100:>9.0f}%"
              f"{r['max_empty_row_band'] * 100:>9.0f}%"
              f"{r['brightest']:>7}  {r['bbox']}")

        if r["ink_ratio"] < floor:
            issues.append(
                f"{rel}: only {r['ink_ratio'] * 100:.1f}% of pixels carry ink "
                f"(floor {floor * 100:.0f}%) — reads as an empty box")
        if f.name not in exempt_max_band:
            if r["max_empty_col_band"] > MAX_EMPTY_BAND:
                issues.append(
                    f"{rel}: {r['max_empty_col_band'] * 100:.0f}% of the width is a "
                    f"single empty band — content is not spread across the canvas")
            if r["max_empty_row_band"] > MAX_EMPTY_BAND:
                issues.append(
                    f"{rel}: {r['max_empty_row_band'] * 100:.0f}% of the height is a "
                    f"single empty band — excessive dead vertical space")
        if r["bbox"] and r["bbox"][2] - r["bbox"][0] < r["w"] * 0.5:
            issues.append(
                f"{rel}: content spans only {(r['bbox'][2] - r['bbox'][0]) / r['w'] * 100:.0f}% "
                f"of the width — the composition is not full-bleed")
        if r["brightest"] < 120:
            issues.append(
                f"{rel}: brightest pixel is only {r['brightest']}/255 — "
                f"the scene has no real highlight")

    print()
    if issues:
        print(f"RASTER ISSUES FOUND ({len(issues)}):")
        for i in issues:
            print(f"  - {i}")
        return 1
    print("All scenes pass raster QA: ink coverage, no dead bands, full-bleed, real highlights.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
