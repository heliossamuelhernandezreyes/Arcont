# ARCONT Laboratory Standard v1

ARCONT es un laboratorio técnico reproducible para tecnología de videojuegos. No contiene juegos de producción.

## Principio central

Toda conclusión técnica debe distinguir tres niveles:

1. **SOURCE** — qué afirma o implementa la fuente primaria.
2. **EXPERIMENT** — qué observamos nosotros bajo condiciones controladas.
3. **RULE** — qué decisión de ingeniería recomendamos y bajo qué límites.

Nunca se debe convertir una observación aislada en una regla universal.

## Unidad de conocimiento

Cada entrada técnica debe intentar registrar:

- problema;
- contexto;
- hipótesis;
- fuente primaria y versión;
- implementación o procedimiento;
- hardware y software de prueba;
- métricas;
- resultado;
- limitaciones;
- resultado negativo, si existe;
- interpretación;
- regla reutilizable;
- fecha y versión del análisis.

## Reproducibilidad

Un experimento válido debe poder repetirse sin depender de memoria humana. Debe fijar, cuando aplique:

- motor y versión;
- commit exacto;
- renderer/backend;
- plataforma;
- dispositivo;
- resolución;
- preset gráfico;
- escena mínima o workload;
- duración;
- warm-up;
- número de repeticiones;
- método de captura;
- variables controladas.

## Métricas mínimas de rendimiento

Cuando apliquen:

- FPS promedio;
- frame time promedio;
- percentiles o 1% low;
- CPU frame time;
- GPU frame time;
- memoria RAM;
- memoria gráfica cuando sea accesible;
- draw calls;
- objetos/instancias;
- tiempo de carga;
- temperatura;
- throttling;
- consumo energético aproximado si puede medirse de forma fiable.

## Resultados negativos

Los fallos se conservan. Un resultado negativo debe registrar qué se intentó, por qué parecía razonable, qué ocurrió, cómo se verificó y qué alternativa quedó mejor posicionada.

## Regla de aislamiento

Los experimentos deben ser mínimos. Un experimento puede contener el código estrictamente necesario para probar una hipótesis, pero no debe evolucionar hasta convertirse en un juego.

## Evidencia

Prioridad de fuentes:

1. código fuente upstream fijado por commit;
2. documentación oficial correspondiente a la versión;
3. issues, PRs o discusiones técnicas upstream;
4. medición reproducible propia;
5. fuentes secundarias claramente etiquetadas.

## Estado de una conclusión

Toda recomendación puede marcarse como:

- `OBSERVED` — observado, aún sin suficiente repetición;
- `REPRODUCED` — repetido de forma consistente;
- `PROVISIONAL_RULE` — útil como regla provisional;
- `VALIDATED_RULE` — suficientemente sustentado para reutilización;
- `INVALIDATED` — evidencia posterior contradijo la conclusión.

ARCONT debe conservar también el historial de cambios de criterio.