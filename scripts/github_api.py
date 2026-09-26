"""Caching GitHub REST API client for the profile generator.

Reads from environment GH_TOKEN / GITHUB_TOKEN. Never commits tokens.
Caches responses under scripts/.cache/ for offline runs.
Retries 5xx with exponential backoff; handles 403 gracefully.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

# One cache root, and it must be the same one that gets created. These were two
# different directories: __init__ created scripts/.cache while _cache_path()
# wrote to <repo root>/.cache, so the first write on a fresh clone raised
# FileNotFoundError. It only ever worked because .cache/ was committed to git,
# which is to say because a bug was hiding inside an accident. The repository
# root is the right home for it -- it is what .gitignore names, and what the
# README-adjacent tooling expects to find.
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
USER_AGENT = "kulraj025-profile-generator"
API_ROOT = "https://api.github.com"
# How long a cached response stays usable. Short enough that a rebuild picks up
# a new repository or a new star, long enough that one build does not re-request
# the same listing for every card.
CACHE_TTL_SECONDS = 1800


class GitHubAPIError(RuntimeError):
    pass


def _env_token() -> str:
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""


class GitHubAPI:
    def __init__(self, cache_dir: Path | None = None) -> None:
        # None rather than `cache_dir: Path = CACHE_DIR`, so the default is
        # resolved here and cannot disagree with _cache_path(). The argument is
        # only used by tests that want an isolated cache.
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.token = _env_token()

    def _headers(self) -> dict[str, str]:
        hdrs = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            hdrs["Authorization"] = f"Bearer {self.token}"
        return hdrs

    @staticmethod
    def _cache_path(url: str) -> Path:
        safe = url.replace("https://", "").replace("?", "_").replace("&", "_").replace("/", "_")
        # Uses CACHE_DIR rather than recomputing the path. Recomputing is what
        # let the two drift apart in the first place: two expressions for one
        # directory, and only one of them was ever created.
        return CACHE_DIR / f"{safe}.json"

    def _cache_fresh(self, cache_path: Path) -> bool:
        """A cache entry is usable only if it exists and is younger than the TTL.

        Older than that, or unreadable, and it is refetched rather than trusted.
        """
        if not cache_path.exists():
            return False
        age = time.time() - cache_path.stat().st_mtime
        return age < CACHE_TTL_SECONDS

    def get_json(self, url: str, use_cache: bool = True, max_retries: int = 4) -> object:
        cache_path = self._cache_path(url)
        # The cache expires. Without a TTL it is permanent: the repository
        # listing in .cache/ was captured before two featured repositories
        # existed, so a fresh clone on a machine with an old cache reported a
        # project as "not in the account" and refused to build. Worse, a stats
        # card rendered from a months-old listing would show a plausible but
        # wrong number, which is the failure mode that cannot be noticed.
        if use_cache and self._cache_fresh(cache_path):
            return json.loads(cache_path.read_text())

        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers=self._headers())
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if use_cache:
                        cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    return data
            except urllib.error.HTTPError as exc:
                if exc.code in (500, 502, 503, 504):
                    time.sleep(2 ** attempt)
                    continue
                if exc.code == 403:
                    body = ""
                    try:
                        body = (exc.read().decode("utf-8", "replace") or "")[:300]
                    except Exception:
                        pass
                    raise GitHubAPIError(f"GitHub API 403: {body or exc.reason}") from exc
                if exc.code == 404:
                    return None
                raise GitHubAPIError(f"HTTP {exc.code} for {url}") from exc
        raise GitHubAPIError(f"Unreachable after {max_retries} retries: {url}")

    def head(self, url: str, max_retries: int = 2) -> int | None:
        """Return HTTP status code for a URL without downloading a body."""
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, method="HEAD", headers=self._headers())
                with urllib.request.urlopen(req, timeout=20) as resp:
                    return resp.status
            except urllib.error.HTTPError as exc:
                if exc.code in (500, 502, 503, 504):
                    time.sleep(2 ** attempt)
                    continue
                return exc.code
            except Exception:
                return None
        return None

    # --- domain helpers ---
    def user(self, login: str) -> dict | None:
        return self.get_json(f"https://api.github.com/users/{login}")

    def public_repos(self, login: str, per_page: int = 100) -> list[dict]:
        data = self.get_json(
            f"https://api.github.com/users/{login}/repos?per_page={per_page}&sort=updated"
        )
        return data or []

    def repo_languages(self, full_name: str) -> dict:
        return self.get_json(f"https://api.github.com/repos/{full_name}/languages") or {}

    def repo(self, full_name: str) -> dict | None:
        return self.get_json(f"https://api.github.com/repos/{full_name}") or None

    def repo_tree(self, full_name: str, branch: str = "main") -> list[str]:
        data = self.get_json(
            f"https://api.github.com/repos/{full_name}/git/trees/{branch}?recursive=1"
        )
        if not data:
            return []
        return [entry.get("path", "") for entry in data.get("tree", []) if not entry.get("path", "").startswith(".git")]

    def public_events(self, login: str, per_page: int = 30) -> list[dict]:
        data = self.get_json(
            f"https://api.github.com/users/{login}/events/public?per_page={per_page}"
        )
        return data or []

    def repo_releases(self, full_name: str, per_page: int = 5) -> list[dict]:
        data = self.get_json(
            f"https://api.github.com/repos/{full_name}/releases?per_page={per_page}"
        )
        return data or []

    def contributions(self, login: str) -> dict | None:
        data = self.get_json(f"https://api.github.com/users/{login}/contributions")
        return data