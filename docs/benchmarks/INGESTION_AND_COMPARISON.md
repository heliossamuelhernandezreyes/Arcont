# Benchmark Ingestion and Comparison Protocol

Este protocolo define cómo un resultado externo entra en ARCONT y cuándo puede usarse para una conclusión.

## Ingesta

1. Validar contra `RESULT_SCHEMA.md`.
2. Confirmar benchmark ID, run ID y versión del esquema.
3. Verificar versión/commit de Godot.
4. Verificar controles experimentales y condiciones térmicas.
5. Registrar referencia a datos crudos.
6. Enlazar hipótesis, source symbols y subsistemas relevantes.
7. Crear una entrada OBSERVATION en el Evidence Ledger.
8. No crear una RULE automáticamente.

## Comparación

Antes de comparar A y B, clasificar cada variable como:

- controlada;
- variable experimental;
- covariable conocida;
- desconocida.

Una diferencia solo puede atribuirse a la variable experimental si el diseño permite aislarla razonablemente.

## Clasificación de comparabilidad

- A: mismos controles críticos; comparación directa.
- B: diferencias menores conocidas; comparación con cautela.
- C: diferencias importantes; solo tendencia exploratoria.
- D: no comparable.

## Detección de regresión

Una regresión potencial puede aparecer en:

- mediana de frame time;
- p95/p99;
- memoria;
- carga;
- draw calls;
- CPU/GPU time;
- stutter;
- estabilidad;
- comportamiento térmico;
- diferencias funcionales o visuales.

No declarar regresión por una sola corrida. Debe existir repetición suficiente y una magnitud que exceda ruido/variabilidad esperable.

## Promoción de conocimiento

`OBSERVATION → REPRODUCED` requiere repetición.

`REPRODUCED → RULE` requiere además una justificación causal o arquitectónica suficiente, límites explícitos y ausencia de evidencia contradictoria dominante.

## Resultado negativo

Si la hipótesis falla, el resultado se conserva y enlaza. Un experimento fallido no es trabajo perdido: reduce el espacio de posibilidades.