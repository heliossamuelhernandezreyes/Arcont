# ARCONT External Microbenchmark Suite Specification

ARCONT no contiene un juego ni un proyecto Godot ejecutable. Las pruebas runtime deben vivir en una suite externa y mínima, separada del banco de conocimiento.

## Propósito

La suite existe únicamente para producir evidencia reproducible sobre el motor. No contiene campaña, personajes, gameplay, niveles, assets de producción ni lógica de producto.

## Contrato con ARCONT

Cada benchmark externo debe:

- declarar un ID estable `ARC-BENCH-*`;
- fijar versión y commit exactos de Godot;
- registrar plataforma, dispositivo, renderer y resolución;
- registrar warm-up, duración, repeticiones y criterios de aborto;
- emitir resultados compatibles con `RESULT_SCHEMA.md`;
- separar datos crudos, resumen estadístico e interpretación;
- enlazar uno o más nodos del Knowledge Graph;
- declarar hipótesis antes de observar el resultado.

## Familias iniciales

### SceneTree
- Node inactivo
- Node3D inactivo
- `_process()`
- `_physics_process()`
- cambio de prioridad
- entrada/salida del árbol
- churn de `instantiate()` / `queue_free()`

### Comunicación
- llamada directa
- signal
- deferred call
- group call

### Rendering
- MeshInstance3D
- materiales compartidos vs únicos
- MultiMesh
- visibilidad/culling

### Física
- bodies activos/inactivos
- shapes
- queries
- contactos

### Navegación
- regions
- agents
- avoidance
- links

### Animación
- AnimationPlayer
- AnimationTree
- Skeleton3D

### Audio
- AudioStreamPlayer
- buses
- spatial audio

## Diseño

Las pruebas deben ser pequeñas y monotemáticas. Una prueba que mide dos cosas a la vez debe dividirse.

La escala se barre progresivamente. Se recomienda una secuencia geométrica y densificación cerca de puntos de inflexión.

Nunca se asume que el mayor N posible es seguro. La suite debe detenerse por temperatura, memoria, congelamiento, frame time extremo o inestabilidad según límites configurados.

## Resultado

La suite externa produce evidencia. ARCONT conserva el conocimiento derivado, sus metadatos, relaciones, decisiones y referencias a los resultados.