# Generación procedural de mundo — lecciones de ARCONT

El prototipo forestal separó correctamente cuatro responsabilidades: terreno, hidrología, ecología y puente de assets.

## Terreno

- Heightfield generado mediante ruido macro y detalle.
- Relieve, valle, crestas y caída de borde controlados por parámetros.
- Máscaras derivadas para pendiente, humedad, flujo y composición.
- Rutas y claros tratados como información de composición, no solo como geometría.

## Hidrología

El agua debe derivarse de la forma del terreno y de información de flujo, en lugar de colocarse completamente a mano. Esto permite que vegetación y materiales respondan al mismo modelo espacial.

## Ecología

La dispersión procedural mejora cuando cada tipo de elemento consulta:

- pendiente;
- humedad;
- cercanía al agua;
- rutas;
- claros;
- ruido de agrupamiento;
- densidad local.

El resultado es más coherente que una dispersión aleatoria uniforme.

## Arquitectura recomendada

`Terrain -> Derived Fields -> Hydrology -> Ecology -> Asset Representation`

Las capas deben compartir datos, pero no mezclarse en un único script monolítico.

## Lección clave

El mundo procedural es más potente cuando genera **campos de información reutilizables**. Esos campos pueden alimentar arte, navegación, spawns, audio, clima y gameplay.
