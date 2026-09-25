"""Detect duplicate repositories based on name, description, homepage, and file structure."""
from __future__ import annotations

import re
from typing import Iterable

# Words that indicate a scratch / test / placeholder repository.
SCRATCH_PATTERNS = [
    re.compile(r"\btest(s)?\b", re.IGNORECASE),
    re.compile(r"\bscratch\b", re.IGNORECASE),
    re.compile(r"\btemp\b", re.IGNORECASE),
    re.compile(r"\bexperiment\b", re.IGNORECASE),
    re.compile(r"\bexample\b", re.IGNORECASE),
    re.compile(r"^test", re.IGNORECASE),
    re.compile(r"\.cpp$", re.IGNORECASE),
]


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _normalize_description(desc: str | None) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (desc or "").lower()).strip()


def _name_similarity(a: str, b: str) -> float:
    """Jaccard similarity over character trigrams of normalized names."""
    na, nb = _normalize_name(a), _normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta = {na[i : i + 3] for i in range(len(na) - 2)}
    tb = {nb[i : i + 3] for i in range(len(nb) - 2)}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _desc_similarity(a: str | None, b: str | None) -> float:
    da, db = _normalize_description(a), _normalize_description(b)
    if not da or not db:
        return 0.0
    if da == db:
        return 1.0
    sa = {da[i : i + 3] for i in range(len(da) - 2)}
    sb = {db[i : i + 3] for i in range(len(db) - 2)}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _homepage_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return 1.0 if a.rstrip("/").lower() == b.rstrip("/").lower() else 0.0


def is_scratch_repository(repo: dict) -> bool:
    """Heuristic: very small repos with only a single .cpp file are scratch."""
    name = repo.get("name", "")
    if any(p.search(name) for p in SCRATCH_PATTERNS):
        return True
    if repo.get("size", 0) == 0:
        return True
    return False


def detect_duplicate_pairs(repos: list[dict]) -> list[tuple[str, str, float]]:
    """Return list of (keep_name, drop_name, confidence) pairs.

    Confidence is 0..1 based on name/description/homepage similarity.
    The first repo in each pair is the stronger candidate (by stars, recency,
    homepage presence, and size).
    """
    candidates = [r for r in repos if not r.get("private") and not r.get("fork")]
    pairs: list[tuple[str, str, float]] = []
    seen = set()
    for i, a in enumerate(candidates):
        for b in candidates[i + 1 :]:
            name_sim = _name_similarity(a["name"], b["name"])
            desc_sim = _desc_similarity(a.get("description"), b.get("description"))
            home_sim = _homepage_similarity(a.get("homepage"), b.get("homepage"))
            score = max(name_sim, (name_sim + desc_sim + home_sim) / 3)
            if score < 0.55:
                continue
            # Decide which repo is stronger.
            keep, drop = _pick_stronger(a, b)
            key = (keep["name"], drop["name"])
            if key in seen:
                continue
            seen.add(key)
            pairs.append((keep["name"], drop["name"], round(score, 2)))
    return pairs


def _pick_stronger(a: dict, b: dict) -> tuple[dict, dict]:
    """Return (keep, drop).

    Preference order:
    1. has_pages=True (more likely to be a complete published project)
    2. Larger size (more content/files = more substantial)
    3. More stars
    4. Non-empty homepage (but not verified here)
    5. More recent push
    """
    a_pages = a.get("has_pages", False)
    b_pages = b.get("has_pages", False)
    if a_pages and not b_pages:
        return a, b
    if b_pages and not a_pages:
        return b, a

    if a.get("size", 0) != b.get("size", 0):
        return (a, b) if a.get("size", 0) > b.get("size", 0) else (b, a)

    if a.get("stargazers_count", 0) != b.get("stargazers_count", 0):
        return (a, b) if a["stargazers_count"] > b["stargazers_count"] else (b, a)

    ha = bool(a.get("homepage"))
    hb = bool(b.get("homepage"))
    if ha and not hb:
        return a, b
    if hb and not ha:
        return b, a

    pa = a.get("pushed_at") or ""
    pb = b.get("pushed_at") or ""
    if pa and pb and pa != pb:
        return (a, b) if pa > pb else (b, a)

    return a, b


def drop_duplicates(repos: list[dict]) -> tuple[list[dict], list[tuple[str, str, float]]]:
    """Return (filtered_repos, duplicate_pairs)."""
    pairs = detect_duplicate_pairs(repos)
    drop_names = {drop for _, drop, _ in pairs}
    filtered = [r for r in repos if r["name"] not in drop_names]
    return filtered, pairs