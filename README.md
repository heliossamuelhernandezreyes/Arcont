# Arcont

Prototipo de videojuego construido con **Godot 4.7.x** y gestionado desde GitHub como fuente de verdad.

## Flujo de trabajo

- `main` contiene el estado estable del proyecto.
- Godot consume directamente los archivos del repositorio.
- Replit puede sincronizarse mediante Git para edición, herramientas y automatización.
- Los cambios deben validarse antes de integrarse a `main` cuando el proyecto crezca.

## Arranque

1. Instala Godot 4.7.2 o una versión 4.7.x compatible.
2. Clona este repositorio.
3. Abre `project.godot`.
4. Ejecuta el proyecto con F6/F5.

## Estructura inicial

- `scenes/`: escenas del juego.
- `scripts/`: lógica GDScript.
- `assets/`: arte, audio y recursos importados.
- `data/`: datos y balance.
- `tools/`: utilidades de desarrollo.

Arcont está actualmente en fase de prototipo; la arquitectura se irá especializando cuando se defina el núcleo jugable.