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

## Ejemplo

```yaml
id: ARC-GODOT-RENDER-0001
type: RULE
claim: "..."
engine_version: 4.7.2-stable
engine_commit: ed1daf0bf001b61586d9930840f2f1394092c079
status: proposed
confidence: low
evidence: []
limitations: []
last_validated: null
```

El ledger debe crecer junto con los experimentos; no es una lista de opiniones.