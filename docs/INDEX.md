# Índice del banco de conocimiento ARCONT

ARCONT se organiza por conocimientos reutilizables, no por un juego concreto.

## Laboratorio técnico

- [`LAB_STANDARD.md`](LAB_STANDARD.md) — estándar del laboratorio: SOURCE → EXPERIMENT → RULE, reproducibilidad y estados de validez.
- [`EXPERIMENT_TEMPLATE.md`](EXPERIMENT_TEMPLATE.md) — plantilla canónica para experimentos mínimos.
- [`BENCHMARK_STANDARD.md`](BENCHMARK_STANDARD.md) — protocolo de benchmarks comparables.
- [`DECISION_RECORD_TEMPLATE.md`](DECISION_RECORD_TEMPLATE.md) — decisiones técnicas trazables.

## Motor — Godot

- [`godot/SOURCE_PIN.md`](godot/SOURCE_PIN.md) — snapshot canónico y reproducible de Godot 4.7.2-stable.
- [`godot/ANALYSIS_MAP.md`](godot/ANALYSIS_MAP.md) — mapa inicial de estudio.
- [`godot/ENGINE_ATLAS.md`](godot/ENGINE_ATLAS.md) — atlas de subsistemas internos del motor.
- [`godot/RESEARCH_ROADMAP.md`](godot/RESEARCH_ROADMAP.md) — programa de investigación y validación.

Godot se conserva aquí como **objeto de estudio del motor**, no como un videojuego. El código fuente upstream se fija por versión y commit; ARCONT conserva análisis y experimentos mínimos sin duplicar innecesariamente todo el repositorio oficial.

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

Los experimentos de ARCONT deben permanecer mínimos, aislados y reproducibles.