import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.map_forge_control import ControlError, Editor, apply_patch, decode, get, revision


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.state = {"map": {"id": "arena", "routes": [{"id": "west", "width": 6}, {"id": "east", "width": 7}]}, "physical": None}

    def test_stable_selector_survives_reordering(self):
        self.state["map"]["routes"].reverse()
        result = apply_patch(self.state, [{"op": "replace", "path": "/map/routes/@west/width", "value": 9}])
        self.assertEqual(get(result, "/map/routes/@west/width"), 9)
        self.assertEqual(get(self.state, "/map/routes/@west/width"), 6)

    def test_failed_batch_does_not_mutate_original(self):
        before = copy.deepcopy(self.state)
        with self.assertRaises(ControlError):
            apply_patch(self.state, [{"op": "replace", "path": "/map/routes/0/width", "value": 9}, {"op": "test", "path": "/map/id", "value": "wrong"}])
        self.assertEqual(self.state, before)

    def test_add_remove_copy_move(self):
        result = apply_patch(self.state, [{"op": "copy", "from": "/map/routes/0", "path": "/map/copied"}, {"op": "move", "from": "/map/copied", "path": "/map/moved"}, {"op": "add", "path": "/map/routes/-", "value": {"id": "north", "width": 3}}, {"op": "remove", "path": "/map/moved"}])
        self.assertEqual(len(result["map"]["routes"]), 3)
        self.assertNotIn("moved", result["map"])

    def test_escaped_pointer(self):
        result = apply_patch(self.state, [{"op": "add", "path": "/map/a~1b~0c", "value": 4}])
        self.assertEqual(get(result, "/map/a~1b~0c"), 4)

    def test_duplicate_selector_is_rejected(self):
        self.state["map"]["routes"].append({"id": "west"})
        with self.assertRaises(ControlError):
            get(self.state, "/map/routes/@west")

    def test_move_parent_into_child_is_rejected(self):
        with self.assertRaises(ControlError):
            apply_patch(self.state, [{"op": "move", "from": "/map", "path": "/map/child"}])

    def test_nonfinite_and_duplicate_json_are_rejected(self):
        for value in ['{"x":NaN}', '{"x":1,"x":2}']:
            with self.assertRaises(ControlError):
                decode(value)


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "tools").mkdir()
        (self.root / "tools" / "adapter.py").write_text('import sys,json\nr=json.load(sys.stdin); m=r["state"]["map"]; ok=m.get("bounds",{}).get("width",0)>0\nprint(json.dumps({"ok":ok,"errors":[] if ok else ["width"]}))\nsys.exit(0 if ok else 1)\n')
        (self.root / "map-forge.authoring.json").write_text(json.dumps({"protocol_version": 1, "adapter_command": [__import__("sys").executable, "tools/adapter.py"]}))
        self.editor = Editor(self.root)
        self.state = {"map": {"id": "arena", "bounds": {"width": 20}, "extension": {"anything": [1, 2, 3]}}, "physical": None}

    def tearDown(self):
        self.temporary.cleanup()

    def create(self):
        return self.editor.execute({"protocol_version": 1, "operation": "create", "map_id": "arena", "state": self.state, "dry_run": False})

    def test_create_dry_run_does_not_write(self):
        result = self.editor.execute({"protocol_version": 1, "operation": "create", "map_id": "arena", "state": self.state})
        self.assertTrue(result["ok"])
        self.assertFalse((self.root / "maps/arena.json").exists())

    def test_create_inspect_patch_and_restore(self):
        created = self.create()
        modified = self.editor.execute({"protocol_version": 1, "operation": "patch", "map_id": "arena", "if_revision": created["revision"], "patch": [{"op": "replace", "path": "/map/bounds/width", "value": 50}], "dry_run": False})
        self.assertEqual(self.editor.read("arena")["map"]["bounds"]["width"], 50)
        restored = self.editor.execute({"protocol_version": 1, "operation": "restore", "map_id": "arena", "if_revision": modified["revision"], "restore_revision": created["revision"], "dry_run": False})
        self.assertEqual(restored["revision"], created["revision"])

    def test_stale_revision_cannot_overwrite(self):
        self.create()
        with self.assertRaises(ControlError):
            self.editor.execute({"protocol_version": 1, "operation": "replace", "map_id": "arena", "if_revision": "stale", "state": self.state, "dry_run": False})
        self.assertEqual(self.editor.read("arena"), self.state)

    def test_invalid_map_is_not_committed(self):
        created = self.create()
        result = self.editor.execute({"protocol_version": 1, "operation": "patch", "map_id": "arena", "if_revision": created["revision"], "patch": [{"op": "replace", "path": "/map/bounds/width", "value": -1}], "dry_run": False})
        self.assertFalse(result["ok"])
        self.assertEqual(revision(self.editor.read("arena")), created["revision"])

    def test_arbitrary_extensions_are_editable(self):
        created = self.create()
        result = self.editor.execute({"protocol_version": 1, "operation": "patch", "map_id": "arena", "if_revision": created["revision"], "patch": [{"op": "add", "path": "/map/extension/custom_system", "value": {"weather": "snow", "custom_mesh": [3, 2, 1]}}]})
        self.assertTrue(result["ok"])

    def test_path_traversal_and_symlinks_are_rejected(self):
        with self.assertRaises(ControlError):
            self.editor.paths("../arena")
        with tempfile.TemporaryDirectory() as other:
            (self.root / "maps").symlink_to(other, target_is_directory=True)
            with self.assertRaises(ControlError):
                self.editor.paths("arena")

    def test_existing_create_is_rejected(self):
        self.create()
        with self.assertRaises(ControlError):
            self.create()

    def test_both_map_and_physical_are_revised(self):
        self.state["physical"] = {"map_id": "arena", "custom": {"river": True}}
        result = self.create()
        self.assertTrue((self.root / "maps/physical/arena.json").exists())
        self.assertEqual(result["revision"], revision(self.editor.read("arena")))

    def test_revision_ignores_object_key_order(self):
        self.assertEqual(revision({"a": 1, "b": 2}), revision({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
