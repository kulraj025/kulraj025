#!/usr/bin/env python3
"""Generate a visual, animated GitHub profile README.

Orchestrates:
  1. GitHub API data collection
  2. Language analysis
  3. Duplicate detection
  4. Project selection
  5. SVG asset generation
  6. README rendering from template

All data is live from the GitHub API. Nothing is hardcoded or faked.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml
from github_api import GitHubAPI
from collect_profile_data import collect_data
from analyze_languages import aggregate_languages, detect_frameworks
from detect_duplicates import drop_duplicates, detect_duplicate_pairs, is_scratch_repository
from select_projects import select_projects, build_project_details
from generate_svg_assets import generate_all
from render_readme import (
    render_template,
    build_hero_section,
    build_identity_section,
    build_technology_section,
    build_projects_section,
    build_activity_section,
    build_learning_section,
    build_contact_section,
    build_footer_section,
)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.yml"
TEMPLATE_PATH = ROOT / "templates" / "README.template.md"
README_PATH = ROOT / "README.md"
LOGIN = "kulraj025"


def _esc(value: object) -> str:
    import html
    return html.escape(str(value), quote=True)


def main() -> int:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    api = GitHubAPI()

    # 1. Collect GitHub data
    data = collect_data(api, LOGIN)
    user = data["user"]
    repos = data["repos"]
    public_repos = data["public_repos"]
    events = data["events"]

    # 2. Analyze languages
    languages = aggregate_languages(public_repos, api)
    frameworks = detect_frameworks(public_repos, api)

    # 3. Detect duplicates
    dup_pairs = detect_duplicate_pairs(public_repos)
    if dup_pairs:
        print("Detected duplicate repositories:")
        for keep, drop, conf in dup_pairs:
            print(f"  -> {keep} (keep) vs {drop} (drop) [confidence: {conf}]")

    # 4. Select featured projects
    max_featured = config.get("projects", {}).get("max_featured", 6)
    hidden = config.get("projects", {}).get("hidden_repositories", [])

    selected, detected_dups = select_projects(
        public_repos,
        max_featured=max_featured,
        hidden=hidden,
        api=api,
    )

    # 5. Build project details (with homepage detection)
    projects = build_project_details(selected, api)

    # Build unified profile dict for SVG generators
    profile_config = config.get("profile", {})
    social_config = config.get("social", {})
    profile = {
        "display_name": profile_config.get("display_name", LOGIN),
        "tagline": profile_config.get("tagline", ""),
        "bio": profile_config.get("bio", ""),
        "location": profile_config.get("location", ""),
        "current_focus": profile_config.get("current_focus", ""),
        "university": profile_config.get("university", {}),
        "social": social_config,
    }

    # Stats dict
    refresh_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stats = {
        "name": data["profile"]["name"] or LOGIN,
        "location": profile_config.get("location", "Busan, South Korea"),
        "public_repos": data["profile"]["public_repos"],
        "followers": data["profile"]["followers"],
        "following": data["profile"]["following"],
        "total_stars": data["profile"]["total_stars"],
        "total_forks": data["profile"]["total_forks"],
        "most_used_language": data["profile"]["most_used_language"],
        "refresh_date": refresh_date,
        "focus": profile_config.get("current_focus", ""),
    }

    # 6. Generate SVG assets
    written = generate_all(config["theme"], profile, stats, languages, events, projects)
    print(f"Generated {len(written)} SVG assets")
    for name, path in written.items():
        print(f"  -> {name}")

    # 7. Render README from template
    sections = {
        "HERO": build_hero_section(),
        "IDENTITY": build_identity_section(config["theme"], profile, stats),
        "TECHNOLOGY": build_technology_section(),
        "PROJECTS": build_projects_section(projects, config["theme"]),
        "ACTIVITY": build_activity_section(),
        "LEARNING": build_learning_section(config["theme"], profile["current_focus"]),
        "CONTACT": build_contact_section(social_config, config["theme"]),
        "FOOTER": build_footer_section(config["theme"], stats),
    }

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    readme = render_template(template, sections)
    README_PATH.write_text(readme, encoding="utf-8")

    print("README regenerated ->", README_PATH.relative_to(ROOT))
    print(f"   user: {stats['name']}")
    print(f"   projects: {len(projects)} featured")
    print(f"   languages: {', '.join(l['name'] for l in languages)}")
    print(f"   duplicate pairs: {len(dup_pairs)}")

    # Write a data summary for debugging (gitignored)
    summary = {
        "refresh_date": refresh_date,
        "profile": stats,
        "languages": languages,
        "projects": [{"name": p["name"], "homepage": p.get("homepage"), "stars": p["stars"]} for p in projects],
        "duplicates": [{"keep": k, "drop": d, "confidence": c} for k, d, c in dup_pairs],
        "frameworks": frameworks,
    }
    summary_path = ROOT / "scripts" / ".cache" / "profile-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
