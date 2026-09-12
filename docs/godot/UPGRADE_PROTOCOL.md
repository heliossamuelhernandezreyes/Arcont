# Godot Upgrade Protocol

ARCONT fija una versión de Godot para que el conocimiento sea reproducible, pero debe poder avanzar sin perder trazabilidad.

## Cuando aparezca una nueva versión objetivo

1. Registrar versión, tag y commit upstream.
2. Mantener el pin anterior en el historial documental.
3. Revisar changelog y diffs de subsistemas relevantes.
4. Clasificar afirmaciones del Evidence Ledger por posible impacto.
5. Repetir primero los benchmarks centinela.
6. Comparar resultados con la línea base anterior.
7. Marcar reglas como confirmadas, degradadas, superseded o falsified.
8. Solo después cambiar la versión canónica de estudio.

## Benchmarks centinela

La suite mínima debe cubrir:

- coste base Node/Node3D;
- `_process` y física;
- instanciación/liberación;
- MeshInstance3D/MultiMesh;
- cuerpos físicos;
- navegación;
- animación;
- audio;
- carga de recursos;
- Android/rendering cuando aplique.

## Regresión

Una regresión no es únicamente menor FPS. Puede ser mayor frame-time tail, memoria, stutter, tiempo de carga, consumo térmico, inestabilidad, diferencia visual o cambio semántico de API.

## Resultado

Cada migración debe producir un informe comparativo. ARCONT nunca debe borrar silenciosamente lo aprendido sobre una versión anterior.