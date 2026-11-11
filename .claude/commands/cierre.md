---
description: Cerrar la sesión, dejando bitácora y estado actualizados para las demás consolas
argument-hint: [tema de la sesión]
---

Deja todo listo para que otra consola (o el usuario) retome sin perder contexto:

1. Revisa qué cambió: `git status -sb` y `git diff --stat`.
2. Crea la nota `Sesiones/AAAA-MM-DD - <tema>.md` en la carpeta de documentación, con:
   frontmatter (`type: sesion`, `date`, `tags: [hackaton, nasa]`), y secciones **Qué se hizo**, **Decisiones**,
   **Archivos tocados**, **Pendiente / siguiente paso** y **Bloqueos**. Enlázala a `[[Estado del proyecto]]`.
3. Actualiza `Estado del proyecto.md` con Edit puntual: saca tu sesión de "En curso", ajusta "Próximos pasos",
   agrega las decisiones a la bitácora de Decisiones y los bloqueos que hayan aparecido.
4. Si una tarjeta de `Tareas/` cambió de situación, actualiza su campo `estado`.
5. Si cambió el alcance o la idea, actualiza `Idea y alcance - Centinela Fitosanitario.md`.
6. Muestra al usuario un resumen de 3 líneas y pregunta si quiere hacer commit. No hagas push.

Tema: $ARGUMENTS
