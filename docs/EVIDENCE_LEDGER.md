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
  sources:
    - core/os/main_loop.h
    - scene/main/scene_tree.h
  status: validated
  confidence: high
  limitations: [afirmación estructural; no implica coste runtime]
  last_validated: 2026-09-12

- id: ARC-GODOT-SRC-SCENE-0002
  type: SOURCE
  claim: SceneTree::ProcessGroup mantiene listas separadas para nodes y physics_nodes, además de colas, estado de orden y ownership.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  sources:
    - scene/main/scene_tree.h
  status: validated
  confidence: high
  limitations: [no establece por sí sola la complejidad temporal observada]
  last_validated: 2026-09-12

- id: ARC-GODOT-SRC-SCENE-0003
  type: SOURCE
  claim: Node almacena modos de proceso, grupos de thread, prioridades y flags compactos de process/physics_process.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  sources:
    - scene/main/node.h
  status: validated
  confidence: high
  limitations: [estructura interna; requiere node.cpp para completar flujo de mutación]
  last_validated: 2026-09-12

- id: ARC-GODOT-HYP-SCENE-0001
  type: INFERENCE
  claim: nodos sin procesamiento activo deberían tener menor coste incremental por frame que nodos registrados para callbacks de proceso.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  evidence:
    - ARC-GODOT-SRC-SCENE-0002
    - ARC-GODOT-SRC-SCENE-0003
  status: proposed
  confidence: low
  limitations: [pendiente de benchmark]
  last_validated: null

- id: ARC-GODOT-HYP-SCENE-0002
  type: INFERENCE
  claim: el coste por frame debería correlacionar más con nodos registrados en process groups que con el número total de nodos del árbol.
  engine_version: 4.7.2-stable
  engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
  evidence:
    - ARC-GODOT-SRC-SCENE-0002
  status: proposed
  confidence: low
  limitations: [pendiente de benchmark]
  last_validated: null
```

El ledger debe crecer junto con los experimentos; no es una lista de opiniones.