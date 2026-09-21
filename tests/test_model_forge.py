import json,struct,tempfile,unittest
from pathlib import Path
from tools.model_forge_inspect import inspect
from tools.model_forge_materialize import gate

class ModelForgeTests(unittest.TestCase):
    def test_green_verified_record_passes_gate(self):
        p=gate({"license":{"name":"CC0-1.0","commercial_use":True,"modification":True},"review":{"license_verified":True}})
        self.assertEqual(p.tier,"green")
    def test_unverified_record_is_rejected(self):
        with self.assertRaises(SystemExit): gate({"license":{"name":"CC0-1.0","commercial_use":True,"modification":True},"review":{"license_verified":False}})
    def test_minimal_glb_inspection(self):
        doc={"asset":{"version":"2.0"},"accessors":[{"count":3,"type":"VEC3"},{"count":3,"type":"SCALAR"}],
             "meshes":[{"primitives":[{"attributes":{"POSITION":0},"indices":1}]}]}
        js=json.dumps(doc,separators=(",",":")).encode(); js+=b" " * ((4-len(js)%4)%4)
        total=12+8+len(js); raw=b"glTF"+struct.pack("<II",2,total)+struct.pack("<II",len(js),0x4E4F534A)+js
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.glb"; p.write_bytes(raw); r=inspect(p)
            self.assertEqual(r["triangles"],1); self.assertEqual(r["meshes"],1); self.assertEqual(r["gltf_version"],"2.0")
if __name__=="__main__": unittest.main()
