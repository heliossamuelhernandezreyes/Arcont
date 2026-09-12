# Godot Research Roadmap — ARCONT

Base canónica: Godot 4.7.2-stable @ `ed1daf0bf001b61586d9930840f2f1394092c079`.

## Fase 0 — Instrumentación

Antes de optimizar, asegurar que sabemos medir:

- frame time CPU/GPU;
- memoria;
- draw calls;
- tiempos de carga;
- cantidad de objetos;
- temperatura/throttling;
- captura reproducible de resultados.

Salida: protocolo y baseline vacío.

## Fase 1 — Coste base del motor

Preguntas:

- ¿cuánto cuesta un Node sin lógica?
- ¿cuánto cuesta `_process()` masivo?
- ¿cuánto cuesta `_physics_process()`?
- ¿qué coste tienen señales frecuentes?
- ¿qué coste tiene instanciar/liberar miles de nodos?

Salida: presupuesto por arquitectura de escena.

## Fase 2 — Render

Experimentos prioritarios:

- MeshInstance3D vs MultiMesh;
- material compartido vs materiales únicos;
- cantidad de luces y sombras;
- transparencia/overdraw;
- LOD y visibility range;
- partículas;
- resolución y escalado;
- Vulkan vs Compatibility cuando sea viable.

Salida: reglas de render móvil y desktop.

## Fase 3 — Física

- StaticBody/CharacterBody/RigidBody por cantidad;
- formas simples vs complejas;
- queries por frame;
- contactos y colisiones;
- debris temporal;
- frecuencia de física.

Salida: presupuestos prácticos de física.

## Fase 4 — Animación

- cantidad de skeletons;
- huesos por personaje;
- AnimationTree/blending;
- IK;
- actualización completa vs LOD de animación;
- personajes fuera de cámara.

Salida: presupuesto de personajes animados.

## Fase 5 — Navegación e IA

- path queries;
- agentes simultáneos;
- avoidance;
- cambios dinámicos;
- grafos manuales vs NavigationServer según escala.

Salida: matriz de decisión de navegación.

## Fase 6 — Audio

- voces simultáneas;
- audio espacial;
- streams largos;
- decodificación;
- efectos de bus;
- latencia.

Salida: presupuesto de audio.

## Fase 7 — Assets y streaming

- importación;
- texturas;
- compresión;
- carga asíncrona;
- recursos compartidos;
- tiempos de entrada a escena;
- picos de memoria.

Salida: pipeline recomendado.

## Fase 8 — Android

- perfiles por dispositivo;
- consumo térmico sostenido;
- memoria real;
- resolución dinámica;
- estabilidad de FPS;
- lifecycle;
- input táctil;
- exportación.

Salida: guía móvil basada en mediciones.

## Fase 9 — Extensibilidad

- GDScript vs C# vs GDExtension en hot paths;
- coste de cruces de frontera;
- herramientas de editor;
- módulos externos.

Salida: criterio para decidir cuándo salir de GDScript.

## Fase 10 — Sistemas combinados

Solo después de medir subsistemas aislados se permiten pruebas combinadas para estudiar interacción entre render, física, navegación, animación y audio.

Estas pruebas siguen sin ser juegos: son workloads técnicos controlados.

## Prioridad

1. instrumentación;
2. scene/core;
3. render;
4. Android;
5. física;
6. animación;
7. navegación;
8. assets;
9. audio;
10. scripting/extensión.

La prioridad puede cambiar si un proyecto futuro plantea una pregunta concreta.