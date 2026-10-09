"""ARCONT read-only camera Bridge contracts, including project confinement."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

from tools.arcont_bridge import BridgeError, handle_request
from tools.visual_camera_diagnostics import analyze_shot

ROOT=Path(__file__).resolve().parents[1]

class CameraBridgeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory()
        self.project=Path(self.work.name)
        self.shot={
            "protocol":"arcont-camera-shot","version":1,
            "camera":{"position":[0,1,5],"target":[0,1,0],"up":[0,1,0],
                      "viewport":[1280,720],"fov_y_degrees":70},
            "objects":[{"id":"pillar","center":[0,1,3],"size":[2,3,1],"role":"structure"}]
        }
        (self.project/"shot.json").write_text(json.dumps(self.shot))

    def tearDown(self):
        self.work.cleanup()

    def call(self, operation, arguments):
        return handle_request(ROOT,self.project,{
            "protocol":"arcont-bridge","version":1,"request_id":"camera-readonly-test",
            "operation":operation,"arguments":arguments
        },allow_project_write=False)

    def test_discover_operation(self):
        reply=self.call("discover",{})
        self.assertIn("visual.camera.analyze",reply["result"]["bridge"]["operations"])

    def test_read_only_camera_report(self):
        before=(self.project/"shot.json").read_bytes()
        result=self.call("visual.camera.analyze",{"shot_path":"shot.json"})
        self.assertTrue(result["ok"])
        self.assertTrue(result["result"]["alerts"])
        self.assertFalse(result["result"]["writes_performed"])
        self.assertEqual((self.project/"shot.json").read_bytes(),before)
        self.assertEqual(result["result"]["shot_sha256"],analyze_shot(self.shot)["shot_sha256"])

    def test_parent_escape_refused(self):
        with self.assertRaises((ValueError,BridgeError)):
            self.call("visual.camera.analyze",{"shot_path":"../escaping-shot.json"})

    def test_unsupported_extra_arguments_refused(self):
        with self.assertRaises(BridgeError):
            self.call("visual.camera.analyze",{"shot_path":"shot.json","shell":"rm -rf"})

    def test_oversized_file_refused(self):
        (self.project/"oversized.json").write_bytes(b"x"*(2*1024*1024+1))
        with self.assertRaises(BridgeError):
            self.call("visual.camera.analyze",{"shot_path":"oversized.json"})

if __name__=="__main__":
    unittest.main()
