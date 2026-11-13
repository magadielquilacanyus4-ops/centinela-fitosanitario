"""Pruebas de src/riesgo_hongos.py con series horarias sinteticas (sin red).

Correr:  python tests/test_riesgo_hongos.py   (o  python -m pytest -q)
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from src import riesgo_hongos as rh


def _horario(rh, t=15.0, lluvia=0.0):
    idx = pd.date_range("2026-10-01", periods=len(rh), freq="h")
    return pd.DataFrame(
        {"T2M": np.broadcast_to(t, len(rh)).astype(float), "RH2M": np.array(rh, float),
         "PRECTOTCORR": np.broadcast_to(lluvia, len(rh)).astype(float)}, index=idx)


def test_episodio_cuenta_horas_consecutivas():
    df = _horario([50] * 5 + [95] * 6 + [50] * 3 + [95] * 2 + [50] * 2)
    ep = rh.episodios(df)
    assert list(ep["horas"]) == [6, 2]


def test_lluvia_tambien_moja():
    df = _horario([50] * 6, lluvia=[0, 0.5, 0.5, 0.5, 0.5, 0])
    assert list(rh.episodios(df)["horas"]) == [4]


def test_minimos_monilinia_floracion():
    # 5 h a 15 C cumple (>=4 h, 10-30 C)
    assert len(rh.episodios_favorables(_horario([50] * 3 + [95] * 5 + [50] * 3, t=15), "monilinia", "floracion")) == 1
    # 3 h no cumple
    assert len(rh.episodios_favorables(_horario([50] * 3 + [95] * 3 + [50] * 3, t=15), "monilinia", "floracion")) == 0
    # 6 h a 5 C no cumple por temperatura
    assert len(rh.episodios_favorables(_horario([50] * 3 + [95] * 6 + [50] * 3, t=5), "monilinia", "floracion")) == 0


def test_fruto_exige_optimo_y_15_horas():
    largo = [50] * 2 + [95] * 16 + [50] * 2
    assert len(rh.episodios_favorables(_horario(largo, t=21), "monilinia", "fruto")) == 1
    assert len(rh.episodios_favorables(_horario(largo, t=14), "monilinia", "fruto")) == 0


def test_botrytis_sin_parametrizar_falla_explicito():
    try:
        rh.episodios_favorables(_horario([95] * 10), "botrytis", "floracion")
    except NotImplementedError:
        return
    raise AssertionError("debio fallar: Botrytis no esta parametrizado")


def test_hora_faltante_corta_el_episodio():
    df = _horario([95] * 8)
    df = df.drop(df.index[4])
    assert list(rh.episodios(df)["horas"]) == [4, 3]


def test_resumen_diario_marca_dia_de_inicio():
    df = _horario([50] * 20 + [95] * 8 + [50] * 20, t=14)
    d = rh.resumen_diario(df, "monilinia", "floracion")
    assert d.loc["2026-10-01", "condicion_favorable"]
    assert not d.loc["2026-10-02", "condicion_favorable"]
    assert d["horas_mojado"].sum() == 8


if __name__ == "__main__":
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("OK", nombre)
