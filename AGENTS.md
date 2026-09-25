# AGENTS.md

## Build & Run

```bash
# Generate the profile (fetches live GitHub data, generates SVGs, builds README)
python scripts/generate_profile.py

# Run the test suite
python -m pytest tests/ -v

# Validate the generated profile
python scripts/validate_profile.py
```

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
- `python scripts/collect_profile_data.py` — collect GitHub data (standalone)

## File Structure

```
.
├── config/profile.yml          # Theme, profile info, project config
├── templates/README.template.md  # README template with markers
├── scripts/
│   ├── github_api.py          # GitHub REST API client (cached)
│   ├── collect_profile_data.py  # Fetches user + repos + events
│   ├── analyze_languages.py   # Aggregates language data
│   ├── detect_duplicates.py   # Detects duplicate repos by name
│   ├── detect_homepages.py    # Validates homepage/demo URLs
│   ├── select_projects.py     # Ranks and selects featured projects
│   ├── generate_svg_assets.py  # All SVG generation (animated + static)
│   ├── render_readme.py       # Template rendering
│   ├── validate_profile.py    # Validation checks
│   └── generate_profile.py     # Main entry point
├── assets/
│   ├── generated/             # Animated SVG assets
│   └── static/                # Static SVG fallbacks
├── tests/                     # Test suite (7 test files, 51 tests)
└── .github/workflows/
    ├── update-profile.yml     # Daily profile refresh
    ├── validate-profile.yml   # CI validation on every push/PR
    └── contributions.yml      # Weekly contribution refresh
```

## CI Workflows

All workflows use `GITHUB_TOKEN` (never personal tokens). See
`.github/workflows/` for details.
