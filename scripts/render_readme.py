#!/usr/bin/env python3
"""Render README.md from the template and live GitHub data.

DESIGN RULE
-----------
Information-bearing text is emitted as native HTML, never as SVG. A README
image is fluid, so glyphs inside a full-width SVG shrink with the viewport and
become unreadable on a phone (see scripts/design.py for the measurements). HTML
renders at real device-independent sizes, reflows, and stays selectable.

SVG is used only for atmosphere, data graphics and display type large enough to
survive scaling.
"""
from __future__ import annotations

import html
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import design as D
from design import PALETTE as P, FONT_MONO, eyebrow
from generate_svg_assets import _lang_color, contrast_ratio, slugify

ROOT = Path(__file__).resolve().parent.parent

SANS = ("-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',"
        "Helvetica,Arial,sans-serif")


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


# ---------------------------------------------------------------------------
# HTML primitives
# ---------------------------------------------------------------------------

def divider() -> str:
    """The repeating horizon rule that carries the section rhythm.

    Replaces the default markdown `---` hairline, which reads as a template.
    """
    return ('<p style="margin:6px 0;"><img src="assets/generated/divider.svg" '
            'width="100%" alt="" /></p>')


_divider = divider


def _img(src: str, alt: str) -> str:
    return (f'<p align="center" style="margin:0;">'
            f'<img src="{e(src)}" width="100%" alt="{e(alt)}" /></p>')


def _h2(title: str, accent: str = P["cyan_br"]) -> str:
    """A real section heading. Rendered as HTML so it is large and crisp."""
    return (f'<h2 style="margin:0 0 4px;font-family:{SANS};font-size:26px;'
            f'font-weight:700;letter-spacing:-0.4px;color:{P["text"]};'
            f'line-height:1.25;">{e(title)}</h2>')


def _note(text: str) -> str:
    return (f'<p style="margin:0 0 14px;font-family:{SANS};font-size:{HTML_BODY}px;'
            f'color:{P["muted"]};letter-spacing:0.1px;line-height:1.5;">{e(text)}</p>')


def _rule() -> str:
    return (f'<div style="height:1px;background:{P["line"]};opacity:0.6;'
            f'margin:0 0 14px;"></div>')


def _button(label: str, href: str, *, primary: bool = False) -> str:
    """A large, obviously interactive link.

    Sized well past the 44px touch target minimum rather than the ~24px pill
    buttons the previous version used, and given a real border so it does not
    dissolve into the background.
    """
    if primary:
        bg, fg, bd = P["cyan_br"], "#04121C", P["cyan_br"]
    else:
        bg, fg, bd = "transparent", P["cyan_br"], P["line"]
    # 16px vertical padding + a 18px line box puts the hit area at 50px, well
    # past the 44px touch-target minimum, and the 15px label is large enough to
    # read as a button rather than a chip.
    return (f'<a href="{e(href)}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-block;margin:6px 8px 6px 0;padding:16px 28px;'
            f'background:{bg};color:{fg};border:1px solid {bd};border-radius:8px;'
            f'font-family:{FONT_MONO};font-size:15px;font-weight:600;'
            f'letter-spacing:1.2px;text-decoration:none;'
            f'line-height:1.2;">{e(label)}</a>')


def _kv_table(rows: list[tuple[str, str]]) -> str:
    """A label/value list as a real table.

    The rows used to be emitted as bare `<tr>` elements and dropped straight
    into a `<td>`. That is invalid HTML: a row must live inside a table, so the
    browser hoists it out and the identity panel's right-hand column silently
    stops being a column. Wrapping them keeps the two-column layout intact.
    """
    body = "".join(
        f'<tr>'
        f'<td style="padding:10px 18px 10px 0;border-bottom:1px solid {P["line"]};'
        f'vertical-align:top;white-space:nowrap;width:1%;">'
        f'<span style="font-family:{FONT_MONO};font-size:{HTML_META}px;'
        f'font-weight:600;letter-spacing:1.5px;color:{P["cyan_br"]};">'
        f'{e(label)}</span></td>'
        f'<td style="padding:10px 0;border-bottom:1px solid {P["line"]};'
        f'vertical-align:top;">'
        f'<span style="font-family:{SANS};font-size:17px;color:{P["text"]};'
        f'font-weight:600;">{value}</span></td>'
        f'</tr>'
        for label, value in rows
    )
    return ('<table width="100%" cellspacing="0" cellpadding="0">'
            f"{body}</table>")


#: Smallest inline HTML type. This is real CSS, so unlike SVG text it does not
#: shrink with the viewport — 11px is genuinely 11px on a phone. Anything that
#: must be read is set at 14px or above; only short metadata labels sit here.
MIN_HTML_FONT_SIZE = 11

#: Size for short metadata labels (percentages, counts, topic chips).
HTML_META = 12

#: Floor for anything a reader is expected to actually read.
HTML_BODY = 14


def _meta_chip(text: str, color: str = P["muted"]) -> str:
    return (f'<span style="font-family:{FONT_MONO};font-size:{HTML_META}px;'
            f'color:{color};margin-right:14px;white-space:nowrap;">{e(text)}</span>')


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def build_hero_section() -> str:
    return _img(
        "assets/generated/hero.svg",
        "KULRAJ NEUPANE (@kulraj025) — student developer at Dong-eui University "
        "in Busan, South Korea, building with AI and exploring machine learning")


def build_identity_section(theme: dict, profile: dict, stats: dict) -> str:
    university = profile.get("university") or {}
    social = profile.get("social") or {}
    education = profile.get("education") or []

    left = [
        _h2("Student developer building with AI"),
        (f'<p style="margin:0 0 14px;font-family:{SANS};font-size:17px;'
         f'line-height:1.6;color:{P["text_2"]};max-width:60ch;">'
         f'{e(profile.get("bio") or "")}</p>'),
    ]
    if education:
        ed = education[0]
        bits = [ed.get("degree"), ed.get("specialization"), ed.get("level")]
        line = " · ".join(b for b in bits if b)
        if line:
            left.append(
                f'<p style="margin:0 0 6px;font-family:{SANS};font-size:16px;'
                f'color:{P["cyan_br"]};font-weight:600;">{e(line)}</p>')
        inst = ed.get("institution") or university.get("institution")
        if inst:
            left.append(_meta_chip(f"{inst} · {ed.get('status') or 'Enrolled'}"))

    right = _kv_table([
        ("STUDYING", e((education[0].get("specialization")
                        if education else "Intelligence Computing"))),
        ("BUILDING", "AI projects and practical digital products"),
        ("LEARNING", "Machine learning"),
        ("BASED IN", e(profile.get("location") or "Busan, South Korea")),
    ])

    buttons = [
        _button("VIEW GITHUB", social.get("github") or "https://github.com/kulraj025", primary=True),
        _button("UNIVERSITY", university.get("website") or "", primary=False),
    ]
    if social.get("email"):
        buttons.append(_button("EMAIL ME", f"mailto:{social['email']}"))

    return "".join([
        eyebrow("01", "IDENTITY", "Verified from repository configuration"),
        '<table width="100%" cellspacing="0" cellpadding="0"><tr>',
        '<td width="56%" valign="top" style="padding:0 24px 0 0;">',
        "".join(left), "</td>",
        '<td valign="top" style="padding:0;">',
        right, "</td>",
        "</tr></table>",
        f'<p style="margin:18px 0 0;">{"".join(buttons)}</p>',
    ])


def build_technology_section(theme: dict, languages: list[dict]) -> str:
    if not languages:
        return ""
    total = sum(float(l.get("bytes") or 0) for l in languages) or 1.0
    rows = []
    for lang in languages:
        name = lang.get("name", "")
        # Prefer the analyser's own percentage; recompute only if absent.
        if lang.get("percent") is not None:
            share = float(lang["percent"])
        else:
            share = float(lang.get("bytes") or 0) / total * 100
        color = _lang_color(name)
        rows.append(
            f'<tr>'
            f'<td style="padding:6px 14px 6px 0;white-space:nowrap;width:1%;">'
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'border-radius:3px;background:{color};"></span></td>'
            f'<td style="padding:6px 12px 6px 0;font-family:{SANS};font-size:16px;'
            f'font-weight:600;color:{P["text"]};white-space:nowrap;">{e(name)}</td>'
            f'<td style="padding:6px 12px 6px 0;width:100%;">'
            f'<span style="display:block;height:6px;border-radius:3px;'
            f'background:{P["surface_2"]};overflow:hidden;">'
            f'<span style="display:block;height:6px;border-radius:3px;'
            f'width:{share:.1f}%;background:{color};"></span></span></td>'
            f'<td style="padding:6px 0 6px 14px;font-family:{FONT_MONO};'
            f'font-size:{HTML_META}px;color:{P["muted"]};text-align:right;'
            f'white-space:nowrap;">{share:.1f}%</td>'
            f'</tr>')

    return "".join([
        eyebrow("02", "TECHNOLOGY", "Detected from public repositories"),
        _img("assets/generated/technology-orbit.svg",
             "Technology orbit sized by real GitHub language byte share"),
        _note("Detected from public repositories — the languages actually present "
              "in public code, listed with their real share of public bytes. "
              "The four largest are drawn in the orbit above."),
        f'<table width="100%" cellspacing="0" cellpadding="0">{"".join(rows)}</table>',
    ])


def _project_card(project: dict, *, featured: bool) -> str:
    name = project.get("name", "")
    accent = project.get("accent") or P["cyan_br"]
    slug = slugify(name)
    size = "featured" if featured else "secondary"
    lang = project.get("language") or ""
    lang_color = _lang_color(lang) if lang else accent

    desc = project.get("description") or "No description provided."
    if featured:
        desc_html = (f'<p style="margin:0 0 12px;font-family:{SANS};font-size:17px;'
                     f'line-height:1.55;color:{P["text_2"]};max-width:62ch;">{e(desc)}</p>')
    else:
        desc_html = (f'<p style="margin:0 0 10px;font-family:{SANS};font-size:15px;'
                     f'line-height:1.5;color:{P["text_2"]};">{e(desc)}</p>')

    name_size = 26 if featured else 19
    name_html = (f'<p style="margin:0 0 8px;font-family:{SANS};font-size:{name_size}px;'
                 f'font-weight:700;color:{P["text"]};letter-spacing:-0.3px;'
                 f'line-height:1.2;">{e(name)}</p>')

    chips = []
    if lang:
        chips.append(
            f'<span style="display:inline-block;margin:0 8px 6px 0;padding:4px 12px;'
            f'border-radius:999px;border:1px solid {lang_color};color:{lang_color};'
            f'font-family:{FONT_MONO};font-size:12px;font-weight:600;'
            f'letter-spacing:0.6px;">{e(lang)}</span>')
    for topic in (project.get("topics") or [])[:3]:
        chips.append(
            f'<span style="display:inline-block;margin:0 8px 6px 0;padding:4px 12px;'
            f'border-radius:999px;border:1px solid {P["line"]};color:{P["muted"]};'
            f'font-family:{FONT_MONO};font-size:12px;">{e(topic)}</span>')

    meta = [
        _meta_chip(f"★ {project.get('stars', 0)}", P["cyan_br"]),
        _meta_chip(f"⑂ {project.get('forks', 0)}"),
        _meta_chip(f"updated {project.get('pushed_at') or '—'}"),
    ]

    repo_url = project.get("html_url") or f"https://github.com/kulraj025/{name}"
    buttons = [_button("REPOSITORY", repo_url, primary=featured)]
    if project.get("homepage"):
        buttons.append(_button("LIVE DEMO", project["homepage"], primary=False))

    art_w = "44%" if featured else "38%"
    return "".join([
        '<table width="100%" cellspacing="0" cellpadding="0"><tr>',
        f'<td width="{art_w}" valign="middle" style="padding:0 20px 0 0;">',
        f'<img src="assets/generated/project-art/{e(slug)}.svg" width="100%" '
        f'alt="Abstract artwork for {e(name)}" /></td>',
        '<td valign="middle" style="padding:0;">',
        name_html, desc_html,
        f'<p style="margin:0 0 10px;">{"".join(chips)}</p>',
        f'<p style="margin:0 0 12px;">{"".join(meta)}</p>',
        f'<p style="margin:0;">{"".join(buttons)}</p>',
        "</td></tr></table>",
    ])


def build_projects_section(projects: list[dict], theme: dict) -> str:
    if not projects:
        return ""
    parts = [eyebrow("03", "FEATURED WORK", "Selected from public repositories")]

    if projects:
        parts.append(_project_card(projects[0], featured=True))

    rest = projects[1:3]
    if rest:
        parts.append(f'<div style="height:1px;background:{P["line"]};opacity:0.6;'
                     f'margin:22px 0;"></div>')
        cells = []
        for project in rest:
            cells.append('<td width="50%" valign="top" style="padding:0 14px 0 0;">'
                         + _project_card(project, featured=False) + "</td>")
        parts.append('<table width="100%" cellspacing="0" cellpadding="0"><tr>'
                     + "".join(cells) + "</tr></table>")

    # Anything beyond the three showcased goes in one compact row of links.
    # Never a fourth card — the brief asks for fewer, larger elements.
    extra = projects[3:]
    if extra:
        links = []
        for project in extra:
            url = project.get("html_url") or ""
            links.append(
                f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer" '
                f'style="display:inline-block;margin:6px 16px 6px 0;font-family:{FONT_MONO};'
                f'font-size:{HTML_BODY}px;color:{P["cyan_br"]};text-decoration:none;'
                f'border-bottom:1px solid {P["line"]};padding-bottom:2px;">'
                f'{e(project.get("name", ""))}</a>')
        parts.append(f'<div style="height:1px;background:{P["line"]};opacity:0.6;'
                     f'margin:22px 0 14px;"></div>')
        parts.append(_note("More work"))
        parts.append(f'<p style="margin:0;">{"".join(links)}</p>')

    return "".join(parts)


def build_activity_section(theme: dict, stats: dict, profile: dict) -> str:
    # Four numeric metrics across the row, not five. "PUBLIC REPOSITORIES" is
    # 20 characters and wrapped to three lines inside a 20% column on a phone,
    # which broke the baseline alignment of the values beneath it. Short labels
    # that never wrap fix the alignment at every width.
    metrics = [
        ("REPOSITORIES", stats.get("public_repos", 0), P["cyan_br"]),
        ("FOLLOWERS", stats.get("followers", 0), P["violet"]),
        ("STARS", stats.get("total_stars", 0), P["cyan_br"]),
        ("FORKS", stats.get("total_forks", 0), P["violet"]),
    ]
    cells = []
    for label, value, color in metrics:
        cells.append(
            '<td width="25%" valign="top" style="padding:0 12px 0 0;">'
            f'<p style="margin:0 0 6px;font-family:{FONT_MONO};font-size:{HTML_META}px;'
            f'font-weight:600;letter-spacing:1.2px;color:{P["muted"]};'
            f'white-space:nowrap;">{e(label)}</p>'
            f'<p style="margin:0;font-family:{SANS};font-size:32px;font-weight:700;'
            f'color:{color};letter-spacing:-0.8px;line-height:1;">{e(value)}</p></td>')

    # The main detected language is a word, not a number, so it gets its own
    # line under the row rather than a fifth column of mismatched type.
    main_lang = stats.get("most_used_language") or ""
    lang_line = ""
    if main_lang:
        color = _lang_color(main_lang)
        lang_line = (
            f'<p style="margin:16px 0 0;font-family:{FONT_MONO};font-size:{HTML_META}px;'
            f'font-weight:600;letter-spacing:1.2px;color:{P["muted"]};">'
            f'MOST DETECTED LANGUAGE'
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'border-radius:3px;background:{color};margin:0 0 0 10px;'
            f'vertical-align:middle;"></span>'
            f'<span style="color:{P["text"]};margin-left:8px;font-size:{HTML_BODY}px;'
            f'letter-spacing:0;">{e(main_lang)}</span></p>')

    return "".join([
        eyebrow("04", "ACTIVITY & LEARNING", "Live from the GitHub API"),
        f'<table width="100%" cellspacing="0" cellpadding="0"><tr>{"".join(cells)}</tr></table>',
        lang_line,
        _img("assets/generated/horizon-signal.svg",
             "Animated signal trace along the Busan horizon"),
        _img("assets/generated/learning-path.svg",
             "Three verified milestones: currently enrolled, building AI projects, "
             "learning machine learning"),
    ])


def build_contact_section(social: dict, theme: dict, stats: dict) -> str:
    buttons = []
    if social.get("email"):
        buttons.append(_button("EMAIL ME", f"mailto:{social['email']}", primary=True))
    if social.get("github"):
        buttons.append(_button("GITHUB", social["github"]))
    uni = ((social.get("_university") or {}).get("website")) or ""
    if uni:
        buttons.append(_button("UNIVERSITY", uni))

    refresh = stats.get("refresh_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return "".join([
        _img("assets/generated/contact-horizon.svg",
             "Contact horizon — closing statement for Kulraj Neupane"),
        eyebrow("05", "CONTACT", "Busan, South Korea"),
        f'<p align="center" style="margin:2px 0 6px;">{"".join(buttons)}</p>',
        (f'<p align="center" style="margin:0;">'
         f'<span style="font-family:{FONT_MONO};font-size:{HTML_META}px;'
         f'letter-spacing:1.4px;color:{P["muted"]};">'
         f'KULRAJ / DIGITAL HORIZON · LIVE GITHUB DATA · '
         f'REFRESHED {e(refresh)}</span></p>'),
    ])


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def render_template(template: str, sections: dict[str, str]) -> str:
    out = template
    for key, body in sections.items():
        start = f"<!-- GENERATED:{key}:START -->"
        end = f"<!-- GENERATED:{key}:END -->"
        if start not in out or end not in out:
            raise ValueError(f"Template is missing markers for section {key}")
        pre, rest = out.split(start, 1)
        _, post = rest.split(end, 1)
        out = f"{pre}{start}\n{body}\n{end}{post}"
    return out
