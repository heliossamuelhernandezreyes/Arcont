#!/usr/bin/env python3
"""Pinned gltfpack adapter. Produces a single GLB and an identity receipt."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

try:
    from tools.processor_identity import DEFAULT_LOCK, digest, processor_identity, verify_identity
    from tools.production_assets import closure
except ModuleNotFoundError:
    from processor_identity import DEFAULT_LOCK, digest, processor_identity, verify_identity
    from production_assets import closure


def process_model(src, dst, ratio=1.0, keep_names=False, lock_path=DEFAULT_LOCK):
    src, dst = Path(src).resolve(), Path(dst).resolve()
    if src.suffix.lower() not in {'.glb', '.gltf'} or dst.suffix.lower() != '.glb':
        raise ValueError('pinned pipeline accepts glTF/GLB to self-contained GLB; convert OBJ/DCC with separately reviewed dependency receipts')
    if src == dst or dst.exists():
        raise ValueError('processor output must be a new file distinct from input')
    if type(ratio) not in (int, float) or not 0 < ratio <= 1:
        raise ValueError('ratio must be >0 and <=1')
    files = {rel: digest(src.parent / rel) for rel in closure(src.parent, src.name)}
    identity = processor_identity('gltfpack', lock_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.process-', dir=dst.parent) as temporary:
        candidate = Path(temporary) / 'asset.glb'
        # Canonical Godot 4.7.2 does not support KHR_mesh_quantization. Keep
        # ordinary float attributes until another target profile proves it.
        command = [identity['executable'], '-noq', '-i', str(src), '-o', str(candidate)]
        if ratio < 1:
            command += ['-si', str(ratio)]
        if keep_names:
            command += ['-kn', '-km']
        process = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        verify_identity(identity)
        if process.returncode or not candidate.is_file():
            raise ValueError(f'processor failed ({process.returncode}): {process.stderr[-2000:]}')
        if any(digest(src.parent / rel) != value for rel, value in files.items()):
            raise ValueError('source dependencies changed during processing')
        # A GLB can legally refer to external files; this output contract cannot.
        if closure(candidate.parent, candidate.name) != [candidate.name]:
            raise ValueError('processor did not produce a self-contained GLB')
        receipt = {'version': 2, 'processor': identity, 'command': command[1:], 'files': files,
                   'input_sha256': files[src.name], 'output_sha256': digest(candidate),
                   'input_size_bytes': src.stat().st_size, 'output_size_bytes': candidate.stat().st_size,
                   'ratio_requested': ratio}
        # Exclusive publication prevents overwriting a destination created meanwhile.
        os.link(candidate, dst)
    Path(str(dst) + '.process.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('--out', required=True)
    parser.add_argument('--ratio', type=float, default=1.0)
    parser.add_argument('--keep-names', action='store_true')
    parser.add_argument('--processor-lock', default=str(DEFAULT_LOCK))
    args = parser.parse_args()
    try:
        receipt = process_model(args.input, args.out, args.ratio, args.keep_names, args.processor_lock)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
