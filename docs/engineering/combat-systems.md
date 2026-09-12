# Sistemas de combate — conocimiento extraído de ARCONT

El prototipo exploró armas de fuego, recarga activa, feedback de impacto, ADS en tercera persona, movilidad táctica, melee direccional, enemigos con personalidades y ataques telegrafiados.

## Patrones valiosos

### Separar lógica y presentación

La lógica de arma no debería depender directamente de la animación concreta. Exponer eventos permite que distintas presentaciones consuman el mismo estado.

### Ataques telegrafiados

Los ataques peligrosos funcionan mejor cuando comunican intención mediante pose, dirección, tiempo y sonido antes del impacto. Esto mejora legibilidad sin reducir dificultad.

### Personalidad enemiga

Variaciones de comportamiento son más interesantes que simples cambios de vida o daño. Ritmo, distancia preferida, fintas, pasos laterales y agresividad pueden producir enemigos reconocibles.

### Feedback sincronizado

Disparo, retroceso, luz, sonido, hit marker, animación mecánica y respuesta del enemigo deben compartir un mismo evento lógico para evitar desincronización.

## Regla reusable

Construir combate alrededor de estados y eventos explícitos; después conectar animación, audio, cámara, UI y VFX como consumidores de esos estados.
