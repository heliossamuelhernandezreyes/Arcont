# ARCONT Knowledge Schema

ARCONT debe ser legible por humanos y también consultable por herramientas o agentes de IA sin depender de interpretar prosa ambigua.

## Metadatos recomendados

Cada análisis, experimento, benchmark, patrón o resultado negativo debe poder expresar:

```yaml
id: ARC-...
kind: source-analysis | experiment | benchmark | pattern | anti-pattern | negative-result | decision
status: proposed | observed | reproduced | validated | superseded | falsified
engine: godot
engine_version: 4.7.2-stable
engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
subsystem: rendering
platform: android
hardware: null
renderer: null
hypothesis: null
metrics: []
evidence: []
limitations: []
related: []
created: YYYY-MM-DD
last_validated: null
```

## Principios

- IDs estables y únicos.
- Campos desconocidos son `null`; no se inventan.
- Evidencia enlaza a fuentes o experimentos concretos.
- Relaciones son explícitas.
- Las conclusiones conservan versión y plataforma.
- Los datos brutos y la interpretación permanecen separables.

## Objetivo

Permitir que en el futuro podamos preguntar a ARCONT, por ejemplo, qué sabemos sobre MultiMesh en Android, y recuperar evidencia, límites, benchmarks, resultados negativos y reglas sin recorrer manualmente todo el repositorio.