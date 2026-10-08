"""Pin external processor bytes before execution; receipt identity is explicit."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil

DEFAULT_LOCK = Path(__file__).resolve().parents[1] / 'processors.lock.json'


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            hasher.update(block)
    return hasher.hexdigest()


def processor_identity(name, lock_path=DEFAULT_LOCK):
    lock_path = Path(lock_path)
    lock = json.loads(lock_path.read_text())
    machine = {'amd64': 'x86_64', 'x64': 'x86_64'}.get(platform.machine().lower(), platform.machine().lower())
    target = platform.system().lower() + '-' + machine
    expected = lock.get('platforms', {}).get(target, {}).get(name)
    if lock.get('version') != 1 or not isinstance(expected, dict):
        raise ValueError(f'no pinned {name} for {target}; supply a reviewed processor lock')
    directory = os.environ.get('ARCONT_PROCESSOR_DIR')
    executable = str(Path(directory) / name) if directory else shutil.which(name)
    if not executable or not Path(executable).is_file():
        raise ValueError(f'pinned processor {name} not found; set ARCONT_PROCESSOR_DIR')
    actual = digest(executable)
    if actual != expected.get('sha256'):
        raise ValueError(f'{name} executable SHA-256 differs from processor lock')
    return {'name': name, 'version': expected['version'], 'sha256': actual,
            'executable': str(Path(executable).resolve()), 'platform': target,
            'source_url': expected['url'], 'lock_sha256': digest(lock_path)}


def verify_identity(identity):
    if digest(identity['executable']) != identity['sha256']:
        raise ValueError('processor executable changed during execution')
