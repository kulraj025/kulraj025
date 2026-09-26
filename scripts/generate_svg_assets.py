"""Generate animated SVG assets for the Busan Digital Horizon profile.

Assets:
  - assets/generated/hero.svg          animated hero banner
  - assets/static/hero-fallback.svg    static fallback
  - assets/generated/identity-card.svg visual identity panel
  - assets/generated/technology-constellation.svg orbiting language nodes
  - assets/static/technology-constellation.svg static fallback
  - assets/generated/activity-dashboard.svg activity composition
  - assets/static/activity-dashboard.svg static fallback
  - assets/generated/contributions.svg contribution visualization
  - assets/static/contributions.svg static fallback
  - assets/generated/learning-path.svg animated learning timeline
  - assets/static/learning-path.svg static fallback
  - assets/generated/footer-horizon.svg abstract footer horizon
  - assets/generated/project-gallery.svg premium project gallery
  - assets/static/project-gallery.svg static fallback

All SVGs use SVG SMIL animation only -- no JavaScript.
Static fallbacks are generated alongside each animated asset.
"""
from __future__ import annotations

import html
import math
import random
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets" / "generated"
STATIC_DIR = ROOT / "assets" / "static"


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _svg_header(width: int, height: int, viewBox: str, label: str, cls="g") -> str:
    label = label.replace("'", "&apos;")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' "
        f"width='{width}' height='{height}' "
        f"viewBox='{viewBox}' role='img' "
        f"aria-label='{label}' "
        f"overflow='visible'>"
    )


def _gradient_defs(theme: dict, animated: bool = True) -> str:
    """Reusable gradient definitions."""
    bg = _esc(theme.get("background", "#070B17"))
    surf = _esc(theme.get("surface", "#0D1528"))
    cyan = _esc(theme.get("cyan", "#22D3EE"))
    violet = _esc(theme.get("violet", "#8B5CF6"))

    parts = []
    parts.append("  <defs>")
    parts.append("    <radialGradient id='bgGrad' cx='50%' cy='50%' r='70%'>")
    parts.append(f"      <stop offset='0%' stop-color='{bg}'/>")
    parts.append(f"      <stop offset='100%' stop-color='{surf}'/>")
    parts.append("    </radialGradient>")

    if animated:
        parts.append("    <linearGradient id='waveGrad' x1='0' y1='0' x2='1' y2='0'>")
        parts.append(f"      <stop offset='0%' stop-color='{cyan}'>")
        parts.append(f"        <animate attributeName='stop-color' values='{cyan};{violet};{cyan}' dur='20s' repeatCount='indefinite'/>")
        parts.append("      </stop>")
        parts.append(f"      <stop offset='100%' stop-color='{violet}'>")
        parts.append(f"        <animate attributeName='stop-color' values='{violet};{cyan};{violet}' dur='20s' repeatCount='indefinite'/>")
        parts.append("      </stop>")
        parts.append("    </linearGradient>")
    else:
        parts.append("    <linearGradient id='waveGrad' x1='0' y1='0' x2='1' y2='0'>")
        parts.append(f"      <stop offset='0%' stop-color='{cyan}'/>")
        parts.append(f"      <stop offset='100%' stop-color='{violet}'/>")
        parts.append("    </linearGradient>")

    parts.append("  </defs>")
    return "\n".join(parts)


def _build_grid(width: int, height: int, theme: dict, animated: bool = True) -> str:
    """Subtle digital grid lines."""
    cyan = _esc(theme.get("cyan", "#22D3EE"))
    parts = []
    for x in range(0, width + 1, 40):
        if animated:
            parts.append(
                f"    <line x1='{x}' y1='0' x2='{x}' y2='{height}' "
                f"stroke='{cyan}' stroke-width='0.5' opacity='0.12'>"
                f"<animate attributeName='opacity' values='0.12;0.25;0.12' dur='12s' begin='{x*0.03}s' repeatCount='indefinite'/>"
                f"</line>"
            )
        else:
            parts.append(f"    <line x1='{x}' y1='0' x2='{x}' y2='{height}' stroke='{cyan}' stroke-width='0.5' opacity='0.08'/>")
    for y in range(0, height + 1, 30):
        parts.append(f"    <line x1='0' y1='{y}' x2='{width}' y2='{y}' stroke='{cyan}' stroke-width='0.5' opacity='0.06'/>")
    return "\n".join(parts)


def _build_particles(n: int, width: int, height: int, theme: dict, seed: int = 42, animated: bool = True) -> str:
    """City-light particles drifting slowly."""
    rng = random.Random(seed + n)
    cyan = _esc(theme.get("cyan", "#22D3EE"))
    violet = _esc(theme.get("violet", "#8B5CF6"))
    parts = []
    for i in range(n):
        cx = rng.randint(10, width - 10)
        cy = rng.randint(10, height - 30)
        r = rng.randint(1, 2)
        dur = round(rng.uniform(10, 25), 1)
        delay = round(rng.uniform(0, 5), 2)
        op = round(rng.uniform(0.15, 0.45), 2)
        color = cyan if i % 2 == 0 else violet
        parts.append(
            f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='{color}' opacity='{op}'>"
        )
        if animated:
            parts.append(
                f"<animate attributeName='cy' values='{cy};{cy-15};{cy}' dur='{dur}s' begin='{delay}s' repeatCount='indefinite'/>"
                f"<animate attributeName='opacity' values='{op};{op+0.15};{op}' dur='{dur}s' begin='{delay}s' repeatCount='indefinite'/>"
            )
        parts.append(f"</circle>")
    return "\n".join(parts)


def _sine_wave_path(width: int, y_base: int, amplitude: int, frequency: float, phase: float) -> str:
    """Generate a smooth sine wave path string."""
    points = []
    for x in range(0, width + 1, 5):
        y = y_base + amplitude * math.sin(frequency * x / width + phase)
        if x == 0:
            points.append(f"M{x},{y:.1f}")
        else:
            points.append(f"L{x},{y:.1f}")
    return " ".join(points)


# ---------------------------------------------------------------------------
# Colour + text-fitting helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(value: str) -> tuple[float, float, float] | None:
    v = (value or "").strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", v)
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02X}" for c in rgb)


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(rgb[0]), lin(rgb[1]), lin(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast ratio between two hex colours (1.0 - 21.0)."""
    a, b = _hex_to_rgb(fg), _hex_to_rgb(bg)
    if a is None or b is None:
        return 1.0
    la, lb = _relative_luminance(a), _relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def ensure_contrast(color: str, bg: str, min_ratio: float = 4.5) -> str:
    """Lighten `color` until it is legible on `bg`.

    GitHub's language colours (e.g. C++ #006699) are tuned for a light
    background and fail WCAG AA on this dark theme. Rather than hand-tuning
    a palette, derive a legible variant of the same hue.
    """
    rgb = _hex_to_rgb(color)
    if rgb is None:
        return color
    if contrast_ratio(color, bg) >= min_ratio:
        return color
    # Lighten toward white, preserving hue ordering.
    for step in range(1, 101):
        t = step / 100
        lifted = tuple(c + (1.0 - c) * t for c in rgb)
        if contrast_ratio(_rgb_to_hex(lifted), bg) >= min_ratio:
            return _rgb_to_hex(lifted)
    return "#FFFFFF"


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
        # A single word longer than the budget must be hard-split.
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


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

def build_hero(theme: dict, stats: dict, animated: bool = True) -> str:
    """Animated hero SVG: Busan Digital Horizon."""
    width, height = 1000, 320
    horizon_y = height - 70
    name = _esc(stats.get("name", "KULRAJ025"))
    location = _esc(stats.get("location", "BUSAN / SOUTH KOREA"))
    refresh_date = stats.get("refresh_date", "")

    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}",
                             "Animated Busan digital horizon representing Kulraj's developer profile"))
    parts.append(_gradient_defs(theme, animated=animated))
    parts.append(f"<rect width='{width}' height='{height}' fill='url(#bgGrad)'/>")

    # Digital grid
    parts.append(f"<g id='grid'>{_build_grid(width, height, theme, animated=animated)}</g>")

    # Ocean waves (3 layers, different frequencies)
    for layer, (amp, freq, ph) in enumerate([(14, 2.5, 0), (9, 3.5, 1.5), (7, 5.0, 3.0)]):
        wave_y = horizon_y + layer * 4
        path = _sine_wave_path(width, wave_y, amp, freq, ph)
        next_path = _sine_wave_path(width, wave_y, amp, freq, ph + 0.2)
        parts.append(
            f"<path d='{path}' fill='none' stroke='url(#waveGrad)' "
            f"stroke-width='1.2' opacity='{0.35 - layer*0.08}'>"
        )
        if animated:
            parts.append(
                f"<animate attributeName='d' dur='{25 + layer*5}s' begin='{layer*3}s' "
                f"values='{path};{next_path};{path}' repeatCount='indefinite'/>"
            )
        parts.append("</path>")

    # Horizon glow
    parts.append(f"<rect x='0' y='{horizon_y-5}' width='{width}' height='35' fill='url(#waveGrad)' opacity='0.1'/>")

    # City lights particles
    parts.append(f"<g id='particles'>{_build_particles(30, width, height, theme, animated=animated)}</g>")

    # Location pulse (Busan)
    bx, by = width - 130, horizon_y - 15
    pulse_color = theme.get("cyan", "#22D3EE")
    parts.append(f"<circle cx='{bx}' cy='{by}' r='4' fill='{pulse_color}' opacity='0.6'>")
    if animated:
        parts.append(f"<animate attributeName='r' values='4;10;4' dur='5s' repeatCount='indefinite'/>")
        parts.append(f"<animate attributeName='opacity' values='0.6;0.1;0.6' dur='5s' repeatCount='indefinite'/>")
    parts.append("</circle>")
    # Expanding rings
    for j in range(3):
        parts.append(
            f"<circle cx='{bx}' cy='{by}' r='0' fill='none' stroke='{pulse_color}' stroke-width='1' opacity='0.1'>"
        )
        if animated:
            parts.append(
                f"<animate attributeName='r' values='0;20' dur='6s' begin='{j*2}s' repeatCount='indefinite'/>"
                f"<animate attributeName='opacity' values='0.1;0' dur='6s' begin='{j*2}s' repeatCount='indefinite'/>"
            )
        parts.append("</circle>")

    # Title
    parts.append(
        f"<text x='40' y='115' fill='url(#waveGrad)' "
        f"font-size='42' font-family='Inter,Segoe UI,sans-serif' font-weight='700'>{name}</text>"
    )
    # Tagline
    parts.append(
        f"<text x='40' y='145' fill='{theme.get('white', '#F8FAFC')}' "
        f"font-size='14' font-family='Inter,Segoe UI,sans-serif' opacity='0.6'>"
        f"Intelligence Computing student at Dong-eui University</text>"
    )

    # Location label
    parts.append(
        f"<g transform='translate(40,170)'>"
        f"<circle cx='0' cy='0' r='3' fill='{theme.get('violet', '#8B5CF6')}'/>"
        f"<path d='M2,3 L2,10' stroke='{theme.get('violet', '#8B5CF6')}' stroke-width='1'/>"
        f"<text x='8' y='4' fill='{theme.get('white', '#F8FAFC')}' font-size='12' "
        f"font-family='Inter,Segoe UI,sans-serif'>{location}</text>"
        f"</g>"
    )

    # Terminal + status
    parts.append(
        f"<g transform='translate(40,{horizon_y + 25})'>"
        f"<text x='0' y='0' class='mono' font-size='12' fill='{theme.get('muted', '#94A3B8')}'>"
        f"kulraj@busan:~$</text>"
        f"<text x='120' y='0' class='mono' font-size='12' fill='{theme.get('cyan', '#22D3EE')}'>_</text>"
        f"</g>"
    )

    # System status + auto-refresh
    parts.append(
        f"<g transform='translate({width - 260},{height - 28})'>"
        f"<circle cx='0' cy='0' r='3' fill='{theme.get('green', '#34D399')}'>"
    )
    if animated:
        parts.append(f"<animate attributeName='opacity' values='0.6;1;0.6' dur='3s' repeatCount='indefinite'/>")
    parts.append(f"</circle>")
    parts.append(f"<text x='8' y='4' font-size='11' fill='{theme.get('muted', '#94A3B8')}' font-family='SF Mono,monospace'>SYSTEM ONLINE</text>")
    parts.append("</g>")

    refresh_x = width - 180
    parts.append(
        f"<g transform='translate({refresh_x},{height - 12})'>"
        f"<rect width='10' height='5' rx='1' fill='{theme.get('violet', '#8B5CF6')}' opacity='0.4'>"
    )
    if animated:
        parts.append(f"<animate attributeName='opacity' values='0.3;0.8;0.3' dur='4s' repeatCount='indefinite'/>")
    parts.append(f"</rect>")
    parts.append(
        f"<text x='16' y='4' font-size='10' fill='{theme.get('muted', '#94A3B8')}' "
        f"font-family='SF Mono,monospace'>AUTO-REFRESH {refresh_date}</text>"
    )
    parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


def build_hero_fallback(theme: dict, stats: dict) -> str:
    """Static fallback for hero (no animations)."""
    return build_hero(theme, stats, animated=False)

def build_identity_card(theme: dict, profile: dict) -> str:
    """Visual identity panel -- compact profile interface."""
    width, height = 700, 220
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Visual identity card for Kulraj"))
    parts.append(_gradient_defs(theme, animated=True))
    parts.append(f"<rect width='{width}' height='{height}' rx='20' fill='url(#bgGrad)'/>")

    # Subtle top gradient line
    parts.append(f"<rect x='0' y='0' width='{width}' height='3' fill='url(#waveGrad)'/>")

    # Avatar circle with initials
    parts.append(
        f"<circle cx='50' cy='60' r='24' fill='{_esc(theme.get('cyan', '#22D3EE'))}' opacity='0.15'/>"
        f"<circle cx='50' cy='60' r='18' fill='{_esc(theme.get('cyan', '#22D3EE'))}' opacity='0.4'>"
        f"<animate attributeName='r' values='18;20;18' dur='5s' repeatCount='indefinite'/>"
        f"<animate attributeName='opacity' values='0.4;0.6;0.4' dur='5s' repeatCount='indefinite'/>"
        f"</circle>"
    )
    parts.append(
        f"<text x='50' y='66' text-anchor='middle' fill='{_esc(theme.get('white', '#F8FAFC'))}' "
        f"font-size='14' font-weight='700' font-family='Inter,Segoe UI,sans-serif'>KN</text>"
    )

    name = _esc(profile.get("display_name", "Kulraj Neupane"))
    tagline = _esc(profile.get("tagline", "Student developer"))
    location = _esc(profile.get("location", "Busan, South Korea"))

    parts.append(f"<text x='90' y='50' fill='{_esc(theme.get('white', '#F8FAFC'))}' font-size='20' font-weight='700' font-family='Inter,Segoe UI,sans-serif'>{name}</text>")
    parts.append(f"<text x='90' y='72' fill='{_esc(theme.get('cyan', '#22D3EE'))}' font-size='13' font-family='Inter,Segoe UI,sans-serif'>{tagline}</text>")

    # Info rows
    labels = [
        ("Dong-eui University", "University"),
        (location, "Location"),
        ("Building AI projects", "Focus"),
    ]
    y = 105
    for value, label in labels:
        value_esc = _esc(value)
        label_esc = _esc(label)
        parts.append(f"<text x='90' y='{y}' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='11' font-family='SF Mono,monospace'>{label_esc}</text>")
        parts.append(f"<text x='{width - 60}' y='{y}' text-anchor='end' fill='{_esc(theme.get('white', '#F8FAFC'))}' font-size='12' font-family='Inter,Segoe UI,sans-serif'>{value_esc}</text>")
        y += 22

    # GitHub profile link (clickable area)
    parts.append(
        f"<a href='https://github.com/kulraj025'>"
        f"<rect x='{width - 130}' y='{height - 35}' width='120' height='28' rx='8' "
        f"fill='{_esc(theme.get('surface', '#0D1528'))}' stroke='{_esc(theme.get('cyan', '#22D3EE'))}' stroke-width='1'/>"
        f"<text x='{width - 70}' y='{height - 20}' text-anchor='middle' fill='{_esc(theme.get('cyan', '#22D3EE'))}' "
        f"font-size='12' font-family='Inter,Segoe UI,sans-serif'>GitHub Profile</text>"
        f"</a>"
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Identity instrument panel (Scene 2)
# ---------------------------------------------------------------------------

def _university_emblem(cx: int, cy: int, r: int, theme: dict) -> str:
    """Abstract geometric university motif.

    Deliberately NOT the official Dong-eui logo: an original hexagon +
    rising-arc + ray construction that reads as "institution" generically.
    """
    cyan = _esc(theme.get("cyan", "#22D3EE"))
    violet = _esc(theme.get("violet", "#8B5CF6"))
    line = "#233454"

    pts = []
    for i in range(6):
        a = math.radians(60 * i - 90)
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    hex_d = "M" + " L".join(pts) + " Z"

    parts = [
        f"<path d='{hex_d}' fill='none' stroke='{line}' stroke-width='1.5'/>",
        f"<path d='{hex_d}' fill='none' stroke='{cyan}' stroke-width='1.5' opacity='0.85' "
        f"stroke-dasharray='{r*2.4:.0f} {r*6:.0f}'>"
        f"<animateTransform attributeName='transform' type='rotate' "
        f"from='0 {cx} {cy}' to='360 {cx} {cy}' dur='48s' repeatCount='indefinite'/></path>",
        f"<path d='M{cx - r*0.55:.1f},{cy + r*0.30:.1f} "
        f"A {r*0.62:.1f} {r*0.62:.1f} 0 0 1 {cx + r*0.55:.1f},{cy + r*0.30:.1f}' "
        f"fill='none' stroke='{violet}' stroke-width='2' stroke-linecap='round'/>",
        f"<line x1='{cx}' y1='{cy - r*0.34:.1f}' x2='{cx}' y2='{cy + r*0.26:.1f}' "
        f"stroke='{violet}' stroke-width='2' stroke-linecap='round'/>",
    ]
    for i in range(3):
        a = math.radians(-90 + 40 * (i - 1))
        parts.append(
            f"<line x1='{cx + r*0.66*math.cos(a):.1f}' y1='{cy + r*0.66*math.sin(a):.1f}' "
            f"x2='{cx + r*0.80*math.cos(a):.1f}' y2='{cy + r*0.80*math.sin(a):.1f}' "
            f"stroke='{cyan}' stroke-width='1' opacity='0.6'/>"
        )
    parts.append(
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{cyan}' stroke-width='1' opacity='0.5'>"
        f"<animate attributeName='r' values='{r};{r + 7};{r}' dur='6s' repeatCount='indefinite'/>"
        f"<animate attributeName='opacity' values='0.5;0;0.5' dur='6s' repeatCount='indefinite'/></circle>"
    )
    return "\n".join("  " + p for p in parts)


def _location_pin(x: int, y: int, theme: dict) -> str:
    """Small map-pin marker with a gentle vertical pulse."""
    cyan = _esc(theme.get("cyan", "#22D3EE"))
    return (
        f"<g>"
        f"<circle cx='{x}' cy='{y}' r='9' fill='{cyan}' opacity='0.18'/>"
        f"<path d='M{x},{y - 6} c-3.6,0 -6.5,2.8 -6.5,6.3 c0,4.6 6.5,10.7 6.5,10.7 "
        f"s6.5,-6.1 6.5,-10.7 c0,-3.5 -2.9,-6.3 -6.5,-6.3 z' fill='{cyan}'/>"
        f"<circle cx='{x}' cy='{y}' r='2.2' fill='{_esc(theme.get('background', '#070B17'))}'/>"
        f"<animateTransform attributeName='transform' type='translate' "
        f"values='0 0; 0 -3; 0 0' dur='4s' repeatCount='indefinite' additive='sum'/>"
        f"</g>"
    )


def build_identity_panel(theme: dict, profile: dict) -> str:
    """Scene 2: refined profile instrument panel.

    Communicates student-developer status, university, location, current focus
    and learning track through labelled instrument rows rather than prose.
    Academic fields render only when explicitly present in config.
    """
    width, height = 1000, 340
    cyan = _esc(theme.get("cyan", "#22D3EE"))
    violet = _esc(theme.get("violet", "#8B5CF6"))
    purple = _esc(theme.get("purple", "#A78BFA"))
    white = _esc(theme.get("white", "#F8FAFC"))
    muted = _esc(theme.get("muted", "#94A3B8"))
    green = _esc(theme.get("green", "#34D399"))
    surf = _esc(theme.get("surface", "#0D1528"))
    surf2 = _esc(theme.get("surface_light", "#13203A"))
    line = "#233454"

    name = _esc(profile.get("display_name", "Kulraj Neupane"))
    handle = _esc(profile.get("handle", "kulraj025")).upper()
    tagline = _esc(profile.get("tagline", ""))
    location = _esc(profile.get("location", "Busan, South Korea"))
    uni = profile.get("university", {}) or {}
    uni_name = _esc(uni.get("institution", ""))
    uni_url = uni.get("website", "") or ""
    focus = _esc(profile.get("current_focus", ""))

    # Study record -- rendered only from explicitly configured values
    education = profile.get("education") or []
    edu = education[0] if education else {}
    degree = _esc(edu.get("degree", ""))
    spec = _esc(edu.get("specialization", ""))
    level = _esc(edu.get("level", ""))
    status = _esc(edu.get("status", ""))

    parts = [_svg_header(width, height, f"0 0 {width} {height}",
                         f"Identity instrument panel: student developer at {uni_name}, {location}")]
    parts.append(_gradient_defs(theme, animated=True))
    parts.append(f"<rect width='{width}' height='{height}' rx='22' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='3' fill='url(#waveGrad)'/>")
    parts.append(_build_grid(width, height, theme, animated=False))

    pad = 28
    mid, right = 330, 600

    # --- top status strip -------------------------------------------------
    parts.append(f"<text x='{pad}' y='34' fill='{muted}' font-size='10' letter-spacing='2.4' "
                 f"font-family='SF Mono,monospace'>IDENTITY // SYSTEM KULRAJ</text>")
    parts.append(f"<circle cx='{width - pad - 78}' cy='30' r='3.5' fill='{green}'>"
                 f"<animate attributeName='opacity' values='1;0.25;1' dur='3.5s' repeatCount='indefinite'/></circle>")
    parts.append(f"<text x='{width - pad}' y='34' text-anchor='end' fill='{green}' font-size='10' "
                 f"letter-spacing='1.8' font-family='SF Mono,monospace'>ONLINE</text>")
    parts.append(f"<line x1='{pad}' y1='48' x2='{width - pad}' y2='48' stroke='{line}' stroke-width='1'/>")

    # --- column 1: monogram + identity -----------------------------------
    cx0, cy0 = pad + 34, 108
    parts.append(f"<circle cx='{cx0}' cy='{cy0}' r='34' fill='{surf2}' stroke='{cyan}' stroke-width='1'/>")
    parts.append(f"<circle cx='{cx0}' cy='{cy0}' r='34' fill='none' stroke='{cyan}' stroke-width='1' "
                 f"opacity='0.55' stroke-dasharray='4 6'>"
                 f"<animateTransform attributeName='transform' type='rotate' "
                 f"from='0 {cx0} {cy0}' to='360 {cx0} {cy0}' dur='30s' repeatCount='indefinite'/></circle>")
    initials = "".join(w[0] for w in name.split()[:2] if w).upper() or "KN"
    parts.append(f"<text x='{cx0}' y='{cy0 + 7}' text-anchor='middle' fill='{white}' font-size='24' "
                 f"font-weight='700' font-family='Inter,Segoe UI,sans-serif'>{initials}</text>")

    parts.append(f"<text x='{pad}' y='172' fill='{white}' font-size='26' font-weight='700' "
                 f"font-family='Inter,Segoe UI,sans-serif'>{name}</text>")
    parts.append(f"<text x='{pad}' y='194' fill='{cyan}' font-size='13' letter-spacing='3' "
                 f"font-family='SF Mono,monospace'>{handle}</text>")
    if tagline:
        parts.append(f"<text x='{pad}' y='218' fill='{muted}' font-size='12.5' "
                     f"font-family='Inter,Segoe UI,sans-serif'>{tagline}</text>")

    parts.append(_location_pin(pad + 7, 246, theme))
    parts.append(f"<text x='{pad + 24}' y='250' fill='{white}' font-size='12' "
                 f"font-family='Inter,Segoe UI,sans-serif'>{location}</text>")

    # Study status chip. The chip carries the short fields only -- the full
    # degree/level/specialisation record lives in the INSTITUTION column, so
    # repeating it here would overflow the pill.
    if degree or level or status:
        chip_label = degree or status or level
        chip_w = 34 + len(chip_label) * 6.2
        parts.append(f"<rect x='{pad}' y='272' width='{chip_w:.0f}' height='30' rx='15' fill='{surf}' "
                     f"stroke='{green}' stroke-width='1'/>")
        parts.append(f"<circle cx='{pad + 17}' cy='287' r='3.5' fill='{green}'/>")
        parts.append(f"<text x='{pad + 29}' y='291' fill='{green}' font-size='10' letter-spacing='1' "
                     f"font-family='SF Mono,monospace'>{chip_label}</text>")

    parts.append(f"<line x1='{mid}' y1='70' x2='{mid}' y2='{height - pad}' stroke='{line}' stroke-width='1'/>")

    # --- column 2: emblem + institution + focus meter ---------------------
    parts.append(f"<text x='{mid + 28}' y='88' fill='{muted}' font-size='10' letter-spacing='2.2' "
                 f"font-family='SF Mono,monospace'>INSTITUTION</text>")
    parts.append(_university_emblem(mid + 66, 152, 40, theme))

    parts.append(f"<text x='{mid + 126}' y='146' fill='{white}' font-size='15' font-weight='600' "
                 f"font-family='Inter,Segoe UI,sans-serif'>{uni_name}</text>")
    if spec:
        parts.append(f"<text x='{mid + 126}' y='166' fill='{muted}' font-size='11.5' "
                     f"font-family='Inter,Segoe UI,sans-serif'>{spec}</text>")
    if level:
        parts.append(f"<text x='{mid + 126}' y='186' fill='{cyan}' font-size='11' letter-spacing='0.6' "
                     f"font-family='SF Mono,monospace'>{level}</text>")
    if status:
        parts.append(f"<text x='{mid + 126}' y='206' fill='{green}' font-size='11' "
                     f"font-family='SF Mono,monospace'>&#9679; {status}</text>")

    parts.append(f"<text x='{mid + 28}' y='248' fill='{muted}' font-size='10' letter-spacing='2.2' "
                 f"font-family='SF Mono,monospace'>CURRENT FOCUS</text>")
    if focus:
        parts.append(f"<text x='{mid + 28}' y='270' fill='{white}' font-size='12' "
                     f"font-family='Inter,Segoe UI,sans-serif'>{focus}</text>")
    seg_w, gap = 26, 6
    for i in range(8):
        filled = i < 5
        col = cyan if filled else line
        anim = (f"<animate attributeName='opacity' values='0.95;0.45;0.95' dur='{3 + i * 0.35:.1f}s' "
                f"begin='{i * 0.18:.2f}s' repeatCount='indefinite'/>") if filled else ""
        parts.append(
            f"<rect x='{mid + 28 + i * (seg_w + gap)}' y='286' width='{seg_w}' height='6' rx='3' "
            f"fill='{col}' opacity='{0.95 if filled else 0.5}'>{anim}</rect>"
        )

    parts.append(f"<line x1='{right}' y1='70' x2='{right}' y2='{height - pad}' stroke='{line}' stroke-width='1'/>")

    # --- column 3: channel rows + icon buttons ----------------------------
    parts.append(f"<text x='{right + 28}' y='88' fill='{muted}' font-size='10' letter-spacing='2.2' "
                 f"font-family='SF Mono,monospace'>CHANNELS</text>")

    social = profile.get("social", {}) or {}
    email = social.get("email", "") or ""
    gh_url = social.get("github", "https://github.com/kulraj025") or "https://github.com/kulraj025"

    # Violet only reaches 4.29:1 on the surface colour, so lift it for text.
    violet_txt = ensure_contrast(violet, surf, 4.5)
    purple_txt = ensure_contrast(purple, surf, 4.5)

    rows = [("PROFILE", gh_url.replace("https://", ""), gh_url, cyan),
            ("UNIVERSITY", "eng.deu.ac.kr", uni_url or "https://eng.deu.ac.kr/eng/index.do", violet_txt)]
    if email:
        rows.append(("EMAIL", "Send a message", f"mailto:{email}", purple_txt))

    # Each row is a caption above a pill, so the two never collide.
    y = 108
    for label, value, href, col in rows:
        parts.append(f"<text x='{right + 28}' y='{y}' fill='{muted}' font-size='9.5' letter-spacing='1.8' "
                     f"font-family='SF Mono,monospace'>{label}</text>")
        parts.append(
            f"<a href='{_esc(href)}' target='_blank' rel='noopener noreferrer'>"
            f"<rect x='{right + 22}' y='{y + 6}' width='{width - right - 50}' height='26' rx='7' "
            f"fill='{surf}' stroke='{line}' stroke-width='1'/>"
            f"<rect x='{right + 22}' y='{y + 6}' width='3' height='26' rx='1.5' fill='{col}'/>"
            f"<text x='{right + 36}' y='{y + 24}' fill='{white}' font-size='11.5' "
            f"font-family='Inter,Segoe UI,sans-serif'>{_esc(value)}</text>"
            f"<text x='{width - 42}' y='{y + 24}' text-anchor='end' fill='{col}' font-size='13' "
            f"font-family='Inter,Segoe UI,sans-serif'>&#8599;</text></a>"
        )
        y += 46

    btn_y = height - pad - 30
    buttons = [("GH", gh_url, cyan),
               ("UNI", uni_url or "https://eng.deu.ac.kr/eng/index.do", violet_txt)]
    if email:
        buttons.append(("MAIL", f"mailto:{email}", purple_txt))
    bx = right + 28
    for label, href, col in buttons:
        bw = 22 + len(label) * 7
        parts.append(
            f"<a href='{_esc(href)}' target='_blank' rel='noopener noreferrer'>"
            f"<rect x='{bx}' y='{btn_y}' width='{bw}' height='26' rx='13' fill='{surf}' "
            f"stroke='{col}' stroke-width='1'/>"
            f"<text x='{bx + bw / 2:.0f}' y='{btn_y + 17}' text-anchor='middle' fill='{col}' "
            f"font-size='9.5' letter-spacing='1.2' font-family='SF Mono,monospace'>{label}</text></a>"
        )
        bx += bw + 8

    parts.append("</svg>")
    return "\n".join(parts)


def _lang_color(lang: str) -> str:
    """GitHub language colour, lifted for legibility on the dark theme."""
    return LANG_HEX.get(lang, theme_default_violet())


def theme_default_violet() -> str:
    return "#8B5CF6"


# Canonical GitHub language colours.
LANG_HEX = {
    "Python": "#3572A5", "PHP": "#4F5D95", "C++": "#f34b7d", "C": "#555555",
    "HTML": "#e34c26", "CSS": "#563d7c", "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6", "Java": "#b07219", "Go": "#00ADD8",
    "Rust": "#dea584", "C#": "#178600", "Shell": "#89e051", "Ruby": "#701516",
    "Swift": "#F05138", "Kotlin": "#A97BFF", "Dart": "#00B4AB", "Vue": "#41b883",
}


def _constellation_geometry(languages: list[dict], width: int, height: int):
    """Return (cx, cy, [(x, y, lang, size), ...]) with every node in bounds.

    Node placement is derived from the available half-extents rather than a
    fixed pixel radius, so labels can never be pushed off-canvas.
    """
    cx, cy = width // 2, height // 2
    # Room needed to the right of a node for its label, and below for the
    # percentage line.
    max_percent = max((l.get("percent", 1) for l in languages), default=1) or 1

    # Widest label decides the horizontal reserve.
    widest = max((len(l["name"]) for l in languages), default=6)
    label_px = widest * 11 * 0.60
    node_px = 8 + (8 + 12) + 4  # max node radius plus stroke

    usable = min(cx, width - cx, cy, height - cy) - max(label_px / 2, node_px) - 22

    n = len(languages)
    inner_count = max(1, (n + 1) // 2)
    rings = [usable * 0.58, usable * 0.95]

    placed = []
    for ring_idx, count in enumerate((inner_count, n - inner_count)):
        if count <= 0:
            continue
        radius = rings[min(ring_idx, len(rings) - 1)]
        for j in range(count):
            i = j if ring_idx == 0 else inner_count + j
            lang = languages[i]
            # Offset each ring so nodes don't line up radially.
            angle = (2 * math.pi * j / count) + ring_idx * (math.pi / count) + 0.25
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            size = max(8, int(8 + (lang.get("percent", 0) / max_percent) * 12))
            placed.append((i, int(x), int(y), lang, size))
    return cx, cy, placed


def _clamp(v: float, lo: float, hi: float) -> int:
    return int(max(lo, min(hi, v)))


def _build_constellation(theme: dict, languages: list[dict], *, animated: bool) -> str:
    """Shared technology-constellation renderer (animated + static fallback)."""
    width, height = 820, 400
    cx, cy = width // 2, height // 2

    parts = [_svg_header(width, height, f"0 0 {width} {height}",
                         "Technology constellation of programming languages")]
    parts.append(_gradient_defs(theme, animated=animated))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")

    if not languages:
        parts.append(
            f"<text x='{cx}' y='{cy}' text-anchor='middle' fill='{_esc(theme.get('muted', '#94A3B8'))}' "
            f"font-size='14' font-family='SF Mono,monospace'>&#8212; no language data &#8212;</text>"
        )
        parts.append("</svg>")
        return "\n".join(parts)

    _, _, placed = _constellation_geometry(languages, width, height)
    radii = sorted({r for r in [80, 120, 160]})

    # Central node
    parts.append(
        f"<circle cx='{cx}' cy='{cy}' r='26' fill='{_esc(theme.get('violet', '#8B5CF6'))}' opacity='0.4'>"
        f"<animate attributeName='r' values='26;30;26' dur='6s' repeatCount='indefinite'/></circle>"
    )
    parts.append(
        f"<text x='{cx}' y='{cy + 4}' text-anchor='middle' fill='{_esc(theme.get('white', '#F8FAFC'))}' "
        f"font-size='9' font-family='SF Mono,monospace'>BUILD SYSTEM</text>"
    )

    for ring_radius in radii:
        pulse = (
            f"<animate attributeName='opacity' values='0.1;0.25;0.1' dur='8s' "
            f"begin='{ring_radius * 0.01:.2f}s' repeatCount='indefinite'/>"
        ) if animated else ""
        parts.append(
            f"<circle cx='{cx}' cy='{cy}' r='{ring_radius}' fill='none' "
            f"stroke='{_esc(theme.get('cyan', '#22D3EE'))}' stroke-width='0.5' opacity='0.1'>"
            f"{pulse}</circle>"
        )

    for i, x, y, lang, size in placed:
        color = ensure_contrast(_lang_color(lang["name"]), theme.get("background", "#070B17"), 3.0)
        label = _esc(lang["name"])
        percent = lang.get("percent", 0)
        angle = math.degrees(math.atan2(y - cy, x - cx))

        if animated:
            parts.append(
                f"<g transform='rotate({angle:.2f} {cx} {cy})'>"
                f"<animateTransform attributeName='transform' type='rotate' "
                f"from='{angle:.2f} {cx} {cy}' to='{angle + 360:.2f} {cx} {cy}' "
                f"dur='{30 + i * 8}s' repeatCount='indefinite'/>"
                f"<line x1='{cx}' y1='{cy}' x2='{x}' y2='{y}' "
                f"stroke='{_esc(theme.get('cyan', '#22D3EE'))}' stroke-width='0.5' opacity='0.2'/>"
                f"<circle cx='{x}' cy='{y}' r='{size}' fill='{color}' opacity='0.85'>"
                f"<animate attributeName='r' values='{size};{size + 4};{size}' dur='4s' "
                f"begin='{i * 0.5:.1f}s' repeatCount='indefinite'/></circle></g>"
            )
        else:
            parts.append(
                f"<line x1='{cx}' y1='{cy}' x2='{x}' y2='{y}' "
                f"stroke='{_esc(theme.get('cyan', '#22D3EE'))}' stroke-width='0.5' opacity='0.2'/>"
                f"<circle cx='{x}' cy='{y}' r='{size}' fill='{color}' opacity='0.85'/>"
            )

        # Labels centred under the node, clamped inside the canvas.
        lx = _clamp(x, 46, width - 46)
        ly = _clamp(y + size + 16, 24, height - 44)
        parts.append(
            f"<text x='{lx}' y='{ly}' text-anchor='middle' fill='{_esc(theme.get('white', '#F8FAFC'))}' "
            f"font-size='11' font-family='SF Mono,monospace'>{label}</text>"
        )
        parts.append(
            f"<text x='{lx}' y='{ly + 13}' text-anchor='middle' fill='{_esc(theme.get('muted', '#94A3B8'))}' "
            f"font-size='9' font-family='SF Mono,monospace'>{percent}%</text>"
        )

    # Legend, wrapped so it can never run off the right edge.
    legend_x, legend_y = 20, height - 28
    for lang in languages:
        w = 15 + len(lang["name"]) * 6
        if legend_x + w > width - 20:
            legend_x, legend_y = 20, legend_y - 16
        color = ensure_contrast(_lang_color(lang["name"]), theme.get("background", "#070B17"), 3.0)
        parts.append(f"<rect x='{legend_x}' y='{legend_y - 9}' width='10' height='10' fill='{color}' rx='2'/>")
        parts.append(
            f"<text x='{legend_x + 15}' y='{legend_y}' fill='{_esc(theme.get('muted', '#94A3B8'))}' "
            f"font-size='10' font-family='Inter,Segoe UI,sans-serif'>{_esc(lang['name'])}</text>"
        )
        legend_x += w

    parts.append("</svg>")
    return "\n".join(parts)


def build_technology_constellation(theme: dict, languages: list[dict]) -> str:
    """Animated constellation of detected programming languages."""
    return _build_constellation(theme, languages, animated=True)


def build_technology_constellation_static(theme: dict, languages: list[dict]) -> str:
    """Static fallback for the technology constellation."""
    return _build_constellation(theme, languages, animated=False)

def build_activity_dashboard(theme: dict, stats: dict, languages: list[dict]) -> str:
    """Custom animated activity composition."""
    width, height = 900, 280
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Animated GitHub activity dashboard"))
    parts.append(_gradient_defs(theme, animated=True))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")

    # Top gradient bar
    parts.append(f"<rect x='0' y='0' width='{width}' height='3' fill='url(#waveGrad)'/>")

    # Large central contribution waveform
    wave_y = 70
    if not languages:
        point_str = " ".join(f"M{i*20},{wave_y}" for i in range(width // 20 + 1))
    else:
        # Build waveform from language distribution
        n_segments = width // 20
        segs = []
        for i in range(n_segments + 1):
            lang_idx = min(i * len(languages) // n_segments, len(languages) - 1)
            pct = languages[lang_idx]["percent"] if languages else 20
            amp = max(15, min(45, pct * 0.8))
            x = i * 20
            y = wave_y + amp * (1 if i % 2 == 0 else -1) * 0.5
            segs.append(f"M{x},{wave_y - 5}Q{x+10},{y} {x+20},{wave_y}")
        point_str = " ".join(segs)
    parts.append(
        f"<path d='{point_str}' fill='none' stroke='url(#waveGrad)' stroke-width='1.5'>"
        f"<animate attributeName='d' dur='25s' repeatCount='indefinite' "
        f"values='{point_str};{point_str}'/></path>"
    )

    # Pulsing dots along waveform
    for i in range(0, width + 1, 50):
        dot_y = wave_y - 5 + random.Random(i).uniform(-5, 5)
        parts.append(
            f"<circle cx='{i}' cy='{dot_y:.1f}' r='2' fill='{theme.get('cyan', '#22D3EE')}'>"
            f"<animate attributeName='r' values='2;4;2' dur='3s' begin='{i*0.02}s' repeatCount='indefinite'/>"
            f"<animate attributeName='opacity' values='0.3;0.8;0.3' dur='3s' begin='{i*0.02}s' repeatCount='indefinite'/>"
            f"</circle>"
        )

    # Small statistic nodes
    nodes = [
        ("Public Repos", stats.get("public_repos", 0)),
        ("Followers", stats.get("followers", 0)),
        ("Following", stats.get("following", 0)),
        ("Total Stars", stats.get("total_stars", 0)),
        ("Total Forks", stats.get("total_forks", 0)),
    ]
    node_w, node_h, gap = 120, 55, 14
    start_x = (width - (node_w * 5 + gap * 4)) // 2
    node_y = 140
    for i, (label, value) in enumerate(nodes):
        x = start_x + i * (node_w + gap)
        parts.append(
            f"<rect x='{x}' y='{node_y}' width='{node_w}' height='{node_h}' rx='10' "
            f"fill='{theme.get('surface_light', '#13203A')}' stroke='{_esc(theme.get('cyan', '#22D3EE'))}' stroke-width='0.5'/>"
        )
        parts.append(
            f"<text x='{x + node_w // 2}' y='{node_y + 22}' text-anchor='middle' "
            f"fill='{_esc(theme.get('white', '#F8FAFC'))}' font-size='20' font-weight='700' "
            f"font-family='SF Mono,monospace'>{value}</text>"
        )
        parts.append(
            f"<text x='{x + node_w // 2}' y='{node_y + 40}' text-anchor='middle' "
            f"fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='9' "
            f"font-family='Inter,Segoe UI,sans-serif'>{label}</text>"
        )

    # Mini heatmap
    today = datetime.now(timezone.utc)
    heat_x = 60
    heat_y = height - 35
    for d in range(20):
        day_intensity = 0.1 + (random.Random(d + 100).random() * 0.6)
        parts.append(
            f"<rect x='{heat_x + d*10}' y='{heat_y}' width='8' height='8' rx='1' "
            f"fill='{theme.get('green', '#34D399')}' opacity='{day_intensity:.2f}'>"
            f"<animate attributeName='opacity' values='{day_intensity:.2f};{day_intensity+0.2:.2f};{day_intensity:.2f}' dur='4s' begin='{d*0.2}s' repeatCount='indefinite'/>"
            f"</rect>"
        )

    # Last refreshed
    parts.append(
        f"<text x='{width - 230}' y='{height - 18}' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='10' "
        f"font-family='SF Mono,monospace'>REFRESHED {stats.get('refresh_date', today.strftime('%Y-%m-%d'))}</text>"
    )

    parts.append("</svg>")
    return "\n".join(parts)


def build_activity_dashboard_static(theme: dict, stats: dict, languages: list[dict]) -> str:
    """Static fallback for activity dashboard."""
    width, height = 900, 280
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "GitHub activity dashboard"))
    parts.append(_gradient_defs(theme, animated=False))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='3' fill='url(#waveGrad)'/>")

    wave_y = 70
    points = " ".join(f"M{i*20},{wave_y + random.Random(i).randint(-5,5)}" for i in range(width // 20 + 1))
    parts.append(f"<path d='{points}' fill='none' stroke='url(#waveGrad)' stroke-width='1.5'/>")

    nodes = [
        ("Public Repos", stats.get("public_repos", 0)),
        ("Followers", stats.get("followers", 0)),
        ("Following", stats.get("following", 0)),
        ("Total Stars", stats.get("total_stars", 0)),
        ("Total Forks", stats.get("total_forks", 0)),
    ]
    node_w, node_h, gap = 120, 55, 14
    start_x = (width - (node_w * 5 + gap * 4)) // 2
    node_y = 140
    for i, (label, value) in enumerate(nodes):
        x = start_x + i * (node_w + gap)
        parts.append(f"<rect x='{x}' y='{node_y}' width='{node_w}' height='{node_h}' rx='10' fill='#13203A' stroke='#22D3EE' stroke-width='0.5'/>")
        parts.append(f"<text x='{x + node_w // 2}' y='{node_y + 22}' text-anchor='middle' fill='#F8FAFC' font-size='20' font-weight='700' font-family='SF Mono,monospace'>{value}</text>")
        parts.append(f"<text x='{x + node_w // 2}' y='{node_y + 40}' text-anchor='middle' fill='#94A3B8' font-size='9' font-family='Inter,Segoe UI,sans-serif'>{label}</text>")

    heat_x = 60
    heat_y = height - 35
    for d in range(20):
        day_intensity = 0.1 + (random.Random(d + 100).random() * 0.6)
        parts.append(f"<rect x='{heat_x + d*10}' y='{heat_y}' width='8' height='8' rx='1' fill='#34D399' opacity='{day_intensity:.2f}'/>")

    parts.append(f"<text x='{width - 230}' y='{height - 18}' fill='#94A3B8' font-size='10' font-family='SF Mono,monospace'>REFRESHED {stats.get('refresh_date', '2026-09-25')}</text>")
    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Contributions
# ---------------------------------------------------------------------------

def build_contributions(theme: dict, events: list[dict]) -> str:
    """Custom contribution visualization from public events."""
    width, height = 900, 180
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "GitHub contribution visualization"))
    parts.append(_gradient_defs(theme, animated=True))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='2' fill='url(#waveGrad)'/>")

    # Generate activity levels from events
    rng = random.Random(77)
    levels = [rng.randint(0, 4) for _ in range(56)]  # 8 weeks x 7 days = 56 blocks
    # Boost based on events
    for ev in events:
        if ev.get("type") in ("PushEvent", "CreateEvent", "PullRequestEvent"):
            idx = int(rng.random() * 56)
            levels[idx] = min(4, levels[idx] + 1)

    cols = 8
    rows = 7
    block_size = 14
    block_gap = 3
    start_x = 40
    start_y = 30

    for col in range(cols):
        for row in range(rows):
            idx = col * rows + row
            if idx >= len(levels):
                break
            level = levels[idx]
            x = start_x + col * (block_size + block_gap)
            y = start_y + row * (block_size + block_gap)
            intensity = level / 4
            color = theme.get("green", "#34D399")
            opacity = 0.15 + intensity * 0.65
            parts.append(
                f"<rect x='{x}' y='{y}' width='{block_size}' height='{block_size}' rx='2' "
                f"fill='{color}' opacity='{opacity:.2f}'>"
                f"<animate attributeName='opacity' values='{opacity:.2f};{opacity+0.2:.2f};{opacity:.2f}' "
                f"dur='6s' begin='{idx*0.1}s' repeatCount='indefinite'/>"
                f"<animate attributeName='fill' values='{color};{_esc(theme.get('cyan', '#22D3EE'))};{color}' "
                f"dur='20s' begin='{idx*0.2}s' repeatCount='indefinite'/>"
                f"</rect>"
            )

    # Waveform path at bottom
    wave_y = height - 30
    points = []
    for i in range(width // 15 + 1):
        level = levels[min(i * len(levels) // (width // 15 + 1), len(levels) - 1)]
        amp = level * 3
        y = wave_y - amp
        if i == 0:
            points.append(f"M{i*15},{y}")
        else:
            points.append(f"L{i*15},{y}")
    points += " L" + str(width) + "," + str(height) + " L0," + str(height) + " Z"
    point_str = "".join(points)
    parts.append(f"<path d='{point_str}' fill='{theme.get('cyan', '#22D3EE')}' opacity='0.08'/>")

    parts.append(f"<text x='40' y='{height - 8}' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='10' font-family='SF Mono,monospace'>ACTIVITY · {len([e for e in events if e.get('type') in ('PushEvent','CreateEvent','PullRequestEvent')])} recent signals</text>")
    parts.append("</svg>")
    return "\n".join(parts)


def build_contributions_static(theme: dict, events: list[dict]) -> str:
    """Static fallback for contributions."""
    width, height = 900, 180
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Contribution heatmap"))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='2' fill='url(#waveGrad)'/>")

    rng = random.Random(77)
    levels = [rng.randint(0, 4) for _ in range(56)]
    cols, rows = 8, 7
    block_size = 14
    block_gap = 3
    start_x = 40
    start_y = 30

    for col in range(cols):
        for row in range(rows):
            idx = col * rows + row
            if idx >= len(levels):
                break
            level = levels[idx]
            x = start_x + col * (block_size + block_gap)
            y = start_y + row * (block_size + block_gap)
            intensity = level / 4
            opacity = 0.15 + intensity * 0.65
            parts.append(f"<rect x='{x}' y='{y}' width='{block_size}' height='{block_size}' rx='2' fill='#34D399' opacity='{opacity:.2f}'/>")

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Learning Path
# ---------------------------------------------------------------------------

def line_color() -> str:
    """Shared hairline colour for dividers and tracks."""
    return "#233454"


def _learning_nodes() -> list[tuple[str, str]]:
    return [
        ("Intelligence Computing", "Active"),
        ("AI Projects", "Current"),
        ("Machine Learning", "Learning"),
        ("Production Systems", "Planned"),
    ]


def _build_learning_path(theme: dict, *, animated: bool) -> str:
    """Shared learning-path renderer (animated + static fallback).

    Nodes are spaced evenly across the full width and their labels wrap to two
    lines. The previous fixed 70px step pushed the first label off the left
    edge and made the middle labels collide.
    """
    width, height = 700, 170
    nodes = _learning_nodes()
    node_y = height // 2
    slot = width / len(nodes)
    cyan = theme.get("cyan", "#22D3EE")
    muted = _esc(theme.get("muted", "#94A3B8"))

    parts = [_svg_header(width, height, f"0 0 {width} {height}", "Learning path timeline")]
    parts.append(_gradient_defs(theme, animated=animated))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='2' fill='url(#waveGrad)'/>")

    # Baseline track
    parts.append(
        f"<line x1='{slot / 2:.0f}' y1='{node_y}' x2='{width - slot / 2:.0f}' y2='{node_y}' "
        f"stroke='{line_color()}' stroke-width='1' opacity='0.35'/>"
    )

    for i, (label, status) in enumerate(nodes):
        cx = int(slot * (i + 0.5))
        active = i < 3
        color = cyan if active else theme.get("muted", "#94A3B8")
        opacity = "1" if active else "0.35"

        if active and animated:
            parts.append(
                f"<line x1='{cx}' y1='{node_y}' x2='{cx + int(slot)}' y2='{node_y}' "
                f"stroke='{cyan}' stroke-width='1' stroke-dasharray='4,3' opacity='0.35'>"
                f"<animate attributeName='stroke-dashoffset' values='0;7;0' dur='4s' "
                f"begin='{i * 0.5:.1f}s' repeatCount='indefinite'/></line>"
            )

        pulse = (
            f"<animate attributeName='r' values='6;8;6' dur='3s' begin='{i * 0.8:.1f}s' repeatCount='indefinite'/>"
            if (active and animated) else ""
        )
        parts.append(f"<circle cx='{cx}' cy='{node_y}' r='6' fill='{color}' opacity='{opacity}'>{pulse}</circle>")

        if active:
            parts.append(
                f"<text x='{cx}' y='{node_y - 14}' text-anchor='middle' fill='{color}' "
                f"font-size='8' font-family='SF Mono,monospace'>&#9679; {_esc(status)}</text>"
            )

        # Labels wrap to at most two lines within half a slot.
        budget = slot / 2 - 6
        for li, line in enumerate(fit_text(label, budget, 10, mono=True, max_lines=2)):
            parts.append(
                f"<text x='{cx}' y='{node_y + 24 + li * 12}' text-anchor='middle' fill='{muted}' "
                f"font-size='10' font-family='SF Mono,monospace'>{_esc(line)}</text>"
            )

    parts.append("</svg>")
    return "\n".join(parts)


def build_learning_path(theme: dict, focus: str) -> str:
    """Animated learning path timeline."""
    return _build_learning_path(theme, animated=True)


def build_learning_path_static(theme: dict, focus: str) -> str:
    """Static fallback for learning path."""
    return _build_learning_path(theme, animated=False)


# ---------------------------------------------------------------------------
# Footer Horizon
# ---------------------------------------------------------------------------

def build_footer_horizon(theme: dict, profile: dict) -> str:
    """Small abstract ocean/city horizon footer."""
    width, height = 900, 140
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Busan digital horizon footer"))
    parts.append(_gradient_defs(theme, animated=True))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")

    horizon_y = height - 50

    # Waves
    for layer, (amp, freq, ph) in enumerate([(12, 2.5, 0), (8, 3.5, 1.5), (6, 5.0, 3.0)]):
        path = _sine_wave_path(width, horizon_y, amp, freq, ph)
        parts.append(f"<path d='{path}' fill='none' stroke='url(#waveGrad)' stroke-width='1' opacity='0.4'/>")

    # City lights (static dots with subtle pulse)
    rng = random.Random(99)
    for x in range(30, width - 10, 25):
        y = horizon_y - rng.randint(5, 30)
        r = rng.randint(1, 2)
        parts.append(
            f"<circle cx='{x}' cy='{y}' r='{r}' fill='{theme.get('blue', '#38BDF8')}' opacity='0.5'>"
            f"<animate attributeName='opacity' values='0.3;0.8;0.3' dur='5s' begin='{x*0.02}s' repeatCount='indefinite'/>"
            f"</circle>"
        )

    # University + links
    university = _esc(profile.get("university", {}).get("institution", "Dong-eui University"))
    university_url = _esc(profile.get("university", {}).get("website", ""))
    github_url = _esc(profile.get("social", {}).get("github", "https://github.com/kulraj025"))
    email = _esc(profile.get("social", {}).get("email", ""))
    location = _esc(profile.get("location", "Busan, South Korea"))

    parts.append(f"<text x='40' y='35' fill='{_esc(theme.get('white', '#F8FAFC'))}' font-size='13' font-weight='600' font-family='Inter,Segoe UI,sans-serif'>{university}</text>")
    parts.append(f"<text x='40' y='52' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='11' font-family='Inter,Segoe UI,sans-serif'>{location}</text>")

    # Animated refresh indicator, right-aligned so it cannot overflow.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    refresh_label = f"AUTO-REFRESH {today}"
    refresh_w = len(refresh_label) * 10 * 0.60
    refresh_x = width - 20
    parts.append(
        f"<circle cx='{refresh_x - refresh_w - 10:.0f}' cy='38' r='3' fill='{theme.get('green', '#34D399')}'>"
        f"<animate attributeName='opacity' values='0.6;1;0.6' dur='3s' repeatCount='indefinite'/>"
        f"</circle>"
    )
    parts.append(f"<text x='{refresh_x}' y='42' text-anchor='end' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='10' font-family='SF Mono,monospace'>{refresh_label}</text>")

    # Links: GitHub + University + Email
    parts.append(
        f"<a href='{github_url}'>"
        f"<text x='40' y='{height - 15}' fill='{_esc(theme.get('cyan', '#22D3EE'))}' font-size='11' font-family='Inter,Segoe UI,sans-serif'>github.com/kulraj025</text>"
        f"</a>"
    )
    parts.append(
        f"<a href='{university_url}'>"
        f"<text x='{width // 2}' y='{height - 15}' text-anchor='middle' fill='{_esc(theme.get('blue', '#38BDF8'))}' font-size='11' font-family='Inter,Segoe UI,sans-serif'>{university}</text>"
        f"</a>"
    )
    parts.append(
        f"<a href='mailto:{email}'>"
        f"<text x='{width - 130}' y='{height - 15}' text-anchor='end' fill='{_esc(theme.get('violet', '#8B5CF6'))}' font-size='11' font-family='Inter,Segoe UI,sans-serif'>Email</text>"
        f"</a>"
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Project Gallery
# ---------------------------------------------------------------------------

# Deterministic accent colors per project (based on language).
# These are GitHub's language colours. Several fail WCAG AA on this dark
# theme (e.g. C++ #006699 is 2.6:1 on #13203A), so they are passed through
# ensure_contrast() at render time rather than hand-tuned here.
LANG_ACCENTS = {
    "Python": "#FFD700",
    "PHP": "#4F95FF",
    "C++": "#006699",
    "HTML": "#E34F2A",
    "CSS": "#1572B6",
    "JavaScript": "#F7DF1E",
    "TypeScript": "#3178C6",
    "Java": "#C43B2B",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "C#": "#239CCC",
}

# Simple SVG icon paths per language category
def _empty_gallery_fallback(theme: dict) -> str:
    """Return a minimal SVG when no projects are available."""
    width, height = 600, 120
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Project gallery"))
    parts.append(_gradient_defs(theme, animated=False))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(
        f"<text x='{width//2}' y='{height//2}' text-anchor='middle' "
        f"fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='14' "
        f"font-family='Inter,Segoe UI,sans-serif'>No featured projects available</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


LANG_ICONS = {
    "Python": "<circle cx='0' cy='0' r='10' fill='#FFD700'/><rect x='-6' y='-4' width='12' height='8' fill='#000'/>",
    "PHP": "<path d='M0,0 L8,-10 L12,-10 L16,0 L12,10 L8,10 Z' fill='#4F95FF'/>",
    "C++": "<rect x='-9' y='-9' width='18' height='18' rx='3' fill='#006699'/>"
           "<path d='M-5,1 L-1,-4 L3,1' fill='none' stroke='#F8FAFC' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'/>"
           "<line x1='3' y1='4' x2='7' y2='4' stroke='#F8FAFC' stroke-width='1.6' stroke-linecap='round'/>",
    "HTML": "<path d='M0,-10 L10,0 L0,10 L-10,0 Z' fill='#E34F2A'/>",
    "CSS": "<rect x='-8' y='-4' width='16' height='8' fill='#1572B6'/>",
    "JavaScript": "<path d='M0,-10 L6,8 L-6,8 Z' fill='#F7DF1E'/>",
    "Java": "<circle cx='0' cy='0' r='8' fill='#C43B2B'/><rect x='-4' y='0' width='8' height='8' fill='#C43B2B'/>",
}

def _lang_icon(lang: str, accent: str, size: int = 12) -> str:
    # Generate a simple deterministic icon based on language name
    svg = LANG_ICONS.get(lang, f"<circle cx='0' cy='0' r='{size}' fill='{accent}'/>")
    # Scale icon to fit
    return f"<g transform='scale(0.7)'>{svg}</g>"

# Abstract illustration generators (deterministic per project name)
def _project_illustration(name: str, accent: str) -> str:
    """Generate a small abstract illustration unique to the project."""
    # Use hash of name to create deterministic variation
    h = hash(name) % 1000
    style = h % 4
    parts = []

    if style == 0:
        # Stacked blocks (like a build system)
        for i in range(3):
            y = -6 + i * 5
            parts.append(f"<rect x='-8' y='{y}' width='16' height='4' rx='1' fill='{accent}' opacity='{0.5 + i*0.15}'/>")
    elif style == 1:
        # Network node
        parts.append(f"<circle cx='0' cy='0' r='6' fill='{accent}' opacity='0.6'/>")
        for angle in range(0, 360, 60):
            import math as m
            x = 9 * m.cos(m.radians(angle))
            y = 9 * m.sin(m.radians(angle))
            parts.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2' fill='{accent}' opacity='0.4'/>")
    elif style == 2:
        # Wave
        points = []
        for i in range(17):
            import math as m
            y = -4 + 2 * m.sin(i * 0.5 + h * 0.1)
            points.append(f"{i-8},{y:.1f}")
        parts.append(f"<polyline points='{' '.join(points)}' fill='none' stroke='{accent}' stroke-width='1.5' opacity='0.6'/>")
    else:
        # Terminal window
        parts.append(f"<rect x='-8' y='-6' width='16' height='10' rx='2' fill='#0D1528' stroke='{accent}' stroke-width='1'/>")
        parts.append(f"<circle cx='-4' cy='-2' r='0.5' fill='{accent}'/>")
        parts.append(f"<rect x='-6' y='0' width='12' height='2' fill='{accent}' opacity='0.5'/>")
    return "<g>" + "".join(parts) + "</g>"


def _build_gallery(theme: dict, projects: list[dict], *, animated: bool) -> str:
    """Shared project-gallery renderer.

    One implementation drives both the animated gallery and the static
    fallback so the two can never drift apart (they previously did, and the
    static copy kept a 120-character untruncated description that overflowed
    the card).
    """
    if not projects:
        return _empty_gallery_fallback(theme)

    width = 900
    card_w = 270
    card_h = 160
    cols = 3
    gap_x = 20
    gap_y = 30
    margin_x = 20
    margin_y = 20
    rows = (len(projects) + cols - 1) // cols
    height = margin_y * 2 + card_h * rows + gap_y * (rows - 1)

    card_bg = theme.get("surface_light", "#13203A")
    page_bg = theme.get("background", "#070B17")
    white = theme.get("white", "#F8FAFC")
    muted = theme.get("muted", "#94A3B8")
    surf = theme.get("surface", "#0D1528")

    parts = [_svg_header(width, height, f"0 0 {width} {height}", "Featured project gallery")]
    parts.append(_gradient_defs(theme, animated=animated))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='3' fill='url(#waveGrad)'/>")

    for i, proj in enumerate(projects):
        col = i % cols
        row = i // cols
        x = margin_x + col * (card_w + gap_x)
        y = margin_y + row * (card_h + gap_y)

        lang = proj.get("language") or "Unknown"
        base_accent = LANG_ACCENTS.get(lang, theme.get("violet", "#8B5CF6"))
        # GitHub language colours are tuned for light backgrounds; lift them
        # until they pass WCAG AA on our dark surfaces.
        accent = ensure_contrast(base_accent, card_bg, 4.5)
        btn_fill = ensure_contrast(base_accent, page_bg, 4.5)
        accent_esc = _esc(accent)
        lang_esc = _esc(lang)
        stars = proj.get("stars", 0)
        updated = proj.get("pushed_at", "")[:10]
        repo_url = _esc(proj.get("html_url", ""))
        demo_url = proj.get("homepage")

        parts.append(
            f"<rect x='{x}' y='{y}' width='{card_w}' height='{card_h}' rx='10' "
            f"fill='{card_bg}' stroke='{accent_esc}' stroke-width='1'/>"
        )
        if animated:
            parts.append(
                f"<defs><linearGradient id='grad{i}' x1='0' y1='0' x2='1' y2='0'>"
                f"<stop offset='0%' stop-color='{accent_esc}'>"
                f"<animate attributeName='stop-color' values='{accent_esc};{btn_fill};{accent_esc}' "
                f"dur='{14 + i * 3}s' begin='{i * 0.45:.2f}s' repeatCount='indefinite'/></stop>"
                f"<stop offset='100%' stop-color='transparent'/>"
                f"</linearGradient></defs>"
            )
            # Slow staggered shimmer travelling across each card's top edge.
            parts.append(f"<rect x='{x}' y='{y}' width='{card_w}' height='3' fill='url(#grad{i})'/>")
            parts.append(
                f"<rect x='{x}' y='{y}' width='{card_w}' height='3' fill='{accent_esc}' opacity='0.25'>"
                f"<animate attributeName='opacity' values='0.05;0.45;0.05' dur='{9 + i * 1.7:.1f}s' "
                f"begin='{i * 0.6:.1f}s' repeatCount='indefinite'/></rect>"
            )
        else:
            parts.append(
                f"<rect x='{x}' y='{y}' width='{card_w}' height='3' fill='{accent_esc}' opacity='0.5'/>"
            )

        parts.append(
            f"<g transform='translate({x + 20},{y + 25})'>"
            f"{_lang_icon(lang, accent)}"
            f"<g transform='translate(50,0)'>{_project_illustration(proj['name'], accent)}</g>"
            + (
                f"<animateTransform attributeName='transform' type='translate' "
                f"values='0 0; 0 -2; 0 0' dur='{7 + i * 1.3:.1f}s' begin='{i * 0.7:.1f}s' "
                f"repeatCount='indefinite' additive='sum'/>"
                if animated else ""
            )
            + "</g>"
        )

        # Name: one line, ellipsised to the card width.
        name_lines = fit_text(proj["name"], card_w - 40, 14, max_lines=1)
        parts.append(
            f"<text x='{x + 20}' y='{y + 55}' fill='{_esc(white)}' font-size='14' "
            f"font-weight='700' font-family='Inter,Segoe UI,sans-serif'>"
            f"{_esc(name_lines[0] if name_lines else '')}</text>"
        )

        # Description: wrapped, at most two lines.
        for li, line in enumerate(fit_text(proj.get("description", ""), card_w - 40, 10, max_lines=2)):
            parts.append(
                f"<text x='{x + 20}' y='{y + 72 + li * 13}' fill='{_esc(muted)}' font-size='10' "
                f"font-family='Inter,Segoe UI,sans-serif'>{_esc(line)}</text>"
            )

        # Compact metadata strip
        meta_y = y + 100
        parts.append(
            f"<rect x='{x}' y='{meta_y}' width='{card_w}' height='2' "
            f"fill='{accent_esc}' opacity='0.35'/>"
        )
        parts.append(
            f"<text x='{x + 20}' y='{meta_y + 15}' fill='{accent_esc}' font-size='10' "
            f"font-weight='600' font-family='SF Mono,monospace'>{lang_esc}</text>"
        )
        parts.append(
            f"<text x='{x + 20}' y='{meta_y + 30}' fill='{_esc(muted)}' font-size='9.5' "
            f"font-family='SF Mono,monospace'>\u2605 {stars}  {updated}</text>"
        )

        btn_y = y + card_h - 30
        parts.append(
            f"<a href='{repo_url}' target='_blank' rel='noopener noreferrer'>"
            f"<rect x='{x + 20}' y='{btn_y}' width='100' height='24' rx='6' "
            f"fill='{surf}' stroke='{accent_esc}' stroke-width='1'/>"
            f"<text x='{x + 70}' y='{btn_y + 16}' text-anchor='middle' fill='{accent_esc}' "
            f"font-size='11' font-family='Inter,Segoe UI,sans-serif'>Repository</text></a>"
        )
        if demo_url:
            # Dark label needs a light button fill to stay legible.
            label_on_btn = page_bg if contrast_ratio(btn_fill, page_bg) >= 4.5 else "#070B17"
            parts.append(
                f"<a href='{_esc(demo_url)}' target='_blank' rel='noopener noreferrer'>"
                f"<rect x='{x + 135}' y='{btn_y}' width='100' height='24' rx='6' fill='{btn_fill}'/>"
                f"<text x='{x + 185}' y='{btn_y + 16}' text-anchor='middle' fill='{label_on_btn}' "
                f"font-size='11' font-weight='600' font-family='Inter,Segoe UI,sans-serif'>"
                f"Live Demo</text></a>"
            )

    parts.append("</svg>")
    return "\n".join(parts)


def build_project_gallery(theme: dict, projects: list[dict]) -> str:
    """Premium project gallery as an animated SVG with cards."""
    return _build_gallery(theme, projects, animated=True)


def build_project_gallery_static(theme: dict, projects: list[dict]) -> str:
    """Static fallback for project gallery."""
    return _build_gallery(theme, projects, animated=False)


# ---------------------------------------------------------------------------
# Asset generation
# ---------------------------------------------------------------------------

def generate_all(theme: dict, profile: dict, stats: dict, languages: list[dict],
                 events: list[dict], projects: list[dict]) -> dict:
    """Generate all SVG assets and write them to disk.

    Returns a dict mapping asset filename to its path.
    """
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    refresh_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stats["refresh_date"] = refresh_date
    if "social" not in profile:
        profile["social"] = {"github": "https://github.com/kulraj025"}

    today = datetime.now(timezone.utc)

    assets = {
        "hero.svg": build_hero(theme, stats, animated=True),
        "identity.svg": build_identity_panel(theme, profile),
        "identity-card.svg": build_identity_card(theme, profile),
        "technology-constellation.svg": build_technology_constellation(theme, languages),
        "activity-dashboard.svg": build_activity_dashboard(theme, stats, languages),
        "contributions.svg": build_contributions(theme, events),
        "learning-path.svg": build_learning_path(theme, profile.get("current_focus", "")),
        "footer-horizon.svg": build_footer_horizon(theme, profile),
        "project-gallery.svg": build_project_gallery(theme, projects),
    }

    # Static fallbacks (written to assets/static/)
    static_assets = {
        "hero-fallback.svg": build_hero_fallback(theme, stats),
        "technology-constellation.svg": build_technology_constellation_static(theme, languages),
        "activity-dashboard.svg": build_activity_dashboard_static(theme, stats, languages),
        "contributions.svg": build_contributions_static(theme, events),
        "learning-path.svg": build_learning_path_static(theme, profile.get("current_focus", "")),
        "project-gallery.svg": build_project_gallery_static(theme, projects),
        "footer-horizon.svg": build_footer_horizon(theme, profile),
    }

    written = {}
    for filename, content in assets.items():
        path = ASSETS_DIR / filename
        path.write_text(content, encoding="utf-8")
        written[filename] = path

    for filename, content in static_assets.items():
        path = STATIC_DIR / filename
        path.write_text(content, encoding="utf-8")
        written[f"static/{filename}"] = path

    return written


if __name__ == "__main__":
    print("Use scripts/generate_profile.py to generate all assets.")
