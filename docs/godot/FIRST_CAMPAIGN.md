# First Godot Research Campaign — Fundamental Cost Model

Esta es la primera campaña empírica de ARCONT. No construye un juego.

## Estado

La campaña ya está **prerregistrada** de forma machine-readable en [`../benchmarks/FIRST_RUNTIME_MATRIX.json`](../benchmarks/FIRST_RUNTIME_MATRIX.json). Ese archivo, y no esta prosa, fija IDs, hipótesis, barridos, warm-up, duración de muestra, repeticiones, métricas, controles y criterios de aborto.

`preregistered` no significa `observed`: hasta que existan resultados runtime externos válidos, las hipótesis permanecen en L2 como máximo.

## Pregunta

¿Cuál es el coste real y la curva de escalado de las primitivas fundamentales de Godot 4.7.2-stable en las plataformas que probemos?

## Fase A — baseline

- proyecto vacío de laboratorio;
- renderer y resolución fijados;
- escena vacía;
- warm-up definido;
- captura de frame time, memoria y estabilidad.

Benchmark inicial: `ARC-BENCH-BASELINE-EMPTY-001`.

## Fase B — SceneTree

Barridos de N para Node inactivo y callbacks de proceso. `_process()` y `_physics_process()` se miden por separado.

Benchmarks iniciales:

- `ARC-BENCH-SCENETREE-INACTIVE-NODE-001`;
- `ARC-BENCH-SCENETREE-PROCESS-NODE-001`;
- `ARC-BENCH-SCENETREE-PHYSICS-NODE-001`.

## Fase C — lifecycle y orden

La primera campaña comienza por churn de prioridad como prueba de cambios en organización de proceso:

- `ARC-BENCH-SCENETREE-PRIORITY-CHURN-001`.

Creación, `instantiate()`, entrada/salida del árbol y `queue_free()` se añaden después de completar el primer circuito de evidencia de extremo a extremo.

## Fase D — comunicación

Comparar llamada directa, señal y otras rutas relevantes bajo cargas controladas. No inferir conclusiones antes de medir.

## Fase E — rendering

Comparar MeshInstance3D, recursos/materiales compartidos y MultiMesh mediante curvas N→frame-time/draw-calls/memoria.

## Fase F — subsistemas

Extender después a física, navegación, animación, audio y carga de recursos.

## Diseño de barrido

El diseño efectivo vive en `FIRST_RUNTIME_MATRIX.json`. Los cambios a barridos o controles después de observar resultados requieren una nueva versión/prerregistro; no se edita retrospectivamente una hipótesis para ajustarla a los datos.

Usar escalas geométricas cuando tenga sentido y densificar alrededor de puntos de inflexión sólo en una campaña posterior explícita. Nunca fijar anticipadamente un máximo que pueda bloquear o dañar el dispositivo; los criterios de aborto forman parte del plan.

## Runner externo

La implementación ejecutable vive fuera de ARCONT y debe seguir [`../benchmarks/HARNESS_IMPLEMENTATION_SPEC.md`](../benchmarks/HARNESS_IMPLEMENTATION_SPEC.md).

Un manifest concreto para un runner se genera con:

```bash
python tools/runtime_evidence.py emit-manifest ARC-BENCH-SCENETREE-INACTIVE-NODE-001
```

## Productos

Cada prueba debe producir:

1. metadatos completos;
2. datos brutos;
3. SHA-256 de los datos brutos;
4. commit exacto del harness;
5. resumen estadístico;
6. observaciones;
7. interpretación separada;
8. entrada del Evidence Ledger;
9. decisión o regla sólo si la evidencia lo permite.

Antes de entrar como evidencia runtime, cada resultado debe pasar:

```bash
python tools/runtime_evidence.py validate-result path/to/run.result.json
```

## Criterio de éxito

La campaña termina cuando podemos describir curvas y límites con incertidumbre explícita, no cuando encontramos un número espectacular. Una única corrida válida puede crear una observación L3; no basta para L4, L5, L6 ni L7.
