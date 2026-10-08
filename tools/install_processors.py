#!/usr/bin/env python3
"""Install only the processor archives and bytes pinned by processors.lock.json."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request
import zipfile
try:
    from tools.processor_identity import DEFAULT_LOCK
except ModuleNotFoundError:
    from processor_identity import DEFAULT_LOCK


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--lock', type=Path, default=DEFAULT_LOCK)
    parser.add_argument('--platform', default='linux-x86_64')
    args = parser.parse_args()
    lock = json.loads(args.lock.read_text())
    args.destination.mkdir(parents=True, exist_ok=True)
    for name, entry in lock['platforms'][args.platform].items():
        target = args.destination / name
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('refusing to overwrite an unrecognized processor: ' + name)
            print('verified', name, entry['version'])
            continue
        with urllib.request.urlopen(entry['url'], timeout=45) as response:
            raw = response.read(80 * 1024 * 1024 + 1)
        if hashlib.sha256(raw).hexdigest() != entry['archive_sha256']:
            raise ValueError('processor archive hash mismatch: ' + name)
        if entry['url'].endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                members = [item for item in archive.infolist() if Path(item.filename).name == name and not item.is_dir()]
                if len(members) != 1:
                    raise ValueError('ambiguous processor archive')
                binary = archive.read(members[0])
        else:
            with tarfile.open(fileobj=io.BytesIO(raw), mode='r:xz') as archive:
                members = [item for item in archive.getmembers() if Path(item.name).name == name and item.isfile()]
                if len(members) != 1:
                    raise ValueError('ambiguous processor archive')
                binary = archive.extractfile(members[0]).read()
        if hashlib.sha256(binary).hexdigest() != entry['sha256']:
            raise ValueError('processor executable hash mismatch: ' + name)
        with target.open('xb') as stream:
            stream.write(binary)
        target.chmod(0o755)
        print('installed', name, entry['version'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
