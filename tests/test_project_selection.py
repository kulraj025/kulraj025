"""Tests for project selection logic."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.select_projects import select_projects, is_excluded, score_repo


SAMPLE_REPOS = [
    {"name": "awesome-project", "full_name": "kulraj025/awesome-project",
      "private": False, "size": 500, "fork": False, "archived": False,
      "topics": ["featured"], "stargazers_count": 10,
      "pushed_at": "2025-09-01T00:00:00Z",
      "description": "A great project", "language": "Python",
      "html_url": "https://github.com/kulraj025/awesome-project",
      "has_pages": True, "homepage": None},
    {"name": "fork-repo", "full_name": "kulraj025/fork-repo",
      "private": False, "size": 100, "fork": True, "archived": False,
      "topics": [], "stargazers_count": 0,
      "pushed_at": "2024-01-01T00:00:00Z",
      "description": "A fork", "language": "Python",
      "html_url": "https://github.com/kulraj025/fork-repo",
      "has_pages": False, "homepage": None},
    {"name": "empty-repo", "full_name": "kulraj025/empty-repo",
      "private": False, "size": 0, "fork": False, "archived": False,
      "topics": [], "stargazers_count": 0,
      "pushed_at": "2024-01-01T00:00:00Z",
      "description": "", "language": "Python",
      "html_url": "https://github.com/kulraj025/empty-repo",
      "has_pages": False, "homepage": None},
    {"name": "scratch-test", "full_name": "kulraj025/scratch-test",
      "private": False, "size": 50, "fork": False, "archived": False,
      "topics": [], "stargazers_count": 0,
      "pushed_at": "2024-01-01T00:00:00Z",
      "description": "test scratch work", "language": "Python",
      "html_url": "https://github.com/kulraj025/scratch-test",
      "has_pages": False, "homepage": None},
    {"name": "archived-repo", "full_name": "kulraj025/archived-repo",
      "private": False, "size": 300, "fork": False, "archived": True,
      "topics": [], "stargazers_count": 0,
      "pushed_at": "2023-01-01T00:00:00Z",
      "description": "old stuff", "language": "Python",
      "html_url": "https://github.com/kulraj025/archived-repo",
      "has_pages": False, "homepage": None},
    {"name": "kulraj025", "full_name": "kulraj025/kulraj025",
      "private": False, "size": 100, "fork": False, "archived": False,
      "topics": ["profile"], "stargazers_count": 0,
      "pushed_at": "2025-09-01T00:00:00Z",
      "description": "My profile", "language": "Markdown",
      "html_url": "https://github.com/kulraj025/kulraj025",
      "has_pages": False, "homepage": None},
]


def test_is_excluded_fork():
    assert is_excluded(SAMPLE_REPOS[1]) is True


def test_is_excluded_empty():
    assert is_excluded(SAMPLE_REPOS[2]) is True


def test_is_excluded_archived():
    assert is_excluded(SAMPLE_REPOS[4]) is True


def test_is_excluded_profile_repo():
    assert is_excluded(SAMPLE_REPOS[5]) is True


def test_is_excluded_valid():
    assert is_excluded(SAMPLE_REPOS[0]) is False


def test_select_projects_filters():
    selected, _ = select_projects(SAMPLE_REPOS, max_featured=6, api=None)
    names = [p["name"] for p in selected]
    assert "awesome-project" in names
    assert "fork-repo" not in names
    assert "empty-repo" not in names
    assert "archived-repo" not in names
    assert "kulraj025" not in names


def test_select_projects_max_limit():
    selected, _ = select_projects(SAMPLE_REPOS, max_featured=2, api=None)
    assert len(selected) <= 2


def test_score_repo_prioritizes_featured():
    repo_featured = SAMPLE_REPOS[0]
    repo_normal = {"name": "x", "full_name": "kulraj025/x",
      "private": False, "size": 500, "fork": False, "archived": False,
      "topics": [], "stargazers_count": 10,
      "pushed_at": "2025-09-01T00:00:00Z",
      "description": "test", "language": "Python",
      "html_url": "https://github.com/kulraj025/x",
      "has_pages": True, "homepage": None, "forks_count": 0}
    score_featured = score_repo(repo_featured)
    score_normal = score_repo(repo_normal)
    assert score_featured > score_normal
