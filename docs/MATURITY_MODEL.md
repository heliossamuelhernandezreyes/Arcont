# ARCONT Knowledge Maturity Model

ARCONT no trata todo conocimiento como equivalente. Cada afirmación puede avanzar o retroceder según la fuerza de su evidencia.

## Niveles

- `L0_UNKNOWN` — no existe evidencia suficiente.
- `L1_SOURCE_TRACED` — la afirmación está vinculada a fuente primaria concreta y versionada.
- `L2_HYPOTHESIS` — existe una predicción explícita, todavía no observada experimentalmente.
- `L3_OBSERVED` — al menos una observación runtime controlada respalda la afirmación.
- `L4_REPRODUCED` — el resultado fue reproducido bajo condiciones equivalentes.
- `L5_CROSS_HARDWARE` — fue reproducido en más de un perfil de hardware relevante.
- `L6_CROSS_VERSION` — sobrevivió revalidación en más de una versión o commit del motor.
- `L7_VALIDATED_RULE` — evidencia fuerte, límites explícitos, contradicciones tratadas y utilidad demostrada para decisiones.

## Reglas de promoción

Una promoción requiere evidencia nueva; nunca se promueve por antigüedad, popularidad o número de documentos que repitan la misma fuente.

`L3+` requiere datos runtime. `L4+` requiere reproducciones independientes. `L5` requiere diversidad real de hardware. `L6` requiere revalidación entre versiones. `L7` exige además límites, evidencia contradictoria conocida y una regla falsable.

## Degradación

La madurez puede bajar cuando:

- cambia un símbolo fuente del que depende la afirmación;
- aparece evidencia contradictoria;
- un benchmark resulta no comparable o defectuoso;
- cambia el renderer, backend, plataforma o API relevante;
- se descubre que faltaban controles experimentales críticos.

El Knowledge Graph y el análisis de impacto deben identificar los nodos afectados. La degradación no borra la evidencia histórica: cambia el estado actual.

## Madurez y confianza no son lo mismo

`maturity` describe el tipo y alcance de validación alcanzado. `confidence` es un índice heurístico para priorizar revisión. Ninguno representa una probabilidad estadística de verdad.

## Invariante

Una regla nunca puede tener una madurez superior a la que su evidencia permite demostrar.
