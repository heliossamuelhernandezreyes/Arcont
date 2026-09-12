# ARCONT Knowledge Graph

ARCONT debe tratar su conocimiento como una red de dependencias, no como una colección plana de documentos.

## Tipos de nodo

- source-symbol
- subsystem
- experiment
- benchmark
- observation
- inference
- rule
- anti-pattern
- negative-result
- decision
- platform
- hardware
- engine-version

## Relaciones

- `depends_on`
- `implemented_by`
- `measured_by`
- `supports`
- `contradicts`
- `supersedes`
- `valid_on`
- `invalidated_by`
- `derived_from`
- `related_to`

## Ejemplo

```yaml
from: ARC-GODOT-RULE-0042
relation: derived_from
to: ARC-GODOT-BENCH-0107
```

Una regla sobre MultiMesh podría depender de RenderingServer, RenderingDevice, renderer, plataforma Android, versión de Godot y uno o más benchmarks.

## Invalidation graph

Cuando cambie una versión del motor, ARCONT debe poder recorrer:

changed source symbol → affected subsystem → experiments → rules → decisions.

Esto permite saber qué conocimiento necesita revalidación en lugar de repetir todo indiscriminadamente.

## Regla de calidad

Una relación no se crea por similitud semántica solamente. Debe existir una razón técnica explícita para enlazar dos nodos.

## Representación

La primera etapa puede mantenerse en Markdown/YAML legible. Si el volumen lo justifica, podrá generarse una representación estructurada adicional, pero la fuente canónica seguirá siendo auditable en Git.