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

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
USER_AGENT = "kulraj025-profile-generator"
API_ROOT = "https://api.github.com"


class GitHubAPIError(RuntimeError):
    pass


def _env_token() -> str:
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""


class GitHubAPI:
    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        self.cache_dir = cache_dir
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
        return Path(__file__).resolve().parent.parent / ".cache" / f"{safe}.json"

    def get_json(self, url: str, use_cache: bool = True, max_retries: int = 4) -> object:
        cache_path = self._cache_path(url)
        if use_cache and cache_path.exists():
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

    # --- domain helpers ---
    def user(self, login: str) -> dict | None:
        return self.get_json(f"https://api.github.com/users/{login}")

    def public_repos(self, login: str, per_page: int = 100) -> list[dict]:
        return self.get_json(f"https://api.github.com/users/{login}/repos?per_page={per_page}&sort=updated") or []

    def repo_languages(self, full_name: str) -> dict:
        return self.get_json(f"https://api.github.com/repos/{full_name}/languages") or {}

    def repo(self, full_name: str) -> dict | None:
        return self.get_json(f"https://api.github.com/repos/{full_name}") or None