#!/usr/bin/env python3
"""KULRAJ / DIGITAL HORIZON — design system.

Single source of truth for the visual identity. Imported by both
`generate_svg_assets.py` (SVG scenes) and `render_readme.py` (native HTML
sections) so the two halves of the README can never drift apart.

THE CENTRAL CONSTRAINT
----------------------
A README image is fluid: a `viewBox` 1000 units wide is rendered at whatever
width the browser gives it (roughly 890px on desktop, 375px on a phone). Every
glyph inside therefore scales with the image. Measured on the previous
generation:

    viewBox font-size   desktop (0.89x)   mobile (0.375x)
    8.0px               7.1px             3.0px
    10px                8.9px             3.8px
    14px                12.5px            5.2px
    20px                17.8px            7.5px
    42px                37.4px            15.8px

92 of 168 text elements rendered below 13px on desktop and *every* one of them
was illegible on mobile. That is why the design read as a prototype: the whole
information layer was invisible, so all the visual work did not register.

THE RULE THIS ENFORCES
----------------------
Information-bearing text does not live inside a full-width SVG. It lives in
native HTML, which renders at real device-independent pixel sizes, reflows, and
stays selectable and accessible. SVG is reserved for:

  * display type large enough to survive scaling (see TYPE_SCALE), and
  * data graphics that carry no essential text (heatmaps, orbits, artwork).

`TYPE_SCALE['floor']` is the hard minimum for any glyph emitted into an SVG and
is asserted by `scripts/qa_layout.py`, so the regression cannot come back.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------

#: Nominal design width for every full-bleed scene, in viewBox units.
CANVAS_W = 1000

#: Approximate rendered width of the README column on a desktop browser.
#: Used to document the downscale factor that drives the type scale.
DESKTOP_RENDER_W = 890

#: Approximate rendered width on a 375px phone.
MOBILE_RENDER_W = 375

#: Fraction of the canvas a full-width README image occupies, per device.
DESKTOP_SCALE = DESKTOP_RENDER_W / CANVAS_W   # 0.89
MOBILE_SCALE = MOBILE_RENDER_W / CANVAS_W    # 0.375

#: Horizontal breathing room inside a scene, in viewBox units.
GUTTER = 64

#: Usable width between gutters.
CONTENT_W = CANVAS_W - GUTTER * 2            # 872


# ---------------------------------------------------------------------------
# Type scale
# ---------------------------------------------------------------------------

#: Sizes are in viewBox units. `role` documents what each step is for, and
#: `min_px` is the size that step degrades to on the worst realistic viewport.
#:
#: Only `hero` and `display` are permitted to carry meaning. Everything at or
#: near the floor is decorative reinforcement of a fact that is also stated in
#: native HTML directly beneath the image.
TYPE_SCALE: dict[str, dict[str, float | str]] = {
    "hero":     {"size": 92,  "role": "Masthead. The single loudest element on the page."},
    "display":  {"size": 40,  "role": "Scene title inside SVG artwork."},
    "title":    {"size": 30,  "role": "Hub / artwork wordmark."},
    "subtitle": {"size": 24,  "role": "Node labels, artwork captions."},
    "label":    {"size": 21,  "role": "Short labels. Duplicated in HTML."},
    "floor":    {"size": 18,  "role": "ABSOLUTE MINIMUM. Decorative only."},
}

#: Hard minimum enforced by qa_layout.py across every generated asset.
MIN_SVG_FONT_SIZE = 18

#: Steps that are allowed to carry meaning that is not repeated in HTML.
#: Everything else must be decorative.
MEANINGFUL_SVG_TEXT_MIN = 21

#: How a given step degrades on a 375px phone, for documentation and tests.
def effective(size: float, scale: float = MOBILE_SCALE) -> float:
    """Rendered pixel size of `size` viewBox units at the given scale factor."""
    return round(size * scale, 2)


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

#: Authoritative palette. `config/profile.yml` is the input; these are the
#: values the art direction calls for and the values qa_layout.py checks
#: contrast against.
PALETTE: dict[str, str] = {
    "bg":         "#070B17",   # page
    "surface":    "#0E1830",   # primary surface
    "surface_2":  "#13213B",   # secondary surface
    "cyan":       "#38BDF8",   # primary cyan
    "cyan_br":    "#22D3EE",   # bright cyan
    "violet":     "#8B5CF6",   # violet intelligence signal
    "purple":     "#A78BFA",   # soft violet
    "green":      "#34D399",   # positive signal
    "text":       "#F8FAFC",   # primary text
    "text_2":     "#CBD5E1",   # secondary text
    "muted":      "#94A3B8",   # muted text
    "line":       "#2A3C62",   # border
}

#: Canvas colour used for WCAG checks. Text is always measured against this or
#: against `surface`, never against a gradient midpoint.
CONTRAST_BG = PALETTE["bg"]

#: Minimum contrast for body text (WCAG AA).
AA_BODY = 4.5

#: Minimum contrast for large display type (WCAG AA large-text, >=24px bold).
AA_LARGE = 3.0

#: Ordered accent ramp for project artwork. Every entry is checked against
#: `bg` at AA_BODY for text use and is distinguishable in hue from its
#: neighbours so adjacent cards do not read as the same colour.
ACCENT_RAMP: list[str] = [
    "#38BDF8",  # cyan
    "#A78BFA",  # soft violet
    "#34D399",  # green
    "#F0A868",  # warm signal
    "#F472B6",  # rose
    "#22D3EE",  # bright cyan
]

#: Canonical GitHub language colours, kept for reference. These are tuned for a
#: light background and MUST be passed through ensure_contrast() before use.
LANG_HEX: dict[str, str] = {
    "PHP": "#4F5D95",
    "C++": "#f34b7d",
    "CSS": "#563d7c",
    "HTML": "#e34c26",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "C": "#555555",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Dart": "#00B4AB",
    "Ruby": "#701516",
    "PHP ": "#4F5D95",
}


# ---------------------------------------------------------------------------
# Typography stacks
# ---------------------------------------------------------------------------

#: SVGs loaded through <img> cannot fetch webfonts, so only system stacks work.
#: The consequence is that SVG type is reserved for large display sizes where
#: substitution is least visible; all body copy is HTML and uses GitHub's stack.
FONT_DISPLAY = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
FONT_MONO = "ui-monospace,'SF Mono','Cascadia Code',Menlo,Consolas,'DejaVu Sans Mono',monospace"

#: Character-width model shared by fit_text() and qa_layout.py so the generator
#: and the QA check agree on what overflows. Sans ~0.52em average advance,
#: monospace exactly 0.60em.
ADVANCE_SANS = 0.52
ADVANCE_MONO = 0.60


def text_width(text: str, font_size: float, *, mono: bool = False,
               weight: str = "normal", tracking: float = 0.0) -> float:
    """Estimated rendered width of a single line of text, in viewBox units."""
    ratio = ADVANCE_MONO if mono else ADVANCE_SANS
    if not mono and weight in ("700", "800", "900", "bold"):
        ratio += 0.045          # bold advances are wider
    return len(text) * font_size * ratio + max(0, len(text) - 1) * tracking


def fit_font_size(text: str, max_px: float, target: float, *, mono: bool = False,
                  weight: str = "normal", tracking: float = 0.0,
                  floor: float = MIN_SVG_FONT_SIZE) -> float:
    """Largest size <= target at which `text` fits within `max_px`."""
    size = target
    while size > floor and text_width(text, size, mono=mono, weight=weight,
                                      tracking=tracking) > max_px:
        size -= 1
    return size


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------

#: Durations in seconds. The brief asks for slow, calm, elegant motion, so
#: nothing is faster than 6s and most sit in the 14-30s band.
DUR = {
    "gradient": 26,
    "swell":     9,
    "drift":    18,
    "orbit":    24,
    "pulse":     4.2,
    "cursor":     1.15,
    "travel":   11,
    "shimmer":   7.5,
}

#: Maximum number of SMIL animations permitted in a single asset. The previous
#: hero carried 101; that is a slideshow, not motion design. Animation should
#: read as one slow system.
MAX_ANIMATIONS_PER_ASSET = 40

#: Ambient opacity for background detail. Kept low so that "not every object
#: glows" holds literally.
AMBIENT = 0.16
FAINT = 0.07


# ---------------------------------------------------------------------------
# Section rhythm
# ---------------------------------------------------------------------------

#: Height of the decorative rule that separates scenes. These replace the
#: default markdown `---` hairlines, which read as a template.
DIVIDER_H = 44

#: Vertical space between a scene and the HTML copy that follows it, in px of
#: markdown. Generous but not empty: the brief calls out unused dark space.
SECTION_GAP_PX = 28

#: Gap above a section's own heading.
SECTION_HEAD_PX = 8


def eyebrow(number: str, title: str, note: str = "") -> str:
    """The numbered section marker that opens each scene.

    Rendered as native HTML rather than SVG so it is crisp, selectable and
    responsive — this is the piece that most improves scanability.

    One line, not three. The marker used to be split across "01" / " / " /
    "TITLE" spans plus a separate provenance note, which scattered four 12px
    fragments above every section and read as dashboard chrome. The number and
    the title are now a single string, and the note sits on the same line in a
    lighter weight, so the marker occupies one line of vertical rhythm.
    """
    muted = PALETTE["muted"]
    cyan = PALETTE["cyan_br"]
    label = 12  # HTML_META equivalent; real CSS, so it does not shrink
    out = [
        f'<p style="margin:{SECTION_HEAD_PX}px 0 10px;">'
        f'<span style="color:{cyan};font-family:{FONT_MONO};font-size:{label}px;'
        f'font-weight:600;letter-spacing:1.6px;">{number}</span>'
        f'<span style="color:{line_color_hex()};font-family:{FONT_MONO};'
        f'font-size:{label}px;letter-spacing:1.6px;"> &nbsp;/&nbsp; </span>'
        f'<span style="color:{PALETTE["text_2"]};font-family:{FONT_MONO};'
        f'font-size:{label}px;font-weight:600;letter-spacing:1.6px;">{title}</span>'
    ]
    if note:
        out.append(
            f'<span style="color:{muted};font-size:{label}px;letter-spacing:0.3px;">'
            f'&nbsp;&nbsp;{note}</span>'
        )
    out.append("</p>")
    return "".join(out)


def line_color_hex() -> str:
    return PALETTE["line"]


def rule() -> str:
    """A hairline used to separate stacked metadata inside HTML blocks."""
    return (f'<div style="height:1px;background:{PALETTE["line"]};'
            f'opacity:0.55;margin:14px 0;"></div>')
