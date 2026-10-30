# ARCONT 1.2 - correcciones y migración

Esta revisión responde a los trece hallazgos de la auditoría sobre
`667f59067573d019406df383f48cc9dd98141083`. La aceptación indicada se ejecuta
en Linux. Arcont sigue siendo un laboratorio para proyectos externos.

| Hallazgo | Corrección | Regresión |
| --- | --- | --- |
| ARC-2026-01 | Rechazo de campos reservados, argumentos cerrados y permiso antes del despacho | Matriz de alias y escritores; MCP stdio y HTTP sobre un proyecto inicializado |
| ARC-2026-02 | Supervisores con deadline heredado, grupos, subreaper y cancelación al morir el padre en Linux | El adaptador no escribe después de devolver timeout |
| ARC-2026-03 | Estado lógico/físico en una generación inmutable y publicación de una sola referencia | Caída antes/después de publicar; el siguiente escritor obtiene el bloqueo |
| ARC-2026-04 | Criterios tipados fijados al crear la sesión y reevaluados sobre petición y respuesta efectivas | Inventario no satisface runtime; resultado falso o documento incorrecto no pasan |
| ARC-2026-05 | Pin de helpers, esquemas, plantillas, gateway, locks, ejecutables y adaptadores | Cambiar un helper importado o adaptador cambia la identidad |
| ARC-2026-06 | Validación aislada con ruta final y registro de clases nuevo | Crear, importar y reemplazar class_name; un cambio inválido conserva bytes |
| ARC-2026-07 | Lector PNG estricto y acotado compartido | CRC, IEND y datos sobrantes rechazados por los tres consumidores |
| ARC-2026-08 | Ejecutabilidad, versión/commit y SHA-256 Linux de Godot | Archivo de texto rechazado; alcance de validación declarado |
| ARC-2026-09 | Contención, rechazo de symlinks y lecturas acotadas por descriptores POSIX | Intención y ancestros de authoring externos rechazados |
| ARC-2026-10 | Disponible distingue herramienta instalada de referencia externa | Runtime sin ejecutor no anuncia available=true |
| ARC-2026-11 | Validador CLI exige assets y datos numéricos válidos | Informes vacíos/mal formados y booleanos numéricos rechazados |
| ARC-2026-12 | Aceptación nativa en push a main para cambios relevantes; retención de 90 días | Workflows y recibos identificados por revisión |
| ARC-2026-13 | Matriz actualizada y verificador local en doctor | Implementación y definiciones de pruebas enlazadas por hash |

## Preparación

```bash
npm ci --prefix integrations/mcp --ignore-scripts --no-audit --no-fund
python tools/arcont_agent.py doctor --timeout 60
python -m unittest discover -s tests -v
GODOT_BIN=/ruta/godot python -m unittest tests.test_audit_hardening -v
```

## Migración de Map Forge

La API mantiene `state: {map, physical}`. Cada commit guarda el estado completo
en `.mapforge/history/<id>/<revision>.json` y publica una referencia atómica en
`.mapforge/heads/<id>.json`. Editor.read, list, inspect y los adaptadores usan
esa generación completa, cuyo digest se comprueba al leer.

Los archivos antiguos de maps y maps/physical se leen mientras no exista una
referencia nueva; su estado se informa como `legacy-unverified`. La primera
escritura publica el formato v2. **Los archivos antiguos se conservan y dejan
de actualizarse.** Un consumidor que los abra directamente debe pasar a la API
o al estado que recibe el adaptador. No se deben mezclar escritores v1 y v2.

Una caída antes del cambio de referencia conserva la generación anterior;
después se ve la nueva completa. La garantía es publicación atómica del espacio
de nombres; no certifica durabilidad física frente a un corte eléctrico.

## Migración de criterios de aceptación

El texto antiguo se puede inspeccionar, pero no completar automáticamente. Es
necesaria una sesión nueva con criterios explícitos, por ejemplo:

```json
{
  "description": "La prueba de combate termina correctamente.",
  "verification_level": "runtime",
  "checks": [{
    "kind": "invoke",
    "capability": "godot.authoring.control",
    "operation": "playtest",
    "request_match": {"document_id": "combat"},
    "expect": [{"pointer": "/result/passed", "op": "equals", "value": true}]
  }]
}
```

Runtime solo admite playtest con passed=true. Static declara los predicados de
una inspección u operación concreta. La descripción es presentación: el nivel
y los predicados expresan exactamente lo demostrado. Cada comprobación debe
quedar cubierta por un paso del mismo plan; todos los pasos citados deben ser
pertinentes. Una edición no se convierte en evidencia de combate por el texto
de su descripción. Los ejemplos y suites nativas usan el contrato tipado.

## Identidad y cancelación

Las sesiones antiguas sin pin de adaptador no ejecutan planes nuevos. Cambiar
una dependencia incluida exige una sesión revisada nueva. El pin conserva los
archivos de Arcont, locks, Python, Godot y configuración/scripts del adaptador.
No certifica todos los paquetes externos que un adaptador pudiera importar:
esos entornos siguen necesitando fijación y revisión del proyecto.

En Linux los supervisores adoptan descendientes huérfanos y se cancelan si muere
su padre. El deadline exterior se propaga. Terminación confirmada y estado
indeterminado son resultados diferentes. La cobertura de descendientes
desligados en otros sistemas no se acredita en esta revisión.

## Límites

- GDScript y adaptadores siguen siendo código confiado, sin sandbox completo.
- La copia aislada para class_name tiene un presupuesto de 512 MiB. Proyectos
  mayores requieren un adaptador de validación revisado.
- Verificar el motor no importa el proyecto; la respuesta lo declara. Las
  suites de aceptación realizan la importación y ejecución reales.
- El verificador de matriz comprueba archivos y definiciones de tests locales;
  no infiere que se hayan ejecutado ni valida referencias remotas.
- Linux headless no acredita FPS sostenidos, temperatura, tacto o calidad
  artística en Android. El siguiente umbral es un consumidor completo y una
  campaña de juego en hardware identificado.
