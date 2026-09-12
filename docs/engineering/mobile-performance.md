# Rendimiento móvil — lecciones de ARCONT

## Principios que funcionaron

1. **MultiMesh/instancing para repetición masiva.** Vegetación y elementos repetidos deben compartir geometría y material cuando sea posible.
2. **Chunks espaciales.** Separar mundo por celdas permite visibilidad, streaming y presupuestos locales.
3. **LOD por distancia.** Geometría cercana y representación simplificada lejana reducen carga de vértices y fragmentos.
4. **Colisión más simple que el arte.** La colisión debe representar jugabilidad, no copiar cada detalle visual.
5. **Destrucción efímera.** Fragmentos físicos deben tener cantidad limitada en móvil y autodestruirse tras pocos segundos.
6. **Texturas comprimidas para Android.** ETC2/ASTC deben formar parte del pipeline cuando el motor y dispositivos objetivo lo permitan.

## Antipatrones observados

- Generar demasiada geometría única cuando un MultiMesh sería suficiente.
- Mantener físicas complejas fuera de cámara.
- Confundir fidelidad visual con fidelidad de colisión.
- Diseñar primero para escritorio y recortar después para móvil.

## Regla reutilizable

Antes de añadir un efecto o sistema, definir su presupuesto aproximado de CPU, GPU, memoria, draw calls y física en el dispositivo objetivo.
