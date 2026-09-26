<!--
  README.template.md — canonical source for README.md
  ====================================================
  README.md is this file with every double-brace slot filled in. To change the
  page: edit here, run `python3 scripts/build_readme.py`, then let "Validate
  Profile" check the result. Never edit README.md alone; the next build will
  overwrite it.

  THE DESIGN SYSTEM — one rhythm, repeated
  ----------------------------------------
  Every section is the same three things in the same order:

      <p align="center"><code>NAME</code></p>     a small monospace label
      ...content...                                 centred
      ---                                           a horizontal rule

  The label is real text in a <code> element, not an image. Monospace and
  centring therefore survive GitHub's sanitiser with no CSS at all, which is the
  only thing guaranteed to survive. `style="color:#22D3EE"` is attached as
  progressive enhancement: if GitHub keeps it the label is cyan, and if it is
  stripped the label is still identical on every section, which is the part
  that actually matters. Do not move layout into that style attribute.

  There are no `## ` headings. They were the reason the page did not look like
  one thing: GitHub renders h2 at a size that competes with the banner, and a
  numbered "02 · Now" read as a slide deck. The anchor links are gone as a
  result, which is a fair trade for a page that scans as a single object.

  Hero: at most one sentence of body text, and it is {{PITCH}}. That is a
  deliberate ceiling, not an oversight — a recruiter decides in about three
  seconds and the sentence is there to be read once, not skimmed twice.

  BADGES — the rule that was learned the hard way
  ----------------------------------------------
  Every shields.io URL must start its query string with `?`:

      ...badge/Email-x-22D3EE?style=for-the-badge      renders
      ...badge/Email-x-22D3EE&style=for-the-badge      "404: badge not found"

  Both return HTTP 200. The broken one returns a 200 SVG whose aria-label is
  `404: badge not found`, which is why a status-code check reports the whole
  row as healthy while the page shows red placeholders. validate_readme.py now
  reads the body. Do not "fix" a badge by swapping `?` back to `&`.

  Underscores: shields.io treats `_` in the label as a space, so a literal
  underscore must be doubled. `kul_rajneupane` renders as "KUL RAJNEUPANE";
  `kul__rajneupane` renders as "KUL_RAJNEUPANE". The doubled form is correct
  and is not a hack — it is the documented escape.

  Dashes: the path is split on `-`, so a label may not contain one.
  `Dong-eui%20University` is therefore unparseable; `Dong%20eui%20University`
  renders the full name. See {{UNIVERSITY_BADGE}}.

  WHAT IS GENERATED AND WHAT IS NOT
  ---------------------------------
  Three regions are computed by scripts/build_readme.py, each fenced by a pair
  of marker comments naming it: BEGIN GENERATED:STATS paired with
  END GENERATED:STATS, and the same for WORK and QUOTE. (They are written here
  without the angle brackets on purpose. This header is closed by the first
  line containing only a closing-comment marker, so a complete marker comment
  written literally in here would end the header early and dump the rest of
  this file -- field map included -- onto the page. See HEADER_RE in
  scripts/build_readme.py and the header_strip test.)

  They exist because a hand-typed version is a page that lies: a repository
  gains a deployment and no Live badge appears, or loses its demo and a dead
  button stays. Everything a reader reads as words is written here by hand, so
  a generator bug can misplace a value but cannot replace the writing.

  WHY THE MARKERS EXIST
  ---------------------
  `--check` has to verify the README against this template on a machine with no
  network and no API budget. So it substitutes the *committed* contents of the
  three generated regions back into the template and compares the rest byte for
  byte. Offline, deterministic, and it catches the real bug class: a template
  edited without rebuilding, a hand-edit to README.md, a slot left unfilled.

  It deliberately does NOT compare the numbers. GitHub's commit-search index
  and Linguist both settle asynchronously after a push — the commit count and
  even the language ordering change minutes later — so a check demanding
  byte-exact agreement with live API data was red almost every time. A
  permanently-red check is worse than no check. The numbers are owned by the
  daily run in profile-widgets.yml; this file owns everything else.

  FIELD MAP — where each value comes from, and how fresh it is
  ------------------------------------------------------------
  Identity
    {{HANDLE}}              config/profile.yml           social.github, last segment
    {{NAME}}                config/profile.yml           display_name
    {{STUDY}}               config/profile.yml           degree subject, short form
    {{CITY}}                config/profile.yml           university city, used only in
                             the banner alt so the graphic carries the location
                             without the line under it having to
    {{LOCATION}}            config/profile.yml           city + country, contact line
    {{PRONOUNS}}            config/profile.yml
    {{TIMEZONE}}            config/profile.yml           KST (UTC+9)
    {{EMAIL}}               config/profile.yml           manual
    {{EMAIL_ENCODED}}       derived from {{EMAIL}}       %40 for the @, shields only
    {{ACCENT_HEX}}          scripts/metrics.py           22D3EE, the only hue used
    {{UNIVERSITY}}          config/profile.yml           manual, keep accurate
    {{UNIVERSITY_URL}}      config/profile.yml           must return 200
    {{UNIVERSITY_BADGE}}    derived from {{UNIVERSITY}}  dashes removed, spaces -> %20
    {{INSTAGRAM_URL}}       config/profile.yml           clean URL only, no ?stkn=
    {{INSTAGRAM_HANDLE}}    derived from {{INSTAGRAM_URL}}
    {{INSTAGRAM_HANDLE_ESCAPED}}
                             derived from {{INSTAGRAM_HANDLE}}
                             _ doubled, because shields reads it as a space

  Hero — both graphics are files in this repository, not third-party URLs
    {{BANNER_URL}}          derived from {{HANDLE}}       assets/banner.svg. Carries
                             its own dark background: cyan on transparency is
                             invisible in GitHub's light theme.
    {{TYPING_URL}}          derived from {{HANDLE}}       assets/typing.svg, 700 wide.
                             Hand-built, because readme-typing-svg concatenates every
                             entry in `lines` into ONE textPath anchored at the path
                             origin, which cropped the heading to "ilding campus
                             products and XAI".
    {{PITCH}}               hand-written                 one line, under ~12 words
    {{TYPING_ALT}}          hand-written                 describes what the graphic
                             animates. It is NOT {{PITCH}}: the pitch is the visible
                             bold line below the image, and reusing it as the alt
                             makes a screen reader say the same sentence twice.

  Stats — three rows, the third conditional
    {{STATS_ROWS}}          build_readme.py              row 1 stats.svg beside
                             langs.svg, row 2 the streak card centred, row 3
                             trophies.svg. The trophy row is emitted only when an
                             award threshold is genuinely met, because drawing an
                             empty trophy card looks like a bug.

                             stats.svg and langs.svg are rendered by
                             scripts/render_stats.py into assets/ and committed
                             rather than embedded from a host. The official
                             github-readme-stats is 503 DEPLOYMENT_PAUSED and
                             github-profile-trophy is 402 DEPLOYMENT_DISABLED —
                             re-checked, and both fail for torvalds as well, so
                             it is not this account's problem to fix. A card that
                             503s is a broken image in the first screenful.

  Now
    {{NOW_BUILDING}}        config: projects.featured[0] the project in flight
    {{NOW_LEARNING}}        hand-written                 one line
    {{NOW_OPEN}}            hand-written                 one line

  Work
    {{WORK_ROWS}}           build_readme.py              one project per cell: a
                             thumbnail from assets/work/, the name in bold, one
                             line of copy, the stack chips, then a Repository
                             button and a Live button only when a demo answers.
    {{THUMB_BASE}}          derived from {{HANDLE}}       raw base for assets/work/
    {{ALL_REPOS_URL}}       derived from {{HANDLE}}       the one link under the grid

  Note — the rotating line
    {{QUOTE_TEXT}}          build_readme.py              content.quotes[day_of_year % n]
    {{QUOTE_LABEL}}         hand-written                 the word above it

  Stack
    {{SKILL_ICONS_URL}}     hand-written                 14 icons. Sixteen made
                             skillicons emit a 556-unit-tall viewBox instead of 256,
                             because the githubactions badge is two lines tall and
                             doubled the whole strip; fourteen is one clean row.
    {{SKILLS_ALT}}          hand-written                 the same list in words

  Activity
    {{SNAKE_URL}}           output branch                the one third-party card
                             still serving
    {{THREED_URL}}          derived from {{HANDLE}}       profile-3d-contrib, tracked
    {{ACTIVITY_CAPTION}}    hand-written                 six words maximum

  Contact
    {{CLOSING}}             hand-written                 the last line
-->

<div align="center">

<img src="{{BANNER_URL}}" alt="{{NAME}} — {{STUDY}}, {{CITY}}" width="100%" />

<img src="{{TYPING_URL}}" alt="{{TYPING_ALT}}" width="100%" style="max-width:700px" />

<br>

**{{PITCH}}**

<br>

<a href="mailto:{{EMAIL}}"><img src="https://img.shields.io/badge/Email-{{EMAIL_ENCODED}}-{{ACCENT_HEX}}?style=for-the-badge&logo=gmail&logoColor=white&labelColor=0B1220" alt="Email {{EMAIL}}" height="30" /></a>
<a href="https://github.com/{{HANDLE}}"><img src="https://img.shields.io/badge/GitHub-{{HANDLE}}-{{ACCENT_HEX}}?style=for-the-badge&logo=github&logoColor=white&labelColor=0B1220" alt="GitHub @{{HANDLE}}" height="30" /></a>
<a href="{{INSTAGRAM_URL}}"><img src="https://img.shields.io/badge/Instagram-{{INSTAGRAM_HANDLE_ESCAPED}}-E4405F?style=for-the-badge&logo=instagram&logoColor=white&labelColor=0B1220" alt="Instagram @{{INSTAGRAM_HANDLE}}" height="30" /></a>
<a href="{{UNIVERSITY_URL}}"><img src="https://img.shields.io/badge/University-{{UNIVERSITY_BADGE}}-{{ACCENT_HEX}}?style=for-the-badge&logo=google-scholar&logoColor=white&labelColor=0B1220" alt="{{UNIVERSITY}}" height="30" /></a>

</div>

---

<p align="center"><code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.22em">STATS</code></p>

<!-- BEGIN GENERATED:STATS -->
<table>
{{STATS_ROWS}}
</table>
<!-- END GENERATED:STATS -->

---

<p align="center"><code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.22em">NOW</code></p>

<table>
  <tr>
    <td width="33%" align="center" valign="top">
      <code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.16em">BUILDING</code><br />
      <b>{{NOW_BUILDING}}</b>
    </td>
    <td width="33%" align="center" valign="top">
      <code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.16em">LEARNING</code><br />
      <b>{{NOW_LEARNING}}</b>
    </td>
    <td width="33%" align="center" valign="top">
      <code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.16em">OPEN TO</code><br />
      <b>{{NOW_OPEN}}</b>
    </td>
  </tr>
</table>

---

<p align="center"><code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.22em">WORK</code></p>

<!-- BEGIN GENERATED:WORK -->
<table>
{{WORK_ROWS}}
</table>
<!-- END GENERATED:WORK -->

<br>

<p align="center"><a href="{{ALL_REPOS_URL}}">Browse all repositories →</a></p>

---

<p align="center"><code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.22em">STACK</code></p>

<div align="center">

<img src="{{SKILL_ICONS_URL}}" alt="{{SKILLS_ALT}}" width="100%" style="max-width:780px" />

</div>

---

<p align="center"><code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.22em">ACTIVITY</code></p>

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

<p align="center"><code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.22em">NOTE</code></p>

<!-- BEGIN GENERATED:QUOTE -->
<p align="center"><sub>{{QUOTE_TEXT}}</sub></p>
<!-- END GENERATED:QUOTE -->

---

<p align="center"><code style="color:#{{ACCENT_HEX}};font-size:11px;letter-spacing:0.22em">CONTACT</code></p>

<div align="center">

<a href="mailto:{{EMAIL}}"><img src="https://img.shields.io/badge/Email-{{EMAIL_ENCODED}}-{{ACCENT_HEX}}?style=for-the-badge&logo=gmail&logoColor=white&labelColor=0B1220" alt="Email {{EMAIL}}" height="30" /></a>
<a href="https://github.com/{{HANDLE}}"><img src="https://img.shields.io/badge/GitHub-{{HANDLE}}-{{ACCENT_HEX}}?style=for-the-badge&logo=github&logoColor=white&labelColor=0B1220" alt="GitHub @{{HANDLE}}" height="30" /></a>
<a href="{{INSTAGRAM_URL}}"><img src="https://img.shields.io/badge/Instagram-{{INSTAGRAM_HANDLE_ESCAPED}}-E4405F?style=for-the-badge&logo=instagram&logoColor=white&labelColor=0B1220" alt="Instagram @{{INSTAGRAM_HANDLE}}" height="30" /></a>
<a href="{{UNIVERSITY_URL}}"><img src="https://img.shields.io/badge/University-{{UNIVERSITY_BADGE}}-{{ACCENT_HEX}}?style=for-the-badge&logo=google-scholar&logoColor=white&labelColor=0B1220" alt="{{UNIVERSITY}}" height="30" /></a>

<br>

<sub>{{PRONOUNS}} · {{LOCATION}} · {{TIMEZONE}} · internships welcome</sub>

<br>

**{{CLOSING}}**

</div>
