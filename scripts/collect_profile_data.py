"""Collect all dynamic GitHub profile data in one structured dictionary.

Fetches from the GitHub REST API (cached by GitHubAPI):
  - User profile (name, bio, followers, following, public_repos)
  - Public repositories (with full metadata)
  - Per-repository language byte counts
  - Recent public events
  - Recent releases per repository

Returns a dict suitable for consumption by the SVG generators and
README renderer.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from github_api import GitHubAPI


def collect_data(api: GitHubAPI, login: str = "kulraj025") -> dict:
    """Collect all dynamic data for the profile. Returns a structured dict."""
    user = api.user(login) or {}
    repos = api.public_repos(login) or []
    events = api.public_events(login, per_page=60) or []

    # Exclude the profile README repository itself from project/repos stats
    profile_repo_name = login.lower()

    public_repos = [r for r in repos if r.get("name", "").lower() != profile_repo_name]

    # Fetch language data for each repo
    repo_languages: dict[str, dict] = {}
    for repo in public_repos:
        try:
            repo_languages[repo["full_name"]] = api.repo_languages(repo["full_name"]) or {}
        except Exception:
            repo_languages[repo["full_name"]] = {}

    # Aggregate stats
    total_stars = sum(r.get("stargazers_count", 0) for r in public_repos)
    total_forks = sum(r.get("forks_count", 0) for r in public_repos)

    # Determine most-used language from byte counts
    lang_totals: dict[str, int] = {}
    for langs in repo_languages.values():
        for lang, bytes_count in langs.items():
            lang_totals[lang] = lang_totals.get(lang, 0) + int(bytes_count)
    most_used_lang = max(lang_totals, key=lang_totals.get) if lang_totals else None

    return {
        "login": login,
        "user": user,
        "profile": {
            "name": user.get("name") or login,
            "display_name": user.get("name") or login,
            "bio": user.get("bio") or "",
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "public_repos": user.get("public_repos", len(public_repos)),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "most_used_language": most_used_lang,
            "location": user.get("location") or "",
        },
        "repos": repos,
        "public_repos": public_repos,
        "repo_languages": repo_languages,
        "events": events,
        "lang_totals": lang_totals,
    }


if __name__ == "__main__":
    import yaml
    api = GitHubAPI()
    data = collect_data(api)
    print(f"User: {data['profile']['name']}")
    print(f"Repos: {len(data['public_repos'])}")
    print(f"Followers: {data['profile']['followers']}")
    print(f"Total stars: {data['profile']['total_stars']}")
    print(f"Most used language: {data['profile']['most_used_language']}")
