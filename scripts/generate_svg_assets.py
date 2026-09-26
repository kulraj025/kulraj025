#!/usr/bin/env python3
"""KULRAJ / DIGITAL HORIZON — SVG scene generation.

Every scene is generated from a single `_build_*` implementation behind an
`animated` flag. Animated and static variants therefore share one layout
implementation and cannot drift apart.

TEXT POLICY (enforced by scripts/qa_layout.py)
----------------------------------------------
A README image is fluid, so every glyph inside a full-width SVG scales with the
viewport: a 10px label in a 1000-unit canvas renders at 3.8px on a phone. The
previous generation put all of its information in SVGs and 92 of 168 text
elements were illegible.

So: SVG carries display type that survives scaling (>= 21 units) and graphics.
Anything a reader must actually read lives in native HTML in the README. See
scripts/design.py for the measurements.
"""
from __future__ import annotations

import hashlib
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import design as D
from design import (
    CANVAS_W, GUTTER, CONTENT_W, MIN_SVG_FONT_SIZE, PALETTE, ACCENT_RAMP,
    LANG_HEX, FONT_DISPLAY, FONT_MONO, DUR, AA_BODY, AA_LARGE,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets" / "generated"
STATIC_DIR = ROOT / "assets" / "static"

P = PALETTE
DUR_S = DUR


# ---------------------------------------------------------------------------
# Colour utilities (kept: shared with scripts/qa_layout.py)
# ---------------------------------------------------------------------------

def _hex_to_rgb(value: str) -> tuple[float, float, float] | None:
    v = (value or "").strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6:
        return None
    try:
        return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return None


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02X}" for c in rgb)


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    def ch(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG 2.1 contrast ratio between two hex colours."""
    a, b = _hex_to_rgb(fg), _hex_to_rgb(bg)
    if a is None or b is None:
        return 0.0
    la, lb = _relative_luminance(a), _relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def ensure_contrast(color: str, bg: str, min_ratio: float = AA_BODY) -> str:
    """Lighten `color` until it reaches `min_ratio` against `bg`.

    GitHub's language colours are designed for a light background. On the
    #070B17 canvas several of them (C++ #006699 at 2.6:1) are unreadable, so
    every language colour is passed through here before it reaches a glyph.
    """
    rgb = _hex_to_rgb(color)
    if rgb is None:
        return P["text"]
    if contrast_ratio(color, bg) >= min_ratio:
        return color
    for step in range(1, 101):
        t = step / 100
        lifted = tuple(c + (1.0 - c) * t for c in rgb)
        if contrast_ratio(_rgb_to_hex(lifted), bg) >= min_ratio:
            return _rgb_to_hex(lifted)
    return "#FFFFFF"


def _lang_color(lang: str) -> str:
    """Readable variant of a language's canonical GitHub colour."""
    base = LANG_HEX.get((lang or "").strip())
    if not base:
        return P["cyan"]
    return ensure_contrast(base, P["bg"], AA_BODY)


def _esc(value: object) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))


def fit_text(text: str, max_px: float, font_size: float, *, mono: bool = False,
             max_lines: int = 2) -> list[str]:
    """Wrap `text` to fit `max_px` per line, ellipsising if it cannot fit.

    Uses the same average-glyph-width model as scripts/qa_layout.py so the
    generated layout and the layout QA agree on what overflows.
    """
    ratio = 0.60 if mono else 0.52
    budget = max(1, int(max_px / (font_size * ratio)))
    words = (text or "").split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    consumed_all = True
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= budget:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        if len(lines) >= max_lines:
            consumed_all = False
            break
        while len(word) > budget and len(lines) < max_lines:
            lines.append(word[: budget - 1] + "\u2026")
            word = word[budget - 1:]
        current = word
    if current and len(lines) < max_lines:
        lines.append(current)
    else:
        consumed_all = consumed_all and not current
    lines = lines[:max_lines]
    if not consumed_all and lines:
        last = lines[-1]
        if len(last) >= budget:
            last = last[: budget - 1].rstrip() + "\u2026"
        else:
            last = last + "\u2026"
        lines[-1] = last
    return lines


def _seeded(name: str) -> random.Random:
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:12], 16))


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (name or "project")).strip("-").lower()
    return slug or "project"


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def _hdr(w: int, h: int, label: str) -> str:
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
        f"viewBox='0 0 {w} {h}' role='img' aria-label='{_esc(label)}' "
        f"preserveAspectRatio='xMidYMid meet'>"
    )


def _text(x: float, y: float, content: str, size: float, *, fill: str,
          weight: str = "400", mono: bool = False, tracking: float = 0.0,
          anchor: str = "start", opacity: float | None = None) -> str:
    """A single line of SVG text. `size` is clamped to the type-scale floor."""
    size = max(MIN_SVG_FONT_SIZE, round(size, 1))
    fam = FONT_MONO if mono else FONT_DISPLAY
    extra = f" letter-spacing='{tracking}'" if tracking else ""
    op = f" opacity='{opacity}'" if opacity is not None else ""
    return (f"<text x='{round(x, 1)}' y='{round(y, 1)}' font-size='{size}' "
            f"font-weight='{weight}' fill='{fill}'{extra}{op} "
            f"font-family=\"{fam}\" text-anchor='{anchor}'>{_esc(content)}</text>")


def _sine_path(x0: float, x1: float, y: float, amp: float, cycles: float,
               phase: float = 0.0, samples: int = 160) -> str:
    """A smooth sine trace, used for waves and signal envelopes."""
    pts = []
    for i in range(samples + 1):
        t = i / samples
        x = x0 + (x1 - x0) * t
        yy = y + amp * math.sin(2 * math.pi * cycles * t + phase)
        pts.append(f"{round(x, 1)},{round(yy, 1)}")
    return "M" + " L".join(pts)


def _starfield(w: int, y0: int, y1: int, count: int, seed: int,
               *, animated: bool, color: str = P["cyan"]) -> str:
    """Ambient particles, batched into a few groups so the animation count
    stays in the single digits instead of one per particle."""
    rng = random.Random(seed)
    groups: list[list[str]] = [[] for _ in range(4)]
    for i in range(count):
        x = round(rng.uniform(GUTTER * 0.4, w - GUTTER * 0.4), 1)
        y = round(rng.uniform(y0, y1), 1)
        r = round(rng.uniform(0.7, 2.1), 2)
        op = round(rng.uniform(0.18, 0.62), 2)
        groups[i % 4].append(
            f"<circle cx='{x}' cy='{y}' r='{r}' fill='{color}' opacity='{op}'/>")
    out = []
    for gi, dots in enumerate(groups):
        if not dots:
            continue
        anim = ""
        if animated:
            anim = (f"<animate attributeName='opacity' "
                    f"values='0.55;1;0.55' dur='{DUR_S['swell'] + gi * 1.7}s' "
                    f"begin='{gi * 0.9}s' repeatCount='indefinite'/>")
        out.append(f"<g>{''.join(dots)}{anim}</g>")
    return "".join(out)


def _contours(w: int, y0: int, y1: int, count: int, seed: int,
              color: str, opacity: float) -> str:
    """Abstract technical map lines: meandering traces that suggest a
    coastline or topography without depicting a real place."""
    rng = random.Random(seed)
    out = []
    for i in range(count):
        base = y0 + (y1 - y0) * (i + 0.5) / count + rng.uniform(-12, 12)
        amp = rng.uniform(9, 26)
        cycles = rng.uniform(1.1, 2.3)
        phase = rng.uniform(0, math.tau)
        d = _sine_path(-40, w + 40, base, amp, cycles, phase, samples=90)
        out.append(f"<path d='{d}' fill='none' stroke='{color}' "
                   f"stroke-width='{round(rng.uniform(0.8, 1.5), 2)}' "
                   f"opacity='{round(opacity * rng.uniform(0.6, 1.0), 3)}'/>")
    return "".join(out)


def _grid(w: int, h: int, step: int, color: str, opacity: float) -> str:
    out = []
    x = step
    while x < w:
        out.append(f"<line x1='{x}' y1='0' x2='{x}' y2='{h}' stroke='{color}' "
                   f"stroke-width='1' opacity='{opacity}'/>")
        x += step
    y = step
    while y < h:
        out.append(f"<line x1='0' y1='{y}' x2='{w}' y2='{y}' stroke='{color}' "
                   f"stroke-width='1' opacity='{opacity * 0.6:.3f}'/>")
        y += step
    return "".join(out)


# ---------------------------------------------------------------------------
# SCENE 1 — Hero
# ---------------------------------------------------------------------------

# The hero must be the tallest full-bleed scene on the page. The masthead and
# the horizon line are fixed; the extra height is all sea, which is where the
# travelling light, the wave paths and the horizon glow live. Growing the sea
# rather than the type keeps the name at 100 units and gives the motion the
# room it needs to read as motion.
HERO_W, HERO_H = CANVAS_W, 620
HERO_HZ = 436


def _build_hero(theme: dict, profile: dict, stats: dict, *, animated: bool) -> str:
    w, h, hz = HERO_W, HERO_H, HERO_HZ
    name = (profile.get("display_name") or "Kulraj Neupane").upper()
    handle = profile.get("handle") or "kulraj025"
    university = ((profile.get("university") or {}).get("institution")
                  or "Dong-eui University")
    location = profile.get("location") or "Busan, South Korea"

    name_size = D.fit_font_size(name, CONTENT_W, 100, weight="800", tracking=1.2)
    name_w = D.text_width(name, name_size, weight="800", tracking=1.2)
    name_x = round((w - name_w) / 2, 1)

    kicker = f"{university.upper()}  ·  {location.upper()}"
    kicker_size = D.fit_font_size(kicker, CONTENT_W, 20, mono=True, tracking=3.0)

    # The tagline is short and large on purpose. A 1000-unit canvas renders at
    # 0.375x on a phone, so anything under ~36 units is unreadable there; the
    # longer 30-unit two-line version this replaces measured 11.2px on mobile.
    line1 = "STUDENT DEVELOPER"
    line2 = "BUILDING WITH AI FROM BUSAN"
    tag_size = D.fit_font_size(line2, CONTENT_W - 40, 38, weight="700", tracking=2.4)
    l1_w = D.text_width(line1, tag_size, weight="700", tracking=2.4)
    l2_w = D.text_width(line2, tag_size, weight="700", tracking=2.4)
    cursor_x = round((w - l2_w) / 2 + l2_w + 16, 1)

    anims: list[str] = []

    # --- background wash -------------------------------------------------
    defs = [
        "<defs>",
        f"<linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0%' stop-color='{P['bg']}'/>"
        f"<stop offset='62%' stop-color='#0A1226'/>"
        f"<stop offset='100%' stop-color='#0C1A33'/>"
        + (f"<animate attributeName='x1' values='0;1;0' dur='{DUR_S['gradient']}s' "
           f"repeatCount='indefinite'/>" if animated else "")
        + "</linearGradient>",
        f"<linearGradient id='sea' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0%' stop-color='#0E1E3C'/>"
        f"<stop offset='100%' stop-color='{P['bg']}'/></linearGradient>",
        # Vertical falloff for the water reflections: bright at the horizon,
        # gone by the bottom edge, so a reflection reads as light on a surface
        # rather than a solid bar.
        f"<linearGradient id='reflect' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0%' stop-color='{P['cyan_br']}' stop-opacity='0.85'/>"
        f"<stop offset='45%' stop-color='{P['cyan']}' stop-opacity='0.30'/>"
        f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='0'/>"
        "</linearGradient>",
        f"<linearGradient id='hz' x1='0' y1='0' x2='1' y2='0'>"
        f"<stop offset='0%' stop-color='{P['cyan']}' stop-opacity='0'/>"
        f"<stop offset='22%' stop-color='{P['cyan_br']}' stop-opacity='0.9'/>"
        f"<stop offset='55%' stop-color='{P['cyan']}' stop-opacity='1'/>"
        f"<stop offset='80%' stop-color='{P['violet']}' stop-opacity='0.85'/>"
        f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='0'/>"
        "</linearGradient>",
        f"<linearGradient id='rule' x1='0' y1='0' x2='1' y2='0'>"
        f"<stop offset='0%' stop-color='{P['cyan_br']}' stop-opacity='0'/>"
        f"<stop offset='50%' stop-color='{P['cyan_br']}' stop-opacity='1'/>"
        f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='0'/>"
        "</linearGradient>",
        f"<radialGradient id='glow' cx='50%' cy='50%' r='50%'>"
        f"<stop offset='0%' stop-color='{P['cyan']}' stop-opacity='0.30'/>"
        f"<stop offset='60%' stop-color='{P['cyan']}' stop-opacity='0.07'/>"
        f"<stop offset='100%' stop-color='{P['cyan']}' stop-opacity='0'/>"
        "</radialGradient>",
        f"<radialGradient id='hot' cx='50%' cy='50%' r='50%'>"
        f"<stop offset='0%' stop-color='#FFFFFF' stop-opacity='0.95'/>"
        f"<stop offset='35%' stop-color='{P['cyan_br']}' stop-opacity='0.7'/>"
        f"<stop offset='100%' stop-color='{P['cyan_br']}' stop-opacity='0'/>"
        "</radialGradient>",
        "</defs>",
    ]
    if animated:
        anims.append("gradient")

    body: list[str] = [
        f"<rect width='{w}' height='{h}' fill='url(#sky)'/>",
        _grid(w, hz, 62, P["cyan"], 0.045),
        f"<ellipse cx='{w / 2}' cy='{hz}' rx='560' ry='210' fill='url(#glow)'/>",
        _contours(w, 40, hz - 30, 4, 7, P["cyan"], D.AMBIENT * 0.55),
        _starfield(w, 30, hz - 90, 34, 11, animated=animated),
    ]

    # --- sea -------------------------------------------------------------
    sea_d = h - hz
    body.append(f"<rect x='0' y='{hz}' width='{w}' height='{sea_d}' fill='url(#sea)'/>")

    # Wave count and spacing derive from the sea depth. Two hard-coded waves
    # filled a 120-unit sea; when the hero grew, the extra depth became a bare
    # gradient and the scene failed the dead-band check. The waves now reach
    # the bottom edge, so the surface reads as a surface at any hero height.
    spacing = max(24, round(sea_d / 5.2))
    wave_specs = ((16, 1.6, 0.30, 24), (9, 2.3, 0.18, 19), (13, 1.1, 0.22, 29),
                  (7, 2.9, 0.14, 22), (11, 0.8, 0.16, 34))
    n_waves = max(2, min(len(wave_specs), sea_d // spacing))
    for i in range(n_waves):
        amp, cyc, op, dur = wave_specs[i]
        d = _sine_path(0, w * 2, hz + 26 + i * spacing, amp, cyc * 2, i * 1.1, samples=200)
        drift = (f"<animateTransform attributeName='transform' type='translate' "
                 f"values='0 0;{-w} 0' dur='{dur}s' repeatCount='indefinite'/>"
                 if animated else "")
        body.append(f"<g>{drift}<path d='{d}' fill='none' stroke='{P['cyan_br']}' "
                    f"stroke-width='{1.6 - i * 0.2}' opacity='{op}'/></g>")
        if animated:
            anims.append("wave")

    # Reflection of the horizon light and the location marker, falling straight
    # down through the water. This is what stops the lower sea reading as a
    # void, and it is the same motif the contact scene closes on.
    for rx, rw, rop in ((w * 0.5, 150, 0.16), (w * 0.845, 54, 0.22)):
        body.append(
            f"<rect x='{round(rx - rw / 2, 1)}' y='{hz + 2}' width='{round(rw)}' "
            f"height='{round(sea_d * 0.72)}' fill='url(#reflect)' opacity='{rop}'/>")

    # Slow current striations in the deep water: a few long, very low-contrast
    # horizontals that drift, so the bottom of the frame is never static.
    for i in range(3):
        y0 = hz + sea_d * (0.52 + i * 0.16)
        drift = (f"<animateTransform attributeName='transform' type='translate' "
                 f"values='0 0;{-w} 0' dur='{47 + i * 9}s' repeatCount='indefinite'/>"
                 if animated else "")
        body.append(
            f"<g>{drift}<path d='{_sine_path(0, w * 2, y0, 5, 2.2, i * 2.3, samples=160)}' "
            f"fill='none' stroke='{P['cyan']}' stroke-width='1' "
            f"opacity='{0.10 - i * 0.02}'/></g>")

    # --- horizon ---------------------------------------------------------
    body.append(f"<rect x='0' y='{hz - 26}' width='{w}' height='52' fill='url(#glow)' opacity='0.5'/>")
    body.append(f"<rect x='0' y='{hz - 1}' width='{w}' height='2' fill='url(#hz)'/>")

    # Light travelling the horizon path.
    if animated:
        body.append(
            f"<g transform='translate(0,{hz})'>"
            f"<circle r='16' fill='url(#hot)'>"
            f"<animateMotion dur='{DUR_S['travel']}s' repeatCount='indefinite' "
            f"path='M0,0 H{w}'/>"
            f"<animate attributeName='opacity' values='0;1;1;0' "
            f"keyTimes='0;0.08;0.9;1' dur='{DUR_S['travel']}s' "
            f"repeatCount='indefinite'/>"
            f"</circle></g>")
        anims.append("travel")
    else:
        body.append(f"<g transform='translate({w * 0.62},{hz})'>"
                    f"<circle r='14' fill='url(#hot)'/></g>")

    # --- location signal (Busan) ----------------------------------------
    lx, ly = int(w * 0.845), hz
    for i in range(2):
        r0 = 10 + i * 13
        grow = (f"<animate attributeName='r' values='{r0};{r0 + 34}' "
                f"dur='{DUR_S['pulse']}s' begin='{i * (DUR_S['pulse'] / 2)}s' "
                f"repeatCount='indefinite'/>"
                f"<animate attributeName='opacity' values='0.55;0' "
                f"dur='{DUR_S['pulse']}s' begin='{i * (DUR_S['pulse'] / 2)}s' "
                f"repeatCount='indefinite'/>" if animated else "")
        body.append(f"<circle cx='{lx}' cy='{ly}' r='{r0}' fill='none' "
                    f"stroke='{P['cyan_br']}' stroke-width='1.4' opacity='0.5'>{grow}</circle>")
        if animated:
            anims.append("pulse")
    body.append(f"<circle cx='{lx}' cy='{ly}' r='4.5' fill='{P['cyan_br']}'/>")
    body.append(f"<path d='M{lx},{ly - 9} l5,9 l-10,0 z' fill='{P['cyan_br']}' opacity='0.9'/>")

    # --- masthead --------------------------------------------------------
    body.append(_text(w / 2, 80, kicker, kicker_size, fill=P["text_2"],
                      weight="600", mono=True, tracking=3.0, anchor="middle"))

    # status dot + handle
    dot_anim = (f"<animate attributeName='opacity' values='0.35;1;0.35' "
                f"dur='{DUR_S['pulse']}s' repeatCount='indefinite'/>"
                if animated else "")
    handle_txt = f"@{handle}"
    hw = D.text_width(handle_txt, 22, mono=True, tracking=2.2)
    hx = round((w - hw) / 2, 1)
    body.append(f"<circle cx='{round(hx - 17, 1)}' cy='119' r='5.5' "
                f"fill='{P['green']}'>{dot_anim}</circle>")
    body.append(_text(hx, 125, handle_txt, 22, fill=P["cyan_br"], weight="600",
                      mono=True, tracking=2.2))
    if animated:
        anims.append("status")

    body.append(_text(name_x, 252, name, name_size, fill=P["text"],
                      weight="800", tracking=1.2))
    body.append(f"<rect x='{round((w - 320) / 2, 1)}' y='288' width='320' "
                f"height='3' rx='1.5' fill='url(#rule)'/>")

    body.append(_text(w / 2, 348, line1, tag_size, fill=P["text_2"],
                      weight="700", tracking=2.4, anchor="middle"))
    body.append(_text(w / 2, 398, line2, tag_size, fill=P["cyan_br"],
                      weight="700", tracking=2.4, anchor="middle"))
    cur = (f"<animate attributeName='opacity' values='1;0;1' "
           f"dur='{DUR_S['cursor']}s' repeatCount='indefinite'/>" if animated else "")
    body.append(f"<rect x='{cursor_x}' y='{398 - tag_size * 0.72}' width='{round(tag_size * 0.42, 1)}' "
                f"height='{round(tag_size * 0.88, 1)}' rx='2' fill='{P['cyan_br']}' "
                f"opacity='0.9'>{cur}</rect>")
    if animated:
        anims.append("cursor")

    return _hdr(w, h, "KULRAJ NEUPANE — student developer in Busan, South Korea, "
                       "studying Intelligence Computing at Dong-eui University") + \
        "".join(defs) + "".join(body) + "</svg>"


# ---------------------------------------------------------------------------
# SCENE 2 — Section divider (the repeating horizon motif)
# ---------------------------------------------------------------------------

def _build_divider(theme: dict, *, animated: bool) -> str:
    w, h = CANVAS_W, D.DIVIDER_H
    cy = h // 2
    pulse = (f"<animate attributeName='opacity' values='0.5;1;0.5' "
             f"dur='{DUR_S['swell']}s' repeatCount='indefinite'/>" if animated else "")
    return _hdr(w, h, "Section divider") + (
        "<defs>"
        f"<linearGradient id='d' x1='0' y1='0' x2='1' y2='0'>"
        f"<stop offset='0%' stop-color='{P['cyan']}' stop-opacity='0'/>"
        f"<stop offset='50%' stop-color='{P['cyan_br']}' stop-opacity='0.75'/>"
        f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='0'/>"
        "</linearGradient></defs>"
        f"<rect x='{GUTTER}' y='{cy - 1}' width='{w - GUTTER * 2}' height='2' "
        f"fill='url(#d)'/>"
        f"<g opacity='0.9'>{pulse}"
        f"<path d='M{w / 2},{cy - 7} l7,7 l-7,7 l-7,-7 z' fill='{P['cyan_br']}'/>"
        f"</g>"
        f"<circle cx='{w / 2 - 120}' cy='{cy}' r='2' fill='{P['violet']}' opacity='0.8'/>"
        f"<circle cx='{w / 2 + 120}' cy='{cy}' r='2' fill='{P['violet']}' opacity='0.8'/>"
    ) + "</svg>"


# ---------------------------------------------------------------------------
# SCENE 3 — Technology orbit
# ---------------------------------------------------------------------------

ORBIT_W, ORBIT_H = CANVAS_W, 520
ORBIT_MAX_NODES = 4          # top N by real byte share; the rest live in HTML


def _orbit_nodes(languages: list[dict], count: int) -> list[dict]:
    return sorted(languages, key=lambda l: -float(l.get("bytes") or 0))[:count]


def _build_orbit(theme: dict, languages: list[dict], *, animated: bool) -> str:
    w, h = ORBIT_W, ORBIT_H
    cx, cy = w / 2, 250
    rx, ry = 336, 172
    nodes = _orbit_nodes(languages, ORBIT_MAX_NODES)

    top = max([float(n.get("bytes") or 0) for n in nodes], default=1.0) or 1.0
    # Five anchor angles, none at the extreme top (a large node there would
    # breach the canvas) — this is the fix for nodes at negative y.
    angles = [200, 160, 340, 20, 90]
    if len(nodes) == 1:
        angles = [270]
    elif len(nodes) == 2:
        angles = [215, 325]
    elif len(nodes) == 3:
        angles = [200, 340, 90]

    body: list[str] = []
    anim_count = 0

    # --- central hub -----------------------------------------------------
    body.append(f"<circle cx='{cx}' cy='{cy}' r='190' fill='url(#hub)'/>")
    body.append(f"<circle cx='{cx}' cy='{cy}' r='104' fill='none' "
                f"stroke='{P['cyan']}' stroke-width='1.2' opacity='0.35'/>")
    spin = (f"<animateTransform attributeName='transform' type='rotate' "
            f"from='0 {cx} {cy}' to='360 {cx} {cy}' dur='{DUR_S['orbit']}s' "
            f"repeatCount='indefinite'/>" if animated else "")
    body.append(f"<g opacity='0.5'>{spin}"
                f"<circle cx='{cx}' cy='{cy}' r='132' fill='none' "
                f"stroke='{P['violet']}' stroke-width='1' stroke-dasharray='3 14'/>"
                f"</g>")
    if animated:
        anim_count += 1

    body.append(f"<circle cx='{cx}' cy='{cy}' r='86' fill='url(#core)'/>")
    core_pulse = (f"<animate attributeName='r' values='84;90;84' "
                  f"dur='{DUR_S['swell']}s' repeatCount='indefinite'/>"
                  if animated else "")
    body.append(f"<circle cx='{cx}' cy='{cy}' r='86' fill='none' "
                f"stroke='{P['cyan_br']}' stroke-width='1.6' opacity='0.65'>{core_pulse}</circle>")
    if animated:
        anim_count += 1
    body.append(_text(cx, cy - 4, "KULRAJ", 32, fill=P["text"], weight="800",
                      anchor="middle"))
    body.append(_text(cx, cy + 26, "BUILD SYSTEM", 18, fill=P["cyan_br"],
                      weight="600", mono=True, tracking=2.4, anchor="middle"))

    # --- connections + nodes --------------------------------------------
    for i, node in enumerate(nodes):
        ang = math.radians(angles[i % len(angles)])
        nx = cx + rx * math.cos(ang)
        ny = cy + ry * math.sin(ang)
        share = float(node.get("bytes") or 0) / top
        radius = 30 + 40 * math.sqrt(share)
        color = _lang_color(node.get("name", ""))
        name = node.get("name", "")

        # Connection brightness tracks relative activity.
        op = round(0.22 + 0.5 * share, 3)
        body.append(f"<line x1='{round(cx, 1)}' y1='{cy}' x2='{round(nx, 1)}' "
                    f"y2='{round(ny, 1)}' stroke='{color}' stroke-width='{round(1 + 2.2 * share, 2)}' "
                    f"opacity='{op}'/>")
        if animated:
            dash = (f"<animate attributeName='stroke-dashoffset' "
                    f"values='0;{-round(40 + 60 * share)}' dur='{round(DUR_S['travel'] - i * 1.4, 1)}s' "
                    f"repeatCount='indefinite'/>")
            body[-1] = body[-1][:-2] + f" stroke-dasharray='2 {round(18 + 26 * share, 1)}'>{dash}</line>"
            anim_count += 1

        body.append(f"<circle cx='{round(nx, 1)}' cy='{round(ny, 1)}' r='{round(radius + 14, 1)}' "
                    f"fill='url(#nodeGlow)' opacity='{round(0.25 + 0.4 * share, 2)}'/>")
        body.append(f"<circle cx='{round(nx, 1)}' cy='{round(ny, 1)}' r='{round(radius, 1)}' "
                    f"fill='{P['surface_2']}' stroke='{color}' stroke-width='2.4'/>")

        # Label inside the node when it genuinely fits, otherwise outside.
        # This is decided by measurement, never by guessing.
        label_size = 26 if radius >= 44 else 24
        inside_w = D.text_width(name, label_size, weight="700")
        if inside_w <= 2 * radius - 18:
            body.append(_text(nx, ny + label_size * 0.35, name, label_size,
                              fill=P["text"], weight="700", anchor="middle"))
        else:
            below = ny >= cy
            ly = ny + radius + 30 if below else ny - radius - 18
            body.append(_text(nx, ly, name, 22, fill=P["text_2"], weight="700",
                              anchor="middle"))

    defs = (
        "<defs>"
        f"<radialGradient id='hub' cx='50%' cy='50%' r='50%'>"
        f"<stop offset='0%' stop-color='{P['violet']}' stop-opacity='0.20'/>"
        f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='0'/>"
        "</radialGradient>"
        f"<radialGradient id='core' cx='42%' cy='36%' r='70%'>"
        f"<stop offset='0%' stop-color='#1B2C4E'/>"
        f"<stop offset='100%' stop-color='{P['surface']}'/>"
        "</radialGradient>"
        f"<radialGradient id='nodeGlow' cx='50%' cy='50%' r='50%'>"
        f"<stop offset='0%' stop-color='{P['cyan']}' stop-opacity='0.35'/>"
        f"<stop offset='100%' stop-color='{P['cyan']}' stop-opacity='0'/>"
        "</radialGradient>"
        "</defs>"
    )
    label = ("Technology orbit built from real GitHub language data: "
             + ", ".join(f"{n.get('name')} {n.get('percent', 0)}%" for n in nodes))
    return _hdr(w, h, label) + defs + "".join(body) + "</svg>"


# ---------------------------------------------------------------------------
# SCENE 4 — Per-project artwork
# ---------------------------------------------------------------------------

MOTIFS = ("contour", "grid", "stack", "nodes", "wave")


def _project_art_body(w: int, h: int, name: str, accent: str, motif: str,
                      *, animated: bool) -> str:
    rng = _seeded(name)
    body: list[str] = [
        f"<rect width='{w}' height='{h}' fill='url(#pa)'/>",
        _grid(w, h, 28, P["cyan"], 0.05),
    ]
    anim = 0

    if motif == "contour":
        for i in range(5):
            r = 26 + i * 22
            body.append(f"<circle cx='{w * 0.72}' cy='{h * 0.5}' r='{r}' fill='none' "
                        f"stroke='{accent}' stroke-width='1.3' "
                        f"opacity='{round(0.5 - i * 0.07, 2)}'/>")
    elif motif == "grid":
        cols, rows = 9, 6
        for cx_ in range(cols):
            for ry_ in range(rows):
                if rng.random() < 0.30:
                    body.append(f"<rect x='{18 + cx_ * 30}' y='{16 + ry_ * 26}' "
                                f"width='16' height='12' rx='2' fill='{accent}' "
                                f"opacity='{round(rng.uniform(0.25, 0.8), 2)}'/>")
    elif motif == "stack":
        for i in range(6):
            bw = int(w * rng.uniform(0.28, 0.72))
            body.append(f"<rect x='{GUTTER // 2}' y='{22 + i * 24}' width='{bw}' "
                        f"height='9' rx='4.5' fill='{accent}' "
                        f"opacity='{round(0.75 - i * 0.09, 2)}'/>")
    elif motif == "nodes":
        pts = [(rng.uniform(50, w - 50), rng.uniform(34, h - 34)) for _ in range(7)]
        for i in range(len(pts) - 1):
            body.append(f"<line x1='{round(pts[i][0], 1)}' y1='{round(pts[i][1], 1)}' "
                        f"x2='{round(pts[i + 1][0], 1)}' y2='{round(pts[i + 1][1], 1)}' "
                        f"stroke='{accent}' stroke-width='1.2' opacity='0.4'/>")
        for i, (px, py) in enumerate(pts):
            body.append(f"<circle cx='{round(px, 1)}' cy='{round(py, 1)}' r='{5 if i else 8}' "
                        f"fill='{accent}' opacity='{0.95 if i == 0 else 0.6}'/>")
    else:  # wave
        for i in range(4):
            d = _sine_path(0, w, h * 0.5 + (i - 1.5) * 22, 12 - i * 2,
                           2.0 + i * 0.4, i * 0.9, samples=110)
            if animated and i == 0:
                body.append(f"<g><animateTransform attributeName='transform' "
                            f"type='translate' values='0 0;{-w} 0' "
                            f"dur='{DUR_S['drift']}s' repeatCount='indefinite'/>"
                            f"<path d='{_sine_path(0, w * 2, h * 0.5 - 33, 12, 4.0, 0, 200)}' "
                            f"fill='none' stroke='{accent}' stroke-width='2' opacity='0.7'/></g>")
                anim += 1
            else:
                body.append(f"<path d='{d}' fill='none' stroke='{accent}' "
                            f"stroke-width='{2.2 - i * 0.4}' "
                            f"opacity='{round(0.7 - i * 0.14, 2)}'/>")

    # A slow shimmer keeps the card alive without demanding attention.
    if animated:
        body.append(
            f"<g><animateTransform attributeName='transform' type='translate' "
            f"values='{-w} 0;{w} 0' dur='{DUR_S['shimmer'] * 2}s' "
            f"repeatCount='indefinite'/>"
            f"<rect x='0' y='0' width='{w // 3}' height='{h}' fill='url(#sh)' "
            f"opacity='0.16'/></g>")
        anim += 1

    # Corner language swatch — colour only, the name is stated in the HTML card.
    body.append(f"<rect x='0' y='0' width='{w}' height='5' fill='{accent}' opacity='0.95'/>")
    body.append(f"<rect x='0' y='{h - 1}' width='{w}' height='1' fill='{P['line']}' opacity='0.6'/>")

    defs = (
        "<defs>"
        f"<linearGradient id='pa' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0%' stop-color='{P['surface']}'/>"
        f"<stop offset='100%' stop-color='{P['surface_2']}'/></linearGradient>"
        f"<linearGradient id='sh' x1='0' y1='0' x2='1' y2='0'>"
        f"<stop offset='0%' stop-color='#FFFFFF' stop-opacity='0'/>"
        f"<stop offset='50%' stop-color='#FFFFFF' stop-opacity='0.5'/>"
        f"<stop offset='100%' stop-color='#FFFFFF' stop-opacity='0'/></linearGradient>"
        "</defs>"
    )
    return defs + "".join(body), anim


def _build_project_art(theme: dict, project: dict, *, animated: bool,
                       size: str = "secondary") -> str:
    if size == "featured":
        w, h = 520, 300
    else:
        w, h = 340, 210
    name = project.get("name", "project")
    accent = project.get("accent") or ACCENT_RAMP[0]
    motif = MOTIFS[sum(name.encode()) % len(MOTIFS)]
    inner, _ = _project_art_body(w, h, name, accent, motif, animated=animated)
    return _hdr(w, h, f"Abstract artwork for {name}") + inner + "</svg>"


# ---------------------------------------------------------------------------
# SCENE 5 — Horizon signal (the activity motif band)
# ---------------------------------------------------------------------------

def _build_horizon_signal(theme: dict, *, animated: bool) -> str:
    w, h = CANVAS_W, 150
    mid = 74
    body: list[str] = [
        f"<rect width='{w}' height='{h}' fill='url(#sg)'/>",
    ]
    for i, (amp, cyc, col, op, dur) in enumerate((
            (30, 1.5, P["cyan_br"], 0.55, 26),
            (20, 2.2, P["cyan"], 0.40, 20),
            (12, 3.1, P["violet"], 0.34, 15))):
        d = _sine_path(0, w * 2, mid + (i - 1) * 20, amp, cyc * 2, i * 1.4, samples=220)
        drift = (f"<animateTransform attributeName='transform' type='translate' "
                 f"values='0 0;{-w} 0' dur='{dur}s' repeatCount='indefinite'/>"
                 if animated else "")
        body.append(f"<g>{drift}<path d='{d}' fill='none' stroke='{col}' "
                    f"stroke-width='{2.4 - i * 0.6}' opacity='{op}'/></g>")
    # travelling highlight
    if animated:
        body.append(f"<g transform='translate(0,{mid})'>"
                    f"<circle r='90' fill='url(#sgl)'>"
                    f"<animateMotion dur='{DUR_S['travel'] * 1.4}s' "
                    f"repeatCount='indefinite' path='M0,0 H{w}'/></circle></g>")
    defs = ("<defs>"
            f"<linearGradient id='sg' x1='0' y1='0' x2='0' y2='1'>"
            f"<stop offset='0%' stop-color='{P['bg']}' stop-opacity='0'/>"
            f"<stop offset='50%' stop-color='#0C1A33' stop-opacity='0.9'/>"
            f"<stop offset='100%' stop-color='{P['bg']}' stop-opacity='0'/></linearGradient>"
            f"<radialGradient id='sgl' cx='50%' cy='50%' r='50%'>"
            f"<stop offset='0%' stop-color='{P['cyan_br']}' stop-opacity='0.22'/>"
            f"<stop offset='100%' stop-color='{P['cyan_br']}' stop-opacity='0'/>"
            "</radialGradient></defs>")
    return _hdr(w, h, "Animated signal trace") + defs + "".join(body) + "</svg>"


# ---------------------------------------------------------------------------
# SCENE 6 — Learning path (verified milestones only)
# ---------------------------------------------------------------------------

def _build_learning_path(theme: dict, profile: dict, *, animated: bool) -> str:
    w, h = CANVAS_W, 230
    n = 3
    y0, y1 = 168, 62
    xs = [GUTTER + 60 + i * ((w - GUTTER * 2 - 120) / (n - 1)) for i in range(n)]

    body: list[str] = []
    for i in range(n - 1):
        x_a, x_b = xs[i], xs[i + 1]
        body.append(f"<line x1='{round(x_a, 1)}' y1='{y0 - (y0 - y1) * i / (n - 1)}' "
                    f"x2='{round(x_b, 1)}' y2='{y0 - (y0 - y1) * (i + 1) / (n - 1)}' "
                    f"stroke='{P['line']}' stroke-width='2.5'/>")
    body.append(f"<line x1='{round(xs[0], 1)}' y1='{y0}' x2='{round(xs[-1], 1)}' "
                f"y2='{y1}' stroke='url(#lg)' stroke-width='2.5' opacity='0.9'/>")

    if animated:
        # A pulse that travels the ascending path, reinforcing "in progress".
        # animateMotion must be a child of the shape it drives.
        body.append(
            f"<circle r='16' fill='url(#lglow)'>"
            f"<animateMotion dur='{DUR_S['travel']}s' repeatCount='indefinite' "
            f"path='M{round(xs[0], 1)},{y0} L{round(xs[-1], 1)},{y1}'/>"
            f"</circle>")

    for i, x in enumerate(xs):
        y = y0 - (y0 - y1) * i / (n - 1)
        done = i < n - 1
        col = P["cyan_br"] if done else P["violet"]
        body.append(f"<circle cx='{round(x, 1)}' cy='{round(y, 1)}' r='26' "
                    f"fill='url(#lglow)' opacity='{0.5 if done else 0.75}'/>")
        body.append(f"<circle cx='{round(x, 1)}' cy='{round(y, 1)}' r='11' "
                    f"fill='{P['surface_2']}' stroke='{col}' stroke-width='2.6'/>")
        if i == n - 1 and animated:
            body[-1] = body[-1][:-2] + (
                f"><animate attributeName='r' values='11;14;11' "
                f"dur='{DUR_S['pulse']}s' repeatCount='indefinite'/></circle>")
        body.append(f"<text x='{round(x, 1)}' y='{round(y + 5, 1)}' font-size='18' "
                    f"font-weight='700' fill='{col}' font-family=\"{FONT_MONO}\" "
                    f"text-anchor='middle'>{i + 1}</text>")

    defs = ("<defs>"
            f"<linearGradient id='lg' x1='0' y1='1' x2='1' y2='0'>"
            f"<stop offset='0%' stop-color='{P['cyan_br']}' stop-opacity='0.45'/>"
            f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='1'/>"
            "</linearGradient>"
            f"<radialGradient id='lglow' cx='50%' cy='50%' r='50%'>"
            f"<stop offset='0%' stop-color='{P['cyan']}' stop-opacity='0.28'/>"
            f"<stop offset='100%' stop-color='{P['cyan']}' stop-opacity='0'/>"
            "</radialGradient></defs>")
    return _hdr(w, h, "Learning path: three verified milestones") + defs + \
        "".join(body) + "</svg>"


# ---------------------------------------------------------------------------
# SCENE 7 — Contact horizon (closing statement)
# ---------------------------------------------------------------------------

def _build_contact_horizon(theme: dict, profile: dict, *, animated: bool) -> str:
    w, h = CANVAS_W, 300
    hz = 196
    name = (profile.get("display_name") or "Kulraj Neupane").upper()

    body: list[str] = [
        f"<rect width='{w}' height='{h}' fill='url(#ch)'/>",
        _contours(w, 30, hz - 40, 3, 21, P["cyan"], D.AMBIENT * 0.5),
        _starfield(w, 20, hz - 80, 22, 5, animated=animated),
        f"<ellipse cx='{w / 2}' cy='{hz}' rx='520' ry='150' fill='url(#cglow)'/>",
    ]
    for i, (amp, cyc, op, dur) in enumerate(((14, 1.7, 0.34, 22), (8, 2.6, 0.20, 17))):
        d = _sine_path(0, w * 2, hz + 26 + i * 26, amp, cyc * 2, i * 1.2, samples=200)
        drift = (f"<animateTransform attributeName='transform' type='translate' "
                 f"values='0 0;{-w} 0' dur='{dur}s' repeatCount='indefinite'/>"
                 if animated else "")
        body.append(f"<g>{drift}<path d='{d}' fill='none' stroke='{P['cyan_br']}' "
                    f"stroke-width='{1.8 - i * 0.6}' opacity='{op}'/></g>")
    body.append(f"<rect x='0' y='{hz - 1}' width='{w}' height='2' fill='url(#chz)'/>")
    if animated:
        body.append(f"<g transform='translate(0,{hz})'><circle r='20' fill='url(#chot)'>"
                    f"<animateMotion dur='{DUR_S['travel'] * 0.8}s' "
                    f"repeatCount='indefinite' path='M0,0 H{w}'/>"
                    f"<animate attributeName='opacity' values='0;1;1;0' "
                    f"keyTimes='0;0.1;0.88;1' dur='{DUR_S['travel'] * 0.8}s' "
                    f"repeatCount='indefinite'/></circle></g>")

    line1 = "LET'S BUILD SOMETHING"
    s1 = D.fit_font_size(line1, CONTENT_W, 46, weight="800", tracking=2.0)
    body.append(_text(w / 2, 108, line1, s1, fill=P["text"], weight="800",
                      tracking=2.0, anchor="middle"))
    body.append(f"<rect x='{round((w - 260) / 2, 1)}' y='132' width='260' height='2' "
                f"fill='url(#chr)'/>")
    body.append(_text(w / 2, 168, "OPEN TO COLLABORATION, INTERNSHIPS AND NEW IDEAS",
                      21, fill=P["cyan_br"], weight="600", mono=True,
                      tracking=2.6, anchor="middle"))

    defs = ("<defs>"
            f"<linearGradient id='ch' x1='0' y1='0' x2='0' y2='1'>"
            f"<stop offset='0%' stop-color='{P['bg']}'/>"
            f"<stop offset='100%' stop-color='#0B1428'/></linearGradient>"
            f"<radialGradient id='cglow' cx='50%' cy='50%' r='50%'>"
            f"<stop offset='0%' stop-color='{P['violet']}' stop-opacity='0.26'/>"
            f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='0'/>"
            "</radialGradient>"
            f"<linearGradient id='chz' x1='0' y1='0' x2='1' y2='0'>"
            f"<stop offset='0%' stop-color='{P['violet']}' stop-opacity='0'/>"
            f"<stop offset='50%' stop-color='{P['violet']}' stop-opacity='1'/>"
            f"<stop offset='100%' stop-color='{P['cyan_br']}' stop-opacity='0'/>"
            "</linearGradient>"
            f"<linearGradient id='chr' x1='0' y1='0' x2='1' y2='0'>"
            f"<stop offset='0%' stop-color='{P['violet']}' stop-opacity='0'/>"
            f"<stop offset='50%' stop-color='{P['violet']}' stop-opacity='1'/>"
            f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='0'/>"
            "</linearGradient>"
            f"<radialGradient id='chot' cx='50%' cy='50%' r='50%'>"
            f"<stop offset='0%' stop-color='#FFFFFF' stop-opacity='0.9'/>"
            f"<stop offset='100%' stop-color='{P['violet']}' stop-opacity='0'/>"
            "</radialGradient></defs>")
    return _hdr(w, h, f"{name} — contact") + defs + "".join(body) + "</svg>"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _write(directory: Path, filename: str, svg: str) -> str:
    """Write an asset and return its repo-relative path.

    The returned path is what the README references, so it must be relative to
    the repository root and use forward slashes on every platform.
    """
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(svg, encoding="utf-8")
    try:
        prefix = directory.relative_to(ROOT).as_posix()
    except ValueError:
        # Outside the repo (tests redirect the output directories); fall back to
        # a path relative to the assets root so callers can still resolve it.
        prefix = directory.name
    return f"{prefix}/{filename}"


def generate_all(theme: dict, profile: dict, stats: dict, languages: list[dict],
                 events: list[dict], projects: list[dict]) -> dict[str, str]:
    """Generate every scene in both animated and static form.

    Returns a mapping of logical name -> repo-relative asset path.
    """
    written: dict[str, str] = {}

    # Clean stale scenes from the previous generation so an orphaned widget can
    # never linger in assets/ and get referenced again.
    for stale in ("technology-constellation.svg", "identity.svg", "identity-card.svg",
                  "project-gallery.svg", "activity-dashboard.svg",
                  "contributions.svg", "footer-horizon.svg"):
        for d in (ASSETS_DIR, STATIC_DIR):
            (d / stale).unlink(missing_ok=True)
    for d in (ASSETS_DIR / "project-art", STATIC_DIR / "project-art"):
        if d.exists():
            for f in d.glob("*.svg"):
                f.unlink()

    pairs = [
        ("hero", lambda a: _build_hero(theme, profile, stats, animated=a),
         lambda: _build_hero(theme, profile, stats, animated=False), "hero.svg"),
        ("divider", lambda a: _build_divider(theme, animated=a),
         lambda: _build_divider(theme, animated=False), "divider.svg"),
        ("technology-orbit", lambda a: _build_orbit(theme, languages, animated=a),
         lambda: _build_orbit(theme, languages, animated=False), "technology-orbit.svg"),
        ("horizon-signal", lambda a: _build_horizon_signal(theme, animated=a),
         lambda: _build_horizon_signal(theme, animated=False), "horizon-signal.svg"),
        ("learning-path", lambda a: _build_learning_path(theme, profile, animated=a),
         lambda: _build_learning_path(theme, profile, animated=False), "learning-path.svg"),
        ("contact-horizon", lambda a: _build_contact_horizon(theme, profile, animated=a),
         lambda: _build_contact_horizon(theme, profile, animated=False), "contact-horizon.svg"),
    ]

    for key, build_a, build_s, filename in pairs:
        written[key] = _write(ASSETS_DIR, filename, build_a(True))
        _write(STATIC_DIR, filename, build_s())

    # Static hero fallback gets its own historical filename.
    _write(STATIC_DIR, "hero-fallback.svg", _build_hero(theme, profile, stats, animated=False))

    # Per-project artwork. Accents are dealt out from the ramp so that
    # adjacent cards are never the same colour.
    for i, project in enumerate(projects):
        project = dict(project)
        project["accent"] = ACCENT_RAMP[i % len(ACCENT_RAMP)]
        size = "featured" if i == 0 else "secondary"
        slug = slugify(project.get("name", f"project-{i}"))
        written[f"project-art:{slug}"] = _write(
            ASSETS_DIR / "project-art", f"{slug}.svg",
            _build_project_art(theme, project, animated=True, size=size))
        _write(STATIC_DIR / "project-art", f"{slug}.svg",
               _build_project_art(theme, project, animated=False, size=size))

    return written
