#!/usr/bin/env python3
"""Deterministically normalize RGBA PNG sprite masters onto a shared production canvas.

The tool is intentionally Python-standard-library only so ARCONT can run it in CI.
It preserves aspect ratio, aligns a stable horizontal pivot and foot baseline, uses
premultiplied-alpha bilinear resampling, and refuses to silently crop frames.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import math
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def _decode_rgba_png(path: Path) -> tuple[int, int, list[bytes]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("invalid PNG signature")
    pos = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        crc_bytes = data[pos + 8 + length:pos + 12 + length]
        if len(payload) != length or len(crc_bytes) != 4:
            raise ValueError("truncated PNG chunk")
        expected_crc = struct.unpack(">I", crc_bytes)[0]
        actual_crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"CRC mismatch in {kind.decode('ascii', errors='replace')} chunk")
        pos += length + 12
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if compression != 0 or filtering != 0:
                raise ValueError("unsupported PNG compression/filter method")
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
    if None in (width, height, bit_depth, color_type, interlace):
        raise ValueError("missing IHDR")
    if bit_depth != 8 or color_type != 6 or interlace != 0:
        raise ValueError(
            f"source must be non-interlaced 8-bit RGBA PNG "
            f"(bit_depth={bit_depth}, color_type={color_type}, interlace={interlace})"
        )
    assert width is not None and height is not None
    if not idat:
        raise ValueError("missing IDAT data")
    raw = zlib.decompress(bytes(idat))
    row_bytes, bpp = width * 4, 4
    if len(raw) != height * (row_bytes + 1):
        raise ValueError("unexpected decompressed PNG size")

    rows: list[bytes] = []
    prev = bytearray(row_bytes)
    cursor = 0
    for _ in range(height):
        filt = raw[cursor]
        cursor += 1
        src = raw[cursor:cursor + row_bytes]
        cursor += row_bytes
        dst = bytearray(row_bytes)
        for i, value in enumerate(src):
            left = dst[i - bpp] if i >= bpp else 0
            up = prev[i]
            upper_left = prev[i - bpp] if i >= bpp else 0
            if filt == 0:
                out = value
            elif filt == 1:
                out = value + left
            elif filt == 2:
                out = value + up
            elif filt == 3:
                out = value + ((left + up) // 2)
            elif filt == 4:
                out = value + _paeth(left, up, upper_left)
            else:
                raise ValueError(f"unsupported PNG filter {filt}")
            dst[i] = out & 0xFF
        rows.append(bytes(dst))
        prev = dst
    return width, height, rows


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _encode_rgba_png(width: int, height: int, rows: list[bytes]) -> bytes:
    if len(rows) != height or any(len(row) != width * 4 for row in rows):
        raise ValueError("row dimensions do not match output canvas")
    raw = bytearray()
    for row in rows:
        raw.append(0)
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + _chunk(b"IEND", b"")
    )


def _visible_bbox(rows: list[bytes], width: int, height: int, alpha_threshold: int) -> list[int] | None:
    x0, y0, x1, y1 = width, height, -1, -1
    for y, row in enumerate(rows):
        for x in range(width):
            if row[x * 4 + 3] > alpha_threshold:
                x0, y0 = min(x0, x), min(y0, y)
                x1, y1 = max(x1, x), max(y1, y)
    return None if x1 < 0 else [x0, y0, x1, y1]


def _pixel(rows: list[bytes], width: int, height: int, x: int, y: int) -> tuple[float, float, float, float]:
    if x < 0 or y < 0 or x >= width or y >= height:
        return 0.0, 0.0, 0.0, 0.0
    row = rows[y]
    base = x * 4
    r, g, b, a = row[base:base + 4]
    af = a / 255.0
    return r * af, g * af, b * af, float(a)


def _sample_bilinear(rows: list[bytes], width: int, height: int, x: float, y: float) -> tuple[int, int, int, int]:
    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = x - x0, y - y0
    points = (
        (_pixel(rows, width, height, x0, y0), (1.0 - fx) * (1.0 - fy)),
        (_pixel(rows, width, height, x0 + 1, y0), fx * (1.0 - fy)),
        (_pixel(rows, width, height, x0, y0 + 1), (1.0 - fx) * fy),
        (_pixel(rows, width, height, x0 + 1, y0 + 1), fx * fy),
    )
    pr = pg = pb = alpha = 0.0
    for (r, g, b, a), weight in points:
        pr += r * weight
        pg += g * weight
        pb += b * weight
        alpha += a * weight
    if alpha <= 0.0:
        return 0, 0, 0, 0
    af = alpha / 255.0
    r = max(0, min(255, round(pr / af)))
    g = max(0, min(255, round(pg / af)))
    b = max(0, min(255, round(pb / af)))
    a = max(0, min(255, round(alpha)))
    return r, g, b, a


def _pair(value: Any, name: str) -> tuple[float, float]:
    if not (isinstance(value, list) and len(value) == 2 and all(isinstance(v, (int, float)) for v in value)):
        raise ValueError(f"{name} must be [x, y]")
    return float(value[0]), float(value[1])


def _canvas(value: Any, name: str = "target_canvas") -> tuple[int, int]:
    if not (isinstance(value, list) and len(value) == 2 and all(isinstance(v, int) and v > 0 for v in value)):
        raise ValueError(f"{name} must be [positive_int, positive_int]")
    return int(value[0]), int(value[1])


def _resolve(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a non-empty string")
    rel = value.removeprefix("res://") if value.startswith("res://") else value
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {value}") from exc
    return candidate


def normalize_frame(
    input_path: Path,
    *,
    target_canvas: tuple[int, int],
    target_pivot: tuple[float, float],
    target_visual_height: float,
    alpha_threshold: int = 8,
    padding_px: int = 4,
    source_anchor_x: str = "canvas_center",
    source_pivot: tuple[float, float] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    if target_visual_height <= 0:
        raise ValueError("target_visual_height must be > 0")
    if not 0 <= alpha_threshold <= 254:
        raise ValueError("alpha_threshold must be between 0 and 254")
    if padding_px < 0:
        raise ValueError("padding_px must be >= 0")

    width, height, rows = _decode_rgba_png(input_path)
    bbox = _visible_bbox(rows, width, height, alpha_threshold)
    if bbox is None:
        raise ValueError(f"no visible pixels above alpha threshold {alpha_threshold}")
    x0, y0, x1, y1 = bbox
    visible_h = y1 - y0 + 1

    if source_pivot is not None:
        src_x, src_y = source_pivot
        if abs(src_y - y1) > 0.5:
            raise ValueError(
                f"source pivot y={src_y:g} must match visible alpha bottom y={y1}; "
                "normalized production frames use the foot baseline as their visible bottom"
            )
    else:
        if source_anchor_x == "canvas_center":
            src_x = (width - 1) / 2.0
        elif source_anchor_x == "alpha_center":
            src_x = (x0 + x1) / 2.0
        else:
            raise ValueError("source_anchor_x must be 'canvas_center' or 'alpha_center'")
        src_y = float(y1)

    out_w, out_h = target_canvas
    tgt_x, tgt_y = target_pivot
    if not (0 <= tgt_x < out_w and 0 <= tgt_y < out_h):
        raise ValueError("target_pivot must lie inside target_canvas")
    scale = target_visual_height / visible_h

    transformed = [
        tgt_x + (x0 - src_x) * scale,
        tgt_y + (y0 - src_y) * scale,
        tgt_x + (x1 - src_x) * scale,
        tgt_y + (y1 - src_y) * scale,
    ]
    tx0, ty0, tx1, ty1 = transformed
    if tx0 < padding_px or ty0 < padding_px or tx1 > (out_w - 1 - padding_px) or ty1 > (out_h - 1 - padding_px):
        raise ValueError(
            "normalized frame would crop or violate padding: "
            f"projected_bbox={[round(v, 3) for v in transformed]}, "
            f"canvas={out_w}x{out_h}, padding={padding_px}; lower target_visual_height or adjust source pivot"
        )

    out_rows: list[bytes] = []
    baseline_row = int(round(tgt_y))
    for oy in range(out_h):
        row = bytearray(out_w * 4)
        if oy <= baseline_row:
            sy = src_y + ((oy - tgt_y) / scale)
            for ox in range(out_w):
                sx = src_x + ((ox - tgt_x) / scale)
                rgba = _sample_bilinear(rows, width, height, sx, sy)
                base = ox * 4
                row[base:base + 4] = bytes(rgba)
        out_rows.append(bytes(row))

    output_bbox = _visible_bbox(out_rows, out_w, out_h, alpha_threshold)
    if output_bbox is None:
        raise ValueError("normalization produced a fully transparent output")
    if output_bbox[3] != baseline_row:
        raise ValueError(
            f"normalized alpha bottom y={output_bbox[3]} does not match target baseline y={baseline_row}"
        )

    pixel_hash = hashlib.sha256(b"".join(out_rows)).hexdigest()
    png_bytes = _encode_rgba_png(out_w, out_h, out_rows)
    return png_bytes, {
        "source_size": [width, height],
        "source_alpha_bbox": bbox,
        "source_pivot": [round(src_x, 4), round(src_y, 4)],
        "target_canvas": [out_w, out_h],
        "target_pivot": [tgt_x, tgt_y],
        "target_visual_height": target_visual_height,
        "scale": round(scale, 8),
        "projected_bbox": [round(v, 4) for v in transformed],
        "output_alpha_bbox": output_bbox,
        "content_sha256": pixel_hash,
        "png_sha256": hashlib.sha256(png_bytes).hexdigest(),
    }


def run_plan(plan_path: Path, project_root: Path) -> tuple[int, dict[str, Any]]:
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return 1, {"ok": False, "errors": [f"cannot read plan: {exc}"], "frames": []}
    defaults = plan.get("defaults", {})
    frames = plan.get("frames")
    if not isinstance(defaults, dict):
        return 1, {"ok": False, "errors": ["defaults must be an object"], "frames": []}
    if not isinstance(frames, list) or not frames:
        return 1, {"ok": False, "errors": ["frames must be a non-empty list"], "frames": []}

    errors: list[str] = []
    prepared: list[tuple[Path, bytes, dict[str, Any]]] = []
    frame_reports: list[dict[str, Any]] = []
    outputs_seen: set[Path] = set()

    for index, frame in enumerate(frames):
        label = f"frames[{index}]"
        if not isinstance(frame, dict):
            errors.append(f"{label}: frame must be an object")
            continue
        try:
            input_value = frame.get("input")
            output_value = frame.get("output")
            input_path = _resolve(project_root, input_value)
            output_path = _resolve(project_root, output_value)
            if input_path == output_path:
                raise ValueError("input and output paths must differ")
            if not input_path.is_file():
                raise ValueError(f"missing input {input_path}")
            if output_path in outputs_seen:
                raise ValueError(f"duplicate output path {output_value}")
            outputs_seen.add(output_path)

            target_canvas = _canvas(frame.get("target_canvas", defaults.get("target_canvas")))
            target_pivot = _pair(frame.get("target_pivot", defaults.get("target_pivot")), "target_pivot")
            target_visual_height = frame.get("target_visual_height", defaults.get("target_visual_height"))
            if not isinstance(target_visual_height, (int, float)):
                raise ValueError("target_visual_height must be numeric")
            alpha_threshold = frame.get("alpha_threshold", defaults.get("alpha_threshold", 8))
            padding_px = frame.get("padding_px", defaults.get("padding_px", 4))
            if not isinstance(alpha_threshold, int):
                raise ValueError("alpha_threshold must be an integer")
            if not isinstance(padding_px, int):
                raise ValueError("padding_px must be an integer")
            source_anchor_x = frame.get("source_anchor_x", defaults.get("source_anchor_x", "canvas_center"))
            source_pivot_value = frame.get("source_pivot")
            source_pivot = _pair(source_pivot_value, "source_pivot") if source_pivot_value is not None else None

            png_bytes, report = normalize_frame(
                input_path,
                target_canvas=target_canvas,
                target_pivot=target_pivot,
                target_visual_height=float(target_visual_height),
                alpha_threshold=alpha_threshold,
                padding_px=padding_px,
                source_anchor_x=source_anchor_x,
                source_pivot=source_pivot,
            )
            report.update({"input": input_value, "output": output_value})
            prepared.append((output_path, png_bytes, report))
            frame_reports.append(report)
        except Exception as exc:
            errors.append(f"{label}: {exc}")

    if errors:
        return 1, {"ok": False, "errors": errors, "frames": frame_reports}

    for output_path, png_bytes, _ in prepared:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)
    return 0, {"ok": True, "errors": [], "frames": frame_reports}


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize RGBA PNG sprite masters onto deterministic production canvases")
    parser.add_argument("plan", type=Path, help="JSON normalization plan")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=None, help="optional JSON report path")
    args = parser.parse_args()
    code, result = run_plan(args.plan.resolve(), args.project_root.resolve())
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    print(payload)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
