# Centinela Fitosanitario 🍒🛰️

Herramienta de apoyo a la decisión que cruza **riesgo de infección** × **viabilidad de aplicación**
para huertos de cerezo y manzano en la Región de O'Higgins (Chile), usando observaciones de la Tierra de la NASA.

**NASA Space Apps Challenge 2026** — desafío *"Conviértete en un detective de tendencias del sistema terrestre"*.

> La idea y el alcance completo están en el doc del proyecto: `claude/idea-y-alcance.md`.

---

## Qué hace (MVP)

1. Detecta la **anomalía climática** de la temporada y argumenta que es significativa.
2. Calcula un **índice de riesgo de infección** (humedad foliar + temperatura) para 1–2 patógenos.
3. Calcula una **ventana de aplicación** (humedad del suelo + lluvia pronosticada) → semáforo puede/no puede.
4. Entrega una **recomendación combinada** y un calendario de los próximos días.

---

## Setup

Requiere [Miniforge/Mamba](https://github.com/conda-forge/miniforge) (recomendado) o conda.

```bash
# 1. Crear el entorno
mamba env create -f environment.yml
mamba activate centinela

# 2. Registrar el kernel para los notebooks
python -m ipykernel install --user --name centinela --display-name "Python (centinela)"

# 3. Activar la limpieza automatica de notebooks (una vez por clon)
nbstripout --install

# 4. Credenciales Earthdata (para SMAP/MODIS/GPM via earthaccess)
cp .env.example .env   # y edita con tu usuario/clave de https://urs.earthdata.nasa.gov/
```

### Correr en VSCode
- Abre la carpeta en VSCode con la extensión **Jupyter**.
- Elige el kernel **"Python (centinela)"**.
- Opcional: para usar un runtime de **Google Colab** como kernel, instala la extensión oficial de Colab para VSCode y selecciónalo al elegir kernel.

---

## Estructura

```
centinela-fitosanitario/
├── environment.yml        # entorno reproducible
├── .env.example           # plantilla de credenciales (NO commitear .env real)
├── .gitignore
├── src/                   # logica en modulos .py (importables, diff-friendly)
│   ├── nasa_power.py      # descarga NASA POWER (REST, sin login)
│   ├── earthdata.py       # descarga SMAP/MODIS/GPM via earthaccess
│   └── risk.py            # riesgo de infeccion + ventana de aplicacion
├── notebooks/             # notebooks "delgados" que orquestan y visualizan
│   └── 01_exploracion.ipynb
└── data/                  # datos locales (ignorado por git)
```

**Convención de trabajo:** la lógica vive en `src/*.py`; los notebooks solo orquestan e ilustran.
Así git hace diffs limpios y el equipo no pelea por el JSON de los `.ipynb`.

---

## Equipo

Proyecto del hackathon. Mantener el doc de alcance actualizado en el proyecto de Claude.
