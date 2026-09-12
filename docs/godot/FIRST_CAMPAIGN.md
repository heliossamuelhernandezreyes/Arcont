# First Godot Research Campaign — Fundamental Cost Model

Esta es la primera campaña empírica de ARCONT. No construye un juego.

## Pregunta

¿Cuál es el coste real y la curva de escalado de las primitivas fundamentales de Godot 4.7.2-stable en las plataformas que probemos?

## Fase A — baseline

- proyecto vacío de laboratorio;
- renderer y resolución fijados;
- escena vacía;
- warm-up definido;
- captura de frame time, memoria y estabilidad.

## Fase B — SceneTree

Barridos de N para Node y Node3D inactivos y con callbacks de proceso. Separar `_process()` de `_physics_process()`.

## Fase C — lifecycle

Medir creación, `instantiate()`, entrada/salida del árbol, `queue_free()` y churn sostenido.

## Fase D — comunicación

Comparar llamada directa, señal y otras rutas relevantes bajo cargas controladas. No inferir conclusiones antes de medir.

## Fase E — rendering

Comparar MeshInstance3D, recursos/materiales compartidos y MultiMesh mediante curvas N→frame-time/draw-calls/memoria.

## Fase F — subsistemas

Extender después a física, navegación, animación, audio y carga de recursos.

## Diseño de barrido

Usar escalas geométricas cuando tenga sentido (por ejemplo 1, 10, 100, 1k, 10k...) y densificar alrededor de puntos de inflexión. No fijar anticipadamente un máximo que pueda bloquear o dañar el dispositivo; detener la prueba bajo criterios térmicos/de estabilidad definidos.

## Productos

Cada prueba debe producir:

1. metadatos completos;
2. datos brutos;
3. resumen estadístico;
4. gráfica o tabla derivada cuando corresponda;
5. observaciones;
6. interpretación separada;
7. entrada del Evidence Ledger;
8. decisión o regla solo si la evidencia lo permite.

## Criterio de éxito

La campaña termina cuando podemos describir curvas y límites con incertidumbre explícita, no cuando encontramos un número espectacular.