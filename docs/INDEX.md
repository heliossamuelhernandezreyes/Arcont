# Índice del banco de conocimiento ARCONT

ARCONT se organiza por conocimientos reutilizables, no por un juego concreto.

## ARCONT 1.0

- [`../arcont.manifest.json`](../arcont.manifest.json) — manifiesto canónico de versión, rol del repositorio, motor fijado y contratos de integridad.
- [`MATURITY_MODEL.md`](MATURITY_MODEL.md) — niveles L0–L7 y reglas de promoción/degradación del conocimiento.
- [`PROVENANCE_AND_IMMUTABILITY.md`](PROVENANCE_AND_IMMUTABILITY.md) — procedencia, SHA-256 e inmutabilidad de evidencia publicada.
- [`../schemas/benchmark-result.schema.json`](../schemas/benchmark-result.schema.json) — contrato machine-readable de resultados de benchmark.

ARCONT 1.0 fija que no se admite código de juego de producción ni un proyecto Godot embebido. La evidencia runtime se produce externamente y se incorpora con procedencia verificable.

## Biblioteca general de ingeniería de videojuegos

- [`knowledge/GAME_DEV_ATLAS.md`](knowledge/GAME_DEV_ATLAS.md) — atlas transversal `shared / 2D / 2.5D / 3D`, dominios técnicos, motores y jerarquía de fuentes.
- [`knowledge/SOURCE_REGISTRY.yaml`](knowledge/SOURCE_REGISTRY.yaml) — registro curado de fuentes primarias, oficiales y referencias técnicas seleccionadas.
- [`knowledge/ACQUISITION_ROADMAP.md`](knowledge/ACQUISITION_ROADMAP.md) — oleadas de adquisición para fundamentos, 2D, 2.5D, 3D, sistemas transversales, plataformas y comparativas entre motores.
- [`knowledge/campaigns/FOUNDATION_ACQUISITION_01.md`](knowledge/campaigns/FOUNDATION_ACQUISITION_01.md) — primera campaña transversal de adquisición.
- [`knowledge/GRAPHICS_ASSET_FOUNDATIONS.md`](knowledge/GRAPHICS_ASSET_FOUNDATIONS.md) — Vulkan, KTX2/Basis, asset delivery y preguntas de investigación para 2D/2.5D/3D.
- [`knowledge/MOBILE_PERFORMANCE_FOUNDATIONS.md`](knowledge/MOBILE_PERFORMANCE_FOUNDATIONS.md) — frame pacing, refresh, termales, rendimiento sostenido y profiling Android.
- [`knowledge/NETWORKING_FOUNDATIONS.md`](knowledge/NETWORKING_FOUNDATIONS.md) — snapshots, lockstep, prediction/reconciliation, rollback y networked physics.

### Segunda gran oleada

- [`knowledge/SECOND_WAVE_OVERVIEW.md`](knowledge/SECOND_WAVE_OVERVIEW.md) — alcance, fuentes, límites y familias de benchmarks de la segunda adquisición.
- [`knowledge/AI_NAVIGATION.md`](knowledge/AI_NAVIGATION.md) — navmesh, Recast/Detour, tiles, queries, crowds, rebuild y streaming de navegación.
- [`knowledge/PHYSICS_SIMULATION.md`](knowledge/PHYSICS_SIMULATION.md) — rigid bodies, contactos, constraints, queries, CCD, lifecycle y destrucción.
- [`knowledge/PROCEDURAL_ANIMATION.md`](knowledge/PROCEDURAL_ANIMATION.md) — PCG, particionado, determinismo, animación, IK, full-body IK y retargeting.
- [`knowledge/DATA_ORIENTED_CONCURRENCY.md`](knowledge/DATA_ORIENTED_CONCURRENCY.md) — ECS, archetypes/chunks, structural changes, jobs, threading y sincronización.
- [`knowledge/GPU_AUDIO_STREAMING.md`](knowledge/GPU_AUDIO_STREAMING.md) — GPU passes/sync/bandwidth, audio DSP/voices, memoria y asset streaming.

ARCONT no intenta copiar Internet. Conserva referencias, procedencia, extracción técnica, preguntas verificables y, únicamente cuando sea legal y útil, material redistribuible. Godot es el primer motor bajo análisis profundo, no el límite temático de ARCONT.

## Laboratorio técnico

- [`LAB_STANDARD.md`](LAB_STANDARD.md) — estándar del laboratorio: SOURCE → EXPERIMENT → RULE, reproducibilidad y estados de validez.
- [`EXPERIMENT_TEMPLATE.md`](EXPERIMENT_TEMPLATE.md) — plantilla canónica para experimentos mínimos.
- [`BENCHMARK_STANDARD.md`](BENCHMARK_STANDARD.md) — protocolo de benchmarks comparables.
- [`DECISION_RECORD_TEMPLATE.md`](DECISION_RECORD_TEMPLATE.md) — decisiones técnicas trazables.
- [`EVIDENCE_LEDGER.md`](EVIDENCE_LEDGER.md) — registro de afirmaciones, evidencia, confianza, límites y falsaciones.
- [`KNOWLEDGE_SCHEMA.md`](KNOWLEDGE_SCHEMA.md) — esquema legible por humanos y herramientas.
- [`KNOWLEDGE_GRAPH.md`](KNOWLEDGE_GRAPH.md) — relaciones explícitas entre fuentes, subsistemas, experimentos, reglas y decisiones.
- [`DECISION_ENGINE.md`](DECISION_ENGINE.md) — transformación de evidencia en recomendaciones condicionadas y revalidables.
- [`VALIDATOR_SPEC.md`](VALIDATOR_SPEC.md) — especificación del validador de trazabilidad, evidencia, vigencia y coherencia del grafo.

## Herramientas operativas

- [`../tools/arcont_lab.py`](../tools/arcont_lab.py) — CLI para integridad, análisis de impacto, confianza heurística y comparación de resultados.
- [`../tools/arcont_hardening.py`](../tools/arcont_hardening.py) — validador ARCONT 1.0 para manifiesto, contratos de evidencia, SHA-256 y madurez.
- [`../tools/README.md`](../tools/README.md) — uso y límites de las herramientas.
- [`../tests/test_arcont_hardening.py`](../tests/test_arcont_hardening.py) — pruebas unitarias y controles negativos del hardening.
- [`.github/workflows/knowledge-integrity.yml`](../.github/workflows/knowledge-integrity.yml) — CI automática en `push` y `pull_request`.

Estas herramientas automatizan comprobaciones mecánicas; no convierten una inferencia en evidencia ni una observación aislada en regla.

## Benchmarks y evidencia runtime

- [`benchmarks/EXTERNAL_SUITE_SPEC.md`](benchmarks/EXTERNAL_SUITE_SPEC.md) — contrato de la suite externa de microbenchmarks.
- [`benchmarks/RESULT_SCHEMA.md`](benchmarks/RESULT_SCHEMA.md) — formato documental de resultados.
- [`benchmarks/INGESTION_AND_COMPARISON.md`](benchmarks/INGESTION_AND_COMPARISON.md) — ingesta, comparabilidad, regresiones y promoción de evidencia.
- [`../schemas/benchmark-result.schema.json`](../schemas/benchmark-result.schema.json) — schema formal para validación automática.

La suite runtime permanece separada del banco de conocimiento. Produce datos; ARCONT conserva hashes, evidencia, relaciones, interpretaciones y decisiones.

## Motor — Godot

- [`godot/SOURCE_PIN.md`](godot/SOURCE_PIN.md) — snapshot canónico y reproducible de Godot 4.7.2-stable.
- [`godot/ANALYSIS_MAP.md`](godot/ANALYSIS_MAP.md) — mapa inicial de estudio.
- [`godot/ENGINE_ATLAS.md`](godot/ENGINE_ATLAS.md) — atlas de subsistemas internos del motor.
- [`godot/RESEARCH_ROADMAP.md`](godot/RESEARCH_ROADMAP.md) — programa de investigación y validación.
- [`godot/COST_MODEL.md`](godot/COST_MODEL.md) — marco para obtener curvas empíricas de coste del motor.
- [`godot/FIRST_CAMPAIGN.md`](godot/FIRST_CAMPAIGN.md) — primera campaña experimental sobre costes fundamentales.
- [`godot/SOURCE_TRACE_PROTOCOL.md`](godot/SOURCE_TRACE_PROTOCOL.md) — trazabilidad desde API pública hasta implementación y backend.
- [`godot/FRAME_LIFECYCLE_TRACE.md`](godot/FRAME_LIFECYCLE_TRACE.md) — primera disección verificada: MainLoop → SceneTree → ProcessGroup → Node y ciclo de frame.
- [`godot/knowledge/scene_tree_graph.yaml`](godot/knowledge/scene_tree_graph.yaml) — primera porción machine-readable del grafo de conocimiento real.
- [`godot/SENTINEL_SUITE.md`](godot/SENTINEL_SUITE.md) — batería mínima para detectar regresiones entre versiones y plataformas.
- [`godot/UPGRADE_PROTOCOL.md`](godot/UPGRADE_PROTOCOL.md) — protocolo para actualizar la versión canónica sin perder conocimiento previo.

Godot se conserva como **objeto de estudio del motor**, no como videojuego. El upstream se fija por versión y commit; ARCONT conserva análisis y evidencia sin duplicar innecesariamente el repositorio oficial.

## Ingeniería

- [`engineering/mobile-performance.md`](engineering/mobile-performance.md) — presupuestos y estrategias para móviles.
- [`engineering/world-generation.md`](engineering/world-generation.md) — terreno, ecología, hidrología y composición procedural.
- [`engineering/ai-navigation.md`](engineering/ai-navigation.md) — navegación, grafos y límites del enfoque usado.
- [`engineering/combat-systems.md`](engineering/combat-systems.md) — patrones extraídos de armas, melee, feedback y dirección de combate.
- [`engineering/destruction.md`](engineering/destruction.md) — coberturas destructibles, estados de daño y física temporal.

## Referencias

- [`ASSET_SOURCES.md`](ASSET_SOURCES.md) — criterios para fuentes y licencias.
- [`HISTORY.md`](HISTORY.md) — transición de prototipo jugable a banco de información.

## Regla canónica

Este repositorio no debe volver a contener un juego completo. Los proyectos futuros pueden consultar ARCONT y reutilizar conocimiento, pero su código de producción debe vivir en repositorios propios.

Los experimentos de ARCONT deben permanecer mínimos, aislados y reproducibles. El runtime ejecutable de benchmarks vive fuera de ARCONT y entrega resultados mediante el esquema canónico con procedencia y hashes verificables.
