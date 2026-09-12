# Godot Sentinel Suite

La Sentinel Suite es la batería mínima que ARCONT debe repetir para detectar cambios importantes entre versiones, configuraciones o plataformas.

## Objetivo

Detectar regresiones y mejoras sin tener que ejecutar toda la investigación histórica.

## Casos centinela

1. Baseline de escena vacía.
2. Node/Node3D inactivos a varios N.
3. `_process()` y `_physics_process()`.
4. instanciación y liberación sostenida.
5. señales frente a llamadas directas.
6. MeshInstance3D frente a MultiMesh.
7. materiales compartidos frente a únicos.
8. cuerpos físicos activos/inactivos.
9. agentes de navegación.
10. AnimationPlayer/AnimationTree.
11. reproducción de audio y mezcla básica.
12. carga/caché de recursos.
13. Android: frame pacing, memoria y comportamiento térmico cuando haya dispositivo disponible.

## Salida mínima

Para cada caso:

- commit de Godot;
- plataforma y renderer;
- hardware;
- configuración;
- tamaño N;
- warm-up;
- repeticiones;
- frame-time p50/p95/p99;
- FPS medio como métrica secundaria;
- memoria;
- draw calls o métricas específicas cuando existan;
- incidencias y desviaciones.

## Comparación

Una nueva corrida debe compararse con una línea base compatible. No comparar resultados de hardware/configuraciones diferentes como si fueran una regresión del motor.

## Umbrales

Los umbrales no son universales. Cada benchmark puede declarar su sensibilidad. Un cambio debe marcarse para revisión cuando supere el ruido esperado o altere la forma de la curva.

## Resultado

La Sentinel Suite no decide por sí sola. Produce evidencia para el Evidence Ledger y activa revalidación de reglas relacionadas mediante el Knowledge Graph.