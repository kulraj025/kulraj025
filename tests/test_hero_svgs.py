"""Regression tests for the hand-written hero SVGs.

Both files exist because of a real, reported bug: the readme-typing-svg service
concatenates every entry in `lines` into ONE comma-joined <textPath> anchored at
the path origin, so a three-line request put ~62% of the string off-canvas and the
page rendered a heading reading "ilding campus products and XAI". The replacement
SVGs are ours, so these tests hold the two properties that bug violated.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BANNER = ROOT / "assets" / "banner.svg"
TYPING = ROOT / "assets" / "typing.svg"
HERO_SVGS = [BANNER, TYPING]

# The ink measurement needs a real rasteriser. The geometry assertions above run
# everywhere; only the measured ones need this.
needs_rasteriser = pytest.mark.skipif(
    not shutil.which("rsvg-convert"),
    reason="rsvg-convert not installed (apt install librsvg2-bin)",
)


@pytest.mark.parametrize("path", HERO_SVGS, ids=lambda p: p.name)
def test_svg_is_well_formed_xml(path: Path) -> None:
    """An unbalanced tag makes rsvg and every browser drop the whole graphic.

    This shipped broken once: wipe2 and wipe3 were missing </rect>, and a
    regex-only checker happily passed them.
    """
    ET.parse(path)


@pytest.mark.parametrize("path", HERO_SVGS, ids=lambda p: p.name)
def test_svg_declares_accessible_label(path: Path) -> None:
    """GitHub renders these as images, so the text must exist in the markup.

    With no <title>/<desc>/aria-label the graphic is an unlabelled image to a
    screen reader and to search indexing.
    """
    svg = path.read_text()
    assert "<title>" in svg, f"{path.name} has no <title>"
    assert 'role="img"' in svg, f"{path.name} has no role=img"
    assert "aria-label" in svg, f"{path.name} has no aria-label"


@pytest.mark.parametrize("path", HERO_SVGS, ids=lambda p: p.name)
def test_text_is_pinned_so_it_cannot_crop(path: Path) -> None:
    """Every <text> pins its advance width, making clipping structurally impossible.

    The brief's hardest requirement is that the first letter never crops. Rather
    than trust a font we do not control, textLength fixes the run's width exactly,
    so the glyphs land at the same offset in whatever font the viewer has.
    """
    svg = path.read_text()
    texts = re.findall(r"<text\b[^>]*>", svg)
    assert texts, f"{path.name} has no <text>"
    for tag in texts:
        assert "textLength=" in tag, f"{path.name}: unpinned <text> can crop: {tag}"


@pytest.mark.parametrize("path", HERO_SVGS, ids=lambda p: p.name)
def test_pinned_text_keeps_horizontal_slack(path: Path) -> None:
    """textLength must leave real margin inside the viewBox on both sides."""
    svg = path.read_text()
    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    assert vb, f"{path.name} has no viewBox"
    width = int(vb.group(1))

    for tag in re.findall(r"<text\b[^>]*>", svg):
        x = float(re.search(r'\sx="([\d.]+)"', tag).group(1))
        length = float(re.search(r'textLength="([\d.]+)"', tag).group(1))
        left, right = x - length / 2, width - (x + length / 2)
        assert left >= 8, f"{path.name}: {left:.0f}px slack on the left, too tight"
        assert right >= 8, f"{path.name}: {right:.0f}px slack on the right, too tight"


@needs_rasteriser
@pytest.mark.parametrize("path", HERO_SVGS, ids=lambda p: p.name)
def test_rendered_glyphs_stay_inside_the_canvas(path: Path) -> None:
    """Rasterise the text layer and measure the real ink bounding box.

    Covers the case textLength cannot: a renderer that ignores textLength and
    falls back to a wider font than we assumed.
    """
    width = int(re.search(r'viewBox="0 0 (\d+) (\d+)"', path.read_text()).group(1))
    height = int(re.search(r'viewBox="0 0 (\d+) (\d+)"', path.read_text()).group(2))

    r = subprocess.run(
        ["python3", str(ROOT / "scripts" / "check_svg_text_fits.py"), str(path)],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, f"{path.name} would crop:\n{r.stdout}{r.stderr}"


def test_typing_animation_is_valid_smil() -> None:
    """keyTimes must run 0..1 or browsers discard the animation.

    Chrome rejects an <animate> whose keyTimes do not begin at 0 and end at 1.
    Two of the three wipes were written that way, which would have left the
    typing effect permanently frozen with no visible symptom in CI.
    """
    svg = TYPING.read_text()
    widths = {
        m.group(1): float(m.group(2))
        for m in re.finditer(r'id="(wipe\d)"><rect[^>]*?width="([\d.]+)"', svg)
    }
    assert len(widths) == 3, f"expected one wipe per line, found {widths}"

    animates = list(
        re.finditer(r'<animate attributeName="width" values="([^"]+)" keyTimes="([^"]+)"', svg)
    )
    assert len(animates) == 3

    for i, m in enumerate(animates, start=1):
        values = [float(x) for x in m.group(1).split(";")]
        keytimes = [float(x) for x in m.group(2).split(";")]
        expected = widths[f"wipe{i}"]

        assert len(values) == len(keytimes), f"wipe{i}: values/keyTimes length mismatch"
        assert keytimes == sorted(keytimes), f"wipe{i}: keyTimes not monotonic"
        assert keytimes[0] == 0.0, f"wipe{i}: keyTimes must start at 0, got {keytimes[0]}"
        assert keytimes[-1] == 1.0, f"wipe{i}: keyTimes must end at 1, got {keytimes[-1]}"
        assert max(values) == expected, f"wipe{i}: never fully reveals the line"
        assert values[-1] == 0.0, f"wipe{i}: would linger visible into the next cycle"


def test_typing_lines_are_distinct_and_short() -> None:
    """The lines are the hero pitch; keep them one short sentence each."""
    svg = TYPING.read_text()
    lines = [
        re.sub(r"<[^>]+>", "", m.group(1)).strip()
        for m in re.finditer(r"<text\b[^>]*>(.*?)</text>", svg, re.S)
    ]
    assert len(lines) == 3
    for line in lines:
        assert 0 < len(line) <= 40, f"typing line too long: {line!r}"


def test_banner_carries_its_own_dark_background() -> None:
    """Cyan text on transparency is invisible in GitHub's light theme.

    A banner is the one element that cannot rely on the reader choosing dark.
    The backing fill may be a solid hex or a gradient, so resolve whichever it is
    and require every stop to be dark.
    """
    def is_dark(hex_colour: str) -> bool:
        r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
        return max(r, g, b) < 0x40

    for path in HERO_SVGS:
        svg = path.read_text()
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
        width, height = vb.group(1), vb.group(2)

        # A rect that covers the whole canvas, ignoring attribute order.
        backdrop = None
        for m in re.finditer(r"<rect\b([^>]*)/?>", svg):
            attrs = m.group(1)
            w = re.search(r'width="([\d.]+)"', attrs)
            h = re.search(r'height="([\d.]+)"', attrs)
            # A backdrop must actually paint. The <clipPath> rect is also
            # full-canvas but carries no fill, and it appears first.
            f = re.search(r'fill="([^"]+)"', attrs)
            if w and h and f and float(w.group(1)) >= float(width) and float(h.group(1)) >= float(height):
                backdrop = attrs
                break

        assert backdrop, f"{path.name} has no full-canvas backing rect"
        fill = re.search(r'fill="([^"]+)"', backdrop).group(1)

        if fill.startswith("url(#"):
            grad_id = fill[5:-1]
            grad = re.search(rf'<linearGradient id="{grad_id}".*?</linearGradient>', svg, re.S)
            assert grad, f"{path.name}: backdrop gradient {grad_id} not found"
            stops = re.findall(r'stop-color="(#[0-9A-Fa-f]{6})"', grad.group(0))
            assert stops, f"{path.name}: gradient {grad_id} has no stops"
            assert all(is_dark(c) for c in stops), (
                f"{path.name}: gradient {grad_id} has a light stop {stops}; "
                "text will be unreadable in light theme"
            )
        else:
            assert is_dark(fill), f"{path.name}: backdrop {fill} is not dark"
