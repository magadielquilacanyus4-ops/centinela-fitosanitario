"""
Centinela Fitosanitario - app Streamlit (frontend MVP).

Selector de comuna/cultivo -> descarga clima (NASA POWER) -> riesgo de infeccion
y ventana de aplicacion (src/risk.py) -> mapa, grafico del evento y semaforo.

Correr local:  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from src.nasa_power import get_power_daily
from src import risk

# streamlit-folium para el mapa (import defensivo: si falta, usamos st.map)
try:
    import folium
    from streamlit_folium import st_folium
    _HAS_MAP = True
except Exception:
    _HAS_MAP = False

# Comunas de O'Higgins (lat, lon aproximados). Agrega las que necesites.
COMUNAS = {
    "Codegua": (-34.03, -70.67),
    "Graneros": (-34.07, -70.73),
    "Mostazal": (-33.98, -70.70),
    "Machali": (-34.18, -70.65),
    "Rancagua": (-34.17, -70.74),
    "Rengo": (-34.41, -70.86),
}

st.set_page_config(page_title="Centinela Fitosanitario", page_icon="\U0001F352", layout="wide")

st.title("\U0001F352\U0001F6F0️ Centinela Fitosanitario")
st.caption(
    "Riesgo de infeccion x viabilidad de aplicacion para huertos de cerezo y manzano "
    "en la Region de O'Higgins, con observaciones de la Tierra de la NASA."
)

# --- Controles ---
with st.sidebar:
    st.header("Parcela")
    comuna = st.selectbox("Comuna", list(COMUNAS))
    cultivo = st.radio("Cultivo", ["Cerezo", "Manzano"])
    st.divider()
    st.header("Periodo")
    inicio = st.date_input("Desde", dt.date(2026, 9, 1))
    fin = st.date_input("Hasta", dt.date(2026, 10, 31))
    st.caption("El evento de primavera 2026 se ve entre septiembre y octubre.")

lat, lon = COMUNAS[comuna]


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

# --- Layout superior: mapa + semaforo ---
col_mapa, col_resumen = st.columns([1, 1])

with col_mapa:
    st.subheader(f"{comuna} - {cultivo}")
    if _HAS_MAP:
        m = folium.Map(location=[lat, lon], zoom_start=11, tiles="OpenStreetMap")
        folium.Marker([lat, lon], tooltip=comuna).add_to(m)
        st_folium(m, height=320, use_container_width=True)
    else:
        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

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
    st.dataframe(rec, use_container_width=True)

st.info(
    "Umbrales de riesgo provisionales (placeholder). Antes de decidir en terreno, "
    "reemplazar por modelos citables (tabla de Mills para venturia; umbrales INIA "
    "para cerezo). Ver la nota Idea y alcance, seccion 11."
)
