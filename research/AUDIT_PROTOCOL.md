# Arcont Reference Lab — Continuous Audit Protocol

## Purpose
This branch is Arcont's persistent technical memory and research laboratory. It stores knowledge, references, experiments, rejected approaches, production lessons and future-facing material so development can consult existing knowledge before repeating broad research.

Nothing in this branch is a production dependency unless deliberately reviewed and integrated elsewhere.

## Workflow
1. Define the production problem or research question.
2. Search the Reference Lab by topic and tags before external research.
3. Reuse existing findings when still current.
4. If knowledge is missing, perform focused research rather than a full sweep.
5. Record source, license, applicability, constraints and confidence.
6. Test candidate patterns in isolation when practical.
7. Record the result: CANDIDATE, TESTING, IMPLEMENTED, REJECTED, SUPERSEDED or WATCH.
8. Link implementation evidence when a finding reaches production.
9. Re-audit topics when Godot, Android targets, hardware assumptions or Arcont architecture materially change.

## Evidence hierarchy
1. Official Godot documentation / engine source / platform documentation.
2. Reproducible measurements and Arcont device profiling.
3. Mature permissively licensed implementations.
4. Technical talks, papers and postmortems.
5. Community examples and experiments.
6. Anecdotes — useful as leads, never as final evidence.

## Reference record
Every important finding should preserve:
- Topic and tags
- Finding / principle
- Source URL and access date when relevant
- Source type
- License / reuse status
- Godot/platform version
- Applicability to Arcont
- Risks and tradeoffs
- Status
- Production evidence or experiment result
- Re-audit trigger

## Rules
- Prefer principles over blind code copying.
- Preserve attribution and license information.
- Prefer MIT, BSD, Apache, CC0 and other compatible permissive material.
- Unknown license means reference-only until clarified.
- Never merge this branch wholesale into production.
- Keep Arcont mobile-first unless a deliberate product decision changes it.
- Treat real-device profiling as stronger evidence than desktop intuition.
- Preserve rejected approaches: knowing why something failed prevents repeated work.
- Store useful adjacent knowledge even when it has no immediate implementation.

## Continuous audit
The lab should be incrementally audited whenever work touches a domain. A full sweep is reserved for major engine upgrades, architecture changes, vertical-slice milestones, or explicit audits.
