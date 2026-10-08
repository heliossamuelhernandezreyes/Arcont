#!/usr/bin/env python3
"""Run byte-pinned Khronos glTF Validator and bind the report to all inputs."""
import argparse
import json
from pathlib import Path
import subprocess

try:
    from tools.processor_identity import DEFAULT_LOCK, digest, processor_identity, verify_identity
    from tools.production_assets import closure
except ModuleNotFoundError:
    from processor_identity import DEFAULT_LOCK, digest, processor_identity, verify_identity
    from production_assets import closure


def validate_spec(model, lock_path=DEFAULT_LOCK):
    model = Path(model).resolve()
    dependencies = closure(model.parent, model.name)
    before = {rel: digest(model.parent / rel) for rel in dependencies}
    identity = processor_identity('gltf_validator', lock_path)
    command = [identity['executable'], '--stdout', '--validate-resources', str(model)]
    process = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    verify_identity(identity)
    if any(digest(model.parent / rel) != value for rel, value in before.items()):
        raise ValueError('model dependencies changed during specification validation')
    try:
        report = json.loads(process.stdout)
    except ValueError as exc:
        raise ValueError('validator did not return JSON') from exc
    issues = report.get('issues', {}) if isinstance(report, dict) else {}
    errors = issues.get('numErrors') if isinstance(issues, dict) else None
    if type(errors) is not int or errors < 0 or report.get('validatorVersion') != identity['version']:
        raise ValueError('validator report has invalid identity or error count')
    receipt = {'version': 1, 'ok': process.returncode == 0 and errors == 0,
               'processor': identity, 'files': before, 'returncode': process.returncode,
               'errors': errors, 'report': report}
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model')
    parser.add_argument('--out', required=True)
    parser.add_argument('--processor-lock', default=str(DEFAULT_LOCK))
    args = parser.parse_args()
    try:
        receipt = validate_spec(args.model, args.processor_lock)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
        return 1
    Path(args.out).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'ok': receipt['ok'], 'errors': receipt['errors'], 'report': args.out}))
    return 0 if receipt['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
