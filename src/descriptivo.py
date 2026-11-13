"""
Estadistica descriptiva de la serie diaria de NASA POWER.

Funciones puras (sin red ni graficos) que usa el notebook 02_descriptivo.
Cada variable se resume dentro de la ventana del evento (21-sep a 20-oct) y se
compara con el mismo periodo de los anios de la base, con el mismo ranking
empirico que `src/anomalia.py`.
"""
from __future__ import annotations

import pandas as pd

from src.anomalia import (
    ANIO_BASE_INI,
    VENTANA_EVENTO,
    agregar_por_anio,
    evaluar_anomalia,
)

NOMBRES = {
    "T2M": "Temperatura media (°C)",
    "T2M_MAX": "Temperatura máxima (°C)",
    "T2M_MIN": "Temperatura mínima (°C)",
    "RH2M": "Humedad relativa (%)",
    "PRECTOTCORR": "Lluvia (mm/día)",
    "GWETROOT": "Humedad zona radicular (0-1)",
    "GWETTOP": "Humedad superficial (0-1)",
}

UMBRAL_DIA_LLUVIOSO = 1.0      # mm; dia con lluvia
UMBRAL_DIA_HUMEDO = 90.0       # % RH2M; dia muy humedo (referencial, no es un umbral de riesgo)


def resumen_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla clasica por variable: n, faltantes, media, desviacion, cuantiles y asimetria."""
    q = df.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).T
    q.columns = ["p5", "p25", "mediana", "p75", "p95"]
    out = pd.DataFrame(
        {
            "n": df.count(),
            "faltantes_%": 100 * df.isna().mean(),
            "media": df.mean(),
            "desv": df.std(),
            "min": df.min(),
            "max": df.max(),
            "asimetria": df.skew(),
        }
    )
    out = out.join(q)[["n", "faltantes_%", "min", "p5", "p25", "mediana", "media", "p75", "p95", "max", "desv", "asimetria"]]
    out.index = [NOMBRES.get(c, c) for c in out.index]
    return out.round(2)


def climatologia_mensual(df: pd.DataFrame, col: str, anio_ini: int, anio_fin: int) -> pd.DataFrame:
    """Promedio mensual de `col` y banda p10-p90 entre anios; lluvia como total mensual."""
    sub = df.loc[(df.index.year >= anio_ini) & (df.index.year <= anio_fin), col]
    if col == "PRECTOTCORR":
        por_anio_mes = sub.groupby([sub.index.year, sub.index.month]).sum()
    else:
        por_anio_mes = sub.groupby([sub.index.year, sub.index.month]).mean()
    g = por_anio_mes.groupby(level=1)
    return pd.DataFrame({"media": g.mean(), "p10": g.quantile(0.10), "p90": g.quantile(0.90)})


def mensual_de_un_anio(df: pd.DataFrame, col: str, anio: int) -> pd.Series:
    sub = df.loc[df.index.year == anio, col]
    return (sub.groupby(sub.index.month).sum() if col == "PRECTOTCORR" else sub.groupby(sub.index.month).mean())


def _con_derivadas(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["DIAS_LLUVIA"] = (d["PRECTOTCORR"] >= UMBRAL_DIA_LLUVIOSO).astype(float).where(d["PRECTOTCORR"].notna())
    d["DIAS_RH90"] = (d["RH2M"] >= UMBRAL_DIA_HUMEDO).astype(float).where(d["RH2M"].notna())
    return d


# (columna, agregacion, etiqueta)
INDICADORES_VENTANA = [
    ("PRECTOTCORR", "sum", "Lluvia acumulada (mm)"),
    ("PRECTOTCORR", "max", "Lluvia máxima diaria (mm)"),
    ("DIAS_LLUVIA", "sum", f"Días con lluvia ≥ {UMBRAL_DIA_LLUVIOSO:g} mm"),
    ("T2M", "mean", "Temperatura media (°C)"),
    ("T2M_MAX", "mean", "Temperatura máxima media (°C)"),
    ("T2M_MIN", "mean", "Temperatura mínima media (°C)"),
    ("RH2M", "mean", "Humedad relativa media (%)"),
    ("DIAS_RH90", "sum", f"Días con HR ≥ {UMBRAL_DIA_HUMEDO:g} %"),
    ("GWETROOT", "mean", "Humedad radicular media (0-1)"),
    ("GWETROOT", "max", "Humedad radicular máxima (0-1)"),
    ("GWETTOP", "mean", "Humedad superficial media (0-1)"),
]


def series_ventana(df: pd.DataFrame, col: str, agg: str,
                   ini: tuple[int, int] = VENTANA_EVENTO[0],
                   fin: tuple[int, int] = VENTANA_EVENTO[1]) -> pd.Series:
    return agregar_por_anio(_con_derivadas(df), col, ini, fin, agg)


def tabla_ventana(df: pd.DataFrame, anio: int, anio_base_ini: int = ANIO_BASE_INI) -> pd.DataFrame:
    """Cada indicador del evento en `anio` frente a la base: media, valor, diferencia y puesto."""
    filas = []
    for col, agg, etiqueta in INDICADORES_VENTANA:
        a = evaluar_anomalia(series_ventana(df, col, agg), anio, anio_base_ini)
        filas.append(
            {
                "indicador": etiqueta,
                f"base {anio_base_ini}-{anio - 1}": a.media,
                str(anio): a.valor,
                "dif_abs": a.valor - a.media,
                "dif_%": a.diferencia_pct,   # poco util en °C: leer dif_abs
                "puesto": f"{a.puesto} de {a.n_base + 1}",
                "percentil": a.percentil,
            }
        )
    return pd.DataFrame(filas).set_index("indicador").round(2)
