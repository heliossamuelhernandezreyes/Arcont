# Godot Frame Lifecycle Trace — 4.7.2-stable

Commit canónico: `ed1daf0bf001b61586d9930840f2f1394092c079`

## Alcance

Primera disección real del motor dentro de ARCONT. Este documento describe únicamente lo que puede sostenerse a partir del código fuente fijado; las conclusiones de coste runtime siguen siendo hipótesis hasta que se midan.

## MainLoop

Ruta upstream: `core/os/main_loop.h`

`MainLoop` deriva de `Object` y define el contrato virtual de ciclo principal mediante `initialize()`, `iteration_prepare()`, `physics_process(double)`, `iteration_end()`, `process(double)` y `finalize()`.

`SceneTree` implementa ese contrato como el main loop de escenas.

## SceneTree

Rutas upstream:

- `scene/main/scene_tree.h`
- `scene/main/scene_tree.cpp`

`SceneTree` deriva directamente de `MainLoop`.

Internamente mantiene `ProcessGroup` con:

- `Vector<Node *> nodes` para proceso normal;
- `Vector<Node *> physics_nodes` para física;
- colas de llamadas;
- flags de orden sucio independientes;
- owner y last-pass.

Los grupos se almacenan mediante `PagedAllocator<ProcessGroup, true>`; el propio código declara que la finalidad es mejorar el uso de caché. También existe caché local de grupos de proceso y soporte explícito para grupos en sub-thread.

### Física

En `SceneTree::physics_process(double)` se observa, entre otras operaciones:

1. incremento de `current_frame`;
2. flush de notificaciones de transform;
3. llamada a `MainLoop::physics_process`;
4. actualización de `physics_process_time`;
5. emisión de `physics_frame`;
6. procesamiento de elementos asociados al frame de física;
7. `_process(true)` para los grupos correspondientes;
8. flush de unique group calls y `MessageQueue`;
9. timers y tweens de física;
10. nuevo flush de transformaciones;
11. limpieza diferida en el orden definido por el motor.

Esto prueba que `_physics_process()` de los nodos no constituye por sí solo el frame de física completo: vive dentro de una secuencia más amplia del SceneTree.

### Proceso normal

`SceneTree::process(double)` llama primero a `MainLoop::process`, registra `process_time`, puede realizar polling de multiplayer y después ejecuta otras etapas del frame de proceso, incluidos timers/tweens no físicos, transform notifications y limpieza diferida.

## Node

Ruta upstream: `scene/main/node.h`

`Node` almacena explícitamente:

- `ProcessMode`;
- `ProcessThreadGroup`;
- prioridad de proceso normal;
- prioridad de proceso físico;
- flags bitpacked para `process`, `physics_process`, internos e input;
- puntero al process group;
- owner del process group;
- orden del process thread group.

El header define comparadores independientes para prioridad normal y de física.

## Primera lectura arquitectónica

### SOURCE confirmado

- `SceneTree` implementa el contrato de `MainLoop`.
- proceso normal y proceso de física mantienen conjuntos de nodos separados dentro de cada `ProcessGroup`.
- Godot dispone de process groups y process thread groups.
- el diseño usa cache local y `PagedAllocator` para la organización de grupos.
- el estado de procesamiento de Node está representado de forma compacta mediante flags y prioridades.

### INFERENCE — requiere benchmark

Todavía NO afirmamos que:

- un Node inactivo tenga coste por-frame cero;
- `_process()` y `_physics_process()` tengan el mismo coste;
- process groups mejoren rendimiento en todos los casos;
- usar sub-threads sea automáticamente más rápido;
- cambiar prioridad tenga coste despreciable.

Esas afirmaciones pasan a la primera campaña experimental.

## Hipótesis derivadas

- `ARC-GODOT-HYP-SCENE-0001`: nodos sin procesamiento activo deberían mostrar una pendiente de coste por-frame considerablemente menor que nodos con `_process()` activo.
- `ARC-GODOT-HYP-SCENE-0002`: el coste incremental del procesamiento debería depender más del número de nodos registrados en los vectores de proceso que del número total de nodos del árbol.
- `ARC-GODOT-HYP-SCENE-0003`: alterar constantemente pertenencia/orden de process groups puede introducir un coste adicional asociado a invalidación y reordenación.
- `ARC-GODOT-HYP-SCENE-0004`: prioridades heterogéneas pueden incrementar trabajo de ordenación cuando los grupos quedan dirty.

Ninguna de estas cuatro hipótesis es todavía una regla de ARCONT.

## Siguiente traza

La próxima disección debe bajar a `scene/main/node.cpp` y seguir exactamente cómo `set_process`, `set_physics_process`, cambios de prioridad y entrada/salida del SceneTree modifican los process groups.