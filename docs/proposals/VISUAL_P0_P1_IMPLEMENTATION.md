# ARCONT Visual Production — P0/P1 implementation candidate

**Estado:** candidato en PR; no constituye la liberación de ARCONT 1.2.0.
**Alcance:** análisis y validación **sólo lectura**; sin red, sin importar Godot, sin escritura de assets o escenas.

## P0 — Contrato visual portable

`tools/visual_production_contract.py` valida el JSON Schema Draft 2020-12 de
`schemas/proposals/visual-production-intent.schema.json` usando `jsonschema==4.25.1`.
Además verifica referencias cruzadas, capas únicas, compatibilidad de renderer conocida,
cámaras y ROI, perfiles y presupuestos coherentes.

Ejemplo en ARCONT:

```bash
python -m pip install jsonschema==4.25.1
python tools/visual_production_contract.py templates/visual-production/industrial_arena.example.json --json
```

Ejemplo con un juego externo **local**:

```bash
python tools/visual_production_contract.py /juegos/demo/visual.intent.json --project-root /juegos/demo --json
```

Con `--project-root` comprueba el mapa, SHA-256 si está fijado,
`regions` citadas por zonas y —para cada asset `staged`/`approved`— la existencia
del recibo local, licencia CC0, hash del recibo y hash de bytes realmente disponibles.
Un asset `planned` no se confunde con uno descargado. Los estados
`measured` se rechazan por falta de trazas auditadas externas: un documento
de diseño no certifica mediciones. No habilita la red o permisos de escritura.

La fixture `industrial_arena.example.json` es **sintética** y usa un mapa
no incluido: sin `--project-root` se valida sólo el contrato y se informa
que las referencias externas y los assets no fueron verificados.

## P1 — Inventario honesto de una escena Godot

`tools/visual_scene_inventory.py` inspecciona .tscn (hasta 4 MiB), sin arrancar
el motor, ejecutar scripts, solicitar red ni alterar import caches. Cuenta únicamente
nodos declarados estáticamente, luces, meshes y scripts. En escenas construidas
dinámicamente **NO** es un conteo real completo.

```bash
python tools/visual_scene_inventory.py --project-root /juegos/demo --scene scenes/main.tscn
```

Salida JSON:

- `static_source`: nodos realmente declarados, tipos, luces y scripts encontrados;
- `runtime`: `null` sin snapshot externo; **no rellenar con inventarios inventados**;
- `limitations`: advertencias sobre nodos generados con GDScript, faltantes y ausencia de
  evidencia de FPS/termales/calidad artística;
- `writes_performed: false`, `engine_executed: false`, `network_used: false`.

Opcionalmente, acepta `--snapshot /juegos/demo/evidence/scene-tree.json`
como **evidencia suministrada por un juego externo**, que debe referenciar mismo
hash de la escena, ruta, renderer, Godot, commit origen y un listado acotado de nodos.
Estas afirmaciones no se autentican automáticamente por el solo hecho de recibir JSON.
El reporte las etiqueta `externally_supplied_runtime_snapshot_unverified`.
Una fase posterior debe añadir un exportador nativo de Godot con firma/CI en el proyecto
de juego y vincular su recibo con el origen.

Ejemplo conceptual de snapshot:

```json
{
  "protocol": "arcont-godot-scene-snapshot",
  "version": 1,
  "scene_path": "scenes/main.tscn",
  "scene_sha256": "<sha256 of scene .tscn>",
  "capture_source": "native-godot",
  "engine_version": "4.7.2-stable",
  "renderer": "gl_compatibility",
  "source_commit": "<40-digit git commit>",
  "nodes": [
    {"path": "World/Key", "type": "DirectionalLight3D", "shadow_enabled": true},
    {"path": "World/Floor", "type": "MeshInstance3D", "material_paths": ["res://materials/floor.tres"]}
  ]
}
```

No se concede a este JSON el nivel L3 OBSERVED sin un origen de ejecución
controlada verificable. No puntúa calidad estética y no certifica Android.

## Casos especiales: FISURA

La escena `scenes/reactivo_13.tscn` de FISURA declara una raíz `Node3D` y
un script `res://scripts/reactivo_13_game.gd`; los centenares de objetos
decorativos y las luces se crean en `_build_world` y stages GDScript. Por
tanto el inventario estático indicará ~1 nodo y avisará de su incompletitud.
Concluir "FISURA tiene cero luces" a partir de ese documento sería **falso**.

La integración posterior en FISURA debe materializar una captura de inventario
dentro del proceso Godot CI, con origen de commit y SHA-256 del .tscn, entregarla
como artefacto y auditarla aquí. Eso no se entrega ni se finge en P1.

## Integración ARCONT Agent / Universal Bridge

Dos capacidades ya están registradas en `agent.capabilities.json` como **read-only**:
`visual.intent.validate` y `visual.scene.inventory`. Su uso desde un agente externo
pasa por las operaciones homónimas de `tools/arcont_bridge.py`, sin permiso
de project-write. No son primitivas de edición ni permiten shell arbitrario.

Ejemplo de petición para validar `visual.intent.json` del proyecto:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "validate-intent-01",
  "operation": "visual.intent.validate",
  "arguments": {"path": "visual.intent.json"}
}
```

Para inspeccionar una escena, usar la operación `visual.scene.inventory`:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "inspect-scene-01",
  "operation": "visual.scene.inventory",
  "arguments": {
    "scene": "scenes/main.tscn",
    "intent_path": "visual.intent.json"
  }
}
```

Ambas rechazan argumentos desconocidos y accesos que escapen del proyecto,
incluidos enlaces simbólicos resueltos fuera. El Bridge sigue separado de ARCONT
para cualquier juego y nunca publica automáticamente un parche.

## Gates automatizados

`tests/test_visual_production.py` incluye pruebas positivas y negativas:
rechazo de esquema incompleto, referencias/IDs duplicados, mapa/regions rotas,
rutas con escape o symlink, licencias y hashes falsos, escenas con scripts,
capturas de inventario con hash equivocado y renderer incompatible. El
workflow `knowledge-integrity.yml` invoca el validador y las pruebas.

**Salida de P0:** contrato real. **Salida de P1:** inventario estático y contrato
de ingesta limitado; todavía falta el adaptador de captura nativa del juego,
la comparación de shots y profiling Android de las fases P2-P3.

**Versionado:** `arcont.manifest.json` continúa en 1.1.0; no se declara
operativa una capacidad bridge/MCP antes de registrar controles y aceptación.
