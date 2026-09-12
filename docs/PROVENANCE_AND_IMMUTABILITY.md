# Evidence Provenance and Immutability

ARCONT debe poder demostrar qué código, motor, hardware y datos produjeron cada resultado.

## Provenance envelope

Toda corrida experimental publicable debe registrar como mínimo:

- `run_id` estable;
- versión/commit exactos del motor;
- commit exacto del harness externo;
- versión del schema de resultado;
- perfil de hardware y plataforma;
- renderer/backend/configuración relevante;
- timestamp UTC;
- referencia a datos crudos;
- SHA-256 de los datos crudos;
- SHA-256 del resultado normalizado cuando se archive.

## Inmutabilidad

Un resultado publicado no se edita silenciosamente. Una corrección crea una nueva revisión o `run_id` y conserva el resultado anterior.

Los datos crudos son append-only desde la perspectiva científica. Si se detecta corrupción o error metodológico, se marca el resultado como invalidado/superseded y se conserva para auditoría.

## Hashing

El hash canónico es SHA-256 calculado sobre los bytes originales del archivo. No se recalcula sobre una representación transformada para fingir continuidad.

Formato recomendado:

```json
{
  "algorithm": "sha256",
  "digest": "<64 hex chars>",
  "bytes": 123456,
  "artifact": "raw/frame_times.csv"
}
```

## Cadena de trazabilidad

`Godot commit -> harness commit -> run metadata -> raw artifact hash -> normalized result -> Evidence Ledger -> Knowledge Graph -> rule/decision`.

Si falta un eslabón, ARCONT debe degradar la confianza o impedir una promoción de madurez que dependa de él.
