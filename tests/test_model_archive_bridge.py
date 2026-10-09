"""Safe no-network game-owned staging using the new explicit-write Bridge boundary."""
from __future__ import annotations
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.arcont_bridge import BridgeError, handle_request
from test_model_forge_camera import sample_glb

ROOT = Path(__file__).resolve().parents[1]

class ArchiveStageBridgeTests(unittest.TestCase):
    def setUp(self):
        self.workspace=tempfile.TemporaryDirectory()
        self.game=Path(self.workspace.name)/"godot_game"
        self.game.mkdir()
        self.source=self.game/"kit.zip"
        with zipfile.ZipFile(self.source,"w") as z:
            z.writestr("License.txt","Creative Commons CC0 1.0")
            z.writestr("Models/GLB format/machine.glb",sample_glb())
            z.writestr("Models/GLB format/Textures/colormap.png",b"\x89PNG\r\n\x1a\n"+b"palette")
        self.args={
            "archive_path":"kit.zip",
            "catalog_path":"assets/catalog/kenney/factory-kit.asset.json",
            "expected_sha256":hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "prefix":"Models/GLB format",
            "models":["machine.glb"],
            "destination":"assets/vendor/real_kit"
        }

    def tearDown(self):
        self.workspace.cleanup()

    def request(self,*,allow_write,args=None):
        return handle_request(ROOT,self.game,{
            "protocol":"arcont-bridge","version":1,"request_id":"zip-stage-test",
            "operation":"model.archive.stage","arguments":args or self.args
        },allow_project_write=allow_write)

    def test_bridge_discovery_includes_explicit_writer(self):
        report=handle_request(ROOT,self.game,{
            "protocol":"arcont-bridge","version":1,"request_id":"discover",
            "operation":"discover","arguments":{}
        },allow_project_write=False)
        self.assertIn("model.archive.stage",report["result"]["bridge"]["operations"])
        self.assertIn("model.archive.stage",report["result"]["bridge"]["mutation_boundary"]["direct_writer_operations"])

    def test_denied_without_explicit_project_write(self):
        with self.assertRaisesRegex(BridgeError,"allow-project-write"):
            self.request(allow_write=False)
        self.assertFalse((self.game/"assets/vendor/real_kit").exists())

    def test_stage_actual_file_closure_with_opt_in(self):
        reply=self.request(allow_write=True)
        self.assertTrue(reply["ok"])
        self.assertTrue(reply["result"]["write_performed"])
        self.assertEqual(reply["result"]["bundle"]["delivery_status"],"source-closure-and-geometry-validated")
        destination=self.game/"assets/vendor/real_kit"
        self.assertTrue((destination/"machine.glb").is_file())
        self.assertTrue((destination/"Textures/colormap.png").is_file())
        self.assertTrue((destination/"SOURCE_LICENSE.txt").is_file())
        with self.assertRaisesRegex(ValueError,"overwrite"):
            self.request(allow_write=True)

    def test_source_digest_cannot_silently_change(self):
        self.args["expected_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"sha256 mismatch"):
            self.request(allow_write=True)
        self.assertFalse((self.game/"assets/vendor/real_kit").exists())

    def test_cannot_stage_archive_from_outside_game(self):
        self.args["archive_path"]="../untrusted/kit.zip"
        with self.assertRaises(ValueError):
            self.request(allow_write=True)

    def test_cannot_load_fake_catalog_outside_arcont_vault(self):
        self.args["catalog_path"]="tests/test_model_forge_camera.py"
        with self.assertRaisesRegex(BridgeError,"Asset Vault"):
            self.request(allow_write=True)

    def test_unknown_arguments_refused(self):
        self.args["shell"]="rm -rf /"
        with self.assertRaises(BridgeError):
            self.request(allow_write=True)

if __name__=="__main__":
    unittest.main()
