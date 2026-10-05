import binascii
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import png_sprite_audit as module


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, rect, alpha=255):
    x0, y0, x1, y1 = rect
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            if x0 <= x <= x1 and y0 <= y <= y1:
                rows.extend((120, 80, 40, alpha))
            else:
                rows.extend((0, 0, 0, 0))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    data = (
        module.PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(rows)))
        + _chunk(b"IEND", b"")
    )
    path.write_bytes(data)


class PngSpriteAuditTests(unittest.TestCase):
    def _manifest(self, root: Path, frames):
        payload = {
            "schema_version": 1,
            "quality_gates": {
                "max_baseline_drift_px": 2,
                "max_pivot_drift_px": 2,
                "max_visual_height_drift_pct": 4,
                "transparent_padding_warning_pct": 95,
            },
            "characters": {
                "hero": {
                    "canvas": [64, 64],
                    "baseline_y": 55,
                    "pivot": [32, 55],
                    "states": {"run": frames},
                }
            },
        }
        path = root / "manifest.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_consistent_frames_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index in (1, 2, 3):
                write_rgba_png(root / f"run_{index:02d}.png", 64, 64, (20, 20, 43, 55))
            frames = [
                {"path": f"run_{index:02d}.png", "pivot": [32, 55]}
                for index in (1, 2, 3)
            ]
            code, result = module.audit(self._manifest(root, frames), root)
            self.assertEqual(code, 0, result)
            self.assertTrue(result["ok"])
            self.assertFalse(result["errors"])

    def test_baseline_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_rgba_png(root / "run_01.png", 64, 64, (20, 20, 43, 59))
            code, result = module.audit(
                self._manifest(root, [{"path": "run_01.png", "pivot": [32, 55]}]), root
            )
            self.assertEqual(code, 1)
            self.assertTrue(any("baseline drift" in error for error in result["errors"]))

    def test_pivot_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_rgba_png(root / "run_01.png", 64, 64, (20, 20, 43, 55))
            code, result = module.audit(
                self._manifest(root, [{"path": "run_01.png", "pivot": [36, 55]}]), root
            )
            self.assertEqual(code, 1)
            self.assertTrue(any("pivot drift" in error for error in result["errors"]))

    def test_visual_height_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_rgba_png(root / "run_01.png", 64, 64, (20, 20, 43, 55))
            write_rgba_png(root / "run_02.png", 64, 64, (20, 10, 43, 55))
            write_rgba_png(root / "run_03.png", 64, 64, (20, 20, 43, 55))
            frames = [
                {"path": f"run_{index:02d}.png", "pivot": [32, 55]}
                for index in (1, 2, 3)
            ]
            code, result = module.audit(self._manifest(root, frames), root)
            self.assertEqual(code, 1)
            self.assertTrue(any("visual height drift" in error for error in result["errors"]))

    def test_transparent_frame_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_rgba_png(root / "run_01.png", 64, 64, (0, 0, -1, -1))
            code, result = module.audit(
                self._manifest(root, [{"path": "run_01.png", "pivot": [32, 55]}]), root
            )
            self.assertEqual(code, 1)
            self.assertTrue(any("no visible pixels" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
