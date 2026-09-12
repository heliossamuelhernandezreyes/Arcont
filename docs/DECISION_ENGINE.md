# ARCONT Decision Engine

El Decision Engine convierte evidencia en recomendaciones condicionadas. No es un sistema de reglas absolutas.

## Entrada

Una decisión debe recibir contexto explícito:

- objetivo;
- plataforma;
- hardware objetivo;
- versión de motor;
- renderer;
- escala esperada;
- restricciones de memoria/CPU/GPU/térmicas;
- necesidades de calidad, latencia y mantenibilidad.

## Proceso

1. Recuperar reglas relacionadas.
2. Filtrar por compatibilidad de versión/plataforma.
3. Recuperar evidencia y resultados negativos.
4. Detectar contradicciones.
5. Puntuar confianza según calidad y repetición de evidencia.
6. Exponer desconocidos relevantes.
7. Proponer opciones, no una conclusión falsa de certeza.
8. Registrar la decisión y sus condiciones.

## Salida recomendada

```yaml
decision_id: ARC-DEC-0001
question: null
context: {}
options: []
recommended: null
confidence: low
supported_by: []
contradicted_by: []
unknowns: []
conditions: []
revalidation_trigger: []
```

## Principios

- Una recomendación sin evidencia suficiente debe decirlo.
- La confianza no depende del número de documentos, sino de la fuerza de la evidencia.
- Resultados negativos pesan tanto como resultados positivos.
- Una recomendación puede ser diferente para Android y desktop.
- Cambiar de versión de Godot puede invalidar la recomendación.

## Regla final

ARCONT debe preferir una respuesta incompleta pero trazable a una respuesta segura de sí misma pero inventada.