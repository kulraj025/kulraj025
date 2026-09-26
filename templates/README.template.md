<!--
  README.template.md — canonical source for README.md
  ====================================================
  README.md is this file with every {{FIELD}} filled in. Edit here, then copy to
  README.md, then let "Validate Profile" check the result.

  This page is VISUAL FIRST. A recruiter has to see motion and structure in about
  three seconds, so the reading order is: banner, typing lines, badges, stats,
  then three project cards. Almost no prose. The previous hand-written draft put a
  wall of centred text under a cropped heading and recruiters bounced.

  FIELD MAP — where each value comes from, and how fresh it is
  ------------------------------------------------------------
  Identity
    {{HANDLE}}              GitHub API  /user            login
    {{NAME}}                GitHub API  /user            name
    {{STUDY}}               config/profile.yml           degree subject, short form
    {{CITY}}                config/profile.yml           city only, no country
    {{EMAIL}}               config/profile.yml           manual
    {{EMAIL_ENCODED}}       derived from {{EMAIL}}       %40 for the @, shields only
    {{ACCENT_HEX}}          config/profile.yml           22D3EE, the only hue used
    {{STACK_THEME}}         config/profile.yml           tokyonight; see note below
    {{REPO}}                GitHub API  /user            owner/repo
    {{BRANCH}}              manual                       the branch raw URLs resolve to
    {{UNIVERSITY}}          config/profile.yml           manual, keep accurate
    {{UNIVERSITY_URL}}      manual                       must return 200
    {{UNIVERSITY_BADGE}}    derived from {{UNIVERSITY}}  spaces -> %20
    {{INSTAGRAM_URL}}       config/profile.yml           manual, clean URL only
    {{INSTAGRAM_HANDLE}}    derived from {{INSTAGRAM_URL}}
    {{INSTAGRAM_HANDLE_ESCAPED}}
                            derived from {{INSTAGRAM_HANDLE}}
                            shields.io treats _ as a space, so kul_rajneupane
                            must be written kul__rajneupane in a badge label

  Hero — the two graphics are files in this repository, not third-party URLs
    {{BANNER_URL}}          derived from {{REPO}}/{{BRANCH}}
                             assets/banner.svg. Carries its own dark background:
                             cyan text on transparency is invisible in light theme.
    {{TYPING_URL}}          derived from {{REPO}}/{{BRANCH}}
                             assets/typing.svg. Hand-built, because readme-typing-svg
                             concatenates every entry in `lines` into ONE textPath
                             and anchors it at the path origin, which cropped the
                             heading to "ilding campus products and XAI".
    {{PITCH}}               hand-written                 one line, under ~12 words

  Proof — third-party, so each needs a 200 before it goes in
    {{STATS_URL}}           GitHub API, proxied          hide=stars,prs,issues
                             Vanity counts are suppressed. This host is a working
                             mirror; github-readme-stats.vercel.app is 503 and
                             github-profile-trophy.vercel.app is 402.
    {{LANGS_URL}}           GitHub API, proxied          compact, 6 languages
    {{STREAK_URL}}          streak-stats.demolab.com    the one card that still serves
    {{STATS_ALT}}           hand-written                 describe the card, do not
                                                          restate the numbers only
    {{LANGS_ALT}}           hand-written
    {{STREAK_ALT}}          hand-written

  Now — one short label per cell, never a sentence
    {{NOW_BUILDING}}        hand-written
    {{NOW_LEARNING}}        hand-written
    {{NOW_OPEN}}            hand-written

  Featured work — exactly three. {{FEATURED_N_*}} is a family: _1_, _2_, _3_.
    {{FEATURED_N_NAME}}         project name, as a heading
    {{FEATURED_N_LINE1}}        what it is, in one line
    {{FEATURED_N_LINE2}}        what state it is in: deployed, or honestly not
    {{FEATURED_N_STACK_BADGES}} verified against the repo's real languages
    {{FEATURED_N_REPO_URL}}     must return 200
    {{FEATURED_N_BADGE_SLUG}}   derived from the repo path, / -> --
    {{FEATURED_N_DEMO_URL}}     omit the button entirely if there is no deployment.
                                Never point a Demo button at a 404.
    {{ALL_REPOS_URL}}      derived from {{HANDLE}}    ?tab=repositories

  Stack
    {{SKILL_ICONS_URL}}     skillicons.dev               must return 200
    {{SKILLS_ALT}}          hand-written                 list the icons for screen readers
    {{SKILL_GROUP_LABELS}}  hand-written                 a few words, under the row

  Activity — generated, so both carry a Fallback comment
    {{SNAKE_URL}}           Platane/snk, branch `output`
                             The segment after the repo name in a raw URL is the
                             BRANCH, so the file sits at the root of `output`.
    {{THREED_URL}}          yoshi389111/...-3d-contrib, on {{BRANCH}}
                             Filename must match the single theme un-tracked in
                             .gitignore; validate_readme.py reads it from there.
    {{ACTIVITY_CAPTION}}    hand-written                 six words or fewer

  Contact — same four badges as the hero, no more
    {{PRONOUNS}}            config/profile.yml
    {{LOCATION}}            config/profile.yml
    {{TIMEZONE}}            config/profile.yml           KST (UTC+9)
    {{CLOSING}}             hand-written                 one line

  WHAT MUST NEVER BE GENERATED
  ----------------------------
  * Any sentence about skill depth, research maturity, or "not research depth
    yet". The stack icons are the claim; an essay underneath it reads as an apology.
  * Follower, star and fork counts in display type. On a student profile they are
    small numbers, and enlarging them costs credibility.
  * A Demo button for a repo with no public deployment.
  * A portfolio or LinkedIn URL that has not been confirmed to return 200.
  * Any project description longer than two lines.

  A note on {{STACK_THEME}}
  -------------------------
  The brief asked for the `transparent` card theme. Transparent renders its text
  in #E4E2E2, which is correct on GitHub's dark theme and completely invisible on
  its light theme, which a large share of visitors use. A card that carries its own
  dark background is legible in both, so the theme is pinned and the deviation is
  deliberate. Re-check with `validate_readme.py --check-external` before changing it.
-->

<div align="center">

<img src="{{BANNER_URL}}" alt="{{NAME}} — {{STUDY}}, {{CITY}}" width="100%" />

<img src="{{TYPING_URL}}" alt="{{PITCH}}" width="100%" style="max-width:700px" />

<br>

**{{PITCH}}**

<br>

<a href="mailto:{{EMAIL}}"><img src="https://img.shields.io/badge/Email-{{EMAIL_ENCODED}}-{{ACCENT_HEX}}&style=for-the-badge" alt="Email {{EMAIL}}" height="30" /></a>
<a href="https://github.com/{{HANDLE}}"><img src="https://img.shields.io/badge/GitHub-{{HANDLE}}-{{ACCENT_HEX}}&style=for-the-badge&logo=github" alt="GitHub @{{HANDLE}}" height="30" /></a>
<a href="{{INSTAGRAM_URL}}"><img src="https://img.shields.io/badge/Instagram-{{INSTAGRAM_HANDLE_ESCAPED}}-{{ACCENT_HEX}}&style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram @{{INSTAGRAM_HANDLE}}" height="30" /></a>
<a href="{{UNIVERSITY_URL}}"><img src="https://img.shields.io/badge/University-{{UNIVERSITY_BADGE}}-{{ACCENT_HEX}}&style=for-the-badge" alt="{{UNIVERSITY}}" height="30" /></a>

</div>

---

<table>
  <tr>
    <td width="50%" align="center" valign="middle"><img src="{{STATS_URL}}" alt="{{STATS_ALT}}" width="100%" style="max-width:460px" /></td>
    <td width="50%" align="center" valign="middle"><img src="{{LANGS_URL}}" alt="{{LANGS_ALT}}" width="100%" style="max-width:460px" /></td>
  </tr>
  <tr>
    <td colspan="2" align="center"><img src="{{STREAK_URL}}" alt="{{STREAK_ALT}}" width="100%" style="max-width:520px" /></td>
  </tr>
</table>

## Now

<table>
  <tr>
    <td align="center"><b>BUILDING</b><br /><br />{{NOW_BUILDING}}</td>
    <td align="center"><b>LEARNING</b><br /><br />{{NOW_LEARNING}}</td>
    <td align="center"><b>OPEN TO</b><br /><br />{{NOW_OPEN}}</td>
  </tr>
</table>

## Work

### {{FEATURED_1_NAME}}

{{FEATURED_1_LINE1}}
{{FEATURED_1_LINE2}}

{{FEATURED_1_STACK_BADGES}}

<br>

<a href="{{FEATURED_1_REPO_URL}}"><img src="https://img.shields.io/badge/Repository-{{FEATURED_1_BADGE_SLUG}}-{{ACCENT_HEX}}&style=for-the-badge" alt="{{FEATURED_1_NAME}} repository" height="28" /></a>

### {{FEATURED_2_NAME}}

{{FEATURED_2_LINE1}}
{{FEATURED_2_LINE2}}

{{FEATURED_2_STACK_BADGES}}

<br>

<a href="{{FEATURED_2_REPO_URL}}"><img src="https://img.shields.io/badge/Repository-{{FEATURED_2_BADGE_SLUG}}-{{ACCENT_HEX}}&style=for-the-badge" alt="{{FEATURED_2_NAME}} repository" height="28" /></a>

### {{FEATURED_3_NAME}}

{{FEATURED_3_LINE1}}
{{FEATURED_3_LINE2}}

{{FEATURED_3_STACK_BADGES}}

<br>

<a href="{{FEATURED_3_REPO_URL}}"><img src="https://img.shields.io/badge/Repository-{{FEATURED_3_BADGE_SLUG}}-{{ACCENT_HEX}}&style=for-the-badge" alt="{{FEATURED_3_NAME}} repository" height="28" /></a> <a href="{{FEATURED_3_DEMO_URL}}"><img src="https://img.shields.io/badge/Live%20demo-Open-{{ACCENT_HEX}}&style=for-the-badge" alt="{{FEATURED_3_NAME}} live demo" height="28" /></a>

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
