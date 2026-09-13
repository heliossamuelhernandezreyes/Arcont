# ARCONT Evidence Ledger

El ledger es el registro de afirmaciones técnicas de ARCONT. Su función es impedir que una conclusión sobreviva separada de la evidencia que la originó.

## Registro mínimo

Cada afirmación relevante debe tener:

- ID estable (`ARC-GODOT-...`);
- afirmación;
- tipo: SOURCE / OBSERVATION / INFERENCE / RULE;
- versión/commit aplicable;
- fuente o experimento;
- nivel de confianza;
- condiciones y límites;
- evidencia contradictoria conocida;
- fecha de última validación;
- estado: proposed / observed / reproduced / validated / superseded / falsified.

## Invariantes

- Una inferencia nunca se presenta como hecho del código fuente.
- Un benchmark nunca se presenta como universal.
- Un resultado negativo se conserva.
- Una regla puede ser degradada o falsificada.
- Cambiar de versión de motor obliga a revisar las reglas afectadas.
- La ausencia de evidencia se registra como desconocido, no como cero ni como falso.

## Entradas activas

```yaml
- id: ARC-GODOT-SRC-SCENE-0001
  type: SOURCE
  claim: SceneTree hereda directamente de MainLoop e implementa su contrato de ciclo principal.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  sources: [core/os/main_loop.h, scene/main/scene_tree.h]
  status: validated
  confidence: high
  limitations: [afirmación estructural; no implica coste runtime]
  last_validated: 2026-09-12

- id: ARC-GODOT-SRC-SCENE-0002
  type: SOURCE
  claim: SceneTree::ProcessGroup mantiene listas separadas para nodes y physics_nodes, además de colas, estado de orden y ownership.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  sources: [scene/main/scene_tree.h]
  status: validated
  confidence: high
  limitations: [no establece por sí sola la complejidad temporal observada]
  last_validated: 2026-09-12

- id: ARC-GODOT-SRC-SCENE-0003
  type: SOURCE
  claim: Node almacena modos de proceso, grupos de thread, prioridades y flags compactos de process/physics_process.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  sources: [scene/main/node.h]
  status: validated
  confidence: high
  limitations: [estructura interna; requiere node.cpp para completar flujo de mutación]
  last_validated: 2026-09-12

- id: ARC-GODOT-OBS-SCENE-0001
  type: OBSERVATION
  claim: En una VM Linux headless con Godot 4.7.2-stable, 3000 Nodes con un callback _process vacío mostraron mayor coste CPU de proceso por frame que 3000 Nodes inactivos sin script.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  experiment: ARC-CAMPAIGN-GODOT-FUNDAMENTALS-01
  evidence: [docs/observations/ARC-GODOT-OBS-SCENE-0001.json, runtime workflow 34692053393, runtime evidence merge e828f7dc174173cbc0509818cea96b59e4263dcf]
  measurements: {inactive_cpu_ms_mean: 0.0413120975160992, process_cpu_ms_mean: 0.408764949402031, cpu_ms_delta: 0.3674528518859318, process_to_inactive_cpu_ratio: 9.89455810716792}
  status: observed
  maturity: L3_OBSERVED
  confidence: medium
  limitations: [una sola observación emparejada; N=3000; repetición 1; VM Linux; headless; gl_compatibility; debug; sin reproducción independiente; sin diversidad de hardware o versión]
  contradictory_evidence: [ninguna evidencia canónica contradictoria registrada; corridas preliminares rechazadas no cuentan como evidencia]
  last_validated: 2026-09-12

- id: ARC-GODOT-HYP-SCENE-0001
  type: INFERENCE
  claim: nodos sin procesamiento activo deberían tener menor coste incremental por frame que nodos registrados para callbacks de proceso.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  evidence: [ARC-GODOT-SRC-SCENE-0002, ARC-GODOT-SRC-SCENE-0003, ARC-GODOT-OBS-SCENE-0001]
  status: observed
  maturity: L3_OBSERVED
  confidence: medium
  limitations: [observado sólo en N=3000 y una repetición sobre una VM Linux headless; no es aún una regla general]
  last_validated: 2026-09-12

- id: ARC-GODOT-HYP-SCENE-0002
  type: INFERENCE
  claim: el coste por frame debería correlacionar más con nodos registrados en process groups que con el número total de nodos del árbol.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  evidence: [ARC-GODOT-SRC-SCENE-0002]
  status: proposed
  confidence: low
  limitations: [pendiente de barrido y comparación suficiente para evaluar correlación]
  last_validated: null

- id: ARC-GODOT-OBS-MAP-NAV-0001
  type: OBSERVATION
  claim: En Close Seal sobre Godot 4.7.2 Linux CI, la superficie de corredores creada por compile_route_surface() contiene polígonos pero no resulta físicamente consultable por NavigationServer3D, mientras una superficie procedural mínima separada sí resulta consultable en el mismo entorno.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  evidence: [docs/knowledge/observations/MAP_FORGE_NAVIGATION_FAILURE_RESEARCH_2026-09-13.md, Close Seal Map Authoring Providers CI]
  status: observed
  maturity: L3_OBSERVED
  confidence: high
  limitations: [un repositorio de producción; Linux GitHub Actions; compilador de corredor actual; no demuestra todavía la causa geométrica exacta]
  contradictory_evidence: [la superficie procedural mínima positiva descarta un fallo general del NavigationServer3D en ese entorno]
  last_validated: 2026-09-13

- id: ARC-GODOT-HYP-MAP-NAV-0001
  type: INFERENCE
  claim: Para Map Forge, compilar corredores semánticos a geometría fuente procedural y dejar que NavigationServer3D.bake_from_source_geometry_data() genere la topología final debería ser más robusto que mantener polígonos de navegación manuales como formato de producción.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  evidence: [ARC-GODOT-OBS-MAP-NAV-0001, documentación oficial de Godot sobre baking desde source geometry, historial upstream de fallos de merge/rasterización]
  status: proposed
  confidence: medium
  limitations: [aún no reproducido con éxito en Close Seal; no es regla validada]
  last_validated: null
```

El ledger debe crecer junto con los experimentos; no es una lista de opiniones.
