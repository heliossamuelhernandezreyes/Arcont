#!/usr/bin/env python3
"""Mechanical audit for normalized RGBA PNG sprite frames.

Designed for ARCONT/Mortofe CI and intentionally limited to the Python standard
library. Semantic identity/costume/camera review remains a separate visual gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path
from statistics import median
from typing import Any

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def _decode_rgba_png(path: Path, alpha_threshold: int) -> dict[str, Any]:
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
        if len(payload) != length:
            raise ValueError("truncated PNG chunk")
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
            f"production frames must be non-interlaced 8-bit RGBA PNG "
            f"(bit_depth={bit_depth}, color_type={color_type}, interlace={interlace})"
        )
    assert width is not None and height is not None
    raw = zlib.decompress(bytes(idat))
    row_bytes, bpp = width * 4, 4
    if len(raw) != height * (row_bytes + 1):
        raise ValueError("unexpected decompressed PNG size")

    rows: list[bytes] = []
    prev = bytearray(row_bytes)
    pos = 0
    for _ in range(height):
        filt = raw[pos]
        pos += 1
        src = raw[pos:pos + row_bytes]
        pos += row_bytes
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

    x0, y0, x1, y1 = width, height, -1, -1
    digest = hashlib.sha256()
    for y, row in enumerate(rows):
        digest.update(row)
        for x in range(width):
            if row[x * 4 + 3] > alpha_threshold:
                x0, y0 = min(x0, x), min(y0, y)
                x1, y1 = max(x1, x), max(y1, y)
    bbox = None if x1 < 0 else [x0, y0, x1, y1]
    return {
        "width": width,
        "height": height,
        "bbox": bbox,
        "sha256": digest.hexdigest(),
    }


def _frames(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, str):
        return [{"path": value}]
    if isinstance(value, dict):
        if isinstance(value.get("path"), str):
            return [value]
        value = value.get("frames")
    if not isinstance(value, list):
        raise ValueError("state must be a path, frame, list, or {'frames': [...]}")
    out = []
    for item in value:
        if isinstance(item, str):
            out.append({"path": item})
        elif isinstance(item, dict) and isinstance(item.get("path"), str):
            out.append(item)
        else:
            raise ValueError("frame entries require a string path")
    return out


def _resource(root: Path, value: str) -> Path:
    return root / value.removeprefix("res://") if value.startswith("res://") else root / value


def _gate(manifest: dict[str, Any], char: dict[str, Any], key: str, default: float) -> float:
    value = char.get("quality_gates", {}).get(key, manifest.get("quality_gates", {}).get(key, default))
    if not isinstance(value, (int, float)):
        raise ValueError(f"quality gate {key} must be numeric")
    return float(value)


def audit(manifest_path: Path, project_root: Path) -> tuple[int, dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chars = manifest.get("characters")
    errors: list[str] = []
    warnings: list[str] = []
    report: dict[str, Any] = {}
    if not isinstance(chars, dict) or not chars:
        return 1, {"ok": False, "errors": ["manifest.characters must be non-empty"], "warnings": []}

    for char_name, char in chars.items():
        if not isinstance(char, dict):
            errors.append(f"{char_name}: spec must be an object")
            continue
        canvas, baseline, states = char.get("canvas"), char.get("baseline_y"), char.get("states")
        if not (isinstance(canvas, list) and len(canvas) == 2 and all(isinstance(v, int) and v > 0 for v in canvas)):
            errors.append(f"{char_name}: invalid canvas {canvas!r}")
            continue
        if not isinstance(baseline, (int, float)) or not 0 <= baseline < canvas[1]:
            errors.append(f"{char_name}: invalid baseline_y {baseline!r}")
            continue
        if not isinstance(states, dict) or not states:
            errors.append(f"{char_name}: states must be non-empty")
            continue
        try:
            baseline_limit = _gate(manifest, char, "max_baseline_drift_px", 2)
            pivot_limit = _gate(manifest, char, "max_pivot_drift_px", 2)
            height_limit = _gate(manifest, char, "max_visual_height_drift_pct", 4)
            padding_warn = _gate(manifest, char, "transparent_padding_warning_pct", 45)
            alpha_threshold = int(_gate(manifest, char, "alpha_threshold", 8))
        except ValueError as exc:
            errors.append(f"{char_name}: {exc}")
            continue
        canonical_pivot = char.get("pivot")
        char_report: dict[str, Any] = {}

        for state_name, state_value in states.items():
            try:
                entries = _frames(state_value)
            except ValueError as exc:
                errors.append(f"{char_name}.{state_name}: {exc}")
                continue
            if not entries:
                errors.append(f"{char_name}.{state_name}: no frames")
                continue
            state_report: list[dict[str, Any]] = []
            seen: dict[str, str] = {}
            suffixes: list[int] = []
            for index, entry in enumerate(entries):
                frame_id = f"{char_name}.{state_name}[{index}]"
                resource_path = entry["path"]
                path = _resource(project_root, resource_path)
                if not path.is_file():
                    errors.append(f"{frame_id}: missing {path}")
                    continue
                if path.suffix.lower() != ".png":
                    errors.append(f"{frame_id}: production frame must be PNG")
                    continue
                try:
                    info = _decode_rgba_png(path, alpha_threshold)
                except Exception as exc:
                    errors.append(f"{frame_id}: {exc}")
                    continue
                if [info["width"], info["height"]] != canvas:
                    errors.append(f"{frame_id}: canvas {info['width']}x{info['height']} != {canvas[0]}x{canvas[1]}")
                bbox = info["bbox"]
                if bbox is None:
                    errors.append(f"{frame_id}: no visible pixels above alpha threshold {alpha_threshold}")
                    continue
                x0, y0, x1, y1 = bbox
                visual_w, visual_h = x1 - x0 + 1, y1 - y0 + 1
                baseline_drift = abs(y1 - baseline)
                if baseline_drift > baseline_limit:
                    errors.append(f"{frame_id}: baseline drift {baseline_drift:g}px > {baseline_limit:g}px")
                padding = 100 * (1 - ((visual_w * visual_h) / (canvas[0] * canvas[1])))
                if padding > padding_warn:
                    warnings.append(f"{frame_id}: transparent padding {padding:.1f}% > {padding_warn:g}%")
                pivot_drift = None
                pivot = entry.get("pivot")
                if pivot is not None:
                    if not (isinstance(pivot, list) and len(pivot) == 2 and all(isinstance(v, (int, float)) for v in pivot)):
                        errors.append(f"{frame_id}: pivot must be [x, y]")
                    elif not (isinstance(canonical_pivot, list) and len(canonical_pivot) == 2):
                        warnings.append(f"{frame_id}: frame pivot declared without canonical character pivot")
                    else:
                        pivot_drift = max(abs(pivot[0] - canonical_pivot[0]), abs(pivot[1] - canonical_pivot[1]))
                        if pivot_drift > pivot_limit:
                            errors.append(f"{frame_id}: pivot drift {pivot_drift:g}px > {pivot_limit:g}px")
                if info["sha256"] in seen:
                    warnings.append(f"{frame_id}: duplicate pixels of {seen[info['sha256']]}")
                else:
                    seen[info["sha256"]] = frame_id
                match = re.search(r"(\d+)(?=\.png$)", Path(resource_path).name, re.I)
                if match:
                    suffixes.append(int(match.group(1)))
                state_report.append({
                    "path": resource_path,
                    "alpha_bbox": bbox,
                    "visual_size": [visual_w, visual_h],
                    "bottom_y": y1,
                    "baseline_drift_px": baseline_drift,
                    "pivot_drift_px": pivot_drift,
                    "transparent_padding_pct": round(padding, 3),
                    "content_sha256": info["sha256"],
                })
            heights = [frame["visual_size"][1] for frame in state_report]
            if len(heights) >= 2:
                ref = float(median(heights))
                for idx, frame in enumerate(state_report):
                    drift = abs(frame["visual_size"][1] - ref) / ref * 100
                    frame["visual_height_drift_pct"] = round(drift, 3)
                    if drift > height_limit:
                        errors.append(f"{char_name}.{state_name}[{idx}]: visual height drift {drift:.2f}% > {height_limit:g}%")
            if len(suffixes) == len(entries) and len(suffixes) > 1:
                ordered = sorted(suffixes)
                if ordered != list(range(ordered[0], ordered[-1] + 1)):
                    warnings.append(f"{char_name}.{state_name}: filename sequence has gaps: {ordered}")
            char_report[state_name] = state_report
        report[char_name] = char_report

    result = {
        "manifest": str(manifest_path),
        "project_root": str(project_root),
        "characters": report,
        "warnings": warnings,
        "errors": errors,
        "ok": not errors,
    }
    return (0 if not errors else 1), result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit normalized RGBA PNG sprite frames")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    code, result = audit(args.manifest.resolve(), args.project_root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
