import json
import tempfile
import unittest
from pathlib import Path

from tools.model_forge_control import execute, respond


class ModelForgeControlTests(unittest.TestCase):
    def model(self, root: Path) -> Path:
        path = root / "source.gltf"
        path.write_text(json.dumps({
            "asset": {"version": "2.0"},
            "accessors": [{"count": 9, "type": "VEC3"}],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
            "materials": [{}],
            "nodes": [],
        }), encoding="utf-8")
        return path

    def test_inspect_and_validate_are_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.model(root)
            inspected = execute(root, {"protocol_version": 1, "operation": "inspect", "model": "source.gltf"})
            self.assertTrue(inspected["ok"])
            self.assertFalse(inspected["write_performed"])
            self.assertEqual(inspected["result"]["triangles"], 3)

            checked = execute(root, {
                "protocol_version": 1,
                "operation": "validate",
                "model": "source.gltf",
                "profile": {"id": "mobile", "budgets": {"triangles_max": 2, "materials_max": 2}},
            })
            self.assertTrue(checked["ok"])
            self.assertFalse(checked["result"]["technical_passed"])

    def test_collision_recipe_is_inline_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.model(root)
            result = execute(root, {
                "protocol_version": 1,
                "operation": "collision.recipe",
                "model": "source.gltf",
                "mode": "convex",
            })
            self.assertFalse(result["write_performed"])
            self.assertEqual(result["result"]["mode"], "convex")
            self.assertTrue(result["result"]["game_validation_required"])

    def test_stage_creates_deterministic_project_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.model(root)
            result = execute(root, {
                "protocol_version": 1,
                "operation": "stage",
                "model": "source.gltf",
                "semantic_id": "environment.wall",
                "destination": "assets/candidates",
            })
            self.assertTrue(result["write_performed"])
            target = root / result["result"]["bundle_directory"]
            self.assertTrue((target / "asset.gltf").is_file())
            self.assertTrue((target / "asset.manifest.json").is_file())

    def test_escape_and_restage_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.model(root)
            bad = respond(root, {"protocol_version": 1, "operation": "inspect", "model": "../source.gltf"})
            self.assertFalse(bad["ok"])
            request = {
                "protocol_version": 1,
                "operation": "stage",
                "model": "source.gltf",
                "semantic_id": "prop.fixture",
                "destination": "assets/candidates",
            }
            self.assertTrue(execute(root, request)["ok"])
            again = respond(root, request)
            self.assertFalse(again["ok"])


if __name__ == "__main__":
    unittest.main()
