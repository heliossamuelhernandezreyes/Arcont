# Godot Source Trace Protocol

Este protocolo define cómo ARCONT debe vincular una afirmación técnica con la implementación concreta de Godot.

## Objetivo

Evitar afirmaciones vagas como "Godot hace X" cuando en realidad una conclusión depende de una clase, función, backend, renderer, plataforma o versión específica.

## Trazabilidad mínima

Toda afirmación basada en implementación interna debe registrar:

- versión y commit exactos de Godot;
- ruta upstream;
- clase o subsistema;
- función o símbolo relevante;
- capa: API pública / glue / server / backend / plataforma;
- dirección del flujo de llamadas conocida;
- si la conclusión es observación directa del código o inferencia;
- enlaces a experimentos que validen comportamiento runtime.

## Formato recomendado

```yaml
id: ARC-GODOT-SRC-0001
engine_version: 4.7.2-stable
engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
path: scene/main/node.cpp
symbol: Node::_process
layer: scene
claim_type: SOURCE
confidence: high
upstream_dependencies: []
runtime_validation: []
notes: null
```

## Regla

Leer el código no sustituye medir el runtime y medir el runtime no sustituye leer el código. Cuando sea posible, ARCONT debe mantener ambas vías y enlazarlas.

## Flujo recomendado

API pública → implementación inmediata → server interno → backend → plataforma → experimento → regla.

Cuando el flujo diverja por renderer o plataforma, debe documentarse como ramas diferentes y no colapsarse en una única explicación.