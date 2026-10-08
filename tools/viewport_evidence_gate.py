#!/usr/bin/env python3
"""ARCONT visual-evidence file integrity, not an artistic or AAA quality score.

Checks independently captured PNGs exist, meet resolution/byte floor,
have coherent IHDR headers, and are not four identical outputs.
Rendering provenance must still be established by the game's own CI logs.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
import zlib

PNG = b"\x89PNG\r\n\x1a\n"


def validate_viewpoints(paths: list[Path], min_width: int = 700,
                        min_height: int = 400, min_bytes: int = 30_000) -> list[str]:
    problems: list[str] = []
    if len(paths) < 2:
        return ["at least two independent viewpoints required"]
    shapes = []
    hashes = []
    for path in paths:
        try:
            data = path.read_bytes()
        except OSError as exc:
            problems.append(f"{path}: not readable ({exc})")
            continue
        if len(data) < min_bytes:
            problems.append(f"{path}: too few bytes to be a substantial framebuffer evidence file")
        if len(data) < 33 or data[:8] != PNG or data[12:16] != b"IHDR":
            problems.append(f"{path}: invalid PNG header")
            continue
        length = struct.unpack(">I", data[8:12])[0]
        if length != 13:
            problems.append(f"{path}: invalid IHDR length")
            continue
        expected_crc = struct.unpack(">I", data[29:33])[0]
        if zlib.crc32(data[12:29]) != expected_crc:
            problems.append(f"{path}: corrupt IHDR CRC")
            continue
        width, height = struct.unpack(">II", data[16:24])
        shapes.append((width, height))
        if width < min_width or height < min_height:
            problems.append(f"{path}: inadequate viewport size {width}x{height}")
        hashes.append(hashlib.sha256(data).hexdigest())
    if len(set(shapes)) > 1:
        problems.append("viewpoints use mismatched resolutions")
    if len(hashes) != len(set(hashes)):
        problems.append("duplicate frame bytes across viewpoints")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--min-width", type=int, default=700)
    parser.add_argument("--min-height", type=int, default=400)
    parser.add_argument("--min-bytes", type=int, default=30_000)
    args = parser.parse_args()
    failures = validate_viewpoints(args.images, args.min_width, args.min_height, args.min_bytes)
    if failures:
        for failure in failures:
            print("VIEWPORT EVIDENCE FAIL", failure)
        return 1
    print("VIEWPORT EVIDENCE PASS distinct=%d min=%dx%d (integrity only; NOT an art-quality rating)" %
          (len(args.images), args.min_width, args.min_height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
