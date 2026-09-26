"""Select and rank featured projects for the profile README.

Priority rules:
1. profile-featured topic
2. featured topic
3. valid homepage URL (verified)
4. portfolio topic
5. stars
6. recent activity (pushed_at)
7. meaningful description

Excludes by default:
- Profile README repo itself
- Empty repos (size 0)
- Test/scratch repos (name patterns)
- Forked repos
- Archived repos
- Repos with profile-hidden / hide-from-profile / private-project topics
- Dupes (see detect_duplicates)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import detect_duplicates
from detect_homepages import resolve_demo_url

LOGIN = "kulraj025"
FEATURED_TOPICS = {"profile-featured", "featured"}
HIDDEN_TOPICS = {"profile-hidden", "hide-from-profile", "private-project"}
PORTFOLIO_TOPICS = {"portfolio", "web-app", "open-source", "web"}


def is_excluded(
    repo: dict,
    *,
    hidden_list: list[str] | None = None,
    include_archived: bool = False,
    include_forks: bool = False,
) -> bool:
    name = repo.get("name", "")
    hidden_list = hidden_list or []
    if name.lower() == LOGIN.lower():
        return True
    if name in hidden_list:
        return True
    if repo.get("private"):
        return True
    if repo.get("size", 0) == 0:
        return True
    if repo.get("archived") and not include_archived:
        return True
    if repo.get("fork") and not include_forks:
        return True
    topics = set(repo.get("topics") or [])
    if topics & HIDDEN_TOPICS:
        return True
    if detect_duplicates.is_scratch_repository(repo):
        return True
    return False


def score_repo(repo: dict) -> tuple:
    """Score for ranking. Higher is better. Returns a sort key tuple."""
    topics = set(repo.get("topics") or [])
    featured = 2 if (topics & FEATURED_TOPICS) else 1
    homepage = 1 if resolve_demo_url(repo) else 0
    portfolio = 1 if (topics & PORTFOLIO_TOPICS) else 0
    stars = repo.get("stargazers_count", 0)
    has_desc = 1 if repo.get("description", "").strip() else 0
    pushed = repo.get("pushed_at") or ""
    return (featured, homepage, portfolio, stars, has_desc, pushed)


def select_projects(
    repos: list[dict],
    *,
    max_featured: int = 6,
    hidden: list[str] | None = None,
    include_archived: bool = False,
    include_forks: bool = False,
    pinned: list[str] | None = None,
    api=None,
) -> tuple[list[dict], list[tuple[str, str, float]]]:
    """Return (selected_projects, duplicate_pairs).

    Applies filtering, deduplication, and ranking.
    `pinned` (config: featured_repositories) forces repos to the front of the
    gallery in the given order, while still respecting hard exclusions.
    """
    hidden = hidden or []
    pinned = pinned or []

    # Exclude obvious trash repos
    candidates = [
        r
        for r in repos
        if not is_excluded(
            r,
            hidden_list=hidden,
            include_archived=include_archived,
            include_forks=include_forks,
        )
    ]

    # Detect and remove duplicates (report the pairs we act on)
    filtered, dup_pairs = detect_duplicates.drop_duplicates(candidates)
    drop_names = {drop for _, drop, _ in dup_pairs}
    filtered = [r for r in filtered if r["name"] not in drop_names]

    # Rank by priority
    ranked = sorted(filtered, key=score_repo, reverse=True)

    # Config-pinned repositories take precedence, in configured order.
    if pinned:
        by_name = {r["name"].lower(): r for r in ranked}
        ordered: list[dict] = []
        for name in pinned:
            match = by_name.pop(name.lower(), None)
            if match is not None:
                ordered.append(match)
        ordered.extend(r for r in ranked if r["name"].lower() in by_name)
        ranked = ordered

    return ranked[:max_featured], dup_pairs


def build_project_details(projects: list[dict], api, *, config_mapping: dict | None = None) -> list[dict]:
    """Build full project detail dicts for rendering."""
    details = []
    for p in projects:
        langs = api.repo_languages(p["full_name"]) or {}
        if langs:
            lang = max(langs.items(), key=lambda kv: kv[1])[0]
        else:
            lang = p.get("language") or "Unknown"

        homepage = resolve_demo_url(p, verify=True, api=api, config_mapping=config_mapping)

        details.append({
            "name": p["name"],
            "full_name": p["full_name"],
            "description": (p.get("description") or "").strip() or "Open-source project",
            "language": lang,
            "stars": p.get("stargazers_count", 0),
            "forks": p.get("forks_count", 0),
            "pushed_at": (p.get("pushed_at") or "")[:10],
            "homepage": homepage,
            "html_url": p["html_url"],
            "topics": p.get("topics", []) or [],
        })
    return details
