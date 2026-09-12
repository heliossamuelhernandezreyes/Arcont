# ARCONT Asset Vault

ARCONT mantiene un catálogo trazable de recursos reutilizables para prototipos y producción 2D, 2.5D y 3D. El objetivo no es copiar Internet ni inflar el repositorio con binarios: es saber qué existe, bajo qué licencia, dónde obtenerlo y para qué sirve.

## Cobertura

- 2D: sprites, tilesets, backgrounds, icons, UI, fonts, VFX, decals.
- 2.5D: sprites/planes en 3D, isométrico, billboards, híbridos 2D/3D.
- 3D: characters, creatures, props, environments, buildings, vehicles, vegetation, modular kits.
- Materials: PBR textures, atlases, trim sheets, decals, HDRIs.
- Animation: humanoid/non-humanoid rigs, locomotion, combat, interactions.
- Audio: SFX, ambience, Foley, UI, impacts, vehicles, creatures, music when licensing permits.
- Technical: shaders, VFX, prototype primitives, debug/UI assets.

## Indexador automático

La herramienta canónica es `tools/asset_vault_indexer.py`.

Flujo:

`SOURCE -> ADAPTER/MANIFEST -> NORMALIZED RECORD -> VALIDATION -> DEDUPLICATION -> INDEX -> QUERY`

Capacidades actuales:

- sincronización real de metadatos desde la API pública de Poly Haven;
- ingesta de manifiestos JSON verificados para proveedores sin API estable;
- validación del contrato de cada asset;
- rechazo de mirroring cuando la licencia no permite redistribución;
- deduplicación por ID de ARCONT, identidad externa del proveedor y SHA-256 de binarios archivados;
- generación de `assets/index.json`;
- consultas por texto, tipo, uso comercial, atribución y compatibilidad Android;
- pruebas automáticas y controles negativos en CI.

Especificación completa: [`INDEXER_SPEC.md`](INDEXER_SPEC.md).

Contrato formal: [`../../schemas/asset-record.schema.json`](../../schemas/asset-record.schema.json).

Catálogo normalizado: [`../../assets/catalog/`](../../assets/catalog/).

## Política de almacenamiento

1. CC0/public-domain assets are preferred for maximum reuse.
2. Assets with attribution/share-alike/custom licenses may be catalogued but their obligations must remain explicit.
3. Restricted assets may be referenced but MUST NOT be mirrored into ARCONT unless redistribution is explicitly allowed.
4. Large binaries stay upstream by default. ARCONT stores metadata, source URL, license evidence, tags, optional preview, hashes for locally archived legal copies, and compatibility notes.
5. Never infer a license from the host site alone when licensing is per asset.
6. License/version at acquisition time is recorded because terms can change.
7. "Free" is not equivalent to "redistributable".

## Preferred source tiers

### Tier A — broad reuse / archive-friendly
- Kenney asset pages: CC0 according to Kenney support documentation.
- Poly Haven assets: CC0 for HDRIs, textures and 3D models.
- Explicit CC0/public-domain individual assets from other repositories.

### Tier B — usable but redistribution must be checked
- Quaternius: current QAL permits free commercial use/modification but prohibits redistribution of the assets themselves; older/individual pages may identify CC0, so record the exact asset/license version.
- Sonniss GameAudioGDC: royalty-free commercial media use, but redistribution as an asset library is prohibited; reference upstream rather than mirror.
- SIL OFL fonts: bundling/use is broad but license/copyright files and Reserved Font Name conditions must be preserved as applicable.

### Tier C — per-asset licensing
- OpenGameArt: multiple free/open licenses; inspect each submission.
- Freesound: CC0, CC-BY and CC-BY-NC coexist; only ingest/reference according to the exact sound license and project requirements.

## Query contract

Un proyecto puede consultar conceptualmente:

`dimension=3d theme=forest style=low_poly platform=android commercial=true attribution=false engine=godot`

La CLI ya soporta una primera versión práctica:

```bash
python tools/asset_vault_indexer.py build
python tools/asset_vault_indexer.py query "forest low poly" --commercial --no-attribution --android
```

El resultado solo contiene candidatos que cumplen los filtros machine-readable disponibles; campos desconocidos permanecen `null` y no se adivinan.

## Safety rails

ARCONT does not claim ownership of third-party assets. It preserves author/source/license provenance. A catalog entry is not legal advice and does not override the original license. If source and cached metadata conflict, stop automatic reuse until reviewed.
