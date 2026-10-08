#!/usr/bin/env python3
"""Inspect glTF/GLB geometry. Counts are structural, not measured GPU cost."""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path


def _invalid_constant(value):
    raise ValueError('non-finite JSON constant: ' + value)


def load_gltf(path: Path):
    if path.suffix.lower() == '.gltf':
        document = json.loads(path.read_text(encoding='utf-8'), parse_constant=_invalid_constant)
    else:
        raw = path.read_bytes()
        if len(raw) < 20 or raw[:4] != b'glTF':
            raise ValueError('not a GLB file')
        version, total = struct.unpack_from('<II', raw, 4)
        if version != 2 or total != len(raw):
            raise ValueError('invalid GLB v2 header')
        offset, document, chunks = 12, None, 0
        while offset < len(raw):
            if offset + 8 > len(raw):
                raise ValueError('truncated GLB chunk header')
            size, kind = struct.unpack_from('<II', raw, offset)
            offset += 8
            if size % 4 or offset + size > len(raw):
                raise ValueError('invalid GLB chunk length')
            if chunks == 0 and kind != 0x4E4F534A:
                raise ValueError('GLB JSON must be its first chunk')
            if kind == 0x4E4F534A:
                if document is not None:
                    raise ValueError('duplicate GLB JSON chunk')
                document = json.loads(raw[offset:offset+size].decode('utf-8'), parse_constant=_invalid_constant)
            offset += size
            chunks += 1
        if document is None:
            raise ValueError('GLB has no JSON chunk')
    if not isinstance(document, dict) or not isinstance(document.get('asset'), dict):
        raise ValueError('glTF document and asset must be objects')
    for field in ('accessors', 'meshes', 'images', 'buffers', 'bufferViews', 'nodes', 'scenes', 'materials', 'textures', 'skins', 'animations', 'cameras'):
        if not isinstance(document.get(field, []), list) or not all(isinstance(x, dict) for x in document.get(field, [])):
            raise ValueError('invalid glTF array: ' + field)
    return document


def component_count(kind):
    return {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}.get(kind)


def _index(value, sequence, label):
    if type(value) is not int or not 0 <= value < len(sequence):
        raise ValueError('invalid ' + label + ' index')
    return sequence[value]


def inspect(path: Path):
    document = load_gltf(path)
    accessors = document.get('accessors', [])
    vertices = primitives = 0
    mesh_triangles = []
    modes = set()
    for mesh in document.get('meshes', []):
        total = 0
        entries = mesh.get('primitives')
        if not isinstance(entries, list) or not entries:
            raise ValueError('mesh requires non-empty primitives')
        for primitive in entries:
            if not isinstance(primitive, dict) or not isinstance(primitive.get('attributes'), dict):
                raise ValueError('invalid mesh primitive attributes')
            position = _index(primitive['attributes'].get('POSITION'), accessors, 'POSITION accessor')
            counted = _index(primitive['indices'], accessors, 'indices accessor') if 'indices' in primitive else position
            for accessor in (position, counted):
                if type(accessor.get('count')) is not int or accessor['count'] < 1:
                    raise ValueError('geometry accessor count must be a positive integer')
            if position.get('type') != 'VEC3':
                raise ValueError('POSITION accessor must be VEC3')
            if 'indices' in primitive and (counted.get('type') != 'SCALAR' or counted.get('componentType', 5123) not in (5121, 5123, 5125)):
                raise ValueError('indices must be unsigned scalar data')
            mode = primitive.get('mode', 4)
            if type(mode) is not int or mode not in range(7):
                raise ValueError('invalid primitive mode')
            count = counted['count']
            if mode == 4:
                if count % 3:
                    raise ValueError('incomplete triangle-list geometry')
                total += count // 3
            elif mode in (5, 6):
                if count < 3:
                    raise ValueError('triangle strip/fan needs at least three elements')
                total += count - 2
            modes.add(mode)
            vertices += position['count']
            primitives += 1
        mesh_triangles.append(total)
    instanced = 0
    for node in document.get('nodes', []):
        if 'mesh' in node:
            instanced += _index(node['mesh'], mesh_triangles, 'node mesh')
    return {
        'path': str(path), 'format': path.suffix.lower().lstrip('.'),
        'meshes': len(mesh_triangles), 'primitives': primitives,
        'vertices_referenced': vertices, 'triangles': sum(mesh_triangles),
        'triangles_instanced_all_nodes': instanced, 'primitive_modes': sorted(modes),
        'triangle_count_scope': 'mesh primitives; strips/fans include degenerate triangles conservatively; all-node instances are separate',
        **{field: len(document.get(field, [])) for field in ('materials', 'textures', 'images', 'nodes', 'skins', 'animations', 'cameras')},
        'extensions_used': document.get('extensionsUsed', []),
        'extensions_required': document.get('extensionsRequired', []),
        'generator': document['asset'].get('generator'), 'gltf_version': document['asset'].get('version'),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='+')
    parser.add_argument('--out')
    args = parser.parse_args()
    reports = [inspect(Path(p)) for p in args.paths if Path(p).suffix.lower() in {'.gltf', '.glb'}]
    text = json.dumps({'model_forge_inspection_version': 2, 'assets': reports}, indent=2, allow_nan=False)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    print(text)
    return 0 if reports else 2


if __name__ == '__main__':
    raise SystemExit(main())
