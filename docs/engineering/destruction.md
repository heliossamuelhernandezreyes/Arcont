# Destrucción y cobertura — lecciones de ARCONT

El sistema de cobertura destructible del prototipo modeló integridad, resistencias por tipo de daño, etapas de deterioro y ruptura final.

## Modelo útil

Una cobertura puede exponer:

- integridad máxima y actual;
- resistencia balística;
- grosor;
- resistencia energética o térmica;
- altura útil de cobertura;
- estado de daño.

## Estados progresivos

En lugar de pasar directamente de intacto a destruido, usar etapas permite cambiar:

- material;
- roughness;
- deformación visual;
- resistencia;
- probabilidad de penetración;
- navegación y cobertura táctica.

## Fragmentos físicos

La ruptura puede generar pocos `RigidBody` temporales. En móvil conviene reducir su cantidad y eliminarlos automáticamente.

## Mejora futura

Para vallas, muros y estructuras largas, preferir daño por segmentos y conexiones estructurales. Un único valor de vida para toda la estructura es sencillo, pero elimina oportunidades tácticas y produce destrucción poco creíble.

## Regla reusable

La destrucción debe modificar gameplay, no solo apariencia. Si abre una brecha, esa brecha debe afectar colisión, IA, cobertura, línea de tiro y navegación.
