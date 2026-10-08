#!/usr/bin/env python3
"""ARCONT visual-evidence file integrity, not an artistic or AAA quality score.

Checks complete PNG decoding, bounded size, resolution and distinct pixels.
Rendering provenance must still be established by the game's own CI logs.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import zlib

try:
    from tools.png_integrity import decode_frame
except ModuleNotFoundError:
    from png_integrity import decode_frame

def validate_viewpoints(paths: list[Path], min_width: int = 700,
                        min_height: int = 400, min_bytes: int = 30_000) -> list[str]:
    problems: list[str] = []
    if len(paths) < 2:
        return ["at least two independent viewpoints required"]
    shapes = []
    hashes = []
    for path in paths:
        try:
            size = path.stat().st_size
        except OSError as exc:
            problems.append(f"{path}: not readable ({exc})")
            continue
        if size < min_bytes:
            problems.append(f"{path}: too few bytes to be a substantial framebuffer evidence file")
        try:
            width, height, pixel_hash = decode_frame(path)
        except (OSError, ValueError, zlib.error) as exc:
            problems.append(f"{path}: invalid PNG ({exc})")
            continue
        shapes.append((width, height))
        if width < min_width or height < min_height:
            problems.append(f"{path}: inadequate viewport size {width}x{height}")
        hashes.append(pixel_hash)
    if len(set(shapes)) > 1:
        problems.append("viewpoints use mismatched resolutions")
    if len(hashes) != len(set(hashes)):
        problems.append("duplicate decoded frame pixels across viewpoints")
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
