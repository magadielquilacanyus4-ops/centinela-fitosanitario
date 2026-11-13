"""
Centinela Fitosanitario - app Streamlit (frontend MVP).

Zona piloto anonimizada -> descarga clima (NASA POWER) -> riesgo de infeccion
y ventana de aplicacion (src/risk.py) -> mapa, grafico del evento y semaforo.

Correr local:  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from src.nasa_power import get_power_daily
from src import anomalia, anonimato, risk

# streamlit-folium para el mapa (import defensivo: si falta, usamos st.map)
try:
    import folium
    from streamlit_folium import st_folium
    _HAS_MAP = True
except Exception:
    _HAS_MAP = False

# Zona de estudio anonimizada (src/anonimato.py): la app solo usa el centro de la celda de datos.
ZONA = anonimato.ZONA_ESTUDIO
PUNTO = anonimato.generalizar(ZONA)

st.set_page_config(page_title="Centinela Fitosanitario", page_icon="\U0001F352", layout="wide")

st.title("\U0001F352\U0001F6F0️ Centinela Fitosanitario")
st.caption(
    "Riesgo de infeccion x viabilidad de aplicacion para huertos de cerezo "
    f"en la zona de {ZONA.comuna} ({ZONA.region_texto}), con observaciones de la Tierra de la NASA."
)

# --- Controles ---
with st.sidebar:
    st.header("Zona de estudio")
    comuna = ZONA.comuna
    st.markdown(f"**Comuna:** {comuna}")
    st.markdown("**Parcela:** piloto (ubicación generalizada)")
    st.markdown("**Cultivo:** Cerezo")
    cultivo = "Cerezo"
    st.divider()
    st.header("Periodo")
    inicio = st.date_input("Desde", dt.date(2026, 9, 1))
    fin = st.date_input("Hasta", dt.date(2026, 10, 31))
    st.caption("El evento de primavera 2026 se ve entre septiembre y octubre.")

lat, lon = PUNTO.lat, PUNTO.lon


@st.cache_data(show_spinner="Descargando clima de NASA POWER...")
def cargar_clima(lat, lon, inicio, fin):
    return get_power_daily(
        lat, lon,
        start=inicio.strftime("%Y%m%d"),
        end=fin.strftime("%Y%m%d"),
    )


try:
    df = cargar_clima(lat, lon, inicio, fin)
except Exception as e:
    st.error(f"No se pudo descargar NASA POWER: {e}")
    st.stop()

rec = risk.recomendacion(df)

# --- 1. Que cambio? Anomalia de lluvia frente al historico ---
ANIO_EVENTO = 2026


@st.cache_data(show_spinner="Descargando historico de NASA POWER (1991-2026)...")
def cargar_historico(lat, lon, anio):
    return anomalia.descargar_historico(lat, lon, anio_fin=anio)


st.header("1. ¿Qué cambió? La lluvia de primavera frente al histórico")
try:
    hist = cargar_historico(lat, lon, ANIO_EVENTO)
    serie_anual = anomalia.agregar_por_anio(hist)
    anom = anomalia.evaluar_anomalia(serie_anual, ANIO_EVENTO)
    curva = anomalia.curva_acumulada(hist, ANIO_EVENTO)
except Exception as e:
    st.warning(f"No se pudo calcular la anomalia: {e}")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lluvia 21-sep a 20-oct", f"{anom.valor:.0f} mm", f"{anom.diferencia_pct:+.0f}% vs promedio")
    c2.metric(f"Promedio {anom.anio_base_ini}-{ANIO_EVENTO - 1}", f"{anom.media:.0f} mm")
    c3.metric("Puesto histórico", f"{anom.puesto}.º de {anom.n_base + 1}")
    c4.metric("Se repite cada", f"~{anom.periodo_retorno:.0f} años")
    st.write(anomalia.describir_anomalia(anom))

    fig_a, ax_a = plt.subplots(figsize=(11, 3.8))
    ax_a.fill_between(curva.index, curva["p10"], curva["p90"], alpha=0.2, label="Rango normal (p10-p90)")
    ax_a.plot(curva.index, curva["promedio"], color="gray", linestyle="--", label="Promedio")
    for a_nom, estilo in (("1997", ":"), ("2015", "-.")):
        if a_nom in curva:
            ax_a.plot(curva.index, curva[a_nom], linestyle=estilo, linewidth=1.2, label=f"{a_nom} (El Niño fuerte)")
    ax_a.plot(curva.index, curva["actual"], color="crimson", linewidth=2.5, label=str(ANIO_EVENTO))
    ax_a.set_ylabel("Lluvia acumulada (mm)")
    ax_a.legend(loc="upper left")
    st.pyplot(fig_a)

    with st.expander("Comparación con años de El Niño fuerte"):
        tabla = anomalia.comparar_analogos(serie_anual, ANIO_EVENTO)
        st.dataframe(
            tabla.rename(columns={"anio": "Año", "valor": "Lluvia (mm)", "puesto": "Puesto",
                                  "n_anios": "Años comparados", "vs_promedio_pct": "% vs promedio"}),
            hide_index=True, width="stretch",
        )
    st.caption(anomalia.NOTA_VALIDEZ)

st.header("2. ¿Qué riesgo trajo? Hongos y ventana de aplicación")

# --- Layout superior: mapa + semaforo ---
col_mapa, col_resumen = st.columns([1, 1])

with col_mapa:
    st.subheader(f"{PUNTO.etiqueta} - {cultivo}")
    if _HAS_MAP:
        m = folium.Map(location=[lat, lon], zoom_start=8, tiles="OpenStreetMap")
        folium.Rectangle(PUNTO.bbox, tooltip="Celda de datos NASA (~50 km)", fill=True,
                         fill_opacity=0.15).add_to(m)
        st_folium(m, height=320, use_container_width=True)
    else:
        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))
    st.caption(
        "Ubicación generalizada al centro de la celda de datos de NASA POWER (~50 km). "
        "No corresponde a un predio ni a un productor real."
    )

with col_resumen:
    st.subheader("Semaforo de los ultimos dias")
    EMOJI = {
        "APLICAR AHORA (riesgo alto, ventana abierta)": "\U0001F7E2",
        "RIESGO sin poder aplicar (vigilar / evaluar dron)": "\U0001F534",
        "Ventana disponible (riesgo bajo)": "\U0001F7E1",
        "Sin accion": "⚪",
    }
    for fecha, row in rec.tail(7)[::-1].iterrows():
        icono = EMOJI.get(row["recomendacion"], "⚪")
        st.write(f"{icono} **{fecha.date()}** - {row['recomendacion']}")

# --- Grafico del evento ---
st.subheader("Lluvia y dias de riesgo")
fig, ax = plt.subplots(figsize=(11, 3.5))
ax.bar(df.index, df["PRECTOTCORR"], width=0.8, label="Lluvia (mm)")
riesgo_dias = rec.index[rec["riesgo"] == 1]
ax.scatter(riesgo_dias, [0] * len(riesgo_dias), color="crimson", marker="v",
           label="Dia de riesgo", zorder=3)
ax.set_ylabel("mm")
ax.legend(loc="upper right")
st.pyplot(fig)

# --- Tabla dia a dia ---
with st.expander("Ver tabla dia a dia"):
    st.dataframe(rec, width="stretch")

st.info(
    "Umbrales de riesgo provisionales (placeholder). Antes de decidir en terreno, "
    "reemplazar por modelos publicados de Botrytis y Monilinia en cerezo "
    "(Biggs y Northover 1988; Tamm 1995; Hort Innovation CY13001). Ver la nota Idea y alcance, seccion 11."
)
