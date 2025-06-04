# -*- coding: utf-8 -*-
"""Streamlit app para comparar dos videos sincronizados con un único indicador
   de probabilidad de error procedente de un Excel (columna Z2:Z1140).

   1. Ajusta las rutas de los archivos en las variables VIDEO1_PATH,
      VIDEO2_PATH y EXCEL_PATH.
   2. Ejecuta: streamlit run app.py
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# RUTAS A TUS ARCHIVOS -------------------------------------------------------
# ---------------------------------------------------------------------------
VIDEO1_PATH = Path("potencia.mp4")  # Primer vídeo
VIDEO2_PATH = Path("presion de alta.mp4")  # Segundo vídeo
EXCEL_PATH = Path("salidas_reales_vs_predichas_directo.xlsx")   # Excel con la columna Z

# ---------------------------------------------------------------------------
# CARGAR DATOS --------------------------------------------------------------
# ---------------------------------------------------------------------------
# 1) Probabilidades (Z2:Z1140) ------------------------------------------------
values = (
    pd.read_excel(EXCEL_PATH, usecols="Z", header=None, skiprows=1, nrows=1139)
      .squeeze("columns")
      .fillna(0)
      .round(0)
      .astype(int)
      .tolist()
)
values_json = json.dumps(values, ensure_ascii=False)

# 2) Codificar vídeos en base64 ------------------------------------------------
#    Esto permite servirlos embebidos en la propia página sin rutas externas.

def to_data_uri(path: Path) -> str:
    data = path.read_bytes()
    b64  = base64.b64encode(data).decode()
    return f"data:video/mp4;base64,{b64}"

video1_uri = to_data_uri(VIDEO1_PATH)
video2_uri = to_data_uri(VIDEO2_PATH)

# ---------------------------------------------------------------------------
# CONFIG DE LA PÁGINA --------------------------------------------------------
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Gemelo Digital en Modo Supervisión para la Detección de Fallos", layout="wide")

st.title("Comparador de Videos")

# ---------------------------------------------------------------------------
# HTML + JS ------------------------------------------------------------------
# ---------------------------------------------------------------------------
html_code = f"""
<style>
.container {{
  display: flex;
  flex-direction: row;
  gap: 24px;
}}
.videos {{
  flex: 1 1 auto;
  max-width: 700px;
}}

.controls {{
  text-align: center;
  margin-bottom: 12px;
}}
.controls button {{
  font-size: 28px;
  margin: 0 8px;
  cursor: pointer;
  background: none;
  border: none;
}}

/* ---------- wrapper con relación 16:9 y overflow oculto ---------- */
.video-box {{
  position: relative;
  width: 100%;
  padding-top: 56.25%;   /* 16:9 */
  overflow: hidden;
  margin-bottom: 8px;
}}
.video-box video {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;     /* rellena el cuadro */
  
  /* ---------- recorte de los bordes negros ---------- */
  /* top | right | bottom | left                       */
  clip-path: inset(0% 6% 9% 7%);
}}
/* --------------------------------------------------------------- */

#probBox {{
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 24px 12px;
  font-size: 26px;
  min-width: 260px;
  text-align: center;
}}
#bar {{ width: 100%; }}
</style>

<div class="controls">
  <button onclick="skipBoth(-10)" title="Rebobinar rápido">⏪</button>
  <button onclick="skipBoth(-5)"  title="Retroceder 5 s">◀️</button>
  <button onclick="togglePlay()"   title="Play/Pause">⏯️</button>
  <button onclick="skipBoth(5)"   title="Avanzar 5 s">▶️</button>
  <button onclick="skipBoth(10)"  title="Avanzar rápido">⏩</button>
</div>

<div class="container">
  <div class="videos">
    <input id="bar" type="range" min="0" value="0" step="0.05"
           onchange="seekBoth(this.value)">

    <!--  envolvemos cada vídeo para poder recortarlo  -->
    <div class="video-box">
      <video id="vid1" src="{video1_uri}" preload="metadata"></video>
    </div>
    <div class="video-box">
      <video id="vid2" src="{video2_uri}" preload="metadata"></video>
    </div>
  </div>

  <div>
    <div id="probBox">Probabilidad de Error: -- %</div>
  </div>
</div>

<script>
// ------------------------------------------------------------------
//  JS igual que antes: los IDs no cambian, solo la parte visual
// ------------------------------------------------------------------
const vid1   = document.getElementById('vid1');
const vid2   = document.getElementById('vid2');
const bar    = document.getElementById('bar');
const values = {values_json};
let metaReady = false;

function syncTime() {{ vid2.currentTime = vid1.currentTime; }}

function updateBar() {{
  bar.value = vid1.currentTime;
  updateProb(vid1.currentTime);
}}

function updateProb(t) {{
  if (!metaReady) return;
  const idx  = Math.min(values.length - 1,
                        Math.floor(t / vid1.duration * (values.length - 1)));
  document.getElementById('probBox').textContent =
        `Probabilidad de Error: ${{values[idx]}} %`;
}}

function skipBoth(sec) {{
  const newTime = Math.max(0,
                    Math.min(vid1.duration, vid1.currentTime + sec));
  vid1.currentTime = newTime;
  syncTime();
  updateBar();
}}

function seekBoth(val) {{
  vid1.currentTime = val;
  syncTime();
  updateBar();
}}

function togglePlay() {{
  if (vid1.paused) {{ vid1.play(); vid2.play(); }}
  else             {{ vid1.pause(); vid2.pause(); }}
}}

vid1.addEventListener('loadedmetadata', () => {{
  bar.max = vid1.duration;
  metaReady = true;
  updateProb(0);
}});
vid1.addEventListener('timeupdate', updateBar);
vid1.addEventListener('seeked', updateBar);

vid2.addEventListener('play',  () => {{ if (vid1.paused) vid1.play(); }});
vid2.addEventListener('pause', () => {{ if (!vid1.paused) vid1.pause(); }});
</script>
"""

# ---------------------------------------------------------------------------
# RENDER --------------------------------------------------------------------
# ---------------------------------------------------------------------------
st.components.v1.html(html_code, height=900, scrolling=False)
