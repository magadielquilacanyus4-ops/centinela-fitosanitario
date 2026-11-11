"""Pruebas de src/anomalia.py con datos sinteticos (sin internet).

Correr:  python -m pytest -q   (o  python tests/test_anomalia.py)
"""
from __future__ import annotations

import sys
import pathlib

import numpy as np
import pandas as pd

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from src import anomalia  # noqa: E402


def _clima_sintetico(anio_fin=2026, boost=None, semilla=0):
    """Lluvia diaria 1991..anio_fin; `boost` = {anio: factor} multiplica la ventana del evento."""
    rng = np.random.default_rng(semilla)
    idx = pd.date_range("1991-01-01", f"{anio_fin}-12-31", freq="D")
    lluvia = rng.gamma(0.4, 4.0, len(idx)) * (rng.random(len(idx)) < 0.25)
    df = pd.DataFrame({"PRECTOTCORR": lluvia}, index=idx)
    for a, f in (boost or {}).items():
        m = (df.index.year == a) & anomalia._mascara_ventana(df.index, *anomalia.VENTANA_EVENTO)
        df.loc[m, "PRECTOTCORR"] *= f
    return df


def test_anomalia_extrema_es_puesto_1():
    df = _clima_sintetico(boost={2026: 8.0})
    serie = anomalia.agregar_por_anio(df)
    a = anomalia.evaluar_anomalia(serie, 2026)
    assert a.puesto == 1
    assert a.n_base == 35
    assert a.percentil > 95
    assert abs(a.prob_excedencia - 1 / 36) < 1e-9
    assert a.periodo_retorno == 36
    assert a.diferencia_pct > 0


def test_anomalia_tercer_puesto_como_en_la_prensa():
    df = _clima_sintetico(boost={1997: 9.0, 2015: 9.0, 2026: 5.0})
    serie = anomalia.agregar_por_anio(df)
    # fuerza el orden 1997 > 2015 > 2026 > resto
    v = serie.copy()
    v.loc[1997], v.loc[2015], v.loc[2026] = 900.0, 800.0, 700.0
    a = anomalia.evaluar_anomalia(v, 2026)
    assert a.puesto == 3
    assert abs(a.prob_excedencia - 3 / 36) < 1e-9
    tabla = anomalia.comparar_analogos(v, 2026)
    assert list(tabla["anio"]) == [1997, 2015, 2026]
    assert list(tabla["puesto"]) == [1, 2, 3]


def test_anio_incompleto_se_descarta():
    df = _clima_sintetico(anio_fin=2026)
    df = df[~((df.index.year == 2026) & (df.index.month == 10) & (df.index.day > 5))]  # ventana a medias
    serie = anomalia.agregar_por_anio(df)
    assert 2026 not in serie.index
    try:
        anomalia.evaluar_anomalia(serie, 2026)
    except ValueError as e:
        assert "2026" in str(e)
    else:
        raise AssertionError("debio fallar por falta de datos")


def test_valores_faltantes_de_power_no_cuentan_como_cero():
    df = _clima_sintetico()
    m = (df.index.year == 2010) & anomalia._mascara_ventana(df.index, *anomalia.VENTANA_EVENTO)
    df.loc[m, "PRECTOTCORR"] = np.nan          # POWER devuelve -999 -> NaN
    assert 2010 not in anomalia.agregar_por_anio(df).index


def test_curva_acumulada_cierra_con_el_total_y_tiene_banda():
    df = _clima_sintetico(boost={2026: 4.0})
    serie = anomalia.agregar_por_anio(df)
    curva = anomalia.curva_acumulada(df, 2026)
    assert len(curva) == 30
    assert abs(curva["actual"].iloc[-1] - serie.loc[2026]) < 1e-6
    assert (curva["p90"] >= curva["p10"]).all()
    assert {"1997", "2015"} <= set(curva.columns)
    assert curva.index[0] == pd.Timestamp("2026-09-21")
    assert curva.index[-1] == pd.Timestamp("2026-10-20")


def test_texto_y_historico_insuficiente():
    df = _clima_sintetico(boost={2026: 6.0})
    a = anomalia.evaluar_anomalia(anomalia.agregar_por_anio(df), 2026)
    txt = anomalia.describir_anomalia(a)
    assert "puesto 1" in txt and "sobre" in txt and "1991-2025" in txt
    corto = pd.Series(range(5), index=range(2022, 2027), dtype=float)
    try:
        anomalia.evaluar_anomalia(corto, 2026)
    except ValueError as e:
        assert "insuficiente" in str(e)
    else:
        raise AssertionError("debio fallar por historico corto")


def test_descarga_por_bloques_y_cache(tmp_path, monkeypatch=None):
    """Mockea get_power_daily: verifica bloques de 5 anios y que la cache evita pedir de nuevo."""
    llamadas = []

    def falso(lat, lon, start, end, params=None):
        llamadas.append((start, end))
        idx = pd.date_range(start, end, freq="D")
        return pd.DataFrame({"PRECTOTCORR": 1.0}, index=idx)

    anomalia_get, anomalia_cache = anomalia.get_power_daily, anomalia.CACHE_DIR
    anomalia.get_power_daily, anomalia.CACHE_DIR = falso, pathlib.Path(tmp_path) / "cache"
    try:
        df = anomalia.descargar_historico(-34.03, -70.67, 1991, 2000)
        assert len(llamadas) == 2 and llamadas[0][0] == "19910101" and llamadas[1][1] == "20001231"
        assert df.index.is_monotonic_increasing and not df.index.has_duplicates
        anomalia.descargar_historico(-34.03, -70.67, 1991, 2000)
        assert len(llamadas) == 2                       # segunda vez: desde cache
    finally:
        anomalia.get_power_daily, anomalia.CACHE_DIR = anomalia_get, anomalia_cache


if __name__ == "__main__":
    import tempfile
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_"):
            if "tmp_path" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                fn(tempfile.mkdtemp())
            else:
                fn()
            print("OK", nombre)
