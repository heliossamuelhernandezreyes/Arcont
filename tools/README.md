# ARCONT operational tooling

`arcont_lab.py` convierte parte de la metodología de ARCONT en comprobaciones ejecutables usando únicamente la biblioteca estándar de Python.

No ejecuta Godot, no contiene gameplay y no sustituye la revisión científica. Su trabajo es detectar incoherencias y reducir errores mecánicos.

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

## Principio canónico

Automatizar una comprobación no convierte una inferencia en una verdad. ARCONT mantiene la cadena:

`source -> hypothesis -> experiment -> raw result -> evidence -> rule -> decision`.
