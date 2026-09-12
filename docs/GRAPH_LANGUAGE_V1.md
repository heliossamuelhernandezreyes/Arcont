# ARCONT Graph Language v1

ARCONT no usa YAML general para su grafo de conocimiento. Usa un subconjunto deliberadamente pequeño, determinista y compatible con `tools/arcont_lab.py`.

## Objetivo

Evitar que un archivo sea YAML válido para una herramienta externa pero tenga una interpretación distinta dentro de ARCONT.

## Estructura admitida

Un archivo de grafo puede contener escalares de nivel raíz y exactamente dos colecciones estructurales:

```yaml
engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
nodes:
  - id: ARC-SOURCE-NODE
    kind: source-symbol
    path: scene/main/node.cpp
    symbol: Node
edges:
  - from: ARC-RULE-NODE
    to: ARC-SOURCE-NODE
    relation: derived_from
```

## Reglas sintácticas

- codificación UTF-8;
- comentarios sólo mediante líneas cuyo primer carácter no blanco sea `#`;
- claves raíz en formato `key: scalar`;
- `nodes:` y `edges:` son listas de objetos planas;
- cada elemento comienza con `- key: scalar`;
- las propiedades siguientes pertenecen al mismo objeto mientras permanezcan indentadas;
- no se admiten objetos anidados dentro de nodos o edges;
- no se admiten listas inline como sintaxis semántica del grafo;
- no se admiten anchors, aliases, tags YAML, bloques multilínea, merge keys ni tipos personalizados;
- los valores reconocidos son `null`/`~`, booleanos, enteros, floats y strings simples o entre comillas;
- cualquier necesidad que exceda este lenguaje debe versionar el formato antes de ampliar el parser.

## Invariantes semánticos

Todo nodo debe tener `id` y `kind`. Los nodos `source-symbol` deben incluir `path` y `symbol`. Los IDs de nodo no pueden repetirse dentro de un mismo grafo. Todo edge debe apuntar a IDs existentes y declarar `relation`.

Las relaciones de dependencia que participan en análisis de impacto son actualmente:

- `depends_on`
- `implemented_by`
- `measured_by`
- `derived_from`
- `supports`
- `valid_on`
- `related_to`

## Compatibilidad futura

`Graph Language v1` es un contrato, no una descripción accidental del parser. Si ARCONT necesita estructuras anidadas, arrays ricos u otra semántica YAML, debe introducir `Graph Language v2`, un migrador o un parser formal compatible, y conservar la capacidad de leer evidencia histórica.

## Regla canónica

Un archivo que dependa de características de YAML fuera de este subconjunto no es un grafo ARCONT válido aunque un parser YAML de propósito general pueda abrirlo.
