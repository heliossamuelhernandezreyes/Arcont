# ARCONT Knowledge Validator Specification

El validador revisa la coherencia interna del banco de conocimiento. No decide si una afirmación es verdadera por sí solo; detecta problemas de trazabilidad, estructura y vigencia.

## Contrato objetivo

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

## Cobertura implementada en 1.1

`arcont_lab validate` comprueba documentos propios, IDs globales y los registros
del grafo tipado en `docs/godot/knowledge/`: referencias colgantes, ciclos de
derivación/dependencia y evidencia por ID, caminos de reglas/decisiones a
fuentes u observaciones y dependencias falsificadas o sustituidas. Los símbolos
de implementación necesitan un commit fijado. Los benchmarks completados
necesitan resultados válidos; los prerregistrados no necesitan fingir una
ejecución. Una regla validada debe superar los requisitos acumulativos de L7.

Los niveles de madurez comprueban tipos y umbrales de metadatos declarados; no
certifican por sí solos que se ejecutaron los experimentos contados. El ledger
y las afirmaciones en prosa no se convierten automáticamente en nodos tipados.
El análisis de impacto informa cobertura y documentos sin representación;
continúa siendo parcial. El contrato objetivo anterior incluye revisiones
humanas que el CLI aún no automatiza.

`arcont_lab compare` exige controles comparables, incluido VSync, motor y
duración. Los ejes intencionales se declaran con `--vary`; se informan métricas
anidadas y se anula el delta de unidades incompatibles. Las unidades no se
convierten automáticamente. La evidencia runtime se valida además contra su
prerregistro mediante `runtime_evidence.py`.
