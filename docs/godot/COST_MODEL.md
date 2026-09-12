# Godot Cost Model

Este documento convierte el análisis de Godot en un modelo empírico de costes. No pretende asignar números universales: cada cifra debe proceder de un experimento reproducible.

## Unidad de análisis

Para cada operación o subsistema registrar:

- coste fijo de existencia;
- coste incremental por instancia;
- coste por frame;
- coste por tick de física;
- coste de creación y destrucción;
- memoria residente y asignaciones;
- coste CPU/GPU cuando sea separable;
- escalado con N;
- punto de inflexión;
- sensibilidad al hardware, renderer y versión del motor.

## Primer conjunto

1. Node y Node3D inactivos.
2. `_process()` y `_physics_process()`.
3. señales y llamadas directas.
4. `instantiate()` y `queue_free()`.
5. MeshInstance3D frente a MultiMesh.
6. materiales únicos frente a compartidos.
7. cuerpos físicos activos e inactivos.
8. agentes de navegación.
9. AnimationPlayer / AnimationTree.
10. AudioStreamPlayer.

## Curvas, no números mágicos

Cada benchmark debe producir una serie N→coste. El objetivo es reconocer la forma de la curva y sus cambios de régimen, no publicar un único FPS.

Registrar al menos p50, p95 y p99 de frame time cuando sea posible. Separar warm-up de medición y repetir las corridas.

## Regla de interpretación

Una observación de un dispositivo no se generaliza automáticamente. Debe etiquetarse por versión de Godot, commit, plataforma, renderer, dispositivo, configuración térmica y configuración del experimento.

Una recomendación solo asciende a regla de ARCONT cuando existe evidencia suficiente bajo `LAB_STANDARD.md`.