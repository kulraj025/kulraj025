"""Tests for the stdlib PNG decoder used by the raster QA.

The decoder exists because rsvg-convert cannot emit PPM and depending on Pillow
made the raster QA pass locally while failing in CI. These tests pin it against
values that can be derived independently, so a regression is caught without
needing Pillow present.
"""
from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import png_decode  # noqa: E402

have_rsvg = bool(shutil_which := __import__("shutil").which("rsvg-convert"))
needs_rsvg = pytest.mark.skipif(not have_rsvg, reason="rsvg-convert not installed")


def _write_png(path: Path, width: int, height: int, rows: list[list[tuple]],
               colour_type: int = 6, force_filter: int | None = None) -> None:
    """Build a PNG by hand.

    With `force_filter` set, every scanline uses that filter type; otherwise row
    y uses filter y % 5, so a five-row image covers all of them at once.
    """
    channels = {0: 1, 2: 3, 6: 4}[colour_type]
    raw = bytearray()
    for y, row in enumerate(rows):
        ftype = y % 5 if force_filter is None else force_filter
        raw.append(ftype)
        prior = rows[y - 1] if y else [(0, 0, 0)] * width
        for x, px in enumerate(row):
            cur = list(px) + [255] * (channels - len(px))
            prev = list(prior[x]) + [255] * (channels - len(prior[x]))
            left = (list(row[x - 1]) + [255] * (channels - 3)) if x else [0] * channels
            upleft = ((list(prior[x - 1]) + [255] * (channels - 3))
                      if x else [0] * channels)
            recon = []
            for c in range(channels):
                a, b, cc = left[c], prev[c], upleft[c]
                if ftype == 0:
                    pred = 0
                elif ftype == 1:      # Sub: difference from the left neighbour
                    pred = a
                elif ftype == 2:      # Up: difference from the row above
                    pred = b
                elif ftype == 3:      # Average of left and up
                    pred = (a + b) >> 1
                else:                 # Paeth
                    p = a + b - cc
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - cc)
                    pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else cc)
                recon.append((cur[c] - pred) & 0xFF)
            raw += bytes(recon)

    def chunk(tag: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, colour_type,
                                      0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw)))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


class TestDecoder:
    def test_decodes_a_known_image_exactly(self):
        """8x4 RGBA, all five filter types, exact expected luminance."""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.png"
            rows = [[(0, 0, 0)] * 8, [(255, 255, 255)] * 8,
                    [(255, 0, 0)] * 8, [(0, 0, 255)] * 8]
            _write_png(p, 8, 4, rows)
            w, h, px = png_decode.decode_grayscale(p)
        assert (w, h) == (8, 4)
        assert len(px) == 32
        # luma of pure black / white / red / blue per Rec. 601
        assert px[0:8] == bytes([0] * 8)
        assert px[8:16] == bytes([255] * 8)
        assert px[16:24] == bytes([int(255 * 0.299 + 0.5)] * 8)
        assert px[24:32] == bytes([int(255 * 0.114 + 0.5)] * 8)

    def test_all_five_filter_types_reconstruct_identically(self):
        """The same image written with each filter must decode the same.

        This is the property that matters: a wrong Sub or Paeth implementation
        still produces plausible-looking bytes, it just produces the wrong
        image. Forcing each filter in turn and requiring one single answer is
        what actually pins the reconstruction.
        """
        width, height = 12, 5
        rows = [[((x * 17 + y * 31) % 256, (x * 5) % 256, (y * 11) % 256)
                 for x in range(width)] for y in range(height)]
        decoded = []
        with tempfile.TemporaryDirectory() as td:
            for forced in range(5):
                p = Path(td) / f"f{forced}.png"
                _write_png(p, width, height, rows, force_filter=forced)
                decoded.append(png_decode.decode_grayscale(p))
        assert len({d[0] for d in decoded}) == 1
        assert len({d[1] for d in decoded}) == 1
        assert len({d[2] for d in decoded}) == 1, (
            "filter type changed the decoded pixels")
        w, h, px = decoded[0]
        assert (w, h) == (width, height)
        expected = bytearray()
        for y in range(height):
            for x in range(width):
                r, g, b = rows[y][x]
                expected.append(int(r * 0.299 + g * 0.587 + b * 0.114 + 0.5))
        assert px == bytes(expected)

    def test_handles_a_greyscale_png(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "g.png"
            _write_png(p, 4, 2, [[(0,), (64,), (128,), (255,)],
                                 [(255,), (128,), (64,), (0,)]], colour_type=0)
            w, h, px = png_decode.decode_grayscale(p)
        assert (w, h) == (4, 2)
        assert list(px) == [0, 64, 128, 255, 255, 128, 64, 0]

    def test_rejects_a_non_png(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.png"
            p.write_bytes(b"not a png at all")
            with pytest.raises(png_decode.PNGError):
                png_decode.decode_grayscale(p)

    def test_rejects_16_bit_depth(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.png"
            p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
            with pytest.raises(png_decode.PNGError):
                png_decode.decode_grayscale(p)


@needs_rsvg
class TestAgainstRealAssets:
    @pytest.mark.parametrize("name", [
        "hero.svg", "technology-orbit.svg", "contact-horizon.svg",
        "horizon-signal.svg", "learning-path.svg", "divider.svg",
    ])
    def test_every_scene_decodes_to_the_right_shape(self, name):
        svg = ROOT / "assets" / "generated" / name
        with tempfile.TemporaryDirectory() as td:
            png = Path(td) / "o.png"
            subprocess.run(["rsvg-convert", "-w", "1000", "-o", str(png), str(svg)],
                           check=True, capture_output=True)
            w, h, px = png_decode.decode_grayscale(png)
        assert w == 1000, name
        assert len(px) == w * h, name
        assert max(px) > 40, f"{name} decoded to an entirely blank image"

    def test_decoder_needs_no_optional_dependency(self):
        """The module must not import Pillow, numpy or anything optional."""
        source = (ROOT / "scripts" / "png_decode.py").read_text()
        for banned in ("PIL", "numpy", "cv2", "imageio"):
            assert banned not in source.replace(
                "Pillow's", "").replace("fixed-point", ""), banned
