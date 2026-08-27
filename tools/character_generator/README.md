# Arcont Character Generator

Generador procedural de humanoides low-poly y modulares para **Arcont**.

La intención no es reemplazar Nomad Sculpt: genera un **maniquí limpio y editable**, con las piezas corporales separadas desde el origen para facilitar rigging, ropa y gore modular.

## Salida

El generador produce un archivo `.obj` con objetos independientes:

- `head`
- `neck`
- `torso`
- `pelvis`
- `upper_arm_L` / `upper_arm_R`
- `forearm_L` / `forearm_R`
- `hand_L` / `hand_R`
- `thigh_L` / `thigh_R`
- `shin_L` / `shin_R`
- `foot_L` / `foot_R`

El personaje se genera en **T-pose** y a escala aproximada en metros.

## Presupuesto geométrico

La configuración inicial apunta a un personaje final de unas **2.500 caras quad**. El maniquí base utiliza alrededor de **1.400 quads**, dejando aproximadamente 1.100 para:

- cara y rasgos;
- cabello;
- ropa;
- calzado;
- equipo;
- superficies de corte/gore;
- detalles de silueta.

Esto es intencional: el presupuesto debe gastarse donde se vea, no en geometría invisible del cuerpo base.

## Generar

Desde la raíz del repositorio:

```bash
python tools/character_generator/generate_character.py
```

No necesita paquetes externos.

El resultado aparecerá en:

```text
tools/character_generator/output/arcont_survivor_base.obj
```

## Personalizar

Edita `character_config.json` antes de ejecutar el generador. Los parámetros principales son:

- `height_m`: altura total aproximada;
- `shoulder_width`: anchura de hombros;
- `waist_width`: cintura;
- longitudes y radios de brazos/piernas;
- `radial_segments`: resolución alrededor de cada extremidad;
- `cut_gap_m`: pequeño espacio entre módulos pensado para puntos de separación.

## Flujo móvil recomendado

```text
GitHub / Replit
      ↓
generate_character.py
      ↓
OBJ modular
      ↓
Nomad Sculpt
      ↓
retoques + ropa + pintura
      ↓
GLB
      ↓
Godot / Arcont
```

## Regla de diseño

No fusionar las extremidades durante el blockout inicial. Cabeza, brazos, antebrazos, muslos y pantorrillas deben poder seguir tratándose como módulos independientes hasta que quede decidido el sistema final de gore.
