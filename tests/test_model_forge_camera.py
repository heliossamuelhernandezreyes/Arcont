"""Source archive closure, malicious ZIP and real camera-space regression tests."""
from __future__ import annotations
import hashlib
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.model_forge_pack_select import stage_archive
from tools.visual_camera_diagnostics import analyze_shot


def sample_glb(uri: str = "Textures/colormap.png") -> bytes:
    doc = {
        "asset": {"version": "2.0", "generator": "ARCONT negative fixture"},
        "images": [{"uri": uri}],
        "accessors": [{"count": 3, "type": "VEC3"}, {"count": 3, "type": "SCALAR", "componentType": 5123}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "nodes": [{"mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0
    }
    payload = json.dumps(doc, separators=(",", ":")).encode()
    payload += b" " * ((-len(payload)) % 4)
    return b"glTF" + struct.pack("<II", 2, len(payload) + 20) + struct.pack("<II", len(payload), 0x4E4F534A) + payload


RECORD = {
    "id": "ARC-ASSET-KENNEY-696C714A33FF63A1",
    "source": {"provider": "Kenney"},
    "review": {"license_verified": True},
    "license": {"name": "CC0-1.0", "commercial_use": True, "modification": True},
}


class SourceClosureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.zip"
        self.target = self.root / "game-vendor"
        self.entries = {
            "License.txt": b"Creative Commons CC0 1.0 Public Domain",
            "Models/GLB format/machine.glb": sample_glb(),
            "Models/GLB format/Textures/colormap.png": b"\x89PNG\r\n\x1a\n" + b"original-colour-atlas",
            "Models/GLB format/unused.glb": sample_glb(),
        }
        self.create_zip()

    def tearDown(self):
        self.tmp.cleanup()

    def create_zip(self):
        with zipfile.ZipFile(self.source, "w", zipfile.ZIP_DEFLATED) as z:
            for k, v in self.entries.items():
                z.writestr(k, v)

    def stage(self, **opts):
        return stage_archive(self.source, record=opts.get("record", RECORD),
                             expected_sha256=opts.get("sha", hashlib.sha256(self.source.read_bytes()).hexdigest()),
                             model_members=opts.get("models", ["machine.glb"]),
                             prefix="Models/GLB format",
                             destination=opts.get("destination", self.target))

    def test_kenney_shared_palette_imported_and_unused_models_excluded(self):
        manifest = self.stage()
        self.assertTrue((self.target / "machine.glb").is_file())
        self.assertTrue((self.target / "Textures/colormap.png").is_file())
        self.assertFalse((self.target / "unused.glb").exists())
        self.assertEqual(set(manifest["files"]), {"machine.glb", "Textures/colormap.png"})
        self.assertEqual(manifest["models"]["machine.glb"]["dependencies"],
                         ["Textures/colormap.png", "machine.glb"])
        self.assertEqual(manifest["models"]["machine.glb"]["inspection"]["triangles"], 1)
        self.assertEqual(manifest["android_runtime_status"], "needs_measurement")
        self.assertTrue((self.target / "PROVENANCE.json").is_file())

    def test_unchanged_destination_cannot_be_overwritten(self):
        self.stage()
        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.stage()

    def test_missing_palette_rejected_with_no_published_bundle(self):
        self.entries.pop("Models/GLB format/Textures/colormap.png")
        self.create_zip()
        with self.assertRaisesRegex(ValueError, "missing glTF external"):
            self.stage()
        self.assertFalse(self.target.exists())

    def test_missing_digest_and_wrong_digest_fail(self):
        for hash_value in ("", "0"*64):
            with self.subTest(hash_value=hash_value):
                with self.assertRaisesRegex(ValueError, "sha256|SHA-256"):
                    self.stage(sha=hash_value)
        self.assertFalse(self.target.exists())

    def test_archive_traversal_denied(self):
        self.entries["../../shell.sh"] = b"bad"
        self.create_zip()
        with self.assertRaises(ValueError):
            self.stage()
        self.assertFalse(self.target.exists())

    def test_uri_traversal_denied(self):
        self.entries["Models/GLB format/machine.glb"] = sample_glb("../steal.png")
        self.create_zip()
        with self.assertRaisesRegex(ValueError, "unsafe"):
            self.stage()
        self.assertFalse(self.target.exists())

    def test_remote_texture_uri_denied(self):
        self.entries["Models/GLB format/machine.glb"] = sample_glb("https://evil.example/p.png")
        self.create_zip()
        with self.assertRaises(ValueError):
            self.stage()
        self.assertFalse(self.target.exists())

    def test_license_gate_is_fail_closed(self):
        bad = dict(RECORD, review={"license_verified": False})
        with self.assertRaises(SystemExit):
            self.stage(record=bad)
        self.assertFalse(self.target.exists())

    def test_cc_by_license_text_cannot_impersonate_cc0(self):
        self.entries["License.txt"] = b"Creative Commons Attribution 4.0 International, attribution is required"
        self.create_zip()
        with self.assertRaisesRegex(ValueError, "does not identify CC0"):
            self.stage()
        self.assertFalse(self.target.exists())

    def test_archive_dependency_cannot_replace_provenance_receipt(self):
        self.entries["Models/GLB format/machine.glb"] = sample_glb("PROVENANCE.json")
        self.entries["Models/GLB format/PROVENANCE.json"] = b"malicious counterfeit receipt"
        self.create_zip()
        with self.assertRaisesRegex(ValueError, "reserved receipt filename"):
            self.stage()
        self.assertFalse(self.target.exists())

    def test_malformed_gltf_asset_metadata_rejected_cleanly(self):
        raw = sample_glb()
        parsed = {
            "asset": None,
            "images": [{"uri": "Textures/colormap.png"}],
            "accessors": [{"count": 3, "type": "VEC3"}, {"count": 3, "type": "SCALAR", "componentType": 5123}],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        }
        payload=json.dumps(parsed).encode()
        payload += b" " * ((-len(payload)) % 4)
        self.entries["Models/GLB format/machine.glb"] = (
            b"glTF" + struct.pack("<II", 2, len(payload) + 20)
            + struct.pack("<II", len(payload), 0x4E4F534A) + payload
        )
        self.create_zip()
        with self.assertRaisesRegex(ValueError, "invalid glTF asset version"):
            self.stage()
        self.assertFalse(self.target.exists())

    def test_zip_symlink_denied(self):
        with zipfile.ZipFile(self.source, "w") as z:
            for k,v in self.entries.items():
                if k == "Models/GLB format/Textures/colormap.png":
                    info = zipfile.ZipInfo(k)
                    info.create_system = 3
                    info.external_attr = (0o120777 << 16)
                    z.writestr(info, v)
                else:
                    z.writestr(k,v)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.stage()
        self.assertFalse(self.target.exists())


def shot() -> dict:
    return {
        "protocol": "arcont-camera-shot", "version": 1,
        "capture_source": "synthetic-test",
        "camera": {
            "position": [0.0, 1.0, 5.0],
            "target": [0.0, 1.0, 0.0],
            "up": [0.0, 1.0, 0.0],
            "fov_y_degrees": 70.0, "viewport": [1280, 720],
        },
        "objects": [
            {"id": "central_pillar", "center": [0.0,1.0,3.0], "size": [2.0,3.0,1.0], "role": "structure"},
            {"id": "enemy", "center": [0.0,1.0,0.0], "size": [0.8,1.7,0.5], "role": "enemy"},
            {"id": "offscreen", "center": [200.0,1.0,1.0], "size": [1.0,1.0,1.0], "role": "structure"},
            {"id": "behind_camera", "center": [0.0,1.0,10.0], "size": [1.0,1.0,1.0], "role": "structure"},
        ],
    }


class CameraDirectorTests(unittest.TestCase):
    def test_projected_pillar_blocks_reticle_and_enemy(self):
        report = analyze_shot(shot())
        self.assertTrue(report["ok"])
        self.assertEqual(report["summary"]["visible_aabb_projections"], 2)
        alerts = report["alerts"]
        self.assertTrue(any(a["kind"] == "large_screen_obstruction" and a["object_id"] == "central_pillar" for a in alerts))
        self.assertTrue(any(a["kind"] == "reticle_region_intersection" and a["object_id"] == "central_pillar" for a in alerts))
        self.assertTrue(any(a["kind"] == "possible_target_occlusion" and a["target_id"] == "enemy" and
                            a["depth_classification"] == "likely_depth_order" for a in alerts))
        self.assertFalse(report["engine_executed"])
        self.assertEqual(report["capture_source"], "synthetic-test")

    def test_camera_look_away_returns_no_obstruction(self):
        case=shot()
        case["camera"]["target"]=[0,1,10]
        report=analyze_shot(case)
        self.assertEqual(report["summary"]["visible_aabb_projections"], 1)
        self.assertFalse(any(alert["object_id"] == "central_pillar" for alert in report["alerts"]))
        self.assertTrue(any(alert["object_id"] == "behind_camera" for alert in report["alerts"]))

    def test_nonfinite_coordinate_rejected(self):
        case=shot()
        case["objects"][0]["center"][0]=float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            analyze_shot(case)

    def test_parallel_camera_up_rejected(self):
        case=shot()
        case["camera"]["up"]=[0,0,-1]
        with self.assertRaisesRegex(ValueError, "non-degenerate"):
            analyze_shot(case)

    def test_duplicate_asset_identifier_rejected(self):
        case=shot()
        case["objects"][1]["id"]="central_pillar"
        with self.assertRaisesRegex(ValueError, "repeated"):
            analyze_shot(case)

    def test_invalid_fov_rejected(self):
        case=shot()
        case["camera"]["fov_y_degrees"]=0
        with self.assertRaisesRegex(ValueError,"FOV"):
            analyze_shot(case)

    def test_spoofed_provenance_is_not_automatically_authenticated(self):
        case=shot()
        case["capture_source"]="native-godot"
        report=analyze_shot(case)
        self.assertTrue(any("independently verify" in item for item in report["limitations"]))


if __name__=="__main__":
    unittest.main()
