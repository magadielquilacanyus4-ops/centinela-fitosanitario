---
description: Ponerse al día con el estado del proyecto antes de trabajar
argument-hint: [tema o tarea de esta sesión]
---

Antes de hacer cualquier cambio, sincroniza el contexto del proyecto:

1. Lee `CLAUDE.md` y `CLAUDE.local.md` (este último trae la ruta de la carpeta de documentación).
2. En la carpeta de documentación lee `Estado del proyecto.md` y las 2 notas más recientes de `Sesiones/`.
3. Corre `git status -sb` y `git log --oneline -5` en el repo.
4. Resume en máximo 8 líneas: dónde estamos, qué hay en curso (y en qué consola), qué sigue y qué bloqueos hay.
5. Tema de esta sesión: $ARGUMENTS. Si viene vacío, pregunta en qué se va a trabajar.
6. Registra la sesión en la sección "En curso" de `Estado del proyecto.md` (fecha, tema y archivos que vas a tocar) usando Edit con un cambio puntual.

No empieces a programar hasta haber hecho los pasos 1 a 6.
