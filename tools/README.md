# ARCONT operational tooling

`arcont_lab.py` convierte parte de la metodología de ARCONT en comprobaciones ejecutables usando únicamente la biblioteca estándar de Python.

No ejecuta Godot, no contiene gameplay y no sustituye la revisión científica. Su trabajo es detectar incoherencias y reducir errores mecánicos.

## Agent Control Plane

ARCONT exposes a machine-readable control plane for AI agents. ARCONT itself remains read-only; registered external game projects can be edited only with explicit permission:

```bash
python tools/arcont_agent.py capabilities
python tools/arcont_agent.py doctor
python tools/arcont_agent.py inspect-project path/to/external/game
python tools/arcont_agent.py invoke godot.authoring.control --project path/to/external/game --request request.json --allow-project-write
python tools/arcont_agent.py invoke map-forge.editor.control --project path/to/external/game --request request.json --allow-project-write
python tools/arcont_agent.py invoke production.control --project path/to/external/game --request request.json --allow-project-write
python tools/arcont_agent.py invoke model-forge.control --project path/to/external/game --request request.json --allow-project-write
python tools/arcont_agent.py run-plan --project path/to/external/game --plan plan.json --allow-project-write
python tools/arcont_agent.py diagnose --policy policy.json --evidence evidence.json --require-match
python tools/arcont_agent.py evaluate-proposal --proposal model-proposal.json --evidence evidence.json --require-match
python tools/arcont_bridge.py --project path/to/external/game --request bridge-request.json
python tools/arcont_bridge.py --project path/to/empty/game --request templates/agent/bootstrap-new-game.request.example.json --allow-project-write
python tools/arcont_bridge.py --project path/to/game --request templates/agent/stage-user-asset.request.example.json --allow-project-write
python tools/arcont_bridge.py --project path/to/game --request templates/agent/search-public-assets.request.example.json
python tools/arcont_bridge.py --project path/to/game --request templates/agent/public-asset-files.request.example.json
python tools/arcont_bridge.py --project path/to/game --request templates/agent/create-player-script.request.example.json --allow-project-write
python tools/arcont_bridge.py --project path/to/game --request templates/agent/edit-main-scene.request.example.json --allow-project-write
```

The canonical capability registry is `agent.capabilities.json`. Discovery reports repository guards, tool availability and access mode; `doctor` runs only explicitly whitelisted read-only diagnostics with bounded output and per-tool timeouts. `inspect-project` inventories an external repository without modifying it. `invoke` only accepts registered `external-project-write` tools, rejects projects embedded inside ARCONT, and requires `--allow-project-write` on every call. `run-plan` adds a bounded, revision-aware sequence layer with a capability allowlist, prior-step bindings, expectations, SHA-256 plan/registry receipts and fail-closed execution. `diagnose` is read-only: it evaluates declarative evidence/hypothesis policies, rejects ambiguous spatial selections, and can compile a repair plan that must still pass through the normal write-permission boundary. `evaluate-proposal` is the narrower model-facing gate: it accepts a novel hypothesis, permits only bounded repair primitives, and lets ARCONT add the writer, stable target path, current-value tests and revision binding. `arcont_bridge.py` is the transport-neutral front door for a fresh external agent: discovery, persistent project intent, local/user asset intake, provider-scoped public asset discovery, hypothesis evaluation and bounded plan execution all reuse the same existing control-plane safety boundary.

The full boundary and extension rules live in `docs/AGENT_CONTROL_PLANE.md`.

## Validación

```bash
python tools/arcont_lab.py validate
```

Comprueba, entre otras cosas:

- enlaces Markdown relativos rotos;
- IDs de nodos duplicados dentro de un grafo;
- edges del Knowledge Graph hacia nodos inexistentes;
- source-symbols sin `path` o `symbol`;
- estados `validated` / `reproduced` sin evidencia inline visible;
- divergencia entre el commit canónico de Godot y los grafos versionados.

Un warning no equivale automáticamente a conocimiento falso. Un error indica una incoherencia estructural que debe corregirse.

## Impact analysis

```bash
python tools/arcont_lab.py impact --changed scene/main/scene_tree.h
```

Busca source-symbols que apuntan al path modificado y recorre dependencias inversas del Knowledge Graph. La salida separa todos los nodos afectados de los que potencialmente requieren revalidación.

La ausencia de un nodo en la salida significa solamente que el grafo actual no conoce esa dependencia; no demuestra ausencia de impacto.

## Confidence engine

```bash
python tools/arcont_lab.py confidence \
  --source-quality 1 \
  --reproductions 3 \
  --hardware-profiles 2 \
  --engine-versions 1 \
  --age-days 30 \
  --contradictions 0
```

Produce un índice heurístico 0-100 con bandas `weak`, `provisional`, `moderate` y `strong`.

**No es una probabilidad estadística.** Sirve para priorizar revisión y comparar madurez relativa de evidencia bajo el mismo modelo. Una contradicción penaliza el índice, la antigüedad reduce la componente de vigencia y la diversidad de reproducciones/hardware/versiones aumenta la confianza.

## Benchmark comparison

Los resultados runtime deben exportarse a JSON siguiendo `docs/benchmarks/RESULT_SCHEMA.md`.

```bash
python tools/arcont_lab.py compare run_a.json run_b.json
```

El comparador:

- revisa compatibilidad básica de benchmark, dispositivo, CPU/GPU, renderer, resolución y build;
- calcula deltas porcentuales descriptivos para métricas disponibles;
- se niega conceptualmente a convertir un delta aislado en "regresión" estadística.

La clasificación final de una regresión requiere repetición, dispersión/incertidumbre y un umbral de ingeniería adecuado al experimento.

## Producción de sprites 2D

ARCONT ya incluye dos puertas mecánicas separadas para arte raster de producción:

```bash
python tools/png_sprite_normalize.py normalization_plan.json \
  --project-root path/to/project \
  --report normalization_report.json

python tools/png_sprite_audit.py production_sprite_manifest.json \
  --project-root path/to/project
```

`png_sprite_normalize.py` transforma masters RGBA a un canvas/pivote/baseline común con escalado bilinear premultiplicado y rechazo explícito de recortes. El plan por lotes sigue `schemas/sprite-normalization-plan.schema.json` y sólo escribe resultados si todos los frames validan.

`png_sprite_audit.py` verifica después dimensiones, límites alfa, baseline, pivote, deriva de altura, duplicados, secuencias y padding. Ninguno de los dos sustituye la revisión visual semántica de identidad, vestuario, cámara, armas o calidad artística.

El contrato completo está en `docs/knowledge/GODOT_2D_SPRITE_PIPELINE.md`.

## Principio canónico

Automatizar una comprobación no convierte una inferencia en una verdad. ARCONT mantiene la cadena:

`source -> hypothesis -> experiment -> raw result -> evidence -> rule -> decision`.
