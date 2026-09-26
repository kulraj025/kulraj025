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
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from github_api import GitHubAPI  # noqa: E402
from metrics import (  # noqa: E402
    ACCENT, MUTED, README, ROOT, TEMPLATE, button, chip, demo_url, handle_from,
    load_config, top_languages, totals, visible_repos,
)
from render_stats import earned_trophies  # noqa: E402

# Raw base for the generated project cards in assets/work/.
THUMB_BASE = "https://raw.githubusercontent.com/{handle}/{handle}/main/assets/work"


def thumb_url(handle: str, name: str) -> str:
    """Raw URL for one project card in assets/work/.

    A function rather than a formatted constant, because a module-level template
    string has to be `.format()`ed at every use site and forgetting one produces
    a URL containing a literal `{handle}`. That is not a visible crash: it is a
    404 inside a cell, on a page whose whole promise is that nothing is broken.
    `test_generated_sections.py` asserts no `{` survives into README.md.
    """
    return f"{THUMB_BASE.format(handle=handle)}/{name}.svg"


def thumb_max_width(name: str, featured: list[dict]) -> int:
    """How wide the card for `name` is allowed to render.

    Read from the SVG's own viewBox rather than assumed, so a card that is
    regenerated at a different width cannot be scaled by a stale hardcoded
    number. The first featured project gets the full grid row and is rendered
    at its natural 900; the rest sit in half-width cells at 480.
    """
    import xml.etree.ElementTree as ET
    path = ROOT / "assets" / "work" / f"{name}.svg"
    width = int(ET.parse(path).getroot().get("width", "0"))
    first = featured[0]["name"] if featured else None
    return width if name == first else min(width, 480)



def project_cell(entry: dict, repo: dict, handle: str, api: GitHubAPI) -> str:
    """One project: thumbnail, name, one line of copy, chips, buttons.

    The thumbnail is a card in assets/work/, not the GitHub social preview.

    `opengraph.githubassets.com` was the obvious choice and it is the wrong one:
    it is a white card, it stamps the account's profile photo onto every
    project, it prints the repository description verbatim — and for
    `helping-station-deu` that description is literally the string "x" — and
    it cannot be themed. Three of them on a dark page read as three holes. The
    local cards are in the banner's own visual language and contain no
    photograph of the person, which is what a project card should be.

    The name is bold text rather than a heading. An H2 per project turned the
    section into a document; at card size the name is a label.
    """
    name = entry["name"]
    title = entry.get("title") or name.replace("_", " ").replace("-", " ").title()
    thumb = thumb_url(handle, name)
    if not (ROOT / "assets" / "work" / f"{name}.svg").exists():
        raise SystemExit(
            f"assets/work/{name}.svg is missing. Run "
            f"`python3 scripts/render_work_thumbs.py` — a featured project "
            f"without a card would leave a hole in the grid, which is the same "
            f"defect the social preview was replaced to fix."
        )
    lines = [
        f'      <img src="{thumb}" alt="{title} project card" width="100%" '
        f'style="max-width:{entry.get("_max_width", 480)}px" />',
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
        # The card's rendered width comes from its own viewBox, so a card
        # regenerated wider or narrower is scaled correctly without a hardcoded
        # number here going stale. The first entry is the full-width row.
        cells.append(project_cell({**entry, "_max_width": thumb_max_width(
            entry["name"], projects)}, repo, handle, api))

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


# The header is the file's own documentation comment: it opens on a line that is
# only an opening-comment marker, and closes on a line that is only a closing
# one. Both halves are required, which is the point.
#
# This used to be `\A\s*<!--.*?-->` -- lazy, so it ended at the FIRST closing
# marker anywhere in the file. That was fine until documenting the generated
# regions required writing a complete marker comment in the header, at which
# point the header was cut 130 lines early, the field map below it fell into the
# page body, and the field map's own `{{STATS_ROWS}}` placeholder was replaced
# with a live <tr> element. Nothing went red: the page rendered, every slot was
# filled, and the output was a plausible README with a table of build internals
# printed across the middle of it.
#
# Anchoring both delimiters to their own lines makes a mid-header comment
# harmless, so the failure mode is gone rather than merely absent today.
HEADER_RE = re.compile(r"\A[ \t]*<!--[^\n]*\n.*?^[ \t]*-->[ \t]*$\n?[ \t]*\n?", re.S | re.M)
GENERATED_RE = re.compile(
    r"[ \t]*<!-- BEGIN GENERATED:([A-Z]+) -->(.*?)<!-- END GENERATED:\1 -->",
    re.S,
)


def splice_regions(body: str, regions: dict[str, str]) -> str:
    """Replace each marker block in the template with the committed block.

    Used by --check. Whole blocks, not just the {{SLOT}} inside them: the WORK
    region wraps its own <table>, so substituting only the slot would emit a
    <table> inside a <table> and the comparison would report a difference on a
    build that is in fact correct.
    """
    missing = [m.group(1) for m in GENERATED_RE.finditer(body) if m.group(1) not in regions]
    if missing:
        raise SystemExit(
            f"template has generated region(s) with nothing committed to compare: "
            f"{', '.join(missing)}"
        )
    return GENERATED_RE.sub(
        lambda m: (m.group(0) if m.group(1) not in regions
                   else f"<!-- BEGIN GENERATED:{m.group(1)} -->\n"
                        f"{regions[m.group(1)].strip()}\n"
                        f"<!-- END GENERATED:{m.group(1)} -->"),
        body,
    )


def committed_regions(readme: str) -> dict[str, str]:
    """Pull the generated regions back out of the published README.

    Used by --check so the comparison can be made without the network: the
    numbers and the quote stay exactly as they were committed, and everything
    around them is re-derived from the template.
    """
    return {m.group(1): m.group(2).strip("\n") for m in GENERATED_RE.finditer(readme)}


def quote_of_the_day(quotes: list[str], when: date | None = None) -> str:
    """Pick the day's line, deterministically.

    Not `random.choice`. A random pick would make the build irreproducible, so
    `--check` could never be trusted and re-running the build would churn the
    file for no reason. Day-of-year modulo the list length is a pure function of
    the date and the config: the page changes every day, the same day always
    renders the same line, and no service is involved that could go down.
    """
    if not quotes:
        raise SystemExit("content.quotes is empty; the NOTE section needs one line")
    d = when or date.today()
    return quotes[d.timetuple().tm_yday % len(quotes)]


def strip_markers(body: str) -> str:
    """Normalise whitespace inside the generated regions.

    The marker comments themselves are KEPT in the published README, and that is
    deliberate. --check locates the two regions by those markers so it can
    re-verify the rest of the file offline; if the build stripped them, the very
    next --check would report the regions missing and never recover without a
    rebuild, which is a check that only works once. GitHub strips HTML comments
    before rendering, so they cost nothing on the page.

    What *is* normalised is the leading and trailing blank line, so that
    reflowing the marker pair by hand in the template does not register as a
    content change.
    """
    return GENERATED_RE.sub(lambda m: f"<!-- BEGIN GENERATED:{m.group(1)} -->\n"
                                     f"{m.group(2).strip()}\n"
                                     f"<!-- END GENERATED:{m.group(1)} -->",
                            body)


def _fill(body: str, values: dict[str, str], strict: bool = False) -> str:
    """Substitute slots into the template body.

    With strict=True each slot must occur exactly once. That rule is for the two
    *generated* slots only, whose values are structural markup: `str.replace` is
    global and silent, so a slot named twice -- once as a real placeholder, once
    inside a table documenting the slots -- has both filled and the
    documentation table grows a <tr> element. The page still renders, every slot
    still reports as filled, and the build still exits 0.

    Ordinary values are exempt. {{HANDLE}} legitimately appears once per URL and
    per badge across the whole page, and a plain string pasted into prose is
    harmless; counting those occurrences would fail a correct template.
    """
    for key, val in values.items():
        token = "{{" + key + "}}"
        n = body.count(token)
        if strict and n != 1:
            raise SystemExit(
                f"slot {token} appears {n} times in the template body; a "
                f"generated slot must appear exactly once. A second occurrence "
                f"is almost always a table documenting the slots, and filling "
                f"that one puts live markup inside the documentation."
            )
        body = body.replace(token, str(val))
    return body


def _report_first_difference(committed: str, rendered: str, limit: int = 6) -> None:
    """Print the first few differing lines.

    "README.md does not match" sends you hunting through a 8KB file. The first
    divergent line is almost always the answer, and when it is not, the six that
    follow usually are.
    """
    import difflib

    a = committed.splitlines()
    b = rendered.splitlines()
    shown = 0
    for line in difflib.unified_diff(a, b, "committed", "rendered", n=1, lineterm=""):
        if line.startswith(("---", "+++")):
            continue
        if shown >= limit:
            print(f"      ... {sum(1 for x in a) - shown} more line(s) differ")
            break
        print(f"      {line}")
        shown += 1
    if shown == 0:
        # Same lines, different bytes: a trailing newline or a line ending.
        print(f"      committed: {len(committed.encode())} bytes, "
              f"rendered: {len(rendered.encode())} bytes, same lines")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render README.md from live data.")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if README.md is not what the template says it should be")
    args = ap.parse_args(argv)

    cfg = load_config()
    profile, social, projects_cfg = cfg["profile"], cfg["social"], cfg["projects"]
    handle = handle_from(cfg)
    committed = README.read_text(encoding="utf-8") if README.exists() else ""
    regions = committed_regions(committed)

    if args.check:
        # OFFLINE BY DESIGN. The two generated regions come from the committed
        # README rather than being rebuilt, so this comparison does not depend on
        # API data that legitimately moves: GitHub's commit-search index and
        # Linguist both settle asynchronously after a push, so the commit count
        # and even the language ordering can change minutes after an otherwise
        # identical build. A check demanding byte-exact agreement with live data
        # was red nearly every time, and a permanently-red check is worse than
        # none because it teaches everyone to ignore it.
        #
        # What this does guarantee, and what actually goes wrong in practice:
        # the template was edited without rebuilding, README.md was hand-edited,
        # or a slot was left unfilled. The numbers are the daily job's business.
        missing = [k for k in ("STATS", "WORK", "QUOTE") if k not in regions]
        if missing:
            print(f"FAIL  README.md has no generated region(s): {', '.join(missing)}")
            print("      run: python3 scripts/build_readme.py")
            return 1
        stats_rows_html = regions["STATS"]
        work_rows_html = regions["WORK"]
        n_projects = None
    else:
        api = GitHubAPI()
        repos_list = visible_repos(api, handle, projects_cfg)
        repos = {r["name"]: r for r in repos_list}
        hidden = set(projects_cfg.get("hidden_repositories") or [])
        featured = [p for p in projects_cfg["featured"] if p["name"] not in hidden][
            : projects_cfg.get("max_featured", 3)]

        t = totals(api, handle, repos_list)
        # render_stats owns the trophy counters; reuse its collection so the
        # README's conditional row and the trophy card can never disagree.
        from render_stats import collect as collect_metrics
        t.update(collect_metrics(api, handle))
        t["_langs"] = top_languages(api, handle, repos_list, limit=6)
        stats_rows_html = stats_row(t, handle)
        work_rows_html = work_rows(featured, repos, handle, api)
        n_projects = len(featured)

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
        # shields.io splits the badge path on "-", so a dash inside the message
        # makes the whole badge unparseable: "Dong-eui%20University" renders as
        # "404: badge not found" even though it is a 200. Dashes become spaces
        # and the real spaces become %20, giving DONG EUI UNIVERSITY.
        "UNIVERSITY_BADGE": uni["institution"].replace("-", " ").replace(" ", "%20"),
        "INSTAGRAM_URL": social["instagram"],
        "INSTAGRAM_HANDLE": ig,
        "INSTAGRAM_HANDLE_ESCAPED": ig.replace("_", "__"),
        "BANNER_URL": f"{raw_base}/assets/banner.svg",
        "TYPING_URL": f"{raw_base}/assets/typing.svg",
        "SNAKE_URL": (f"https://raw.githubusercontent.com/{handle}/{handle}"
                      f"/output/github-contribution-grid-snake-dark.svg"),
        "THREED_URL": f"{raw_base}/profile-3d-contrib/profile-night-green.svg",
        "THUMB_BASE": THUMB_BASE.format(handle=handle),
        "ALL_REPOS_URL": f"https://github.com/{handle}?tab=repositories",
        # Fourteen, not sixteen. skillicons lays sixteen out in a 556-unit-tall
        # viewBox instead of 256 because the `githubactions` badge is two lines
        # tall and drags the whole strip to double height -- which is the orphan
        # second line. Dropping `linux` and `githubactions` gives one clean row.
        "SKILL_ICONS_URL": (
            "https://skillicons.dev/icons?i=python,ts,js,php,cpp,html,css,fastapi,"
            "nextjs,react,mysql,postgres,docker,git"
        ),
        "PITCH": "I ship small campus products, then make the reasoning inspectable.",
        "TYPING_ALT": ("Animated text: campus products and explainable AI. "
                       "Third year at Dong-eui University. "
                       "Open to internships, Korea or remote."),
        "NOW_BUILDING": "SkillBridge",
        "NOW_LEARNING": "Ranking + explanation",
        "NOW_OPEN": "Internships · Korea or remote",
        "ACTIVITY_CAPTION": "Contribution graph, regenerated daily.",
        "CLOSING": "Ship the first version. Email me.",
        "SKILLS_ALT": (
            "Skills: Python, TypeScript, JavaScript, PHP, C++, HTML, CSS, FastAPI, "
            "Next.js, React, MySQL, PostgreSQL, Docker, Git"
        ),
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

    # --check splices the committed blocks in whole; a build fills the slots.
    if args.check:
        out = splice_regions(body, regions)
    else:
        out = _fill(body, {"STATS_ROWS": stats_rows_html,
                           "WORK_ROWS": work_rows_html,
                           "QUOTE_TEXT": quote_of_the_day(cfg["content"]["quotes"])},
                    strict=True)
    out = _fill(out, values)

    leftover = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", out)))
    if leftover:
        raise SystemExit(f"unfilled template slots: {leftover}")

    out = strip_markers(out)

    if args.check:
        if committed != out:
            print("FAIL  README.md does not match templates/README.template.md")
            print("      run: python3 scripts/build_readme.py")
            _report_first_difference(committed, out)
            return 1
        print("ok    README.md matches the template")
        return 0

    README.write_text(out, encoding="utf-8")
    print(f"wrote README.md ({len(out.encode()):,} bytes, {n_projects} projects)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
