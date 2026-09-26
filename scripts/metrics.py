#!/usr/bin/env python3
"""The one place that talks to the GitHub API for this profile.

`build_readme.py` and `render_stats.py` both need the same numbers, and if each
computed its own they would eventually disagree -- a card showing 53 commits
next to alt text saying 52 is the kind of small wrongness that costs a
profile its credibility. So every fetch, every palette constant and every
derived count lives here and both callers import it.

Nothing in this module knows about markup.
"""
from __future__ import annotations

import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml  # noqa: E402

from detect_homepages import resolve_demo_url  # noqa: E402
from github_api import GitHubAPI  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "README.template.md"
README = ROOT / "README.md"
CONFIG = ROOT / "config" / "profile.yml"
ASSETS = ROOT / "assets"

SHIELDS = "https://img.shields.io/badge"
ACCENT = "22D3EE"
# Muted teal, so the accent chip reads as primary on a row of chips.
MUTED = "2A7F9E"
LANG_COLORS = {
    "Python": "3572A5", "JavaScript": "F1E05A", "TypeScript": "3178C6",
    "PHP": "4F5D95", "HTML": "E34C26", "CSS": "563D7C", "C++": "F34B7D",
    "Java": "B07219", "C": "555555", "C#": "178600", "Go": "00ADD8",
    "Rust": "DEA584", "Ruby": "701516", "Shell": "89E051", "Dart": "00B4AB",
    "Kotlin": "A97BFF", "Swift": "F05138", "Svelte": "FF3E00", "Vue": "41B883",
    "PowerShell": "012456", "Jupyter": "DA5B0B",
}


def load_config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def handle_from(cfg: dict) -> str:
    return cfg["social"]["github"].rstrip("/").rsplit("/", 1)[-1]


def search_count(api: GitHubAPI, handle: str, extra: str, kind: str = "commits") -> int:
    """Count from the search API. Returns 0 rather than raising: one
    unreachable search must not be able to fail a build over a card."""
    q = urllib.parse.quote(f"author:{handle} {extra}".strip())
    try:
        data = api.get_json(
            f"https://api.github.com/search/{kind}?q={q}&per_page=1") or {}
    except Exception:  # noqa: BLE001
        return 0
    return int(data.get("total_count") or 0)


def visible_repos(api: GitHubAPI, handle: str, projects_cfg: dict) -> list[dict]:
    repos = [r for r in api.public_repos(handle) if not r.get("fork")]
    if projects_cfg.get("include_forks"):
        repos = api.public_repos(handle)
    if projects_cfg.get("include_archived"):
        return repos
    return [r for r in repos if not r.get("archived")]


def totals(api: GitHubAPI, handle: str, repos: list[dict]) -> dict:
    """Every number a card or a piece of alt text can show.

    Stars, pull requests and issues are included deliberately. The
    `hide=stars,prs,issues` parameter that was on the old card suppressed them,
    which reads as selective reporting rather than modesty; six honest stars
    next to a zero is more credible than a card that quietly omits the column.
    """
    year = datetime.now(timezone.utc).year
    return {
        "handle": handle,
        "year": year,
        "stars": sum(r.get("stargazers_count", 0) for r in repos),
        "commits": search_count(api, handle, f"author-date:>={year}-01-01"),
        "prs": search_count(api, handle, "is:pr", kind="issues"),
        "issues": search_count(api, handle, "is:issue", kind="issues"),
        "repos": len(repos),
    }


def trophy_counts(api: GitHubAPI, handle: str) -> dict:
    """The counters the trophy rules are measured against.

    Pull requests and issues must be counted through the *issues* search index,
    not the commits one. `search/commits?q=author:X is:pr is:merged` does not
    error: the commits index has no idea what `is:pr` means, quietly ignores it
    and returns every commit by that author. That is how a profile with zero
    pull requests rendered a "Pull Shark" trophy next to a stats card reading
    "0 pull requests". Qualifiers aimed at the wrong index fail silently, which
    is the worst way for a count to be wrong.

    Computed rather than assumed, including the ones that are currently zero
    (the account was created in 2025, so there are no 2013 contributions and no
    Arctic Code Vault). Hardcoding those as zero would be a claim that stops
    being true if the history were ever imported.
    """
    return {
        "merged_prs": search_count(api, handle, "is:pr is:merged", kind="issues"),
        "closed_issues": search_count(api, handle, "is:issue is:closed", kind="issues"),
        "coauthored_commits": search_count(api, handle, "co-author:"),
        "arctic_2013": search_count(api, handle, "author-date:2013-01-01..2013-12-31"),
    }


def merged_without_review(api: GitHubAPI, handle: str) -> int:
    """The 'YOLO' award is a merged PR that nobody reviewed, so it is the
    difference between all merged PRs and reviewed ones, not a separate count.

    Both halves come from the issues index, for the reason above.
    """
    merged = search_count(api, handle, "is:pr is:merged", kind="issues")
    reviewed = search_count(api, handle, "is:pr is:merged review:*", kind="issues")
    return max(0, merged - reviewed)


def top_languages(api: GitHubAPI, handle: str, repos: list[dict], limit: int = 6):
    """Language mix across the account, weighted by bytes GitHub measures."""
    totals_by_lang: dict[str, int] = {}
    for repo in repos:
        try:
            langs = api.repo_languages(f"{handle}/{repo['name']}") or {}
        except Exception:  # noqa: BLE001
            continue
        for name, size in langs.items():
            totals_by_lang[name] = totals_by_lang.get(name, 0) + size
    grand = sum(totals_by_lang.values())
    if not grand:
        return []
    # Sorted by (-bytes, name), never by bytes alone. `sorted(key=bytes,
    # reverse=True)` leaves ties in dict-insertion order, which is not a defined
    # order: it follows the order the repository listing came back in. Two
    # languages at the same size then swap places between two runs of the same
    # data, which reshuffles the language card and -- because the card and the
    # README alt text are rendered by separate calls -- makes them disagree.
    # Alphabetical tie-breaking is boring and identical every time.
    ranked = sorted(totals_by_lang.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [(n, v * 100.0 / grand) for n, v in ranked]


def repo_languages(api: GitHubAPI, handle: str, repo_name: str, limit: int = 4):
    try:
        langs = api.repo_languages(f"{handle}/{repo_name}") or {}
    except Exception:  # noqa: BLE001
        return []
    if not langs:
        return []
    total = sum(langs.values())
    # Same tie-break as top_languages: see the comment there.
    ranked = sorted(langs.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [(n, v * 100.0 / total) for n, v in ranked]


def demo_url(repo: dict, api: GitHubAPI) -> str | None:
    """A demo URL, but only one that actually answers.

    `resolve_demo_url` tries the repository homepage, then GitHub Pages, then a
    config mapping. verify=True is the part that matters: it is what stops the
    README getting a Live button pointing at a deployment that 404s. This is the
    whole reason the Work section is generated rather than typed.
    """
    try:
        return resolve_demo_url(repo, verify=True, api=api)
    except Exception:  # noqa: BLE001 - one bad repo must not break the build
        return None


def chip(label: str, *, color: str, alt: str, height: int = 20) -> str:
    """One shields.io chip.

    `_` is doubled because shields.io renders an underscore as a space, so
    `kul_rajneupane` has to be written `kul__rajneupane` or the badge reads
    "kul rajneupane".
    """
    text = urllib.parse.quote(label.replace("_", "__"))
    return (
        f'<img src="{SHIELDS}/{text}-{color.lstrip("#")}?style=flat-square" '
        f'alt="{alt}" height="{height}" />'
    )


def button(label: str, url: str, *, alt: str, color: str = ACCENT) -> str:
    return (
        f'<a href="{url}"><img src="{SHIELDS}/{urllib.parse.quote(label)}-{color}'
        f'?style=for-the-badge" alt="{alt}" height="28" /></a>'
    )
