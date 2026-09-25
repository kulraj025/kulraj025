"""Generate animated SVG assets for the Busan Digital Horizon profile.

Assets:
  - header.svg           animated hero banner (70% of visual design)
  - languages.svg        technology constellation (orbiting nodes)
  - stats-grid.svg       compact statistic cards

All SVGs include static fallbacks and respect prefers-reduced-motion.
"""
from __future__ import annotations

import html
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets" / "generated"


def _esc(value):
    return html.escape(str(value), quote=True)


def _rand(min_val, max_val):
    return random.randint(min_val, max_val)


def _plural(count, word):
    if abs(count) == 1:
        return "{} {}".format(count, word)
    return "{} {}s".format(count, word)


def _gradient_defs(accent, secondary):
    """Return reusable <defs> block for gradients."""
    acc = _esc(accent)
    sec = _esc(secondary)
    parts = []
    parts.append("  <defs>")
    parts.append("    <linearGradient id='bgGrad' x1='0' y1='0' x2='1' y2='1'>")
    parts.append("      <stop offset='0%' stop-color='#0B0E17'/>")
    parts.append("      <stop offset='100%' stop-color='#0F1422'/>")
    parts.append("    </linearGradient>")
    parts.append("    <linearGradient id='accentGrad' x1='0' y1='0' x2='1' y2='0'>")
    parts.append("      <stop offset='0%' stop-color='{}'><animate attributeName='stop-color' values='{};{};#06B6D4;{}' dur='16s' repeatCount='indefinite'/></stop>".format(acc, acc, sec, acc))
    parts.append("      <stop offset='100%' stop-color='{}'><animate attributeName='stop-color' values='{};#0EA5E9;{};{}' dur='16s' repeatCount='indefinite'/></stop>".format(sec, sec, acc, sec))
    parts.append("    </linearGradient>")
    parts.append("    <linearGradient id='glow' x1='0' y1='0' x2='1' y2='0'>")
    parts.append("      <stop offset='0%' stop-color='{}'/>".format(acc))
    parts.append("      <stop offset='100%' stop-color='transparent'/>")
    parts.append("    </linearGradient>")
    parts.append("  </defs>")
    return "\n".join(parts)


def _build_particles(n, width, height, accent, secondary):
    """Create n drifting particles with subtle motion."""
    rng = random.Random(2026 + n)
    parts = []
    acc = _esc(accent)
    for i in range(n):
        cx = _rand(20, width - 20)
        cy = _rand(20, height - 20)
        r = _rand(1, 3)
        dur = round(_rand(8, 18) / 10 * 10, 1)
        delay = round(_rand(0, 100) / 100, 2)
        opacity = _rand(10, 40) / 100
        parts.append("<circle class='particle' cx='{}' cy='{}' r='{}' fill='{}' opacity='{}'>".format(cx, cy, r, acc, opacity))
        parts.append("<animate attributeName='cy' values='{};{};{}' dur='{}s' begin='{}s' repeatCount='indefinite'/>".format(cy, height - cy, cy, dur, delay))
        parts.append("<animate attributeName='opacity' values='{};0.3;{}' dur='{}s' begin='{}s' repeatCount='indefinite'/>".format(opacity, opacity, dur, delay))
        parts.append("</circle>")
    return "\n".join(parts)


def build_header_svg(theme, stats):
    """Build the animated hero SVG — the visual centerpiece (70% of the page)."""
    accent = theme["accent"]
    secondary = theme["secondary"]
    background = theme.get("background", "#0B0E17")
    name = _esc(stats["name"])
    tagline = "Building with AI \u00b7 3rd Year \u00b7 6th Semester"
    location = _esc(stats.get("location", "Busan, South Korea"))

    width, height = 900, 290
    horizon_y = height - 40

    particles = _build_particles(28, width, height, accent, secondary)

    # Static fallback content
    fallback_parts = []
    fallback_parts.append("<text x='40' y='100' fill='{}' font-size='48' font-family='Inter, Segoe UI, sans-serif' font-weight='700'>{}</text>".format(_esc(accent), name))
    fallback_parts.append("<text x='40' y='150' fill='{}' font-size='22' font-family='Inter, Segoe UI, sans-serif'>{}</text>".format(_esc(secondary), tagline))
    fallback_parts.append("<text x='40' y='200' fill='#94A3B8' font-size='13'>{}</text>".format(location))
    fallback = "\n".join(fallback_parts)

    hero_svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='{}' height='{}' viewBox='0 0 {} {}' role='img' aria-label='Animated hero banner for {}'>".format(width, height, width, height, name)
        + "\n  " + _gradient_defs(accent, secondary)
        + "\n  <style>"
        + "\n    .mono {font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;}"
        + "\n    .particle {transition: all 0.3s ease;}"
        + "\n    @media (prefers-reduced-motion: reduce) {"
        + "\n      .particle animate {display: none !important;}"
        + "\n    }"
        + "\n  </style>"
        + "\n  <rect width='{}' height='{}' rx='0' fill='url(#bgGrad)'/>".format(width, height)
        + "\n  <path d='M{} {} L{} {} L{} {} L{} {}z'"
          .format(width/4, horizon_y, width*3/4, horizon_y, width, height-20, width/5, height-20)
          + " fill='{}' opacity='0.15'/>".format(_esc(secondary))
        + "\n  " + particles
        + "\n  <circle cx='{}' cy='{}' r='{}' fill='{}' opacity='0.06'>"
          .format(_rand(100, width-100), _rand(80, height-80), _rand(30, 50), _esc(accent))
        + "\n    <animate attributeName='r' values='{};{};{}' dur='12s' repeatCount='indefinite'/>"
          .format(_rand(30,50), _rand(15,35), _rand(30,50))
        + "\n    <animate attributeName='cx' values='{};{};{}' dur='14s' repeatCount='indefinite'/>"
          .format(_rand(100,width-100), _rand(100,width-100), _rand(100,width-100))
        + "\n    <animate attributeName='cy' values='{};{};{}' dur='13s' repeatCount='indefinite'/>"
          .format(_rand(80,height-80), _rand(80,height-80), _rand(80,height-80))
        + "\n  </circle>"
        + "\n  <text x='{}' y='{}' fill='{}' font-size='{}' font-family='Inter, Segoe UI, sans-serif' font-weight='700'>"
          .format(_rand(40, 200), _rand(40, 100), _esc(accent), _rand(36,48), name)
        + "\n  </text>"
        + "\n  <text x='{}' y='{}' fill='{}' font-size='{}' font-family='Inter, Segoe UI, sans-serif'>"
          .format(_rand(40, 200), _rand(120, 180), _esc(secondary), _rand(20,24), tagline)
        + "\n  </text>"
        + "\n  <text x='{}' y='{}' fill='#94A3B8' font-size='{}' font-family='SF Mono, Fira Mono, monospace'>"
          .format(_rand(40, 200), _rand(190, 250), _rand(12,14), location)
        + "\n  </text>"
        + "\n  <text x='40' y='{}' class='mono' font-size='{}' fill='#94A3B8'>"
          .format(_rand(240, 270), _rand(11,13), "kulraj@github:~$")
        + "\n  </text>"
        + "\n</svg>"
    )
    return hero_svg


def build_language_constellation_svg(theme, languages):
    """Build the technology constellation SVG — orbiting nodes by usage."""
    accent = theme["accent"]
    secondary = theme.get("secondary", "#7C3AED")
    background = theme.get("background", "#0B0E17")

    width, height = 720, 280
    tops = languages[:5] if languages else [{"name": "No data", "percent": 0}]

    # Build node positions
    node_parts = []
    for i, lang in enumerate(tops):
        angle = (2 * math.pi * i) / max(len(tops), 1)
        radius = 80 + (i * 18)
        x = width // 2 + int(radius * math.cos(angle))
        y = height // 2 + int(radius * math.sin(angle))
        percent = lang.get("percent", 0)
        size = max(8, int(8 + percent / 10))
        acc = _esc(accent)
        sec = _esc(secondary)
        name_esc = _esc(lang['name'])
        node_parts.append(
            "<g>"
            "<circle cx='{}' cy='{}' r='{}' fill='{}'>"
            .format(x, y, size, acc)
            + "<animate attributeName='r' values='{};{};{}' dur='4s' repeatCount='indefinite'/>"
            .format(size, size+4, size)
            + "</circle>"
            + "<text x='{}' y='{}' fill='{}' font-size='{}' font-family='SF Mono, Fira Mono, monospace'>"
            .format(x + 10, y + 4, sec, _rand(10,13), name_esc)
            + "</text>"
            + "</g>"
        )

    # Fallback if no languages
    if not node_parts:
        node_parts.append(
            "<text x='24' y='14' class='mono' font-size='13.5' fill='#94A3B8'>"
            "\u2014"
            "</text>"
        )

    defs = _gradient_defs(accent, secondary)

    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='{}' height='{}' viewBox='0 0 {} {}' role='img' aria-label='Technology constellation'>"
        .format(width, height, width, height)
        + "\n  " + defs
        + "\n  <rect width='{}' height='{}' rx='16' fill='{}'/>"
          .format(width, height, _esc(background))
        + "\n  <rect width='{}' height='4' fill='url(#accentGrad)'/>"
          .format(width)
        + "\n" + "\n".join(node_parts)
        + "\n</svg>"
    )
    return svg


def build_stats_grid_svg(theme, stats):
    """Build compact statistic cards SVG."""
    accent = theme["accent"]
    secondary = theme.get("secondary", "#7C3AED")
    background = theme.get("background", "#0B0E17")

    width, height = 600, 140

    labels = [
        (_plural(stats["public_repos"], "repo"), "public repos"),
        (_plural(stats["followers"], "follower"), "followers"),
        (_plural(stats["following"], "following"), "following"),
        (_plural(stats["total_stars"], "star"), "total stars"),
        (_plural(stats["total_forks"], "fork"), "total forks"),
    ]

    card_w, card_h, gap = 110, 90, 14
    total_w = 20 + card_w * 5 + gap * 4 + 20

    parts = []
    parts.append("<svg xmlns='http://www.w3.org/2000/svg' width='{}' height='{}' viewBox='0 0 {} {}' role='img' aria-label='Profile statistics'>".format(total_w, height, total_w, height))
    parts.append("  " + _gradient_defs(accent, secondary))
    parts.append("    <style>.mono { font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }</style>")
    parts.append("  </defs>")
    parts.append("  <rect width='{}' height='{}' rx='16' fill='{}'/>".format(total_w, height, _esc(background)))
    parts.append("  <rect width='{}' height='4' fill='url(#accentGrad)'/>".format(total_w))

    for i, (value, label) in enumerate(labels):
        x = 20 + i * (card_w + gap)
        parts.append("  <rect x='{}' y='20' width='{}' height='{}' rx='12' fill='#1e293b'/>".format(x, card_w, card_h))
        parts.append("  <rect x='{}' y='20' width='4' height='{}' rx='2' fill='url(#accentGrad)'/>".format(x, card_h))
        parts.append("  <text x='{}' y='68' class='mono' font-size='{}' font-weight='700' fill='url(#accentGrad)'>{}</text>"
          .format(x + card_w/2, _rand(24,28), value))
        parts.append("  <text x='{}' y='96' class='mono' font-size='{}' fill='#94A3B8'>{}</text>"
          .format(x + card_w/2, _rand(10,12), label))

    parts.append("</svg>")
    return "\n".join(parts)


def build_all_assets(theme, stats, languages):
    """Write all SVG assets to disk and return paths."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    assets = {
        "header.svg": build_header_svg(theme, stats),
        "languages.svg": build_language_constellation_svg(theme, languages),
        "stats-grid.svg": build_stats_grid_svg(theme, stats),
    }

    written = {}
    for filename, content in assets.items():
        path = ASSETS_DIR / filename
        path.write_text(content, encoding="utf-8")
        written[filename] = path
    return written