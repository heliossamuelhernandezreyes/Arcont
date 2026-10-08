"""Regression tests from the 2026-10-08 audit, including process boundaries."""
import copy
import hashlib
import json
import multiprocessing
from pathlib import Path
import struct
import tempfile
import time
import unittest
from unittest.mock import patch
import zlib

from tools import arcont_lab, asset_trust, asset_vault_indexer, godot_structured_editing as editing
from tools.arcont_hardening import check_maturity, validate_result
from tools.license_policy import normalize_license_name
from tools.map_forge_contract import validate_contract
from tools.model_forge_control import respond as model_control
from tools.model_forge_inspect import inspect, load_gltf
from tools.project_lock import document_lock
from tools.processor_identity import processor_identity
from tools.public_asset_discovery import _asset_type, _project_policy
from tools.runtime_evidence import canonical_plan, load_json, repo_root, validate_against_plan
from tools.viewport_evidence_gate import validate_viewpoints


def _writer(root, relative, expected, value, barrier, queue):
    root = Path(root)
    staging = root / ('candidate-' + value)
    staging.write_text(value)
    original = editing._revision_guard
    def delayed(*args):
        result = original(*args)
        time.sleep(0.05)  # Deliberately open the old check/replace race window.
        return result
    barrier.wait(timeout=10)
    try:
        with patch.object(editing, '_revision_guard', side_effect=delayed):
            revision = editing._publish_staged(root, relative, staging, expected)
        queue.put(('ok', value, revision))
    except ValueError as exc:
        queue.put(('conflict', value, str(exc)))


def _hold_lock(root, ready):
    with document_lock(Path(root), 'document.gd'):
        ready.set()
        time.sleep(30)


def _chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))


def _png(rgb, metadata=b'', rgba=False):
    pixels = bytes(rgb) + (b'\xff' if rgba else b'')
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', struct.pack('>IIBBBBB', 4, 4, 8, 6 if rgba else 2, 0, 0, 0))
            + (_chunk(b'tEXt', metadata) if metadata else b'')
            + _chunk(b'IDAT', zlib.compress((b'\0' + pixels * 4) * 4)) + _chunk(b'IEND', b''))


def _model(root, mode=4, count=3):
    (root / 'incoming' / 'textures').mkdir(parents=True, exist_ok=True)
    (root / 'incoming' / 'shared.bin').write_bytes(b'\0' * count * 12)
    (root / 'incoming' / 'textures' / 'albedo.png').write_bytes(_png((1, 20, 70)))
    document = {'asset': {'version': '2.0'},
                'buffers': [{'uri': 'shared.bin', 'byteLength': count * 12}],
                'bufferViews': [{'buffer': 0, 'byteLength': count * 12}],
                'accessors': [{'count': count, 'type': 'VEC3', 'componentType': 5126, 'bufferView': 0}],
                'images': [{'uri': 'textures/albedo.png'}],
                'meshes': [{'primitives': [{'mode': mode, 'attributes': {'POSITION': 0}}]}]}
    (root / 'incoming' / 'source.gltf').write_text(json.dumps(document))
    return document


def _runtime_result():
    plan = load_json(canonical_plan(repo_root()))
    bench = plan['benchmarks'][0]
    return plan, {
        'schema_version': 1, 'benchmark_id': bench['id'], 'run_id': 'regression',
        'engine': plan['engine'],
        'platform': {'os': 'Linux', 'device': 'fixture', 'cpu': 'fixture', 'gpu': 'fixture'},
        'runtime': {'renderer': 'gl_compatibility', 'resolution': '1280x720', 'build_type': 'release', 'vsync': False},
        'experiment': {'campaign_id': plan['campaign_id'], 'hypothesis_ref': bench['hypothesis_ref'],
                       'variable': bench['variable'], 'value': bench['sweep'][0], 'repetition': 1,
                       'warmup_seconds': bench['warmup_seconds'], 'sample_seconds': bench['sample_seconds'],
                       'controls': bench.get('controls', {})},
        'metrics': {name: {'mean': 1.0} for name in bench['metrics']},
        'provenance': {'harness_commit': '1'*40, 'raw_data_sha256': 'a'*64}, 'aborted': False,
    }


class ReliabilityRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_two_processes_cannot_publish_the_same_revision(self):
        context = multiprocessing.get_context('spawn')
        for relative in ('scripts/player.gd', 'scenes/main.tscn', 'resources/material.tres', 'project.godot'):
            with self.subTest(relative=relative):
                target = self.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('original')
                expected = hashlib.sha256(target.read_bytes()).hexdigest()
                barrier, queue = context.Barrier(2), context.Queue()
                processes = [context.Process(target=_writer, args=(str(self.root), relative, expected, value, barrier, queue)) for value in ('first', 'second')]
                for process in processes:
                    process.start()
                outcomes = [queue.get(timeout=15) for _ in processes]
                for process in processes:
                    process.join(10)
                    self.assertEqual(process.exitcode, 0)
                self.assertEqual(sorted(row[0] for row in outcomes), ['conflict', 'ok'])
                winner = next(row for row in outcomes if row[0] == 'ok')
                self.assertEqual(target.read_text(), winner[1])
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), winner[2])

    def test_crashed_writer_releases_lock_without_stale_file_cleanup(self):
        context = multiprocessing.get_context('spawn')
        ready = context.Event()
        process = context.Process(target=_hold_lock, args=(str(self.root), ready))
        process.start()
        try:
            self.assertTrue(ready.wait(10))
        finally:
            process.terminate()
            process.join(10)
        with document_lock(self.root, 'document.gd', timeout=1):
            pass

    def test_function_replace_refuses_global_prefix_and_suffix(self):
        path = self.root / 'scripts/player.gd'
        path.parent.mkdir()
        original = b'extends Node\r\n\r\nfunc target():\r\n    pass\r\n\r\nvar keep := 2\r\n'
        path.write_bytes(original)
        expected = hashlib.sha256(original).hexdigest()
        for replacement in ('var injected := 1\nfunc target():\n    pass\n', 'func target():\n    pass\nvar injected := 1\n', 'func target():\n    pass\nclass Extra:\n    pass\n'):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                editing._script_function_replace(self.root, 'scripts/player.gd', 'target', replacement, expected)
            self.assertEqual(path.read_bytes(), original)
        with patch.object(editing, '_validate_script_with_godot', return_value={'ok': True}):
            editing._script_function_replace(self.root, 'scripts/player.gd', 'target', '# replacement\nfunc target():\n    return 4\n', expected)
        result = path.read_bytes()
        self.assertTrue(result.startswith(b'extends Node\r\n\r\n'))
        self.assertTrue(result.endswith(b'var keep := 2\r\n'))

    def stage_request(self):
        return {'protocol_version': 1, 'operation': 'stage', 'model': 'incoming/source.gltf',
                'semantic_id': 'props.triangle', 'destination': 'assets/staged'}

    def test_stage_preserves_bin_texture_dependencies_and_hashes(self):
        _model(self.root)
        result = model_control(self.root, self.stage_request())
        self.assertTrue(result['ok'], result)
        bundle = self.root / result['result']['bundle_directory']
        self.assertEqual((bundle / 'shared.bin').read_bytes(), (self.root / 'incoming/shared.bin').read_bytes())
        self.assertTrue((bundle / 'textures/albedo.png').is_file())
        for relative, entry in result['result']['files'].items():
            self.assertEqual(hashlib.sha256((bundle / relative).read_bytes()).hexdigest(), entry['sha256'])
        self.assertEqual(result['result']['delivery_status'], 'candidate')

    def test_failed_staging_never_publishes_a_partial_bundle(self):
        _model(self.root)
        (self.root / 'incoming/shared.bin').unlink()
        result = model_control(self.root, self.stage_request())
        self.assertFalse(result['ok'])
        self.assertFalse((self.root / 'assets/staged/props/triangle').exists())

    def test_dependency_copy_failure_rolls_back_temporary_bundle(self):
        _model(self.root)
        with patch('tools.model_forge_control.shutil.copyfile', side_effect=OSError('disk full')):
            result = model_control(self.root, self.stage_request())
        self.assertFalse(result['ok'])
        self.assertEqual(list((self.root / 'assets/staged/props').iterdir()), [])

    def test_stage_refuses_symlink_source(self):
        _model(self.root)
        (self.root / 'alias').symlink_to(self.root / 'incoming', target_is_directory=True)
        request = self.stage_request()
        request['model'] = 'alias/source.gltf'
        self.assertFalse(model_control(self.root, request)['ok'])

    def test_strips_and_fans_cannot_bypass_triangle_budget(self):
        for mode in (5, 6):
            with self.subTest(mode=mode):
                _model(self.root, mode, 1002)
                request = self.stage_request()
                request.update(operation='validate', profile={'budgets': {'triangles_max': 100, 'materials_max': 10}})
                result = model_control(self.root, request)
                self.assertFalse(result['result']['technical_passed'])
                self.assertEqual(result['result']['inspection']['triangles'], 1000)
                request['profile']['budgets']['triangles_max'] = 1000
                self.assertTrue(model_control(self.root, request)['result']['technical_passed'])

    def test_invalid_geometry_accessors_modes_and_counts_fail(self):
        original = _model(self.root)
        for field, bad_values in [('mode', [True, -1, 7]), ('indices', [-1, True, 9])]:
            for value in bad_values:
                doc = copy.deepcopy(original)
                doc['meshes'][0]['primitives'][0][field] = value
                (self.root / 'incoming/source.gltf').write_text(json.dumps(doc))
                self.assertFalse(model_control(self.root, self.stage_request())['ok'])
        doc = copy.deepcopy(original)
        doc['accessors'][0]['count'] = 4
        (self.root / 'incoming/source.gltf').write_text(json.dumps(doc))
        self.assertFalse(model_control(self.root, self.stage_request())['ok'])

    def test_glb_truncated_chunk_is_rejected(self):
        path = self.root / 'truncated.glb'
        raw = b'glTF' + struct.pack('<II', 2, 24) + struct.pack('<II', 400, 0x4E4F534A) + b'{}  '
        path.write_bytes(raw)
        with self.assertRaises(ValueError):
            load_gltf(path)

    def test_runtime_rejects_nonfinite_boolean_and_negative_time(self):
        plan, baseline = _runtime_result()
        self.assertEqual(validate_against_plan(baseline, plan), [])
        for value in (float('nan'), float('inf'), -float('inf'), True, -1):
            data = copy.deepcopy(baseline)
            data['metrics']['cpu_ms'] = {'mean': value}
            self.assertTrue(validate_against_plan(data, plan), value)
        for value in ('false', 0, None):
            data = copy.deepcopy(baseline)
            data.update(aborted=value, metrics={}, provenance={})
            self.assertTrue(validate_against_plan(data, plan))
        for field in ('warmup_seconds', 'sample_seconds'):
            data = copy.deepcopy(baseline)
            data['experiment'][field] = -1
            self.assertTrue(validate_result(data))
        baseline['metrics']['signed_displacement'] = {'value': -1.0}
        self.assertEqual(validate_result(baseline), [])

    def test_runtime_wrong_shapes_return_errors_instead_of_crashing(self):
        plan, baseline = _runtime_result()
        for field in ('engine', 'platform', 'runtime', 'experiment', 'metrics', 'provenance'):
            data = copy.deepcopy(baseline)
            data[field] = ['bad']
            self.assertTrue(validate_against_plan(data, plan))
        self.assertTrue(validate_result([]))

    def test_map_rejects_bad_optional_fields_and_boolean_coordinates(self):
        baseline = {'version': 1, 'id': 'fixture', 'bounds': {'width': 20, 'depth': 20},
                    'anchors': [{'id': 'spawn', 'kind': 'spawn', 'position': [0, 0, 0]}],
                    'routes': [], 'regions': [{'id': 'area', 'kind': 'combat', 'center': [0, 0, 0]}], 'authoring': {}}
        self.assertEqual(validate_contract(baseline), [])
        for value in (float('nan'), float('inf'), True, -1):
            for kind in ('anchors', 'regions'):
                data = copy.deepcopy(baseline)
                data[kind][0]['radius'] = value
                self.assertTrue(validate_contract(data))
        data = copy.deepcopy(baseline)
        data['anchors'][0]['position'][0] = True
        self.assertTrue(validate_contract(data))
        data = copy.deepcopy(baseline)
        data['bounds']['height'] = -1
        self.assertTrue(validate_contract(data))

    def test_png_fake_header_corrupt_crc_and_truncated_image_fail(self):
        a, b = self.root / 'a.png', self.root / 'b.png'
        b.write_bytes(_png((4, 5, 6)))
        valid = _png((1, 2, 3))
        for invalid in (valid[:33] + b'\0'*31000, valid[:-12], valid[:45] + bytes([valid[45] ^ 1]) + valid[46:]):
            a.write_bytes(invalid)
            self.assertTrue(validate_viewpoints([a, b], 4, 4, 20))

    def test_png_metadata_or_rgb_encoding_cannot_fake_distinct_viewpoints(self):
        a, b = self.root / 'a.png', self.root / 'b.png'
        a.write_bytes(_png((1, 2, 3)))
        for value in (_png((1, 2, 3), b'Comment\0other'), _png((1, 2, 3), rgba=True)):
            b.write_bytes(value)
            self.assertTrue(any('duplicate' in err for err in validate_viewpoints([a, b], 4, 4, 20)))
        b.write_bytes(_png((4, 5, 6)))
        self.assertEqual(validate_viewpoints([a, b], 4, 4, 20), [])

    def test_polyhaven_type_zero_and_live_adapter_share_taxonomy(self):
        for value, expected in ((0, 'hdri'), (1, 'texture'), (2, 'model')):
            record = asset_vault_indexer.polyhaven_record('fixture', {'type': value})
            self.assertEqual(record['asset_type'], expected)
            self.assertEqual(_asset_type({'type': value}), expected)
            self.assertEqual(record['technical']['pbr'], value in (1, 2))
        self.assertEqual(_asset_type({'type': False}), 'unknown')

    def test_license_alias_deny_takes_precedence(self):
        intent = {'protocol': 'arcont-project-intent', 'version': 1, 'project_id': 'test', 'title': 'Test',
                  'genre': 'action', 'targets': ['Windows'], 'asset_policy': {'public_assets': True,
                  'user_assets': True, 'commercial_use_required': True, 'allow_network_discovery': True}}
        for allowed, denied in (('CC0', 'CC0-1.0'), ('CC0-1.0', 'CC0')):
            intent['asset_policy'].update(allowed_licenses=[allowed], forbidden_licenses=[denied])
            (self.root / 'project.intent.json').write_text(json.dumps(intent))
            with self.assertRaises(PermissionError):
                _project_policy(self.root)
            intent['asset_policy']['forbidden_licenses'] = []
            (self.root / 'project.intent.json').write_text(json.dumps(intent))
            _project_policy(self.root)
        self.assertIsNone(normalize_license_name('not CC0; commercial use prohibited'))

    def test_runtime_trust_distinguishes_declared_from_verified_bytes(self):
        item = {'level': 'runtime', 'tested_at': '2026-10-08', 'evidence_ref': 'missing.json'}
        record = {'compatibility': {'godot': True}, 'compatibility_evidence': {'godot': item}}
        self.assertTrue(asset_trust.validate_record_trust(record, self.root))
        item['evidence_ref'] = 'https://github.com/owner/repo/actions/runs/123'
        self.assertEqual(asset_trust.evidence_resolution(item, self.root), 'declared')
        item['tested_at'] = 'not-a-date'
        self.assertTrue(asset_trust.validate_record_trust(record))
        item.update(tested_at='2026-10-08', evidence_ref='receipt.json')
        receipt = self.root / 'receipt.json'
        receipt.write_text('{"run_id":"fixture"}')
        self.assertEqual(asset_trust.evidence_resolution(item, self.root), 'reference-verified')
        item['evidence_sha256'] = hashlib.sha256(receipt.read_bytes()).hexdigest()
        self.assertEqual(asset_trust.evidence_resolution(item, self.root), 'bytes-verified')
        receipt.write_text('modified')
        self.assertTrue(asset_trust.validate_record_trust(record, self.root))

    def test_catalog_wrong_types_are_rejected(self):
        record = asset_vault_indexer.polyhaven_record('fixture', {'type': 2})
        for field, bad in (('asset_type', []), ('technical', 'not-an-object'), ('license', []), ('compatibility', True)):
            value = copy.deepcopy(record)
            value[field] = bad
            self.assertTrue(asset_vault_indexer.validate_record(value))

    def graph(self, text):
        directory = self.root / 'docs/godot/knowledge'
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'test.yaml').write_text(text)

    def test_graph_rejects_circular_invalidated_missing_evidence(self):
        self.graph('''nodes:
  - id: ARC-RULE-A
    kind: rule
    status: validated
    evidence: missing.json
  - id: ARC-RULE-B
    kind: rule
    status: falsified
edges:
  - from: ARC-RULE-A
    relation: derived_from
    to: ARC-RULE-B
  - from: ARC-RULE-B
    relation: derived_from
    to: ARC-RULE-A
''')
        errors, _ = arcont_lab.validate(self.root)
        for code in ('derivation-cycle', 'unresolved-evidence', 'invalidated-dependency', 'rule-without-evidence-path', 'maturity'):
            self.assertTrue(any(code in err for err in errors), errors)

    def test_preregistered_benchmark_does_not_require_a_completed_result(self):
        self.graph('nodes:\n  - id: ARC-BENCH-TEST\n    kind: benchmark\n    status: preregistered\nedges:\n')
        self.assertEqual(arcont_lab.validate(self.root)[0], [])

    def test_evidence_id_cycle_and_malformed_maturity_are_rejected(self):
        self.graph('''nodes:
  - id: ARC-OBS-A
    kind: observation
    evidence: ARC-OBS-B
  - id: ARC-OBS-B
    kind: observation
    evidence: ARC-OBS-A
edges:
''')
        self.assertTrue(any('derivation-cycle' in err for err in arcont_lab.validate(self.root)[0]))
        for evidence in ({'source_traced': 'false'}, {'observations': True}, {'reproductions': -1}):
            self.assertTrue(check_maturity('L7_VALIDATED_RULE', evidence))

    def test_processor_identity_refuses_missing_and_changed_executables(self):
        with patch.dict('os.environ', {'ARCONT_PROCESSOR_DIR': str(self.root)}):
            with self.assertRaisesRegex(ValueError, 'not found'):
                processor_identity('gltfpack')
            (self.root / 'gltfpack').write_bytes(b'unreviewed executable')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                processor_identity('gltfpack')

    def test_vendor_docs_do_not_contaminate_knowledge_validation(self):
        directory = self.root / 'integrations/mcp/node_modules/package'
        directory.mkdir(parents=True)
        (directory / 'README.md').write_text('[missing](does-not-exist.md)')
        self.assertEqual(arcont_lab.validate(self.root), ([], []))
        (self.root / 'README.md').write_text('[missing](does-not-exist.md)')
        self.assertTrue(arcont_lab.validate(self.root)[0])

    def test_comparison_requires_controls_and_reads_nested_cpu_statistics(self):
        _, a = _runtime_result()
        a['metrics']['cpu_ms'] = {'mean': 10, 'unit': 'ms'}
        b = copy.deepcopy(a)
        b['metrics']['cpu_ms']['mean'] = 1
        result = arcont_lab.compare_results(a, b)
        self.assertTrue(result['directly_comparable'], result)
        row = next(row for row in result['metrics'] if row['metric'] == 'metrics.cpu_ms.mean')
        self.assertEqual(row['delta_percent'], -90)
        b['runtime']['vsync'] = True
        self.assertFalse(arcont_lab.compare_results(a, b)['directly_comparable'])
        del b['runtime']['vsync']
        self.assertFalse(arcont_lab.compare_results(a, b)['directly_comparable'])
        b = copy.deepcopy(a)
        b['engine']['version'] = 'experiment-next-version'
        self.assertFalse(arcont_lab.compare_results(a, b)['directly_comparable'])
        self.assertTrue(arcont_lab.compare_results(a, b, ('engine.version',))['directly_comparable'])
        b = copy.deepcopy(a)
        b['metrics']['cpu_ms']['unit'] = 's'
        result = arcont_lab.compare_results(a, b)
        self.assertFalse(result['directly_comparable'])
        self.assertIsNone(next(row for row in result['metrics'] if row['metric'] == 'metrics.cpu_ms.mean')['delta_percent'])


if __name__ == '__main__':
    unittest.main()
