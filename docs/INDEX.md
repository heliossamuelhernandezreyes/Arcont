# Índice del banco de conocimiento ARCONT

ARCONT se organiza por conocimientos reutilizables, no por un juego concreto.

## Motor — Godot

- [`godot/SOURCE_PIN.md`](godot/SOURCE_PIN.md) — snapshot canónico y reproducible de Godot 4.7.2-stable para análisis del motor.
- [`godot/ANALYSIS_MAP.md`](godot/ANALYSIS_MAP.md) — mapa de estudio de core, escenas, render, física, navegación, audio, scripting, assets, animación, editor, Android, build system, profiling y extensibilidad.

Godot se conserva aquí como **objeto de estudio del motor**, no como un videojuego. El código fuente upstream se fija por versión y commit; ARCONT conserva nuestros análisis y experimentos mínimos sin duplicar innecesariamente todo el repositorio oficial.

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

Este repositorio no debe volver a contener un juego completo. Los proyectos futuros pueden consultar ARCONT, copiar ideas o implementar módulos inspirados en él, pero su código de producción debe vivir en repositorios propios.
