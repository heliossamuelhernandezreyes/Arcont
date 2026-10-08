#!/usr/bin/env python3
"""Deliver a project-owned model through the shared transactional staging gate."""
import argparse
import json
from pathlib import Path
try:
    from tools.model_forge_control import respond
except ModuleNotFoundError:
    from model_forge_control import respond


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model', help='path relative to the external project')
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--semantic-id', required=True)
    parser.add_argument('--out', required=True, help='destination relative to the external project')
    parser.add_argument('--profile', help='budget profile JSON; required unless --candidate')
    parser.add_argument('--candidate', action='store_true', help='explicitly stage an uncertified candidate')
    args = parser.parse_args()
    request = {'protocol_version': 1, 'operation': 'stage', 'model': args.model,
               'semantic_id': args.semantic_id, 'destination': args.out,
               'delivery_mode': 'candidate' if args.candidate else 'validated'}
    if args.profile:
        request['profile'] = json.loads(Path(args.profile).read_text())
    result = respond(args.project, request)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
