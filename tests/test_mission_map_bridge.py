"""Mission<Map Forge reconciliation prevents drift even if both files pass separately."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from mission_map_bridge import validate_pair


class MapMissionBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mission=json.loads((ROOT/"templates/mission_slice/mission_contract.example.json").read_text())
        cls.world={
            "version":1,"id":"example_world",
            "bounds":copy.deepcopy(cls.mission["map"]["bounds"]),
            "anchors":[{"id":a["id"],"kind":"spawn" if a["kind"] in ("enemy_spawn","player_spawn") else a["kind"],
                        "team":"enemy" if a["kind"]=="enemy_spawn" else ("player" if a["kind"]=="player_spawn" else None),
                        "position":list(a["position"])} for a in cls.mission["anchors"]],
            "routes":[{"id":"route","kind":"primary","width":3,"points":[[0,0,10],[0,0,-10]]}],
            "regions":[{"id":"arena","kind":"encounter","center":[0,0,0],"size":[40,0,30]}],
            "authoring":{"navigation":{"agent_radius":0.5,"agent_height":1.8,"cell_size":0.25,"cell_height":0.25}}
        }

    def check(self, modify, message):
        mission=copy.deepcopy(self.mission)
        world=copy.deepcopy(self.world)
        modify(mission,world)
        errors=validate_pair(mission,world,"maps/example_room.json")
        self.assertTrue(any(message in e for e in errors),errors)

    def test_valid_contract(self):
        self.assertEqual(validate_pair(self.mission,self.world,"maps/example_room.json"),[])

    def test_missing_anchor(self):
        self.check(lambda m,w:w["anchors"].pop(), "missing from game-authored map")

    def test_moved_anchor(self):
        self.check(lambda m,w:w["anchors"][0].update(position=[1,0,10]), "spatial mismatch")

    def test_team_mismatch(self):
        self.check(lambda m,w:w["anchors"][1].update(team="player"), "spawn team")

    def test_bounds_mismatch(self):
        self.check(lambda m,w:w["bounds"].update(width=41), "map.bounds.width")

    def test_wrong_filename(self):
        self.assertTrue(any("does not match" in e for e in validate_pair(self.mission,self.world,"maps/not_the_file.json")))


if __name__=="__main__":
    unittest.main()
