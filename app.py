import streamlit as st
import pandas as pd
import plotly.express as px
import gspread

# Configuración de la página web
st.set_page_config(page_title="KPI PaintShop Multi-Taller", layout="wide", initial_sidebar_state="expanded")

# --- CONEXIÓN AUTOMÁTICA A GOOGLE SHEETS ---
def conectar_base_datos():
    try:
        # Método directo usando la URL guardada en Secrets
        url_hoja = st.secrets["private_gsheets_url"]
        # Abrimos la hoja de forma pública/compartida a través de gspread
        gc = gspread.public_link(url_hoja)
        return gc.sheet1
    except Exception as e:
        # Intento secundario si el método directo tiene restricciones de versión
        try:
            url_hoja = st.secrets["private_gsheets_url"]
            # Alternativa alternativa nativa de lectura
            df_direct = pd.read_csv(url_hoja.replace('/edit', '/export?format=csv'))
            return df_direct
        except:
            st.error(f"⚠️ Error de conexión con la base de datos: {e}")
            st.info("💡 Recuerda que tu Google Sheet debe estar compartido como 'Cualquier persona con el enlace puede editar'.")
            return None

objeto_conexion = conectar_base_datos()

# Cargar datos desde la conexión
df_total = pd.DataFrame(columns=["Taller", "Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material"])

if objeto_conexion is not None:
    if isinstance(objeto_conexion, pd.DataFrame):
        df_total = objeto_conexion
    else:
        try:
            records = objeto_conexion.get_all_records()
            if records:
                df_total = pd.DataFrame(records)
        except:
            pass

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
if guardar and objeto_conexion is not None and not isinstance(objeto_conexion, pd.DataFrame):
    if not df_total.empty and 'Taller' in df_total.columns and ((df_total['Taller'] == taller_seleccionado) & (df_total['Mes'] == mes_input)).any():
        st.sidebar.warning("Ya existen datos para este mes. Modifícalos directamente en el Excel si lo necesitas.")
    else:
        nueva_fila = [taller_seleccionado, mes_input, h_fact, h_real, paneles, venta, coste]
        objeto_conexion.append_row(nueva_fila)
        st.sidebar.success(f"¡Datos de {mes_input} guardados en la nube!")
        st.rerun()
elif guardar:
    st.sidebar.error("El modo de almacenamiento actual es de solo lectura. Revisa la conexión.")

# --- FILTRADO DE DATOS PARA MOSTRAR EN PANTALLA ---
if not df_total.empty and 'Taller' in df_total.columns and taller_seleccionado in df_total['Taller'].values:
    df = df_total[df_total['Taller'] == taller_seleccionado].copy()
else:
    df = pd.DataFrame({
        "Taller": [taller_seleccionado], "Mes": ["Sin Datos"], "Horas_Facturadas": [1], 
        "Horas_Reales": [1], "Paneles_Pintados": [1], "Venta_Pintura": [0.0], "Coste_Material": [0.0]
    })

# --- CÁLCULO DE KPIS CONSOLIDADOS ---
total_venta = df['Venta_Pintura'].sum() if 'Venta_Pintura' in df.columns else 0
total_coste = df['Coste_Material'].sum() if 'Coste_Material' in df.columns else 0
total_paneles = df['Paneles_Pintados'].sum() if 'Paneles_Pintados' in df.columns else 0
total_h_fact = df['Horas_Facturadas'].sum() if 'Horas_Facturadas' in df.columns else 0
total_h_real = df['Horas_Reales'].sum() if 'Horas_Reales' in df.columns else 0

margen_global = ((total_venta - total_coste) / total_venta) * 100 if total_venta > 0 else 0
coste_panel_global = total_coste / total_paneles if total_paneles > 0 else 0
eficiencia_global = (total_h_fact / total_h_real) * 100 if total_h_real > 0 else 0

df['Margen Bruto (%)'] = ((df['Venta_Pintura'] - df['Coste_Material']) / df['Venta_Pintura'] * 100).round(1) if total_venta > 0 else 0
df['Coste por Panel (€)'] = (df['Coste_Material'] / df['Paneles_Pintados']).round(2) if 'Paneles_Pintados' in df.columns else 0
df['Eficiencia Pintores (%)'] = (df['Horas_Facturadas'] / df['Horas_Reales'] * 100).round(1) if 'Horas_Reales' in df.columns else 0

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
    if 'Venta_Pintura' in df.columns and 'Coste_Material' in df.columns:
        fig_fin = px.bar(df, x="Mes", y=["Venta_Pintura", "Coste_Material"], 
                         barmode="group", labels={"value": "Euros (€)", "variable": "Concepto"},
                         color_discrete_sequence=["#1E3A8A", "#EF4444"])
        st.plotly_chart(fig_fin, use_container_width=True)

with g2:
    st.subheader("Evolución del Coste por Panel")
    if 'Coste por Panel (€)' in df.columns:
        fig_coste = px.line(df, x="Mes", y="Coste por Panel (€)", markers=True, color_discrete_sequence=["#10B981"])
        if df['Coste por Panel (€)'].max() > 0:
            fig_coste.add_hline(y=35.0, line_dash="dash", line_color="red", annotation_text="Límite Máximo")
        st.plotly_chart(fig_coste, use_container_width=True)

# --- TABLA CRUDA ---
st.markdown("### 📋 Histórico Analítico Filtro Taller")
columnas_visibles = [c for c in ["Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material", "Margen Bruto (%)", "Coste por Panel (€)", "Eficiencia Pintores (%)"] if c in df.columns]
st.dataframe(df[columnas_visibles], use_container_width=True, hide_index=True)
