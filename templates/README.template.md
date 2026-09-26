<!--
  README.template.md — canonical source for README.md
  ====================================================
  README.md is this file with every double-brace slot filled in. To change the
  page: edit here, run `python3 scripts/build_readme.py`, then let "Validate
  Profile" check the result. Never edit README.md alone; the next build will
  overwrite it.

  This page is VISUAL FIRST. A recruiter has to see motion and structure in about
  three seconds, so the reading order is: banner, typing lines, badges, stats,
  then the project grid. Almost no prose.

  WHAT IS GENERATED AND WHAT IS NOT
  ---------------------------------
  Only {{WORK_ROWS}} and {{STATS_ROWS}} are computed, by scripts/build_readme.py.
  Both exist because a hand-typed version was a page that lied: a repository
  gained a deployment and no Live badge appeared, or lost its demo and a dead
  button stayed. Everything a reader reads as words is written here by hand, so
  a generator bug can misplace a value but cannot replace the writing.

  The generator never runs on a schedule. A previous one did, and overwrote this
  file with generated filler within 24 hours. You run this one deliberately and
  read the diff. `tests/test_readme_is_current.py` fails the build if the
  committed README and a fresh render disagree.

  FIELD MAP — where each value comes from, and how fresh it is
  ------------------------------------------------------------
  Identity
    {{HANDLE}}              config/profile.yml           social.github, last path segment
    {{NAME}}                config/profile.yml           display_name
    {{STUDY}}               config/profile.yml           degree subject, short form
    {{CITY}}                config/profile.yml           city only, no country
    {{LOCATION}}            config/profile.yml           city + country, the contact line
    {{PRONOUNS}}            config/profile.yml
    {{TIMEZONE}}            config/profile.yml           KST (UTC+9)
    {{EMAIL}}               config/profile.yml           manual
    {{EMAIL_ENCODED}}       derived from {{EMAIL}}       %40 for the @, shields only
    {{ACCENT_HEX}}          scripts/metrics.py           22D3EE, the only hue used
    {{UNIVERSITY}}          config/profile.yml           manual, keep accurate
    {{UNIVERSITY_URL}}      config/profile.yml           must return 200
    {{UNIVERSITY_BADGE}}    derived from {{UNIVERSITY}}  spaces -> %20
    {{INSTAGRAM_URL}}       config/profile.yml           manual, clean URL only
    {{INSTAGRAM_HANDLE}}    derived from {{INSTAGRAM_URL}}
    {{INSTAGRAM_HANDLE_ESCAPED}}
                            derived from {{INSTAGRAM_HANDLE}}
                            shields.io treats _ as a space, so kul_rajneupane
                            must be written kul__rajneupane in a badge label

  Hero — the two graphics are files in this repository, not third-party URLs
    {{BANNER_URL}}          derived from {{HANDLE}}       assets/banner.svg. Carries
                             its own dark background: cyan text on transparency is
                             invisible in GitHub's light theme.
    {{TYPING_URL}}          derived from {{HANDLE}}       assets/typing.svg. Hand-built,
                             because readme-typing-svg concatenates every entry in
                             `lines` into ONE textPath anchored at the path origin,
                             which cropped the heading to "ilding campus products
                             and XAI". `multiline=true` is ignored by the live version.
    {{PITCH}}               hand-written                 one line, under ~12 words
    {{TYPING_ALT}}          hand-written                 describes what the graphic
                             animates. It is NOT {{PITCH}}: the pitch is the
                             visible bold line directly below the image, and
                             reusing it as the alt makes a screen reader
                             announce the same sentence twice in a row.

  Stats — three rows, and the third is conditional
    {{STATS_ROWS}}          build_readme.py              the whole block: row 1 is
                             stats.svg beside langs.svg, row 2 is the streak card
                             centred, row 3 is trophies.svg. The trophy row is
                             emitted only when an award threshold is genuinely met,
                             because drawing an empty trophy card looks like a bug.

                             stats.svg and langs.svg are rendered by
                             scripts/render_stats.py into assets/ and committed,
                             rather than embedded from a host. The official
                             github-readme-stats is 503 DEPLOYMENT_PAUSED (it fails
                             for torvalds too) and github-profile-trophy is 402
                             DEPLOYMENT_DISABLED. A 503 renders as a broken image
                             in the first screenful, and depending on an unofficial
                             mirror would tie the profile to a stranger's account.

                             Alt text is derived from the fetched values, so it
                             cannot describe a card whose numbers have since moved.

  Now — one short label per cell, never a sentence
    {{NOW_BUILDING}}        hand-written
    {{NOW_LEARNING}}        hand-written
    {{NOW_OPEN}}            hand-written

  Work — the grid, generated from config order
    {{WORK_ROWS}}           build_readme.py              one project per cell: an
                             opengraph preview, the name in bold, one line of copy,
                             the stack chips, a Repository button, and a Live demo
                             button ONLY when a URL answers 200.
    {{ALL_REPOS_URL}}       derived from {{HANDLE}}      ?tab=repositories

    Everything structural about a project lives in config/profile.yml under
    `projects.featured`, in this order: summary, stack, and which repository.
    Adding a fourth project pairs it into the trailing row with no template edit.
    The `summary` is curated rather than read from the repository description,
    because those are one sentence of marketing or, in one case, literally "x".
    The `stack` is curated rather than derived from the byte histogram on
    purpose: measured, skillbridge reads JavaScript-first, which misrepresents a
    Python service that happens to ship a frontend.

  Stack
    {{SKILL_ICONS_URL}}     skillicons.dev               must return 200
    {{SKILLS_ALT}}          hand-written                 list the icons for screen readers
    {{SKILL_GROUP_LABELS}}  hand-written                 a few words, under the row

  Activity — generated, so both carry a Fallback comment
    {{SNAKE_URL}}           Platane/snk, branch `output`
                             The segment after the repo name in a raw URL is the
                             BRANCH, so the file sits at the root of `output`.
    {{THREED_URL}}          yoshi389111/...-3d-contrib, on main
                             Filename must match the single theme un-tracked in
                             .gitignore; validate_readme.py reads it from there.
    {{ACTIVITY_CAPTION}}    hand-written                 six words or fewer

  Contact — same four badges as the hero, no more
    {{CLOSING}}             hand-written                 one line

  WHAT MUST NEVER BE GENERATED
  ----------------------------
  * Any sentence about skill depth, research maturity, or "not research depth
    yet". The stack icons are the claim; an essay underneath it reads as an apology.
  * A Demo button for a repo with no verified public deployment.
  * A portfolio or LinkedIn URL that has not been confirmed to return 200.
  * A number not returned by the API. Every count here is measured; if a figure
    would have to be guessed, the field stays empty instead.
  * Any project description longer than one line.
-->

<div align="center">

<img src="{{BANNER_URL}}" alt="{{NAME}} — {{STUDY}}, {{CITY}}" width="100%" />

<img src="{{TYPING_URL}}" alt="{{TYPING_ALT}}" width="100%" style="max-width:700px" />

<br>

**{{PITCH}}**

<br>

<a href="mailto:{{EMAIL}}"><img src="https://img.shields.io/badge/Email-{{EMAIL_ENCODED}}-{{ACCENT_HEX}}&style=for-the-badge" alt="Email {{EMAIL}}" height="30" /></a>
<a href="https://github.com/{{HANDLE}}"><img src="https://img.shields.io/badge/GitHub-{{HANDLE}}-{{ACCENT_HEX}}&style=for-the-badge&logo=github" alt="GitHub @{{HANDLE}}" height="30" /></a>
<a href="{{INSTAGRAM_URL}}"><img src="https://img.shields.io/badge/Instagram-{{INSTAGRAM_HANDLE_ESCAPED}}-{{ACCENT_HEX}}&style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram @{{INSTAGRAM_HANDLE}}" height="30" /></a>
<a href="{{UNIVERSITY_URL}}"><img src="https://img.shields.io/badge/University-{{UNIVERSITY_BADGE}}-{{ACCENT_HEX}}&style=for-the-badge" alt="{{UNIVERSITY}}" height="30" /></a>

</div>

---

## Stats

<table>
{{STATS_ROWS}}
</table>

## Now

<table>
  <tr>
    <td width="33%" align="center"><b>BUILDING</b><br />{{NOW_BUILDING}}</td>
    <td width="33%" align="center"><b>LEARNING</b><br />{{NOW_LEARNING}}</td>
    <td width="33%" align="center"><b>OPEN TO</b><br />{{NOW_OPEN}}</td>
  </tr>
</table>

## Work

<table>
{{WORK_ROWS}}
</table>

<br>

[Browse all public repositories →]({{ALL_REPOS_URL}})

## Stack

<div align="center">

<img src="{{SKILL_ICONS_URL}}" alt="{{SKILLS_ALT}}" width="100%" style="max-width:760px" />

<br>

<sub>{{SKILL_GROUP_LABELS}}</sub>

</div>

## Activity

<!-- Fallback: if the snake is missing the page still reads fine; it is decoration. -->
<div align="center">

<img src="{{SNAKE_URL}}" alt="Contribution snake animation" width="100%" style="max-width:700px" />

<br>

<!-- Fallback: the 3D calendar appears after the first workflow run. -->
<img src="{{THREED_URL}}" alt="3D contribution calendar" width="100%" style="max-width:560px" />

<br>

<sub>{{ACTIVITY_CAPTION}}</sub>

</div>

---

## Contact

<div align="center">

<a href="mailto:{{EMAIL}}"><img src="https://img.shields.io/badge/Email-{{EMAIL_ENCODED}}-{{ACCENT_HEX}}&style=for-the-badge" alt="Email {{EMAIL}}" height="30" /></a>
<a href="https://github.com/{{HANDLE}}"><img src="https://img.shields.io/badge/GitHub-{{HANDLE}}-{{ACCENT_HEX}}&style=for-the-badge&logo=github" alt="GitHub @{{HANDLE}}" height="30" /></a>
<a href="{{INSTAGRAM_URL}}"><img src="https://img.shields.io/badge/Instagram-{{INSTAGRAM_HANDLE_ESCAPED}}-{{ACCENT_HEX}}&style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram @{{INSTAGRAM_HANDLE}}" height="30" /></a>
<a href="{{UNIVERSITY_URL}}"><img src="https://img.shields.io/badge/University-{{UNIVERSITY_BADGE}}-{{ACCENT_HEX}}&style=for-the-badge" alt="{{UNIVERSITY}}" height="30" /></a>

<br>

<sub>{{PRONOUNS}} · {{LOCATION}} · {{TIMEZONE}}</sub>

<br>

**{{CLOSING}}**

</div>
