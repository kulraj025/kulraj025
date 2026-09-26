"""Select and rank featured projects for the profile README.

Priority rules (the sort key in `score_repo` follows this order exactly):
1. profile-featured / featured topic
2. valid homepage URL (verified)
3. portfolio topic
4. description quality, graded: a real paragraph beats a single line
5. recent activity (pushed_at)
6. stars

Description and recency outrank stars deliberately. The showcase card is the
largest element on the page, so what it says and how current it is matters
more than a single star.

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


def description_tier(repo: dict) -> int:
    """Grade a repository description: 0 absent, 1 a line, 2 a real paragraph.

    Graded rather than ranked on raw length, so a 44-character line and a
    39-character line are not separated by noise. A repository that can
    actually describe itself in two or three sentences makes a far better
    showcase card than one that can only manage a fragment, and the card is
    the largest element on the page.
    """
    desc = (repo.get("description") or "").strip()
    if not desc:
        return 0
    return 2 if len(desc) >= 90 else 1


def score_repo(repo: dict) -> tuple:
    """Score for ranking. Higher is better. Returns a sort key tuple.

    The key order follows the documented preference list exactly, which puts
    description quality and recency *above* stars. Ranking stars higher meant
    a repository whose own description was a single weak line took the
    largest card on the page purely because it had one star.
    """
    topics = set(repo.get("topics") or [])
    featured = 2 if (topics & FEATURED_TOPICS) else 1
    homepage = 1 if resolve_demo_url(repo) else 0
    portfolio = 1 if (topics & PORTFOLIO_TOPICS) else 0
    pushed = repo.get("pushed_at") or ""
    stars = repo.get("stargazers_count", 0)
    return (featured, homepage, portfolio, description_tier(repo), pushed, stars)


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
