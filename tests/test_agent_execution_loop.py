import tempfile
import unittest
from pathlib import Path

from tools.agent_execution_loop import (
    evaluate_expectations,
    execute_plan,
    json_pointer,
    resolve_bindings,
    validate_plan,
)


class AgentExecutionLoopTests(unittest.TestCase):
    def registry(self):
        return {
            "schema_version": 1,
            "protocol": "arcont-agent-control",
            "capabilities": [
                {"id": "writer", "access": "external-project-write", "invocable": True},
                {"id": "other", "access": "external-project-write", "invocable": True},
            ],
        }

    def base_plan(self):
        return {
            "protocol": "arcont-agent-plan",
            "version": 1,
            "id": "fixture_plan",
            "goal": "exercise revision-aware execution",
            "permissions": {"project_write": True},
            "capability_allowlist": ["writer"],
            "steps": [
                {
                    "id": "inspect",
                    "kind": "invoke",
                    "capability": "writer",
                    "request": {"protocol_version": 1, "operation": "inspect"},
                    "expect": [{"pointer": "/result/revision", "op": "equals", "value": "abc"}],
                },
                {
                    "id": "patch",
                    "kind": "invoke",
                    "capability": "writer",
                    "request": {
                        "protocol_version": 1,
                        "operation": "patch",
                        "if_revision": {"$from": "inspect", "pointer": "/result/revision"},
                    },
                    "expect": [{"pointer": "/result/revision", "op": "equals", "value": "def"}],
                },
            ],
        }

    def test_json_pointer_and_binding_resolution(self):
        source = {"a": {"b/c": [{"value": 9}]}}
        self.assertEqual(json_pointer(source, "/a/b~1c/0/value"), 9)
        bound = resolve_bindings(
            {"revision": {"$from": "one", "pointer": "/result/revision"}},
            {"one": {"result": {"revision": "abc"}}},
            {"one"},
        )
        self.assertEqual(bound["revision"], "abc")
        with self.assertRaises(ValueError):
            resolve_bindings({"x": {"$from": "future", "pointer": "/x"}}, {}, set())

    def test_plan_requires_capability_allowlist(self):
        plan = self.base_plan()
        plan["steps"][0]["capability"] = "other"
        with self.assertRaises(ValueError):
            validate_plan(plan, {"writer", "other"})

    def test_execution_binds_prior_revision_and_completes(self):
        calls = []

        def invoke(root, capability, project, request, allow, timeout):
            calls.append(request)
            if request["operation"] == "inspect":
                return {"ok": True, "result": {"revision": "abc"}}
            self.assertEqual(request["if_revision"], "abc")
            return {"ok": True, "result": {"revision": "def", "committed": True}}

        with tempfile.TemporaryDirectory() as project_tmp, tempfile.TemporaryDirectory() as root_tmp:
            result = execute_plan(
                Path(root_tmp),
                Path(project_tmp),
                self.base_plan(),
                True,
                self.registry(),
                lambda project, max_files: {"ok": True},
                invoke,
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["steps_completed"], 2)
        self.assertEqual(calls[1]["if_revision"], "abc")
        self.assertEqual(result["write_steps"], 1)

    def test_expectation_failure_stops_following_steps(self):
        calls = []

        def invoke(root, capability, project, request, allow, timeout):
            calls.append(request["operation"])
            return {"ok": True, "result": {"revision": "wrong"}}

        with tempfile.TemporaryDirectory() as project_tmp, tempfile.TemporaryDirectory() as root_tmp:
            result = execute_plan(
                Path(root_tmp),
                Path(project_tmp),
                self.base_plan(),
                True,
                self.registry(),
                lambda project, max_files: {"ok": True},
                invoke,
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["failed_step"], "inspect")
        self.assertEqual(calls, ["inspect"])

    def test_plan_and_cli_both_must_authorize_write(self):
        with tempfile.TemporaryDirectory() as project_tmp, tempfile.TemporaryDirectory() as root_tmp:
            with self.assertRaises(PermissionError):
                execute_plan(
                    Path(root_tmp),
                    Path(project_tmp),
                    self.base_plan(),
                    False,
                    self.registry(),
                    lambda project, max_files: {"ok": True},
                    lambda *args: {"ok": True},
                )

    def test_read_only_project_inspection_plan_needs_no_write_permission(self):
        plan = {
            "protocol": "arcont-agent-plan",
            "version": 1,
            "id": "inspect_only",
            "goal": "inventory project",
            "permissions": {"project_write": False},
            "capability_allowlist": ["writer"],
            "steps": [
                {
                    "id": "inventory",
                    "kind": "inspect-project",
                    "max_files": 100,
                    "expect": [{"pointer": "/project/engine", "op": "equals", "value": "godot"}],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as project_tmp, tempfile.TemporaryDirectory() as root_tmp:
            result = execute_plan(
                Path(root_tmp),
                Path(project_tmp),
                plan,
                False,
                self.registry(),
                lambda project, max_files: {"ok": True, "project": {"engine": "godot"}},
                lambda *args: self.fail("invoke should not run"),
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["write_steps"], 0)

    def test_expectation_operators(self):
        output = {"ok": True, "value": 7, "empty": 0}
        checks = evaluate_expectations(output, [
            {"pointer": "/ok", "op": "truthy"},
            {"pointer": "/value", "op": "not-equals", "value": 8},
            {"pointer": "/empty", "op": "falsy"},
            {"pointer": "/value", "op": "exists"},
        ])
        self.assertTrue(all(item["ok"] for item in checks))


if __name__ == "__main__":
    unittest.main()
