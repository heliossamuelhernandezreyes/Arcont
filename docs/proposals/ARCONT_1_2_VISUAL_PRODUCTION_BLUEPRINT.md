# ARCONT 1.2 — Visual Production Orchestration (propuesta técnica)

**Estado:** BLUEPRINT con P0/P1 experimentales implementados en la rama de PR; NO hay lanzamiento ARCONT 1.2.
**Implementación P0/P1:** `tools/visual_production_contract.py`, `tools/visual_scene_inventory.py`, operaciones read-only del Bridge y pruebas `tests/test_visual_production.py`; ver [`VISUAL_P0_P1_IMPLEMENTATION.md`](VISUAL_P0_P1_IMPLEMENTATION.md). La captura **nativa** del árbol de Godot en FISURA y su certificación CI siguen pendientes.
**Fecha:** 2026-10-08.
**Repositorio:** ARCONT = laboratorio de conocimiento y contratos; los juegos permanecen externos.
**Caso de aceptación inicial:** FISURA Reactivo-13, únicamente como consumidor externo; no se incorporan assets, escenas ni código de FISURA a ARCONT.

## 0. Decisión arquitectónica

Construir una **capa delgada de intención, inspección y evidencia visual** que orqueste los sistemas ya existentes. No crear un "motor de belleza" ni duplicar los ejecutores de ARCONT 1.1.

Inventario revisado en main:
- `schemas/map-authoring-contract.schema.json` y `tools/map_forge_contract.py`: contrato semántico y validación.
- `tools/public_asset_discovery.py`: búsqueda controlada en Poly Haven con política de proyecto, manifiestos, verificación y staging condicionado.
- `tools/model_forge_control.py`: inspección, presupuestos y staging local de glTF/GLB.
- `tools/production_control.py`: assets, sector, audio, performance y acabados; no reemplazar.
- `tools/godot_structured_editing.py`: cambios con SHA previo, validación de Godot y commit atómico en un proyecto externo.
- `tools/development_session.py`: planes acotados, bloqueo de escritor, recibos, revalidación y no reintento silencioso.
- `tools/viewport_evidence_gate.py`: integridad/dimensiones/diferenciación de PNG; NO prueba calidad visual.
- `schemas/external-evidence.schema.json` y `docs/MATURITY_MODEL.md`: evidencia externa L0-L7.
- `arcont.manifest.json`: 1.1.0; prohibido código de juego o proyecto Godot embebido.

**Regla invariable:** gameplay y colisiones = juego propietario. Intención visual, auditoría, evidencia y esquemas = ARCONT. Un adaptador del proyecto materializa la presentación sin reescribir el mapa semántico.

**No objetivos para 1.2:** IA infalible que puntúe belleza, iluminación fotorrealista automática, ejecución de shaders arbitrarios, rasterizador propio, extracción arbitraria de archivos, descargas por URLs del modelo, bypass del permiso project-write, certificado AAA, FPS garantizado desde Linux.

## 1. Resultado de producto

Un agente externo debería poder pedir:
"Inspecciona una escena industrial, identifica monotonía de materiales y errores verificables de iluminación, construye una propuesta de dos variantes y prepara el plan de pruebas sin cambiar gameplay".

Debería obtener:
1. Informe de inventario de luces, mallas, materiales y assets con enlaces a identificadores reales.
2. Intención visual tipada (zonas, jerarquía, paleta, presupuesto, roles).
3. Propuesta de cambios ordenados, con costo esperado y restricciones de colisión.
4. Diff visual con capturas **comparables** de antes/después, no solo seis PNG distintos.
5. Comparación de hardware real cuando exista; degradación explícita a "no medido" cuando no.
6. Recibos reproducibles con hashes, versión del motor, renderer, escena, cámara y limitaciones.
7. Sólo después del opt-in de escritura: staging en el repositorio del juego y validación, nunca fusión automática.

## 2. Arquitectura de componentes

```text
External game (intent + semantic map + scene + assets)
                |
          READ-ONLY AUDIT
                |
  visual.intent.validate ---- project intent and map cross refs
  visual.scene.inventory --- existing Godot project inspection adapter
  visual.asset.audit ------- Asset Vault / Public Asset / Model Forge
  visual.lighting.audit ---- renderer-specific light inventory
  visual.budget.estimate --- budget model with uncertainty
                |
       REVIEWABLE CHANGE PLAN
  zones + asset roles + lighting profile + material slots
                |
        HUMAN PROJECT-WRITE OPT-IN
                |
  Development Session -> existing structured/Godot authoring adapters
  staged patch -> hash/revision check -> Godot parse -> CI
                |
     CAPTURE + EVIDENCE + COMPARISON
  viewport integrity -> framing/ROI comparison -> perf traces
                |
      HUMAN ART REVIEW + DEVICE GATE
                |
          external game PR
```

La interfaz pública es portable; los adaptadores Godot específicos quedan en ARCONT como herramientas de validación/autoría **aplicadas únicamente a proyectos externos**. Un adaptador de Unity u otro motor no debe cambiar el schema semántico.

## 3. Capacidades de ARCONT 1.2

| ID conceptual | Entrada | Salida | Fase / autoridad |
|---|---|---|---|
| `visual.intent.validate` | contrato visual JSON + mapa opcional | errores, advertencias, referencias cruzadas | P0, sólo lectura |
| `visual.scene.inventory` | proyecto externo, escena, renderer | nodos tipados, materiales, luces, contadores con procedencia | P1, lectura / proceso del motor con opt-in si genera caches |
| `visual.asset.role.audit` | registro visual + inventario/proveniencia existentes | usos faltantes, duplicados, assets no licenciados, anomalías de escala | P1, sólo lectura |
| `visual.lighting.audit` | perfiles y luces reales | cobertura, sombras activas, rango, jerarquía e incompatibilidades conocidas | P1, sin editar la escena |
| `visual.environment.audit` | capas, zonas y escena | cobertura/oclusiones heurísticas, rutas y decoración indebida | P1, sin alterar nav/colisiones |
| `visual.capture.plan` | baseline, cámara y zonas | plan de capturas homologadas, máscaras/ROI | P2, sólo lectura |
| `visual.capture.compare` | PNG verificadas + metadatos de captura | comparabilidad, cambios geométricos y métricas con limitaciones | P2, sólo lectura |
| `visual.budget.evaluate` | contadores + render/device traces opcionales | pronóstico marcado como estimado + mediciones p50/p95/p99 si existen | P2, lectura |
| `visual.plan.stage` | plan validado + revisiones + permiso explícito | solicitud para editores existentes y recibos; ninguna escritura genérica nueva | P3, escritura externa autorizada |

**Estado operacional por fases:** `visual.intent.validate` y `visual.scene.inventory` ahora existen como operaciones read-only del Bridge (candidatas P0/P1), con CLI, pruebas y registro en `agent.capabilities.json`. Las otras siete siguen propuestas; no se han implementado adaptadores de escritura, captura nativa de FISURA ni la comparación visual P2. El manifiesto general sigue en 1.1.0. Ninguna de estas operaciones acredita por sí sola calidad artística o Android.

## 4. Modelo de datos: visual-production-intent v1

El contrato propuesto de referencia vive en `schemas/proposals/visual-production-intent.schema.json`; la fixture neutral en `templates/visual-production/industrial_arena.example.json`.

Campos canónicos:
- `protocol` / `version` / `project_id` / `scene_id`.
- `semantic_map`: ruta relativa existente y SHA-256 opcional; los IDs de zona se cruzan con `regions`/extensiones del mapa, no se redefinen colisiones.
- `render_profile`: motor, renderer, versiones y plataforma objetivo; capacidades explícitas.
- `visual_kit`: familias de materiales, paleta y principios de composición, referencias internas.
- `zones`: cada una con roles (`insertion`, `combat`, `objective`, `extraction`, `transition`), foco visual y `lighting_profile_id`.
- `lighting_profiles`: intención y lista de roles de luces; presupuestos `shadow_budget` y `local_light_budget`; NO prometer que bloom/GI esté disponible en Compatibility.
- `asset_roles`: fichas de rol, categoría, fuente/asset-record externo, ruta opcional, escala esperada, usos/no usos, LOD y estado de procedencia.
- `layers`: gameplay-semantic / structure / functional-props / dressing / signage / atmosphere con relaciones de precedencia y `collider_authority`.
- `budgets`: límites de diseño con unidad y calidad `estimated` o `measured`; target FPS y fallback, total lights/shadows/texture memory/visible instances según evidencia.
- `capture_plan`: cámaras reproducibles, resolución, backend y ROI; referencias baseline/after solo si se dispone de archivos con SHA-256.
- `approval`: roles humanos para arte, performance y release; booleanos para requisitos de aceptación.

Reglas entre documentos que JSON Schema **no** puede resolver:
- `lighting_profile_id` debe referirse a un perfil real y no duplicado.
- `semantic_map` y cada `zone.region_id` deben existir en el mapa versionado si se declara el enlace.
- Un asset `staged` debe tener registro de procedencia verificable y sha256 que coincida con bytes externos; `planned` puede no tener ruta/binario.
- Nadie asigna colisión a `render-only` ni modifica las reglas de misión desde este contrato.
- Presupuestos sin trazas reales se etiquetan `estimated`; CI Linux no acredita Android.
- Las cámaras comparadas deben tener misma pose, FOV, resolución, renderer, escena, tiempo/estado y settings; cualquier diferencia invalida la comparabilidad por defecto.

## 5. Seis módulos funcionales

### A. Visual Kit Forge

**Responsabilidad:** transformar la intención artística en reglas auditablemente coherentes, sin generar arte por sí mismo.

Entradas: visual kit, zonas, materiales existentes, shot list.
Salidas: inventario de familias, paleta por zona, focos hero, reglas de repetición, carencias por rol.
Comprobaciones automáticas: IDs duplicados, zonas sin foco, materiales no declarados, paletas sin contraste de propósito, claves huérfanas.
Inspección humana: belleza, naturalidad, historia ambiental, legibilidad del riesgo.

### B. Asset Role Registry 2.0

**Responsabilidad:** unir procedencia (Asset Vault / Public Asset / Model Forge) con **función visual**, costo y restricciones de placement.

Estados: `planned`, `inspected`, `staged`, `approved`, `rejected`; nunca inferir `approved` de un nombre o de una URL.
Roles: `hero`, `structure`, `functional`, `clutter`, `fixture`, `signage`, `atmospheric`.
Integridad: licencia, uso comercial, cadena de dependencias, hash, polígonos/triángulos, superficies, resoluciones, memoria estimada/medida, instancias, bounding box, colisión permitida/no permitida.
No duplicar download: usar adaptadores existentes y política de `project.intent.json`. Sin permiso de red, sólo indexar assets locales ya disponibles.

### C. Environment Layering

Capas separadas:
1. `gameplay-semantic`: mapa/colisión/rutas, únicamente propiedad del juego.
2. `structure`: paredes/columnas/pasarelas decorativas.
3. `functional-props`: dispositivos y maquinaria.
4. `dressing`: cables, residuos, tornillos, decals con presupuesto.
5. `signage`: señalización y jerarquía de objetivos.
6. `atmosphere`: partículas/emisión/efectos sujetos al renderer.

Reglas: referencias a anclas semánticas, no geometría de combate duplicada; arte nunca debe tapar retícula, enemigos u objetivos en shots mínimos. Toda modificación del gameplay requeriría un contrato de juego separado.

### D. Lighting Intent Profiles

Cada zona define: rol narrativo, esquema cromático, prioridad del foco, luz principal/relleno, luces prácticas, sombras necesarias, material respuesta, alerta y fallback.

El auditor informa **intención frente a implementación**: sombras activas, número de Omni/Spot/Directional, rangos, energía, superposición y si el renderer admite el efecto pretendido. La compatibilidad de Godot `gl_compatibility` impone perfiles de calidad separados; no usar Forward+ como supuesto universal.
No definir "más luces = mejor"; usar intención, contraste y coste medido.

### E. Visual Evidence Comparison

Evidencia: PNG original, SHA-256, escena/commit, Godot/renderer, cámara y transform, viewport, FOV, estado de misión, perfiles de luz, tiempo/frame semilla y hash de settings.
Gates: mismo frame de referencia o estado reproducible, mismas ROI, captura no retocada, imágenes no duplicadas, tamaños correctos, índice visible de cada zona.
Métricas **de soporte**: diferencias estructurales por ROI, rango de luminancia/negros sobreexpuestos, fracción de pantalla ocupada por héroe/objetivo, frecuencia de assets repetidos desde el inventario, hotspots de frame time si se dispone de profiler.
**Nunca** traducir automáticamente esas cifras a "calidad AAA" ni tratar diferencia de píxeles como mejora estética. Un cambio puede ser visible y objetivamente peor.

### F. Android Visual Budget Gate

Contrato de costes para renderer/dispositivo/perfil:
- Estáticos: número de luces que afectan el área, shadow casters, draws/instancias (si motor puede exponerlos), triángulos, materiales, texturas y tamaños.
- Dinámicos: tiempos CPU/GPU, p50/p95/p99 frame duration, memoria residente, ralentización térmica y batería sólo si medidos.
- Comparabilidad: versión Godot, backend, resolution scale, refresh rate, escena, dispositivo, duración, build, warmup y modo de energía.
- Presupuestos: valores por proyecto y dispositivo objetivo; fallback explícito 30 fps si 60 es inalcanzable, nunca rebajar silently.
- Resultado: `pass` / `fail` / `needs_measurement` / `incomparable`.

**Política:** el export APK y CI render de Linux no cuentan como certificación de fps, temperatura o suavidad en Android.

## 6. Calidad: gates para promover una escena

| Gate | Criterio objetivo | Evidencia | Rechazo |
|---|---|---|---|
| G0 Intent | JSON Schema 2020-12 + referencias cruzadas | fixture y parse | zona/perfil duplicados, referencia rota |
| G1 Rights | asset provenance + commercial policy | records SHA y licencia | blob sin licencia, hash falso |
| G2 Semantic | mapa/collision/nav invariantes | diff semántico, tests Godot | visual cambió física |
| G3 Rendering | engine import, shader/material compatible | salida Godot con commit | parse, material missing |
| G4 Capture | before/after con misma cámara/ROI | PNG y metadatos HASH | capturas no comparables |
| G5 Visual Review | revisión humana documentada | decisiones/observaciones | contraste, layout, señales fallidas |
| G6 Mobile | perfil real sostenido Android | traces y plan preinscrito | framerate/thermal fuera de presupuesto |

Un gate sin datos `needs_measurement` **no pasa**. G5 no puede automatizarse fingiendo juicio artístico; G6 no puede derivarse de estimaciones de polígonos.

## 7. Política de seguridad y control

- ARCONT sólo lectura por defecto; cualquier inicio de Godot que cambie cache es operación controlada con opt-in conforme al sistema 1.1.
- Las escrituras se realizan únicamente en un repositorio/directorio externo autorizado, con revisión SHA, staging, validación y rollback o rechazo; nunca dentro del repositorio ARCONT.
- Usar `development.session.control` para plan de una ejecución, límite de pasos, lock, recibo, recheck y cero reintentos automáticos ante ambigüedad o crash.
- Asset Discovery sólo Poly Haven hasta que nuevos adaptadores y políticas se aprueben; no permitir URL arbitraria o descarga/archivo no admitido. Derechos de uso y derechos de redistribución se auditan independientemente.
- No generar shaders/scripts `@tool` arbitrarios; el plan visual no amplía las capacidades del editor estructurado existente.
- Fases de autoaplicación: ninguna en la propuesta; aprobarse en PR externo luego de evidencia y revisión humana.
- Evidencias preservan versión, contexto, límites y nivel de madurez, siguiendo L0–L7.

## 8. Plan de implementación, dependencias y criterios de salida

**P0 — Contrato y adopción documental (sin ejecución):**
- Publicar ADR, schema Draft 2020-12, fixture neutral y políticas de aceptación.
- Incorporar validador estático independiente con pruebas negativas: IDs duplicados, referencias rotas, `renderer` incompatible, ruta que escapa del proyecto, asset `staged` sin provenance.
- Aceptación: fixtures buenas válidas y todas las negativas rechazadas; sin modificar manifest/version.

**P1 — Inspección sin escritura:**
- Reutilizar registros de asset, Map Forge, scene inspección y herramientas Production/Model Forge; producir normalización de roles/layers/lights.
- Salida JSON reproducible con hashes y warnings. No shell arbitrario.
- Aceptación: lectura de FISURA por commit fijo sin editar un archivo del juego; contrato portable contra otra fixture sintética.

**P2 — Evidencia visual:**
- Capturas equivalentes y diferencia por ROI; comparar versiones registrando variables de captura.
- Exigir falla ante FOV/resolución/commit/renderer distintos; aceptar una regresión reproducible cuando están emparejados.
- Integrar mediciones reales sólo mediante el pipeline de observabilidad existente, sin equivalencia asumida entre GPU profilers.

**P3 — Orquestación opt-in y experimento externo:**
- Un adaptador en FISURA convierte intención visual revisada en operación limitada sobre archivos del juego con `if_revision`.
- Ejecutar pruebas antiguas de misión, navegación, coberturas, Godot/Android, capturas y mobile profiling.
- Comparar al menos dos variantes de un solo sector (p. ej. Nodo A) antes de decorar toda la misión.
- Resultado: un PR de FISURA documentado, no un merge automático.

**P4 — Promoción de ARCONT 1.2:**
- Proponer `arcont_version=1.2.0` **sólo** después de que operaciones, schemas, documentación, tests negativos/positivos, CI, compatibilidad bridge/MCP y política estén integrados y auditados.
- No inferir L5 cross-hardware sin dos dispositivos reales relevantes; no llamar al producto terminado por aprobar integridad de PNG.

## 9. Pruebas de aceptación obligatorias

1. Contrato visual válido pasa; campos inesperados, IDs y tipos incorrectos fallan.
2. Mapa no coincide con región: falla verificablemente antes de cualquier staging.
3. Asset sin licencia o SHA incorrecto: se bloquea, aun si su mesh se importa.
4. Proyecto con descubrimiento por red deshabilitado: nunca consulta proveedor.
5. Sin project-write: operaciones de inspección seguras; `visual.plan.stage` denegada.
6. Revisión de archivo discordante, sesión obsoleta o dos escritores: staging rechaza sin pérdida de cambios.
7. Render/captura con distintas poses o FOV: `incomparable`, no "mejor".
8. Smoke Godot que pasa mientras la geometría decorativa ocluye cámara: debe detectarse en auditoría de composición o marcarse para revisión humana.
9. Sin perfiles físicos Android: presupuesto de runtime `needs_measurement`.
10. Trace Android comparable + fallos de thermal/frame pacing: no promover visual pass a release.
11. Sin modificar navegación/colisión: hashes / contratos del mapa y tests existentes quedan intactos.
12. Arte visual que no mejora según revisión humana: se rechaza aunque todas las métricas de diferencias indiquen cambio.

## 10. Integración FISURA 0.9.3 sin invadir ARCONT

Repositorio consumidor: `heliossamuelhernandezreyes/Godot-juegos-3d.-` (rama PR de juego).
Fase piloto: Nodo A / Reactivo-13.
Cambios propuestos en FISURA: archivo `visual.intent.json`, escena/art scripts propios, referencias de assets aprobados y capturas con contrato de cámara; **ninguno** se almacena como runtime dentro de ARCONT.

Baselines: revisión de FISURA 0.9.2 y sus seis screenshots auténticas, cámara/colliders de la misma revisión, Godot 4.7.2 Compatibility, assets CC0 con provenance existente.

Meta estética a evaluar humanamente: una sección de Nodo A con lectura inmediata de objetivo, un foco industrial reconocible, materiales de desgaste coherentes, separación de planos y sombras selectivas. Meta técnica: no alterar física/misión y cuantificar sobrecosto real en Android.

**No activar automáticamente `allow_network_discovery` del proyecto**: si no se autoriza, continuar con el inventario local y presentar faltantes.

## 11. Riesgos, decisiones y requisitos de implementación futura

| Riesgo | Mitigación |
|---|---|
| Métricas superficiales premian colores saturados | Separar métricas físicas, comparabilidad y aprobación artística humana |
| "Arquitectura visual" se vuelve segundo Map Forge | Mapa semántico con ID y hashes únicos; no crear rutas/colisiones paralelas |
| Reutilizar un asset incorrectamente licenciado | Trazar provenance y políticas por instancia antes de staging |
| Compatibilidad gráfica | Perfil renderer explícito, estados `unsupported` y fallback |
| Degradar Android por adornos | presupuesto por sector, variante degradada y pruebas sostenidas |
| Sesión/agente sobreescribe trabajo humano | if_revision + permisos + lock/recibo del stack 1.1 |
| Distintos screenshots parecen "antes/después" | pose exacta y metadata + rechazo de comparaciones ambiguas |
| Confundir documentos con herramientas operativas | versionar proposal vs implemented y mantener manifest 1.1 hasta superar gates |

## 12. Entregables de este PR de diseño

- Este blueprint normativo como **propuesta revisable**.
- Schema inicial `schemas/proposals/visual-production-intent.schema.json`.
- Ejemplo neutral `templates/visual-production/industrial_arena.example.json`.
- No se cambia `main`, `arcont.manifest.json`, `agent.capabilities.json`, el Bridge, herramientas runtime ni los juegos.

### Criterio para aceptar el blueprint

Que sea implementable por otro desarrollador sin adivinar responsabilidades, que los contratos marquen claramente autoridad/seguridad/comparabilidad y que todas las afirmaciones distingan **planteado**, **probado en Linux**, **medido en Android** y **aprobado por humano**.

**Conclusión:** ARCONT 1.2 debe ser un orquestador de intención visual y evidencia reproducible, no un generador autónomo de "calidad AAA".
