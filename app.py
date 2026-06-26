import streamlit as st
import pandas as pd
import plotly.express as px
import gspread

# Configuración de la página web
st.set_page_config(page_title="KPI PaintShop Multi-Taller", layout="wide", initial_sidebar_state="expanded")

# --- CONEXIÓN AUTOMÁTICA A GOOGLE SHEETS (BASE DE DATOS) ---
# REEMPLAZA ESTE ENLACE POR EL DE TU PROPIA HOJA DE GOOGLE SHEETS:
URL_HOJA = "https://docs.google.com/spreadsheets/d/1tyMR_aQTSetE8d1qyEr0ZUWTJvR0riC073TNmICHkiQ/edit?gid=0#gid=0"

def conectar_base_datos():
    try:
        # Conexión simplificada para Streamlit Cloud usando modo público-editor
        gc = gspread.public_link(URL_HOJA)
        sheet = gc.sheet1
        return sheet
    except Exception as e:
        st.error(f"Error de conexión con la base de datos: {e}")
        return None

sheet_db = conectar_base_datos()

# Cargar datos desde Google Sheets
if sheet_db:
    try:
        records = sheet_db.get_all_records()
        if records:
            df_total = pd.DataFrame(records)
        else:
            df_total = pd.DataFrame(columns=["Taller", "Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material"])
    except:
        df_total = pd.DataFrame(columns=["Taller", "Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material"])
else:
    df_total = pd.DataFrame(columns=["Taller", "Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material"])

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Sistema de Rentabilidad y KPIs - Control Multi-Taller")
st.caption("Los datos se guardan y sincronizan automáticamente en la nube de forma independiente por taller.")

# --- FORMULARIO LATERAL: SELECCIÓN DE TALLER Y REGISTRO ---
st.sidebar.header("🏢 Identificación y Datos")

# Selector de taller para evitar mezclar datos
taller_seleccionado = st.sidebar.selectbox("Selecciona tu Taller / Usuario", [
    "Taller Central", 
    "Taller Norte", 
    "Taller Sur", 
    "Taller Pintura Express",
    "Gestor Invitado"
])

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Registrando datos para:** {taller_seleccionado}")

with st.sidebar.form("formulario_taller"):
    mes_input = st.selectbox("Selecciona el Mes", [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ])
    h_fact = st.number_input("Horas Facturadas de Pintura", min_value=0, step=1, value=300)
    h_real = st.number_input("Horas Reales de Presencia", min_value=1, step=1, value=300)
    paneles = st.number_input("Total Paneles Pintados", min_value=1, step=1, value=200)
    venta = st.number_input("Venta Total Pintura (€)", min_value=0.0, step=100.0, value=15000.0)
    coste = st.number_input("Coste Total Material Consumido (€)", min_value=0.0, step=100.0, value=5000.0)
    
    guardar = st.form_submit_button("💾 Guardar en Base de Datos")

# Procesar y subir datos a Google Sheets
if guardar and sheet_db is not None:
    # Comprobar si ya existen datos para ese mismo taller y mes para sobreescribirlos o añadirlos
    if not df_total.empty and ((df_total['Taller'] == taller_seleccionado) & (df_total['Mes'] == mes_input)).any():
        st.sidebar.warning("Ya existen datos para este mes. Limpia la fila en tu Google Sheet si deseas modificarlos.")
    else:
        nueva_fila = [taller_seleccionado, mes_input, h_fact, h_real, paneles, venta, coste]
        sheet_db.append_row(nueva_fila)
        st.sidebar.success(f"¡Datos de {mes_input} guardados en la nube!")
        st.rerun()

# --- FILTRADO DE DATOS PARA MOSTRAR EN PANTALLA ---
# La web solo mostrará los gráficos correspondientes al taller que esté seleccionado en el menú izquierdo
if not df_total.empty and taller_seleccionado in df_total['Taller'].values:
    df = df_total[df_total['Taller'] == taller_seleccionado].copy()
else:
    # Datos semilla vacíos si el taller seleccionado aún no ha registrado nada
    df = pd.DataFrame({
        "Taller": [taller_seleccionado], "Mes": ["Sin Datos"], "Horas_Facturadas": [1], 
        "Horas_Reales": [1], "Paneles_Pintados": [1], "Venta_Pintura": [0.0], "Coste_Material": [0.0]
    })

# --- CÁLCULO DE KPIS CONSOLIDADOS ---
total_venta = df['Venta_Pintura'].sum()
total_coste = df['Coste_Material'].sum()
total_paneles = df['Paneles_Pintados'].sum()
total_h_fact = df['Horas_Facturadas'].sum()
total_h_real = df['Horas_Reales'].sum()

margen_global = ((total_venta - total_coste) / total_venta) * 100 if total_venta > 0 else 0
coste_panel_global = total_coste / total_paneles if total_paneles > 0 else 0
eficiencia_global = (total_h_fact / total_h_real) * 100 if total_h_real > 0 else 0

df['Margen Bruto (%)'] = ((df['Venta_Pintura'] - df['Coste_Material']) / df['Venta_Pintura'] * 100).round(1) if total_venta > 0 else 0
df['Coste por Panel (€)'] = (df['Coste_Material'] / df['Paneles_Pintados']).round(2)
df['Eficiencia Pintores (%)'] = (df['Horas_Facturadas'] / df['Horas_Reales'] * 100).round(1)

# --- PANEL VISUAL ---
st.markdown(f"### 🏆 Rendimiento Acumulado: {taller_seleccionado}")
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric(label="MARGEN BRUTO PINTURA", value=f"{margen_global:.1f} %", delta="Target óptimo: > 60%")
with kpi2:
    st.metric(label="COSTE MEDIO / PANEL", value=f"{coste_panel_global:.2f} €", delta="Target óptimo: < 35 €", delta_color="inverse")
with kpi3:
    st.metric(label="EFICIENCIA OPERARIOS", value=f"{eficiencia_global:.1f} %", delta="Target óptimo: > 100%")

st.markdown("---")

# --- GRÁFICOS ---
st.markdown("### 📈 Análisis de Tendencias del Taller Seleccionado")
g1, g2 = st.columns(2)

with g1:
    st.subheader("Brecha Financiera: Venta vs Coste de Material")
    fig_fin = px.bar(df, x="Mes", y=["Venta_Pintura", "Coste_Material"], 
                     barmode="group", labels={"value": "Euros (€)", "variable": "Concepto"},
                     color_discrete_sequence=["#1E3A8A", "#EF4444"])
    st.plotly_chart(fig_fin, use_container_width=True)

with g2:
    st.subheader("Evolución del Coste por Panel")
    fig_coste = px.line(df, x="Mes", y="Coste por Panel (€)", markers=True, color_discrete_sequence=["#10B981"])
    if df['Coste por Panel (€)'].max() > 0:
        fig_coste.add_hline(y=35.0, line_dash="dash", line_color="red", annotation_text="Límite Máximo")
    st.plotly_chart(fig_coste, use_container_width=True)

# --- TABLA CRUDA ---
st.markdown("### 📋 Histórico Analítico Filtro Taller")
st.dataframe(df[["Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material", "Margen Bruto (%)", "Coste por Panel (€)", "Eficiencia Pintores (%)"]], 
             use_container_width=True, hide_index=True)