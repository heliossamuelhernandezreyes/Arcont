import unittest

from tools.agent_diagnosis import DiagnosisError, diagnose, select_candidate, validate_policy


def policy():
    return {
        "protocol": "arcont-agent-diagnosis-policy",
        "version": 1,
        "id": "fixture_policy",
        "description": "generic spatial repair fixture",
        "hypotheses": [
            {
                "id": "oversized_nearby_collider",
                "code": "collider_height_out_of_range",
                "summary": "Nearby collidable object exceeds the accepted height.",
                "priority": 100,
                "when": [
                    {"left": {"$evidence": "/signals/cover_low"}, "op": "equals", "right": False},
                    {"left": {"$evidence": "/signals/vault_state"}, "op": "not-equals", "right": "vault"},
                ],
                "candidate": {
                    "source": "/world/objects",
                    "filters": [
                        {"left": {"$candidate": "/collision"}, "op": "equals", "right": True},
                        {"left": {"$candidate": "/type"}, "op": "equals", "right": "box"},
                    ],
                    "nearest_xz_to": "/observations/position",
                    "position_pointer": "/position",
                    "max_distance": 4.0,
                    "stable_patch_prefix": "/map/authoring/objects",
                },
                "require": [
                    {"left": {"$candidate": "/size/1"}, "op": "gt", "right": {"$evidence": "/limits/max_height"}},
                ],
                "details": {
                    "object_id": {"$candidate": "/id"},
                    "observed_height": {"$candidate": "/size/1"},
                    "accepted_height": {"$evidence": "/baseline/height"},
                },
                "repair_plan": {
                    "id": "repair_spatial_collider",
                    "goal": "Restore the diagnosed collider to its accepted geometry.",
                    "capability": "map-forge.editor.control",
                    "inspect_request": {
                        "protocol_version": 1,
                        "operation": "inspect",
                        "map_id": {"$evidence": "/context/map_id"},
                    },
                    "repair_request": {
                        "protocol_version": 1,
                        "operation": "patch",
                        "map_id": {"$evidence": "/context/map_id"},
                        "if_revision": {"$from": "inspect_target", "pointer": "/result/revision"},
                        "dry_run": False,
                        "patch": [
                            {
                                "op": "test",
                                "path": {"$candidate_path": "/size/1"},
                                "value": {"$candidate": "/size/1"},
                            },
                            {
                                "op": "replace",
                                "path": {"$candidate_path": "/size/1"},
                                "value": {"$evidence": "/baseline/height"},
                            },
                            {
                                "op": "replace",
                                "path": {"$candidate_path": "/position/1"},
                                "value": {"$evidence": "/baseline/center_y"},
                            },
                        ],
                    },
                    "expect": [
                        {"pointer": "/result/committed", "op": "equals", "value": True}
                    ],
                },
            }
        ],
    }


def evidence():
    return {
        "signals": {"cover_low": False, "vault_state": "free"},
        "observations": {"position": [-5.05, 0.0, 100.7]},
        "context": {"map_id": "arena"},
        "limits": {"max_height": 1.35},
        "baseline": {"height": 1.14, "center_y": 0.57},
        "world": {
            "objects": [
                {
                    "id": "far_box",
                    "type": "box",
                    "collision": True,
                    "position": [5.0, 0.9, 100.0],
                    "size": [4.0, 2.2, 0.5],
                },
                {
                    "id": "near_box",
                    "type": "box",
                    "collision": True,
                    "position": [-4.7, 0.85, 100.0],
                    "size": [4.0, 1.7, 0.56],
                },
                {
                    "id": "near_visual_only",
                    "type": "box",
                    "collision": False,
                    "position": [-5.0, 0.9, 100.5],
                    "size": [4.0, 2.5, 0.1],
                },
            ]
        },
    }


class AgentDiagnosisTests(unittest.TestCase):
    def test_selects_nearest_eligible_candidate_and_compiles_safe_plan(self):
        report = diagnose(policy(), evidence())
        self.assertTrue(report["ok"])
        self.assertTrue(report["matched"])
        hypothesis = report["hypothesis"]
        self.assertEqual(hypothesis["candidate"]["id"], "near_box")
        self.assertEqual(hypothesis["details"]["observed_height"], 1.7)
        plan = hypothesis["repair_plan"]
        self.assertEqual(plan["capability_allowlist"], ["map-forge.editor.control"])
        self.assertTrue(plan["permissions"]["project_write"])
        request = plan["steps"][1]["request"]
        self.assertEqual(request["if_revision"], {"$from": "inspect_target", "pointer": "/result/revision"})
        self.assertEqual(request["patch"][0]["path"], "/map/authoring/objects/@near_box/size/1")
        self.assertEqual(request["patch"][0]["value"], 1.7)
        self.assertEqual(request["patch"][1]["value"], 1.14)
        self.assertEqual(request["patch"][2]["path"], "/map/authoring/objects/@near_box/position/1")

    def test_no_match_does_not_invent_repair(self):
        data = evidence()
        data["signals"]["cover_low"] = True
        report = diagnose(policy(), data)
        self.assertTrue(report["ok"])
        self.assertFalse(report["matched"])
        self.assertEqual(report["status"], "no-match")
        self.assertNotIn("hypothesis", report)

    def test_candidate_must_satisfy_required_numeric_evidence(self):
        data = evidence()
        data["world"]["objects"][1]["size"][1] = 1.2
        report = diagnose(policy(), data)
        self.assertTrue(report["ok"])
        self.assertFalse(report["matched"])

    def test_spatial_tie_is_rejected_instead_of_guessing(self):
        data = evidence()
        data["observations"]["position"] = [0.0, 0.0, 0.0]
        data["world"]["objects"] = [
            {"id": "left", "type": "box", "collision": True, "position": [-1.0, 0.8, 0.0], "size": [1, 2, 1]},
            {"id": "right", "type": "box", "collision": True, "position": [1.0, 0.8, 0.0], "size": [1, 2, 1]},
        ]
        report = diagnose(policy(), data)
        self.assertTrue(report["ok"])
        self.assertFalse(report["matched"])
        self.assertIn("ambiguous", report["evaluations"][0]["candidate_error"])

    def test_equal_priority_hypotheses_are_ambiguous(self):
        p = policy()
        duplicate = dict(p["hypotheses"][0])
        duplicate["id"] = "second_hypothesis"
        duplicate["code"] = "second_code"
        duplicate["repair_plan"] = dict(duplicate["repair_plan"])
        duplicate["repair_plan"]["id"] = "second_repair"
        p["hypotheses"].append(duplicate)
        report = diagnose(p, evidence())
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "ambiguous")
        self.assertEqual(len(report["candidate_hypotheses"]), 2)

    def test_higher_priority_hypothesis_wins_deterministically(self):
        p = policy()
        duplicate = dict(p["hypotheses"][0])
        duplicate["id"] = "higher"
        duplicate["code"] = "higher_code"
        duplicate["priority"] = 200
        duplicate["repair_plan"] = dict(duplicate["repair_plan"])
        duplicate["repair_plan"]["id"] = "higher_repair"
        p["hypotheses"].append(duplicate)
        report = diagnose(p, evidence())
        self.assertTrue(report["ok"])
        self.assertEqual(report["hypothesis"]["id"], "higher")

    def test_selector_rejects_candidate_outside_max_distance(self):
        p = policy()["hypotheses"][0]["candidate"]
        data = evidence()
        data["observations"]["position"] = [100.0, 0.0, 100.0]
        with self.assertRaises(DiagnosisError):
            select_candidate(p, data)

    def test_policy_rejects_duplicate_hypothesis_ids(self):
        p = policy()
        p["hypotheses"].append(dict(p["hypotheses"][0]))
        with self.assertRaises(DiagnosisError):
            validate_policy(p)


if __name__ == "__main__":
    unittest.main()
