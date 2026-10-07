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
            {
                "id": "inventory",
                "kind": "inspect-project",
                "max_files": 1000,
                "expect": [{"pointer": "/project/engine", "op": "equals", "value": "godot"}]
            }
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
        self.assertEqual(len(state["toolchain_sha256"]), 64)
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
            "steps": [{
                "id": "inventory",
                "ok": True,
                "write_performed": False,
                "expectations": [{"ok": True}]
            }]
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
                "completion_note": "Plan expectations passed.",
                "completion_evidence": [{"criterion_index": 0, "step_ids": ["inventory"]}]
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
                "complete_milestone": True,
                "completion_evidence": [{"criterion_index": 0, "step_ids": ["inventory"]}]
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
    @patch("tools.development_session._toolchain_sha")
    def test_toolchain_drift_is_refused_before_execution(self, toolchain, run):
        toolchain.side_effect = ["a" * 64, "b" * 64]
        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        with self.assertRaises(SessionError):
            execute_one(
                self.project,
                {
                    "session_id": "build_game",
                    "if_session_revision": state["revision"],
                    "milestone_id": "movement",
                    "plan": plan(),
                    "complete_milestone": False
                }
            )
        run.assert_not_called()

    @patch("tools.development_session.execute_plan")
    @patch("tools.development_session._toolchain_sha")
    def test_environment_drift_during_run_pauses_without_completing_milestone(self, toolchain, run):
        toolchain.side_effect = ["a" * 64, "a" * 64, "b" * 64]
        run.return_value = {
            "ok": True,
            "status": "completed",
            "steps_completed": 1,
            "write_steps": 0,
            "steps": [{
                "id": "inventory",
                "ok": True,
                "write_performed": False,
                "expectations": [{"ok": True}]
            }]
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
                "completion_evidence": [{"criterion_index": 0, "step_ids": ["inventory"]}]
            }
        )
        self.assertFalse(report["ok"])
        new_state = report["result"]["session"]
        self.assertEqual(new_state["status"], "paused")
        self.assertEqual(new_state["stop_reason"], "environment-changed-during-run")
        self.assertEqual(new_state["milestones"][0]["status"], "active")
        self.assertEqual(new_state["counters"]["milestones_completed"], 0)

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

    @patch("tools.development_session.execute_plan")
    def test_unresolved_pending_run_blocks_automatic_retry(self, run):
        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        pending = self.project / ".arcont/development-sessions/build_game/pending-run.json"
        pending.write_text(
            json.dumps({
                "protocol": "arcont-development-session-pending",
                "version": 1,
                "session_id": "build_game",
                "run_id": "run-001-interrupted",
                "milestone_id": "movement",
                "session_revision_before": state["revision"],
                "plan_id": "movement_plan",
                "plan_sha256": __import__("tools.agent_execution_loop", fromlist=["canonical_sha256"]).canonical_sha256(plan()),
            }),
            encoding="utf-8",
        )
        with self.assertRaises(SessionError):
            execute_one(
                self.project,
                {
                    "session_id": "build_game",
                    "if_session_revision": state["revision"],
                    "milestone_id": "movement",
                    "plan": plan(),
                    "complete_milestone": False,
                },
            )
        run.assert_not_called()

    @patch("tools.development_session.execute_plan")
    def test_pending_marker_symlink_is_refused(self, run):
        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        session_dir = self.project / ".arcont/development-sessions/build_game"
        outside = Path(self.tmp.name) / "pending.json"
        outside.write_text("{}", encoding="utf-8")
        (session_dir / "pending-run.json").symlink_to(outside)
        with self.assertRaises(SessionError):
            execute_one(
                self.project,
                {
                    "session_id": "build_game",
                    "if_session_revision": state["revision"],
                    "milestone_id": "movement",
                    "plan": plan(),
                    "complete_milestone": False,
                },
            )
        run.assert_not_called()

    def test_completed_pending_is_cleared_only_when_receipt_hash_matches(self):
        import hashlib
        from tools.development_session import _atomic_json, _reconcile_completed_pending, _state_revision
        from tools.agent_execution_loop import canonical_sha256

        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        session_dir = self.project / ".arcont/development-sessions/build_game"
        run_id = "run-001-committed"
        receipt_rel = ".arcont/development-sessions/build_game/runs/run-001-committed.json"
        receipt_path = self.project / receipt_rel
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text('{"ok":true}\n', encoding="utf-8")
        plan_hash = canonical_sha256(plan())
        state["history"].append({
            "run_id": run_id,
            "milestone_id": "movement",
            "ok": True,
            "status": "completed",
            "plan_id": "movement_plan",
            "plan_sha256": plan_hash,
            "receipt": receipt_rel,
            "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            "steps_completed": 1,
            "write_steps": 0,
            "failed_step": None,
        })
        state["revision"] = _state_revision(state)
        _atomic_json(session_dir / "session.json", state)
        pending = {
            "protocol": "arcont-development-session-pending",
            "version": 1,
            "session_id": "build_game",
            "run_id": run_id,
            "milestone_id": "movement",
            "session_revision_before": created["result"]["session"]["revision"],
            "plan_id": "movement_plan",
            "plan_sha256": plan_hash,
        }
        _atomic_json(session_dir / "pending-run.json", pending)
        self.assertIsNone(_reconcile_completed_pending(self.project, state))
        self.assertFalse((session_dir / "pending-run.json").exists())

        # Recreate the marker, corrupt the receipt, and require fail-closed behavior.
        _atomic_json(session_dir / "pending-run.json", pending)
        receipt_path.write_text('{"ok":false}\n', encoding="utf-8")
        with self.assertRaises(SessionError):
            _reconcile_completed_pending(self.project, state)
        self.assertTrue((session_dir / "pending-run.json").is_file())

    @patch("tools.development_session.execute_plan")
    def test_completion_requires_evidence_for_every_acceptance_criterion(self, run):
        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        with self.assertRaises(SessionError):
            execute_one(
                self.project,
                {
                    "session_id": "build_game",
                    "if_session_revision": state["revision"],
                    "milestone_id": "movement",
                    "plan": plan(),
                    "complete_milestone": True,
                    "completion_evidence": [],
                },
            )
        run.assert_not_called()

    @patch("tools.development_session.execute_plan")
    def test_completion_evidence_must_have_machine_signal(self, run):
        run.return_value = {
            "ok": True,
            "status": "completed",
            "steps_completed": 1,
            "write_steps": 0,
            "steps": [{
                "id": "inventory",
                "ok": True,
                "write_performed": False,
                "expectations": []
            }]
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
                "completion_evidence": [{"criterion_index": 0, "step_ids": ["inventory"]}],
            },
        )
        self.assertFalse(report["ok"])
        self.assertEqual(report["result"]["session"]["milestones"][0]["status"], "active")
        self.assertEqual(
            report["result"]["next_action"],
            "review-completion-evidence-and-submit-new-plan",
        )

    def test_session_directory_symlink_is_not_accepted(self):
        created = create(self.project, {"spec": spec()})
        session_dir = self.project / ".arcont/development-sessions/build_game"
        state_copy = json.loads((session_dir / "session.json").read_text())
        outside = Path(self.tmp.name) / "outside-session"
        outside.mkdir()
        (outside / "session.json").write_text(json.dumps(state_copy))
        for child in list(session_dir.iterdir()):
            child.unlink()
        session_dir.rmdir()
        session_dir.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(SessionError):
            inspect(self.project, {"session_id": "build_game"})

    def test_session_lock_symlink_is_not_accepted(self):
        created = create(self.project, {"spec": spec()})
        state = created["result"]["session"]
        session_dir = self.project / ".arcont/development-sessions/build_game"
        outside = Path(self.tmp.name) / "outside-lock"
        outside.write_text("lock")
        (session_dir / "session.lock").symlink_to(outside)
        with self.assertRaises(SessionError):
            execute_one(
                self.project,
                {
                    "session_id": "build_game",
                    "if_session_revision": state["revision"],
                    "milestone_id": "movement",
                    "plan": plan(),
                    "complete_milestone": False
                }
            )

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
