# Mapa de análisis de Godot

Objetivo: comprender el motor de abajo hacia arriba y convertir esa comprensión en conocimiento reutilizable para futuros videojuegos.

## Capas a estudiar

1. **Core** — Object, Variant, memoria, threading, señales, tipos y ciclo de vida.
2. **Scene system** — Node, SceneTree, recursos, PackedScene, ownership y procesamiento.
3. **Rendering** — RenderingServer, backends, shaders, materiales, luces, sombras, partículas, instancing, LOD y culling.
4. **Physics** — PhysicsServer2D/3D, cuerpos, shapes, broad/narrow phase, queries y sincronización.
5. **Navigation** — NavigationServer, mapas, regiones, agentes, avoidance, links y actualización dinámica.
6. **Audio** — AudioServer, buses, streams, efectos, espacialización y mezcla.
7. **Scripting** — GDScript, C#, GDExtension, bindings, llamadas entre script y engine.
8. **Assets/resources** — Resource, loaders/savers, import pipeline, caché y formatos.
9. **Animation** — AnimationPlayer, AnimationTree, Skeleton, skinning, IK y runtime animation.
10. **Editor** — plugins, inspectors, gizmos, importación, tooling y separación editor/runtime.
11. **Platforms** — Android primero; después desktop/web cuando sea relevante.
12. **Build system** — SCons, módulos, features, templates y builds personalizados.
13. **Profiling** — CPU, GPU, memoria, frame pacing, draw calls y física.
14. **Extensibilidad** — módulos del motor frente a GDExtension y plugins.

## Método

Para cada subsistema registrar:

- propósito;
- arquitectura;
- flujo de datos;
- clases/archivos clave;
- coste aproximado;
- límites conocidos;
- comportamiento en móvil;
- APIs públicas frente a implementación interna;
- oportunidades de optimización;
- errores comunes;
- experimentos mínimos reproducibles;
- conclusiones transferibles a futuros juegos.

## Regla de limpieza

Los experimentos de motor deben ser mínimos y aislados. ARCONT no alberga campañas, niveles, personajes, narrativa ni un juego completo. Si un experimento empieza a convertirse en producto, debe migrar a un repositorio independiente.
