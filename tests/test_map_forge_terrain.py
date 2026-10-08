import copy
import unittest
from tools.map_forge_terrain import brush


class TerrainBrushTests(unittest.TestCase):
    def setUp(self):
        self.state = {"map": {"authoring": {"materials": [{"id": "soil"}, {"id": "grass"}], "heightfields": [{"id": "ground", "columns": 3, "rows": 3, "spacing": [2, 2], "position": [10, 0, -4], "heights": [0] * 9, "material": "soil"}]}}, "physical": None}
        self.options = {"heightfield_id": "ground", "center": [12, -2], "radius": 2, "strength": 3, "mode": "raise"}

    def test_world_coordinates_and_immutable_input(self):
        before = copy.deepcopy(self.state)
        result = brush(self.state, self.options)
        self.assertEqual(result["map"]["authoring"]["heightfields"][0]["heights"], [0, 0, 0, 0, 3, 0, 0, 0, 0])
        self.assertEqual(self.state, before)

    def test_lower_and_flatten(self):
        raised = brush(self.state, self.options)
        lowered = brush(raised, {**self.options, "mode": "lower"})
        self.assertEqual(lowered, self.state)
        flat = brush(raised, {**self.options, "mode": "flatten", "height": 5, "strength": 1})
        self.assertEqual(flat["map"]["authoring"]["heightfields"][0]["heights"][4], 5)

    def test_smoothing_reads_snapshot(self):
        raised = brush(self.state, self.options)
        smoothed = brush(raised, {**self.options, "mode": "smooth", "strength": 1})
        self.assertAlmostEqual(smoothed["map"]["authoring"]["heightfields"][0]["heights"][4], 1 / 3)

    def test_paint_and_reversible_holes(self):
        opts = {**self.options, "center": [11, -3], "radius": 0.5}
        painted = brush(self.state, {**opts, "mode": "paint", "material": "grass"})
        self.assertEqual(painted["map"]["authoring"]["heightfields"][0]["paint"], ["grass", "soil", "soil", "soil"])
        holed = brush(painted, {**opts, "mode": "hole"})
        filled = brush(holed, {**opts, "mode": "fill"})
        self.assertFalse(any(filled["map"]["authoring"]["heightfields"][0]["holes"]))

    def test_invalid_inputs_and_missed_brush(self):
        for edit in [{"radius": 0}, {"center": [999, 999]}, {"mode": "paint", "material": "missing"}, {"strength": float("nan")}, {"heightfield_id": "missing"}]:
            with self.assertRaises(ValueError):
                brush(self.state, {**self.options, **edit})

    def test_invalid_grid_rejected_before_any_edit(self):
        self.state["map"]["authoring"]["heightfields"][0]["heights"] = [0]
        with self.assertRaises(ValueError):
            brush(self.state, self.options)
