"""
Descarga de datos meteorologicos diarios desde NASA POWER (API REST, sin login).

NASA POWER es la via mas rapida para arrancar: temperatura, humedad relativa y
precipitacion diarias por coordenada. Con eso se estiman grados-dia, humedad
foliar aproximada y la base del indice de riesgo.

Docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
"""
from __future__ import annotations

import requests
import pandas as pd

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Parametros utiles para fitosanidad:
#   T2M      = temperatura media a 2 m (C)
#   T2M_MAX  = temperatura maxima (C)
#   T2M_MIN  = temperatura minima (C)
#   RH2M     = humedad relativa a 2 m (%)
#   PRECTOTCORR = precipitacion corregida (mm/dia)
DEFAULT_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "PRECTOTCORR"]


def get_power_daily(
    lat: float,
    lon: float,
    start: str,
    end: str,
    params: list[str] | None = None,
) -> pd.DataFrame:
    """Devuelve un DataFrame diario de NASA POWER para un punto.

    Args:
        lat, lon: coordenadas del huerto (grados decimales).
        start, end: fechas 'YYYYMMDD'.
        params: lista de variables POWER (por defecto DEFAULT_PARAMS).

    Returns:
        DataFrame indexado por fecha, una columna por variable.
    """
    params = params or DEFAULT_PARAMS
    query = {
        "parameters": ",".join(params),
        "community": "AG",          # comunidad agroclimatologia
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
    }
    resp = requests.get(POWER_URL, params=query, timeout=60)
    resp.raise_for_status()
    data = resp.json()["properties"]["parameter"]

    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "fecha"
    # POWER usa -999 como valor faltante
    return df.where(df != -999.0)


if __name__ == "__main__":
    # Ejemplo: Codegua, O'Higgins, primavera 2026
    df = get_power_daily(-34.03, -70.67, "20260901", "20261031")
    print(df.tail())
