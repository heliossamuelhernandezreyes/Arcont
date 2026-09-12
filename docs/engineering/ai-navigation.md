# IA y navegación — lecciones de ARCONT

El prototipo utilizó un `AStar3D` con puntos escritos manualmente y conexiones validadas mediante raycasts.

## Ventajas del enfoque

- Muy simple de depurar.
- Determinista.
- Suficiente para mapas pequeños y estáticos.
- Barato en CPU.

## Limitaciones detectadas

- Escala mal a mapas grandes.
- Los puntos manuales introducen mantenimiento constante.
- Si una puerta se abre, una cobertura cae o una barricada desaparece, el grafo puede quedar desactualizado.
- La geometría física y la representación mental de la IA pueden divergir.

## Recomendación reusable

Usar grafos manuales solo cuando el espacio táctico sea pequeño y controlado. Para mundos dinámicos, combinar navegación del motor, obstáculos dinámicos, enlaces especiales y reconstrucción localizada.

## Regla de diseño

Cualquier sistema destructible que modifique transitabilidad debe notificar a navegación. La destrucción visual sin actualización navegacional crea errores sistémicos difíciles de depurar.
