# Contributing to the Profile

This repository **is** the GitHub profile for `kulraj025`. It is a small,
self-updating system:

```
GitHub repositories
      ↓  GitHub API
GitHub Actions workflow (daily)
      ↓  Python generator
Generated README.md + SVG assets
      ↓
Your profile on github.com/kulraj025
```

Everything you see is generated from **live public GitHub data** — nothing is
hardcoded and nothing is faked.

---

## 1. How the data is collected

A GitHub Actions workflow (`update-profile.yml`) runs daily (06:00 UTC),
on every push (only when `config/`, `scripts/`, `templates/`, or `tests/` change),
and manually via `workflow_dispatch`. It:

1. Fetches your public profile and repositories from the GitHub REST API.
2. Measures real per-repository language byte counts.
3. Ranks featured projects (topics → live homepages → stars → recency).
4. Regenerates local SVG assets (hero, identity card, technology constellation,
   activity dashboard, contributions, learning path, footer, project gallery).
5. Rebuilds `README.md` from the template.
6. Runs the test suite and validation checks.
7. Commits only the files that actually changed (using the built-in
   `GITHUB_TOKEN`, never a personal token).

A separate `validate-profile.yml` workflow runs on every push and PR to ensure
all SVGs are valid XML, all markers are present, and all tests pass.

A `contributions.yml` workflow refreshes the contribution heatmap weekly.

## 2. How to feature a repository

Add **one of these topics** to the repository (Repo → *About* → *Topics*):

| Topic               | Effect                                          |
|---------------------|-------------------------------------------------|
| `profile-featured`  | **Always** placed at the top of Featured Projects |
| `featured`          | Strongly considered for Featured Projects        |
| `portfolio`         | Identifies portfolio-style work                  |
| `web-app`           | Identifies web applications                      |
| `open-source`       | Identifies open-source work                      |

Repositories are ranked: `profile-featured`/`featured` topics → has a live
homepage → most stars → recently updated → non-fork → non-archived.

## 3. How to make a deployed website appear automatically

The cleanest workflow in the world — no code needed:

1. Open the project repository on GitHub → **Settings → General**.
2. Paste your live URL into the **Website** (Homepage) field:
   `https://your-site.example`
3. *(Optional but recommended)* add the `profile-featured` topic.

On the next profile refresh the project card automatically gains a
**Visit live demo** link. No editing of this repo is required.

> The Homepage field is the **only** source of truth for demo links.
> Descriptions are never scraped and URLs are never guessed, so the profile
> can never show a broken link.

## 4. How to hide a repository

Add **any** of these topics: `profile-hidden`, `hide-from-profile`,
`private-project` — or list the repo name under
`projects.hidden_repositories` in `config/profile.yml`.

## 5. How to manually trigger the workflow

- Open the **Actions** tab of this repository.
- Select **Update Profile README** or **Validate Profile**.
- Click **Run workflow → Run**.

## 6. How to customize colors and profile text

Everything editable lives in [`config/profile.yml`](config/profile.yml):

- `profile` → display name, tagline, bio, current focus, **education**,
  **university** (Dong-eui University, Busan, South Korea)
- `projects` → max featured count, forced/hidden repositories
- `social` → links (only rendered when filled and valid)
- `theme` → accent / secondary / background colors for the generated SVGs

Live GitHub facts (star counts, fork counts, languages, URLs, dates) are
**never** overridden by config.

## 7. Troubleshooting workflow failures

| Symptom                       | Likely cause / fix                                        |
|-------------------------------|-----------------------------------------------------------|
| 403 rate limit in logs        | Transient — the daily schedule retries automatically.     |
| "No changes to commit"        | Not a failure — data simply didn't change.                |
| Snake missing on profile      | Run **Generate Contribution Snake** once manually.          |
| Workflow won't push           | Check repo branch protection rules block the bot.             |
| SVG colors appear broken      | Ensure color values in `config/profile.yml` are quoted.       |
| Tests fail in CI              | Run `python -m pytest tests/` locally and fix.               |

## 8. What is never shown

- Private repositories or private activity
- Tokens, credentials or environment values
- Fake stars, followers, contributions or achievements
- Links that are missing or broken

## 9. Keeping secrets safe

- The workflow uses the repository-scoped `GITHUB_TOKEN` — no personal
  access token is ever needed or committed.
- Local runs read `GH_TOKEN`/`GITHUB_TOKEN` from the environment only.
- Never paste a personal access token into a file, issue, chat or commit.

## 10. The visual design system

The profile uses a custom **"Busan Digital Horizon"** design:

- Deep midnight-blue background with animated gradient
- Cyan ocean-wave geometry and violet digital gradients
- Animated particle systems in the hero banner
- Technology constellation with orbiting language nodes
- Compact statistic cards with real data
- All animations use SVG SMIL only — no JavaScript
- Static fallbacks for every animated element
- Respects `prefers-reduced-motion`