import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.production_control import execute, respond


class ProductionControlTests(unittest.TestCase):
    def test_capabilities_are_non_mutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = execute(Path(tmp), {"protocol_version": 1, "operation": "capabilities"})
            self.assertTrue(result["ok"])
            self.assertFalse(result["write_performed"])
            self.assertIn("assets.stage", result["mutating_operations"])
            self.assertIn("bundle.materialize", result["mutating_operations"])

    def test_assets_stage_is_explicitly_reported_as_write(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
            "tools.production_control.stage", return_value={"bundle_directory": "assets/candidates/x"}
        ) as stage_mock:
            request = {
                "protocol_version": 1,
                "operation": "assets.stage",
                "plan": {"version": 1},
                "destination": "assets/candidates",
            }
            result = execute(Path(tmp), request)
            self.assertTrue(result["ok"])
            self.assertTrue(result["write_performed"])
            stage_mock.assert_called_once()

    def test_performance_summary_remains_read_only(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
            "tools.production_control.summarize", return_value={"p95_ms": 16.0}
        ):
            result = execute(
                Path(tmp),
                {"protocol_version": 1, "operation": "performance.summarize", "record": {"scope": "fixture"}},
            )
            self.assertTrue(result["ok"])
            self.assertFalse(result["write_performed"])
            self.assertEqual(result["result"]["p95_ms"], 16.0)

    def test_bundle_materialize_requires_boolean_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = respond(
                Path(tmp),
                {
                    "protocol_version": 1,
                    "operation": "bundle.materialize",
                    "source": ".arcont/runs/x",
                    "destination": "assets/x",
                    "files": {"scene.tscn": "a" * 64},
                    "replace": "yes",
                },
            )
            self.assertFalse(result["ok"])
            self.assertFalse(result["write_performed"])

    def test_unknown_operation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = respond(Path(tmp), {"protocol_version": 1, "operation": "magic"})
            self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
