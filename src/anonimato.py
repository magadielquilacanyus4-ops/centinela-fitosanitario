"""
Capa de anonimato.

El proyecto es publico (repo en GitHub, demo en Streamlit Cloud). Por eso nunca debe
contener ni mostrar la ubicacion exacta de un predio, ni nombres de productores,
empresas o predios que aparezcan en prensa o en conversaciones.

Reglas:
1. Ubicacion: solo se usa y se muestra el CENTRO DE LA CELDA DE DATOS que contiene a la
   zona (grilla nominal de NASA POWER: 0.5 x 0.625 grados, ~50 km; a verificar). Es mas
   honesto, porque el dato no resuelve una parcela, y a la vez impide ubicar un predio.
2. Etiquetas: la parcela es siempre "Parcela piloto" (generica), nunca el nombre de un predio.
3. Texto: los nombres de personas y empresas privadas se guardan SOLO en un archivo local
   ignorado por git (data/privado/nombres.txt, uno por linea). Sirven para ocultarlos en
   textos y para escanear el repo antes de publicar:

       python -m src.anonimato
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVO_NOMBRES = ROOT / "data" / "privado" / "nombres.txt"

# Grilla nominal de NASA POWER (MERRA-2). Verificar localmente (ver README).
PASO_LAT = 0.5
PASO_LON = 0.625


@dataclass(frozen=True)
class ZonaEstudio:
    """Zona del proyecto. `referencia` es la capital comunal (dato publico), NO un predio."""
    comuna: str
    region_texto: str
    referencia: tuple[float, float]


# Zona de estudio vigente. Para cambiarla basta editar esta linea.
ZONA_ESTUDIO = ZonaEstudio("Curicó", "Región del Maule", (-34.98, -71.24))


@dataclass(frozen=True)
class PuntoPublico:
    """Lo unico que la app usa y muestra de la ubicacion."""
    lat: float
    lon: float
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    etiqueta: str

    @property
    def bbox(self) -> list[list[float]]:
        return [[self.lat_min, self.lon_min], [self.lat_max, self.lon_max]]


def centro_celda(lat: float, lon: float,
                 paso_lat: float = PASO_LAT, paso_lon: float = PASO_LON) -> tuple[float, float]:
    """Centro de la celda de la grilla que contiene al punto."""
    return (round(lat / paso_lat) * paso_lat, round(lon / paso_lon) * paso_lon)


def generalizar(zona: ZonaEstudio = ZONA_ESTUDIO) -> PuntoPublico:
    """Reduce la zona a su celda de datos: centro y limites, sin coordenadas de predios."""
    lat, lon = centro_celda(*zona.referencia)
    return PuntoPublico(
        lat=round(lat, 4), lon=round(lon, 4),
        lat_min=round(lat - PASO_LAT / 2, 4), lat_max=round(lat + PASO_LAT / 2, 4),
        lon_min=round(lon - PASO_LON / 2, 4), lon_max=round(lon + PASO_LON / 2, 4),
        etiqueta=f"Parcela piloto - zona de {zona.comuna}",
    )


# --- Nombres privados ------------------------------------------------------

_VARIANTES = {"a": "aáàäâ", "e": "eéèëê", "i": "iíìïî", "o": "oóòöô", "u": "uúùüû", "n": "nñ"}


def _patron(nombre: str) -> re.Pattern:
    """Regex sin distinguir mayusculas ni tildes ('Victor' = 'Víctor')."""
    partes = []
    for ch in nombre.strip():
        if ch.isspace():
            partes.append(r"\s+")
            continue
        base = ch.lower()
        for k, v in _VARIANTES.items():
            if base == k or base in v:
                partes.append(f"[{v}{v.upper()}]")
                break
        else:
            partes.append(re.escape(ch))
    return re.compile("".join(partes), re.IGNORECASE)


def cargar_nombres(ruta: Path = ARCHIVO_NOMBRES) -> list[str]:
    if not ruta.exists():
        return []
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    return [x.strip() for x in lineas if x.strip() and not x.lstrip().startswith("#")]


def ocultar_nombres(texto: str, nombres: list[str], reemplazo: str = "[reservado]") -> str:
    for n in nombres:
        texto = _patron(n).sub(reemplazo, texto)
    return texto


EXTENSIONES = (".py", ".md", ".txt", ".ipynb", ".json", ".yml", ".yaml", ".csv", ".toml")
EXCLUIR = {".git", "__pycache__", "privado", ".venv", "env", ".conda", ".ipynb_checkpoints"}
EXCLUIR_ARCHIVOS = {"CLAUDE.local.md", "settings.local.json"}


def escanear(raiz: Path, nombres: list[str]) -> list[tuple[str, int, str]]:
    """Busca nombres privados en los archivos de texto. Devuelve (ruta, linea, nombre)."""
    patrones = [(n, _patron(n)) for n in nombres]
    hallazgos = []
    for ruta in sorted(Path(raiz).rglob("*")):
        if not ruta.is_file() or ruta.suffix.lower() not in EXTENSIONES:
            continue
        if ruta.name in EXCLUIR_ARCHIVOS or any(p in EXCLUIR for p in ruta.relative_to(raiz).parts):
            continue
        try:
            lineas = ruta.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, linea in enumerate(lineas, 1):
            for n, pat in patrones:
                if pat.search(linea):
                    hallazgos.append((str(ruta.relative_to(raiz)), i, n))
    return hallazgos


def main() -> int:
    nombres = cargar_nombres()
    if not nombres:
        print(f"No hay lista de nombres. Crea {ARCHIVO_NOMBRES.relative_to(ROOT)} "
              "(uno por linea) con los nombres a proteger.")
        return 2
    hallazgos = escanear(ROOT, nombres)
    if hallazgos:
        print("ATENCION: hay nombres protegidos en el repo:")
        for ruta, linea, n in hallazgos:
            print(f"  {ruta}:{linea}  ({n[:1]}...)")
        return 1
    print(f"OK: ninguno de los {len(nombres)} nombres protegidos aparece en el repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
