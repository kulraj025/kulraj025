#!/usr/bin/env python3
"""Structural checks on the generated README's HTML.

GitHub renders README HTML through a sanitizer and then a real browser. Invalid
markup does not raise an error there — it is silently reflowed. A `<tr>` emitted
outside a `<table>`, for example, gets hoisted into a table of its own and the
two-column layout that was intended simply stops being a column, with no error
anywhere to explain why.

So this parses the output the way a browser would and asserts the structure
actually survived. It is the check that catches "the page renders wrong and
nothing reports an error".
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

VOID = {"img", "br", "hr", "meta", "link", "input", "source"}
#: Elements GitHub's sanitizer strips. None may appear in the output.
FORBIDDEN = {"script", "style", "iframe", "object", "embed", "form", "input",
             "video", "audio", "foreignObject"}


class Structure(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.problems: list[str] = []
        self.counts: dict[str, int] = {}
        self.text = 0
        self.depth_at: dict[str, int] = {}

    def handle_starttag(self, tag, attrs):
        self.counts[tag] = self.counts.get(tag, 0) + 1
        a = {k: v for k, v in attrs}

        if tag in FORBIDDEN:
            self.problems.append(f"forbidden element <{tag}> — GitHub strips this")
        if tag in VOID:
            alt = a.get("alt")
            if tag == "img" and alt is None:
                self.problems.append("<img> without alt text")
            if tag == "img" and a.get("src", "").strip() == "":
                self.problems.append("<img> with empty src")
            return

        # A table row or cell is only meaningful inside a table.
        if tag in ("tr", "td", "th"):
            if not any(t == "table" for t in self.stack):
                self.problems.append(
                    f"<{tag}> outside a <table> — the browser will hoist it "
                    f"and the intended layout is lost")
        if tag == "td":
            parent = next((t for t in reversed(self.stack) if t not in VOID), None)
            if parent not in ("tr",):
                self.problems.append(
                    f"<td> directly inside <{parent or 'nothing'}> — "
                    f"expected a <tr>")
        if tag == "tr":
            if not any(t == "table" for t in self.stack):
                self.problems.append("<tr> outside a <table>")
            else:
                # must be a direct child of table/tbody/thead/tfoot
                parent = self.stack[-1] if self.stack else ""
                if parent not in ("table", "tbody", "thead", "tfoot"):
                    self.problems.append(
                        f"<tr> nested inside <{parent}> — expected table/tbody")
        if tag in ("p", "div"):
            for t in reversed(self.stack):
                if t == "p":
                    self.problems.append(
                        f"<{tag}> nested inside <p> — the browser closes the "
                        f"outer <p> early and the layout shifts")
                    break
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in self.stack:
            # pop back to the matching open tag; anything left open is unclosed
            i = len(self.stack) - 1 - self.stack[::-1].index(tag)
            unclosed = self.stack[i + 1:]
            for u in unclosed:
                self.problems.append(f"<{u}> left unclosed before </{tag}>")
            del self.stack[i:]
        else:
            self.problems.append(f"</{tag}> with no matching open tag")

    def handle_data(self, data):
        if data.strip():
            self.text += len(data.strip())


def check_images(md: str) -> list[str]:
    problems: list[str] = []
    for m in re.finditer(r"<img\b[^>]*>", md):
        tag = m.group(0)
        src = re.search(r'src="([^"]*)"', tag)
        if not src or not src.group(1).strip():
            problems.append("img without a usable src")
            continue
        if not (ROOT / src.group(1)).is_file():
            problems.append(f"img src does not resolve: {src.group(1)}")
        if 'alt="' not in tag:
            problems.append(f"img missing alt: {src.group(1)}")
    return problems


def main() -> int:
    if not README.is_file():
        print(f"missing {README}")
        return 1
    md = README.read_text(encoding="utf-8")

    s = Structure()
    s.feed(md)
    s.close()
    for u in s.stack:
        s.problems.append(f"<{u}> never closed at end of document")

    problems = s.problems + check_images(md)

    print(f"README structure — {sum(s.counts.values())} tags, "
          f"{len(s.counts.get('img', [])) if False else s.counts.get('img', 0)} images, "
          f"{s.text} characters of text")
    print("-" * 68)
    if problems:
        seen: set[str] = set()
        for p in problems:
            if p in seen:
                continue
            seen.add(p)
            print(f"  FAIL  {p}")
        print(f"\n{len(seen)} distinct structural problem(s).")
        return 1

    print("  ok    no <tr>/<td> outside a table")
    print("  ok    no block element nested inside <p>")
    print("  ok    every tag balanced")
    print("  ok    no script/style/iframe/object/embed/form/video")
    print("  ok    every image has alt text and a resolvable src")
    print("\nREADME structure is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
