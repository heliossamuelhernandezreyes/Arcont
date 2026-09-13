# ARCONT

ARCONT ya no es un videojuego.

Desde septiembre de 2026, este repositorio funciona como **banco de información y laboratorio técnico para el desarrollo de videojuegos**: investigación, patrones de arquitectura, experimentos, decisiones, errores, aprendizajes y referencias reutilizables.

## Godot como objeto de estudio

ARCONT conserva una referencia canónica y reproducible al código fuente de **Godot Engine 4.7.2-stable** para poder analizar el motor de forma limpia, sin mezclar ese análisis con un juego concreto.

El snapshot está fijado al commit upstream `ed1daf0bf001b61586d9930840f2f1394092c079`. Los detalles y la metodología viven en `docs/godot/`.

Esto no convierte ARCONT otra vez en un proyecto de Godot: aquí estudiamos el motor. Los juegos de producción deben vivir en repositorios separados.

## Propósito

- Comprender Godot internamente y registrar conocimiento verificable sobre el motor.
- Conservar conocimiento técnico útil para futuros juegos.
- Documentar soluciones probadas y resultados negativos.
- Servir como laboratorio de render, física, navegación, audio, animación, scripting, diseño, rendimiento móvil, IA, combate, generación procedural y pipelines 3D.
- Evitar que prototipos específicos se conviertan accidentalmente en dependencias canónicas.

## Toolchains indexados

- **Map authoring / level design:** [`docs/knowledge/MAP_AUTHORING_TOOLCHAIN.md`](docs/knowledge/MAP_AUTHORING_TOOLCHAIN.md) y su registro reproducible [`MAP_AUTHORING_TOOLCHAIN.yaml`](docs/knowledge/MAP_AUTHORING_TOOLCHAIN.yaml). Incluye Terrain3D, Cyclops Level Builder, ProtonScatter y FuncGodot con licencia, upstream revisado, SHA observado, rol, riesgos y backlog de validación.
- **ARCONT Map Forge:** [`docs/knowledge/MAP_FORGE_STANDARD.md`](docs/knowledge/MAP_FORGE_STANDARD.md) define el estándar portable y agnóstico de motor derivado de la primera implementación validada en Close Seal. El contrato reusable vive en [`schemas/map-authoring-contract.schema.json`](schemas/map-authoring-contract.schema.json), con plantilla en [`templates/map-forge/map_contract.example.json`](templates/map-forge/map_contract.example.json) y validador independiente en [`tools/map_forge_contract.py`](tools/map_forge_contract.py).

Map Forge no convierte ARCONT en un editor ejecutable ni en un proyecto Godot. ARCONT conserva el estándar, contrato, validación, evidencia y patrones de adaptadores; cada juego implementa su editor físico y runtime bridge en su propio repositorio.

## Qué ya no vive aquí

El antiguo juego/prototipo ejecutable de ARCONT fue retirado del estado actual del repositorio. No se mantienen aquí sus escenas, gameplay, assets, presets de exportación ni CI destinado a compilar aquel juego.

El historial de Git permanece como registro técnico histórico, pero **HEAD/main representa el banco de conocimiento y laboratorio del motor**.

## Índice

Consulta [`docs/INDEX.md`](docs/INDEX.md).
