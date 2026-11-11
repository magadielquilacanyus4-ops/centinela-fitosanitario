"""Prueba de humo de app.py con datos sinteticos (sin internet). Requiere streamlit.
Correr:  python tests/probar_app_sintetico.py
"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT))
from streamlit.testing.v1 import AppTest
import src.nasa_power as npw, src.anomalia as an

def falso(lat, lon, start, end, params=None):
    rng = np.random.default_rng(abs(hash((round(lat,2), start))) % (2**32))
    idx = pd.date_range(start, end, freq="D")
    n = len(idx)
    df = pd.DataFrame({
        "T2M": 12 + 8*np.sin((idx.dayofyear-30)/365*2*np.pi) + rng.normal(0,1.5,n),
        "RH2M": rng.uniform(55,98,n),
        "PRECTOTCORR": rng.gamma(0.4,4.0,n)*(rng.random(n)<0.25),
    }, index=idx)
    df["T2M_MAX"]=df["T2M"]+6; df["T2M_MIN"]=df["T2M"]-6
    m = (idx.year==2026)&(idx.month.isin([9,10]))
    df.loc[m,"PRECTOTCORR"] *= 4          # evento sintetico
    cols = params or ["T2M","T2M_MAX","T2M_MIN","RH2M","PRECTOTCORR"]
    return df[cols]

npw.get_power_daily = falso
an.get_power_daily = falso
an.CACHE_DIR = pathlib.Path("/tmp/cache_test")

at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
print("excepciones:", [e.value for e in at.exception])
print("errores:", [e.value for e in at.error])
print("warnings:", [w.value for w in at.warning])
print("headers:", [h.value for h in at.header])
print("metricas:", [(m.label, m.value, m.delta) for m in at.metric])
print("texto anomalia:", [m.value for m in at.markdown if "acumulada" in m.value][:1])
print("sidebar cultivo:", [m.value for m in at.sidebar.markdown])
print("radios:", [r.label for r in at.sidebar.radio])
# cambiar de comuna
at.sidebar.selectbox[0].select("Rengo").run()
print("tras cambiar a Rengo -> excepciones:", [e.value for e in at.exception], "| metricas:", [(m.label, m.value) for m in at.metric][:2])
