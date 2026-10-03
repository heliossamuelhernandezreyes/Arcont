import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from road_network_contract import validate


class RoadNetworkContractTests(unittest.TestCase):
    def setUp(self):
        self.network = {"version": 1, "roads": [{"id": "avenue", "lanes": ["reverse", "forward"],
            "points": [{"id": "a", "position": [-20, 0, 0], "tangent": [1, 0, 0]},
                       {"id": "b", "position": [20, 8, 0], "tangent": [1, 0.1, 0]}]}]}

    def test_explicit_ramp_and_large_coordinates(self):
        self.network["roads"][0]["points"][1]["position"][0] = 100000
        self.assertEqual(validate(self.network), [])

    def test_identity_collisions_rejected(self):
        self.network["roads"][0]["points"][1]["id"] = "a"
        self.assertTrue(any("duplicate" in e for e in validate(self.network)))

    def test_nan_boolean_width_and_vertical_tangent(self):
        road = self.network["roads"][0]
        road["lane_width"] = True
        road["points"][0]["position"][0] = float("nan")
        road["points"][1]["tangent"] = [0, 1, 0]
        self.assertGreaterEqual(len(validate(self.network)), 3)

    def test_closed_chain_and_lane_order(self):
        road = self.network["roads"][0]
        road["closed"] = True
        self.assertTrue(validate(self.network))
        third = copy.deepcopy(road["points"][0])
        third["id"] = "c"
        third["position"] = [0, 0, 20]
        road["points"].append(third)
        self.assertFalse(validate(self.network))
        road["lanes"] = ["sideways"]
        self.assertTrue(validate(self.network))

    def test_malformed_source(self):
        for value in [None, {}, {"version": True, "roads": []}, {"version": 1, "roads": [None]}]:
            self.assertTrue(validate(value))
