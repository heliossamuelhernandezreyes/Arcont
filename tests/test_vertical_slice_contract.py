"""Regression tests for the engine-neutral ARCONT vertical-slice design validator."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from vertical_slice_contract import validate_contract  # noqa: E402


class MissionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads(
            (ROOT / "templates/mission_slice/mission_contract.example.json").read_text(encoding="utf-8")
        )

    def check_failure(self, modify, expected):
        candidate = copy.deepcopy(self.example)
        modify(candidate)
        errors = validate_contract(candidate)
        self.assertTrue(any(expected in e for e in errors), f"expected {expected!r}, got {errors}")

    def test_valid_reusable_example(self):
        self.assertEqual(validate_contract(self.example), [])

    def test_duplicate_cross_collection_id(self):
        self.check_failure(lambda x: x["anchors"][0].update(id="start_zone"), "duplicate global id")

    def test_phase_requires_completed_objective(self):
        self.check_failure(lambda x: x["transitions"][0]["condition"].update(objective_ids=[]), "condition.event and condition.objective_ids required")

    def test_unknown_role(self):
        self.check_failure(lambda x: x["encounters"][0]["units"][0].update(role="phantom"), "unknown enemy role")

    def test_outside_zone_spawn(self):
        self.check_failure(lambda x: x["anchors"][0].update(position=[0, 0, -13]), "outside declared zone")

    def test_enemy_overcap(self):
        self.check_failure(lambda x: x["encounters"][0]["units"][0].update(count=8), "units exceed")

    def test_no_route_to_victory(self):
        self.check_failure(lambda x: x.update(transitions=[]), "no route to victory")

    def test_broken_phase_reference(self):
        self.check_failure(lambda x: x["phases"][0].update(objective_ids=["nonexistent"]), "unknown reference")

    def test_bad_world_bounds(self):
        self.check_failure(lambda x: x["map"]["bounds"].update(width=-40), "map.bounds")

    def test_missing_qa_evidence_contract(self):
        self.check_failure(lambda x: x.update(qa_gates=[]), "at least one gate")

    def test_required_objective_cannot_be_skipped(self):
        self.check_failure(lambda x: x["transitions"][0]["condition"].update(objective_ids=["complete_extraction"]), "not part of source phase")


if __name__ == "__main__":
    unittest.main()
