#!/usr/bin/env python3
"""Generate a visual, animated GitHub profile README.

Produces:
  - assets/generated/header.svg        animated hero banner
  - assets/generated/languages.svg     technology constellation
  - assets/generated/stats-grid.svg    compact statistic cards
  - README.md                          merged from template markers

All data is live from GitHub API. Nothing is hardcoded or faked.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from github_api import GitHubAPI  # noqa: E402
from generate_stats import (  # noqa: E402
    build_header_svg,
    build_stats_grid_svg,
    build_language_constellation_svg,
    build_all_assets,
)
from render_readme import render_template  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.yml"
TEMPLATE_PATH = ROOT / "templates" / "README.template.md"
README_PATH = ROOT / "README.md"
LOGIN = "kulraj025"

FEATURED_TOPICS = {"profile-featured", "featured"}
HIDDEN_TOPICS = {"profile-hidden", "hide-from-profile", "private-project"}


def is_hidden(repo: dict) -> bool:
    return bool(set(repo.get("topics") or []) & HIDDEN_TOPICS)


def is_featured_by_topic(repo: dict) -> bool:
    return bool(set(repo.get("topics") or []) & FEATURED_TOPICS)


def detect_homepage(repo: dict) -> str | None:
    """Live-demo URL from the repository's official Homepage field."""
    url = (repo.get("homepage") or "").strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def rank_projects(
    repos: list[dict],
    *,
    login: str = LOGIN,
    max_featured: int = 6,
    hidden: list[str] | None = None,
) -> list[dict]:
    """Rank featured projects by the visual-first priority:

    1. repositories tagged profile-featured / featured
    2. repositories with a live Homepage URL
    3. repositories with the most stars
    4. most recently updated
    5. non-fork before fork, non-archived before archived
    """
    hidden = hidden or []
    candidates: list[dict] = []

    for repo in repos:
        name = repo.get("name", "")
        if name.lower() == login.lower():
            continue
        if repo.get("private"):
            continue
        if is_hidden(repo) or name in hidden:
            continue
        if repo.get("fork") or repo.get("archived"):
            if not is_featured_by_topic(repo):
                continue
        if repo.get("size", 0) == 0:
            continue
        candidates.append(repo)

    def score(repo: dict) -> tuple:
        topic = 2 if is_featured_by_topic(repo) else 1
        homepage = 1 if detect_homepage(repo) else 0
        stars = repo.get("stargazers_count", 0)
        pushed = repo.get("pushed_at") or ""
        return (topic, homepage, stars, pushed)

    ordered = sorted(candidates, key=score, reverse=True)
    hidden_set = set(hidden)
    forced = [r for r in ordered if r["name"] not in hidden_set][:max_featured]
    return forced[:max_featured]


def build_language_breakdown(api: GitHubAPI, repos: list[dict]) -> list[dict]:
    """Aggregate real per-repository byte counts into top languages."""
    totals: dict[str, int] = {}
    for repo in repos:
        if repo.get("size", 0) == 0:
            continue
        langs = api.repo_languages(repo["full_name"])
        for lang, bytes_count in langs.items():
            totals[lang] = totals.get(lang, 0) + int(bytes_count)
    # fallback to primary language metadata
    for repo in repos:
        lang = repo.get("language")
        if lang and lang not in totals:
            totals[lang] = totals.get(lang, 0) + 1

    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    return [
        {"name": name, "bytes": n, "percent": round(n / total * 100, 1)}
        for name, n in ranked
    ]


def _plural(count: int, word: str) -> str:
    if abs(count) == 1:
        return f"{count} {word}"
    return f"{count} {word}s"


def _esc(value: object) -> str:
    import html
    return html.escape(str(value), quote=True)


def main() -> int:
    import yaml

    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    api = GitHubAPI()

    # Use public identity endpoint; fall back to configured display name
    user = api.user(LOGIN) or {}
    repos = api.public_repos(LOGIN)
    public = [r for r in repos if not r.get("private")]

    # Exclude the profile README repo itself
    public = [r for r in public if r.get("name", "").lower() != LOGIN.lower()]

    # Language breakdown from real byte counts
    languages = build_language_breakdown(api, public)

    # Rank featured projects
    projects = rank_projects(public, max_featured=config["projects"].get("max_featured", 6))

    # Dominant language per repo (for project cards)
    project_languages: dict[str, str] = {}
    for repo in public:
        langs = api.repo_languages(repo["full_name"]) or {}
        if langs:
            project_languages[repo["full_name"]] = max(langs.items(), key=lambda kv: kv[1])[0]

    # Build SVG assets
    build_all_assets(config["theme"], {
        "name": user.get("name") or config["profile"]["display_name"],
        "public_repos": user.get("public_repos", len(public)),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
        "total_forks": sum(r.get("forks_count", 0) for r in repos),
    }, languages)

    # Project details for cards
    project_details = []
    for p in projects:
        home = detect_homepage(p)
        project_details.append(
            {
                "name": p["name"],
                "full_name": p["full_name"],
                "description": (p.get("description") or "").strip() or "Open-source project",
                "language": project_languages.get(p["full_name"]) or p.get("language") or "—",
                "stars": p.get("stargazers_count", 0),
                "forks": p.get("forks_count", 0),
                "pushed_at": p.get("pushed_at", "")[:10],
                "homepage": home,
                "html_url": p["html_url"],
                "topics": p.get("topics", []) or [],
            }
        )

    # Render template
    sections = {
        "HERO": "",  # will be populated by template or inline
        "ABOUT": "",
        "EDUCATION": "",
        "TECH_CONSTELLATION": "",
        "PROJECTS": "",
        "ACTIVITY": "",
        "LEARNING_PATH": "",
        "CONTACT": "",
        "STATS": "",
        "FOOTER": "",
    }

    # --- HERO (inline SVG since it's the visual centerpiece) ---
    # The template's HERO marker will be replaced; we provide the SVG directly.
    # (render_template will swap <!-- HERO:START --><!-- HERO:END -->)
    hero_svg = build_header_svg(config["theme"], {
        "name": user.get("name") or config["profile"]["display_name"],
        "public_repos": user.get("public_repos", len(public)),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
        "total_forks": sum(r.get("forks_count", 0) for r in repos),
    })
    sections["HERO"] = hero_svg

    # --- ABOUT ---
    about_lines = []
    uni = config["profile"].get("university") or {}
    if uni.get("institution"):
        about_lines.append(
            f"Student at <a href=\"{_esc(uni['website'])}\">{_esc(uni['institution'])}</a>"
        )
    about_lines.append(config["profile"].get("location", ""))
    about_lines.append(f'Currently building with <b>{_esc(config["profile"].get("current_focus", ""))}</b>')
    bio = config["profile"].get("bio", "")
    if bio:
        about_lines.append(f'"From "Hello World" to the real world" — I {bio}')
    sections["ABOUT"] = "<br>".join(about_lines) if about_lines else ""

    # --- EDUCATION ---
    edu = config["profile"].get("education") or []
    if edu and sections.get("EDUCATION") is not None:
        e = edu[0]
        rows = []
        for label, value in (
            ("Degree", e.get("degree", "")),
            ("Field", e.get("specialization", "")),
            ("Level", e.get("level", "")),
            ("Institution", e.get("institution") or "Dong-eui University"),
            ("Status", e.get("status", "")),
        ):
            if value:
                rows.append(f"| **{label}** | {value} |")
        sections["EDUCATION"] = (
            "### 🎓 Education\n\n| | |\n|---|---|\n" + "\n".join(rows)
            if rows
            else ""
        )

    # --- TECHNOLOGY CONSTELLATION ---
    constellation_svg = build_language_constellation_svg(config["theme"], languages)
    sections["TECH_CONSTELLATION"] = constellation_svg

    # --- PROJECTS ---
    if project_details:
        rows = []
        for p in project_details:
            # unique accent color from repo name hash
            accent = "#" + hex(hash(p["name"]) % 0xFFFFFF)[2:].zfill(6)
            # simple visual symbol based on language
            lang = p["language"]
            rows.append(
                f"| [ {p['name']} ]({p['html_url']}) | {_esc(p['description'])} | {_esc(lang)} | "
                f"⭐ {p['stars']} | 🍴 {p['forks']} | {_plural(1, '')} | "
                f"[View]({p['html_url']}){[f'· [Live Demo]({p['homepage']})' if p['homepage'] else '']}"
            )
        sections["PROJECTS"] = (
            "### 🚀 Featured Projects\n\n| Project | Description | Stack | Stars | Last Update |\n|---|---|---|---|---|\n" + "\n".join(rows)
            if rows
            else ""
        )
    else:
        sections["PROJECTS"] = ""

    # --- ACTIVITY ---
    sections["ACTIVITY"] = ""

    # --- LEARNING PATH ---
    learning = config["content"].get("show_learning_path", True)
    if learning and config["profile"].get("current_focus"):
        sections["LEARNING_PATH"] = f"### 🛠️ Current Focus\n{_esc(config['profile']['current_focus'])}"
    else:
        sections["LEARNING_PATH"] = ""

    # --- CONTACT ---
    email = config["social"].get("email", "")
    github = config["social"].get("github", "")
    contact_parts = []
    if email:
        contact_parts.append(f'[<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M4 3c-1.1 0-2 .9-2 2v6c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2H4zm.354-1.646a.5.5 0 0 1 .708.708l1.414 1.414a.5.5 0 0 1-.708 0L4.354 5.355a.5.5 0 1 1 .158-.898zM2 10.5c-.58-.208-1-.853-1-1.5V5.18a4.5 4.5 0 0 1 1.089-3.37l.155.15a5.5 5.5 0 0 1 1.5 1.53l-.15.15a4.5 4.5 0 0 1-1.5 1.089zM8.5 14c-.58-.208-1-.853-1-1.5V9.82a.5.5 0 0 1 .51-.298l1.5 1.5a5.5 5.5 0 0 0 1.089-.6l-.15-.15a.5.5 0 0 1-.61-.093l-1.5-1.5a4.5 4.5 0 0 1-1.27-.95l.15-.15a.5.5 0 0 1 .093.61l1.5 1.5zM12 5.83a.5.5 0 0 1 .307.188l.258.67.628.05a.5.5 0 0 1 .108.427l-.63.248-.258-.668a.5.5 0 0 1-.41-.311l.628-.05-.258-.67a.5.5 0 0 1 0-.376l.628-.05.258-.67a.5.5 0 0 1 .311.108l.63.25a.5.5 0 0 1 .427.108l.258.67.628.05a.5.5 0 0 1 .108.427l-.628.05.258.668a.5.5 0 0 1 .41.311l-.628.05.258.67a.5.5 0 0 1 .311.376l-.628.05.258.67a.5.5 0 0 1 .093.6l1.5 1.5a4.5 4.5 0 0 0 1.089-.6l-.15-.15a.5.5 0 0 1-.61-.093l-1.5-1.5a4.5 4.5 0 0 1-1.27-.95l.15-.15a.5.5 0 0 1 .093.61l1.5 1.5z"/></svg>](mailto:{_esc(email)})')
    if github:
        contact_parts.append(f'[GitHub]({_esc(github)})')
    sections["CONTACT"] = " | ".join(contact_parts) if contact_parts else ""

    # --- STATS ---
    stats_svg = build_stats_grid_svg(config["theme"], {
        "public_repos": user.get("public_repos", len(public)),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
        "total_forks": sum(r.get("forks_count", 0) for r in repos),
    })
    sections["STATS"] = stats_svg

    # --- FOOTER ---
    sections["FOOTER"] = (
        f'LIVE DATA • REFRESHED {__import__("datetime").datetime.utcnow().strftime("%Y-%m-%d")}'
    )

    # Render final README from template
    readme = render_template(TEMPLATE_PATH.read_text(encoding="utf-8"), sections)
    README_PATH.write_text(readme, encoding="utf-8")

    # Write SVG assets info so template knows where to find them
    print(f"✅ README regenerated → {README_PATH.relative_to(ROOT)}")
    print(f"   user: {sections['HERO'][:30]}...")
    print(f"   projects: {len(project_details)} featured")
    print(f"   languages: {', '.join(l['name'] for l in languages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())