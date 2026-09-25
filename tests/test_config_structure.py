"""Tests for profile configuration structure."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "profile.yml"


def test_config_file_exists():
    assert CONFIG_PATH.exists()


def test_config_has_required_sections():
    config = yaml.safe_load(CONFIG_PATH.read_text())
    assert "profile" in config
    assert "theme" in config
    assert "social" in config


def test_config_profile_has_required_fields():
    config = yaml.safe_load(CONFIG_PATH.read_text())
    profile = config["profile"]
    assert "display_name" in profile
    assert "location" in profile
    assert "university" in profile
    assert profile["university"]["institution"]
    assert profile["university"]["website"]


def test_config_theme_has_required_colors():
    config = yaml.safe_load(CONFIG_PATH.read_text())
    theme = config["theme"]
    for key in ("background", "surface", "cyan", "violet", "white", "muted"):
        assert key in theme, f"theme.{key} missing"


def test_config_social_has_github():
    config = yaml.safe_load(CONFIG_PATH.read_text())
    social = config["social"]
    assert "github" in social
    assert "kulraj025" in social["github"]


def test_config_projects_section():
    config = yaml.safe_load(CONFIG_PATH.read_text())
    projects = config.get("projects", {})
    assert "max_featured" in projects
