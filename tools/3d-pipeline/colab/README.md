# ARCONT 3D — Google Colab Free

Este flujo permite generar un `.glb` desde una imagen sin contratar GPU.

## Abrir

Abre el notebook en Colab desde:

https://colab.research.google.com/github/heliossamuelhernandezreyes/Arcont/blob/main/tools/3d-pipeline/colab/ARCONT_3D.ipynb

## Uso recomendado desde Android

1. Abre el enlace en Chrome/Brave.
2. En Colab selecciona `Entorno de ejecución > Cambiar tipo de entorno de ejecución > GPU`.
3. Ejecuta las celdas de arriba abajo.
4. Deja `BACKEND = 'sf3d'` para la mejor salida inicial.
5. Stable Fast 3D requiere aceptar gratis el acceso al modelo en Hugging Face y usar un token de tipo `Read`.
6. Sube una referencia con fondo limpio, cuerpo completo y brazos separados del torso.
7. El notebook intentará remallado `quad` hacia ~2500 vértices; si ese paso falla, conserva automáticamente la malla generada sin remallado.
8. Al terminar, Android descargará `arcont_character.glb`.

## Backend de respaldo

Cambia:

```python
BACKEND = 'triposr'
```

para usar TripoSR. No requiere token de Hugging Face y sirve para blockouts rápidos, aunque la reconstrucción humana suele ser inferior a Stable Fast 3D.

## Coste

El notebook está diseñado para el nivel gratuito de Google Colab. La GPU gratuita no está garantizada: Google puede no asignarla o cortar sesiones según disponibilidad y uso. El flujo no incluye ningún servicio de pago ni claves de facturación.

## Objetivo de Arcont

Este notebook solo cubre `imagen -> malla`. La etapa posterior prevista es:

`GLB -> limpieza -> retopología final -> segmentación anatómica -> rig -> gore modular -> Godot`.
