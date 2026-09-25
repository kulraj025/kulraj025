"""Tests for homepage detection logic."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.detect_homepages import detect_homepage, _normalize_url, _is_valid_url


def test_normalize_github_url():
    url = _normalize_url("https://kulraj025.github.io/repo/")
    assert url == "https://kulraj025.github.io/repo"


def test_normalize_strips_trailing_slash():
    url = _normalize_url("https://example.com/")
    assert not url.endswith("/")


def test_is_valid_url_rejects_empty():
    assert _is_valid_url("") is False


def test_is_valid_url_rejects_whitespace():
    assert _is_valid_url("   ") is False


def test_is_valid_url_accepts_http():
    assert _is_valid_url("https://validsite.com") is True


def test_detect_homepage_with_url():
    repo = {"homepage": "https://validsite.com", "html_url": "https://github.com/kulraj025/repo"}
    result = detect_homepage(repo)
    assert result == "https://validsite.com"


def test_detect_homepage_no_url():
    repo = {"homepage": None, "html_url": "https://github.com/kulraj025/repo"}
    result = detect_homepage(repo)
    assert result is None or "github.io" in str(result)


def test_detect_homepage_with_pages():
    from scripts.detect_homepages import detect_github_pages
    repo = {"homepage": None, "html_url": "https://github.com/kulraj025/repo",
            "has_pages": True, "owner": {"login": "kulraj025"}, "name": "repo"}
    result = detect_github_pages(repo)
    assert "github.io" in str(result)
