# ARCONT Benchmark Standard v1

Los benchmarks de ARCONT buscan comparar decisiones técnicas de forma útil para producción, especialmente en hardware móvil.

## Reglas

- Medir en hardware real siempre que la pregunta dependa del dispositivo.
- Registrar versión exacta del motor y commit.
- Separar cold start, warm-up y ventana de medición.
- Ejecutar varias corridas y conservar dispersión, no solo un promedio.
- No comparar resultados obtenidos con resolución, renderer o presets diferentes sin indicarlo explícitamente.
- Registrar temperatura y throttling cuando el test dure lo suficiente para afectar rendimiento.

## Perfil mínimo del dispositivo

```yaml
device:
  model:
  soc:
  cpu:
  gpu:
  ram_gb:
  os:
  display_resolution:
  refresh_rate_hz:
```

## Perfil mínimo del motor

```yaml
engine:
  name: Godot
  version: 4.7.2-stable
  commit: ed1daf0bf001b61586d9930840f2f1394092c079
  renderer:
  build_type:
```

## Resultado recomendado

```yaml
workload:
  name:
  count:
  duration_seconds:
  warmup_seconds:
  repetitions:

results:
  fps_mean:
  fps_1pct_low:
  frame_time_mean_ms:
  frame_time_p95_ms:
  frame_time_p99_ms:
  cpu_frame_ms:
  gpu_frame_ms:
  ram_mb:
  draw_calls:
  load_time_ms:

thermal:
  start_c:
  end_c:
  throttling:
```

## Escalamiento

Cuando tenga sentido, las pruebas deben usar escalones de carga para encontrar la curva de degradación y no solo un punto aislado. Ejemplos: 100, 1 000, 10 000, 50 000 y 100 000 instancias; o 10, 50, 100, 250, 500 y 1 000 cuerpos físicos.

## Comparabilidad

Cada resultado debe declarar si es:

- comparable directamente;
- comparable con reservas;
- no comparable.

La razón debe quedar escrita.

## Objetivo

El benchmark no busca producir una cifra bonita. Busca encontrar umbrales, cuellos de botella, relaciones coste/beneficio y límites prácticos reutilizables.