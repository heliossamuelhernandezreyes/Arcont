# Arcont: investigación de herramientas Godot y propuesta de integración

Consulta: **2 de octubre de 2026 UTC**; la solicitud comenzó el **1 de octubre en Monterrey**. Autor del proyecto: **Helios Samuel Hernández Reyes**.

## Resultado y alcance

Se revisaron **83 proyectos o herramientas externas**, **17 capacidades nativas** y **3 fuentes de assets**, en **14 áreas**. Esta es una búsqueda amplia y una selección razonada; no se afirma que incluya todos los repositorios existentes.

El objetivo es que un asistente pueda operar una plataforma de creación para Godot mediante Arcont: construir, inspeccionar, ejecutar, observar, medir y corregir. El diseño artístico sigue siendo una decisión explícita del autor. Los algoritmos procedurales pueden ejecutar operaciones repetitivas con parámetros y semillas, sin decidir el mapa completo.

**Este cambio contiene investigación y propuesta. No instala ni integra estos candidatos y no añade pruebas de runtime.** La disponibilidad de un proyecto, su README y su licencia no prueban compatibilidad, estabilidad, rendimiento o que un asistente pueda usarlo sin desarrollar un adaptador.

Inventario estructurado: [GODOT_TOOLCHAIN_CANDIDATES_2026-10-02.json](GODOT_TOOLCHAIN_CANDIDATES_2026-10-02.json).

## Qué existe ya en Arcont

La rama canónica inspeccionada es `550ca709b79fe72417aa5ef6fc1e6eaf2d873ec1`. El [control de Map Forge está publicado en PR #14](https://github.com/heliossamuelhernandezreyes/Arcont/pull/14), cabeza `c59ad6b748814ce01c56aac360060c58b8534ba8`, y seguía sin fusionarse al revisar. Su [adaptador del juego está en Close Seal PR #7](https://github.com/heliossamuelhernandezreyes/Closeseal/pull/7); [el mapa urbano está en PR #8](https://github.com/heliossamuelhernandezreyes/Closeseal/pull/8).

Ese trabajo ofrece inspección, edición de datos completos, pinceles, validación, revisiones, historial, materialización y capturas. El puente de Cyclops todavía crea workspace y guías; el de Scatter crea zonas sin demostrar una pila completa de items/modificadores; FuncGodot tiene un socket que no demuestra importación real. Terrain3D recibió operaciones adicionales en el trabajo previo. Estos alcances se deben distinguir de la observación inicial de proveedores.

Perfetto, Tracy, Recast y Godot benchmarks ya tienen referencias en el banco técnico. Incluirlos aquí significa proponer cómo aprovecharlos en el nuevo flujo; no descubrirlos como si no existieran ni afirmar que estén ejecutándose.

Arcont conserva contratos, herramientas reutilizables y conocimiento. El manifiesto prohíbe juegos de producción y proyectos Godot embebidos. Los adaptadores ejecutables pertenecen al proyecto que los usa; los experimentos generales, a Runtime Lab/Nia-Tech. La exportación del juego debe funcionar sin el servidor del asistente.

## Criterio de búsqueda

Se consultaron repositorios upstream, README, documentación del motor 4.7, textos de licencia y metadatos directos de GitHub. Se comprobaron metadatos de los 82 repositorios GitHub incluidos; SoX se consultó en su distribución upstream. El JSON retiene fechas de actividad, archivado, versión declarada y hashes de README/licencia cuando se leyeron por API.

La evidencia es **documental**, con controles de consistencia y procedencia. Las capacidades externas se tratan como declaraciones upstream. Las estrategias de adaptación son propuestas de esta investigación. No se compararon todos los códigos internamente ni se ejecutaron addons nuevos.

Los nombres parecidos y forks se conservan como alternativas, sin convertirlos automáticamente en módulos independientes. Cantidad de herramientas, estrellas y demostraciones vistosas no se utilizan como prueba de calidad. Una fecha de push tampoco demuestra estabilidad.

## Cómo formar un sistema común

Arcont debería publicar un servicio semántico de autoría, accesible por CLI y MCP. Ambos transportes llamarían las mismas operaciones y respetarían los mismos cambios de revisión. El registro describiría operaciones reales y parámetros, con descubrimiento por capacidad, para que el asistente no cargue definiciones irrelevantes ni invente soporte.

Cada objeto tendría una identidad estable y un propietario de sus datos. Las escenas y recursos Godot seguirían siendo editables. Las extensiones de un proveedor conservarían su información avanzada; no se reduciría todo a un JSON limitado que perdiera sólidos, grafos, pistas o modificadores. El contrato de Map Forge conservaría sus datos semánticos y referencias con reglas claras de sincronización.

Las operaciones deberían cubrir:

- **Leer:** escenas, recursos, materiales, assets, geometría, estado de proveedores y diagnósticos.
- **Editar:** escena/nodos, sólidos/caras, curvas, terreno, distribución, materiales, luces, audio y pistas de animación.
- **Construir:** importación, meshes, colisiones, navegación, iluminación y acústica derivadas.
- **Probar:** ejecución, entrada del jugador, observaciones del estado, capturas visuales y audio.
- **Medir:** tiempos de frame, memoria, llamadas de dibujo, cuerpos/consultas, voces/DSP y latencia.
- **Recuperar:** vista previa, historial, deshacer, validación y recuperación de archivos derivados.

El writer actual de Map Forge no es una transacción atómica de todo el filesystem y no revierte archivos externos del proveedor. Extenderlo requiere registrar/stagear también escenas, recursos, importaciones y bakes. No basta con poner un servidor MCP delante.

Una herramienta se considera integrada cuando una operación controlada produce recursos guardados, vuelve a abrirse, se puede editar otra vez, aparece correctamente en runtime y se puede verificar. Detectar el addon o crear un nodo de su clase es una prueba más limitada.

## Selección del primer sistema

| Responsabilidad | Selección propuesta | Decisión pendiente |
|---|---|---|
| Editor y juego observable | Evaluar satelliteoflove como primer puente; comparar Toolkit por extensibilidad y Rust por undo/eventos | Un único escritor; conexión al proceso real, estados y archivos coherentes |
| Suelo y edificios | Completar Terrain3D y Cyclops; conservar primitivas/meshes nativos | Sólidos e interiores realmente editables y guardados |
| Calles y distribución | Road Generator y operación completa de ProtonScatter | Cruces, pendientes, exclusiones y regeneración estable |
| Apariencia | Material Maker, Sky3D, materiales/probes/LightmapGI nativos | Exportación automatizable; un solo propietario del ambiente |
| Sonido | Buses y música interactiva nativos; comparar SpatialAudioPlayer3D con Nexus Resonance | Calidad, geometría acústica y presupuesto CPU/Android |
| Escala | MultiMesh por sector, LOD/HLOD, carga por regiones, colisión simplificada | Medir antes y después en escenarios y dispositivos definidos |
| Calidad del cambio | CLI/importaciones, GUT o GdUnit4 y diagnóstico LSP | Framework fijado para Godot exacto y tests útiles |

LimboAI/Beehave, diálogos, red y voz son módulos posteriores según el juego. Su inclusión no obliga a cambiar el contrato de Close Seal ni convertir su demo de exploración en un género nuevo.

Las cuevas y volúmenes editables pueden requerir Voxel Tools como backend especializado. MTerrain/TerraBrush se mantienen como alternativas a evaluar, no como otros dos motores de terreno que deban ejecutarse a la vez.

## Qué significa integración con IA

Conviene separar cuatro funciones:

1. **El asistente opera Godot:** puente de editor, recursos y runtime. Esta es la prioridad solicitada.
2. **Un chat vive dentro del editor:** panel que llama a un proveedor de modelos; puede o no exponer herramientas.
3. **Personajes usan comportamientos de juego:** árboles/estados como LimboAI o Beehave, sin requerir un LLM.
4. **Un modelo se ejecuta durante el juego:** diálogo o voz local; opcional, con memoria, latencia y licencia propias.

El primer caso puede funcionar usando el asistente que ya opera Arcont y sin añadir un servicio generativo al juego. Requiere un host con Godot y un transporte accesible al asistente. La documentación de un MCP no crea esa conexión por sí sola.

## Hallazgos que cambian decisiones

- **GodotAI de Sods2:** la licencia actual restringe redistribución y derivados comerciales. No se acepta como base OSS aunque una ficha o descripción sugiera otra cosa. [LICENSE](https://github.com/Sods2/GodotAI/blob/main/LICENSE).
- **Beckett:** la edición Lite es MIT; parte de las pruebas autónomas pertenece a Full de pago. No sumar esas capacidades al conjunto abierto.
- **FMOD/Wwise:** sus integraciones públicas no hacen abiertos los middleware. Se conservan como referencia fuera del núcleo completamente OSS.
- **Foliage3D:** solo el addon específico tiene MIT; los assets de demo no están licenciados para redistribuir. [Alcance upstream](https://github.com/caphindsight/Foliage3D#license).
- **GDQuest VFX:** código MIT y arte CC-BY-NC-SA. El arte de demo no se incorpora automáticamente al juego comercial. [Licencias](https://github.com/gdquest-demos/godot-4-VFX-assets).
- **Sky3D:** código MIT y mapas de estrellas con avisos propios. **Toolkit:** código MIT e identidad gráfica excluida de esa licencia.
- **Audacity:** LICENSE actual declara GPLv3 para el conjunto; el manual antiguo que indica GPLv2 no decide la licencia del checkout.
- **Meridian:** el encabezado de `__init__.py` declara GPLv3 o posterior aunque GitHub no clasifique una licencia raíz. [Cabecera](https://github.com/Naxela/Meridian/blob/main/__init__.py).
- **Jolt:** existe en Godot desde 4.4. Primero usar el módulo nativo; la extensión en mantenimiento solo responde a necesidades específicas.
- **Rendimiento:** compatibilidad de renderer, Android o biblioteca no demuestra que una escena cumpla el presupuesto del dispositivo.

## Primera prueba de aceptación

Usar un sector del mapa urbano ya creado como escenario verificable. El asistente debería poder:

1. Convertir una avenida en curva con pendiente y un cruce, manteniendo continuidad.
2. Ajustar el suelo y construir una fábrica con puerta, habitación, techo y escalera recorribles.
3. Distribuir vegetación y props conservando entradas y calle despejadas.
4. Configurar materiales/iluminación y escuchar una fuente exterior desde fuera y dentro del edificio.
5. Guardar, reabrir, modificar una pared y reconstruir los derivados afectados.
6. Recorrer el sector con el personaje y registrar contactos, rutas, frames, memoria, capturas y audio.
7. Deshacer una operación sin dejar cambios de escena o bakes ajenos al historial.

Las cifras de FPS, memoria y tiempos se fijan con el proyecto y la plataforma; ninguna queda demostrada por esta investigación. En Android se necesita medición de export y dispositivo reales. Registrar hardware, renderer, motor, revisión de assets, semilla y hashes. El progreso debe mejorar un entorno jugable y editable, no solo aumentar el número de plugins.

## Inventario por área

**P0:** primer experimento. **P1:** siguiente capa importante. **P2:** alternativa o necesidad concreta. **P3:** especializado/posterior. **HOLD:** excluido o referencia con límites. Las licencias aquí son resúmenes de alcance, no una autorización global de todas las dependencias. Para versión declarada, actividad upstream y snapshots, consultar el JSON.

### Control del editor por asistentes

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Godot MCP — satelliteoflove](https://github.com/satelliteoflove/godot-mcp) | MIT | P0 | Adaptar lectura del editor, capturas, estado del juego, entrada y pasos de tiempo a Arcont. Un cliente por editor; necesita proceso Godot y conexión real; aún no integrado. |
| [Godot MCP Toolkit](https://github.com/NPGameDev/godot-mcp-toolkit) | MIT código; identidad gráfica excluida | P0 | Usar su API de extensiones GDScript para publicar operaciones de los módulos de Arcont. Comparar con el puente anterior mediante la misma prueba; no activar servidores competidores como escritores. |
| [Open Godot MCP — Rust](https://github.com/OneStepAt4time/open-godot-mcp) | MIT | P1 | Adaptar operaciones con UndoRedo y eventos del editor. Las afirmaciones de exclusividad del README no se aceptan como comparación verificada. |
| [Godot MCP — bradypp](https://github.com/bradypp/godot-mcp) | MIT | P2 | Automatizar escenas, nodos, ejecución y lectura de errores. Probar cobertura real de estado vivo y deshacer; no elegir por cantidad de herramientas. |
| [minimal-godot-mcp](https://github.com/ryanmazzolini/minimal-godot-mcp) | MIT | P1 | Consultar diagnósticos GDScript por LSP y salida de depuración. Complemento de análisis; no sustituye el control de geometría o del editor. |
| [Godot MCP — triforge0](https://github.com/triforge0/godot-mcp) | MIT | P2 | Comparar automatización de escenas, depuración y pruebas. Candidato redundante; la compatibilidad exacta y cobertura no se probaron. |
| [Open Godot MCP — masteryee](https://github.com/masteryee-labs/Open-Godot-MCP) | MIT | P2 | Evaluar LSP, DAP, pruebas y escenarios multijugador. Comparación documental; no demostrar determinismo entre máquinas por el README. |
| [Beckett Godot MCP Lite](https://github.com/beckettlab/beckett-godot-mcp) | MIT edición Lite | P2 | Evaluar inspección, edición, capturas y estado remoto por HTTP. El control de entrada y parte de las pruebas pertenece a Full de pago; no contar Full como OSS. |
| [AI Assistant Hub](https://github.com/FlamxGames/godot-ai-assistant-hub) | MIT | P2 | Adaptar herramientas del editor y contexto si se requiere asistente dentro de Godot. Es interfaz al proveedor; su ejecución y capacidad de edición deben probarse. |
| [Godot AI Assistant — módulo C++](https://github.com/spardanviro/Godot_AI) | Apache-2.0 | P3 | Estudiar contexto de escena y acciones EditorScript. Requiere compilar el editor; preferir puente compatible con binario oficial para la primera integración. |
| [GodotAI — Sods2](https://github.com/Sods2/GodotAI) | Licencia propia restrictiva; no clasificar como OSS | HOLD | Referencia funcional de panel de chat y proveedores. LICENSE impide redistribuir el plugin y derivados comerciales sin permiso; descartar del núcleo OSS. |

### Terreno, arquitectura y trazado

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Terrain3D](https://github.com/TokisanGames/Terrain3D) | MIT | P0 | Ampliar pinceles, regiones, materiales, importación y sincronización. Ya hay integración parcial probada en trabajo previo; probar cada operación y renderer por separado. |
| [Cyclops Level Builder](https://github.com/blackears/cyclopsLevelBuilder) | MIT | P0 | Exponer sólidos, caras y materiales; conservar edición y producir colisión/navegación. El puente actual crea workspace y guías, no demuestra autoría completa de sólidos. |
| [ProtonScatter](https://github.com/HungryProton/scatter) | MIT código; assets demo separados | P0 | Configurar elementos, modificadores, semilla, exclusiones y colocación sobre superficies. Hoy hay zonas preparadas; faltan pilas de modificadores y salida validada; no redistribuir texturas demo por asumir MIT. |
| [FuncGodot](https://github.com/func-godot/func_godot_plugin) | MIT | P1 | Importar MAP/VMF con entidades, materiales y colisiones. El socket actual no prueba importación completa; medir guardado y reimportación. |
| [Road Generator](https://github.com/TheDuckCow/godot-road-generator) | MIT | P0 | Editar puntos, carriles, pendientes y cruces; coordinar ajuste del terreno. Proyecto incompleto; comprobar rutas en cruces y continuidad, sin suponer sistema de tráfico terminado. |
| [Voxel Tools](https://github.com/Zylann/godot_voxel) | MIT | P3 | Controlar volumen, excavación, cuevas, chunks y almacenamiento. README conserva GDExtension en roadmap; puede requerir motor especial; backend opcional. |
| [TerraBrush](https://github.com/spimort/TerraBrush) | MIT | P2 | Evaluar terreno, pintura y distribución como alternativa. Duplica Terrain3D; no mantener dos terrenos activos sin una necesidad medida. |
| [MTerrain](https://github.com/mohsenph69/Godot-MTerrain-plugin) | MIT | P2 | Evaluar terreno, octree/LOD/HLOD y navegación. Medir valor frente a Terrain3D y HLOD nativo; no adoptar promesas de rendimiento sin benchmark. |
| [Godot Map Builder](https://github.com/callmemhz/godot-map-builder) | MIT | P2 | Adaptar pinceles convexos, edición de caras, texturas y bake. Comparar con Cyclops mediante la misma habitación editable; evitar duplicar editores de sólidos. |
| [Gaea — addon Godot](https://github.com/gaea-godot/gaea) | MIT | P3 | Exponer algoritmos y parámetros de generación como operaciones editables. Proyecto distinto del software comercial Gaea; generación opcional, sin decidir por sí sola el diseño. |
| [GDQuest procedural generation](https://github.com/gdquest-demos/godot-4-procedural-generation) | MIT código; assets CC-BY-4.0 | P3 | Extraer algoritmos pequeños con entradas y semillas explícitas. Demos de referencia, no editor universal ni garantía de mapas 3D completos. |
| [Godot procgen — Hachemi](https://github.com/alexishachemi/godot-procgen) | MIT | P3 | Evaluar generación por habitaciones y parámetros de conexiones. Especializado en cuevas/mazmorras; probar adaptación geométrica al entorno 3D. |

### Modelado e importación 3D

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Blender](https://github.com/blender/blender) | GPL-3.0; archivos individuales pueden diferir | P1 | Operar bpy/Python, Geometry Nodes, modelado, UV, rig y exportación glTF/GLB. CPU/GPU y versión de Blender necesarias; scripts y assets deben conservarse reproducibles. |
| [MCP for Blender](https://github.com/ahujasid/mcp-for-blender) | MIT puente; servicios/assets externos aparte | P2 | Adaptar observación y ejecución de operaciones Blender al flujo de assets de Arcont. Servicios de generación son opcionales y tienen términos/costos propios; no necesarios para modelar. |
| [Meridian](https://github.com/Naxela/Meridian) | GPL-3.0-or-later en cabecera __init__.py | P2 | Evaluar exportación de escena, materiales, luces y bakes desde Blender. Compilador de proyecto/escenas; impedir sobrescrituras del juego y probar reimportación antes de usar. |
| [Blender-Godot Pipeline helper](https://github.com/bikemurt/blender-godot-pipeline) | MIT helper Godot; componente Blender aparte | P3 | Reusar ideas de metadatos de importación. Solo helper es lo revisado; autor recomienda GLTFDocumentExtension; no asumir paquete completo libre. |
| [TrenchBroom](https://github.com/TrenchBroom/TrenchBroom) | GPL-3.0 | P2 | Intercambiar geometría arquitectónica mediante FuncGodot. No necesita ser editor principal del asistente; probar importación round-trip y entidades. |
| [Godot Blender exporter antiguo](https://github.com/godotengine/godot-blender-exporter) | GPL-2.0 | HOLD | Referencia de exportación de escenas. README recomienda glTF 2.0 para pipeline completo; no escoger como base nueva. |
| [3D asset import](https://docs.godotengine.org/en/4.7/tutorials/assets_pipeline/importing_3d_scenes/index.html) (nativo) | MIT motor Godot; documentación separada | P0 | Importar glTF/GLB/blend y metadatos; configurar materiales/animación/colisión. La importación .blend necesita Blender instalado; preferir contratos de importación explícitos. |

### Materiales, atmósfera, agua y efectos

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Material Maker](https://github.com/RodZill4/material-maker) | MIT | P1 | Crear grafos/materiales y exportar mapas PBR. Probar API/automatización de exportación; no se verificó un CLI headless de todos sus workflows. |
| [Sky3D](https://github.com/TokisanGames/Sky3D) | MIT código; mapas de estrellas con atribución | P1 | Controlar hora, sol/luna, cielo, niebla y exposición. Debe coordinarse con un único WorldEnvironment; algunos parámetros son conducidos por su controlador. |
| [Waterways](https://github.com/Arnklit/Waterways) | MIT | P3 | Editar curvas de río, mallas y mapas de flujo/espuma. Revisar rama y shaders: el README también conserva instrucciones antiguas; no asumir compatibilidad 4.7. |
| [GodotOceanWaves](https://github.com/2Retr0/GodotOceanWaves) | MIT | P3 | Controlar espectro, cascadas y apariencia del agua. Ejemplo técnico; requiere backend adecuado y medición GPU, no opción base para Compatibility. |
| [Godot4 OceanFFT](https://github.com/tessarakkt/godot4-oceanfft) | MIT declarada | P3 | Evaluar olas FFT, flotación y LOD. README lo presenta como trabajo temprano; costo y renderer pendientes. |
| [Godot Asset Placer](https://github.com/levinzonr/godot-asset-placer) | MIT | P2 | Gestionar paletas y colocación de assets con metadatos compartidos. Exponer datos/operaciones a Arcont; tener UI no prueba que el asistente pueda usar su lógica. |
| [Foliage3D](https://github.com/caphindsight/Foliage3D) | MIT solo addons/foliage_3d | P3 | Evaluar vegetación interactiva, generación cercana y LOD. Demo, modelos, texturas y materiales no licenciados; excluirlos de importación automática. |
| [Trail3D](https://github.com/SomeRanDev/Godot-Trail3D) | MIT | P2 | Añadir/configurar estelas por parámetros. Comparar con trails nativos; el autor remite a alternativa GPU para Forward/Mobile. |
| [GDQuest VFX assets](https://github.com/gdquest-demos/godot-4-VFX-assets) | MIT código; arte CC-BY-NC-SA-4.0 | P3 | Estudiar partículas/shaders y reconstruir recursos con assets aptos. Arte no comercial: no copiar la demo completa a un juego comercial. |
| [Global illumination](https://docs.godotengine.org/en/4.7/tutorials/3d/global_illumination/introduction_to_global_illumination.html) (nativo) | MIT motor Godot; documentación separada | P0 | Configurar/bakear LightmapGI y probes; perfiles de GI por plataforma. SDFGI/VoxelGI exigen Forward+; LightmapGI admite renderers distintos, con requisitos de hardware para bake. |
| [3D particle trails](https://docs.godotengine.org/en/4.7/tutorials/3d/particles/trails.html) (nativo) | MIT motor Godot; documentación separada | P1 | Configurar partículas y estelas con recursos editables. Solo Forward+ y Mobile; Compatibility no soportado. Controlar overdraw y comparar alternativa CPU. |

### Física, colisiones y navegación

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Godot Jolt extension](https://github.com/godot-jolt/godot-jolt) | MIT | P1 | Usar módulo nativo; extensión solo si una función concreta lo exige. Extensión en mantenimiento; sus limitaciones no deben trasladarse sin comprobar al Jolt integrado. |
| [Jolt Physics](https://github.com/jrouwe/JoltPhysics) | MIT | P2 | Estudiar colisiones, cuerpos y parámetros a través de Godot. No integrar otra instancia del motor físico por defecto. |
| [Recast and Detour](https://github.com/recastnavigation/recastnavigation) | Zlib | P1 | Controlar geometría de bake y regiones mediante navegación nativa. No asumir que todas las APIs de Detour se exponen en Godot. |
| [GodotStairs](https://github.com/mrezai/GodotStairs) | MIT | P2 | Evaluar subida/bajada de escalones y respuesta del personaje. POC de controlador; probar alturas, pendientes, techo y Jolt exacto. |
| [Godot Destruction](https://github.com/the-dunk/Godot-Destruction) | MIT | P3 | Evaluar fractura de mallas convexas y fragmentos físicos. Repositorio distingue trabajo operativo, en desarrollo y planeado; no anunciar todo como terminado. |
| [Jolt nativo](https://docs.godotengine.org/en/4.7/tutorials/physics/using_jolt_physics.html) (nativo) | MIT motor Godot; documentación separada | P0 | Seleccionar/configurar backend y probar cuerpos, contactos y restricciones. No requiere addon Jolt externo desde Godot 4.4; estabilidad y costo son pruebas del proyecto. |
| [Collision shapes 3D](https://docs.godotengine.org/en/4.7/tutorials/physics/collision_shapes_3d.html) (nativo) | MIT motor Godot; documentación separada | P0 | Crear primitivas, convexos/descomposición y mallas estáticas; inspeccionar capas y máscaras. Colisión concava es para estáticos; simplificación y márgenes cambian coste y respuesta. |
| [Navigation 3D](https://docs.godotengine.org/en/4.7/tutorials/navigation/navigation_optimizing_performance.html) (nativo) | MIT motor Godot; documentación separada | P0 | Bakes por geometría real, regiones, agentes, consultas y depuración de rutas. Evitar rebakes completos por cada cambio; probar sincronización, links y obstáculos. |

### Sonido espacial y música durante el juego

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Nexus Resonance](https://github.com/undomick/godot-nexus-resonance) | MIT puente; Steam Audio y dependencias aparte | P1 | Configurar materiales acústicos, sondas, fuentes y bakes mediante API. Probar binarios 4.7.2/Android; geometría estática destruida requiere reconstrucción acústica. |
| [Godot Steam Audio — stechyo](https://github.com/stechyo/godot-steam-audio) | MIT puente; Steam Audio Apache-2.0 | P2 | Alternativa para oclusión, transmisión y reverberación. README advierte bibliotecas propietarias opcionales: revisar build/dependencias para ruta totalmente OSS. |
| [Steam Audio](https://github.com/ValveSoftware/steam-audio) | Apache-2.0; terceros aparte | P2 | Backend acústico para un adaptador seleccionado. Soporte Android del SDK no prueba soporte del addon ni rendimiento del juego. |
| [SpatialAudioPlayer3D](https://github.com/Danikakes/spatial_audio_player_3d) | MIT | P1 | Configurar oclusión, materiales, zonas y reverberación estimada por raycasts. Alternativa a extensión nativa; medir CPU/raycasts y calidad; no prometer equivalencia con simulador acústico. |
| [AdaptiSound](https://github.com/MrWalkmanDev/AdaptiSound) | MIT | P2 | Autoría de música adaptativa y cambios de estado. Comparar primero con AudioStreamInteractive/Synchronized nativos; no duplicar mezcladores. |
| [Godot MIDI](https://github.com/nlaha/godot-midi) | MIT | P2 | Importar MIDI y exponer eventos/sincronización. Eventos MIDI no implican sintetizador ni banco instrumental completo; proyecto WIP. |
| [Godot AMP](https://github.com/DatLycan/Godot-AMP) | MIT | HOLD | Referencia de stems y transiciones adaptativas. Repositorio archivado; preferir nativo o proyecto mantenido después de pruebas. |
| [FMOD for Godot](https://github.com/MadFlyFish/fmod-for-godot) | MIT integración; FMOD propietario | HOLD | Referencia de eventos/mezcla para futuras interoperabilidades. No satisface una cadena completamente OSS; SDK tiene licencia separada. |
| [Wwise Godot integration](https://github.com/alessandrofama/wwise-godot-integration) | Licencia integración separada; Wwise propietario | HOLD | Referencia de autoría y profiler acústico. No contar disponibilidad de código del wrapper como middleware OSS. |
| [Audio buses](https://docs.godotengine.org/en/4.7/tutorials/audio/audio_buses.html) (nativo) | MIT motor Godot; documentación separada | P0 | Editar buses, efectos, niveles y ruteo; capturar audio del juego. Controlar clipping, número de voces y coste DSP; el oído y una captura deben revisar el resultado. |
| [Interactive music streams](https://docs.godotengine.org/en/4.7/classes/class_audiostreaminteractive.html) (nativo) | MIT motor Godot; documentación separada | P0 | Autoría de clips y transiciones; combinar con AudioStreamSynchronized para capas. Primera opción antes de sumar un plugin; composición y archivos musicales se crean aparte. |

### Creación y procesamiento de sonido

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [jsfxr](https://github.com/chr15m/jsfxr) | Unlicense | P1 | Generar efectos sintetizados con parámetros y exportar audio. Especializado en sonido retro; no sustituye grabaciones y diseño de sonido realista. |
| [Audacity](https://github.com/audacity/audacity) | GPL-3.0 conjunto actual; archivos individuales pueden diferir | P2 | Editar/procesar audio mediante mod-script-pipe y scripts. Requiere módulo habilitado; manual antiguo GPLv2 contradice LICENSE actual: usar licencia del checkout. |
| [Ardour](https://github.com/Ardour/ardour) | GPL-2.0-or-later | P3 | Autoría de sesiones, mezcla y exportación; evaluar scripting Lua. No se probó una automatización completa sin GUI; plugins/bancos tienen licencias propias. |
| [LMMS](https://github.com/LMMS/lmms) | GPL-2.0 | P2 | Editar proyectos de música y renderizar por CLI. Instrumentos/samples y reproducibilidad requieren versiones y licencias separadas. |
| [SoX](https://sourceforge.net/projects/sox/) | GPLv2 programa; LGPL biblioteca según distribución | P2 | Procesar, convertir y sintetizar señales por operaciones reproducibles. Fijar build/codecs; revisar mantenimiento y no asumir calidad artística automática. |
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | LGPL base; GPL y otras condiciones según configuración | P1 | Conversión, extracción, análisis de audio y entrega de capturas/video. Licencia efectiva depende de build y codecs; usar herramienta externa con procedencia. |

### Voz e inferencia local opcionales

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Piper](https://github.com/OHF-Voice/piper1-gpl) | GPL-3.0 motor; voces por modelo | P3 | Producir voces temporales y evaluar narración offline. Licencia/calidad de cada voz aparte; no requiere introducir un LLM en el mapa. |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | MIT código; modelos por verificar | P3 | Transcribir grabaciones, evaluar comandos de voz y subtítulos. Necesita modelo y mediciones de latencia; no es sistema de creación de mapas. |
| [Godot LLM](https://github.com/Adriankhl/godot-llm) | MIT declarado | P3 | Evaluar inferencia y embeddings para funciones opcionales del juego. Distinto de que el asistente opere el editor; pesos, memoria y plataforma aparte. |
| [Local Agents](https://github.com/adammikulis/local-agents) | MIT | P3 | Evaluar inferencia/voz/memoria local con API del addon. Stack pesado para móvil; auditar dependencias y modelos; no incluirlo por defecto. |
| [Chorus LLM — GDLlama](https://github.com/xarillian/chorus-llm) | MIT | P3 | Evaluar nodo local de inferencia y embeddings. Renombrado desde GDLlama; comparar con alternativas y medir memoria real. |

### Animación y cámaras

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Phantom Camera](https://github.com/ramokz/phantom-camera) | MIT | P1 | Controlar seguimiento, prioridades y transiciones de cámaras. Probar encuadres, colisiones de cámara y recursos editables; no basta una captura fija. |
| [GodotIK](https://github.com/monxa/GodotIK) | MIT; revisar THIRDPARTY | P2 | Configurar cadenas, objetivos y restricciones de IK. Comparar con SkeletonModifier/IK de Godot exacto antes de añadir dependencia nativa. |
| [AnimationTree and AnimationPlayer](https://docs.godotengine.org/en/4.7/tutorials/animation/animation_tree.html) (nativo) | MIT motor Godot; documentación separada | P0 | Editar tracks, blends, estados y parámetros; probar transición en runtime. Necesita animaciones y rigs aptos; animación de locomoción debe verificarse con movimiento real. |
| [Retargeting 3D skeletons](https://docs.godotengine.org/en/4.7/tutorials/assets_pipeline/retargeting_3d_skeletons.html) (nativo) | MIT motor Godot; documentación separada | P0 | Configurar mapeo de huesos e importación de animaciones entre personajes. Probar proporciones, pose base y root motion; evitar módulos antiguos duplicados. |

### Comportamiento y narrativa

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [LimboAI](https://github.com/limbonaut/limboai) | MIT | P2 | Editar árboles de comportamiento, estados y tareas de NPC. Compatibilidad exacta 4.7.2 pendiente; es IA de personajes, no puente del asistente. |
| [Beehave](https://github.com/bitbrain/beehave) | MIT | P2 | Editar árboles de comportamiento en nodos y observar estados. Alternativa a LimboAI; elegir uno por necesidades y pruebas. |
| [Dialogue Manager](https://github.com/nathanhoad/godot_dialogue_manager) | MIT | P2 | Autoría de diálogo ramificado, condiciones y recursos textuales. No equivale a un sistema completo de misiones; integrar señales/estado del juego. |
| [Dialogic](https://github.com/dialogic-godot/dialogic) | MIT | P2 | Editar timelines, personajes y diálogos. Alternativa para narrativa/presentación; no instalar dos sistemas de diálogo por defecto. |

### Multijugador y backend

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Netfox](https://github.com/foxssake/netfox) | MIT | P3 | Configurar predicción/rollback y automatizar escenarios de red. Exige diseño de simulación y tests de latencia; no garantiza física determinista. |
| [Nakama Godot SDK](https://github.com/heroiclabs/nakama-godot) | Apache-2.0 | P3 | Adaptar autenticación, sesiones, matchmaking y pruebas de varios clientes. Cliente requiere backend; desplegar servidores es trabajo separado. |
| [Nakama server](https://github.com/heroiclabs/nakama) | Apache-2.0 edición abierta | P3 | Backend opcional probado en laboratorio antes del juego. Servicios gestionados/enterprise y costos de infraestructura no se confunden con código OSS. |

### Rendimiento, streaming y observación

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Tracy](https://github.com/wolfpld/tracy) | BSD-3-Clause | P1 | Importar trazas CPU/GPU/memoria en la evidencia de Arcont. Ya hay registro de observabilidad; no implica que la sesión actual esté instrumentada. |
| [Perfetto](https://github.com/google/perfetto) | Apache-2.0 | P1 | Registrar scheduling, memoria y frames; analizar con Trace Processor. Ya figura en Arcont; medición en teléfono requiere acceso real al dispositivo. |
| [RenderDoc](https://github.com/baldurk/renderdoc) | MIT | P1 | Capturar frames y analizar draw calls, shaders, texturas y render targets. Necesita GPU/proceso compatibles y captura real; no extrapolar resultados PC a móvil. |
| [meshoptimizer](https://github.com/zeux/meshoptimizer) | MIT | P2 | Usar LOD de importación nativo; estudiar optimización adicional si hace falta. No importar otro stack de simplificación sin medir diferencia de calidad/costo. |
| [Godot benchmarks](https://github.com/godotengine/godot-benchmarks) | MIT | P1 | Ejecutar campañas aisladas en Runtime Lab y registrar resultados. Ya es proveedor conocido de Arcont; microbenchmark no prueba rendimiento del juego completo. |
| [MultiMesh](https://docs.godotengine.org/en/4.7/classes/class_multimesh.html) (nativo) | MIT motor Godot; documentación separada | P0 | Agrupar instancias por sector y material; controlar visibilidad y buffers. Culling de conjunto: un MultiMesh gigante puede perjudicar; colisiones se gestionan aparte. |
| [Mesh LOD](https://docs.godotengine.org/en/4.7/tutorials/3d/mesh_lod.html) (nativo) | MIT motor Godot; documentación separada | P0 | Configurar importación y umbrales; comparar calidad y frame time. LOD de importación no sustituye streaming o colisión simplificada. |
| [Visibility ranges HLOD](https://docs.godotengine.org/en/4.7/tutorials/3d/visibility_ranges.html) (nativo) | MIT motor Godot; documentación separada | P0 | Cambiar edificios/grupos por representación simplificada según distancia. Hay que autorar agregados coherentes y medir transiciones; no es streaming automático. |
| [Occlusion culling](https://docs.godotengine.org/en/4.7/tutorials/3d/occlusion_culling.html) (nativo) | MIT motor Godot; documentación separada | P0 | Crear/bakear oclusores y medir escenas interiores/urbanas. Puede no ayudar en terrenos abiertos; medir coste y falsos ocultamientos. |
| [Background loading](https://docs.godotengine.org/en/4.7/tutorials/io/background_loading.html) (nativo) | MIT motor Godot; documentación separada | P0 | Solicitar recursos en segundo plano y organizar sectores con presupuesto. Carga asíncrona no evita por sí sola picos de instanciación ni resuelve diseño de streaming. |
| [Renderer profiles](https://docs.godotengine.org/en/4.7/tutorials/rendering/renderers.html) (nativo) | MIT motor Godot; documentación separada | P0 | Elegir Forward+, Mobile/Compatibility y controlar calidad de sombras/efectos. Una función disponible en PC no implica coste aceptable en Android. |
| [Godot profiler](https://docs.godotengine.org/en/4.7/tutorials/scripting/debug/the_profiler.html) (nativo) | MIT motor Godot; documentación separada | P0 | Registrar medidas del motor, GDScript y monitores; comparar escenarios idénticos. La medición de editor no equivale a export de producción; fijar hardware y configuración. |

### Pruebas, análisis y CI

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [GUT](https://github.com/bitwes/Gut) | MIT | P1 | Tests GDScript por CLI y pruebas de recursos/adaptadores. Main apunta a 4.6: fijar versión apropiada; elegir un framework principal. |
| [GdUnit4](https://github.com/godot-gdunit-labs/gdUnit4) | MIT | P1 | Assertions, scene runners, mocks y CI. Compatibilidad exacta del pin todavía debe probarse; alternativa a GUT. |
| [gdtoolkit](https://github.com/Scony/godot-gdscript-toolkit) | MIT | P1 | Linter, formatter y parser por CLI. Complementa diagnóstico del motor; parser independiente no prueba ejecución. |
| [godot-ci](https://github.com/abarichello/godot-ci) | MIT | P2 | Reusar ideas de importación, tests y exportación en GitHub Actions. Arcont ya tiene CI; usar versiones exactas y adaptar sin reemplazar evidencia existente. |

### Guardado y localización

| Proyecto o capacidad | Licencia / alcance | Orden | Operación propuesta y límite |
|---|---|---|---|
| [Godot Localization Editor](https://github.com/EthanGrahn/godot-localization-editor) | MIT | P3 | Editar CSV y comprobar recursos/UI en varios idiomas. No es traductor automático; validar caracteres, claves y expansión de textos. |
| [Godot SaveKit](https://github.com/fernforestgames/godot-savekit) | MIT | P3 | Configurar serializadores y pruebas de guardar/cargar. Estado del juego separado del historial del editor; ensayar migración y recursos. |

## Fuentes de assets complementarias

Estas tres fuentes son recursos de arte, no otros motores de edición. Registrar cada archivo/pack y sus hashes al incorporarlo.

| Fuente | Uso | Licencia y control propuesto |
|---|---|---|
| [Kenney](https://kenney.nl/support) | Modelos estilizados, UI y sonidos; ya usados en el mapa urbano | CC0 assets publicados. Seleccionar pack/archivo por ID, registrar hash, importación y límites del asset. |
| [Poly Haven](https://polyhaven.com/license) | HDRIs, texturas PBR y modelos | CC0 assets; API/sitio con términos separados. Adquirir assets concretos con procedencia y adaptar resolución/calidad al proyecto. |
| [ambientCG](https://docs.ambientcg.com/license/) | Materiales PBR, modelos y recursos de apariencia | CC0 assets publicados. Importar mapas de textura, configurar materiales y medir uso de memoria. |

## Qué queda por hacer

Elegir el puente mediante la prueba común, implementar adaptadores reales y ejecutar el laboratorio de integración. Fijar releases/commits, checksums de binarios y archivos de terceros para los proveedores elegidos. Conservar y actualizar las modificaciones mínimas como adaptadores, en vez de fusionar decenas de proyectos en un fork difícil de mantener. Esta investigación no modifica las licencias upstream ni la madurez de observaciones previas.
