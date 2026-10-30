#!/usr/bin/env python3
"""Strict production-budget validation for non-empty Model Forge reports."""
import argparse
import json
from pathlib import Path


def validate_report(report, profile):
    if not isinstance(profile, dict) or not isinstance(profile.get('id'), str) or not profile['id']:
        raise ValueError('profile requires a non-empty id')
    budgets = profile.get('budgets')
    if not isinstance(budgets, dict):
        raise ValueError('profile requires budgets')
    for key in ('triangles_max', 'materials_max'):
        if type(budgets.get(key)) is not int or budgets[key] < 0:
            raise ValueError('budget must be a non-negative integer: ' + key)
    assets = report.get('assets') if isinstance(report, dict) else None
    if not isinstance(assets, list) or not 1 <= len(assets) <= 10000:
        raise ValueError('inspection requires 1..10000 assets; an empty report is not validation')
    results = []
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError('inspection assets must be objects')
        errors = []
        for metric in ('triangles', 'materials'):
            value = asset.get(metric)
            if type(value) is not int or value < 0:
                errors.append('missing or invalid ' + metric)
            elif value > budgets[metric + '_max']:
                errors.append(f'{metric} {value} > {budgets[metric + "_max"]}')
        if asset.get('gltf_version') != '2.0':
            errors.append('not glTF 2.0')
        if not isinstance(asset.get('path'), str) or not asset['path']:
            errors.append('asset path required')
        results.append({'path': asset.get('path'), 'ok': not errors, 'errors': errors})
    return {'profile': profile['id'], 'ok': all(x['ok'] for x in results), 'assets': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report')
    parser.add_argument('--profile', required=True)
    args = parser.parse_args()
    try:
        result = validate_report(json.loads(Path(args.report).read_text()), json.loads(Path(args.profile).read_text()))
    except (ValueError, OSError) as exc:
        result = {'ok': False, 'assets': [], 'error': str(exc)}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
