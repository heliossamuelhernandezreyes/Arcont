import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.development_session import SessionError, create, execute_one, inspect
from tools.project_bootstrap_control import bootstrap


def intent():
    return {
        "protocol": "arcont-project-intent",
        "version": 1,
        "project_id": "session_fixture",
        "title": "Session Fixture",
        "genre": "third-person action",
        "targets": ["Windows"],
        "asset_policy": {
            "user_assets": True,
            "public_assets": False,
            "commercial_use_required": True,
            "allow_network_discovery": False
        }
    }


def spec():
    return {
        "id": "build_game",
        "goal": "Create a tiny playable game through bounded ARCONT milestones.",
        "capability_allowlist": ["godot.structured.control"],
        "permissions": {"project_write": True},
        "budgets": {
            "max_plan_runs": 3,
            "max_execution_steps": 12,
            "max_write_steps": 6,
            "max_failed_runs": 2
        },
        "milestones": [
            {
                "id": "movement",
                "goal": "Create basic movement.",
                "acceptance": ["Player moves under a validated input action."]
            },
            {
                "id": "runtime",
                "goal": "Verify runtime behavior.",
                "acceptance": ["A runtime check passes."]
            }
        ]
    }


def plan(plan_id="movement_plan"):
    return {
        "protocol": "arcont-agent-plan",
        "version": 1,
        "id": plan_id,
        "goal": "Bounded movement milestone work.",
        "permissions": {"project_write": True},
        "capability_allowlist": ["godot.structured.control"],
        "steps": [
            {"id": "inventory", "kind": "inspect-project", "max_files": 1000}
        ]
    }


class DevelopmentSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "game"
        self.project.mkdir()
        bootstrap(self.project, intent(), "godot-3d-minimal")

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_persists_revisioned_milestones_and_budgets(self):
        report = create(self.project, {"spec": spec()})
        self.assertTrue(report["ok"])
        state = report["result"]["session"]
        self.assertEqual(len(state["revision"]), 64)
        self.assertEqual(state["milestones"][0]["status"], "active")
        self.assertEqual(state["milestones"][1]["status"], "pending")
        self.assertEqual(report["result"]["remaining"]["plan_runs"], 3)
        self.assertTrue((self.project / ".arcont/development-sessions/build_game/session.json").is_file())

    def test_inspect_detects_project_intent_drift_without_mutating_session(self):
        created = create(self.project, {"spec": spec()})
        before = created["result"]["session"]["revision"]
        project_intent = json.loads((self.project / "project.intent.json").read_text())
        project_intent["title"] = "Changed"
        (self.project / "project.intent.json").write_text(json.dumps(project_intent))
        report = inspect(self.project, {"session_id": "build_game"})
        self.assertFalse(report["result"]["environment"]["intent_matches"])
        self.assertEqual(report["result"]["session"]["revision"], before)

    @patch("tools.development_session.execute_plan")
    def test_successful_plan_can_complete_milestone_and_activate_next(self, run):
        run.return_value = {
            "ok": True,
            "status": "completed",
            "steps_completed": 1,
            "write_steps": 0,
            "plan_sha256": "a" * 64,
            "steps": []
        }
        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        report = execute_one(
            self.project,
            {
                "session_id": "build_game",
                "if_session_revision": state["revision"],
                "milestone_id": "movement",
                "plan": plan(),
                "complete_milestone": True,
                "completion_note": "Plan expectations passed."
            }
        )
        self.assertTrue(report["ok"])
        new_state = report["result"]["session"]
        self.assertEqual(new_state["milestones"][0]["status"], "completed")
        self.assertEqual(new_state["milestones"][1]["status"], "active")
        self.assertEqual(new_state["counters"]["milestones_completed"], 1)
        self.assertNotEqual(new_state["revision"], state["revision"])
        receipt = self.project / report["result"]["run"]["receipt"]
        self.assertTrue(receipt.is_file())
        self.assertEqual(len(report["result"]["run"]["receipt_sha256"]), 64)

    @patch("tools.development_session.execute_plan")
    def test_failed_plan_is_recorded_and_never_auto_retried(self, run):
        run.return_value = {
            "ok": False,
            "status": "stopped",
            "failed_step": "build",
            "steps_completed": 1,
            "write_steps": 1,
            "steps": []
        }
        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        report = execute_one(
            self.project,
            {
                "session_id": "build_game",
                "if_session_revision": state["revision"],
                "milestone_id": "movement",
                "plan": plan(),
                "complete_milestone": True
            }
        )
        self.assertFalse(report["ok"])
        self.assertEqual(run.call_count, 1)
        new_state = report["result"]["session"]
        self.assertEqual(new_state["milestones"][0]["status"], "active")
        self.assertEqual(new_state["counters"]["failed_runs"], 1)
        self.assertEqual(report["result"]["next_action"], "review-failure-and-submit-new-plan")

    @patch("tools.development_session.execute_plan")
    def test_failure_budget_pauses_session(self, run):
        cfg = spec()
        cfg["budgets"]["max_failed_runs"] = 1
        run.return_value = {
            "ok": False,
            "status": "stopped",
            "failed_step": "build",
            "steps_completed": 1,
            "write_steps": 0,
            "steps": []
        }
        created = create(self.project, {"spec": cfg})
        state = created["result"]["session"]
        report = execute_one(
            self.project,
            {
                "session_id": "build_game",
                "if_session_revision": state["revision"],
                "milestone_id": "movement",
                "plan": plan(),
                "complete_milestone": False
            }
        )
        self.assertEqual(report["result"]["session"]["status"], "paused")
        self.assertEqual(report["result"]["session"]["stop_reason"], "failed-run-budget-exhausted")
        self.assertEqual(report["result"]["next_action"], "session-paused")

    @patch("tools.development_session.execute_plan")
    def test_stale_session_revision_is_refused_before_execution(self, run):
        created = create(self.project, {"spec": spec()})
        with self.assertRaises(SessionError):
            execute_one(
                self.project,
                {
                    "session_id": "build_game",
                    "if_session_revision": "0" * 64,
                    "milestone_id": "movement",
                    "plan": plan(),
                    "complete_milestone": False
                }
            )
        run.assert_not_called()

    @patch("tools.development_session.execute_plan")
    def test_plan_cannot_escape_session_capability_allowlist(self, run):
        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        bad = plan()
        bad["capability_allowlist"] = ["public-asset.control"]
        with self.assertRaises((SessionError, ValueError)):
            execute_one(
                self.project,
                {
                    "session_id": "build_game",
                    "if_session_revision": state["revision"],
                    "milestone_id": "movement",
                    "plan": bad,
                    "complete_milestone": False
                }
            )
        run.assert_not_called()

    def test_session_state_symlink_is_not_accepted(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        session_root = self.project / ".arcont/development-sessions"
        session_root.parent.mkdir(parents=True, exist_ok=True)
        session_root.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(SessionError):
            create(self.project, {"spec": spec()})


if __name__ == "__main__":
    unittest.main()
