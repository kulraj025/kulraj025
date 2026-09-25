"""Tests for duplicate repository detection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.detect_duplicates import detect_duplicate_pairs, _pick_stronger


def _make_repo(name, size=100, stars=0, homepage=None, has_pages=False, pushed="2025-01-01T00:00:00Z"):
    return {
        "name": name, "full_name": f"kulraj025/{name}",
        "size": size, "stargazers_count": stars, "homepage": homepage,
        "has_pages": has_pages, "pushed_at": pushed,
        "forks_count": 0, "language": "Python",
        "description": "test", "html_url": f"https://github.com/kulraj025/{name}",
        "private": False, "fork": False, "archived": False, "topics": [],
    }


def test_detect_duplicate_similar_names():
    repos = [_make_repo("MyProject"), _make_repo("My-Project"), _make_repo("CompletelyDifferent")]
    pairs = detect_duplicate_pairs(repos)
    assert len(pairs) == 1
    keep, drop, _ = pairs[0]
    assert drop == "My-Project"


def test_pick_stronger_prefers_has_pages():
    a = _make_repo("a", size=50, has_pages=False)
    b = _make_repo("b", size=50, has_pages=True)
    keep, drop = _pick_stronger(a, b)
    assert keep["name"] == "b"


def test_pick_stronger_prefers_larger_size():
    a = _make_repo("a", size=100, has_pages=False)
    b = _make_repo("b", size=500, has_pages=False)
    keep, drop = _pick_stronger(a, b)
    assert keep["name"] == "b"


def test_pick_stronger_prefers_more_stars():
    a = _make_repo("a", size=100, stars=0)
    b = _make_repo("b", size=100, stars=50)
    keep, drop = _pick_stronger(a, b)
    assert keep["name"] == "b"
