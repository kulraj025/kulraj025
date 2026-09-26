#!/usr/bin/env python3
"""Geometric layout QA for the generated SVG assets.

This is an objective substitute for eyeballing renders. It parses each SVG and
checks for the failure modes that actually break these compositions:

1. Elements extending outside the viewBox (clipped / invisible content)
2. Text overflowing its container horizontally
3. Text baselines closer than their own line height (illegible overlap)
4. Text blocks horizontally overlapping each other
5. Missing width/height on the root <svg>
6. Unbalanced tags / malformed XML
7. Links pointing at empty or placeholder hrefs
8. Colour contrast of text against the panel background (WCAG AA)

Run:  python scripts/qa_layout.py
Exit: 0 = clean, 1 = issues found
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIRS = [ROOT / "assets" / "generated", ROOT / "assets" / "static"]

# Type-scale floor, in viewBox units. A README image is fluid, so a glyph at N
# units in a 1000-unit canvas renders at N*0.89 px on desktop and N*0.375 px on
# a 375px phone. The previous generation put information at 8-14 units, which
# is 3-5px on mobile: 92 of 168 text elements were illegible. Anything a reader
# must read now lives in native HTML instead, and this floor stops small text
# from creeping back into the SVGs.
MIN_FONT_SIZE = 18.0

# How many <animate*> / <animateTransform*> / <animateMotion*> elements one
# asset may contain. The previous hero carried 101, which is a slideshow rather
# than motion design; the brief asks for calm, legible motion.
MAX_ANIMATIONS = 40

# Elements that would make an asset non-renderable or unsafe on GitHub.
FORBIDDEN_TAGS = ("script", "iframe", "foreignObject", "video", "audio", "embed")

# Any href/src pointing outside the repository would break behind GitHub's
# image proxy and is rejected outright.
EXTERNAL_REF = re.compile(r"(?:href|src)\s*=\s*['\"](?:https?:)?//", re.I)

SVG_NS = "{http://www.w3.org/2000/svg}"

# Average glyph width as a fraction of font-size, per generic family.
MONO = 0.60
SANS = 0.52
BOLD_SANS = 0.56

# WCAG relative-luminance contrast helpers
def _srgb_to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _hex_to_rgb(value: str) -> tuple[float, float, float] | None:
    value = (value or "").strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", value)
    if not m:
        return None
    h = m.group(1)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (_srgb_to_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg: str, bg: str) -> float | None:
    a, b = _hex_to_rgb(fg), _hex_to_rgb(bg)
    if a is None or b is None:
        return None
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _local(tag: str) -> str:
    return tag.replace(SVG_NS, "")


def _num(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(m.group()) if m else default


def _text_width(el: ET.Element) -> float:
    size = _num(el.get("font-size"), 12.0)
    family = (el.get("font-family") or "").lower()
    weight = (el.get("font-weight") or "400").lower()
    if "mono" in family:
        ratio = MONO
    elif weight in ("bold", "600", "700", "800", "900"):
        ratio = BOLD_SANS
    else:
        ratio = SANS
    letter_spacing = _num(el.get("letter-spacing"), 0.0)
    return len((el.text or "")) * size * ratio + letter_spacing * len(el.text or "")


def _iter_shapes(root: ET.Element):
    """Yield (element, dx, dy) for rect/circle, honouring ancestor translate()."""
    def walk(el: ET.Element, dx: float, dy: float):
        for child in el:
            tag = _local(child.tag)
            ndx, ndy = dx, dy
            if tag == "g":
                m = re.search(r"translate\(\s*(-?[\d.]+)[ ,]+(-?[\d.]+)", child.get("transform") or "")
                if m:
                    ndx += float(m.group(1))
                    ndy += float(m.group(2))
                else:
                    m1 = re.search(r"translate\(\s*(-?[\d.]+)", child.get("transform") or "")
                    if m1:
                        ndx += float(m1.group(1))
            if tag in ("rect", "circle"):
                yield child, ndx, ndy
            yield from walk(child, ndx, ndy)

    yield from walk(root, 0.0, 0.0)


def _iter_texts(root: ET.Element):
    """Yield (element, dx, dy) applying accumulated ancestor translate().

    Most of these compositions position text inside <g transform="translate()">
    wrappers, so absolute coordinates require walking the transform chain.
    """
    def walk(el: ET.Element, dx: float, dy: float):
        for child in el:
            tag = _local(child.tag)
            ndx, ndy = dx, dy
            if tag == "g":
                tr = child.get("transform") or ""
                m = re.search(r"translate\(\s*(-?[\d.]+)[ ,]+(-?[\d.]+)", tr)
                if m:
                    ndx += float(m.group(1))
                    ndy += float(m.group(2))
                else:
                    m1 = re.search(r"translate\(\s*(-?[\d.]+)", tr)
                    if m1:
                        ndx += float(m1.group(1))
            if tag == "text" and (child.text or "").strip():
                yield child, dx, dy
            yield from walk(child, ndx, ndy)

    yield from walk(root, 0.0, 0.0)


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = path.as_posix()

    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        return [f"{rel}: malformed XML: {exc}"]

    if _local(root.tag) != "svg":
        return [f"{rel}: root element is <{_local(root.tag)}>, expected <svg>"]

    if not root.get("width") or not root.get("height"):
        issues.append(f"{rel}: root <svg> missing width/height attributes")

    # --- safety: nothing that GitHub will refuse to render ----------------
    for el in root.iter():
        tag = _local(el.tag)
        if tag in FORBIDDEN_TAGS:
            issues.append(f"{rel}: contains forbidden <{tag}> element")
    for el in root.iter():
        for attr in ("href", "xlink:href", "src"):
            val = el.get(attr) or ""
            if val and EXTERNAL_REF.search(f"{attr}='{val}'"):
                issues.append(f"{rel}: external reference {val!r} (must be self-contained)")

    # --- motion budget ---------------------------------------------------
    anims = sum(
        1 for el in root.iter()
        if _local(el.tag) in ("animate", "animateTransform", "animateMotion", "animateColor")
    )
    if anims > MAX_ANIMATIONS:
        issues.append(f"{rel}: {anims} animation elements exceeds budget of {MAX_ANIMATIONS}")
    # Static fallbacks are static by definition; only generated assets animate.
    if anims == 0 and "assets/generated" in rel:
        issues.append(f"{rel}: no animation elements (generated assets must animate)")

    # --- type scale ------------------------------------------------------
    smallest = None
    for t, _dx, _dy in _iter_texts(root):
        size = _num(t.get("font-size"), 0.0)
        if size <= 0:
            continue
        if smallest is None or size < smallest:
            smallest = size
        if size < MIN_FONT_SIZE:
            issues.append(
                f"{rel}: font-size={size:g} is below the {MIN_FONT_SIZE:g} floor; "
                f"it renders at {size * 0.375:.1f}px on a 375px phone. "
                f"Move the text to native HTML in render_readme.py instead."
            )

    vb = root.get("viewBox")
    if not vb:
        issues.append(f"{rel}: missing viewBox")
        return issues
    try:
        vx, vy, vw, vh = (float(x) for x in re.split(r"[ ,]+", vb.strip()))
    except ValueError:
        issues.append(f"{rel}: unparseable viewBox {vb!r}")
        return issues

    # 1. empty / placeholder hrefs
    for a in root.iter(f"{SVG_NS}a"):
        href = a.get("href") or a.get("xlink:href") or ""
        if not href.strip() or href.strip() in ("#", "mailto:", "https://", "http://"):
            issues.append(f"{rel}: <a> with empty/placeholder href {href!r}")

    # Collect solid-fill rects so text contrast can be measured against the
    # surface it actually sits on (buttons, chips, cards) rather than the page.
    surfaces: list[tuple[float, float, float, float, str]] = []
    for el in root.iter():
        if _local(el.tag) != "rect":
            continue
        fill = (el.get("fill") or "").strip()
        if not fill.startswith("#") or fill in ("none",):
            continue
        x, y = _num(el.get("x")), _num(el.get("y"))
        w, h = _num(el.get("width")), _num(el.get("height"))
        if w > 0 and h > 0:
            surfaces.append((x, y, x + w, y + h, fill))

    def bg_for_text(x0: float, y0: float, x1: float, y1: float, default: str) -> str:
        """Smallest solid rect containing the text box wins; else the page bg."""
        best, best_area = None, None
        for sx0, sy0, sx1, sy1, fill in surfaces:
            if sx0 - 1 <= x0 and sy0 - 1 <= y0 and sx1 + 1 >= x1 and sy1 + 1 >= y1:
                area = (sx1 - sx0) * (sy1 - sy0)
                if best_area is None or area < best_area:
                    best, best_area = fill, area
        return best or default

    # 2. geometry bounds for shapes.
    # A few px of bleed is deliberate (edge particles, glow rings) and the root
    # sets overflow='visible'; only flag substantial escapes.
    BLEED_TOLERANCE = 6.0
    for el, dx, dy in _iter_shapes(root):
        tag = _local(el.tag)
        # A shape driven by <animateMotion> has no meaningful x/y: its position
        # comes from the motion path, and it is meant to travel off and back
        # on to the canvas. Static bounds checking would only produce noise.
        if any(_local(c.tag) == "animateMotion" for c in el):
            continue
        if _num(el.get("opacity"), 1.0) < 0.5 and el.get("opacity") is not None:
            continue  # decorative, low-opacity
        if tag == "rect":
            x, y = _num(el.get("x")) + dx, _num(el.get("y")) + dy
            w, h = _num(el.get("width")), _num(el.get("height"))
            if w and x < vx - BLEED_TOLERANCE:
                issues.append(f"{rel}: rect x={x} w={w} escapes left edge")
            if w and x + w > vx + vw + BLEED_TOLERANCE:
                issues.append(f"{rel}: rect x={x} w={w} escapes right edge")
            if h and y < vy - BLEED_TOLERANCE:
                issues.append(f"{rel}: rect y={y} h={h} escapes top edge")
            if h and y + h > vy + vh + BLEED_TOLERANCE:
                issues.append(f"{rel}: rect y={y} h={h} escapes bottom edge")
        elif tag == "circle":
            cx, cy, r = (
                _num(el.get("cx")) + dx,
                _num(el.get("cy")) + dy,
                _num(el.get("r")),
            )
            if cx - r < vx - BLEED_TOLERANCE or cx + r > vx + vw + BLEED_TOLERANCE:
                issues.append(f"{rel}: circle cx={cx} r={r} escapes horizontal bounds")
            if cy - r < vy - BLEED_TOLERANCE or cy + r > vy + vh + BLEED_TOLERANCE:
                issues.append(f"{rel}: circle cy={cy} r={r} escapes vertical bounds")

    # 3. text bounds + collisions
    boxes: list[tuple[float, float, float, float, str, float]] = []
    for t, dx, dy in _iter_texts(root):
        label = (t.text or "").strip()
        size = _num(t.get("font-size"), 12.0)
        x, y = _num(t.get("x")) + dx, _num(t.get("y")) + dy
        w = _text_width(t)
        anchor = (t.get("text-anchor") or "start").lower()

        if anchor == "middle":
            x0, x1 = x - w / 2, x + w / 2
        elif anchor == "end":
            x0, x1 = x - w, x
        else:
            x0, x1 = x, x + w

        if x0 < vx - 1:
            issues.append(f"{rel}: text {label!r} starts left of viewBox (x0={x0:.1f} < {vx})")
        if x1 > vx + vw + 1:
            issues.append(
                f"{rel}: text {label!r} overflows right edge "
                f"(x1={x1:.1f} > {vx + vw}); shorten it or reduce font-size"
            )
        if y < vy or y > vy + vh:
            issues.append(f"{rel}: text {label!r} baseline y={y} outside viewBox height {vh}")
        boxes.append((x0, y - size * 0.8, x1, y + size * 0.25, label, size))

    # 4. pairwise overlap (text vs text)
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            ax0, ay0, ax1, ay1, alabel, asize = boxes[i]
            bx0, by0, bx1, by1, blabel, bsize = boxes[j]
            h_overlap = min(ax1, bx1) - max(ax0, bx0)
            v_overlap = min(ay1, by1) - max(ay0, by0)
            if h_overlap > 1.5 and v_overlap > 1.5:
                issues.append(
                    f"{rel}: text overlap {alabel!r} <-> {blabel!r} "
                    f"(h={h_overlap:.1f}px v={v_overlap:.1f}px)"
                )

    # 5. contrast of text against the declared panel background
    bg_default = "#070B17"
    src = path.read_text(encoding="utf-8")
    m = re.search(
        r"<rect[^>]*width='%d'[^>]*height='%d'" % (int(vw), int(vh)), src
    )
    if m:
        fill = re.search(r"fill='(#[0-9a-fA-F]{6})'", m.group())
        if fill:
            bg_default = fill.group(1)

    for t, dx, dy in _iter_texts(root):
        fill = t.get("fill") or ""
        size = _num(t.get("font-size"), 12.0)
        if not fill.startswith("#"):
            if fill.strip() and fill.strip() != "none" and not fill.startswith("url("):
                issues.append(
                    f"{rel}: invalid text fill {(t.text or '').strip()!r} -> fill={fill!r} "
                    f"(must be a #hex colour or url(#gradient))"
                )
            continue  # url(#gradient) fills can't be resolved statically
        x, y = _num(t.get("x")) + dx, _num(t.get("y")) + dy
        w = _text_width(t)
        anchor = (t.get("text-anchor") or "start").lower()
        if anchor == "middle":
            x0, x1 = x - w / 2, x + w / 2
        elif anchor == "end":
            x0, x1 = x - w, x
        else:
            x0, x1 = x, x + w
        bg = bg_for_text(x0, y - size * 0.8, x1, y + size * 0.25, bg_default)
        ratio = _contrast(fill, bg)
        if ratio is None:
            continue
        large = size >= 18 or (size >= 14 and _num(t.get("font-weight"), 400) >= 700)
        threshold = 3.0 if large else 4.5
        if ratio < threshold:
            issues.append(
                f"{rel}: low contrast {(t.text or '').strip()!r} {fill} on {bg} "
                f"= {ratio:.2f}:1 (needs {threshold}:1)"
            )

    return issues


def main() -> int:
    files: list[Path] = []
    for d in ASSET_DIRS:
        if d.exists():
            files.extend(sorted(d.glob("*.svg")))
            # project artwork lives one level down, in project-art/
            for sub in sorted(d.glob("*/*.svg")):
                files.append(sub)

    if not files:
        print("No SVG assets found.")
        return 1

    all_issues: list[str] = []
    for f in files:
        all_issues.extend(check_file(f))

    print(f"Checked {len(files)} SVG assets across {len(ASSET_DIRS)} directories.")
    print(f"Type-scale floor: font-size >= {MIN_FONT_SIZE:g} viewBox units "
          f"(= {MIN_FONT_SIZE * 0.89:.1f}px desktop, {MIN_FONT_SIZE * 0.375:.1f}px mobile).\n")
    if all_issues:
        print(f"LAYOUT ISSUES FOUND ({len(all_issues)}):")
        for i in all_issues:
            print(f"  - {i}")
        return 1
    print("All assets pass layout QA: in-bounds, no text collisions, AA contrast, "
          "type scale, motion budget, self-contained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
