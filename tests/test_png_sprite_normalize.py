import binascii
import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import png_sprite_normalize as module


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, rect, rgba=(120, 80, 40, 255)):
    x0, y0, x1, y1 = rect
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(rgba if x0 <= x <= x1 and y0 <= y <= y1 else (0, 0, 0, 0))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        module.PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw)))
        + _chunk(b"IEND", b"")
    )


class PngSpriteNormalizeTests(unittest.TestCase):
    def test_normalize_baseline_canvas_and_height(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src.png"
            write_rgba_png(src, 64, 80, (20, 10, 43, 69))
            data, report = module.normalize_frame(
                src,
                target_canvas=(384, 384),
                target_pivot=(192, 350),
                target_visual_height=240,
                alpha_threshold=8,
                padding_px=4,
                source_anchor_x="alpha_center",
            )
            out = root / "out.png"
            out.write_bytes(data)
            width, height, rows = module._decode_rgba_png(out)
            bbox = module._visible_bbox(rows, width, height, 8)
            self.assertEqual((width, height), (384, 384))
            self.assertEqual(bbox[3], 350)
            self.assertLessEqual(abs((bbox[3] - bbox[1] + 1) - 240), 2)
            self.assertTrue(report["content_sha256"])

    def test_explicit_horizontal_pivot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src.png"
            write_rgba_png(src, 80, 80, (10, 20, 39, 69))
            data, report = module.normalize_frame(
                src,
                target_canvas=(384, 384),
                target_pivot=(192, 350),
                target_visual_height=200,
                source_pivot=(30, 69),
                padding_px=4,
            )
            self.assertEqual(report["source_pivot"], [30, 69])
            out = root / "out.png"
            out.write_bytes(data)
            width, height, rows = module._decode_rgba_png(out)
            bbox = module._visible_bbox(rows, width, height, 8)
            self.assertEqual(bbox[3], 350)

    def test_transparent_source_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src.png"
            write_rgba_png(src, 32, 32, (0, 0, -1, -1))
            with self.assertRaisesRegex(ValueError, "no visible pixels"):
                module.normalize_frame(
                    src,
                    target_canvas=(64, 64),
                    target_pivot=(32, 55),
                    target_visual_height=40,
                )

    def test_crop_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src.png"
            write_rgba_png(src, 64, 64, (0, 5, 63, 55))
            with self.assertRaisesRegex(ValueError, "would crop"):
                module.normalize_frame(
                    src,
                    target_canvas=(64, 64),
                    target_pivot=(32, 55),
                    target_visual_height=50,
                    padding_px=4,
                )

    def test_plan_is_transactional_and_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "master.png"
            write_rgba_png(src, 64, 80, (20, 10, 43, 69))
            plan = {
                "schema_version": 1,
                "defaults": {
                    "target_canvas": [384, 384],
                    "target_pivot": [192, 350],
                    "target_visual_height": 240,
                    "source_anchor_x": "alpha_center",
                },
                "frames": [
                    {"input": "master.png", "output": "norm/a.png"},
                    {"input": "master.png", "output": "norm/b.png"},
                ],
            }
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            code, result = module.run_plan(plan_path, root)
            self.assertEqual(code, 0, result)
            self.assertEqual(
                hashlib.sha256((root / "norm/a.png").read_bytes()).hexdigest(),
                hashlib.sha256((root / "norm/b.png").read_bytes()).hexdigest(),
            )

            bad = dict(plan)
            bad["frames"] = [
                {"input": "master.png", "output": "norm/c.png"},
                {"input": "missing.png", "output": "norm/d.png"},
            ]
            plan_path.write_text(json.dumps(bad), encoding="utf-8")
            code, result = module.run_plan(plan_path, root)
            self.assertEqual(code, 1)
            self.assertFalse((root / "norm/c.png").exists())


if __name__ == "__main__":
    unittest.main()
