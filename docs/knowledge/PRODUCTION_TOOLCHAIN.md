# Production toolchain 0.1

Una entrada operativa para preparar recursos entregados, validar perfiles de animación y sectores explícitos, y conservar observaciones de rendimiento comparables. Las herramientas compartidas viven en Arcont; los adaptadores nativos, assets y escenas de producción viven en el juego.

## Versión reproducible

`production-toolchain.json` registra los componentes con SHA-256, el motor y las revisiones de origen. La revisión Git completa fija también sus dependencias. `doctor` falla si cambia un archivo registrado. La integración de Nexo fija el commit exacto de Arcont en su lock y en CI.

La consolidación conserva el writer actual de Godot, Map Forge, carreteras y playtests; incorpora los archivos aditivos de Model Forge y del estándar 3D. Los PR anteriores permanecen revisables y no se fusionan automáticamente.

```bash
python tools/production_toolchain.py doctor
python tools/production_toolchain.py assets /ruta/juego/authoring/production/assets.json --project /ruta/juego --stage assets/production_candidates
python tools/production_toolchain.py animation /ruta/juego/authoring/production/animation.json
python tools/production_toolchain.py sector /ruta/juego/authoring/production/sector.json
python tools/production_toolchain.py observe /ruta/evidencia/sector-performance.json
```

## Assets entregados

El plan referencia un manifiesto de procedencia ya revisado por el juego, fijado por hash. Cada GLB/glTF, buffer externo y textura debe aparecer con su SHA-256. Se comprueban rutas, extensiones requeridas, presupuesto de triángulos/materiales y presencia de skin declarada. Esta primera versión admite glTF 2.0 con listas de triángulos y licencias GREEN explícitas.

El staging conserva las rutas relativas en un directorio identificado por contenido. Una repetición devuelve el mismo bundle; modificaciones del origen, de sus dependencias o de la copia son rechazadas. La herramienta no sustituye un validador completo de especificación glTF ni aprueba visualmente un modelo. No convierte FBX/OBJ, crea LODs o recomprime texturas en esta aceptación.

Model Forge conserva la adquisición, inspección y orquestación previa. Sus procesadores externos son experimentales: requieren versiones/binarios fijados y aceptación propia antes de usarlos en entregas.

## Animación y sectores

El perfil exige clips únicos y un mapa de huesos uno a uno. El adaptador nativo de Nexo exige topología parental equivalente, corrige claves de posición/rotación con los rests declarados y conserva tiempos/loops. Guarda y vuelve a cargar la AnimationLibrary. La aceptación usa las 18 animaciones existentes, un caso con nombres/rests cambiados y un control negativo de mapping ausente. No demuestra contacto correcto entre personajes de proporciones diferentes.

Un sector define suelo, coberturas y al menos dos rutas con radio de paso. La validación comprueba segmentos completos contra las cajas expandidas, límites y alturas declaradas de salto. El juego construye una escena editable separada, bakea navegación y comprueba cápsulas y rayos en Godot. El recorrido del controlador de producción se comprueba por el playtest existente; los sweeps del sector no sustituyen ese recorrido.

## Evidencia

Cada revisión conserva receta, hashes, escena nativa guardada, reapertura, PNG real, logs y muestras de intervalos de frame. El resumen calcula media, p50, p95, p99 y máximo; rechaza comparaciones con dispositivo, escenario, motor, renderer, build, resolución o warmup diferentes.

Las observaciones Linux con render de software sirven para detectar fallos y revisar la escena. No establecen FPS sostenido, termales, latencia táctil ni memoria GPU en Android. Los registros `android-device` requieren mediciones reales en ese dispositivo; no se convierten automáticamente en reglas o aprobaciones de rendimiento.

Los contratos están en `schemas/production-asset-plan.schema.json`, `schemas/animation-retarget-profile.schema.json`, `schemas/tactical-sector-recipe.schema.json` y `schemas/production-performance-record.schema.json`. La aceptación externa se ejecuta en Closeseal con `tools/shooter_production_smoke.py` y su workflow de Nexo.
