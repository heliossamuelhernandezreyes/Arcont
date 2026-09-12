# Plantilla de experimento ARCONT

## Identidad

- ID:
- Fecha:
- Autor/ejecutor:
- Área:
- Estado: `OBSERVED | REPRODUCED | PROVISIONAL_RULE | VALIDATED_RULE | INVALIDATED`

## Pregunta

¿Qué queremos saber exactamente?

## Hipótesis

Resultado esperado antes de ejecutar la prueba.

## Fuente

- Motor/herramienta:
- Versión:
- Commit/tag:
- Documentación/código relevante:

## Entorno

- Dispositivo:
- SoC/CPU:
- GPU:
- RAM:
- SO:
- Resolución:
- Renderer/backend:
- Build:
- Estado térmico inicial:

## Variables controladas

Lista de elementos que deben permanecer constantes.

## Variable independiente

Qué cambia entre las corridas.

## Procedimiento

Pasos exactos para reproducir la prueba.

## Warm-up

Cómo se estabiliza la prueba antes de medir.

## Muestras

Número de repeticiones y duración de cada una.

## Métricas

| Métrica | Resultado | Unidad | Método |
|---|---:|---|---|
| FPS promedio | | fps | |
| 1% low | | fps | |
| Frame time | | ms | |
| CPU | | ms | |
| GPU | | ms | |
| RAM | | MB | |
| Draw calls | | | |
| Temperatura final | | °C | |

## Observaciones

Comportamientos no previstos, stutter, artefactos, errores, throttling u otros efectos.

## Resultado

Qué ocurrió, separado de la interpretación.

## Interpretación

Por qué creemos que ocurrió.

## Límites

Qué NO demuestra este experimento.

## Resultado negativo

Registrar intentos fallidos relevantes.

## Regla reutilizable

Conclusión operativa y condiciones bajo las que aplica.

## Próxima prueba

Qué experimento permitiría refutar, ampliar o validar la conclusión.