"""
Anomalia de una variable climatica frente al historico.

Es el nucleo del desafio "Conviertete en un detective de tendencias": que cambia,
cuanto y si el cambio es significativo. Por defecto mide la lluvia acumulada entre
el 21-sep y el 20-oct (la ventana del evento de primavera 2026) y la compara con
los mismos dias de los anios 1991-2025.

Como la lluvia NO sigue una distribucion normal, el resultado principal es el
ranking empirico (puesto, percentil, periodo de retorno). El z-score se entrega
solo como referencia.

Los datos vienen de NASA POWER (src/nasa_power.py).
"""
from __future__ import annotations

import datetime as dt
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.nasa_power import get_power_daily

VENTANA_EVENTO = ((9, 21), (10, 20))   # (mes, dia) de inicio y fin
ANIOS_ANALOGOS = (1997, 2015)          # anios de El Nino fuerte
ANIO_BASE_INI = 1991                   # inicio del periodo de referencia
CACHE_DIR = Path("data/cache")

NOTA_VALIDEZ = (
    "La lluvia no sigue una distribución normal: por eso se reporta el ranking "
    "empírico y el z-score es solo referencial. El resultado es probabilístico, "
    "no una certeza. Datos NASA POWER (grilla gruesa, ~50 km)."
)


# --- Descarga del historico ------------------------------------------------

def _fin_disponible(anio: int) -> dt.date:
    """Ultimo dia pedible: POWER tiene unos dias de rezago respecto de hoy."""
    return min(dt.date(anio, 12, 31), dt.date.today() - dt.timedelta(days=5))


def descargar_historico(
    lat: float,
    lon: float,
    anio_ini: int = ANIO_BASE_INI,
    anio_fin: int = 2026,
    params: tuple[str, ...] = ("PRECTOTCORR",),
    bloque: int = 5,
    usar_cache: bool = True,
) -> pd.DataFrame:
    """Serie diaria de NASA POWER entre anio_ini y anio_fin, pedida por bloques.

    Guarda una copia en data/cache (ignorada por git). Si el rango incluye el
    anio en curso, la copia vale 24 horas.
    """
    params = list(params)
    ruta = CACHE_DIR / f"power_{lat:.2f}_{lon:.2f}_{'-'.join(params)}_{anio_ini}_{anio_fin}.csv"
    if usar_cache and ruta.exists():
        reciente = (time.time() - ruta.stat().st_mtime) < 86400
        if anio_fin < dt.date.today().year or reciente:
            return pd.read_csv(ruta, index_col=0, parse_dates=True)

    partes = []
    for a in range(anio_ini, anio_fin + 1, bloque):
        b = min(a + bloque - 1, anio_fin)
        ini, fin = dt.date(a, 1, 1), _fin_disponible(b)
        if ini > fin:
            break
        partes.append(
            get_power_daily(lat, lon, ini.strftime("%Y%m%d"), fin.strftime("%Y%m%d"), params=params)
        )
    df = pd.concat(partes).sort_index()
    df = df[~df.index.duplicated()]
    if usar_cache:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(ruta)
    return df


# --- Agregacion por anio ---------------------------------------------------

def _mascara_ventana(index: pd.DatetimeIndex, ini: tuple[int, int], fin: tuple[int, int]):
    md = index.month * 100 + index.day
    return (md >= ini[0] * 100 + ini[1]) & (md <= fin[0] * 100 + fin[1])


def _largo_ventana(ini: tuple[int, int], fin: tuple[int, int]) -> int:
    return (dt.date(2001, *fin) - dt.date(2001, *ini)).days + 1


def agregar_por_anio(
    df: pd.DataFrame,
    col: str = "PRECTOTCORR",
    ini: tuple[int, int] = VENTANA_EVENTO[0],
    fin: tuple[int, int] = VENTANA_EVENTO[1],
    agg: str = "sum",
    min_cobertura: float = 0.9,
) -> pd.Series:
    """Un valor por anio (suma o promedio de la ventana). Descarta anios incompletos."""
    sub = df.loc[_mascara_ventana(df.index, ini, fin), col]
    grupos = sub.groupby(sub.index.year)
    valores = grupos.agg(agg)
    cobertura = grupos.count() / _largo_ventana(ini, fin)
    return valores.where(cobertura >= min_cobertura).dropna().rename(col)


# --- Anomalia y significancia ----------------------------------------------

@dataclass(frozen=True)
class Anomalia:
    anio: int
    valor: float
    media: float
    desviacion: float
    z: float                  # solo referencial
    percentil: float          # 0-100 dentro de la base
    puesto: int               # 1 = el valor mas alto
    n_base: int               # anios de la base (sin contar el evaluado)
    prob_excedencia: float    # fraccion de anios con un valor igual o mayor (Weibull)
    periodo_retorno: float    # 1 / prob_excedencia, en anios
    diferencia_pct: float     # % sobre/bajo el promedio de la base
    anio_base_ini: int

    def a_dict(self) -> dict:
        return asdict(self)


def evaluar_anomalia(serie: pd.Series, anio: int, anio_base_ini: int = ANIO_BASE_INI) -> Anomalia:
    """Compara `anio` con la base (anio_base_ini hasta el anio anterior, sin incluirlo)."""
    if anio not in serie.index:
        raise ValueError(f"No hay datos completos para {anio} en la ventana pedida.")
    valor = float(serie.loc[anio])
    base = serie[(serie.index >= anio_base_ini) & (serie.index != anio)]
    n = len(base)
    if n < 10:
        raise ValueError(f"Historico insuficiente ({n} anios); se necesitan al menos 10.")
    media, desv = float(base.mean()), float(base.std(ddof=1))
    mayores = int((base > valor).sum())
    iguales = int((base == valor).sum())
    menores = int((base < valor).sum())
    prob = (mayores + 1) / (n + 1)           # posicion de graficacion de Weibull
    return Anomalia(
        anio=anio,
        valor=valor,
        media=media,
        desviacion=desv,
        z=(valor - media) / desv if desv > 0 else float("nan"),
        percentil=100.0 * (menores + 0.5 * iguales) / n,
        puesto=mayores + 1,
        n_base=n,
        prob_excedencia=prob,
        periodo_retorno=1.0 / prob,
        diferencia_pct=100.0 * (valor - media) / media if media else float("nan"),
        anio_base_ini=anio_base_ini,
    )


def describir_anomalia(
    a: Anomalia,
    variable: str = "lluvia",
    unidad: str = "mm",
    periodo: str = "21-sep al 20-oct",
) -> str:
    """Frase lista para mostrar, con lenguaje probabilistico."""
    signo = "sobre" if a.diferencia_pct >= 0 else "bajo"
    return (
        f"Del {periodo} de {a.anio}, la {variable} acumulada fue {a.valor:.0f} {unidad}, "
        f"{abs(a.diferencia_pct):.0f}% {signo} el promedio {a.anio_base_ini}-{a.anio - 1} "
        f"({a.media:.0f} {unidad}). Ocupa el puesto {a.puesto} entre {a.n_base + 1} años "
        f"(percentil {a.percentil:.0f}). Un valor igual o mayor apareció en cerca de "
        f"{a.prob_excedencia * 100:.0f}% de los años, es decir, aproximadamente 1 de cada "
        f"{a.periodo_retorno:.0f} años."
    )


def comparar_analogos(
    serie: pd.Series, anio_actual: int, analogos: tuple[int, ...] = ANIOS_ANALOGOS
) -> pd.DataFrame:
    """Tabla del anio actual y de los anios analogos (El Nino fuerte)."""
    anios = [a for a in (*analogos, anio_actual) if a in serie.index]
    out = pd.DataFrame({"anio": anios, "valor": [float(serie.loc[a]) for a in anios]})
    out["puesto"] = out["valor"].apply(lambda v: int((serie > v).sum()) + 1)
    out["n_anios"] = len(serie)
    base = serie[(serie.index >= ANIO_BASE_INI) & (serie.index != anio_actual)]
    out["vs_promedio_pct"] = 100.0 * (out["valor"] - base.mean()) / base.mean()
    return out


def curva_acumulada(
    df: pd.DataFrame,
    anio: int,
    col: str = "PRECTOTCORR",
    ini: tuple[int, int] = VENTANA_EVENTO[0],
    fin: tuple[int, int] = VENTANA_EVENTO[1],
    analogos: tuple[int, ...] = ANIOS_ANALOGOS,
    anio_base_ini: int = ANIO_BASE_INI,
) -> pd.DataFrame:
    """Acumulado dia a dia dentro de la ventana: anio actual vs. promedio y banda p10-p90."""
    largo = _largo_ventana(ini, fin)
    cols = {}
    for a in sorted(set(df.index.year)):
        sub = df.loc[(df.index.year == a) & _mascara_ventana(df.index, ini, fin), col]
        if sub.count() < 0.9 * largo:
            continue
        desfase = (sub.index - pd.Timestamp(a, ini[0], ini[1])).days
        s = pd.Series(sub.values, index=desfase).reindex(range(largo))
        cols[a] = s.fillna(0).cumsum()
    m = pd.DataFrame(cols)
    if anio not in m.columns:
        raise ValueError(f"No hay datos completos para {anio} en la ventana pedida.")
    base = m[[c for c in m.columns if c >= anio_base_ini and c != anio]]
    out = pd.DataFrame(
        {
            "actual": m[anio],
            "promedio": base.mean(axis=1),
            "p10": base.quantile(0.10, axis=1),
            "p90": base.quantile(0.90, axis=1),
        }
    )
    for a in analogos:
        if a in m.columns:
            out[str(a)] = m[a]
    out.index = pd.date_range(dt.date(anio, *ini), periods=largo)
    return out


def comparar_puntos(
    puntos: dict[str, tuple[float, float]], anio: int, anio_base_ini: int = ANIO_BASE_INI
) -> pd.DataFrame:
    """Anomalia en varios puntos (responde el 'donde' del desafio).

    OJO: la grilla de NASA POWER es gruesa (~50 km). Comunas vecinas caen en la
    misma celda y darian valores identicos; usar puntos separados.
    """
    filas = []
    for nombre, (lat, lon) in puntos.items():
        df = descargar_historico(lat, lon, anio_base_ini, anio)
        a = evaluar_anomalia(agregar_por_anio(df), anio, anio_base_ini)
        filas.append({"punto": nombre, "lat": lat, "lon": lon, **a.a_dict()})
    return pd.DataFrame(filas)


if __name__ == "__main__":
    # Ejemplo: zona de estudio anonimizada, primavera 2026 (requiere internet)
    from src import anonimato
    pt = anonimato.generalizar()
    hist = descargar_historico(pt.lat, pt.lon)
    serie = agregar_por_anio(hist)
    a = evaluar_anomalia(serie, 2026)
    print(describir_anomalia(a))
    print(comparar_analogos(serie, 2026))
