"""Template renderer for the visual GitHub profile README.

Uses HTML comment markers to inject generated sections:

    <!-- GENERATED:NAME:START -->
    ... generated content ...
    <!-- GENERATED:NAME:END -->

Only the block between markers is replaced; everything else is preserved.
"""
from __future__ import annotations

import re
import html

_MARKER = re.compile(r"<!-- GENERATED:(\w+):START -->(.*?)<!-- GENERATED:\1:END -->", re.DOTALL)


def render_template(template: str, sections: dict[str, str]) -> str:
    """Replace every marker block with the matching generated section."""

    def _replace(match: re.Match) -> str:
        name = match.group(1)
        body = sections.get(name, "").strip()
        return f"<!-- GENERATED:{name}:START -->\n{body}\n<!-- GENERATED:{name}:END -->"

    rendered = _MARKER.sub(_replace, template)

    # Collapse quadruple+ blank lines left by section replacement
    while "\n\n\n\n" in rendered:
        rendered = rendered.replace("\n\n\n\n", "\n\n")
    return rendered.strip() + "\n"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_hero_section() -> str:
    """Hero scene: centered animated SVG image."""
    return (
        '<p align="center">'
        '<img src="assets/generated/hero.svg" width="100%" '
        'alt="Animated Busan digital horizon representing Kulraj\'s developer profile" />'
        '</p>'
    )


def build_identity_section(theme: dict, profile: dict, stats: dict) -> str:
    """Identity scene: instrument panel SVG plus a compact text summary.

    The text line is deliberate: it keeps the README readable with a screen
    reader and useful if the SVG fails, without turning the scene into prose.
    """
    muted = _esc(theme.get("muted", "#94A3B8"))
    white = _esc(theme.get("white", "#F8FAFC"))
    cyan = _esc(theme.get("cyan", "#22D3EE"))

    name = _esc(profile.get("display_name", "Kulraj025"))
    location = _esc(profile.get("location", "Busan, South Korea"))
    uni = (profile.get("university") or {}).get("institution", "")
    edu = (profile.get("education") or [{}])[0]
    study = " \u00b7 ".join(
        x for x in [edu.get("degree", ""), edu.get("specialization", ""), edu.get("level", "")] if x
    )

    bits = [f"<strong style='color:{white}'>{name}</strong>", location]
    if uni:
        bits.append(_esc(uni))
    if study:
        bits.append(_esc(study))

    return (
        '<p align="center">'
        '<img src="assets/generated/identity.svg" width="100%" '
        'alt="Identity instrument panel: student developer at Dong-eui University, '
        'Busan, South Korea" />'
        "</p>"
        f'<p align="center" style="color:{muted};font-size:13px;">{" \u00b7 ".join(bits)}</p>'
    )


def build_technology_section() -> str:
    """Technology constellation scene."""
    return (
        '<p align="center">'
        '<img src="assets/generated/technology-constellation.svg" width="100%" '
        'alt="Technology constellation of programming languages" />'
        '</p>'
    )


def build_projects_section(projects: list[dict], theme: dict) -> str:
    """Project gallery scene using SVG cards."""
    if not projects:
        return '<p align="center"><em>No featured projects available.</em></p>'
    return (
        '<p align="center">'
        '<img src="assets/generated/project-gallery.svg" width="100%" '
        'alt="Featured project gallery" />'
        '</p>'
    )


def build_activity_section() -> str:
    """Activity dashboard scene + contribution visualization."""
    return (
        '<p align="center">'
        '<img src="assets/generated/activity-dashboard.svg" width="100%" '
        'alt="GitHub activity dashboard" />'
        '</p>'
        '<p align="center">'
        '<img src="assets/generated/contributions.svg" width="100%" '
        'alt="Contribution heatmap" />'
        '</p>'
    )


def build_learning_section(theme: dict, focus: str) -> str:
    """Learning path scene."""
    if not focus:
        return '<p align="center"><em>Learning path not configured.</em></p>'
    return (
        '<p align="center">'
        '<img src="assets/generated/learning-path.svg" width="100%" '
        'alt="Learning path timeline" />'
        '</p>'
    )


def build_contact_section(social: dict, theme: dict) -> str:
    """Contact scene: footer horizon SVG plus a real, navigable link row.

    The email is exposed only as a secure mailto: link (never as plain text),
    per the content-authenticity rules. Real links are required so the README
    stays usable with a screen reader and when images fail to load.
    """
    cyan = _esc(theme.get("cyan", "#22D3EE"))
    violet = _esc(theme.get("violet", "#8B5CF6"))

    def link(label: str, href: str, colour: str) -> str:
        return (
            f'<a href="{href}" target="_blank" rel="noopener noreferrer" '
            f'style="color:{colour};font-family:SF Mono,monospace;font-size:12px;'
            f'text-decoration:none;border:1px solid {colour}44;border-radius:999px;'
            f'padding:6px 14px;display:inline-block;margin:4px;">{label}</a>'
        )

    parts = [
        '<p align="center">'
        '<img src="assets/generated/footer-horizon.svg" width="100%" '
        'alt="Busan digital horizon footer with university and contact links" />'
        '</p>'
        '<p align="center">'
    ]

    email = (social.get("email") or "").strip()
    website = (social.get("website") or "").strip()

    if email:
        parts.append(link("Email", f"mailto:{email}", cyan))
    parts.append(link("GitHub", "https://github.com/kulraj025", cyan))
    if website:
        parts.append(link("Website", website, violet))
    parts.append(link("Dong-eui University", "https://eng.deu.ac.kr/eng/index.do", violet))
    parts.append("</p>")

    return "".join(parts)


def build_footer_section(theme: dict, stats: dict) -> str:
    """Footer refresh indicator."""
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    muted = _esc(theme.get("muted", "#94A3B8"))
    cyan = _esc(theme.get("cyan", "#22D3EE"))
    return (
        f'<p align="center"><span style="color:{muted};font-family:SF Mono,monospace;font-size:12px;">'
        f"\u2022 LIVE DATA \u2022 REFRESHED {today} \u2022</span></p>"
        f'<p align="center"><span style="color:{cyan};font-family:SF Mono,monospace;font-size:10px;">'
        f"Busan Digital Horizon \u00B7 Auto-generated profile"
        f"</span></p>"
    )
