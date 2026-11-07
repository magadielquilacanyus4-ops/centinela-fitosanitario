"""
Acceso a productos NASA via earthaccess (requiere Earthdata Login).

Usar para SMAP (humedad del suelo), MODIS (LST/NDVI) y GPM/IMERG (precipitacion).
Para arrancar rapido conviene empezar por NASA POWER (ver nasa_power.py) y sumar
estos cuando se necesite humedad de suelo real o series historicas largas.

Docs: https://earthaccess.readthedocs.io/
"""
from __future__ import annotations

import os
from pathlib import Path

import earthaccess
from dotenv import load_dotenv

load_dotenv()


def login():
    """Autentica contra Earthdata. Lee .env (EARTHDATA_USERNAME / _PASSWORD)."""
    return earthaccess.login(strategy="environment")


def search_smap(bbox: tuple[float, float, float, float], start: str, end: str):
    """Busca granulos SMAP L4 (humedad de suelo) en un bbox y rango de fechas.

    Args:
        bbox: (lon_min, lat_min, lon_max, lat_max).
        start, end: fechas 'YYYY-MM-DD'.

    Returns:
        Lista de resultados de earthaccess (pasar a earthaccess.download()).
    """
    return earthaccess.search_data(
        short_name="SPL4SMGP",   # SMAP L4 Global 3-hourly Soil Moisture
        bounding_box=bbox,
        temporal=(start, end),
    )


def download(results, out_dir: str | Path = "data/raw"):
    """Descarga granulos a disco y devuelve las rutas locales."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    return earthaccess.download(results, local_path=str(out))


if __name__ == "__main__":
    login()
    # bbox aproximado de O'Higgins
    results = search_smap((-71.7, -35.0, -70.0, -33.8), "2026-09-01", "2026-10-31")
    print(f"Granulos encontrados: {len(results)}")
