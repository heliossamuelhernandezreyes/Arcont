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

## Qué ya no vive aquí

El antiguo juego/prototipo ejecutable de ARCONT fue retirado del estado actual del repositorio. No se mantienen aquí sus escenas, gameplay, assets, presets de exportación ni CI destinado a compilar aquel juego.

El historial de Git permanece como registro técnico histórico, pero **HEAD/main representa el banco de conocimiento y laboratorio del motor**.

## Índice

Consulta [`docs/INDEX.md`](docs/INDEX.md).
