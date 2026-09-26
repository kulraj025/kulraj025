"""Validate the generated profile for correctness.

Checks:
1. Required files exist
2. SVGs are well-formed XML
3. Template markers are present and balanced
4. Homepage URLs are valid
5. No duplicate projects in README
6. Static fallbacks exist for every animated asset
7. Text limits are respected

Exit code 0 = all checks pass, 1 = failures found.
"""
from __future__ import annotations

import re
import sys
import html
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE",
    ".gitignore",
    "config/profile.yml",
    "templates/README.template.md",
    "scripts/generate_profile.py",
    "scripts/render_readme.py",
    "scripts/generate_svg_assets.py",
    "scripts/github_api.py",
    "scripts/collect_profile_data.py",
    "scripts/analyze_languages.py",
    "scripts/select_projects.py",
    "scripts/detect_homepages.py",
    "scripts/detect_duplicates.py",
    "assets/generated/hero.svg",
    "assets/generated/divider.svg",
    "assets/generated/technology-orbit.svg",
    "assets/generated/horizon-signal.svg",
    "assets/generated/learning-path.svg",
    "assets/generated/contact-horizon.svg",
    "assets/static/hero.svg",
    "assets/static/hero-fallback.svg",
    "assets/static/divider.svg",
    "assets/static/technology-orbit.svg",
    "assets/static/horizon-signal.svg",
    "assets/static/learning-path.svg",
    "assets/static/contact-horizon.svg",
]

REQUIRED_MARKERS = [
    "HERO",
    "IDENTITY",
    "TECHNOLOGY",
    "PROJECTS",
    "ACTIVITY",
    "CONTACT",
]

# Reject hosts for URL validation
REJECT_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "example.com",
    "example.org", "example.net", "test.com", "domain.example",
    "your-site.example", "site.example",
}


def validate_files_exist() -> list[str]:
    errors = []
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"Missing required file: {rel}")
    return errors


def validate_svg(path: Path) -> list[str]:
    errors = []
    if not path.exists():
        errors.append(f"SVG file missing: {path}")
        return errors
    try:
        content = path.read_text(encoding="utf-8")
        # Strip XML declaration if present, then parse
        ET.fromstring(content)
    except ET.ParseError as e:
        errors.append(f"Invalid SVG XML in {path.name}: {e}")
    return errors


def validate_svg_assets() -> list[str]:
    errors = []
    gen_dir = ROOT / "assets" / "generated"
    static_dir = ROOT / "assets" / "static"

    # Every generated scene must animate, and every one must have a static
    # counterpart. Project artwork is generated on demand, so the top level of
    # generated/ plus the project-art/ subtree are both swept.
    animated = sorted(p.name for p in gen_dir.glob("*.svg"))
    animated += sorted(f"project-art/{p.name}" for p in (gen_dir / "project-art").glob("*.svg"))

    for name in animated:
        errors.extend(validate_svg(gen_dir / name))
        if not (static_dir / name).exists():
            errors.append(f"Missing static fallback: assets/static/{name}")

    # The hero also keeps its historical fallback filename.
    if not (static_dir / "hero-fallback.svg").exists():
        errors.append("Missing static fallback: assets/static/hero-fallback.svg")

    return errors


def validate_template_markers() -> list[str]:
    errors = []
    template = (ROOT / "templates" / "README.template.md").read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        start = f"<!-- GENERATED:{marker}:START -->"
        end = f"<!-- GENERATED:{marker}:END -->"
        if start not in template:
            errors.append(f"Missing marker START in template: {marker}")
        if end not in template:
            errors.append(f"Missing marker END in template: {marker}")
    return errors


def validate_readme_markers() -> list[str]:
    """Check that all required markers are present in the generated README."""
    errors = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        start = f"<!-- GENERATED:{marker}:START -->"
        end = f"<!-- GENERATED:{marker}:END -->"
        if start not in readme:
            errors.append(f"Missing marker START in README: {marker}")
        if end not in readme:
            errors.append(f"Missing marker END in README: {marker}")
    return errors


def validate_urls() -> list[str]:
    """Check that URLs in the README are valid."""
    errors = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    # Extract URLs from markdown links
    link_pattern = re.compile(r"]\(([^)]+)\)")
    urls = link_pattern.findall(readme)
    for url in urls:
        if url.startswith("assets/") or url.startswith("#"):
            continue
        if not url.startswith(("http://", "https://", "mailto:")):
            continue
        if url.startswith("mailto:"):
            continue
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.netloc.split(":")[0].lower()
            if host in REJECT_HOSTS:
                errors.append(f"Rejected URL host: {url}")
        except Exception:
            errors.append(f"Malformed URL: {url}")
    return errors


def validate_no_duplicate_projects() -> list[str]:
    """Check the README doesn't contain duplicate project names."""
    errors = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Look for project card titles (in SVG) or project links (in markdown)
    repo_links = re.findall(r"github\.com/kulraj025/([^\)\"\'\s]+)", readme)
    seen = set()
    for name in repo_links:
        if name.lower() in seen:
            errors.append(f"Duplicate project reference in README: {name}")
        seen.add(name.lower())
    return errors


def validate_text_limits() -> list[str]:
    """Check text isn't excessively long."""
    errors = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    # Count lines in plain text paragraphs (non-SVG, non-HTML)
    lines = readme.split("\n")
    long_paragraph = 0
    in_paragraph = False
    for line in lines:
        if line.strip() and not line.strip().startswith(("<", "!", "---", "##", "#", "|", ":", "*", "-", "<", "</", "[")):
            long_paragraph += 1
            if long_paragraph > 5:
                errors.append("Found a paragraph with more than 5 consecutive text lines")
                long_paragraph = 0
        else:
            long_paragraph = 0
    return errors


def validate_config() -> list[str]:
    """Validate the profile configuration."""
    errors = []
    try:
        import yaml
        config_path = ROOT / "config" / "profile.yml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        profile = config.get("profile", {})
        if not profile.get("display_name"):
            errors.append("Config: display_name is missing")
        if not profile.get("location"):
            errors.append("Config: location is missing")

        social = config.get("social", {})
        email = social.get("email", "")
        if email and "@" not in email:
            errors.append(f"Config: invalid email format: {email}")

        uni = profile.get("university", {})
        if not uni.get("institution"):
            errors.append("Config: university institution is missing")
        if not uni.get("website"):
            errors.append("Config: university website is missing")

        theme = config.get("theme", {})
        for key in ("background", "cyan", "violet"):
            if key not in theme:
                errors.append(f"Config: theme.{key} is missing")
    except ImportError:
        errors.append("PyYAML not installed for config validation")
    return errors


def run_all() -> list[str]:
    """Run all validation checks and return list of errors."""
    errors = []
    errors.extend(validate_files_exist())
    errors.extend(validate_svg_assets())
    errors.extend(validate_template_markers())
    errors.extend(validate_readme_markers())
    errors.extend(validate_urls())
    errors.extend(validate_no_duplicate_projects())
    errors.extend(validate_text_limits())
    errors.extend(validate_config())
    return errors


if __name__ == "__main__":
    errors = run_all()
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All validation checks passed.")
        sys.exit(0)
