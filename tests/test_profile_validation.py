"""Tests for profile validation."""
import sys
import py_compile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.validate_profile import (
    validate_files_exist, validate_svg_assets, validate_template_markers,
    validate_config,
)


def test_all_scripts_compile():
    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    for f in scripts_dir.glob("*.py"):
        py_compile.compile(f, doraise=True)


def test_required_files_exist():
    errors = validate_files_exist()
    for err in errors:
        if "scripts/" in err:
            assert False, f"Missing script file: {err}"


def test_svg_assets_valid():
    errors = validate_svg_assets()
    assert len(errors) == 0, f"SVG validation errors: {errors}"


def test_template_fields_are_all_documented():
    """Every {{FIELD}} used in the template body must appear in the field map.

    Replaces the old scene-marker check. The README is hand-maintained now, so the
    contract is not "6 markers exist" but "no field is used without a documented
    source", which is what stops a stale number being pasted in.
    """
    import re

    template = (Path(__file__).resolve().parent.parent
                / "templates" / "README.template.md").read_text(encoding="utf-8")

    # The field map is the leading documentation comment.
    header = re.match(r"<!--.*?-->", template, re.S)
    assert header, "template must start with a documentation comment"
    body = template[header.end():]

    field_map = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", header.group(0)))
    used = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", body))

    # A documented field may be a family written once, e.g. {{FEATURED_N_URL}}
    # stands for FEATURED_1_URL..FEATURED_3_URL. Expand those so the map documents
    # the family instead of repeating every member.
    import re as _re

    def documented(field: str) -> bool:
        # _N_ is a wildcard for the project number, so it must keep its underscores:
        # FEATURED_N_URL -> FEATURED_[0-9]+_URL, not FEATURED[0-9]+URL.
        return any(
            _re.fullmatch(pat.replace("_N_", "_[0-9]+_"), field) for pat in field_map
        )

    undocumented = {f for f in used - field_map if not documented(f)}
    assert not undocumented, f"undocumented template fields: {sorted(undocumented)}"
    assert used, "template should use at least one field"


def test_template_braces_are_balanced():
    import re

    template = (Path(__file__).resolve().parent.parent
                / "templates" / "README.template.md").read_text(encoding="utf-8")
    assert template.count("{{") == template.count("}}"), "unbalanced {{ }} in template"
    assert not re.search(r"\{\{\s*\}\}", template), "empty field placeholder"


def test_readme_has_no_unfilled_fields():
    """README.md is the template with fields filled in, so none may remain."""
    import re

    readme = (Path(__file__).resolve().parent.parent
              / "README.md").read_text(encoding="utf-8")
    leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", readme)
    assert not leftover, f"unfilled fields left in README.md: {sorted(set(leftover))}"


def test_config_validates():
    errors = validate_config()
    assert len(errors) == 0, f"Config validation errors: {errors}"
