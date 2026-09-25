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


def test_template_markers_present():
    errors = validate_template_markers()
    assert len(errors) == 0, f"Template marker errors: {errors}"


def test_config_validates():
    errors = validate_config()
    assert len(errors) == 0, f"Config validation errors: {errors}"
