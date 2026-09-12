# ARCONT Knowledge Validator Specification

El validador revisa la coherencia interna del banco de conocimiento. No decide si una afirmación es verdadera por sí solo; detecta problemas de trazabilidad, estructura y vigencia.

## Chequeos obligatorios

### Identidad
- IDs duplicados.
- IDs mal formados.
- referencias a IDs inexistentes.

### Evidencia
- RULE sin evidencia.
- INFERENCE presentada como SOURCE.
- afirmación SOURCE sin versión/commit/ruta/símbolo cuando dependa de implementación.
- benchmark sin resultado o sin metadatos mínimos.
- decisión sin reglas/evidencia enlazada.

### Vigencia
- reglas aplicables a una versión distinta del pin canónico sin revalidación.
- conocimiento marcado validated cuya evidencia fue superseded/falsified.
- nodos afectados por cambio de versión todavía no revalidados.

### Grafo
- relaciones colgantes.
- ciclos inválidos cuando impliquen derivación lógica circular.
- decisión que depende de una regla falsificada.
- regla sin camino hacia SOURCE u OBSERVATION.

### Benchmarks
- runs comparados con controles incompatibles sin advertencia.
- resultados sin raw_data_ref cuando debería existir.
- ausencia de repeticiones o warm-up cuando el protocolo de la prueba los exige.
- campos inventados en lugar de `null`.

## Severidad

- ERROR: rompe trazabilidad o invalida una conclusión.
- WARNING: evidencia incompleta o conocimiento posiblemente obsoleto.
- INFO: oportunidad de mejorar cobertura.

## Salida sugerida

```yaml
validator_version: 1
status: fail
errors: 2
warnings: 5
findings:
  - severity: ERROR
    code: RULE_WITHOUT_EVIDENCE
    subject: ARC-GODOT-RULE-0042
    message: "Validated rule has no evidence path."
```

## Invariante

El validador nunca transforma automáticamente una hipótesis en regla ni una regla en verdad. Solo verifica que el conocimiento respete el contrato epistemológico de ARCONT.