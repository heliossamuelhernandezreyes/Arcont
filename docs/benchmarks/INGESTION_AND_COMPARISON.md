# Benchmark Ingestion and Comparison Protocol

Este protocolo define cómo un resultado externo entra en ARCONT y cuándo puede usarse para una conclusión.

## Prerregistro

Antes de ejecutar una prueba, el benchmark debe existir en la campaña canónica `FIRST_RUNTIME_MATRIX.json` y estar enlazado al Knowledge Graph. La campaña se valida con:

```bash
python tools/runtime_evidence.py validate-plan
```

Modificar hipótesis, sweep, warm-up, duración, repeticiones o controles después de observar resultados invalida la comparación con el prerregistro original. Un rediseño se registra como una nueva revisión/campaña, no como edición retroactiva.

## Ingesta

1. Validar estructura básica contra `RESULT_SCHEMA.md` / `benchmark-result.schema.json`.
2. Validar contra el benchmark prerregistrado mediante `tools/runtime_evidence.py validate-result`.
3. Confirmar benchmark ID, run ID y versión del esquema.
4. Verificar versión y commit exactos de Godot.
5. Verificar OS, dispositivo, CPU, GPU, renderer, resolución, build y VSync.
6. Verificar variable, sweep point, repetición, warm-up y duración contra el plan.
7. Verificar commit exacto del harness externo.
8. Verificar SHA-256 del artefacto de datos crudos.
9. Verificar controles experimentales y condiciones térmicas disponibles.
10. Enlazar hipótesis, source symbols y subsistemas relevantes.
11. Crear una entrada OBSERVATION en el Evidence Ledger sólo después de pasar estos gates.
12. No crear una RULE automáticamente.

Un archivo `*.result.json` que sólo pasa el schema genérico pero no el contrato de campaña **no es evidencia runtime canónica**.

## Corridas abortadas

Una corrida abortada se conserva. Debe registrar `aborted=true` y `abort_reason`. Puede carecer de algunas métricas finales, pero no puede presentarse como resultado exitoso ni contarse como reproducción. Los datos parciales y el motivo de aborto son evidencia sobre límites operativos, no sobre la hipótesis completa.

## Comparación

Antes de comparar A y B, clasificar cada variable como:

- controlada;
- variable experimental;
- covariable conocida;
- desconocida.

Una diferencia sólo puede atribuirse a la variable experimental si el diseño permite aislarla razonablemente.

## Clasificación de comparabilidad

- A: mismos controles críticos; comparación directa.
- B: diferencias menores conocidas; comparación con cautela.
- C: diferencias importantes; sólo tendencia exploratoria.
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

- Prerregistro + source trace + hipótesis: techo L2.
- Primera observación runtime válida: puede habilitar L3.
- L4 requiere al menos dos reproducciones independientes válidas; no dos resúmenes calculados de la misma corrida.
- L5 requiere diversidad real de hardware relevante.
- L6 requiere revalidación en dos o más versiones/commits del motor.
- L7 sigue requiriendo además límites explícitos, contradicciones tratadas, falsabilidad y utilidad demostrada para decisiones.

La promoción debe pasar el validador de madurez de ARCONT; nunca se infiere sólo por el número de archivos presentes.

## Resultado negativo

Si la hipótesis falla, el resultado se conserva y enlaza. Un experimento fallido no es trabajo perdido: reduce el espacio de posibilidades.
