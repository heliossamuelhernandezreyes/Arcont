#!/usr/bin/env python3
"""ARCONT deterministic 2D sprite audit + atlas packer.

This tool is deliberately art-direction agnostic. It operates on already
separated PNG frames and a JSON manifest that declares semantic anchors,
animation ordering and runtime limits.

Requires Pillow only for image operations:
    python -m pip install Pillow

The pure manifest/layout helpers use only the Python standard library so they
can be unit-tested in ARCONT's dependency-light CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

SCHEMA_VERSION = 1


def ordered_frames(manifest: dict) -> list[dict]:
    """Flatten manifest states in declared order, preserving frame order."""
    frames: list[dict] = []
    for state_name, state in manifest["states"].items():
        for index, path in enumerate(state["frames"]):
            frames.append(
                {
                    "state": state_name,
                    "state_index": index,
                    "path": path,
                    "fps": state.get("fps"),
                    "loop": bool(state.get("loop", False)),
                }
            )
    return frames


def page_layout(frame_count: int, columns: int, rows: int) -> list[dict]:
    """Return deterministic atlas page/slot metadata for N frames."""
    if frame_count < 0 or columns <= 0 or rows <= 0:
        raise ValueError("invalid frame_count/columns/rows")
    per_page = columns * rows
    result: list[dict] = []
    for index in range(frame_count):
        page = index // per_page
        local = index % per_page
        result.append(
            {
                "index": index,
                "page": page,
                "column": local % columns,
                "row": local // columns,
            }
        )
    return result


def _pillow():
    try:
        from PIL import Image  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "sprite_pipeline image commands require Pillow. "
            "Install with: python -m pip install Pillow"
        ) from exc
    return Image


def _alpha_bbox(image) -> tuple[int, int, int, int] | None:
    return image.getchannel("A").getbbox()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "canvas", "anchor", "states"}
    missing = sorted(required - set(data))
    if missing:
        raise SystemExit(f"manifest missing required keys: {', '.join(missing)}")
    if int(data["schema_version"]) != SCHEMA_VERSION:
        raise SystemExit(
            f"unsupported manifest schema_version={data['schema_version']}"
        )
    if data["anchor"].get("type") != "feet":
        raise SystemExit("v1 supports semantic feet anchors only")
    return data


def _resolve(root: Path, entry: str) -> Path:
    path = Path(entry)
    return path if path.is_absolute() else root / path


@dataclass
class AuditFrame:
    index: int
    state: str
    state_index: int
    path: str
    width: int
    height: int
    alpha_bbox: list[int] | None
    opaque_width: int
    opaque_height: int
    transparent_padding_percent: float
    sha256: str


def audit(manifest_path: Path, output: Path | None = None) -> dict:
    Image = _pillow()
    manifest = _load_manifest(manifest_path)
    root = manifest_path.parent
    expected_w, expected_h = map(int, manifest["canvas"])
    warning_padding = float(
        manifest.get("quality_gates", {}).get(
            "transparent_padding_warning_percent", 45
        )
    )

    result_frames: list[AuditFrame] = []
    errors: list[str] = []
    warnings: list[str] = []
    seen_hashes: dict[str, str] = {}

    for flat_index, frame in enumerate(ordered_frames(manifest)):
        path = _resolve(root, frame["path"])
        if not path.exists():
            errors.append(f"missing frame: {frame['path']}")
            continue
        with Image.open(path) as im:
            rgba = im.convert("RGBA")
            width, height = rgba.size
            bbox = _alpha_bbox(rgba)

        if (width, height) != (expected_w, expected_h):
            errors.append(
                f"{frame['path']}: {width}x{height}, expected "
                f"{expected_w}x{expected_h}"
            )

        if bbox:
            opaque_w = bbox[2] - bbox[0]
            opaque_h = bbox[3] - bbox[1]
            opaque_area = opaque_w * opaque_h
        else:
            opaque_w = opaque_h = opaque_area = 0
            errors.append(f"{frame['path']}: fully transparent frame")

        padding_pct = 100.0 * (1.0 - opaque_area / max(1, width * height))
        if padding_pct > warning_padding:
            warnings.append(
                f"{frame['path']}: transparent padding {padding_pct:.1f}%"
            )

        digest = _sha256(path)
        if digest in seen_hashes:
            warnings.append(
                f"{frame['path']}: duplicate bytes of {seen_hashes[digest]}"
            )
        else:
            seen_hashes[digest] = frame["path"]

        result_frames.append(
            AuditFrame(
                index=flat_index,
                state=frame["state"],
                state_index=frame["state_index"],
                path=frame["path"],
                width=width,
                height=height,
                alpha_bbox=list(bbox) if bbox else None,
                opaque_width=opaque_w,
                opaque_height=opaque_h,
                transparent_padding_percent=round(padding_pct, 3),
                sha256=digest,
            )
        )

    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "arcont-sprite-audit",
        "manifest": str(manifest_path),
        "expected_canvas": [expected_w, expected_h],
        "anchor": manifest["anchor"],
        "frame_count": len(result_frames),
        "errors": errors,
        "warnings": warnings,
        "frames": [asdict(item) for item in result_frames],
        "passed": not errors,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return report


def pack(
    manifest_path: Path,
    output_dir: Path,
    cell_width: int,
    cell_height: int,
    columns: int,
    rows: int,
    colors: int | None,
) -> dict:
    Image = _pillow()
    manifest = _load_manifest(manifest_path)
    root = manifest_path.parent
    frames = ordered_frames(manifest)
    layout = page_layout(len(frames), columns, rows)
    page_count = math.ceil(len(frames) / (columns * rows)) if frames else 0
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = [
        Image.new(
            "RGBA",
            (cell_width * columns, cell_height * rows),
            (0, 0, 0, 0),
        )
        for _ in range(page_count)
    ]

    frame_records: list[dict] = []
    for frame, slot in zip(frames, layout):
        source = _resolve(root, frame["path"])
        with Image.open(source) as im:
            rgba = im.convert("RGBA")
            if rgba.size != (cell_width, cell_height):
                rgba = rgba.resize(
                    (cell_width, cell_height),
                    Image.Resampling.LANCZOS,
                )
        x = slot["column"] * cell_width
        y = slot["row"] * cell_height
        pages[slot["page"]].alpha_composite(rgba, (x, y))
        frame_records.append(
            {
                **frame,
                **slot,
                "region": [x, y, cell_width, cell_height],
            }
        )

    page_records: list[dict] = []
    for page_index, page in enumerate(pages):
        target = output_dir / f"atlas_{page_index:02d}.png"
        if colors:
            quantized = page.quantize(
                colors=colors,
                method=Image.Quantize.FASTOCTREE,
                dither=Image.Dither.NONE,
            )
            quantized.save(target, optimize=True)
        else:
            page.save(target, optimize=True)
        page_records.append(
            {
                "page": page_index,
                "path": target.name,
                "size": [page.width, page.height],
                "sha256": _sha256(target),
                "bytes": target.stat().st_size,
            }
        )

    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": "arcont-sprite-atlas",
        "source_manifest": str(manifest_path),
        "cell": [cell_width, cell_height],
        "grid": [columns, rows],
        "page_count": page_count,
        "frame_count": len(frames),
        "pages": page_records,
        "frames": frame_records,
    }
    (output_dir / "atlas_manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit separated 2D frames and build deterministic atlases."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    audit_cmd = sub.add_parser("audit", help="audit PNG frame set")
    audit_cmd.add_argument("manifest", type=Path)
    audit_cmd.add_argument("--output", type=Path)

    pack_cmd = sub.add_parser("pack", help="pack deterministic PNG atlas pages")
    pack_cmd.add_argument("manifest", type=Path)
    pack_cmd.add_argument("--output-dir", type=Path, required=True)
    pack_cmd.add_argument("--cell", default="256x256")
    pack_cmd.add_argument("--grid", default="4x4")
    pack_cmd.add_argument("--colors", type=int)

    return parser


def _parse_pair(value: str, flag: str) -> tuple[int, int]:
    try:
        left, right = value.lower().split("x", 1)
        a, b = int(left), int(right)
    except Exception as exc:
        raise SystemExit(f"{flag} must be WIDTHxHEIGHT") from exc
    if a <= 0 or b <= 0:
        raise SystemExit(f"{flag} values must be positive")
    return a, b


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "audit":
        report = audit(args.manifest, args.output)
        return 0 if report["passed"] else 2

    cell_w, cell_h = _parse_pair(args.cell, "--cell")
    cols, rows = _parse_pair(args.grid, "--grid")
    if args.colors is not None and not 2 <= args.colors <= 256:
        raise SystemExit("--colors must be in [2, 256]")
    result = pack(
        args.manifest,
        args.output_dir,
        cell_w,
        cell_h,
        cols,
        rows,
        args.colors,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
