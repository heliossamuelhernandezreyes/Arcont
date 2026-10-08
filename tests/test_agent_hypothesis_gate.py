import unittest

from tools.agent_execution_loop import validate_plan
from tools.agent_hypothesis_gate import ProposalError, compile_policy, evaluate_proposal, validate_proposal


def proposal():
    return {
        "protocol": "arcont-agent-hypothesis-proposal",
        "version": 1,
        "id": "novel_cover_fault",
        "goal": "Restore the nearby collider to the accepted low-cover geometry.",
        "provenance": {
            "author_type": "model",
            "model": "test-model",
            "note": "Fixture proposal generated from failed interaction evidence.",
        },
        "hypothesis": {
            "id": "oversized_nearby_box",
            "code": "nearby_collider_too_tall",
            "summary": "A nearby collidable box is taller than the accepted interaction range.",
            "priority": 100,
            "when": [
                {"left": {"$evidence": "/signals/interaction_ok"}, "op": "equals", "right": False},
                {"left": {"$evidence": "/signals/state"}, "op": "not-equals", "right": "vault"},
            ],
            "candidate": {
                "source": "/world/objects",
                "filters": [
                    {"left": {"$candidate": "/type"}, "op": "equals", "right": "box"},
                    {"left": {"$candidate": "/collision"}, "op": "equals", "right": True},
                ],
                "nearest_xz_to": "/observations/position",
                "position_pointer": "/position",
                "max_distance": 4.0,
            },
            "require": [
                {"left": {"$candidate": "/size/1"}, "op": "gt", "right": {"$evidence": "/limits/max_height"}},
            ],
            "details": {
                "object_id": {"$candidate": "/id"},
                "observed_height": {"$candidate": "/size/1"},
                "accepted_height": {"$evidence": "/baseline/height"},
            },
            "repair": {
                "kind": "map-forge-stable-object-patch",
                "map_id": {"$evidence": "/context/map_id"},
                "changes": [
                    {"candidate_pointer": "/size/1", "value": {"$evidence": "/baseline/height"}},
                    {"candidate_pointer": "/position/1", "value": {"$evidence": "/baseline/center_y"}},
                ],
            },
        },
    }


def evidence():
    return {
        "signals": {"interaction_ok": False, "state": "free"},
        "observations": {"position": [-5.0, 0.0, 100.7]},
        "context": {"map_id": "arena"},
        "limits": {"max_height": 1.35},
        "baseline": {"height": 1.14, "center_y": 0.57},
        "world": {
            "objects": [
                {
                    "id": "near_box",
                    "type": "box",
                    "collision": True,
                    "position": [-4.7, 0.85, 100.0],
                    "size": [4.0, 1.7, 0.56],
                },
                {
                    "id": "far_box",
                    "type": "box",
                    "collision": True,
                    "position": [20.0, 0.85, 100.0],
                    "size": [4.0, 2.0, 0.56],
                },
            ]
        },
    }


class AgentHypothesisGateTests(unittest.TestCase):
    def test_model_proposal_compiles_to_revision_checked_execution_plan(self):
        report = evaluate_proposal(proposal(), evidence())
        self.assertTrue(report["ok"])
        self.assertEqual(report["provenance"]["author_type"], "model")
        diagnosis = report["diagnosis"]
        self.assertTrue(diagnosis["matched"])
        hypothesis = diagnosis["hypothesis"]
        self.assertEqual(hypothesis["candidate"]["id"], "near_box")
        plan = hypothesis["repair_plan"]
        validate_plan(plan, {"map-forge.editor.control"})
        self.assertEqual(plan["capability_allowlist"], ["map-forge.editor.control"])
        request = plan["steps"][1]["request"]
        self.assertEqual(request["if_revision"], {"$from": "inspect_target", "pointer": "/result/revision"})
        self.assertEqual(
            [item["op"] for item in request["patch"]],
            ["test", "replace", "test", "replace"],
        )
        self.assertEqual(request["patch"][0]["path"], "/map/authoring/objects/@near_box/size/1")
        self.assertEqual(request["patch"][1]["value"], 1.14)
        self.assertEqual(request["patch"][2]["path"], "/map/authoring/objects/@near_box/position/1")
        self.assertEqual(request["patch"][3]["value"], 0.57)

    def test_no_match_produces_no_selected_repair(self):
        data = evidence()
        data["signals"]["interaction_ok"] = True
        report = evaluate_proposal(proposal(), data)
        self.assertTrue(report["ok"])
        self.assertFalse(report["diagnosis"]["matched"])
        self.assertNotIn("hypothesis", report["diagnosis"])

    def test_rejects_arbitrary_repair_kind(self):
        p = proposal()
        p["hypothesis"]["repair"]["kind"] = "shell"
        with self.assertRaises(ProposalError):
            validate_proposal(p)

    def test_rejects_candidate_derived_replacement_value(self):
        p = proposal()
        p["hypothesis"]["repair"]["changes"][0]["value"] = {"$candidate": "/size/0"}
        with self.assertRaises(ProposalError):
            validate_proposal(p)

    def test_rejects_stable_id_or_parent_path_injection(self):
        for pointer in ("/@evil/size/1", "/../size/1"):
            p = proposal()
            p["hypothesis"]["repair"]["changes"][0]["candidate_pointer"] = pointer
            with self.assertRaises(ProposalError):
                validate_proposal(p)

    def test_rejects_proposal_without_evidence_precondition(self):
        p = proposal()
        p["hypothesis"]["when"] = []
        with self.assertRaises(ProposalError):
            validate_proposal(p)

    def test_rejects_repair_without_candidate_requirement(self):
        p = proposal()
        p["hypothesis"]["require"] = []
        with self.assertRaises(ProposalError):
            validate_proposal(p)

    def test_rejects_candidate_outside_distance_bound(self):
        data = evidence()
        data["observations"]["position"] = [100.0, 0.0, 100.0]
        report = evaluate_proposal(proposal(), data)
        self.assertTrue(report["ok"])
        self.assertFalse(report["diagnosis"]["matched"])
        self.assertIn("max_distance", report["diagnosis"]["evaluations"][0]["candidate_error"])

    def test_compiled_policy_cannot_select_arbitrary_writer(self):
        p = compile_policy(proposal())
        self.assertEqual(p["hypotheses"][0]["repair_plan"]["capability"], "map-forge.editor.control")
        self.assertEqual(
            p["hypotheses"][0]["candidate"]["stable_patch_prefix"],
            "/map/authoring/objects",
        )


if __name__ == "__main__":
    unittest.main()
