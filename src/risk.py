"""
Logica central: riesgo de infeccion + viabilidad de aplicacion.

ADVERTENCIA DE VALIDEZ (importante para el pitch):
Los umbrales aqui son PLACEHOLDERS de arranque, no verdades agronomicas.
Antes de presentar, reemplazar por modelos publicados y citables:
  - Manzano / venturia (sarna): tabla de Mills (horas de humedad foliar x temperatura).
  - Cerezo / pudriciones y canceres: umbrales de la literatura local (INIA).
Ver pendientes en claude/idea-y-alcance.md, seccion 11.
"""
from __future__ import annotations

import pandas as pd


# --- 1. Riesgo de infeccion -------------------------------------------------

def estimar_humedad_foliar(df: pd.DataFrame, umbral_rh: float = 90.0) -> pd.Series:
    """Proxy simple de humedad foliar: dias con humedad relativa alta o lluvia.

    Placeholder. Un modelo real estima HORAS de mojado foliar; aqui, a escala
    diaria, marcamos el dia como "humedo" si RH2M >= umbral o hubo lluvia.
    """
    humedo = (df["RH2M"] >= umbral_rh) | (df["PRECTOTCORR"] > 0.2)
    return humedo.astype(int)


def riesgo_infeccion(df: pd.DataFrame) -> pd.Series:
    """Indice 0-1 de riesgo diario de infeccion (PLACEHOLDER).

    Combina mojado foliar con una ventana de temperatura favorable (~10-25 C).
    Reemplazar por el modelo epidemiologico del patogeno objetivo.
    """
    humedo = estimar_humedad_foliar(df)
    temp_ok = df["T2M"].between(10, 25).astype(int)
    # riesgo alto solo si hay mojado foliar Y temperatura favorable
    return (humedo * temp_ok).clip(0, 1)


# --- 2. Viabilidad de aplicacion -------------------------------------------

def ventana_aplicacion(
    df: pd.DataFrame,
    humedad_suelo: pd.Series | None = None,
    umbral_suelo: float = 0.40,
) -> pd.Series:
    """Marca los dias en que SI se puede aplicar (1) o NO (0).

    No se puede aplicar si:
      - llueve ese dia, o
      - el suelo esta anegado (humedad_suelo por sobre el umbral) -> maquinaria no entra.

    Args:
        df: salida de NASA POWER (necesita PRECTOTCORR).
        humedad_suelo: serie diaria de humedad volumetrica (SMAP). Opcional.
        umbral_suelo: por sobre este valor, se considera suelo intransitable.
    """
    sin_lluvia = (df["PRECTOTCORR"] <= 0.2)
    if humedad_suelo is not None:
        suelo_ok = humedad_suelo.reindex(df.index) <= umbral_suelo
    else:
        suelo_ok = pd.Series(True, index=df.index)
    return (sin_lluvia & suelo_ok).astype(int)


# --- 3. Recomendacion combinada --------------------------------------------

def recomendacion(df: pd.DataFrame, humedad_suelo: pd.Series | None = None) -> pd.DataFrame:
    """Cruza riesgo y ventana de aplicacion en una tabla accionable."""
    out = pd.DataFrame(index=df.index)
    out["riesgo"] = riesgo_infeccion(df)
    out["puede_aplicar"] = ventana_aplicacion(df, humedad_suelo)

    def etiqueta(row):
        if row["riesgo"] and row["puede_aplicar"]:
            return "APLICAR AHORA (riesgo alto, ventana abierta)"
        if row["riesgo"] and not row["puede_aplicar"]:
            return "RIESGO sin poder aplicar (vigilar / evaluar dron)"
        if not row["riesgo"] and row["puede_aplicar"]:
            return "Ventana disponible (riesgo bajo)"
        return "Sin accion"

    out["recomendacion"] = out.apply(etiqueta, axis=1)
    return out
