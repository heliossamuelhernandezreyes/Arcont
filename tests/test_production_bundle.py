import json
from pathlib import Path
import tempfile
import unittest
from tools.production_bundle import materialize,digest

class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source='.arcont/runs/scene/abc'
        self.src=self.root/self.source;self.src.mkdir(parents=True)
        self.file=self.src/'scene.tscn';self.file.write_text('[gd_scene format=3]\n[ext_resource type="Mesh" path="res://.arcont/runs/scene/abc/mesh.res" id="1"]\n')
        self.mesh=self.src/'mesh.res';self.mesh.write_bytes(b'opaque-native-mesh')
    def files(self):return {'scene.tscn':digest(self.file),'mesh.res':digest(self.mesh)}
    def run_bundle(self,**kwargs):return materialize(self.root,self.source,'assets/review',self.files(),**kwargs)
    def test_relocates_and_preserves_binaries(self):
        self.assertTrue(self.run_bundle()['native_reopen_required'])
        self.assertIn('res://assets/review/mesh.res',(self.root/'assets/review/scene.tscn').read_text())
        self.assertEqual(self.mesh.read_bytes(),(self.root/'assets/review/mesh.res').read_bytes())
    def test_tamper_keeps_previous_head(self):
        self.run_bundle();before=(self.root/'assets/review/scene.tscn').read_bytes();files=self.files()
        self.file.write_text('changed')
        with self.assertRaises(ValueError):materialize(self.root,self.source,'assets/review',files,True)
        self.assertEqual(before,(self.root/'assets/review/scene.tscn').read_bytes())
    def test_unmanaged_destination_and_traversal_rejected(self):
        (self.root/'assets/review').mkdir(parents=True)
        with self.assertRaises(ValueError):self.run_bundle(replace=True)
        with self.assertRaises(ValueError):materialize(self.root,self.source,'assets/../maps',self.files())
    def test_binary_reference_rejected(self):
        self.mesh.write_bytes(b'res://.arcont/runs/scene/abc/other.res')
        with self.assertRaises(ValueError):self.run_bundle()
    def test_symlink_rejected(self):
        self.mesh.unlink();self.mesh.symlink_to(self.file)
        with self.assertRaises(ValueError):self.run_bundle()
