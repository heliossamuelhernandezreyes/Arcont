# ARCONT 1.1 — Integración y fiabilidad

Esta revisión reúne la base de conocimiento de `main` y las capacidades del
gateway MCP, y corrige los casos reproducidos en la auditoría del 8 de octubre
de 2026. ARCONT sigue siendo un laboratorio: los proyectos, assets entregados
y ejecuciones de Godot pertenecen a repositorios externos.

## Preparación y verificación

Desde la raíz de ARCONT, con Python 3.12 y Node 24:

```sh
npm ci --prefix integrations/mcp --ignore-scripts --no-audit --no-fund
python tools/arcont_agent.py doctor --timeout 60
python -m unittest discover -s tests
```

El gateway conserva su autorización explícita de escritura sobre proyectos
externos. Instalar dependencias no concede esa autorización. `doctor` revisa
documentos propios y excluye dependencias, cachés y salidas generadas.

Para validación de modelos en Linux x86_64:

```sh
python tools/install_processors.py --destination /tmp/arcont-processors
export ARCONT_PROCESSOR_DIR=/tmp/arcont-processors
```

El instalador comprueba los hashes del archivo descargado y del ejecutable
contra [`processors.lock.json`](../processors.lock.json). Cada ejecución vuelve
a comprobar la identidad del procesador. Otras plataformas necesitan un lock
revisado; no se selecciona silenciosamente otro binario disponible en `PATH`.

La aceptación nativa requiere el Godot oficial 4.7.2 del pin canónico, con
`GODOT_BIN` apuntando al ejecutable:

```sh
python tests/reliability_live_acceptance.py \
  --project /tmp/arcont-reliability-game \
  --evidence /tmp/arcont-reliability-evidence
```

La carpeta de proyecto debe ser nueva o estar vacía. CI instala las herramientas
fijadas, comprueba Godot por SHA-256 y conserva los receipts como artefactos.

## Cambios frente a la auditoría

| Hallazgo | Comportamiento en 1.1 | Límite de la garantía |
| --- | --- | --- |
| ARC-AUD-01: ramas divergentes | Integración de la base de conocimiento y el gateway en una sola rama de entrega. | La disponibilidad en `main` depende de integrar esta revisión. |
| ARC-AUD-02: carrera entre escritores | Bloqueo entre procesos durante la comprobación final y publicación de scripts, escenas, recursos e input. | Protege escritores ARCONT cooperantes; un editor externo no adquiere ese bloqueo. |
| ARC-AUD-03: dependencias glTF perdidas | Copia transaccional de modelo, buffers e imágenes, con hashes antes y después. | Se rechazan dependencias ausentes, rutas no locales y colisiones de nombres. |
| ARC-AUD-04: presupuesto geométrico | Cuenta listas, strips y fans; valida índices de accessors, modos y conteos. | Los degenerados se cuentan conservadoramente; el coste de instancias se informa aparte. |
| ARC-AUD-05: benchmarks inválidos | Rechaza NaN, infinito, booleanos numéricos, duraciones negativas y estructuras incorrectas. | La validez estructural no acredita una medición real. |
| ARC-AUD-06: reglas sin trazabilidad | Comprueba ciclos de derivación, dependencias invalidadas, evidencia enlazada y madurez declarada del grafo tipado. | No interpreta afirmaciones arbitrarias en prosa ni verifica automáticamente experimentos remotos. |
| ARC-AUD-07: doctor tras npm | Excluye directorios de dependencias y prueba `doctor` después de `npm ci`. | Sigue comprobando enlaces rotos de documentos propios. |
| ARC-AUD-08: taxonomía incorrecta | Migra 2.384 fichas Poly Haven y comparte la taxonomía con el descubrimiento público. | Una ficha catalogada no equivale a un asset probado. |
| ARC-AUD-09: PNG incompleto o repetido | Comprueba CRC, chunks, descompresión, scanlines y filtros; compara píxeles normalizados. | Acepta PNG RGB/RGBA de 8 bits sin entrelazado; diferencias de píxeles no demuestran composición correcta. |
| ARC-AUD-10: alias de licencias | Normalización común; una prohibición CC0 también cubre CC0-1.0 y viceversa. | Los nombres desconocidos no se adivinan por coincidencia parcial. |
| ARC-AUD-11: alcance global | El reemplazo de función rechaza declaraciones globales adicionales y preserva bytes externos, incluidos CRLF. | Es una operación acotada; no es un parser general ni un sandbox completo de GDScript. |
| ARC-AUD-12: contrato de mapas | Valida tipos, coordenadas, radios, límites y estructuras opcionales; alinea el equipo neutral `null`. | No acredita navegabilidad ni calidad espacial por sí solo. |
| ARC-AUD-13: confianza sin resolver | Diferencia evidencia declarada, archivo local resuelto y bytes verificados por hash. | Las referencias HTTPS y ARC se mantienen declaradas en auditorías sin acceso remoto. |
| ARC-AUD-14: comparabilidad | Exige controles, motor, VSync y duraciones compatibles; lee estadísticas anidadas y detecta unidades distintas. | Los ejes que cambian se declaran con `--vary`; no convierte unidades automáticamente. |
| ARC-AUD-15: impacto incompleto | Añade relaciones de navegación, cámara, animación e importación; expone documentos cubiertos y ausentes. | El grafo sigue siendo parcial: ausencia de impacto no significa ausencia de riesgo. |
| ARC-AUD-16: procesadores variables | Versiones, hashes, entradas completas y receipts fijados; gate Khronos obligatorio para entrega validada. | Validar glTF y presupuesto no sustituye importar y probar en el motor objetivo. |

## Entrega de modelos

`model_forge_control` distingue `delivery_mode: "candidate"` de
`delivery_mode: "validated"`. Por compatibilidad, el control conserva candidate
como valor por defecto y lo marca `not-certified`. La CLI de staging exige
validación por defecto y permite `--candidate` explícito.

La entrega validada requiere un perfil con budgets, valida el bundle completo
con Khronos y publica un manifiesto con `delivery_status:
"spec-and-budget-validated"`. `runtime_evidence_required` permanece en `true`.
Un strip de 1.002 vértices consume 1.000 triángulos del presupuesto.

`gltfpack` se ejecuta con `-noq` y sin compresión meshopt por defecto: la
aceptación nativa detectó que el motor fijado no importaba el resultado con
`KHR_mesh_quantization`, aunque pasara la especificación glTF. Los formatos de
entrada del procesador son glTF/GLB; OBJ y DCC requieren una conversión separada
con dependencias y procedencia revisadas.

## Evidencia y siguientes umbrales

La verificación registrada en
[`reliability/2026-10-08.json`](reliability/2026-10-08.json) incluye pruebas
unitarias, aceptación del gateway, edición, sesiones y regresiones nativas.
Las regresiones nativas comprueban dos escritores simultáneos sobre cuatro
superficies y la reapertura real de modelos: 1, 1.000 y 1 triángulos.

Esta evidencia corresponde a Linux headless. No acredita rendimiento en un
Android físico, calidad artística, legibilidad de una misión, ni compatibilidad
universal de los 4.643 registros del catálogo. Para elevar esas afirmaciones
hacen falta campañas externas con hardware, escenas, capturas y mediciones
identificables; se conservan separadas de la aceptación de las herramientas.
