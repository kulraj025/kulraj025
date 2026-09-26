# AGENTS.md

## Build & Run

```bash
# Generate the profile (fetches live GitHub data, generates SVGs, builds README)
python scripts/generate_profile.py

# Run the test suite
python -m pytest tests/ -v

# Validate the generated profile
python scripts/validate_profile.py

# Geometric layout QA (bounds, text collisions, WCAG contrast, type scale)
python scripts/qa_layout.py

# README structure QA (valid HTML nesting, image srcs, alt text)
python scripts/qa_structure.py

# Raster QA (ink coverage, dead bands, full-bleed scenes)
python scripts/qa_render.py

# Preview the rendered README in a browser
python scripts/preview_server.py   # then open http://127.0.0.1:8766/preview1012.html
```

## Architecture

`scripts/design.py` is the single source of truth for the canvas, type scale,
palette, motion durations and section rhythm. The SVG generators and the HTML
renderer both import it, so the two halves of a scene cannot drift apart.

**Information lives in HTML; display-scale type and text-free graphics live in
SVG.** A README image is fluid, so text inside a `viewBox="0 0 1000 H"` SVG
renders at 0.89x on desktop and 0.375x on a phone. 1000 units is the canvas, so
`MIN_SVG_FONT_SIZE = 18` is the floor — below that, text is illegible on mobile.
Anything a reader must actually read is native HTML, which is crisp,
selectable and responsive. Per-project artwork contains no text at all.

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
├── config/profile.yml          # Identity, education, social, project config
├── templates/README.template.md  # README template with 6 scene markers
├── scripts/
│   ├── design.py               # Source of truth: canvas, type scale, palette, motion
│   ├── github_api.py           # GitHub REST API client (cached)
│   ├── collect_profile_data.py # Fetches user + repos + events
│   ├── analyze_languages.py    # Aggregates language data
│   ├── detect_duplicates.py    # Detects duplicate repos by name
│   ├── detect_homepages.py     # Validates homepage/demo URLs
│   ├── select_projects.py      # Ranks and selects featured projects
│   ├── generate_svg_assets.py  # All SVG generation (animated + static)
│   ├── render_readme.py        # Native-HTML README rendering
│   ├── generate_profile.py     # Main entry point
│   ├── validate_profile.py     # Required files, markers, static fallbacks
│   ├── qa_layout.py            # SVG geometry/contrast/type/motion QA
│   ├── qa_structure.py         # README HTML structure QA
│   ├── qa_render.py            # Raster/pixel QA
│   └── preview_server.py       # Local browser preview
├── assets/
│   ├── generated/              # Animated SVG assets (+ project-art/)
│   └── static/                 # Static SVG fallbacks (one per generated asset)
├── tests/                      # Test suite
└── .github/workflows/
    ├── update-profile.yml      # Daily profile refresh
    ├── validate-profile.yml    # CI validation on every push/PR
    └── contributions.yml       # Weekly contribution refresh
```

## CI Workflows

All workflows use `GITHUB_TOKEN` (never personal tokens). See
`.github/workflows/` for details.
