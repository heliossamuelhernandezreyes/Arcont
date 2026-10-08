"""Traceability checks for ARCONT's typed graph records; no truth promotion."""
from pathlib import Path
import json
import re


def validate_semantics(root: Path, nodes: dict, edges: list):
    errors = []
    dependencies = {key: set() for key in nodes}
    derivations = {key: set() for key in nodes}
    invalid = {'falsified', 'superseded'}
    for edge in edges:
        src, dst, relation = edge.get('from'), edge.get('to'), edge.get('relation')
        if src not in nodes or dst not in nodes:
            continue
        if relation in {'derived_from', 'depends_on', 'implemented_by', 'measured_by', 'supported_by'}:
            dependencies[src].add(dst)
        if relation == 'supports':
            dependencies[dst].add(src)
        if relation in {'derived_from', 'depends_on'}:
            derivations[src].add(dst)

    for key, node in nodes.items():
        evidence = node.get('evidence')
        if isinstance(evidence, str) and evidence in nodes:
            dependencies[key].add(evidence)
            derivations[key].add(evidence)

    def closure(start):
        found, pending = set(), list(dependencies[start])
        while pending:
            value = pending.pop()
            if value not in found:
                found.add(value)
                pending.extend(dependencies[value])
        return found

    # Kahn's algorithm avoids recursion limits on large knowledge graphs.
    incoming = {key: 0 for key in nodes}
    for values in derivations.values():
        for value in values:
            incoming[value] += 1
    ready = [key for key, count in incoming.items() if count == 0]
    visited = set()
    while ready:
        key = ready.pop()
        visited.add(key)
        for value in derivations[key]:
            incoming[value] -= 1
            if incoming[value] == 0:
                ready.append(value)
    if len(visited) != len(nodes):
        errors.append('derivation-cycle: ' + ', '.join(sorted(set(nodes) - visited)))

    for key, node in nodes.items():
        kind, status = node.get('kind'), node.get('status')
        evidence = node.get('evidence')
        if evidence:
            if isinstance(evidence, str) and evidence in nodes:
                pass  # Already included before cycle and closure checks.
            elif isinstance(evidence, str):
                path = (root / evidence.split('#', 1)[0]).resolve()
                if root.resolve() not in path.parents or not path.is_file():
                    errors.append(f'unresolved-evidence: {key}: {evidence}')
            else:
                errors.append(f'invalid-evidence-reference: {key}')
        if kind == 'source-symbol' and not re.fullmatch(r'[0-9a-fA-F]{40}', str(node.get('_engine_commit', ''))):
            errors.append(f'unpinned-source: {key}')
        if kind == 'benchmark' and status not in {'preregistered', 'proposed', 'planned'}:
            result = node.get('result')
            if not isinstance(result, str) or not (root / result).is_file():
                errors.append(f'benchmark-without-result: {key}')
            else:
                try:
                    try:
                        from tools.arcont_hardening import validate_result
                    except ModuleNotFoundError:
                        from arcont_hardening import validate_result
                    errors.extend(f'{key}: {err}' for err in validate_result(json.loads((root / result).read_text())))
                except (OSError, ValueError) as exc:
                    errors.append(f'invalid-benchmark-result: {key}: {exc}')

    for key, node in nodes.items():
        related = closure(key)
        kind, status = node.get('kind'), node.get('status')
        if kind in {'rule', 'decision'}:
            traced = any(nodes[ref].get('kind') in {'source-symbol', 'observation'}
                         and nodes[ref].get('status') not in invalid for ref in related)
            if not traced:
                errors.append(f'{kind}-without-evidence-path: {key}')
        if kind == 'decision' or status in {'validated', 'reproduced'}:
            bad = sorted(ref for ref in related if nodes[ref].get('status') in invalid)
            if bad:
                errors.append(f'invalidated-dependency: {key}: {bad}')
        maturity = node.get('maturity')
        if kind == 'rule' and status == 'validated':
            maturity = 'L7_VALIDATED_RULE'
        if maturity:
            try:
                try:
                    from tools.arcont_hardening import check_maturity
                except ModuleNotFoundError:
                    from arcont_hardening import check_maturity
                errors.extend(f'{key}: {err}' for err in check_maturity(maturity, node))
            except (TypeError, ValueError):
                errors.append(f'invalid-maturity-evidence: {key}')
    return errors
