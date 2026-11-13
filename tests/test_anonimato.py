"""Pruebas de src/anonimato.py. Correr:  python3 tests/test_anonimato.py"""
import pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import anonimato as a


def test_misma_celda_curico_molina():
    assert a.centro_celda(-34.98, -71.24) == a.centro_celda(-35.12, -71.28) == (-35.0, -71.25)


def test_generalizar_no_expone_referencia():
    p = a.generalizar()
    assert (p.lat, p.lon) == (-35.0, -71.25)
    assert (p.lat, p.lon) != a.ZONA_ESTUDIO.referencia
    assert p.lat_min < p.lat < p.lat_max and p.lon_min < p.lon < p.lon_max
    assert "Parcela piloto" in p.etiqueta


def test_ocultar_nombres_con_tildes_y_mayusculas():
    t = a.ocultar_nombres("Habló Víctor Catán; VICTOR  CATAN insistió.", ["Victor Catan"])
    assert "Catán" not in t and "CATAN" not in t and t.count("[reservado]") == 2


def test_escanear_encuentra_y_respeta_exclusiones():
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "nota.md").write_text("linea 1\nproductor Ana Pérez en Molina\n", encoding="utf-8")
        (d / "data").mkdir()
        (d / "data" / "privado.md").write_text("Ana Pérez", encoding="utf-8")
        (d / "CLAUDE.local.md").write_text("Ana Perez", encoding="utf-8")
        h = a.escanear(d, ["Ana Perez"])
        assert h == [("nota.md", 2, "Ana Perez")], h
        assert a.escanear(d, ["Otra Persona"]) == []


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("ok", nombre)
