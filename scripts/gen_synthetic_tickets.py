"""Generate three synthetic remito-like PNG tickets (stdlib only).

These are NOT real scale tickets. They exist so the demo and OCR
spike can run without photographing field paper.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "tickets"

# 5x7 uppercase bitmap (bit 4 = left). Space and a few punctuation marks.
_FONT: dict[str, tuple[int, ...]] = {
    " ": (0, 0, 0, 0, 0),
    "-": (0, 0, 0x0E, 0, 0),
    ".": (0, 0, 0, 0, 0x01),
    "/": (0x02, 0x04, 0x08, 0x10, 0x20),
    ":": (0, 0x0A, 0, 0x0A, 0),
    "0": (0x1F, 0x11, 0x11, 0x11, 0x1F),
    "1": (0x00, 0x11, 0x1F, 0x10, 0x00),
    "2": (0x1D, 0x15, 0x15, 0x15, 0x17),
    "3": (0x11, 0x15, 0x15, 0x15, 0x1F),
    "4": (0x07, 0x04, 0x04, 0x04, 0x1F),
    "5": (0x17, 0x15, 0x15, 0x15, 0x1D),
    "6": (0x1F, 0x15, 0x15, 0x15, 0x1D),
    "7": (0x01, 0x01, 0x01, 0x01, 0x1F),
    "8": (0x1F, 0x15, 0x15, 0x15, 0x1F),
    "9": (0x17, 0x15, 0x15, 0x15, 0x1F),
    "A": (0x1E, 0x05, 0x05, 0x05, 0x1E),
    "B": (0x1F, 0x15, 0x15, 0x15, 0x0A),
    "C": (0x0E, 0x11, 0x11, 0x11, 0x0A),
    "D": (0x1F, 0x11, 0x11, 0x11, 0x0E),
    "E": (0x1F, 0x15, 0x15, 0x15, 0x11),
    "F": (0x1F, 0x05, 0x05, 0x05, 0x01),
    "G": (0x0E, 0x11, 0x15, 0x15, 0x1C),
    "H": (0x1F, 0x04, 0x04, 0x04, 0x1F),
    "I": (0x11, 0x11, 0x1F, 0x11, 0x11),
    "J": (0x08, 0x10, 0x10, 0x10, 0x0F),
    "K": (0x1F, 0x04, 0x0A, 0x11, 0x11),
    "L": (0x1F, 0x10, 0x10, 0x10, 0x10),
    "M": (0x1F, 0x02, 0x04, 0x02, 0x1F),
    "N": (0x1F, 0x02, 0x04, 0x08, 0x1F),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1F, 0x05, 0x05, 0x05, 0x02),
    "Q": (0x0E, 0x11, 0x19, 0x11, 0x1E),
    "R": (0x1F, 0x05, 0x0D, 0x15, 0x12),
    "S": (0x12, 0x15, 0x15, 0x15, 0x09),
    "T": (0x01, 0x01, 0x1F, 0x01, 0x01),
    "U": (0x0F, 0x10, 0x10, 0x10, 0x0F),
    "V": (0x07, 0x08, 0x10, 0x08, 0x07),
    "W": (0x1F, 0x08, 0x04, 0x08, 0x1F),
    "X": (0x11, 0x0A, 0x04, 0x0A, 0x11),
    "Y": (0x03, 0x04, 0x18, 0x04, 0x03),
    "Z": (0x19, 0x15, 0x15, 0x15, 0x13),
}

TICKETS = (
    {
        "filename": "remito-soja-tucuman.png",
        "header": "REMITO / TICKET DE BALANZA",
        "accent": (34, 92, 56),
        "lines": (
            "SINTETICO - NO ES UN TICKET REAL",
            "FECHA: 2026-08-20",
            "PATENTE: AB123CD",
            "TONELAJE: 18500 KG",
            "ORIGEN: TUCUMAN",
            "DESTINO: ROSARIO",
            "PRODUCTO: SOJA",
            "HUMEDAD: 13.5",
        ),
    },
    {
        "filename": "remito-maiz-salta.png",
        "header": "REMITO / TICKET DE BALANZA",
        "accent": (140, 92, 18),
        "lines": (
            "SINTETICO - NO ES UN TICKET REAL",
            "FECHA: 2026-08-21",
            "PATENTE: AC456DE",
            "TONELAJE: 24200 KG",
            "ORIGEN: SALTA",
            "DESTINO: TIMBUES",
            "PRODUCTO: MAIZ",
            "HUMEDAD: 14.2",
        ),
    },
    {
        "filename": "remito-trigo-santiago.png",
        "header": "REMITO / TICKET DE BALANZA",
        "accent": (92, 52, 20),
        "lines": (
            "SINTETICO - NO ES UN TICKET REAL",
            "FECHA: 2026-08-22",
            "PATENTE: AD789FG",
            "TONELAJE: 15800 KG",
            "ORIGEN: SANTIAGO DEL ESTERO",
            "DESTINO: SAN LORENZO",
            "PRODUCTO: TRIGO",
            "HUMEDAD: 12.8",
        ),
    },
)

WIDTH = 820
HEIGHT = 520
SCALE = 3


def _chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_png(path: Path, pixels: list[list[tuple[int, int, int]]]) -> None:
    height = len(pixels)
    width = len(pixels[0])
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))
    compressed = zlib.compress(bytes(raw), 9)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def _fill(
    pixels: list[list[tuple[int, int, int]]],
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    for y in range(max(0, y0), min(HEIGHT, y1)):
        row = pixels[y]
        for x in range(max(0, x0), min(WIDTH, x1)):
            row[x] = color


def _glyph(ch: str) -> tuple[int, ...]:
    return _FONT.get(ch.upper(), _FONT[" "])


def _draw_text(
    pixels: list[list[tuple[int, int, int]]],
    x: int,
    y: int,
    text: str,
    color: tuple[int, int, int],
    scale: int = SCALE,
) -> None:
    cx = x
    for ch in text:
        cols = _glyph(ch)
        for col_i, bits in enumerate(cols):
            for row_i in range(7):
                if bits & (1 << row_i):
                    _fill(
                        pixels,
                        cx + col_i * scale,
                        y + row_i * scale,
                        cx + (col_i + 1) * scale,
                        y + (row_i + 1) * scale,
                        color,
                    )
        cx += 6 * scale


def render_ticket(spec: dict) -> list[list[tuple[int, int, int]]]:
    paper = (248, 244, 230)
    ink = (28, 24, 18)
    accent: tuple[int, int, int] = spec["accent"]
    pixels = [[paper for _ in range(WIDTH)] for _ in range(HEIGHT)]
    _fill(pixels, 0, 0, WIDTH, 12, accent)
    _fill(pixels, 0, HEIGHT - 12, WIDTH, HEIGHT, accent)
    _fill(pixels, 0, 0, 12, HEIGHT, accent)
    _fill(pixels, WIDTH - 12, 0, WIDTH, HEIGHT, accent)
    _fill(pixels, 24, 28, WIDTH - 24, 88, accent)
    _draw_text(pixels, 40, 42, spec["header"], (252, 250, 240), scale=3)
    y = 112
    for line in spec["lines"]:
        _draw_text(pixels, 40, y, line, ink, scale=3)
        y += 42
    _draw_text(pixels, 40, HEIGHT - 48, "QCAMP DEMO FIXTURE", ink, scale=2)
    return pixels


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in TICKETS:
        dest = OUT / spec["filename"]
        write_png(dest, render_ticket(spec))
        print(f"wrote {dest.relative_to(ROOT)} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
