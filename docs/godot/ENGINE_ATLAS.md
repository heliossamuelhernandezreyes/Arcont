# Godot Engine Atlas — ARCONT

Referencia base: Godot 4.7.2-stable, commit `ed1daf0bf001b61586d9930840f2f1394092c079`.

Este atlas define qué partes del motor debemos comprender y relacionar. No pretende sustituir la documentación oficial; organiza nuestro análisis técnico.

## 1. Core

- Object
- RefCounted
- Variant
- String/StringName
- ClassDB
- ObjectDB
- memory allocation
- containers
- threading
- synchronization
- job/task execution
- signals/callables

Preguntas: coste de abstracciones, ownership, referencias, allocations, llamadas dinámicas y concurrencia.

## 2. Scene system

- Node
- SceneTree
- PackedScene
- lifecycle
- notifications
- process/physics process
- groups
- ownership
- instancing

Preguntas: coste por nodo, profundidad del árbol, callbacks por frame, señales, creación/destrucción masiva.

## 3. Resources and assets

- Resource
- ResourceLoader
- ResourceSaver
- import pipeline
- caching
- dependency graph
- textures
- meshes
- shaders
- materials

Preguntas: carga, caché, duplicación, memoria, streaming y tiempos de importación.

## 4. Rendering

- RenderingServer
- RenderingDevice
- renderer architecture
- Vulkan
- OpenGL compatibility
- command submission
- meshes
- MultiMesh
- materials
- shaders
- lights
- shadows
- visibility
- occlusion
- post-processing
- particles

Preguntas: draw calls, state changes, shader cost, overdraw, bandwidth, fill rate, CPU submission, GPU bottlenecks.

## 5. Physics

- PhysicsServer2D/3D
- bodies
- areas
- broad phase
- narrow phase
- collision shapes
- CharacterBody
- RigidBody
- joints
- queries
- interpolation

Preguntas: coste por cuerpo, contacto, forma, solver, query y actualización dinámica.

## 6. Navigation

- NavigationServer
- maps
- regions
- meshes
- agents
- avoidance
- links
- dynamic obstacles
- path queries

Preguntas: coste de baking, consultas, avoidance, cambios dinámicos y número de agentes.

## 7. Animation

- AnimationPlayer
- AnimationTree
- skeletons
- skinning
- blend trees
- IK
- root motion
- retargeting
- animation libraries

Preguntas: coste CPU/GPU, cantidad de huesos, personajes simultáneos, blending, compresión y actualización a distancia.

## 8. Audio

- AudioServer
- buses
- streams
- spatial audio
- effects
- decoding
- mixing

Preguntas: voces simultáneas, latencia, decodificación, streaming, espacialización y coste de efectos.

## 9. Scripting

- GDScript
- C#
- GDExtension
- native C++ internals
- calls across boundaries
- reflection

Preguntas: coste de llamadas, allocations, hot paths y cuándo mover lógica a código nativo.

## 10. Networking

- MultiplayerAPI
- ENet/WebSocket/WebRTC cuando corresponda
- RPC
- serialization
- authority

Preguntas: overhead, latencia, ancho de banda, determinismo, prediction y rollback como arquitectura externa.

## 11. Input and platform

- Input
- touch
- sensors
- controllers
- Android lifecycle
- permissions
- window/display

Preguntas: latencia, multitouch, cambios de foco, suspend/resume y peculiaridades móviles.

## 12. Editor and tooling

- editor plugins
- importers
- inspectors
- gizmos
- build/export
- command line

Preguntas: automatización, herramientas internas, validación de contenido y pipelines.

## 13. Profiling

- built-in profiler
- monitors
- debugger
- rendering diagnostics
- external Android/GPU tooling cuando aplique

Objetivo: relacionar síntomas visibles con subsistemas concretos.

## 14. Android/mobile

- renderer selection
- texture compression
- memory limits
- thermal behavior
- battery
- APK/AAB/export
- architecture ABI
- lifecycle

Objetivo: convertir móvil en plataforma de primera clase, no en una reducción tardía de desktop.

## Regla del atlas

Cada área debe acabar conectada con:

`SOURCE -> INTERNAL MODEL -> EXPERIMENT -> METRICS -> FAILURE MODES -> PATTERN -> DECISION RULE`

El atlas está incompleto por diseño: crece solo cuando hay evidencia útil.