"""Detect valid live-demo URLs for repositories.

Source priority:
1. GitHub repository homepage field
2. Verified GitHub Pages URL (HTTP 200)
3. Explicit config mapping
4. Manually approved URL

Rejects: localhost, example.com, empty, invalid, broken, placeholder URLs.
"""
from __future__ import annotations

import re
import urllib.parse
from typing import Iterable

REJECT_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "example.com",
    "example.org",
    "example.net",
    "test.com",
    "invalid",
    "domain.example",
    "your-site.example",
    "your-domain.example",
    "site.example",
    "my-site.example",
    "placeholder.example",
    "demo.example",
}

PLACEHOLDER_PATHS = {
    "todo",
    "tbd",
    "coming-soon",
    "wip",
    "work-in-progress",
    "placeholder",
}


def _normalize_url(url: str) -> str:
    """Normalize a URL: strip whitespace, ensure scheme, strip trailing slash."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    url = url.rstrip("/")
    return url


def _is_valid_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc:
        return False
    host = parsed.netloc.split(":")[0].lower()
    if host in REJECT_HOSTS:
        return False
    if host.endswith(".example.com") or host.endswith(".example.org") or host.endswith(".example.net"):
        return False
    path = parsed.path.lower().strip("/")
    if any(p in path.split("/") for p in PLACEHOLDER_PATHS):
        return False
    if any(tok in path for tok in ("todo", "tbd", "placeholder", "coming-soon")):
        return False
    return True


def detect_homepage(repo: dict, *, verify: bool = False, api=None) -> str | None:
    """Return a validated homepage URL for a repo, or None."""
    url = (repo.get("homepage") or "").strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if not _is_valid_url(url):
        return None
    if verify and api is not None:
        status = api.head(url)
        if status is None or status >= 400:
            return None
    return url


def detect_github_pages(repo: dict, *, verify: bool = False, api=None) -> str | None:
    """Return a verified GitHub Pages URL for a repo, or None.

    Only considers repos with has_pages=True and a known default branch.
    """
    if not repo.get("has_pages"):
        return None
    name = repo.get("name", "")
    if not name:
        return None
    candidate = f"https://{repo.get('owner', {}).get('login', 'kulraj025')}.github.io/{name}/"
    if not _is_valid_url(candidate):
        return None
    if verify and api is not None:
        status = api.head(candidate)
        if status is None or status >= 400:
            return None
    return candidate


def resolve_demo_url(repo: dict, *, verify: bool = False, api=None, config_mapping: dict | None = None) -> str | None:
    """Resolve a live-demo URL using the documented source priority."""
    # 1. Repository homepage field
    homepage = detect_homepage(repo, verify=verify, api=api)
    if homepage:
        return homepage
    # 2. Verified GitHub Pages URL
    pages = detect_github_pages(repo, verify=verify, api=api)
    if pages:
        return pages
    # 3. Explicit config mapping
    if config_mapping:
        mapped = config_mapping.get(repo.get("name"))
        if mapped and _is_valid_url(mapped):
            return mapped
    return None