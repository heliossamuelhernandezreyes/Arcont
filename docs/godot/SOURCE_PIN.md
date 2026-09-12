# Godot Engine — fuente canónica para análisis

ARCONT conserva una referencia reproducible al código fuente del motor Godot para estudiarlo como tecnología, no como base de un juego dentro de este repositorio.

## Snapshot canónico

- Motor: Godot Engine
- Versión: 4.7.2-stable
- Repositorio upstream: https://github.com/godotengine/godot
- Tag: `4.7.2-stable`
- Commit exacto: `ed1daf0bf001b61586d9930840f2f1394092c079`
- Tree del commit: `8cce5a783df3eb396336ecfb9331aaab0c172807`
- Fecha del commit estable: 2026-08-17
- Licencia principal: MIT

El análisis de ARCONT debe citar versión, commit y ruta upstream cuando una conclusión dependa de implementación concreta.

## Política

No se añade `project.godot`, escenas de juego, gameplay ni assets de un juego bajo esta sección. Godot se estudia como motor: core, scene tree, servidores, rendering, física, navegación, audio, scripting, recursos, importación, editor, plataformas, extensiones y build system.

No se modifica silenciosamente el snapshot canónico cuando aparezca una versión nueva. Una actualización debe registrarse explícitamente para poder comparar versiones y evitar que un análisis cambie debajo de nosotros.

## Código fuente

El código fuente completo permanece en el repositorio oficial de Godot, fijado por el commit anterior. ARCONT almacena el pin reproducible y nuestros análisis, en lugar de duplicar miles de archivos upstream dentro de `main`. Esto mantiene el banco limpio y permite inspeccionar exactamente el mismo código fuente cuando sea necesario.
