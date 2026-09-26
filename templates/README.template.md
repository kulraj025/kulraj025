<!--
  README.template.md — canonical source for README.md
  ====================================================
  README.md is this file with every {{FIELD}} filled in. Edit here, then copy to
  README.md, then let "Validate Profile" check the result.

  FIELD MAP — where each value comes from, and how fresh it is
  ------------------------------------------------------------
  Identity
    {{NAME}}                GitHub API  /user            name
    {{HANDLE}}              GitHub API  /user            login
    {{EMAIL}}               config/profile.yml           manual
    {{EMAIL_ENCODED}}       derived from {{EMAIL}}       %40 for the @, shields only
    {{ACCENT}}              config/profile.yml           "cyan", the only hue used
    {{ACCENT_HEX}}          derived from {{ACCENT}}      22D3EE
    {{UNIVERSITY}}          config/profile.yml           manual, keep accurate
    {{UNIVERSITY_URL}}      manual                       must return 200
    {{UNIVERSITY_BADGE}}    derived from {{UNIVERSITY}}  spaces -> %20

  01 Hero
    {{ROLE_1}} {{ROLE_2}} {{ROLE_3}}
                            hand-written. Each line must stay under ~38 characters
                            or the typing SVG clips it.
    {{HEADLINE}}            config/profile.yml           manual, max 70 words
    {{EDUCATION_LINE}}      config/profile.yml           manual
    {{PORTFOLIO_URL}}       manual                       omit the button if absent
    {{INSTAGRAM_URL}}       config/profile.yml           manual, clean URL only
    {{INSTAGRAM_HANDLE}}    derived from {{INSTAGRAM_URL}}
    {{INSTAGRAM_HANDLE_ESCAPED}}
                            derived from {{INSTAGRAM_HANDLE}}
                            shields.io treats _ as a space, so kul_rajneupane
                            must be written kul__rajneupane in a badge label

  02 Now
    {{FOCUS_BUILDING}}      hand-written                 one flagship project
    {{FOCUS_LEARNING}}      hand-written                 be specific, not humble
    {{AVAILABILITY}}        config/profile.yml           manual

  03 Featured Work — exactly three. {{FEATURED_N_*}} is hand-written on purpose;
     only the stack badges and links are mechanical. See "WHAT MUST NEVER BE
     GENERATED" below.
    {{FEATURED_N_NAME}}         project name
    {{FEATURED_N_TAGLINE}}      what it is, in five words or fewer
    {{FEATURED_N_PROBLEM_AND_SHIP}}
                                the problem, then what actually shipped
    {{FEATURED_N_OUTCOME}}      verifiable: deployed, tested, used, or not yet
    {{FEATURED_N_STACK_BADGES}} verified against the repo's real languages
    {{FEATURED_N_SLUG}}         repo name, for the badge label
    {{FEATURED_N_URL}}          must return 200
    {{FEATURED_N_DEMO}}         optional, must return 200, omit the button if not
    {{REPO_COUNT}}          GitHub API  /user            public_repos

  04 Capabilities
    {{SKILLS_LANGUAGES}}    hand-written                 group, never a flat dump
    {{SKILLS_WEB}}          hand-written
    {{SKILLS_DATA_AI}}      hand-written                 mark in-progress as such
    {{SKILLS_SYSTEMS}}      hand-written
    {{SKILLS_TOOLS}}        hand-written
    {{SKILLICON_KEYS}}      skillicons.dev icon keys     only icons that are real

  05 Proof & Activity
    {{ACTIVITY_CAPTION}}    hand-written                 say what is live vs cached
    {{LANG_BADGES}}         sum of /repos/*/languages    recompute on refresh
    {{PRIMARY_LANGUAGE}}    largest entry in the above    derived

  06 / 07 / 08
    {{CURRENT_CHAPTER}}     hand-written                 what you are training now
    {{CONTACT_ASK}}         config/profile.yml           manual
    {{TIMEZONE}}            config/profile.yml           KST (UTC+9)
    {{CLOSING_LINE}}        hand-written                 one line, no throat-clearing
    {{LAST_REVIEW}}         date of the last accuracy pass

  WHAT MUST NEVER BE GENERATED
  ------------------------------------------------------------
  * Case studies. A generated description of a repo reads as filler, and a wrong
    one is worse than none. {{FEATURED_*}} stays hand-written; only the stack
    badges and repo links are mechanical.
  * Follower, star and fork counts in display type. On a student profile these are
    small numbers, and rendering "1 follower" at 40px actively costs credibility.
    Activity, streak, languages and shipped work are the honest signals.
  * A contribution history. Do not synthesise one. If there is little activity, show
    less, not a decorative chart of nothing.

  EDITING RULES
  ------------------------------------------------------------
  * Images: <img src="..." alt="..." width="100%" style="max-width:NNNpx" />
    The alt text is not optional — GitHub shows it in place of a failed image, and
    screen readers announce it. It is the fallback.
  * Every new third-party image gets a Fallback comment beside it.
  * No HTML tables with three or more columns. They collapse on a phone.
  * No <script>, <style>, <iframe>, <object>, <embed>, <form> or <video>. GitHub
    strips them, so the page would silently differ from what you wrote.
  * Accent colour is {{ACCENT}} and nothing else. Pick one hue and hold it.
-->

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=26&pause=2000&color=22D3EE&center=true&vCenter=true&width=620&lines={{ROLE_1}}+-+{{ROLE_2}}+-+{{ROLE_3}}" alt="{{NAME}} - {{ROLE_2}}." width="100%" style="max-width:620px" />

<br>

{{HEADLINE}}

<br>

{{EDUCATION_LINE}}

<br>

<a href="mailto:{{EMAIL}}"><img src="https://img.shields.io/badge/Email-{{EMAIL_ENCODED}}-{{ACCENT_HEX}}&style=for-the-badge" alt="Email {{EMAIL}}" height="28" /></a>
<a href="https://github.com/{{HANDLE}}"><img src="https://img.shields.io/badge/GitHub-{{HANDLE}}-{{ACCENT_HEX}}&style=for-the-badge&logo=github" alt="GitHub @{{HANDLE}}" height="28" /></a>
<a href="{{PORTFOLIO_URL}}"><img src="https://img.shields.io/badge/Portfolio-Visit-{{ACCENT_HEX}}&style=for-the-badge" alt="Portfolio" height="28" /></a>
<a href="{{INSTAGRAM_URL}}"><img src="https://img.shields.io/badge/Instagram-{{INSTAGRAM_HANDLE_ESCAPED}}-{{ACCENT_HEX}}&style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram @{{INSTAGRAM_HANDLE}}" height="28" /></a>
<a href="{{UNIVERSITY_URL}}"><img src="https://img.shields.io/badge/University-{{UNIVERSITY_BADGE}}-{{ACCENT_HEX}}&style=for-the-badge" alt="{{UNIVERSITY}}" height="28" /></a>

</div>

---

## 02 · Now

- **Building** — {{FOCUS_BUILDING}}
- **Learning** — {{FOCUS_LEARNING}}
- **Looking for** — {{AVAILABILITY}}

## 03 · Featured Work

<!-- Exactly three. One is the flagship; the other two prove range. -->

### 1. {{FEATURED_1_NAME}} — {{FEATURED_1_TAGLINE}}

{{FEATURED_1_PROBLEM_AND_SHIP}}

**Outcome:** {{FEATURED_1_OUTCOME}}

{{FEATURED_1_STACK_BADGES}}

[![Repository](https://img.shields.io/badge/Repository-{{HANDLE}}%2F{{FEATURED_1_SLUG}}-{{ACCENT_HEX}}&style=flat-square)]({{FEATURED_1_URL}})
<!-- Only add a demo button when the demo URL has been checked and returns 200. -->
[![Live demo](https://img.shields.io/badge/Live%20demo-Open-{{ACCENT_HEX}}&style=flat-square)]({{FEATURED_1_DEMO}})

---

### 2. {{FEATURED_2_NAME}} — {{FEATURED_2_TAGLINE}}

{{FEATURED_2_PROBLEM_AND_SHIP}}

**Outcome:** {{FEATURED_2_OUTCOME}}

{{FEATURED_2_STACK_BADGES}}

[![Repository](https://img.shields.io/badge/Repository-{{HANDLE}}%2F{{FEATURED_2_SLUG}}-{{ACCENT_HEX}}&style=flat-square)]({{FEATURED_2_URL}})

---

### 3. {{FEATURED_3_NAME}} — {{FEATURED_3_TAGLINE}}

{{FEATURED_3_PROBLEM_AND_SHIP}}

**Outcome:** {{FEATURED_3_OUTCOME}}

{{FEATURED_3_STACK_BADGES}}

[![Repository](https://img.shields.io/badge/Repository-{{HANDLE}}%2F{{FEATURED_3_SLUG}}-{{ACCENT_HEX}}&style=flat-square)]({{FEATURED_3_URL}})

<a href="https://github.com/{{HANDLE}}?tab=repositories">Browse all {{REPO_COUNT}} public repositories →</a>

## 04 · Capabilities

<!-- Grouped, never a flat dump. Mark anything still being learned as learning. -->

**Languages** — {{SKILLS_LANGUAGES}}

**Web** — {{SKILLS_WEB}}

**Data & AI** — {{SKILLS_DATA_AI}}

**Systems** — {{SKILLS_SYSTEMS}}

**Tools** — {{SKILLS_TOOLS}}

<img src="https://skillicons.dev/icons?i={{SKILLICON_KEYS}}" alt="Skill icons" width="100%" style="max-width:520px" />

## 05 · Proof & Activity

{{ACTIVITY_CAPTION}}

<!-- SETUP: enable GitHub Actions workflows listed in .github/workflows to generate snake + 3d graphs -->

<img src="https://streak-stats.demolab.com/?user={{HANDLE}}&theme=dark&hide_border=true" alt="GitHub contribution streak for {{HANDLE}}" width="100%" style="max-width:520px" />
<!-- Fallback: state the real totals in words here, so the section survives an outage. -->

<img src="https://raw.githubusercontent.com/{{HANDLE}}/{{HANDLE}}/output/github-contribution-grid-snake.svg" alt="Contribution snake animation" width="100%" style="max-width:820px" />
<!-- Fallback: the language breakdown below carries the same signal without an image. -->

<img src="https://raw.githubusercontent.com/{{HANDLE}}/{{HANDLE}}/main/profile-3d-contrib/profile-night-rainbow.svg" alt="3D contribution calendar" width="100%" style="max-width:820px" />

**Languages across public repositories** — measured by bytes written, not self-declared.

{{LANG_BADGES}}

<!--
  Optional third-party widgets. Leave commented out rather than shipping a broken
  image; each one gets its own Fallback comment if it is ever enabled.

  https://github-readme-stats.vercel.app/api?username={{HANDLE}}&show_icons=true&hide_rank=true&hide_border=true
  https://github-readme-stats.vercel.app/api/top-langs/?username={{HANDLE}}&layout=compact&hide_border=true
  https://github-profile-trophy.vercel.app/?username={{HANDLE}}&column=7&no-bg=true
-->

## 06 · Education & Current Chapter

**{{UNIVERSITY}}** — {{EDUCATION_LINE}}

{{CURRENT_CHAPTER}}

## 07 · Contact

{{CONTACT_ASK}}

[![Email](https://img.shields.io/badge/Email-{{EMAIL_ENCODED}}-{{ACCENT_HEX}}&style=for-the-badge)](mailto:{{EMAIL}})
[![GitHub](https://img.shields.io/badge/GitHub-{{HANDLE}}-{{ACCENT_HEX}}&style=for-the-badge&logo=github&logoColor=white)](https://github.com/{{HANDLE}})
[![Instagram](https://img.shields.io/badge/Instagram-{{INSTAGRAM_HANDLE_ESCAPED}}-{{ACCENT_HEX}}&style=for-the-badge&logo=instagram&logoColor=white)]({{INSTAGRAM_URL}})

{{TIMEZONE}}

## 08 · Footer

{{CLOSING_LINE}}

<sub>Contribution graphics regenerate daily via GitHub Actions. Last content review: {{LAST_REVIEW}}.</sub>
