import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página web
st.set_page_config(page_title="KPI PaintShop Web", layout="wide", initial_sidebar_state="expanded")

# --- ESTILOS PERSONALIZADOS (Diseño Taller Premium) ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #1E3A8A; }
    div[data-testid="stMetricLabel"] { font-size: 14px; font-weight: 600; color: #475569; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Sistema de Rentabilidad y KPIs - Taller de Pintura")
st.caption("Aplicación web operativa para el control de márgenes, consumos y eficiencia de operarios.")

# --- BASE DE DATOS LOCAL SIMULADA (Para que sea 100% operativo al arrancar) ---
# En producción, esto se guarda en un archivo .csv o una base de datos en la nube.
if 'db_taller' not in st.session_state:
    datos_iniciales = {
        "Mes": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"],
        "Horas_Facturadas": [310, 330, 380, 340, 400, 420],
        "Horas_Reales": [290, 300, 320, 310, 330, 340],
        "Paneles_Pintados": [220, 245, 290, 250, 310, 325],
        "Venta_Pintura": [13800.0, 14900.0, 16800.0, 15200.0, 18100.0, 18900.0],
        "Coste_Material": [4900.0, 5100.0, 5500.0, 5250.0, 5800.0, 5950.0]
    }
    st.session_state.db_taller = pd.DataFrame(datos_iniciales)

df = st.session_state.db_taller

# --- FORMULARIO LATERAL: INTRODUCCIÓN DE DATOS ---
st.sidebar.header("📝 Registro de Datos Mensuales")
st.sidebar.markdown("Introduce los datos de cierre del mes para actualizar los gráficos.")

with st.sidebar.form("formulario_taller"):
    mes_input = st.selectbox("Selecciona el Mes", [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ])
    h_fact = st.number_input("Horas Facturadas de Pintura (Baremo)", min_value=0, step=1, value=300)
    h_real = st.number_input("Horas Reales de Presencia (Pintores)", min_value=1, step=1, value=300)
    paneles = st.number_input("Total Paneles/Piezas Pintadas", min_value=1, step=1, value=200)
    venta = st.number_input("Venta Total Facturada en Pintura (€)", min_value=0.0, step=100.0, value=15000.0)
    coste = st.number_input("Coste Total de Material Consumido (€)", min_value=0.0, step=100.0, value=5000.0)
    
    guardar = st.form_submit_button("💾 Guardar y Calcular KPIs")

# Procesar los datos del formulario
if guardar:
    # Si el mes ya existe, lo actualiza, si no, lo añade
    if mes_input in df['Mes'].values:
        df.loc[df['Mes'] == mes_input, ["Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material"]] = [h_fact, h_real, paneles, venta, coste]
    else:
        nueva_fila = pd.DataFrame([[mes_input, h_fact, h_real, paneles, venta, coste]], columns=df.columns)
        df = pd.concat([df, nueva_fila], ignore_index=True)
    
    st.session_state.db_taller = df
    st.sidebar.success(f"¡Datos de {mes_input} procesados!")

# --- CÁLCULO DE KPIS CONSOLIDADOS ---
total_venta = df['Venta_Pintura'].sum()
total_coste = df['Coste_Material'].sum()
total_paneles = df['Paneles_Pintados'].sum()
total_h_fact = df['Horas_Facturadas'].sum()
total_h_real = df['Horas_Reales'].sum()

margen_global = ((total_venta - total_coste) / total_venta) * 100 if total_venta > 0 else 0
coste_panel_global = total_coste / total_paneles if total_paneles > 0 else 0
eficiencia_global = (total_h_fact / total_h_real) * 100 if total_h_real > 0 else 0

# Enriquecer el dataframe con columnas calculadas para las tablas
df['Margen Bruto (%)'] = ((df['Venta_Pintura'] - df['Coste_Material']) / df['Venta_Pintura'] * 100).round(1)
df['Coste por Panel (€)'] = (df['Coste_Material'] / df['Paneles_Pintados']).round(2)
df['Eficiencia Pintores (%)'] = (df['Horas_Facturadas'] / df['Horas_Reales'] * 100).round(1)

# --- VISTA 1: TARJETAS DE INDICADORES (KPI CARDS) ---
st.markdown("### 🏆 Rendimiento Acumulado del Año")
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric(label="MARGEN BRUTO PINTURA", value=f"{margen_global:.1f} %", delta="Target óptimo: > 60%")
with kpi2:
    st.metric(label="COSTE MEDIO / PANEL", value=f"{coste_panel_global:.2f} €", delta="Target óptimo: < 35 €", delta_color="inverse")
with kpi3:
    st.metric(label="EFICIENCIA OPERARIOS", value=f"{eficiencia_global:.1f} %", delta="Target óptimo: > 100%")

st.markdown("---")

# --- VISTA 2: GRÁFICOS INTERACTIVOS ---
st.markdown("### 📈 Análisis de Tendencias e Historial")
g1, g2 = st.columns(2)

with g1:
    st.subheader("Brecha Financiera: Venta vs Coste de Material")
    fig_fin = px.bar(df, x="Mes", y=["Venta_Pintura", "Coste_Material"], 
                     barmode="group", labels={"value": "Euros (€)", "variable": "Concepto"},
                     color_discrete_sequence=["#1E3A8A", "#EF4444"])
    st.plotly_chart(fig_fin, use_container_width=True)

with g2:
    st.subheader("Evolución del Coste por Panel")
    fig_coste = px.line(df, x="Mes", y="Coste por Panel (€)", markers=True,
                        color_discrete_sequence=["#10B981"])
    # Línea de referencia límite de 35€
    fig_coste.add_hline(y=35.0, line_dash="dash", line_color="red", annotation_text="Límite Máximo Óptimo")
    st.plotly_chart(fig_coste, use_container_width=True)

# --- VISTA 3: TABLA DE DATOS CRUDA ---
st.markdown("### 📋 Histórico Analítico del Taller")
st.dataframe(df[["Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material", "Margen Bruto (%)", "Coste por Panel (€)", "Eficiencia Pintores (%)"]], 
             use_container_width=True, hide_index=True)