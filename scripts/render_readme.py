"""Template renderer for the visual GitHub profile README.

Uses HTML comment markers to inject generated sections:

    <!-- NAME:START -->
    ... generated content ...
    <!-- NAME:END -->

Only the block between markers is replaced; everything else (hand-written
sections, footers, <details> blocks) is preserved untouched on every run.
"""
from __future__ import annotations

import re

_MARKER = re.compile(r"<!-- (\w+):START -->(.*?)<!-- \1:END -->", re.DOTALL)


def render_template(template: str, sections: dict[str, str]) -> str:
    """Replace every marker block with the matching generated section."""

    def _replace(match: re.Match) -> str:
        name = match.group(1)
        body = sections.get(name, "").strip()
        # If the marker block was empty in the template but we have content,
        # insert it. If the template had content between markers, preserve it
        # only if no generated content overrides it (simple approach: always
        # replace with generated content).
        return f"<!-- {name}:START -->\n{body}\n<!-- {name}:END -->"

    rendered = _MARKER.sub(_replace, template)

    # Collapse quadruple blank lines left by section replacement
    while "\n\n\n\n" in rendered:
        rendered = rendered.replace("\n\n\n\n", "\n\n")
    return rendered.strip() + "\n"