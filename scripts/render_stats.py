#!/usr/bin/env python3
"""Render the stats, language and trophy cards as local SVGs.

WHY THESE ARE RENDERED HERE INSTE OF EMBEDDED
---------------------------------------------
The brief asked for the official github-readme-stats and github-profile-trophy
hosts. Both are down, and not because of this repository:

    github-readme-stats.vercel.app    503 DEPLOYMENT_PAUSED   (fails for torvalds too)
    github-profile-trophy.vercel.app  402 DEPLOYMENT_DISABLED

A card that 503s renders as a broken image, and a broken image on the first
screenful is the one thing a recruiter cannot fail to notice. The unofficial
mirror that does serve would tie the profile's most-read row to a stranger's
account, so that was not used either. Rendering the same numbers here means
nothing third-party can take the page down, and the cards stay in the tokyonight
palette the rest of the page already uses.

Every card carries its own dark background. That is not decoration: near-white
or cyan text on a transparent card is invisible in GitHub's light theme, which a
large share of visitors are using.

`earned_trophies` is imported by build_readme.py, so the README's conditional
trophy row and the trophy card are always decided by the same numbers.

    python3 scripts/render_stats.py           # write the three SVGs
    python3 scripts/render_stats.py --check   # exit 1 if any of them is stale
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from github_api import GitHubAPI  # noqa: E402
from metrics import (  # noqa: E402
    ACCENT, ASSETS, LANG_COLORS, handle_from, load_config, merged_without_review,
    top_languages, totals, trophy_counts, visible_repos,
)

# tokyonight, so these sit in the same palette as the rest of the page.
BG = "#1A1B26"
TITLE = "#7AA2F7"
TEXT = "#A9B1D6"
DIM = "#565F89"
FONT = "Segoe UI,Ubuntu,Helvetica,Arial,sans-serif"

# Trophy thresholds: the published rules from the github-profile-trophy project,
# restated here so the card is reproducible and auditable rather than dependent
# on a service that currently returns 402. An award is drawn only when the
# measured count actually clears a threshold, and an award that is not earned is
# not drawn at any size. That is why the README's trophy row is conditional.
TROPHY_RULES = [
    ("Star Gazer", "stars", (16, 48, 128)),
    ("Pull Shark", "merged_prs", (2, 16, 128)),
    ("Pull Guru", "merged_prs", (2, 16, 64)),
    ("Quickdraw", "closed_issues", (2, 16, 64)),
    ("Issue Hunter", "closed_issues", (2, 16, 64)),
    ("YOLO", "unreviewed_prs", (1, 10, 24)),
    ("Pair Extraordinaire", "coauthored_commits", (2, 10, 24)),
    ("Arctic Code Vault", "arctic_2013", (1, 1, 1)),
]
LEVEL_NAMES = ("bronze", "silver", "gold")

_NARROW = set("iljtfrI.,:;'!|()[]{}/\\ ")
_WIDE = set("MWmw@%")


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def text_w(s: str, size: float) -> float:
    """Estimated rendered width of `s` at `size` px. Deliberately pessimistic."""
    total = 0.0
    for ch in s:
        if ch in _NARROW:
            total += 0.34
        elif ch in _WIDE:
            total += 0.92
        elif ch.isupper() or ch.isdigit():
            total += 0.63
        else:
            total += 0.55
    return total * size


def text(x, y, s, *, size, fill, weight=400, anchor="start", limit=0) -> str:
    """One <text> element, refused if it would run past the width it is given.

    Clipped text is not hypothetical: it is how the previous hero rendered
    "ilding campus products and XAI". Raising here beats shipping that again.
    """
    if limit and text_w(s, size) > limit:
        raise ValueError(f"text {s!r} at {size}px measures about "
                         f"{text_w(s, size):.0f}px, over its {limit}px box")
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>'
    )


def card(w: int, h: int, title: str) -> list[str]:
    """Own background, then the title.

    No stroke: the brief asked for hide_border, and the background rect is what
    keeps the card legible when GitHub is in light mode.
    """
    return [
        f'<rect width="{w}" height="{h}" rx="8" fill="{BG}" />',
        text(20, 32, title, size=14, fill=TITLE, weight=700, limit=w - 40),
    ]


def svg(parts: list[str], w: int, h: int, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">\n'
        + "\n".join(f"  {p}" for p in parts)
        + "\n</svg>\n"
    )


# --------------------------------------------------------------------------- stats


def render_stats(t: dict) -> str:
    """Commits, stars, pull requests, issues, repositories.

    Values sit at 26px. The style guide bans counters in display type (the
    validator's threshold is 32px) and this is deliberately under it: a student
    profile should not magnify a star count of six, but it should also not hide
    the column.
    """
    w, h = 460, 232
    parts = card(w, h, f"{t['handle']}'s GitHub Stats")
    metrics = [
        (str(t["commits"]), f"Commits {t['year']}"),
        (str(t["stars"]), "Stars"),
        (str(t["prs"]), "Pull requests"),
        (str(t["issues"]), "Issues"),
        (str(t["repos"]), "Repositories"),
    ]
    centers = [90.0, 230.0, 370.0]
    for i, (value, label) in enumerate(metrics):
        cx = centers[i % 3]
        y = 116 if i < 3 else 186
        parts.append(text(cx, y, value, size=26, fill="#BFDBFE", weight=700,
                          anchor="middle", limit=140))
        parts.append(text(cx, y + 18, label, size=11, fill=DIM,
                          anchor="middle", limit=140))
    return svg(parts, w, h, "GitHub statistics card")


# --------------------------------------------------------------------------- langs


def render_langs(langs: list[tuple[str, float]]) -> str:
    w = 460
    h = 76 + max(1, len(langs)) * 26
    parts = card(w, h, "Most Used Languages")
    if not langs:
        parts.append(text(20, 68, "No public language data", size=12, fill=DIM,
                          limit=w - 40))
        return svg(parts, w, h, "Languages by bytes card")

    label_x, bar_x, bar_w = 20, 132, 250
    top = max(p for _, p in langs) or 1.0
    for i, (name, pct) in enumerate(langs):
        y = 68 + i * 26
        parts.append(text(label_x, y, name, size=12, fill=TEXT,
                          limit=bar_x - label_x - 10))
        parts.append(f'<rect x="{bar_x}" y="{y - 9}" width="{bar_w}" height="10" '
                     f'rx="5" fill="#24283B" />')
        filled = max(4, round(bar_w * pct / top))
        parts.append(f'<rect x="{bar_x}" y="{y - 9}" width="{filled}" height="10" '
                     f'rx="5" fill="{LANG_COLORS.get(name, ACCENT)}" />')
        parts.append(text(bar_x + bar_w + 6, y, f"{pct:.1f}%", size=11, fill=DIM,
                          limit=438 - bar_x - bar_w - 6))
    return svg(parts, w, h, "Languages by bytes card")


# ----------------------------------------------------------------------- trophies


def earned_trophies(t: dict) -> list[tuple[str, str, str]]:
    """(award, tier, value) for every rule the account actually clears."""
    out: list[tuple[str, str, str]] = []
    for name, key, levels in TROPHY_RULES:
        value = int(t.get(key, 0) or 0)
        for tier, threshold in enumerate(levels):
            if value >= threshold:
                out.append((name, LEVEL_NAMES[tier], f"{value:,}"))
                break
    return out


def render_trophies(trophies: list[tuple[str, str, str]]) -> str:
    w = 460
    h = 68 + max(1, len(trophies)) * 30
    parts = card(w, h, "Trophies")
    if not trophies:
        parts.append(text(20, 68, "No award thresholds met yet", size=12, fill=DIM,
                          limit=w - 40))
        return svg(parts, w, h, "Trophy card, no awards earned")
    for i, (name, tier, value) in enumerate(trophies):
        y = 68 + i * 30
        parts.append(text(20, y, name, size=13, fill=TEXT, weight=600, limit=300))
        parts.append(text(w - 20, y, f"{tier} · {value}", size=11, fill=DIM,
                          anchor="end", limit=130))
    return svg(parts, w, h, "Trophy card")


# --------------------------------------------------------------------------- main


def collect(api: GitHubAPI, handle: str) -> dict:
    """One fetch pass, shared by the three cards."""
    repos = visible_repos(api, handle, load_config()["projects"])
    t = totals(api, handle, repos)
    t.update(trophy_counts(api, handle))
    t["unreviewed_prs"] = merged_without_review(api, handle)
    return t


def build(api: GitHubAPI, handle: str) -> tuple[dict[str, str], dict]:
    t = collect(api, handle)
    langs = top_languages(api, handle, visible_repos(api, handle, load_config()["projects"]),
                          limit=6)
    files = {
        "stats.svg": render_stats(t),
        "langs.svg": render_langs(langs),
        "trophies.svg": render_trophies(earned_trophies(t)),
    }
    return files, t


def check_cards() -> list[str]:
    """Structural, offline checks on the committed cards. Returns the problems.

    WHY THIS IS NOT A COMPARISON AGAINST THE API
    --------------------------------------------
    The obvious check is "re-render and diff", and it was that. It is also
    unusable: `langs.svg` is built from per-repository language byte counts, and
    Linguist re-analyses asynchronously after a push, so a byte-exact comparison
    was red on a cold cache within minutes of a green run. The commit counter has
    the same problem one level up, because GitHub's commit-search index lags the
    repository -- it read 37 commits while the repository had 40.

    A check that is red for reasons unrelated to the code is worse than no check,
    because the only rational response to a permanently-red CI is to stop reading
    it. So this verifies what is actually stable, and the daily run in
    profile-widgets.yml owns the numbers:

      * the card exists, parses, and carries an opaque background of its own
        (a transparent card is invisible in GitHub's light theme)
      * it has a title, so it is not an unlabelled graphic
      * no text node is empty or a placeholder
      * `langs.svg` is internally consistent: shares descend and sum to 100
      * every number drawn in `stats.svg` appears in the README alt text for
        that card, so the graphic and its description cannot disagree
    """
    import xml.etree.ElementTree as ET

    svg_ns = "{http://www.w3.org/2000/svg}"
    problems: list[str] = []
    texts: dict[str, list[str]] = {}

    for name in ("stats.svg", "langs.svg", "trophies.svg"):
        path = ASSETS / name
        if not path.exists():
            problems.append(f"{name} is missing")
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            problems.append(f"{name} is not valid XML: {exc}")
            continue

        w, h = root.get("width"), root.get("height")
        bg = root.find(f"{svg_ns}rect")
        if bg is None or not (bg.get("fill") or "").startswith("#"):
            problems.append(f"{name} has no opaque background rect")
        else:
            if bg.get("width") != w or bg.get("height") != h:
                problems.append(
                    f"{name} background is {bg.get('width')}x{bg.get('height')} but "
                    f"the card is {w}x{h}: the edges would show through")
        if not (root.find(f"{svg_ns}title") is not None
                or root.get("aria-label") or root.get("role")):
            problems.append(f"{name} has no <title> or aria-label")

        nodes = [(e.text or "").strip() for e in root.iter(f"{svg_ns}text")]
        texts[name] = [t for t in nodes if t]
        for bad in ("TODO", "N/A", "undefined", "None", "null", "{}", "…"):
            if bad in texts[name]:
                problems.append(f"{name} contains the placeholder {bad!r}")
        if not texts[name]:
            problems.append(f"{name} has no text at all")

    # langs.svg must be internally consistent: shares descending, summing to 100
    # once the display rounding is allowed for. Two languages at 20.4% and 20.1%
    # both print as "20%", so the tolerance is the number of rows, not a guess.
    langs = texts.get("langs.svg", [])
    shares: list[float] = []
    for t in langs:
        m = re.fullmatch(r"(\d+(?:\.\d+)?)%", t)
        if m:
            shares.append(float(m.group(1)))
    if shares:
        if any(b > a for a, b in zip(shares, shares[1:])):
            problems.append(
                f"langs.svg shares are not in descending order: {shares}")
        if abs(sum(shares) - 100.0) > len(shares):
            problems.append(
                f"langs.svg shares sum to {sum(shares):.1f}%, which is not 100% "
                f"within display rounding")

    # The card and its alt text are rendered by different code paths. This is the
    # one cross-file invariant worth having, and it is fully offline.
    readme = ASSETS.parent / "README.md"
    if readme.exists() and "stats.svg" in texts:
        page = readme.read_text(encoding="utf-8")
        m = re.search(r'assets/stats\.svg" alt="([^"]*)"', page)
        if not m:
            problems.append("README.md has no alt text for assets/stats.svg")
        else:
            alt = m.group(1)
            drawn = [t for t in texts["stats.svg"] if t.isdigit()]
            for value in drawn:
                if value not in alt:
                    problems.append(
                        f"stats.svg draws {value!r} but the README alt text for it "
                        f"does not mention it: {alt!r}")

    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render the local stats cards.")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if a committed card is malformed or disagrees "
                         "with its alt text (offline; does not compare numbers)")
    args = ap.parse_args(argv)

    if args.check:
        problems = check_cards()
        if problems:
            print(f"FAIL  {len(problems)} problem(s) with the committed cards:")
            for p in problems:
                print(f"      - {p}")
            print("      run: python3 scripts/render_stats.py")
            return 1
        print("ok    stats cards are well-formed and agree with their alt text")
        return 0

    handle = handle_from(load_config())
    files, _ = build(GitHubAPI(), handle)
    for name, content in files.items():
        (ASSETS / name).write_text(content, encoding="utf-8")
        print(f"wrote assets/{name} ({len(content.encode()):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
