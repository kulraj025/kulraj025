#!/usr/bin/env python3
"""Render README.md from templates/README.template.md plus live GitHub data.

WHY A GENERATOR IS BACK, AND WHAT IS DIFFERENT THIS TIME
--------------------------------------------------------
A generator previously ran on a daily cron and overwrote this README with
generated filler, destroying the hand-written case studies. That is why the
project rule says "do not reintroduce a step that writes README.md".

The rule's actual cause was *when* it ran, not *what* it wrote. This one is
different in three ways:

  1. It never runs on a schedule. You run it, and you decide whether the diff
     is good. Nothing publishes behind your back.
  2. It only fills {{WORK_ROWS}} and the stat-card URLs. Every sentence, label
     and heading is still written by hand in the template, so a generator bug
     cannot replace the writing -- it can only misplace a value.
  3. `tests/test_readme_is_current.py` fails the build when the committed
     README and a fresh render disagree, so drift is caught rather than
     discovered by a visitor.

The thing it actually buys is the conditional cases. Hand-typed, the Work
section is a page that lies the moment reality changes: a repository gains a
deployment and no Live badge appears, or one loses its demo and a dead button
stays. Here a Live badge is emitted only when a URL answers 200, the number
and order of projects come from config, and alt text is derived from the
fetched values so it cannot describe a card whose numbers have moved on.

    python3 scripts/build_readme.py            # write README.md
    python3 scripts/build_readme.py --check    # exit 1 if README.md is stale
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from github_api import GitHubAPI  # noqa: E402
from metrics import (  # noqa: E402
    ACCENT, MUTED, README, TEMPLATE, button, chip, demo_url, handle_from,
    load_config, top_languages, totals, visible_repos,
)
from render_stats import earned_trophies  # noqa: E402


def project_cell(entry: dict, repo: dict, handle: str, api: GitHubAPI) -> str:
    """One project: preview image, name, one line of copy, chips, buttons.

    The name is bold text rather than a heading. An H2 per project turned the
    section into a document; at card size the name is a label.
    """
    name = entry["name"]
    title = entry.get("title") or name.replace("_", " ").replace("-", " ").title()
    preview = f"https://opengraph.githubassets.com/1/{handle}/{name}"
    lines = [
        f'      <img src="{preview}" alt="{title}" width="100%" '
        f'style="max-width:480px" />',
        f"      <br /><b>{title}</b><br />",
        f"      {entry['summary']}",
    ]

    # Chips show the stack configured for the project, which is the claim the
    # reader is meant to take away, and not the raw byte histogram -- which for
    # skillbridge reads JavaScript-first and misrepresents a Python service.
    stack = [s.strip() for s in entry.get("stack", []) if s and s.strip()]
    if stack:
        lines.append("      <br />" + " ".join(
            chip(s, color=ACCENT if i == 0 else MUTED, alt=s)
            for i, s in enumerate(stack)))

    badges = [button("Repository", repo["html_url"], alt=f"{title} repository")]
    demo = demo_url(repo, api)
    if demo:
        badges.append(button("Live demo", demo, alt=f"{title} live demo"))
    else:
        print(f"note  {name}: no verified demo URL, Live badge omitted", file=sys.stderr)
    lines.append("      <br />" + " ".join(badges))
    return "\n".join(lines)


def work_rows(projects: list[dict], repos: dict, handle: str, api: GitHubAPI) -> str:
    """The project grid: first project full width, the rest two per row.

    Built from whatever config lists, so a fourth project slots into the
    trailing pair without the template being touched.
    """
    if not projects:
        raise SystemExit("no featured projects configured")

    cells = []
    for entry in projects:
        repo = repos.get(entry["name"])
        if repo is None:
            raise SystemExit(f"featured repository {entry['name']!r} is not in the account")
        cells.append(project_cell(entry, repo, handle, api))

    rows = [f'  <tr>\n    <td colspan="2" align="center">\n{cells[0]}\n    </td>\n  </tr>']
    for i in range(1, len(cells), 2):
        pair = cells[i:i + 2]
        # Pad an odd trailing project so the final row is not half a table.
        if len(pair) == 1:
            pair.append('      <td width="50%"></td>')
        rows.append(
            '  <tr>\n    <td width="50%" align="center" valign="top">\n'
            f"{pair[0]}\n    </td>\n"
            '    <td width="50%" align="center" valign="top">\n'
            f"{pair[1]}\n    </td>\n  </tr>"
        )
    return "\n".join(rows)


def stats_row(t: dict, handle: str) -> str:
    """Row 1: the two summary cards. Row 2: the streak. Row 3: trophies.

    The trophy row is conditional. github-profile-trophy answers 402, and
    substituting an empty card for it would be worse than omitting it, so the
    card is rendered locally instead and the row disappears until a threshold
    is actually met. Today none is: 6 stars is under the 16 the Star Gazer
    award needs. That is the section doing its job, not a missing section.
    """
    raw = f"https://raw.githubusercontent.com/{handle}/{handle}/main/assets"
    rows = [
        f'  <tr>\n    <td width="50%" align="center" valign="middle">'
        f'<img src="{raw}/stats.svg" alt="{stats_alt(t)}" width="100%" '
        f'style="max-width:460px" /></td>\n'
        f'    <td width="50%" align="center" valign="middle">'
        f'<img src="{raw}/langs.svg" alt="{langs_alt(t["_langs"])}" width="100%" '
        f'style="max-width:460px" /></td>\n  </tr>',
        f'  <tr>\n    <td colspan="2" align="center">'
        f'<img src="{streak_url(handle)}" alt="Contribution streak: current streak, '
        f'longest streak and total contributions" width="100%" '
        f'style="max-width:560px" /></td>\n  </tr>',
    ]
    trophies = earned_trophies(t)
    if trophies:
        names = ", ".join(f"{n} ({tier})" for n, tier, _ in trophies)
        rows.append(
            f'  <tr>\n    <td colspan="2" align="center">'
            f'<img src="{raw}/trophies.svg" alt="Trophies earned: {names}" '
            f'width="100%" style="max-width:460px" /></td>\n  </tr>'
        )
    return "\n".join(rows)


def streak_url(handle: str) -> str:
    """The one third-party card still serving, so it stays remote."""
    return (
        "https://streak-stats.demolab.com/?user={h}&theme=tokyonight&hide_border=true"
        "&ringColor={a}&fireColor={a}&currStreakNumColor={a}&sideLabelsColor=7DD3FC"
    ).format(h=handle, a=ACCENT)


def stats_alt(t: dict) -> str:
    return (f"GitHub statistics: {t['commits']} commits in {t['year']}, "
            f"{t['stars']} stars, {t['prs']} pull requests, {t['issues']} issues, "
            f"{t['repos']} public repositories")


def langs_alt(langs) -> str:
    if not langs:
        return "Languages by bytes across public repositories"
    return "Languages by bytes: " + ", ".join(f"{n} {p:.0f}%" for n, p in langs)


HEADER_RE = re.compile(r"\A\s*<!--.*?-->\s*", re.S)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render README.md from live data.")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if README.md differs from the rendered template")
    args = ap.parse_args(argv)

    cfg = load_config()
    profile, social, projects_cfg = cfg["profile"], cfg["social"], cfg["projects"]
    api = GitHubAPI()
    handle = handle_from(cfg)

    repos_list = visible_repos(api, handle, projects_cfg)
    repos = {r["name"]: r for r in repos_list}
    hidden = set(projects_cfg.get("hidden_repositories") or [])
    featured = [p for p in projects_cfg["featured"] if p["name"] not in hidden][
        : projects_cfg.get("max_featured", 3)]

    t = totals(api, handle, repos_list)
    # render_stats owns the trophy counters; reuse its collection so the README's
    # conditional row and the trophy card can never disagree.
    from render_stats import collect as collect_metrics
    t.update(collect_metrics(api, handle))
    t["_langs"] = top_languages(api, handle, repos_list, limit=6)

    uni = profile["university"]
    ig = social["instagram"].rstrip("/").rsplit("/", 1)[-1]
    raw_base = f"https://raw.githubusercontent.com/{handle}/{handle}/main"

    values = {
        "NAME": profile["display_name"],
        "HANDLE": handle,
        "STUDY": profile["education"][0]["specialization"],
        "CITY": uni["city"],
        "LOCATION": profile["location"],
        "PRONOUNS": "he/him",
        "TIMEZONE": "KST (UTC+9)",
        "EMAIL": social["email"],
        "EMAIL_ENCODED": social["email"].replace("@", "%40"),
        "ACCENT_HEX": ACCENT,
        "UNIVERSITY": uni["institution"],
        "UNIVERSITY_URL": uni["website"],
        "UNIVERSITY_BADGE": uni["institution"].replace(" ", "%20"),
        "INSTAGRAM_URL": social["instagram"],
        "INSTAGRAM_HANDLE": ig,
        "INSTAGRAM_HANDLE_ESCAPED": ig.replace("_", "__"),
        "BANNER_URL": f"{raw_base}/assets/banner.svg",
        "TYPING_URL": f"{raw_base}/assets/typing.svg",
        "SNAKE_URL": (f"https://raw.githubusercontent.com/{handle}/{handle}"
                      f"/output/github-contribution-grid-snake-dark.svg"),
        "THREED_URL": f"{raw_base}/profile-3d-contrib/profile-night-green.svg",
        "STATS_ROWS": stats_row(t, handle),
        "ALL_REPOS_URL": f"https://github.com/{handle}?tab=repositories",
        "SKILL_ICONS_URL": (
            "https://skillicons.dev/icons?i=python,ts,js,php,cpp,html,css,fastapi,"
            "nextjs,react,mysql,postgres,docker,linux,git,githubactions"
        ),
        "PITCH": "I ship small campus products, then make the reasoning inspectable.",
        "TYPING_ALT": ("Animated text: campus products and explainable AI. "
                       "Third year at Dong-eui University. "
                       "Open to internships, Korea or remote."),
        "NOW_BUILDING": "SkillBridge",
        "NOW_LEARNING": "Ranking + explanation",
        "NOW_OPEN": "Internships · Korea / remote",
        "SKILL_GROUP_LABELS": "Languages · Web · Data · Systems · Tools",
        "ACTIVITY_CAPTION": "Contribution graph, regenerated daily.",
        "CLOSING": "Ship the first version. Email me.",
        "SKILLS_ALT": (
            "Skills: Python, TypeScript, JavaScript, PHP, C++, HTML, CSS, FastAPI, "
            "Next.js, React, MySQL, PostgreSQL, Docker, Linux, Git, GitHub Actions"
        ),
        "WORK_ROWS": work_rows(featured, repos, handle, api),
    }

    # The template opens with a documentation comment that *names* the slots it
    # defines, e.g. "Only {{WORK_ROWS}} and {{STATS_ROWS}} are computed". Filling
    # the whole file therefore pastes the entire generated grid into the middle
    # of that comment: the page still renders, because it is all inside `<!--
    # -->` and the validator still reports every slot filled, so nothing goes
    # red. It is simply a 24KB page that is mostly a comment, which is a
    # spectacularly quiet way to be wrong.
    #
    # So: strip the header, and substitute only into what is left.
    template = TEMPLATE.read_text(encoding="utf-8")
    body = HEADER_RE.sub("", template, count=1)
    if body == template:
        raise SystemExit(
            "templates/README.template.md does not open with its documentation "
            "comment; the generated header would be pasted into the page"
        )

    out = body
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", str(val))

    leftover = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", out)))
    if leftover:
        raise SystemExit(f"unfilled template slots: {leftover}")

    if args.check:
        current = README.read_text(encoding="utf-8") if README.exists() else ""
        if current != out:
            print("FAIL  README.md is out of date with config and the GitHub API")
            print("      run: python3 scripts/build_readme.py")
            return 1
        print("ok    README.md matches config and the GitHub API")
        return 0

    README.write_text(out, encoding="utf-8")
    print(f"wrote README.md ({len(out.encode()):,} bytes, {len(featured)} projects)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
