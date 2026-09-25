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
# Technology Constellation
# ---------------------------------------------------------------------------

LANG_COLORS = {
    "Python": "#FFD700",
    "JavaScript": "#F7DF1E",
    "TypeScript": "#3178C6",
    "PHP": "#8892BF",
    "C++": "#006699",
    "C": "#283593",
    "HTML": "#E34F2A",
    "CSS": "#1572B6",
    "Java": "#C43B2B",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "Ruby": "#CC2",
    "Shell": "#89E051",
    "C#": "#239",
    "Vue": "#42B883",
    "React": "#61DAFB",
    "Dart": "#00B4D4",
    "Kotlin": "#0095D5",
    "Swift": "#FF4",
}


def _lang_color(lang: str) -> str:
    for name, color in LANG_COLORS.items():
        if lang.lower() == name.lower():
            return color
    return "#94A3B8"


def build_technology_constellation(theme: dict, languages: list[dict]) -> str:
    """Animated constellation of detected programming languages."""
    width, height = 820, 320
    cx, cy = width // 2, height // 2 - 10

    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Technology constellation of programming languages"))
    parts.append(_gradient_defs(theme, animated=True))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")

    if not languages:
        parts.append(f"<text x='{cx}' y='{cy}' text-anchor='middle' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='14' font-family='SF Mono,monospace'>— no language data —</text>")
        parts.append("</svg>")
        return "\n".join(parts)

    # Central node
    parts.append(
        f"<circle cx='{cx}' cy='{cy}' r='26' fill='{_esc(theme.get('violet', '#8B5CF6'))}' opacity='0.4'>"
        f"<animate attributeName='r' values='26;30;26' dur='6s' repeatCount='indefinite'/>"
        f"</circle>"
    )
    parts.append(
        f"<text x='{cx}' y='{cy + 4}' text-anchor='middle' fill='{_esc(theme.get('white', '#F8FAFC'))}' "
        f"font-size='9' font-family='SF Mono,monospace'>BUILD SYSTEM</text>"
    )

    # Orbit rings
    max_percent = max(l.get("percent", 1) for l in languages) or 1
    for ring_radius in [110, 150, 185]:
        parts.append(
            f"<circle cx='{cx}' cy='{cy}' r='{ring_radius}' fill='none' "
            f"stroke='{_esc(theme.get('cyan', '#22D3EE'))}' stroke-width='0.5' opacity='0.1'>"
            f"<animate attributeName='opacity' values='0.1;0.25;0.1' dur='8s' begin='{ring_radius*0.01}s' repeatCount='indefinite'/>"
            f"</circle>"
        )

    # Orbiting nodes
    n = len(languages)
    for i, lang in enumerate(languages):
        angle = (2 * math.pi * i) / n + (i * 0.3)
        radius = 110 + (i * 25) if i < 3 else 100 + (i * 22)
        x = cx + int(radius * math.cos(angle))
        y = cy + int(radius * math.sin(angle))
        size = max(8, int(8 + (lang["percent"] / max_percent) * 12))
        color = _lang_color(lang["name"])
        label = _esc(lang["name"])
        percent = lang.get("percent", 0)

        # Orbit animation
        parts.append(
            f"<g transform='rotate({math.degrees(angle)} {cx} {cy})'>"
            f"<animateTransform attributeName='transform' type='rotate' "
            f"from='{math.degrees(angle)} {cx} {cy}' "
            f"to='{math.degrees(angle) + 360} {cx} {cy}' "
            f"dur='{(30 + i * 8)}s' repeatCount='indefinite'/>"
            f"<line x1='{cx}' y1='{cy}' x2='{x}' y2='{y}' "
            f"stroke='{_esc(theme.get('cyan', '#22D3EE'))}' stroke-width='0.5' opacity='0.2'/>"
            f"<circle cx='{x}' cy='{y}' r='{size}' fill='{color}' opacity='0.8'>"
            f"<animate attributeName='r' values='{size};{size+4};{size}' dur='4s' begin='{i*0.5}s' repeatCount='indefinite'/>"
            f"</circle>"
            f"</g>"
        )

        # Label
        parts.append(
            f"<text x='{x + 12}' y='{y + 4}' fill='{_esc(theme.get('white', '#F8FAFC'))}' "
            f"font-size='11' font-family='SF Mono,monospace'>{label}</text>"
        )
        parts.append(
            f"<text x='{x + 12}' y='{y + 17}' fill='{_esc(theme.get('muted', '#94A3B8'))}' "
            f"font-size='9' font-family='SF Mono,monospace'>{percent}%</text>"
        )

    # Legend
    legend_x = 20
    for lang in languages:
        color = _lang_color(lang["name"])
        label = _esc(lang["name"])
        parts.append(f"<rect x='{legend_x}' y='{height - 30}' width='10' height='10' fill='{color}' rx='2'/>")
        parts.append(f"<text x='{legend_x + 15}' y='{height - 22}' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='10' font-family='Inter,Segoe UI,sans-serif'>{label}</text>")
        legend_x += 15 + len(lang["name"]) * 6

    parts.append("</svg>")
    return "\n".join(parts)


def build_technology_constellation_static(theme: dict, languages: list[dict]) -> str:
    """Static fallback for the technology constellation."""
    width, height = 820, 320
    cx, cy = width // 2, height // 2 - 10
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Technology constellation"))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")

    if not languages:
        parts.append(f"<text x='{cx}' y='{cy}' text-anchor='middle' fill='#94A3B8' font-size='14'>— no language data —</text>")
        parts.append("</svg>")
        return "\n".join(parts)

    parts.append(f"<circle cx='{cx}' cy='{cy}' r='26' fill='#8B5CF6' opacity='0.4'/>")
    parts.append(f"<text x='{cx}' y='{cy + 4}' text-anchor='middle' fill='#F8FAFC' font-size='9' font-family='SF Mono,monospace'>BUILD SYSTEM</text>")

    n = len(languages)
    for i, lang in enumerate(languages):
        angle = (2 * math.pi * i) / n + (i * 0.3)
        radius = 110 + (i * 25) if i < 3 else 100 + (i * 22)
        x = cx + int(radius * math.cos(angle))
        y = cy + int(radius * math.sin(angle))
        size = max(8, int(8 + (lang["percent"] / 100) * 12))
        color = _lang_color(lang["name"])
        label = _esc(lang["name"])
        parts.append(f"<line x1='{cx}' y1='{cy}' x2='{x}' y2='{y}' stroke='#22D3EE' stroke-width='0.5' opacity='0.2'/>")
        parts.append(f"<circle cx='{x}' cy='{y}' r='{size}' fill='{color}'/>")
        parts.append(f"<text x='{x + 12}' y='{y + 4}' fill='#F8FAFC' font-size='11' font-family='SF Mono,monospace'>{label}</text>")

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Activity Dashboard
# ---------------------------------------------------------------------------

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

def build_learning_path(theme: dict, focus: str) -> str:
    """Animated learning path timeline."""
    width, height = 700, 170
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Learning path timeline"))
    parts.append(_gradient_defs(theme, animated=True))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='2' fill='url(#waveGrad)'/>")

    # Path nodes
    nodes = [
        ("Intelligence Computing", "Active"),
        ("AI Projects", "Current"),
        ("Machine Learning", "Learning"),
        ("Production Systems", "Planned"),
    ]
    node_x = 60
    node_y = height // 2
    for i, (label, status) in enumerate(nodes):
        active = i < 3  # first 3 are active
        color = theme.get("cyan", "#22D3EE") if active else theme.get("muted", "#94A3B8")
        opacity = "1" if active else "0.3"
        parts.append(
            f"<circle cx='{node_x}' cy='{node_y}' r='6' fill='{color}' opacity='{opacity}'>"
        )
        if active:
            parts.append(f"<animate attributeName='r' values='6;8;6' dur='3s' begin='{i*0.8}s' repeatCount='indefinite'/>")
        parts.append(f"</circle>")

        # Label
        label_esc = _esc(label)
        status_esc = _esc(status)
        parts.append(
            f"<text x='{node_x}' y='{node_y + 22}' text-anchor='middle' "
            f"fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='10' font-family='SF Mono,monospace'>"
            f"{label_esc}</text>"
        )
        if active:
            parts.append(
                f"<text x='{node_x}' y='{node_y - 12}' text-anchor='middle' "
                f"fill='{color}' font-size='8' font-family='SF Mono,monospace'>● {status_esc}</text>"
            )

        # Connect to next node
        if i < len(nodes) - 1:
            next_x = node_x
            line_x = node_x + 70
            parts.append(
                f"<line x1='{line_x}' y1='{node_y}' x2='{line_x + 40}' y2='{node_y}' "
                f"stroke='{theme.get('cyan', '#22D3EE')}' stroke-width='1' stroke-dasharray='4,3' opacity='0.3'>"
                f"<animate attributeName='stroke-dashoffset' values='0;7;0' dur='4s' begin='{i*0.5}s' repeatCount='indefinite'/>"
                f"</line>"
            )
            node_x = line_x + 40

    parts.append("</svg>")
    return "\n".join(parts)


def build_learning_path_static(theme: dict, focus: str) -> str:
    """Static fallback for learning path."""
    width, height = 700, 170
    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Learning path"))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='2' fill='url(#waveGrad)'/>")

    nodes = ["Intelligence Computing", "AI Projects", "Machine Learning", "Production Systems"]
    node_x = 60
    node_y = height // 2
    for i, label in enumerate(nodes):
        active = i < 3
        color = theme.get("cyan", "#22D3EE") if active else theme.get("muted", "#94A3B8")
        opacity = "1" if active else "0.3"
        parts.append(f"<circle cx='{node_x}' cy='{node_y}' r='6' fill='{color}' opacity='{opacity}'/>")
        parts.append(f"<text x='{node_x}' y='{node_y + 22}' text-anchor='middle' fill='#94A3B8' font-size='10' font-family='SF Mono,monospace'>{_esc(label)}</text>")
        if i < len(nodes) - 1:
            parts.append(f"<line x1='{node_x + 10}' y1='{node_y}' x2='{node_x + 60}' y2='{node_y}' stroke='#22D3EE' stroke-width='1' stroke-dasharray='4,3' opacity='0.3'/>")
            node_x += 70

    parts.append("</svg>")
    return "\n".join(parts)


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

    # Animated refresh indicator
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    refresh_x = width - 100
    parts.append(
        f"<circle cx='{refresh_x}' cy='38' r='3' fill='{theme.get('green', '#34D399')}'>"
        f"<animate attributeName='opacity' values='0.6;1;0.6' dur='3s' repeatCount='indefinite'/>"
        f"</circle>"
    )
    parts.append(f"<text x='{width - 90}' y='42' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='10' font-family='SF Mono,monospace'>AUTO-REFRESH {today}</text>")

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

    parts.append("</svg>")
    return "\n".join(parts)



# ---------------------------------------------------------------------------
# Project Gallery
# ---------------------------------------------------------------------------

# Deterministic accent colors per project (based on language)
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
    "C#": "#239",
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
    "C++": "<rect x='-8' y='-8' width='16' height='16' fill='#006699' opacity='0.7'/><text x='0' y='4' text-anchor='middle' fill='#006699' font-size='10' font-weight='700'>C++</text>",
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


def build_project_gallery(theme: dict, projects: list[dict]) -> str:
    """Premium project gallery as an animated SVG with cards."""
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

    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Featured project gallery"))
    parts.append(_gradient_defs(theme, animated=True))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='3' fill='url(#waveGrad)'/>")

    for i, proj in enumerate(projects):
        col = i % cols
        row = i // cols
        x = margin_x + col * (card_w + gap_x)
        y = margin_y + row * (card_h + gap_y)

        lang = proj.get("language") or "Unknown"
        accent = LANG_ACCENTS.get(lang, theme.get("violet", "#8B5CF6"))
        accent_esc = _esc(accent)
        name_esc = _esc(proj["name"])
        desc_esc = _esc(proj.get("description", "")[:120])
        lang_esc = _esc(lang)
        stars = proj.get("stars", 0)
        forks = proj.get("forks", 0)
        updated = proj.get("pushed_at", "")[:10]
        repo_url = _esc(proj.get("html_url", ""))
        demo_url = proj.get("homepage")

        # Card background
        parts.append(
            f"<rect x='{x}' y='{y}' width='{card_w}' height='{card_h}' rx='10' "
            f"fill='{theme.get('surface_light', '#13203A')}' stroke='{accent_esc}' stroke-width='1'/>"
        )
        # Gradient top line
        parts.append(
            f"<defs><linearGradient id='grad{i}' x1='0' y1='0' x2='1' y2='0'>"
            f"<stop offset='0%' stop-color='{accent_esc}'/><stop offset='100%' stop-color='transparent'/>"
            f"</linearGradient></defs>"
        )
        parts.append(f"<rect x='{x}' y='{y}' width='{card_w}' height='3' fill='url(#grad{i})'/>")

        # Language icon + abstract illustration
        parts.append(
            f"<g transform='translate({x + 20},{y + 25})'>"
            f"<g transform='translate(0,0)'>{_lang_icon(lang, accent)}</g>"
            f"<g transform='translate(50,0)'>{_project_illustration(proj['name'], accent)}</g>"
            f"</g>"
        )

        # Project name
        parts.append(
            f"<text x='{x + 20}' y='{y + 55}' fill='{_esc(theme.get('white', '#F8FAFC'))}' font-size='14' font-weight='700' font-family='Inter,Segoe UI,sans-serif'>{name_esc}</text>"
        )

        # Description
        parts.append(
            f"<text x='{x + 20}' y='{y + 70}' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='10' font-family='Inter,Segoe UI,sans-serif'>{desc_esc}</text>"
        )

        # Metadata strip
        meta_y = y + 85
        parts.append(f"<rect x='{x}' y='{meta_y}' width='{card_w}' height='2' fill='{accent_esc}' opacity='0.2'/>")
        parts.append(
            f"<text x='{x + 20}' y='{meta_y + 14}' fill='{lang_esc}' font-size='10' font-weight='600' font-family='SF Mono,monospace'>{lang_esc}</text>"
        )
        parts.append(
            f"<text x='{x + 80}' y='{meta_y + 14}' fill='{_esc(theme.get('muted', '#94A3B8'))}' font-size='10' font-family='SF Mono,monospace'>"
            f"\u2605 {stars}  \u1F374 {forks}  {updated}</text>"
        )

        # Buttons
        btn_y = y + card_h - 30
        parts.append(
            f"<a href='{repo_url}'>"
            f"<rect x='{x + 20}' y='{btn_y}' width='100' height='24' rx='6' "
            f"fill='{theme.get('surface', '#0D1528')}' stroke='{accent_esc}' stroke-width='1'/>"
            f"<text x='{x + 70}' y='{btn_y + 16}' text-anchor='middle' fill='{accent_esc}' font-size='11' font-family='Inter,Segoe UI,sans-serif'>Repository</text>"
            f"</a>"
        )
        if demo_url:
            demo_esc = _esc(demo_url)
            parts.append(
                f"<a href='{demo_esc}'>"
                f"<rect x='{x + 135}' y='{btn_y}' width='100' height='24' rx='6' "
                f"fill='{accent_esc}'/>"
                f"<text x='{x + 185}' y='{btn_y + 16}' text-anchor='middle' fill='{_esc(theme.get('background', '#070B17'))}' font-size='11' font-weight='600' font-family='Inter,Segoe UI,sans-serif'>Live Demo</text>"
                f"</a>"
            )

    parts.append("</svg>")
    return "\n".join(parts)


def build_project_gallery_static(theme: dict, projects: list[dict]) -> str:
    """Static fallback for project gallery."""
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

    parts = []
    parts.append(_svg_header(width, height, f"0 0 {width} {height}", "Featured project gallery"))
    parts.append(_gradient_defs(theme, animated=False))
    parts.append(f"<rect width='{width}' height='{height}' rx='16' fill='url(#bgGrad)'/>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='3' fill='url(#waveGrad)'/>")

    for i, proj in enumerate(projects):
        col = i % cols
        row = i // cols
        x = margin_x + col * (card_w + gap_x)
        y = margin_y + row * (card_h + gap_y)

        lang = proj.get("language") or "Unknown"
        accent = LANG_ACCENTS.get(lang, "#8B5CF6")
        name_esc = _esc(proj["name"])
        desc_esc = _esc(proj.get("description", "")[:120])
        lang_esc = _esc(lang)
        stars = proj.get("stars", 0)
        updated = proj.get("pushed_at", "")[:10]
        repo_url = _esc(proj.get("html_url", ""))
        demo_url = proj.get("homepage")

        parts.append(f"<rect x='{x}' y='{y}' width='{card_w}' height='{card_h}' rx='10' fill='#13203A' stroke='{accent}' stroke-width='1'/>")
        parts.append(f"<rect x='{x}' y='{y}' width='{card_w}' height='3' fill='{accent}' opacity='0.5'/>")
        parts.append(f"<g transform='translate({x + 20},{y + 25})'><g transform='scale(0.7)'>{LANG_ICONS.get(lang, f'<circle cx="0" cy="0" r="12" fill="{accent}"/>')}<circle cx='0' cy='0' r='6' fill='{accent}'/></g></g>")
        parts.append(f"<text x='{x + 20}' y='{y + 55}' fill='#F8FAFC' font-size='14' font-weight='700' font-family='Inter,Segoe UI,sans-serif'>{name_esc}</text>")
        parts.append(f"<text x='{x + 20}' y='{y + 70}' fill='#94A3B8' font-size='10' font-family='Inter,Segoe UI,sans-serif'>{desc_esc}</text>")
        parts.append(f"<text x='{x + 20}' y='{y + 90}' fill='{accent}' font-size='10' font-family='SF Mono,monospace'>{lang_esc}  \u2605 {stars}  {updated}</text>")
        parts.append(f"<a href='{repo_url}'><rect x='{x + 20}' y='{y + 130}' width='100' height='24' rx='6' fill='#0D1528' stroke='{accent}' stroke-width='1'/><text x='{x + 70}' y='{y + 146}' text-anchor='middle' fill='{accent}' font-size='11'>Repository</text></a>")
        if demo_url:
            parts.append(f"<a href='{_esc(demo_url)}'><rect x='{x + 135}' y='{y + 130}' width='100' height='24' rx='6' fill='{accent}'/><text x='{x + 185}' y='{y + 146}' text-anchor='middle' fill='#070B17' font-size='11' font-weight='600'>Live Demo</text></a>")

    parts.append("</svg>")
    return "\n".join(parts)


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
