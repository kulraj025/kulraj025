# AGENTS.md

## What this repository is now

`README.md` is **generated** from `templates/README.template.md`,
`config/profile.yml` and the GitHub API. It is written like a product landing
page rather than a dashboard, and the *prose* is still hand-written — but it
lives in the template, not in `README.md`.

**To change the page: edit the template or the config, then run
`python3 scripts/build_readme.py`.** Never edit `README.md` by hand; the next
build overwrites it and the next `Validate Profile` push fails.

### Why a generator came back, and what is different

A generator previously ran on a daily cron and overwrote this README with
generated filler, destroying the hand-written case studies. That is why the old
rule said "do not reintroduce a step that writes README.md".

The rule's actual cause was *when* it ran, not *what* it wrote. The difference
now is structural rather than a promise:

- **There is no hand-written prose left in `README.md`.** It is a pure function
  of the template, the config and the API. The daily run re-evaluates that
  function; it cannot replace the writing, because the writing is not there.
- **The generator never touches its own inputs.** The workflow hashes
  `templates/README.template.md` and `config/profile.yml` before running and
  fails if either changed. If a scheduled run could edit the template, the whole
  argument would collapse.
- **Only two slots are computed**: `{{WORK_ROWS}}` and `{{STATS_ROWS}}`. Every
  heading, label and sentence is still written by hand in the template. Each
  slot sits inside a pair of marker comments (`BEGIN GENERATED:STATS` /
  `END GENERATED:STATS`, and the same for `WORK`) which are **published** in
  `README.md` — that is how `--check` finds the two regions again without a
  network. GitHub strips HTML comments before rendering, so they cost nothing on
  the page.
- **The changes are reviewable.** One commit, containing only the two generated
  files and the two cards, on a daily schedule.

What it buys is the conditional cases. Hand-typed, the Work section is a page
that lies the moment reality changes: a repository gains a deployment and no
Live badge appears, or one loses its demo and a dead button stays. Generated, a
Live badge is emitted only when a URL answers 200.

`validate-profile.yml` fails the push when the committed README and the template
disagree, so drift is caught in seconds rather than at the next daily run.

### Build order

```bash
python3 scripts/render_stats.py    # writes assets/{stats,langs,trophies}.svg
python3 scripts/build_readme.py    # writes README.md from the template
```

Both take `--check`, and **both checks are offline.** They make no API request,
need no token, and are deterministic. See "What `--check` does and does not
check" below — the short version is that they verify everything that is stable
and deliberately ignore the numbers, which the daily run owns.

## Build & Run

```bash
# Rebuild the cards and the page from live data (this is the real build)
python3 scripts/render_stats.py
python3 scripts/build_readme.py

# Validate the README (part of what CI runs)
python3 scripts/validate_readme.py --check-workflows

# Check for drift without writing anything
python3 scripts/render_stats.py --check
python3 scripts/build_readme.py --check

# Also audit external image availability (non-fatal; third-party outages expected)
python3 scripts/validate_readme.py --check-external

# Run the test suite
python -m pytest tests/ -v
```

`GITHUB_TOKEN` is optional but strongly recommended. The search API allows 60
requests an hour unauthenticated and a build makes about a dozen; without a
token a busy hour returns 403 and the cards render **zeros**, which is the
dangerous kind of wrong because it looks real.

## Architecture


`scripts/design.py` is the single source of truth for the canvas, type scale,
palette, motion durations and section rhythm. The SVG generators and the HTML
renderer both import it, so the two halves of a scene cannot drift apart.

`scripts/metrics.py` is the single source of truth for the **numbers**: every
GitHub call, the palette constants, the badge helpers, the demo resolution and
the derived counts. `build_readme.py` and `render_stats.py` both import it, so
a card and a piece of alt text cannot disagree about the same figure. Neither of
those two scripts knows how to talk to the API.

**Information lives in HTML; display-scale type and text-free graphics live in
SVG.** A README image is fluid, so text inside a `viewBox="0 0 1000 H"` SVG
renders at 0.89x on desktop and 0.375x on a phone. 1000 units is the canvas, so
`MIN_SVG_FONT_SIZE = 18` is the floor — below that, text is illegible on mobile.
Anything a reader must actually read is native HTML, which is crisp,
selectable and responsive. Per-project artwork contains no text at all.

The `assets/*.svg` **stat cards** are the deliberate exception: they are metric
cards, designed at their display size (460px wide) with 11–26px text, exactly
what the service they replace did. They are sized 1:1 with their `max-width` so
the scale factor is 1.0, and `render_stats.text()` refuses to emit a string that
would overflow the box it is given.

## Linting / Type Checking

No dedicated linter or type-checker is configured. The codebase uses Python 3.12+
with `from __future__ import annotations` in all modules.

## Testing

- Framework: `pytest`
- Install: `pip install -r requirements.txt` (includes `pytest`)
- Run: `python -m pytest tests/ -v`
- The test suite validates SVG XML structure, template rendering, config
  structure, project selection logic, and duplicate detection.

## Commands

- `python scripts/generate_profile.py` — full generation pipeline
- `python scripts/validate_profile.py` — validate generated output
- `python scripts/qa_layout.py` — SVG geometry/contrast QA (in-bounds, collisions, AA, type scale, motion budget)
- `python scripts/qa_structure.py` — README HTML nesting QA (in-bounds structure, image srcs, alt text)
- `python scripts/qa_render.py` — raster QA via `rsvg-convert` (ink coverage, dead bands)
- `python scripts/preview_server.py` — serve a browser-accurate preview of the rendered README
- `python scripts/collect_profile_data.py` — collect GitHub data (standalone)

## Layout invariants

`scripts/qa_layout.py`, `scripts/qa_structure.py` and `scripts/qa_render.py` are
enforced in CI and must stay clean.

**SVG generators** (`scripts/generate_svg_assets.py`):

- **No text may exceed its container.** Use `fit_text()` to wrap/truncate;
  do not hand-slice strings.
- **Text must clear other text.** Captions sit at least 16px above the element
  they label.
- **Contrast must pass WCAG AA.** GitHub's language colours are tuned for a
  light background; pass them through `ensure_contrast(color, bg, 4.5)`
  rather than using them raw.
- **Shapes must stay on canvas.** Derive radii from the available half-extents;
  never hardcode a pixel radius.
- **No scene may have a dead band.** `qa_render.py` fails any scene whose
  longest empty row or column run exceeds 30% of its height or width. If you
  grow a canvas, fill the new area — do not leave it as bare gradient.
- **Motion is budgeted.** `MAX_ANIMATIONS_PER_ASSET = 40`. Batch repeated
  elements (particles, contours) into a few opacity-animated groups rather than
  one animation per element.
- Animated and static variants share one `_build_*` implementation with an
  `animated` flag. Do not fork them into two copies — that is how the two
  drifted apart previously.

**README HTML** (`scripts/render_readme.py`):

- **The markup must survive a browser.** GitHub sanitizes and then renders;
  invalid nesting is silently reflowed, not reported. A `<tr>` emitted outside
  a `<table>` loses its intended layout with nothing logged.
  `qa_structure.py` catches this class of bug.
- **No block element inside `<p>`.** The browser closes the outer `<p>` early.
- **Only inline `style` survives.** GitHub's sanitizer strips `<style>` blocks.
- **No tiny metadata.** `HTML_META` (12px) is for short labels only; anything a
  reader must read is `HTML_BODY` (14px) or larger. If information cannot be
  displayed readably, remove it rather than shrinking it.
- **State each fact once.** Repeating the same value in two sections reads as
  dashboard chrome.
- **The hero must stay the dominant scene** and carry the largest type on the
  page by a wide margin.

## File Structure

```
.
├── config/profile.yml          # Identity, education, social, and the featured projects
├── templates/README.template.md  # Canonical README source, {{FIELD}} slots + field map
├── assets/                     # Everything the README loads as an image
│   ├── banner.svg              # Hero banner, 1100x220, textLength-pinned
│   ├── typing.svg              # 3 stacked animated lines, replaces readme-typing-svg
│   ├── stats.svg               # Generated metric card: commits, stars, PRs, issues, repos
│   ├── langs.svg               # Generated language card, weighted by measured bytes
│   ├── trophies.svg            # Generated award card; the row is dropped when empty
│   ├── generated/              # Legacy animated SVG assets (+ project-art/)
│   └── static/                 # Legacy static SVG fallbacks
├── scripts/
│   ├── design.py               # Source of truth: canvas, type scale, palette, motion
│   ├── metrics.py              # Source of truth: every API call, count and badge helper
│   ├── github_api.py           # GitHub REST API client (cached, with a TTL)
│   ├── build_readme.py         # Renders README.md from the template + live data
│   ├── render_stats.py         # Renders assets/{stats,langs,trophies}.svg
│   ├── collect_profile_data.py # Fetches user + repos + events
│   ├── analyze_languages.py    # Aggregates language data
│   ├── detect_duplicates.py    # Detects duplicate repos by name
│   ├── detect_homepages.py     # Validates homepage/demo URLs
│   ├── select_projects.py      # Ranks and selects featured projects
│   ├── generate_svg_assets.py  # All SVG generation (animated + static)
│   ├── render_readme.py        # Legacy HTML README renderer (unused for README.md)
│   ├── generate_profile.py     # Legacy asset regeneration; does NOT write README.md
│   ├── validate_readme.py      # Validates README.md structure (run in CI)
│   ├── check_svg_text_fits.py  # Rasterises hero text, measures ink margins
│   ├── validate_profile.py     # Legacy validation for the SVG pipeline
│   ├── qa_layout.py            # SVG geometry/contrast/type/motion QA
│   ├── qa_structure.py         # README HTML structure QA
│   ├── qa_render.py            # Raster/pixel QA
│   ├── png_decode.py           # stdlib zlib PNG decoder used by qa_render
│   └── preview_server.py       # Local browser preview
├── tests/                      # Test suite
│   ├── test_hero_svgs.py       # Crop, SMIL and light-theme guards for the hero
│   └── test_generated_sections.py  # Stats/Now/Work invariants, incl. the conditional Live badge
└── .github/workflows/
    ├── validate-profile.yml    # README validation + offline drift checks (blocking)
    └── profile-widgets.yml     # Snake, 3D calendar, stat cards, README (daily)
```

## Testing conventions

**Tests in `tests/` are offline, and so is `--check`.** A test that calls the
GitHub API fails on a rate limit or a network blip, and a test that fails for
reasons unrelated to the code teaches everyone to ignore it. Both `--check`
modes were moved off the network for the same reason — see below. Nothing in
`tests/` or in the push-time CI step makes a request, so nothing in either can
be red for a reason that is not about the code.

**A CI-reachable check must be stdlib-only.** This is not theoretical: the hero
crop test passed locally and failed in CI because it shelled out to ImageMagick,
which is not installed on the runner. It now uses the stdlib PNG decoder in
`scripts/png_decode.py`, and the workflow installs `librsvg2-bin` where a
rasteriser is genuinely required.

## CI Workflows

Both use `GITHUB_TOKEN` (never personal tokens). See `.github/workflows/` for details.

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `validate-profile.yml` | push to `main`, daily, manual | README structure, **offline drift checks**, pytest. **Must stay green.** |
| `profile-widgets.yml` | daily 01:17 UTC, manual, first push | Platane/snk → snake on the `output` branch; yoshi389111 → 3D calendar on `main`; `render_stats.py` + `build_readme.py` → the cards and the README on `main`. |

### Removed, and why

- **`update-profile.yml`** — regenerated `README.md` from the SVG generator on a
  daily schedule, overwriting hand-written case studies within 24 hours. Its role
  is now filled by `build_readme.py` in `profile-widgets.yml`, which is safe for
  the structural reason described at the top of this file, and which asserts that
  it did not modify the template or the config.
- **`contributions.yml`** — referenced `build_contributions_static()`, which was
  deleted when the fake contribution grid was removed. It was already failing.
- **`generate-snake.yml`** — superseded by `profile-widgets.yml`, and it published to
  `assets/generated/` on `main`, which nothing referenced.

### Widget availability

Third-party README widget services go down, and several were down when this
README was written. Re-check with `validate_readme.py --check-external` before
adding any new one, and give it a `<!-- Fallback: ... -->` comment when you do.

| Service | State | Decision |
| --- | --- | --- |
| `streak-stats.demolab.com` | 200 | used — the one third-party card still serving |
| `img.shields.io` | 200 | badges |
| `skillicons.dev` | 200 | capability icons |
| `opengraph.githubassets.com` | 200 | project preview images |
| `github-readme-stats.vercel.app` | **503 `DEPLOYMENT_PAUSED`** | replaced by a local `assets/stats.svg`. Fails for `torvalds` too, so it is not this repository's problem to fix |
| `github-profile-trophy.vercel.app` | **402 `DEPLOYMENT_DISABLED`** | replaced by a local `assets/trophies.svg` |
| `github-readme-stats-eight-theta.vercel.app` | 200 | **not used.** It works, but it is a stranger's deployment: the profile's first screenful would fail whenever their account or quota did |
| `lowlighter.io` | **DNS does not resolve** | not embedded |
| `readme-typing-svg.demolab.com` | 200, but **unusable** | removed — see below |

**Never embed a third-party image that does not return 200.** A broken image with
alt text still reads as a broken page.

**Prefer a local card over a working mirror.** The stats and language cards are
rendered by `scripts/render_stats.py` into `assets/` and committed, for the same
reason `banner.svg` and `typing.svg` are: the alternative was a dependency this
repository does not control. They are refreshed by the daily widgets run and
checked for drift on every push.

#### Trophy rules

`assets/trophies.svg` restates the published `github-profile-trophy` thresholds
in `render_stats.TROPHY_RULES` rather than calling the service, and **draws an
award only when the measured count clears its threshold**. `build_readme.py`
imports the same `earned_trophies()` to decide whether to emit the row, so the
card and the page cannot disagree. An empty card is never shown: as of writing,
6 stars is below the 16 that "Star Gazer" needs, so the row is absent.

The PR counters go through the **issues** search index, not the commits one.
`search/commits?q=author:X is:pr is:merged` does not error — the commits index
does not understand `is:pr`, ignores it, and returns every commit by that
author. That is how a profile with zero pull requests briefly rendered a
"Pull Shark" trophy next to a stats card reading "0 pull requests".
`tests/test_generated_sections.py` asserts no award is ever granted below its
own threshold.

#### Why the typing SVG is ours and not readme-typing-svg

The service is up, but it cannot render stacked lines. Every entry in `lines` is
joined with commas into **one** `<textPath>`, and `text-anchor='middle'` anchors
that run at the path origin — so a three-line request puts most of the string
off-canvas. The published page rendered a heading reading
`ilding campus products and XAI`. `multiline=true` is ignored by the deployed
version. `assets/typing.svg` is hand-built instead.

`assets/banner.svg` and `assets/typing.svg` therefore pin every `<text>` with
`textLength`, which fixes each run's advance width regardless of which font the
viewer has, making clipping structurally impossible. `scripts/check_svg_text_fits.py`
rasterises the text layer and measures the real ink margins; `tests/test_hero_svgs.py`
fails the build if a glyph could crop or if the SMIL `keyTimes` are invalid
(Chrome silently discards an `<animate>` whose `keyTimes` do not run 0→1).

Both files carry their own dark background. Cyan text on transparency is
invisible in GitHub's **light** theme, and a banner cannot assume the reader
chose dark.

#### Card theme

The cards use the `tokyonight` palette, not the brief's `transparent`.
`transparent` renders text in `#E4E2E2`: correct on dark, invisible on light.
Every card carries its own dark background for the same reason, and
`validate_readme.py` fails the build if one does not.

The old remote card used `hide=stars,prs,issues`. That was reversed: suppressing
the three least flattering columns reads as selective reporting, not modesty. The
local card shows commits, stars, pull requests, issues and repositories. Values
sit at **26px**, deliberately under the validator's 32px display-size threshold
— a student profile should not magnify a star count of six, but it should not
hide the column either.

Follower, star and fork counts must never be rendered in display type.

#### The API cache has a TTL

`GitHubAPI.get_json` caches into `.cache/`, and the TTL is 30 minutes
(`CACHE_TTL_SECONDS`). Without one the cache was permanent: the repository
listing had been captured before two featured repositories existed, so a build
on a machine with an old cache reported a project as "not in the account" and
refused to build. Worse, a stats card rendered from a months-old listing shows
a plausible but wrong number, which is the failure mode nobody notices.


There is exactly **one** cache root, `CACHE_DIR`, and `__init__` creates the same
directory `_cache_path()` writes to. These were two separate expressions for one
path — `__init__` made `scripts/.cache` while `_cache_path()` wrote to
`<repo root>/.cache` — so the first write on a fresh clone raised
`FileNotFoundError`. It only ever worked because `.cache/` was committed to git,
which is to say because an accident was hiding a bug. Untracking `.cache/`
exposed it immediately, in CI, on the step that had just been added.

#### What `--check` does, and what it deliberately does not do

Both checks used to re-render from the API and compare byte for byte. They were
**red on nearly every run**, for reasons that had nothing to do with the code:

- GitHub's **commit-search index lags the repository**. The card read 37 commits
  while the repository had 40, and the gap closed minutes later.
- **Linguist re-analyses asynchronously** after a push, so `langs.svg` changed
  between two runs minutes apart — TypeScript went 45.1% to 47.8% and C++ entered
  the top six, with no code change at all.
- The API can simply return a **stale response for one repository** on one call.
  Two cold runs of the same commit, minutes apart, produced different
  `langs.svg` files; a third matched the first.

A check that is red for reasons unrelated to the code is worse than no check,
because the only rational response to a permanently-red CI is to stop reading it.
So each check now verifies what is actually stable, and the daily run in
`profile-widgets.yml` — the only thing that makes a request — owns the numbers.

`build_readme.py --check` re-renders the template with the two generated regions
taken from the committed file, then compares the rest. Offline and
deterministic, and it still catches every real fault: a hand-edited `README.md`,
a template edited without rebuilding, a changed config value, an unfilled slot.
It reports the first differing line rather than only naming the file.

`render_stats.py --check` is structural: each card parses, carries an opaque
background of its own full size, has a title, holds no placeholder text, has
shares that descend and sum to 100 within display rounding, and **agrees with
the README alt text describing it** — the one cross-file invariant, and the one
that catches a hand-edited card.

**If you need to know whether a number is current, run the build.** That is what
the daily job does.

#### Two bugs that a green CI did not catch

Both were found by hand, after CI had been green, and both are now pinned by
tests.

**The documentation comment was pasted into the page.** `HEADER_RE` was
`\A\s*<!--.*?-->`, lazy, so it ended at the *first* closing marker anywhere in
the file. Documenting the new generated regions meant writing a complete marker
comment in the header, which moved that first marker about 130 lines earlier. The
field map below it fell into the page body, and its own `{{STATS_ROWS}}` was
then replaced with live `<tr>` markup. Nothing went red: the page rendered,
every slot reported as filled, the tests passed, CI was green, and the README was
21KB instead of 8KB with build internals printed across it. `HEADER_RE` now
requires both delimiters to be alone on their lines, and a generated slot must
appear **exactly once** in the body — a second occurrence is the field map.

**Tied languages swapped places between runs.** `sorted(key=bytes, reverse=True)`
leaves ties in dict-insertion order, which follows the order the repository
listing happened to come back in. HTML and JavaScript are both at 3.3% here, and
they did swap — so the card and the README alt text disagreed, because they are
rendered by two separate calls that each got a different insertion order. Every
ranking is now `sorted(key=lambda kv: (-kv[1], kv[0]))`: bytes first,
alphabetical for ties, identical every time.

The lesson in both cases is the same. A test that cannot fail, and a check that
is red for the wrong reason, are equally useless — one hides the bug, the other
teaches you to ignore the signal. Prefer a check that is narrow, offline,
deterministic, and demonstrably red when it should be.
