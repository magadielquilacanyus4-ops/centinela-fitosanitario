"""
Condiciones favorables para infeccion por Monilinia y Botrytis en cerezo,
a partir de temperatura y humedad horarias de NASA POWER.

Los modelos publicados de infeccion usan  temperatura x HORAS DE MOJADO.
POWER no mide mojado foliar: se aproxima con horas de humedad relativa alta o
lluvia (PROXY, ver `horas_mojado`). No es un indice inventado: se evalua si cada
episodio de mojado cumple los minimos publicados (rango de temperatura y horas)
y se cuentan esos episodios. No se estima una probabilidad de infeccion, porque
las curvas completas (Tamm 1995, Biggs y Northover 1988) aun no estan
verificadas contra el texto original.

ESTADO DE LOS PARAMETROS (ver PARAMETROS): los valores salen de resumenes y
citas de busqueda, NO del texto completo de los articulos (el sitio de la APS
devolvio 403). Hay que contrastarlos antes del pitch. Botrytis en cerezo no
tiene aun un modelo propio localizado: queda sin parametrizar.

Lenguaje: "condiciones favorables", nunca "habra infeccion". No prescribe
productos ni dosis.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# --- Proxy de mojado ---------------------------------------------------------
UMBRAL_RH_MOJADO = 90.0     # % ; SUPUESTO del proyecto (no citado). Probar 85/90/95.
UMBRAL_LLUVIA_MOJADO = 0.1  # mm/h ; SUPUESTO del proyecto (no citado)


@dataclass(frozen=True)
class Criterio:
    """Condiciones minimas para que un episodio de mojado se considere favorable."""
    t_min: float
    t_max: float
    horas_min: float
    fuente: str
    estado: str       # que tan verificado esta
    nota: str = ""


# Cada entrada: (patogeno, etapa)
PARAMETROS: dict[tuple[str, str], Criterio | None] = {
    # Luo et al. (2001), flor de ciruelo (Monilinia fructicola): sin tizon de flor a
    # <10 o >30 C ni con <4 h de mojado. Tamm et al. (1995), cerezo dulce, M. laxa,
    # 5-20 C y 0-24 h: la incidencia sube con temperatura y duracion del mojado.
    ("monilinia", "floracion"): Criterio(
        t_min=10.0, t_max=30.0, horas_min=4.0,
        fuente="Luo et al. 2001 (ciruelo, M. fructicola); Tamm et al. 1995 (cerezo, M. laxa)",
        estado="cifras tomadas de resumenes de busqueda; falta contrastar con el texto completo",
        nota="Minimos, no probabilidad. El cerezo de Tamm se probo solo hasta 20 C.",
    ),
    # Biggs y Northover (1988), fruto sano de cerezo y durazno, M. fructicola:
    # optimo 20-22,5 C en cerezo, >80 % de infeccion tras 15 h de mojado.
    ("monilinia", "fruto"): Criterio(
        t_min=20.0, t_max=22.5, horas_min=15.0,
        fuente="Biggs y Northover 1988 (cerezo y durazno, M. fructicola)",
        estado="cifras tomadas del resumen de busqueda; falta contrastar con el texto completo",
        nota="Es el OPTIMO observado (>80 % de infeccion), no el minimo; subestima el riesgo fuera de 20-22,5 C.",
    ),
    # No se localizo un modelo de Botrytis para flor/fruto de cerezo. Bulger et al.
    # (1987) es de flor de frutilla (5-30 C, hasta 32 h) y Broome et al. (1995) de
    # uva: son sustitutos de otra especie y no se usan como si fueran de cerezo.
    ("botrytis", "floracion"): None,
    ("botrytis", "fruto"): None,
}


# --- Horas y episodios de mojado --------------------------------------------

def horas_mojado(
    df_h: pd.DataFrame,
    umbral_rh: float = UMBRAL_RH_MOJADO,
    umbral_lluvia: float = UMBRAL_LLUVIA_MOJADO,
) -> pd.Series:
    """Booleano por hora: HR >= umbral o lluvia horaria >= umbral (PROXY de mojado foliar)."""
    mojado = (df_h["RH2M"] >= umbral_rh) | (df_h["PRECTOTCORR"] >= umbral_lluvia)
    return mojado.where(df_h["RH2M"].notna() & df_h["PRECTOTCORR"].notna(), False)


def episodios(df_h: pd.DataFrame, **kw) -> pd.DataFrame:
    """Episodios continuos de mojado: inicio, fin, horas y temperatura media."""
    m = horas_mojado(df_h, **kw)
    # Una hora sin dato corta el episodio; las horas deben ser consecutivas.
    horas = df_h.index.to_series()
    corte = (~m) | (horas.diff() != pd.Timedelta(hours=1)) | (~m.shift(fill_value=False))
    grupo = corte.cumsum()
    filas = []
    for _, bloque in df_h[m].groupby(grupo[m]):
        filas.append(
            {
                "inicio": bloque.index[0],
                "fin": bloque.index[-1],
                "horas": len(bloque),
                "t_media": float(bloque["T2M"].mean()),
                "t_min": float(bloque["T2M"].min()),
                "t_max": float(bloque["T2M"].max()),
            }
        )
    cols = ["inicio", "fin", "horas", "t_media", "t_min", "t_max"]
    return pd.DataFrame(filas, columns=cols)


def episodios_favorables(
    df_h: pd.DataFrame, patogeno: str, etapa: str, **kw
) -> pd.DataFrame:
    """Episodios que cumplen los minimos publicados (temperatura media del episodio y horas).

    Devuelve un DataFrame vacio con aviso si el par patogeno/etapa no esta parametrizado.
    """
    crit = PARAMETROS.get((patogeno, etapa))
    if crit is None:
        raise NotImplementedError(
            f"Sin modelo publicado verificado para {patogeno} / {etapa} (ver PARAMETROS)."
        )
    ep = episodios(df_h, **kw)
    ok = (ep["horas"] >= crit.horas_min) & ep["t_media"].between(crit.t_min, crit.t_max)
    return ep[ok].reset_index(drop=True)


def resumen_diario(df_h: pd.DataFrame, patogeno: str, etapa: str, **kw) -> pd.DataFrame:
    """Por dia (fecha de inicio del episodio): horas de mojado y si hubo un episodio favorable."""
    dias = pd.DataFrame(index=pd.date_range(df_h.index.min().normalize(), df_h.index.max().normalize()))
    dias.index.name = "fecha"
    m = horas_mojado(df_h, **kw)
    dias["horas_mojado"] = m.groupby(m.index.normalize()).sum().reindex(dias.index).fillna(0).astype(int)
    fav = episodios_favorables(df_h, patogeno, etapa, **kw)
    marca = fav["inicio"].dt.normalize().value_counts() if len(fav) else pd.Series(dtype=int)
    dias["episodios_favorables"] = marca.reindex(dias.index).fillna(0).astype(int)
    dias["condicion_favorable"] = dias["episodios_favorables"] > 0
    return dias
