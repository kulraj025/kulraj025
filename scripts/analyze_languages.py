"""Analyze real programming language usage from GitHub API byte counts."""
from __future__ import annotations

from typing import Iterable

# Framework / tool detection signatures keyed by language family.
# Only reported when actually detected in repository metadata.
FRAMEWORK_SIGNATURES: dict[str, list[tuple[str, str]]] = {
    "Python": [
        ("requirements.txt", "requirements.txt"),
        ("pyproject.toml", "pyproject.toml"),
        ("setup.py", "setup.py"),
        ("Pipfile", "Pipfile"),
        ("fastapi", "FastAPI"),
        ("django", "Django"),
        ("flask", "Flask"),
        ("scikit-learn", "scikit-learn"),
        ("tensorflow", "TensorFlow"),
        ("pytorch", "PyTorch"),
        ("numpy", "NumPy"),
        ("pandas", "pandas"),
        ("opencv-python", "OpenCV"),
    ],
    "JavaScript": [
        ("package.json", "package.json"),
        ("next.config.js", "Next.js"),
        ("nuxt.config.js", "Nuxt.js"),
        ("vue.config.js", "Vue.js"),
        ("vite.config.ts", "Vite"),
        ("react", "React"),
        ("vue", "Vue"),
        ("express", "Express"),
        ("axios", "Axios"),
        ("three.js", "Three.js"),
    ],
    "TypeScript": [
        ("package.json", "package.json"),
        ("tsconfig.json", "tsconfig.json"),
        ("next.config.ts", "Next.js"),
        ("vite.config.ts", "Vite"),
        ("react", "React"),
        ("vue", "Vue"),
        ("express", "Express"),
        ("nest", "NestJS"),
    ],
    "PHP": [
        ("composer.json", "composer.json"),
        ("artisan", "Laravel"),
        ("codeigniter", "CodeIgniter"),
        ("symfony", "Symfony"),
        ("wp-config.php", "WordPress"),
    ],
    "C++": [
        ("CMakeLists.txt", "CMake"),
        ("Makefile", "Makefile"),
        ("vcpkg.json", "vcpkg"),
    ],
    "C#": [
        ("*.csproj", "*.csproj"),
        ("*.sln", "*.sln"),
    ],
    "Java": [
        ("pom.xml", "Maven"),
        ("build.gradle", "Gradle"),
        ("settings.gradle", "Gradle"),
    ],
    "Go": [
        ("go.mod", "Go modules"),
        ("go.sum", "Go modules"),
    ],
    "Rust": [
        ("Cargo.toml", "Cargo"),
    ],
    "Ruby": [
        ("Gemfile", "Bundler"),
    ],
    "Swift": [
        ("Package.swift", "Swift Package Manager"),
    ],
}


def aggregate_languages(repos: list[dict], api) -> list[dict]:
    """Aggregate real per-repository byte counts into top languages.

    Falls back to primary-language metadata when byte counts are empty.
    """
    totals: dict[str, int] = {}
    for repo in repos:
        if repo.get("size", 0) == 0:
            continue
        langs = api.repo_languages(repo["full_name"]) or {}
        if langs:
            for lang, bytes_count in langs.items():
                totals[lang] = totals.get(lang, 0) + int(bytes_count)
        else:
            lang = repo.get("language")
            if lang:
                totals[lang] = totals.get(lang, 0) + repo.get("size", 0)

    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    return [
        {"name": name, "bytes": n, "percent": round(n / total * 100, 1)}
        for name, n in ranked
    ]


def detect_frameworks(repos: list[dict], api) -> dict[str, list[str]]:
    """Detect frameworks/tools actually present in repository metadata.

    Returns {language: [framework, ...]}.
    """
    detected: dict[str, list[str]] = {}
    for repo in repos:
        if repo.get("size", 0) == 0:
            continue
        topics = set(repo.get("topics") or [])
        lang = repo.get("language")
        # Check topics first (cheap, always available).
        for language, signatures in FRAMEWORK_SIGNATURES.items():
            for token, label in signatures:
                if token in topics:
                    detected.setdefault(language, [])
                    if label not in detected[language]:
                        detected[language].append(label)
        # Check repository file tree for framework markers.
        try:
            tree = api.repo_tree(repo["full_name"])
        except Exception:
            tree = []
        tree_set = set(tree)
        for language, signatures in FRAMEWORK_SIGNATURES.items():
            for token, label in signatures:
                if "*" in token:
                    # Glob-like match against tree entries.
                    suffix = token.split("*", 1)[0]
                    if any(t.endswith(suffix) for t in tree_set):
                        detected.setdefault(language, [])
                        if label not in detected[language]:
                            detected[language].append(label)
                elif token in tree_set or token in topics:
                    detected.setdefault(language, [])
                    if label not in detected[language]:
                        detected[language].append(label)
    return detected