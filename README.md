<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=26&pause=2000&color=22D3EE&center=true&vCenter=true&width=620&lines=Kulraj+Neupane+-+Student+Developer,Building+campus+products+and+XAI+systems,Open+to+internships+-+remote+or+Korea" alt="Kulraj Neupane - Student Developer. Building campus products and XAI systems. Open to internships - remote or Korea." width="100%" style="max-width:620px" />

<br>

I'm a third-year **Intelligence Computing** student at **Dong-eui University** in Busan, South Korea.
I build small, real products for real users — a campus communication platform, a student volunteer
programme, and <b>SkillBridge</b>, an explainable matching tool that shows *why* a student fits a role.
I care about working software, clear reasoning, and shipping the first version.

<br>

B.Sc. (Hons) · Intelligence Computing · 3rd Year, 6th Semester · Dong-eui University

<br>

<a href="mailto:Kulraj024@gmail.com"><img src="https://img.shields.io/badge/Email-Kulraj024%40gmail.com-22D3EE?style=for-the-badge" alt="Email Kulraj024@gmail.com" height="28" /></a>
<a href="https://github.com/kulraj025"><img src="https://img.shields.io/badge/GitHub-kulraj025-22D3EE?style=for-the-badge&logo=github" alt="GitHub @kulraj025" height="28" /></a>
<a href="https://kulraj025.github.io/Initial-Portfolio-Website-/"><img src="https://img.shields.io/badge/Portfolio-Visit-22D3EE?style=for-the-badge" alt="Portfolio" height="28" /></a>
<a href="https://eng.deu.ac.kr/eng/index.do"><img src="https://img.shields.io/badge/University-Dong--eui-22D3EE?style=for-the-badge" alt="Dong-eui University" height="28" /></a>

</div>

---

## 02 · Now

- **Building** — **SkillBridge**: evidence-based skill and opportunity matching. The matcher is deliberately transparent and rule-based first, with a documented path to a real model once a labelled evaluation set exists.
- **Learning** — machine learning, applied to ranking and explanation rather than to leaderboards. Currently focused on evaluation, not accuracy claims.
- **Looking for** — an internship in full-stack or AI product work, in Korea or remote. Open to research assistant roles as well.

## 03 · Featured Work

### 1. SkillBridge — explainable skill & opportunity matching

Students can rarely answer two questions: *which of my skills does this job actually need*, and *why am I a
good match?* Most matching tools return a score with no argument attached. SkillBridge is built the other way
round — every match traces back to specific evidence on a student's profile.

The Python backend runs on FastAPI with a deterministic, inspectable matcher, a Pydantic data model, and
repository-backed persistence. Development was spec-first: product spec, data model, roadmap, and a user
research plan were written before the scoring function, precisely so the rules could be argued about and
replaced later without rewriting the product around them.

**Outcome:** runs end to end locally via Docker Compose, with tests on the matcher. Not publicly deployed yet.

`Python` `FastAPI` `Pydantic` `Docker` `pytest`

[![Repository](https://img.shields.io/badge/Repository-kulraj025%2Fskillbridge-22D3EE?style=flat-square)](https://github.com/kulraj025/skillbridge)

---

### 2. Helping Station DEU — a draw people can verify

A student volunteer programme at my university ended each day with a lucky draw. The obvious version of that
feature is the one nobody believes. This one is designed to be checked.

Participants register in about a minute, see only their entry number, and watch the draw live. Organisers get
an event lifecycle that blocks invalid transitions, QR and A4 poster export, attendance and eligibility
tracking, prize claims, and CSV/JSON export. Every sensitive action lands in an append-only audit log, and a
completed draw can never be edited — only corrected by append.

The fairness mechanism is the centre of it: the participant pool is frozen and hashed, selection is
cryptographic on the server, the commitment is published, and anybody can run the verification step
afterwards against the published data.

**Outcome:** 129 files, 6 test suites, strict TypeScript, Next.js + Prisma + PostgreSQL. Written to be run at
a real campus event, with a local PGlite database so it can be demonstrated without infrastructure.

`TypeScript` `Next.js` `React` `Prisma` `PostgreSQL` `Zod` `Vitest` `Tailwind CSS`

[![Repository](https://img.shields.io/badge/Repository-kulraj025%2Fhelping--station--deu-22D3EE?style=flat-square)](https://github.com/kulraj025/helping-station-deu)

---

### 3. Campus Connect X v2 — campus communication, in one place

Campus announcements, events, and student interaction were spread across channels that nobody controlled.
Campus Connect puts them in a single responsive web app, which makes the whole thing a real deployment
target rather than a class exercise.

A full-stack PHP and MySQL platform: announcements, event updates, student interaction, and campus services
behind a simple interface, with a SQL schema and an admin side.

**Outcome:** deployed and publicly reachable.

`PHP` `MySQL` `HTML` `CSS` `JavaScript`

[![Repository](https://img.shields.io/badge/Repository-kulraj025%2Fcampus__connect__x__v2-22D3EE?style=flat-square)](https://github.com/kulraj025/campus_connect_x_v2)
[![Live demo](https://img.shields.io/badge/Live%20demo-Open-22D3EE?style=flat-square)](https://kulraj025.github.io/campus_connect_x_v2/)

<a href="https://github.com/kulraj025?tab=repositories">Browse all 12 public repositories →</a>

## 04 · Capabilities

**Languages** — Python, TypeScript, PHP, JavaScript, C++, SQL, HTML/CSS

**Web** — Next.js, React, FastAPI, REST, MySQL, PostgreSQL, Prisma, Tailwind CSS

**Data & AI** — information retrieval, ranking, and **learning**: model evaluation and explainability. Hands-on
with classical and learned ranking; not yet at research depth, and I say so rather than implying otherwise.

**Systems** — Docker, Docker Compose, GitHub Actions, Next.js API routes, PostgreSQL migrations, CSV/JSON export

**Tools** — Git, GitHub, Linux, Postman, Figma, Vitest, pytest, ESLint, Prettier

<img src="https://skillicons.dev/icons?i=python,typescript,js,php,mysql,postgres,react,nextjs,docker,git,github,tailwind,prisma,fastapi,cpp,html,css" alt="Skill icons: Python, TypeScript, JavaScript, PHP, MySQL, PostgreSQL, React, Next.js, Docker, Git, GitHub, Tailwind, Prisma, FastAPI, C++, HTML, CSS" width="100%" style="max-width:520px" />

## 05 · Proof & Activity

Live from the GitHub API. The contribution snake and the 3D calendar are regenerated daily by Actions, so they
are always current; the streak card is fetched at page load.

<!-- SETUP: enable GitHub Actions workflows listed in .github/workflows to generate snake + 3d graphs -->

<img src="https://streak-stats.demolab.com/?user=kulraj025&theme=dark&hide_border=true" alt="GitHub contribution streak for kulraj025: 61 total contributions, current streak 2 days, longest streak 2 days" width="100%" style="max-width:520px" />

<!-- Fallback if the streak service is down: 61 contributions in the last year across 12 public repositories. -->

<img src="https://raw.githubusercontent.com/kulraj025/kulraj025/output/github-contribution-grid-snake.svg" alt="Contribution snake animation" width="100%" style="max-width:820px" />

<!-- Fallback: a static reading of the same data is the language breakdown immediately below. -->

<img src="https://raw.githubusercontent.com/kulraj025/kulraj025/main/profile-3d-contrib/profile-night-rainbow.svg" alt="3D contribution calendar" width="100%" style="max-width:820px" />

<!-- Fallback: the plain 2D grid at /contrib works without the 3D action. -->

**Languages across public repositories** — measured by bytes written, not self-declared.

<img src="https://img.shields.io/badge/TypeScript-49.0%25-22D3EE?style=flat-square" alt="TypeScript 49.0%" />
<img src="https://img.shields.io/badge/PHP-21.3%25-2A7F9E?style=flat-square" alt="PHP 21.3%" />
<img src="https://img.shields.io/badge/Python-16.0%25-2A7F9E?style=flat-square" alt="Python 16.0%" />
<img src="https://img.shields.io/badge/CSS-5.5%25-3A4A63?style=flat-square" alt="CSS 5.5%" />
<img src="https://img.shields.io/badge/C%2B%2B-3.5%25-3A4A63?style=flat-square" alt="C++ 3.5%" />
<img src="https://img.shields.io/badge/HTML-3.4%25-3A4A63?style=flat-square" alt="HTML 3.4%" />

Plus JavaScript 1.0%, and Shell, PowerShell and Dockerfile together under 0.3%.

<!--
Optional third-party widgets. These services were unreachable when this README was last
generated, so they are left commented out rather than shipped as broken images. Paste a
line back in if the endpoint returns 200 for your account.

  GitHub stats card (deployment paused globally at time of writing):
  https://github-readme-stats.vercel.app/api?username=kulraj025&show_icons=true&hide_rank=true&hide_border=true

  Top languages (same outage):
  https://github-readme-stats.vercel.app/api/top-langs/?username=kulraj025&layout=compact&hide_border=true

  Trophy case (deployment disabled, HTTP 402):
  https://github-profile-trophy.vercel.app/?username=kulraj025&column=7&no-bg=true
-->

## 06 · Education & Current Chapter

**Dong-eui University** — B.Sc. (Hons), Intelligence Computing. 3rd year, 6th semester.

Currently training three things, in this order: **machine learning** as a discipline rather than a tutorial,
**full-stack delivery** end to end including deployment and database migrations, and **product thinking** —
deciding what not to build, which is the part my first three projects were worst at.

## 07 · Contact

Open to internships, research assistant roles, and collaborations — in Korea or remote.

[![Email](https://img.shields.io/badge/Email-Kulraj024%40gmail.com-22D3EE?style=for-the-badge&logo=gmail&logoColor=white)](mailto:Kulraj024@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-kulraj025-22D3EE?style=for-the-badge&logo=github&logoColor=white)](https://github.com/kulraj025)
[![University](https://img.shields.io/badge/Dong--eui%20University-22D3EE?style=for-the-badge)](https://eng.deu.ac.kr/eng/index.do)

Based in Busan, South Korea — **KST (UTC+9)**, so overlap with both APAC and European hours is workable.

## 08 · Footer

If you need someone who ships the first version instead of waiting for perfect conditions — email me.

<sub>Contribution graphics regenerate daily via GitHub Actions. Last content review: 26 September 2026.</sub>
