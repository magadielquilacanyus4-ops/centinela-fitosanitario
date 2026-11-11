# CLAUDE.md — Centinela Fitosanitario

Herramienta de apoyo a la decisión para huertos de cerezo y manzano en la Región de O'Higgins (Chile).
Cruza **riesgo de infección × viabilidad de aplicación** con observaciones de la Tierra de la NASA.

**NASA Space Apps Challenge 2026** — desafío definitivo: *"Conviértete en un detective de tendencias del sistema terrestre"*.
El desafío pide responder: **qué cambia, dónde, cuánto y si el cambio es significativo**.
(El desafío "Field Shift / Cambio de rumbo" fue descartado: exige rotación de cultivos, que no aplica a frutales perennes.)

Hackatón: 14–15 de noviembre de 2026. Entrega con un día de margen (14-nov).

## Dónde vive cada cosa

| Qué | Dónde |
|---|---|
| Código, README técnico, entorno | **Este repo** (fuente de verdad del código) |
| Estado, idea y alcance, Kanban, papers, notas de sesión | **Carpeta del proyecto en la bóveda de Obsidian** (privada, fuera del repo) |

La ruta local de esa carpeta está en `CLAUDE.local.md` (no se sube a GitHub).
Si el archivo no existe, pídele la ruta al usuario antes de seguir.

Contenido de la carpeta de documentación:
- `Estado del proyecto.md` — **tablero compartido**: qué está hecho, qué sigue, decisiones, bloqueos.
- `Idea y alcance - Centinela Fitosanitario.md` — idea, alcance, datos, riesgos de validez.
- `Tareas/` — tarjetas del Kanban (campo `estado`: Por hacer / En curso / Revisión / Hecho).
- `Sesiones/` — una nota por sesión de trabajo (bitácora).
- `investigacion/` — papers y material de referencia.

## Protocolo de trabajo (obligatorio, hay varias consolas en paralelo)

**Al empezar:** ejecuta `/inicio` (o, a mano: lee `Estado del proyecto.md` y las 2 últimas notas de `Sesiones/`).
**Al terminar:** ejecuta `/cierre` (nota de sesión + actualizar estado).

Reglas para no pisarse entre consolas:
1. Cada consola escribe **solo su propia nota** en `Sesiones/`. Nunca edites la nota de otra sesión.
2. En `Estado del proyecto.md` usa **Edit con cambios puntuales**. No reescribas el archivo completo.
3. Antes de tocar un archivo de código, mira en "En curso" de `Estado del proyecto.md` si otra consola lo está usando.
4. Commits y push **solo cuando el usuario lo pida**. Mensajes de commit en español.
5. Si cambia el alcance o una decisión, anótalo en `Estado del proyecto.md` (sección Decisiones) con fecha.

## Convenciones del código

- La lógica vive en `src/*.py`; los notebooks solo orquestan e ilustran (diffs limpios).
- Entorno: `mamba activate centinela` (ver `environment.yml`). Dependencias de runtime para Streamlit en `requirements.txt`.
- Frontend: `streamlit run app.py`.
- Nunca commitear `.env` ni `data/`.
- Los umbrales de `src/risk.py` son **placeholders**: antes del pitch deben reemplazarse por modelos publicados y citables
  (tabla de Mills para venturia; literatura INIA para cerezo).

## Reglas de validez científica

- Lenguaje probabilístico: "mayor probabilidad de…", nunca certezas.
- El granizo no se detecta por satélite NASA: entra como evento ingresado por el usuario.
- Reconocer la latencia de datos (SMAP/GPM casi en tiempo real tienen rezago).
- Anclar el riesgo en umbrales publicados; no inventar un índice.
- No prescribir dosis ni productos.
