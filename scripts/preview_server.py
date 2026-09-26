#!/usr/bin/env python3
"""Serve a faithful local render of README.md over HTTP for browser inspection.

The README's relative asset paths must resolve the way they do on github.com,
so the render is served from the repository root and the README body is
injected as a sibling HTML file. GitHub's constraints are reproduced:

  * <style> blocks are stripped (the sanitizer does this) — only inline style
    survives, which is why the generator emits inline styles
  * the content column is 1012px with 32px gutters, images cap at 890px
  * align="center" maps to text-align:center
  * GitHub's dark theme
"""
from __future__ import annotations

import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path("/home/Jeevan/profile-build")

CSS = """
:root{--fg:#c9d1d9;--muted:#8b949e;--border:#30363d}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#010409;color:#f0f6fc;
 font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif}
.markdown-body{max-width:1012px;margin:0 auto;padding:32px;word-wrap:break-word}
.markdown-body img{max-width:100%;height:auto;display:block}
.markdown-body table{border-collapse:collapse;border-spacing:0;width:100%}
.markdown-body td{padding:0;vertical-align:top}
.markdown-body p{margin-top:0;margin-bottom:16px}
.markdown-body h2{font-weight:600;font-size:1.5em;margin:24px 0 16px}
.markdown-body a{color:#2f81f7;text-decoration:none}
.markdown-body hr{height:1px;border:0;background:#21262d;margin:24px 0}
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>README preview</title>
<style>{css}
body{{background:#010409}}
.markdown-body{{max-width:{width}px;padding:{pad}px}}
</style></head>
<body><article class="markdown-body">
{body}
</article></body></html>
"""


def body_html(width: int) -> str:
    md = (REPO / "README.md").read_text(encoding="utf-8")
    out: list[str] = []
    for chunk in re.split(r"\n\s*\n", md):
        chunk = re.sub(r"<!--\s*GENERATED:\w+:(?:START|END)\s*-->", "", chunk).strip()
        if not chunk:
            continue
        if chunk.startswith(("<table", "<div", "<p", "<img", "<h2", "<a ")):
            out.append(chunk)
        else:
            out.append(f"<p>{chunk}</p>")
    pad = 32 if width > 500 else 16
    return PAGE.format(css=CSS, width=width, pad=pad, body="\n".join(out))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(REPO), **kw)

    def do_GET(self):
        m = re.match(r"^/preview(\d*)\.html", self.path.split("?")[0])
        if m:
            w = int(m.group(1) or 1012)
            body = body_html(w).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
