import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.godot_structured_editing import (
    StructuredError,
    _function_spans,
    _script_function_replace,
    _script_inspect,
    _validate_scene_change,
    _validate_script_source,
    execute,
)
from tools.project_bootstrap_control import bootstrap


def project_intent():
    return {
        "protocol": "arcont-project-intent",
        "version": 1,
        "project_id": "structured_fixture",
        "title": "Structured Fixture",
        "genre": "third-person action",
        "targets": ["Windows"],
        "asset_policy": {
            "user_assets": True,
            "public_assets": False,
            "commercial_use_required": True,
            "allow_network_discovery": False,
        },
    }


class StructuredGodotEditingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "game"
        self.project.mkdir()
        bootstrap(self.project, project_intent(), "godot-3d-minimal")

    def tearDown(self):
        self.tmp.cleanup()

    def test_function_parser_finds_top_level_functions(self):
        source = (
            "extends Node\n\n"
            "func alpha():\n"
            "    pass\n\n"
            "func beta(value):\n"
            "    if value:\n"
            "        return 1\n"
            "    return 0\n"
        )
        spans = _function_spans(source)
        self.assertEqual(set(spans), {"alpha", "beta"})
        self.assertLess(spans["alpha"][0], spans["beta"][0])

    def test_script_safety_rejects_privileged_editor_host_and_network_apis(self):
        refused = [
            "@tool\nextends Node\n",
            "extends Node\nfunc x():\n    OS.execute('x', [])\n",
            "extends Node\nfunc x():\n    FileAccess.open('user://x', FileAccess.WRITE)\n",
            "extends Node\nfunc x():\n    var r = HTTPRequest.new()\n",
            "extends Node\nfunc x():\n    ProjectSettings.save()\n",
        ]
        for source in refused:
            with self.subTest(source=source):
                with self.assertRaises(StructuredError):
                    _validate_script_source(source)

    @patch("tools.godot_structured_editing._validate_script_with_godot")
    def test_script_create_is_revisioned_and_inspectable(self, validate):
        validate.return_value = {"ok": True, "evidence": ".arcont/test"}
        report = execute(
            self.project,
            {
                "protocol_version": 1,
                "operation": "script.create",
                "path": "scripts/player.gd",
                "if_revision": None,
                "source": "extends CharacterBody3D\n\nfunc _physics_process(_delta):\n    velocity = Vector3.ZERO\n",
            },
        )
        self.assertTrue(report["ok"])
        revision = report["result"]["revision"]
        self.assertEqual(len(revision), 64)

        inspected = _script_inspect(self.project, "scripts/player.gd")
        self.assertEqual(inspected["result"]["revision"], revision)
        self.assertEqual(inspected["result"]["extends"], "CharacterBody3D")
        self.assertEqual(inspected["result"]["functions"][0]["name"], "_physics_process")

        with self.assertRaises(StructuredError):
            execute(
                self.project,
                {
                    "protocol_version": 1,
                    "operation": "script.replace",
                    "path": "scripts/player.gd",
                    "if_revision": "0" * 64,
                    "source": "extends CharacterBody3D\n",
                },
            )

    @patch("tools.godot_structured_editing._validate_script_with_godot")
    def test_function_replace_changes_only_selected_function(self, validate):
        validate.return_value = {"ok": True, "evidence": ".arcont/test"}
        created = execute(
            self.project,
            {
                "protocol_version": 1,
                "operation": "script.create",
                "path": "scripts/player.gd",
                "if_revision": None,
                "source": (
                    "extends CharacterBody3D\n\n"
                    "func helper():\n"
                    "    return 3\n\n"
                    "func _physics_process(_delta):\n"
                    "    velocity = Vector3.ZERO\n"
                ),
            },
        )
        before = created["result"]["revision"]
        result = _script_function_replace(
            self.project,
            "scripts/player.gd",
            "_physics_process",
            "func _physics_process(_delta):\n    velocity = Vector3(0, 0, -1)\n",
            before,
        )
        self.assertTrue(result["ok"])
        source = (self.project / "scripts/player.gd").read_text()
        self.assertIn("func helper():\n    return 3", source)
        self.assertIn("velocity = Vector3(0, 0, -1)", source)

    @patch("tools.godot_structured_editing._validate_script_with_godot")
    def test_invalid_script_validation_rolls_back(self, validate):
        validate.side_effect = [
            {"ok": True, "evidence": ".arcont/create"},
            {"ok": False, "evidence": ".arcont/fail"},
        ]
        created = execute(
            self.project,
            {
                "protocol_version": 1,
                "operation": "script.create",
                "path": "scripts/player.gd",
                "if_revision": None,
                "source": "extends Node\n\nfunc ok():\n    pass\n",
            },
        )
        original = (self.project / "scripts/player.gd").read_bytes()
        with self.assertRaises(StructuredError):
            execute(
                self.project,
                {
                    "protocol_version": 1,
                    "operation": "script.replace",
                    "path": "scripts/player.gd",
                    "if_revision": created["result"]["revision"],
                    "source": "extends Node\n\nfunc broken():\n    pass\n",
                },
            )
        self.assertEqual((self.project / "scripts/player.gd").read_bytes(), original)

    def test_scene_change_rejects_privileged_node_type_and_unsafe_paths(self):
        with self.assertRaises(StructuredError):
            _validate_scene_change(
                {"op": "add", "parent": ".", "name": "Fetcher", "type": "HTTPRequest"}
            )
        with self.assertRaises(StructuredError):
            _validate_scene_change(
                {"op": "remove", "path": "../Outside"}
            )

    @patch("tools.godot_structured_editing._validate_script_with_godot")
    def test_script_commit_refuses_concurrent_revision_change(self, validate):
        validate.return_value = {"ok": True, "evidence": ".arcont/create"}
        created = execute(
            self.project,
            {
                "protocol_version": 1,
                "operation": "script.create",
                "path": "scripts/player.gd",
                "if_revision": None,
                "source": "extends Node\n\nfunc original():\n    pass\n",
            },
        )
        target = self.project / "scripts/player.gd"

        def concurrent_validation(_project, _relative):
            target.write_text("extends Node\n\nfunc concurrent():\n    pass\n", encoding="utf-8")
            return {"ok": True, "evidence": ".arcont/concurrent"}

        validate.side_effect = concurrent_validation
        with self.assertRaises(StructuredError):
            execute(
                self.project,
                {
                    "protocol_version": 1,
                    "operation": "script.replace",
                    "path": "scripts/player.gd",
                    "if_revision": created["result"]["revision"],
                    "source": "extends Node\n\nfunc arcont_edit():\n    pass\n",
                },
            )
        self.assertIn("func concurrent()", target.read_text())

    @patch("tools.godot_structured_editing._run_godot_script")
    def test_scene_commit_refuses_concurrent_revision_change(self, runner):
        target = self.project / "scenes/main.tscn"
        before = __import__("hashlib").sha256(target.read_bytes()).hexdigest()

        def fake_runner(project, _source, request, timeout=120):
            staged = project / request["output"].removeprefix("res://")
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text("[gd_scene format=3]\n\n[node name=\"Staged\" type=\"Node3D\"]\n")
            target.write_text("[gd_scene format=3]\n\n[node name=\"Concurrent\" type=\"Node3D\"]\n")
            return {"ok": True, "result": {"ok": True}, "evidence": ".arcont/fake"}

        runner.side_effect = fake_runner
        with self.assertRaises(StructuredError):
            execute(
                self.project,
                {
                    "protocol_version": 1,
                    "operation": "scene.edit",
                    "scene": "scenes/main.tscn",
                    "if_revision": before,
                    "changes": [{"op": "rename", "path": ".", "name": "Arcont"}],
                },
            )
        self.assertIn('name="Concurrent"', target.read_text())

    def test_scene_set_cannot_bypass_dedicated_script_attachment(self):
        with self.assertRaises(StructuredError):
            _validate_scene_change(
                {
                    "op": "set",
                    "path": "Player",
                    "property": "script",
                    "value": {"$type": "Resource", "path": "res://scripts/player.gd"},
                }
            )
        with self.assertRaises(StructuredError):
            _validate_scene_change(
                {"op": "set", "path": "Player", "property": "owner", "value": None}
            )

    def test_scene_attach_rejects_privileged_existing_script_before_engine_run(self):
        scripts = self.project / "scripts"
        scripts.mkdir(exist_ok=True)
        (scripts / "unsafe.gd").write_text("@tool\nextends Node\n", encoding="utf-8")
        revision = __import__("hashlib").sha256((self.project / "scenes/main.tscn").read_bytes()).hexdigest()
        with self.assertRaises(StructuredError):
            execute(
                self.project,
                {
                    "protocol_version": 1,
                    "operation": "scene.edit",
                    "scene": "scenes/main.tscn",
                    "if_revision": revision,
                    "changes": [
                        {"op": "add", "parent": ".", "name": "Unsafe", "type": "Node"},
                        {"op": "attach_script", "path": "Unsafe", "script": "res://scripts/unsafe.gd"},
                    ],
                },
            )

    def test_resource_editor_refuses_script_resource_types(self):
        with self.assertRaises(StructuredError):
            execute(
                self.project,
                {
                    "protocol_version": 1,
                    "operation": "resource.edit",
                    "resource": "resources/unsafe.tres",
                    "if_revision": None,
                    "resource_type": "GDScript",
                    "changes": [{"op": "set", "property": "source_code", "value": "extends Node"}],
                },
            )

    @patch("tools.godot_structured_editing._validate_script_with_godot")
    def test_script_path_cannot_escape_through_symlink(self, validate):
        validate.return_value = {"ok": True}
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        scripts = self.project / "scripts"
        scripts.rmdir()
        scripts.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(StructuredError):
            execute(
                self.project,
                {
                    "protocol_version": 1,
                    "operation": "script.create",
                    "path": "scripts/escape.gd",
                    "if_revision": None,
                    "source": "extends Node\n",
                },
            )
        self.assertEqual(list(outside.iterdir()), [])

    def test_capabilities_expose_bounded_structured_surface(self):
        report = execute(self.project, {"protocol_version": 1, "operation": "capabilities"})
        self.assertTrue(report["ok"])
        self.assertFalse(report["arbitrary_shell"])
        self.assertFalse(report["raw_arbitrary_file_write"])
        self.assertTrue(report["revision_checked"])
        self.assertTrue(report["rollback_on_validation_failure"])


if __name__ == "__main__":
    unittest.main()
