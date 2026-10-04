import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
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

    def test_replace_atomically_and_check_receipt_contents(self):
        self.run_bundle();self.file.write_text('[gd_scene format=3]\n; revision two\n')
        self.run_bundle(replace=True)
        self.assertIn('revision two',(self.root/'assets/review/scene.tscn').read_text())
        (self.root/'assets/review/owned-by-game.txt').write_text('preserve')
        with self.assertRaises(ValueError):self.run_bundle(replace=True)
        self.assertTrue((self.root/'assets/review/owned-by-game.txt').exists())

    def test_copied_receipt_cannot_authorize_replacement(self):
        self.run_bundle();marker=self.root/'assets/review/arcont-bundle.json'
        data=json.loads(marker.read_text());data['destination']='assets/other';marker.write_text(json.dumps(data))
        with self.assertRaises(ValueError):self.run_bundle(replace=True)
        self.assertTrue(self.root.joinpath('assets/review/scene.tscn').exists())

    def test_read_hash_detects_change_after_stat(self):
        from tools.production_bundle import read_artifact
        with patch('tools.production_bundle.read_artifact',side_effect=lambda p,n,sha:(p.write_bytes(b'changed'),read_artifact(p,n,sha))[1]):
            with self.assertRaises(ValueError):self.run_bundle()
        self.assertFalse((self.root/'assets/review').exists())

    def test_oversized_sparse_file_rejected_before_read(self):
        with self.mesh.open('wb') as f:f.truncate(513*1024*1024)
        with patch('tools.production_bundle.read_artifact',side_effect=AssertionError('must not read')):
            with self.assertRaises(ValueError):materialize(self.root,self.source,'assets/review',{'mesh.res':'a'*64})

    def test_atomic_failure_preserves_old_bundle(self):
        self.run_bundle();before=(self.root/'assets/review/scene.tscn').read_bytes()
        self.file.write_text('[gd_scene format=3]\n; modified\n')
        with patch('tools.production_bundle.atomic_publish',side_effect=OSError('simulated publication failure')):
            with self.assertRaises(OSError):self.run_bundle(replace=True)
        self.assertEqual(before,(self.root/'assets/review/scene.tscn').read_bytes())

    def test_no_replace_never_clobbers_late_destination(self):
        from tools.production_bundle import atomic_publish
        def late(candidate,target,replace):
            target.mkdir();(target/'concurrent.txt').write_text('other publisher')
            return atomic_publish(candidate,target,replace)
        with patch('tools.production_bundle.atomic_publish',side_effect=late):
            with self.assertRaises(ValueError):self.run_bundle()
        self.assertEqual('other publisher',(self.root/'assets/review/concurrent.txt').read_text())
