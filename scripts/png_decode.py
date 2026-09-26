"""Minimal PNG decoder for QA rasterisation.

Decodes an 8-bit PNG to grayscale bytes using nothing but `zlib` from the
standard library.

Why this exists: rsvg-convert can only emit png, pdf, ps, eps or svg — there is
no PPM output. Decoding the PNG therefore needs a real decoder, and the
alternatives were both wrong. Asking rsvg-convert to convert its own PNG output
fails outright, and depending on Pillow means the check silently passes on a
developer machine and fails in CI, which is exactly how this check shipped
broken the first time.

Accuracy: the Rec. 601 weights are applied in floating point, where Pillow
applies fixed-point integer arithmetic. The two agree exactly on most pixels
and differ by at most 1/255 on the rest, which is immaterial against ink
thresholds of 40/255. What matters here is that this module has no optional
dependency and behaves identically on every machine.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

#: Rec. 601 luma coefficients, the same weighting Pillow's "L" mode uses, so
#: ink thresholds mean the same thing here as they did before.
_LUMA_R, _LUMA_G, _LUMA_B = 0.299, 0.587, 0.114

_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class PNGError(RuntimeError):
    pass


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter(raw: bytes, width: int, height: int, bpp: int) -> bytearray:
    """Reverse the PNG per-scanline filters into a flat sample buffer."""
    stride = width * bpp
    out = bytearray(stride * height)
    prev = bytearray(stride)
    pos = 0
    for y in range(height):
        ftype = raw[pos]
        pos += 1
        line = bytearray(raw[pos : pos + stride])
        pos += stride
        if ftype == 0:
            pass
        elif ftype == 1:  # Sub
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:  # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:  # Average
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:  # Paeth
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 0xFF
        else:
            raise PNGError(f"unknown PNG filter type {ftype}")
        out[y * stride : (y + 1) * stride] = line
        prev = line
    return out


def decode_grayscale(path: Path) -> tuple[int, int, bytes]:
    """Return (width, height, one luminance byte per pixel)."""
    data = Path(path).read_bytes()
    if not data.startswith(_SIGNATURE):
        raise PNGError(f"{Path(path).name}: not a PNG")

    pos = len(_SIGNATURE)
    width = height = depth = colour = interlace = None
    idat = bytearray()
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        ctype = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        pos += 12 + length  # length + type + data + crc
        if ctype == b"IHDR":
            width, height, depth, colour, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", body)
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break

    if width is None:
        raise PNGError(f"{Path(path).name}: no IHDR chunk")
    if depth != 8:
        raise PNGError(f"{Path(path).name}: bit depth {depth} is not supported (need 8)")
    if interlace:
        raise PNGError(f"{Path(path).name}: interlaced PNG is not supported")
    if colour not in (0, 2, 6):
        raise PNGError(
            f"{Path(path).name}: colour type {colour} is not supported "
            f"(need greyscale, RGB or RGBA)")

    channels = _CHANNELS[colour]
    flat = _unfilter(zlib.decompress(bytes(idat)), width, height, channels)

    if colour == 0:
        return width, height, bytes(flat)
    return _rgb_to_gray(flat, width, height, channels)


def _rgb_to_gray(flat: bytearray, width: int, height: int, bpp: int) -> tuple[int, int, bytes]:
    out = bytearray(width * height)
    for i in range(width * height):
        o = i * bpp
        # +0.5 so the truncation rounds, matching Pillow's "L" conversion. The
        # difference is at most 1, but keeping it exact means these QA numbers
        # are comparable against anything else measured the same way.
        out[i] = int(
            flat[o] * _LUMA_R + flat[o + 1] * _LUMA_G + flat[o + 2] * _LUMA_B + 0.5
        )
    return width, height, bytes(out)
