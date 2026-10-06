import copy
import unittest

from tools.playtest_contract import validate


class PlaytestContractTests(unittest.TestCase):
    def setUp(self):
        self.session = {"version": 1, "id": "route", "actor": "Actors/Explorer", "seed": 41,
                        "commands": [{"id": "entry", "frames": 120, "actions": {"forward": 1},
                                      "capture": "Cameras/Entrance", "expect": {"position": [0, 0, 8], "tolerance_m": 0.5}}]}

    def test_bounded_session_accepts_empty_input_for_waiting(self):
        self.session["commands"].append({"id": "wait", "frames": 30, "actions": {}})
        self.assertEqual(validate(self.session), [])

    def test_time_budgets_and_duplicate_checkpoints_are_rejected(self):
        self.session["commands"][0]["frames"] = 3600
        self.session["commands"].append(copy.deepcopy(self.session["commands"][0]))
        errors = validate(self.session)
        self.assertTrue(any("3600" in error for error in errors))
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_nonfinite_input_and_invalid_node_selectors_are_rejected(self):
        self.session["actor"] = "../Explorer"
        self.session["commands"][0]["capture"] = "res://camera"
        self.session["commands"][0]["actions"]["forward"] = float("nan")
        self.assertEqual(len(validate(self.session)), 3)

    def test_unknown_features_and_boolean_frame_counts_fail(self):
        self.session["commands"][0]["frames"] = True
        self.session["commands"][0]["teleport"] = [0, 0, 0]
        self.assertTrue(validate(self.session))
