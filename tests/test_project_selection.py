"""Unit tests for the profile generator's selection logic.

Run with:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generate_profile import (  # noqa: E402
    detect_homepage,
    is_featured_by_topic,
    is_hidden,
    rank_projects,
)


def _repo(name, *, size=10, stars=0, homepage="", topics=None, fork=False,
          archived=False, private=False, pushed="2026-01-01T00:00:00Z",
          language="Python"):
    return {
        "name": name,
        "full_name": f"kulraj025/{name}",
        "description": f"About {name}",
        "size": size,
        "stargazers_count": stars,
        "forks_count": 0,
        "pushed_at": pushed,
        "homepage": homepage,
        "topics": topics or [],
        "fork": fork,
        "archived": archived,
        "private": private,
        "language": language,
        "html_url": f"https://github.com/kulraj025/{name}",
    }


class DetectHomepageTests(unittest.TestCase):
    def test_no_homepage(self):
        self.assertIsNone(detect_homepage(_repo("a")))

    def test_plain_url(self):
        self.assertEqual(
            detect_homepage(_repo("a", homepage="https://a.example.com")),
            "https://a.example.com",
        )

    def test_missing_scheme_is_fixed(self):
        self.assertEqual(
            detect_homepage(_repo("a", homepage="a.example.com")),
            "https://a.example.com",
        )

    def test_whitespace_is_trimmed(self):
        self.assertEqual(
            detect_homepage(_repo("a", homepage="  https://a.example.com  ")),
            "https://a.example.com",
        )


class TopicTests(unittest.TestCase):
    def test_hidden_topics(self):
        self.assertTrue(is_hidden(_repo("a", topics=["profile-hidden"])))
        self.assertTrue(is_hidden(_repo("a", topics=["hide-from-profile"])))
        self.assertTrue(is_hidden(_repo("a", topics=["private-project"])))

    def test_featured_topics(self):
        self.assertTrue(is_featured_by_topic(_repo("a", topics=["profile-featured"])))
        self.assertTrue(is_featured_by_topic(_repo("a", topics=["featured"])))


class RankProjectsTests(unittest.TestCase):
    def test_excludes_profile_repo_empty_private_hidden(self):
        repos = [
            _repo("kulraj025", size=5),
            _repo("empty", size=0),
            _repo("secret", private=True),
            _repo("hidden", topics=["profile-hidden"]),
            _repo("good"),
        ]
        picked = rank_projects(repos)
        self.assertEqual([p["name"] for p in picked], ["good"])

    def test_homepage_beats_pure_recency(self):
        repos = [
            _repo("recent", pushed="2026-06-01T00:00:00Z", stars=1),
            _repo("has-demo", pushed="2025-01-01T00:00:00Z",
                  homepage="https://demo.example.com"),
        ]
        picked = rank_projects(repos)
        self.assertEqual(picked[0]["name"], "has-demo")

    def test_stars_beat_recency(self):
        repos = [
            _repo("old-popular", stars=50, pushed="2024-01-01T00:00:00Z"),
            _repo("new-quiet", stars=1, pushed="2026-06-01T00:00:00Z"),
        ]
        picked = rank_projects(repos)
        self.assertEqual(picked[0]["name"], "old-popular")

    def test_forks_and_archived_excluded_unless_featured(self):
        repos = [
            _repo("fork", fork=True),
            _repo("archived", archived=True),
            _repo("featured-fork", fork=True, topics=["profile-featured"]),
            _repo("normal"),
        ]
        picked = [p["name"] for p in rank_projects(repos)]
        self.assertIn("featured-fork", picked)
        self.assertNotIn("fork", picked)
        self.assertNotIn("archived", picked)
        self.assertIn("normal", picked)

    def test_manual_force_featured_goes_first(self):
        repos = [_repo("a", stars=9), _repo("b", stars=1)]
        picked = rank_projects(repos, hidden=["b"])
        # b is in hidden, so it should be excluded
        self.assertEqual([p["name"] for p in picked], ["a"])

    def test_max_featured_respected(self):
        repos = [_repo(f"r{i}") for i in range(10)]
        picked = rank_projects(repos, max_featured=3)
        self.assertEqual(len(picked), 3)

    def test_empty_input(self):
        self.assertEqual(rank_projects([]), [])

    def test_only_profile_repo(self):
        self.assertEqual(rank_projects([_repo("kulraj025", size=5)]), [])


if __name__ == "__main__":
    unittest.main()