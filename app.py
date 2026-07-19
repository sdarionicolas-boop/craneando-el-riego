# app.py
"""
Dashboard de Recomendación de Riego de Precisión - MVP "Craneando el Riego"
"""

import streamlit as pd_st # just import streamlit
import streamlit as st
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.config import SUELO_CONFIG
from core.soil import SoilProfile
from core.crop import CropModel
from core.balance import DailyWaterBalance
from data.weather import WeatherHistory, get_7day_forecast
from data.sensor import get_humidity_data

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Craneando el Riego — Dashboard MVP",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos funcionales sencillos
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-card h3 {
        color: #111111 !important;
        margin: 5px 0px !important;
        font-size: 22px !important;
    }
    .metric-card small {
        color: #555555 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    .metric-card p {
        margin: 5px 0px 0px 0px !important;
        font-size: 13px !important;
    }
    .recommendation-alert {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        color: #856404;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .recommendation-ok {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        color: #155724;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Título y Subtítulo
st.title("🚜 Craneando el Riego — Precisión y Anticipación")
st.subheader("Plataforma de recomendación de riego integrado para cultivos extensivos")

# Cargar Datos Históricos de referencia
weather_loader = WeatherHistory()
try:
    df_history = weather_loader.load_from_excel()
except Exception as e:
    st.error(f"Error al cargar el archivo Excel de referencia: {e}")
    st.stop()

# --- SIDEBAR: CONFIGURACIÓN Y SIMULACIÓN ---
st.sidebar.header("⚙️ Configuración del Lote")

# Selección de Lote (por ahora solo San Martín, con datos placeholder de El Trébol)
lote_selected = st.sidebar.selectbox("Lote Piloto", ["San Martín"])

# Cargar configuración de suelo
soil_profile = SoilProfile.from_config(lote_selected, SUELO_CONFIG)
au_corregida = soil_profile.calculate_au_corregida()
techo = soil_profile.techo_sistema

# Configuración de fecha de siembra
default_siembra = datetime.date(2025, 9, 17)
siembra_date = st.sidebar.date_input("Fecha de Siembra / Emergencia", default_siembra)
crop_model = CropModel(siembra_date)

# Configuración agronómica interactiva
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Criterio de Riego")
cc_target_pct = st.sidebar.slider("% CC Objetivo a cubrir", 70, 100, 100, help="Estrategia ofensiva (100%) vs conservadora (deja margen para lluvias)")
infiltracion_limit = st.sidebar.number_input("Infiltración máx. suelo (mm/riego)", 5.0, 50.0, soil_profile.infiltracion_max, step=5.0)
st.sidebar.caption("⚠️ *Infiltración de 15.0 mm: Valor estimado por bibliografía para suelos Vertisoles arcillosos de San Martín (sin medición en campo).*")
caudal_pivote = st.sidebar.number_input("Caudal Pivote (mm/hora)", 0.5, 5.0, soil_profile.caudal_pivote, step=0.1)

# Simulación de la fecha actual
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Modo Demo — Campaña El Trébol 2025-26")
st.sidebar.warning(
    "⚠️ **Nota de Lote**: Las constantes de suelo y clima corresponden a **El Trébol 2025-26** "
    "para validar la lógica matemática del motor. Los datos reales de San Martín se aplicarán apenas "
    "lleguen del laboratorio."
)
st.sidebar.markdown(
    "Puedes desplazar la fecha de evaluación para probar la respuesta del sistema:"
)
min_date = df_history["fecha"].min()
max_date = df_history["fecha"].max()
eval_date = st.sidebar.slider("Fecha de Evaluación", min_date, max_date, datetime.date(2025, 12, 25))

# --- PROCESAMIENTO DEL BALANCE HÍDRICO ---
# Filtrar histórico hasta la fecha de evaluación
df_past = df_history[df_history["fecha"] <= eval_date].copy()

# Recalcular balance diario hasta hoy basándose en la configuración
au_riego_prev = 90.0
au_secano_prev = 90.0
engine = DailyWaterBalance(techo_sistema=techo)

au_riego_list = []
au_secano_list = []
etc_list = []
lluvia_ef_list = []
kc_list = []
stage_list = []

for idx, row in df_past.iterrows():
    # Obtener Kc y etapa fenológica para este día
    kc, stage = crop_model.get_kc_and_stage(row["fecha"])
    
    # Calcular balance
    res = engine.calculate_next_day(
        au_prev=au_riego_prev,
        au_secano_prev=au_secano_prev,
        riego=row["riego"],
        lluvia=row["lluvia"],
        etp=row["etp"],
        kc=kc,
        coef_override=row["coef_lluvia"]
    )
    
    au_riego_list.append(res["au_riego"])
    au_secano_list.append(res["au_secano"])
    etc_list.append(res["etc"])
    lluvia_ef_list.append(res["lluvia_ef"])
    kc_list.append(kc)
    stage_list.append(stage)
    
    au_riego_prev = res["au_riego"]
    au_secano_prev = res["au_secano"]

df_past["au_riego"] = au_riego_list
df_past["au_secano"] = au_secano_list
df_past["etc"] = etc_list
df_past["lluvia_ef"] = lluvia_ef_list
df_past["kc"] = kc_list
df_past["stage"] = stage_list
df_past["umbral"] = [crop_model.get_umbral_mm(d) for d in df_past["fecha"]]

# --- CÁLCULO Y CONVERSIÓN DE HUMEDAD DEL SENSOR (CALIBRACIÓN) ---
df_sensor_raw = get_humidity_data(lote_selected, min_date, eval_date)
au_sensor_mm_list = []
for idx, row in df_sensor_raw.iterrows():
    # Convertir usando la función unificada en SoilProfile para evitar duplicaciones
    vwc_list = [row["humedad_0_20"], row["humedad_20_40"], row["humedad_40_80"]]
    au_sensor_mm = soil_profile.calculate_au_from_vwc(vwc_list)
    au_sensor_mm_list.append(au_sensor_mm)
df_sensor_raw["au_sensor_mm"] = au_sensor_mm_list
df_past = df_past.merge(df_sensor_raw[["fecha", "au_sensor_mm"]], on="fecha", how="left")

# --- CÁLCULO DE PROYECCIÓN A 7 DÍAS ---
# Obtener el pronóstico climático para los próximos 7 días
forecast_data = get_7day_forecast()
proj_records = []
proj_au_riego = au_riego_prev
proj_au_secano = au_secano_prev

for i, f in enumerate(forecast_data):
    f_date = eval_date + datetime.timedelta(days=i+1)
    kc, stage = crop_model.get_kc_and_stage(f_date)
    umbral = crop_model.get_umbral_mm(f_date)
    
    # Simular proyección sin riegos planificados para ver cuándo cruza el umbral
    res = engine.calculate_next_day(
        au_prev=proj_au_riego,
        au_secano_prev=proj_au_secano,
        riego=0.0,
        lluvia=f["lluvia"],
        etp=f["etp"],
        kc=kc
    )
    
    proj_records.append({
        "fecha": f_date,
        "lluvia": f["lluvia"],
        "riego": 0.0,
        "etp": f["etp"],
        "kc": kc,
        "stage": stage,
        "etc": res["etc"],
        "lluvia_ef": res["lluvia_ef"],
        "au_riego": res["au_riego"],
        "au_secano": res["au_secano"],
        "umbral": umbral
    })
    
    proj_au_riego = res["au_riego"]
    proj_au_secano = res["au_secano"]

df_proj = pd.DataFrame(proj_records)
df_total = pd.concat([df_past, df_proj], ignore_index=True)

# --- RECOMENDACIÓN DE RIEGO ---
st.markdown("### 💡 Recomendación de Riego Actual")

current_au = df_past["au_riego"].iloc[-1]
current_stage = df_past["stage"].iloc[-1]
current_umbral = df_past["umbral"].iloc[-1]

# Buscar si cruzará el umbral en la proyección de 7 días
crosses_threshold = False
cross_date = None
cross_au = None

for idx, row in df_proj.iterrows():
    if row["au_riego"] < row["umbral"]:
        crosses_threshold = True
        cross_date = row["fecha"]
        cross_au = row["au_riego"]
        break

# Calcular requerimiento de riego
# Deficit para llevar al % CC objetivo
au_target = au_corregida * (cc_target_pct / 100.0)
deficit = au_target - current_au

if deficit > 0:
    lamina_rec = min(deficit, infiltracion_limit)
    tiempo_horas = lamina_rec / caudal_pivote
else:
    lamina_rec = 0.0
    tiempo_horas = 0.0

if current_au < current_umbral:
    st.markdown(
        f'<div class="recommendation-alert">'
        f'<strong>⚠️ ALERTA: EL CULTIVO ESTÁ BAJO ESTRÉS HÍDRICO HACE {current_umbral - current_au:.1f} mm.</strong><br>'
        f'Se recomienda iniciar riego **DE INMEDIATO**.<br>'
        f'- **Lámina sugerida**: {lamina_rec:.1f} mm (limitada por capacidad de infiltración de {infiltracion_limit} mm)<br>'
        f'- **Tiempo de operación estimado**: {tiempo_horas:.1f} horas de pivote'
        f'</div>',
        unsafe_allow_html=True
    )
elif crosses_threshold:
    dias_restantes = (cross_date - eval_date).days
    st.markdown(
        f'<div class="recommendation-alert">'
        f'<strong>⏳ ANTICIPACIÓN: Se proyecta cruce del umbral en {dias_restantes} días ({cross_date.strftime("%d/%m")}).</strong><br>'
        f'Planificar riego preventivo para evitar estrés (AU proyectado caerá a {cross_au:.1f} mm).<br>'
        f'- **Lámina preventiva recomendada**: {lamina_rec:.1f} mm<br>'
        f'- **Tiempo de operación estimado**: {tiempo_horas:.1f} horas de pivote'
        f'</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f'<div class="recommendation-ok">'
        f'<strong>✅ ESTADO ÓPTIMO: No se prevé estrés hídrico en los próximos 7 días.</strong><br>'
        f'El balance hídrico proyectado permanece sobre el umbral de estrés ({current_umbral:.1f} mm). '
        f'Nivel de Agua Útil actual: {current_au:.1f} mm ({current_au/au_corregida*100:.1f}% del AU corregida).'
        f'</div>',
        unsafe_allow_html=True
    )

# --- EXPANDER PARA ALERTA TELEGRAM ---
from alerts.telegram import check_and_send_alerts
if crosses_threshold or current_au < current_umbral:
    with st.expander("📲 Simulación de Alerta Telegram"):
        st.markdown("**Mensaje de Alerta que se enviaría a Telegram:**")
        dias = (cross_date - eval_date).days if cross_date else 0
        mensaje_test = (
            f"⚠️ **ALERTA RIEGO CRÍTICA - LOTE {lote_selected.upper()}**\n\n"
            f"Se proyecta que el nivel de Agua Útil cruzará el umbral de estrés en **{dias} días** ({cross_date.strftime('%d/%m') if cross_date else eval_date.strftime('%d/%m')}).\n\n"
            f"📈 **Valores Proyectados:**\n"
            f"- Agua Útil Proyectada: {cross_au if cross_au else current_au:.1f} mm\n"
            f"- Umbral de Estrés: {current_umbral:.1f} mm\n\n"
            f"💧 **Recomendación Agronómica:**\n"
            f"- Lámina sugerida: **{lamina_rec:.1f} mm**\n"
            f"- Tiempo estimado de pivote: **{tiempo_horas:.1f} horas**\n\n"
            f"_Alerta generada automáticamente por Craneando el Riego v1.0._"
        )
        st.code(mensaje_test, language="markdown")
        
        if st.button("Disparar alerta de prueba (Telegram)"):
            import os
            if not os.environ.get("TELEGRAM_BOT_TOKEN") or not os.environ.get("TELEGRAM_CHAT_ID"):
                st.warning("⚠️ Variables de entorno `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` no configuradas. El envío real fue omitido, pero se simuló en los logs del servidor (revisa la consola).")
            
            success_tg = check_and_send_alerts(
                lote=lote_selected,
                df_proj=df_proj,
                eval_date=eval_date,
                lamina_rec=lamina_rec,
                tiempo_horas=tiempo_horas
            )
            if success_tg:
                st.success("✅ Alerta enviada exitosamente a Telegram.")
            else:
                st.info("ℹ️ Alerta simulada en la consola de desarrollo.")


# --- PANEL DE MÉTRICAS ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f'<div class="metric-card">'
        f'<small>Agua Útil Actual</small>'
        f'<h3>{current_au:.1f} mm</h3>'
        f'<p style="color: {"green" if current_au >= current_umbral else "red"}">'
        f'{current_au/au_corregida*100:.1f}% de AU corregida</p>'
        f'</div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f'<div class="metric-card">'
        f'<small>Umbral Crítico (Etapa)</small>'
        f'<h3>{current_umbral:.1f} mm</h3>'
        f'<p style="color: gray">Estado: {current_stage}</p>'
        f'</div>',
        unsafe_allow_html=True
    )
with col3:
    st.markdown(
        f'<div class="metric-card">'
        f'<small>Próxima Lluvia (7d)</small>'
        f'<h3>{df_proj["lluvia"].sum():.1f} mm</h3>'
        f'<p style="color: blue">Pronóstico acumulado</p>'
        f'</div>',
        unsafe_allow_html=True
    )
with col4:
    st.markdown(
        f'<div class="metric-card">'
        f'<small>Evapotranspiración (Últ. 7d)</small>'
        f'<h3>{df_past["etc"].iloc[-7:].sum():.1f} mm</h3>'
        f'<p style="color: orange">ETc acumulada cultivo</p>'
        f'</div>',
        unsafe_allow_html=True
    )

# --- VISUALIZACIÓN GRÁFICA ---
st.markdown("### 📈 Gráfico de Balance Hídrico Proyectado")

# Crear figura de Plotly para el balance hídrico
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Agregar sombreado para el área de estrés (bajo el umbral)
# Creamos la serie del umbral
fig.add_trace(
    go.Scatter(
        x=df_total["fecha"],
        y=df_total["umbral"],
        name="Umbral de Estrés",
        line=dict(color="red", width=2, dash="dash"),
    )
)

# Línea de AU con Riego (Histórico + Proyección)
# Separar histórico de proyección visualmente
df_past_plot = df_total[df_total["fecha"] <= eval_date]
df_proj_plot = df_total[df_total["fecha"] >= eval_date]

fig.add_trace(
    go.Scatter(
        x=df_past_plot["fecha"],
        y=df_past_plot["au_riego"],
        name="Agua Útil (Riego aplicado)",
        line=dict(color="#1f77b4", width=3),
    )
)

fig.add_trace(
    go.Scatter(
        x=df_proj_plot["fecha"],
        y=df_proj_plot["au_riego"],
        name="Agua Útil (Proyección 7d)",
        line=dict(color="#1f77b4", width=3, dash="dot"),
        showlegend=False
    )
)

# Línea de AU Secano (Testigo)
fig.add_trace(
    go.Scatter(
        x=df_total["fecha"],
        y=df_total["au_secano"],
        name="Agua Útil (Secano - Testigo)",
        line=dict(color="orange", width=1.5, dash="dashdot"),
    )
)

# Barras de Lluvia y Riego en el eje secundario
df_past_rain = df_past_plot[df_past_plot["lluvia"] > 0]
df_past_irr = df_past_plot[df_past_plot["riego"] > 0]
df_proj_rain = df_proj_plot[df_proj_plot["lluvia"] > 0]

if not df_past_rain.empty:
    fig.add_trace(
        go.Bar(
            x=df_past_rain["fecha"],
            y=df_past_rain["lluvia"],
            name="Lluvia (mm)",
            marker_color="blue",
            opacity=0.6,
            width=86400000 * 0.8 # Ancho de 1 día
        ),
        secondary_y=True
    )
    
if not df_past_irr.empty:
    fig.add_trace(
        go.Bar(
            x=df_past_irr["fecha"],
            y=df_past_irr["riego"],
            name="Riego aplicado (mm)",
            marker_color="green",
            opacity=0.6,
            width=86400000 * 0.8
        ),
        secondary_y=True
    )

if not df_proj_rain.empty:
    fig.add_trace(
        go.Bar(
            x=df_proj_rain["fecha"],
            y=df_proj_rain["lluvia"],
            name="Lluvia Pronóstico (mm)",
            marker_color="lightblue",
            opacity=0.6,
            width=86400000 * 0.8
        ),
        secondary_y=True
    )

# Línea vertical indicando la fecha de evaluación
fig.add_vline(x=eval_date, line_width=2, line_dash="solid", line_color="gray")
fig.add_annotation(x=eval_date, y=techo, text="Hoy (Evaluación)", showarrow=True, arrowhead=1)

fig.update_layout(
    title=f"Evolución de Agua Útil - Lote {lote_selected} (Siembra: {siembra_date.strftime('%d/%m/%Y')})",
    xaxis_title="Fecha",
    yaxis_title="Agua Útil en Suelo (mm)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=80, b=40),
    height=500
)

fig.update_yaxes(title_text="Lluvia / Riego (mm)", secondary_y=True, range=[100, 0]) # Invertido para que caiga desde arriba
fig.update_yaxes(range=[0, techo + 10], secondary_y=False)

st.plotly_chart(fig, use_container_width=True)


# --- CLIMA EN TIEMPO REAL (DGHyOS) ---
st.markdown("### 🌦️ Ingesta de Clima en Tiempo Real (Red de Estaciones DGHyOS)")
st.markdown(
    "Esta sección muestra las mediciones reales de precipitación y evapotranspiración (ETo) obtenidas "
    "en tiempo real desde la red de estaciones meteorológicas del Gobierno de Entre Ríos (DGHyOS), "
    "utilizadas para alimentar el motor en producción."
)

with st.spinner("Conectando con la red oficial de estaciones de Entre Ríos..."):
    from data.weather import get_realtime_weather_last_7_days
    realtime_data, active_weather_source = get_realtime_weather_last_7_days()

# Mostrar el origen de la fuente climática con un banner informativo
st.success(f"📡 **Fuente climática activa**: {active_weather_source}")

# Crear columnas para el clima real
col_rt_stats, col_rt_table = st.columns([2, 2])

with col_rt_stats:
    total_rt_rain = sum(d["lluvia"] for d in realtime_data)
    total_rt_et = sum(d["etp"] for d in realtime_data)
    
    st.markdown(
        f'<div class="metric-card" style="background-color: #ffffff; border-left: 5px solid #2980b9;">'
        f'<small>Lluvia Real Acumulada (Últimos 7d)</small>'
        f'<h3 style="color: #2980b9 !important; font-weight: bold !important;">{total_rt_rain:.1f} mm</h3>'
        f'<p style="color: #555555 !important;">Registrado en estación meteorológica</p>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        f'<div class="metric-card" style="background-color: #ffffff; border-left: 5px solid #d35400;">'
        f'<small>ETo Real Acumulada (Últimos 7d)</small>'
        f'<h3 style="color: #d35400 !important; font-weight: bold !important;">{total_rt_et:.1f} mm</h3>'
        f'<p style="color: #555555 !important;">Evapotranspiración de referencia</p>'
        f'</div>',
        unsafe_allow_html=True
    )

with col_rt_table:
    # Convertir a DataFrame para visualización
    df_rt = pd.DataFrame(realtime_data)
    df_rt["Fecha"] = df_rt["fecha"].apply(lambda d: d.strftime('%d/%m/%Y'))
    df_rt = df_rt.rename(columns={"lluvia": "Lluvia (mm)", "etp": "ETo (mm)"})
    st.dataframe(df_rt[["Fecha", "Lluvia (mm)", "ETo (mm)"]], hide_index=True, use_container_width=True)

st.markdown("---")


# --- SECCIÓN DE CALIBRACIÓN: MODELO VS SENSOR ---
st.markdown("### 🔍 Calibración: Modelo de Balance vs Sensor Real")
st.markdown(
    "Este gráfico contrasta el nivel de **Agua Útil calculado** por el motor de balance hídrico "
    "contra el **Agua Útil medida empíricamente** por el sensor de humedad de suelo (Nuevas Sondas de Prueba). "
    "Las lecturas volumétricas (% VWC) de los 3 horizontes se convirtieron a milímetros equivalentes de AU "
    "para permitir una comparación directa y validar la calibración del modelo. "
    "*Nota: Se descartó el uso de AGSENSE/Valley ya que el proveedor solo brinda monitoreo operativo mecánico del pivote, no lecturas de humedad.*"
)

fig_calib = go.Figure()

# Línea de AU Riego (Modelo)
fig_calib.add_trace(
    go.Scatter(
        x=df_past_plot["fecha"],
        y=df_past_plot["au_riego"],
        name="AU Calculada (Modelo)",
        line=dict(color="#1f77b4", width=3.0),
    )
)

# Línea de AU medida por Sensor
fig_calib.add_trace(
    go.Scatter(
        x=df_past_plot["fecha"],
        y=df_past_plot["au_sensor_mm"],
        name="AU Medida (Sensor AGSENSE)",
        line=dict(color="#2ca02c", width=2.0, dash="dash"),
        mode="lines+markers"
    )
)

# Umbral de Estrés
fig_calib.add_trace(
    go.Scatter(
        x=df_past_plot["fecha"],
        y=df_past_plot["umbral"],
        name="Umbral de Estrés",
        line=dict(color="red", width=1.5, dash="dot"),
    )
)

fig_calib.update_layout(
    title="Calibración Empírica de Agua Útil en el Suelo (Histórico)",
    xaxis_title="Fecha",
    yaxis_title="Agua Útil en Suelo (mm)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=60, b=40),
    height=400
)
fig_calib.update_yaxes(range=[0, techo + 10])

st.plotly_chart(fig_calib, use_container_width=True)

st.info(
    "💡 **Nota de Ingesta del Sensor**: Los datos de humedad de suelo son simulados en esta fase (mock/stub) "
    "con el fin de ilustrar la interfaz de validación. La integración de AGSENSE/Valley se descartó dado que "
    "el proveedor solo brinda monitoreo operativo del pivote (motores, presión, caudal) y no lecturas de humedad. "
    "La conexión final requiere configurar las nuevas sondas en prueba de esta campaña."
)


# --- SECCIONES COMPLEMENTARIAS: KILIMO CLOSE & NDVI VALIDATION ---
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📊 Balance Acumulado (Cierre de Campaña)")
    st.markdown(
        "*Resumen acumulado del lote estilo Kilimo (ingresos de agua vs egresos de transpiración)*"
    )
    
    # Calcular acumulados históricos
    total_et = df_past["etc"].sum()
    total_rain_ef = df_past["lluvia_ef"].sum()
    total_riego = df_past["riego"].sum()
    initial_au = df_past["au_riego"].iloc[0]
    final_au = df_past["au_riego"].iloc[-1]
    
    # Gráfico de barras de balance de masa
    fig_balance = go.Figure()
    fig_balance.add_trace(go.Bar(
        x=["Egreso: Evapotranspiración (ETc)", "Ingreso: Lluvia Efectiva", "Ingreso: Riego Aplicado"],
        y=[total_et, total_rain_ef, total_riego],
        marker_color=["#e74c3c", "#3498db", "#2ecc71"],
        width=0.5
    ))
    
    fig_balance.update_layout(
        yaxis_title="Agua Acumulada (mm)",
        margin=dict(l=40, r=40, t=20, b=20),
        height=320
    )
    
    st.plotly_chart(fig_balance, use_container_width=True)

with col_right:
    st.markdown("### 🛰️ Validación Cruzada Kc (Teórico vs NDVI)")
    st.markdown(
        "*Comparativa del Kc teórico (planilla) contra el calculado por índice NDVI de vigor vegetativo*"
    )
    
    # Mostrar la curva Kc teórica
    df_kc = df_past.copy()
    
    fig_kc = go.Figure()
    fig_kc.add_trace(go.Scatter(
        x=df_kc["fecha"],
        y=df_kc["kc"],
        name="Kc Teórico (Planilla Mariano)",
        line=dict(color="#2980b9", width=2.5)
    ))
    
    # NDVI Kc - Marcado como MOCK / PENDIENTE
    # Simular una curva NDVI aproximada que sigue la forma del Kc pero con algo de ruido y desfase
    sim_ndvi_kc = df_kc["kc"].values * 0.95 + np.random.normal(0, 0.03, len(df_kc))
    sim_ndvi_kc = np.clip(sim_ndvi_kc, 0.05, 1.15)
    
    fig_kc.add_trace(go.Scatter(
        x=df_kc["fecha"],
        y=sim_ndvi_kc,
        name="Kc NDVI (Simulado - Pendiente GEE)",
        line=dict(color="#27ae60", width=1.5, dash="dash"),
    ))
    
    fig_kc.update_layout(
        yaxis_title="Valor Coeficiente Kc",
        margin=dict(l=40, r=40, t=20, b=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_kc, use_container_width=True)
    
    st.info(
        "💡 **Nota de Ingesta NDVI**: La curva verde es simulada para demostración visual de validación de desvíos. "
        "La integración con Google Earth Engine (GEE) o importación de CSV satelital está marcada como pendiente en la Fase v2."
    )


# --- ROADMAP VISUAL ---
st.markdown("---")
st.markdown("### 🗺️ Roadmap de Fases — Expectativas del MVP")
st.markdown(
    "Para alinear las expectativas del productor respecto a la experiencia previa con Kilimo, "
    "detallamos el alcance técnico y las próximas integraciones del sistema."
)

roadmap_cols = st.columns(3)
with roadmap_cols[0]:
    st.markdown("#### **Fase 1: MVP (Actual)**")
    st.markdown(
        "- **Estado**: Ejecución / En curso\n"
        "- Motor físico de balance diario exacto.\n"
        "- Recomendación de riego lote completo.\n"
        "- Integración de clima local y pronóstico 7d.\n"
        "- Sensores de humedad del suelo vía mockup."
    )
with roadmap_cols[1]:
    st.markdown("#### **Fase 2: Satélite y Sensores Reales**")
    st.markdown(
        "- **Estado**: Planificado (Campaña 26-27)\n"
        "- Conexión API real Valley/AGSENSE.\n"
        "- Ingesta automatizada NDVI vía Google Earth Engine.\n"
        "- Reemplazo automático del Kc de tabla por Kc basal satelital."
    )
with roadmap_cols[2]:
    st.markdown("#### **Fase 3: Multi-Zona / Pivote Seccionado**")
    st.markdown(
        "- **Estado**: Backlog v2\n"
        "- Segmentación espacial dentro del lote (por tramos/ángulos de pivote).\n"
        "- Prescripciones de riego variables (VRI).\n"
        "- Integración directa para comando del pivote."
    )
