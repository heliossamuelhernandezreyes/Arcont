#!/usr/bin/env python3
"""Audit acceptance using real Godot, gltfpack and Khronos Validator processes."""
import argparse
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import godot_structured_editing as editing
from tools.model_forge_control import respond as model_control
from tools.model_forge_process import process_model
from tools.model_forge_spec_validate import validate_spec
from tools.processor_identity import digest


def writer(project, request, barrier, queue):
    original = editing._publish_staged
    def synchronized(*args):
        barrier.wait(timeout=40)
        return original(*args)
    with patch.object(editing, '_publish_staged', side_effect=synchronized):
        queue.put(editing.respond(Path(project), request))


def model(project, name, vertices, mode):
    folder = project / 'incoming' / name
    folder.mkdir(parents=True)
    raw = b''.join(struct.pack('<fff', *vertex) for vertex in vertices)
    (folder / 'shared.bin').write_bytes(raw)
    low = [min(v[i] for v in vertices) for i in range(3)]
    high = [max(v[i] for v in vertices) for i in range(3)]
    document = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
                'nodes': [{'mesh': 0}], 'buffers': [{'uri': 'shared.bin', 'byteLength': len(raw)}],
                'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': len(raw), 'target': 34962}],
                'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': len(vertices), 'type': 'VEC3', 'min': low, 'max': high}],
                'meshes': [{'primitives': [{'attributes': {'POSITION': 0}, 'mode': mode}]}]}
    path = folder / 'source.gltf'
    path.write_text(json.dumps(document))
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    project, evidence = args.project.resolve(), args.evidence.resolve()
    project.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    if (project / 'project.godot').exists():
        raise ValueError('acceptance requires an empty fresh project')
    godot = os.environ['GODOT_BIN']
    (project / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="Arcont reliability acceptance"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    (project / 'scripts').mkdir()
    (project / 'scenes').mkdir()
    (project / 'resources').mkdir()
    (project / 'scripts/player.gd').write_text('extends Node\nfunc target():\n    return 0\n')
    (project / 'scenes/main.tscn').write_text('[gd_scene format=3]\n[node name="Main" type="Node3D"]\n')
    (project / 'resources/material.tres').write_text('[gd_resource type="StandardMaterial3D" format=3]\n[resource]\nroughness = 0.5\n')
    assertions, races = {}, {}
    context = multiprocessing.get_context('spawn')
    for kind, relative in [('script', 'scripts/player.gd'), ('scene', 'scenes/main.tscn'), ('resource', 'resources/material.tres'), ('input', 'project.godot')]:
        expected = digest(project / relative)
        requests = []
        for index in (1, 2):
            request = {'protocol_version': 1, 'if_revision': expected}
            if kind == 'script':
                request.update(operation='script.replace', path=relative, source=f'extends Node\nfunc target():\n    return {index}\n')
            elif kind == 'scene':
                request.update(operation='scene.edit', scene=relative, changes=[{'op': 'rename', 'path': '.', 'name': f'Root{index}'}])
            elif kind == 'resource':
                request.update(operation='resource.edit', resource=relative, changes=[{'op': 'set', 'property': 'roughness', 'value': index / 4}])
            else:
                request.update(operation='input.action.set', action=f'move_{index}', events=[{'type': 'key', 'keycode': 'W', 'physical': True}])
            requests.append(request)
        barrier, queue = context.Barrier(2), context.Queue()
        processes = [context.Process(target=writer, args=(str(project), request, barrier, queue)) for request in requests]
        try:
            for process in processes:
                process.start()
            results = [queue.get(timeout=60) for _ in processes]
            for process in processes:
                process.join(5)
                assert process.exitcode == 0
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(5)
        accepted = [result for result in results if result.get('ok')]
        refused = [result for result in results if not result.get('ok')]
        assert len(accepted) == len(refused) == 1, results
        assert 'revision conflict' in refused[0]['error'], results
        assert accepted[0]['result']['revision'] == digest(project / relative)
        races[kind] = results
        assertions[kind + '_same_revision_one_writer'] = True

    path = project / 'scripts/player.gd'
    before = path.read_bytes()
    result = editing.respond(project, {'protocol_version': 1, 'operation': 'script.function.replace', 'path': 'scripts/player.gd',
        'function': 'target', 'if_revision': digest(path), 'source': 'var unauthorized := 1\nfunc target():\n    return 3\n'})
    assert not result['ok'] and path.read_bytes() == before
    assertions['function_scope_preserved'] = True

    triangle = model(project, 'triangle', [(0,0,0), (1,0,0), (0,1,0)], 4)
    strip = model(project, 'strip', [(i//2, i%2, 0) for i in range(1002)], 5)
    profile = {'id': 'acceptance', 'budgets': {'triangles_max': 100, 'materials_max': 10}}
    request = {'protocol_version': 1, 'operation': 'stage', 'model': triangle.relative_to(project).as_posix(),
               'destination': 'assets/staged', 'semantic_id': 'acceptance.triangle', 'profile': profile, 'delivery_mode': 'validated'}
    staged = model_control(project, request)
    assert staged['ok'], staged
    bundle = project / staged['result']['bundle_directory']
    assert (bundle / 'shared.bin').read_bytes() == (triangle.parent / 'shared.bin').read_bytes()
    assert staged['result']['spec_validation']['errors'] == 0
    assertions['complete_gltf_bundle_spec_validated'] = True
    rejected = model_control(project, {**request, 'operation': 'validate', 'model': strip.relative_to(project).as_posix()})
    assert not rejected['result']['technical_passed'] and rejected['result']['inspection']['triangles'] == 1000, rejected
    assertions['strip_budget_rejected'] = True

    processed = project / 'processed' / 'triangle.glb'
    receipt = process_model(triangle, processed, keep_names=True)
    validated = validate_spec(processed)
    assert validated['ok'], validated
    assert receipt['output_sha256'] == digest(processed)
    assertions['pinned_processing_spec_roundtrip'] = True
    # Keep deliberately invalid resources outside the final clean Godot project.
    invalid_dir = evidence / 'invalid-model'
    invalid_dir.mkdir()
    invalid = invalid_dir / 'bad.gltf'
    invalid.write_text(json.dumps({'asset': {'version': '2.0'}, 'nodes': [{'mesh': 99}]}))
    assert not validate_spec(invalid)['ok']
    assertions['khronos_rejects_invalid_reference'] = True

    imported = subprocess.run([godot, '--headless', '--path', str(project), '--editor', '--import', '--quit'], capture_output=True, text=True, timeout=120)
    logs = imported.stdout + '\n' + imported.stderr
    (evidence / 'final-import.log').write_text(logs)
    assert imported.returncode == 0 and not re.search(r'ERROR:|Parse Error|Failed to load', logs), logs
    probe = project / 'probe.gd'
    probe.write_text('''extends SceneTree
func count_faces(node: Node) -> int:
    var total: int = 0
    if node is MeshInstance3D and node.mesh:
        total += node.mesh.get_faces().size() / 3
    for child in node.get_children():
        total += count_faces(child)
    return total
func _initialize():
    var counts: Array = []
    for path in OS.get_cmdline_user_args():
        var scene = load(path)
        if not scene is PackedScene:
            quit(2)
            return
        var node = scene.instantiate()
        counts.append(count_faces(node))
        node.free()
    print("ARCONT_COUNTS=" + JSON.stringify(counts))
    quit(0)
''')
    resource_paths = ['res://' + (bundle / 'asset.gltf').relative_to(project).as_posix(),
                      'res://' + strip.relative_to(project).as_posix(),
                      'res://' + processed.relative_to(project).as_posix()]
    probed = subprocess.run([godot, '--headless', '--path', str(project), '--script', 'res://probe.gd', '--', *resource_paths], capture_output=True, text=True, timeout=60)
    logs = probed.stdout + '\n' + probed.stderr
    (evidence / 'resource-reopen.log').write_text(logs)
    assert probed.returncode == 0 and not re.search(r'ERROR:|Parse Error|Failed to load', logs), logs
    match = re.search(r'ARCONT_COUNTS=(\[[^\n]+\])', logs)
    counts = json.loads(match.group(1)) if match else None
    assert counts == [1, 1000, 1], counts
    assertions['godot_reopens_staged_and_processed_models'] = True
    assertions['godot_confirms_1000_strip_faces'] = True
    version = subprocess.check_output([godot, '--version'], text=True).strip()
    summary = {'ok': True, 'godot_version': version, 'godot_sha256': digest(godot),
               'assertions': assertions, 'native_face_counts': counts,
               'races': races, 'staging': staged['result'], 'processing': receipt,
               'limits': ['Linux headless only; no physical Android performance or art-quality claim.']}
    (evidence / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'ok': True, 'assertions': assertions, 'native_face_counts': counts}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
