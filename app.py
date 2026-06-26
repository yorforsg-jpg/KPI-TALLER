import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Configuración de la página web
st.set_page_config(page_title="KPI PaintShop Multi-Taller", layout="wide", initial_sidebar_state="expanded")

st.title("📊 Sistema de Rentabilidad y KPIs - Control Multi-Taller")
st.caption("Sincronización automatizada en la nube independiente por cada usuario.")

# --- CONEXIÓN COMPLETA A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Lee todos los datos existentes
    df_total = conn.read(ttl="0m")
    # Limpiar columnas vacías si las hay
    df_total = df_total.dropna(how="all")
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    df_total = pd.DataFrame(columns=["Taller", "Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material"])

# Si la tabla se lee vacía o sin las columnas correctas, forzar estructura básica
if df_total.empty or "Taller" not in df_total.columns:
    df_total = pd.DataFrame(columns=["Taller", "Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material"])

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

# Procesar y subir datos a Google Sheets si se pulsa el botón
if guardar:
    # Validar si ya existe el registro para evitar duplicados en la pantalla visual
    registro_existe = not df_total.empty and ((df_total['Taller'] == taller_seleccionado) & (df_total['Mes'] == mes_input)).any()
    
    if registro_existe:
        st.sidebar.warning(f"Ya existen datos de {mes_input} para {taller_seleccionado}.")
    else:
        # Añadir nueva fila al DataFrame local
        nueva_fila = pd.DataFrame([{
            "Taller": taller_seleccionado, 
            "Mes": mes_input, 
            "Horas_Facturadas": h_fact, 
            "Horas_Reales": h_real, 
            "Paneles_Pintados": paneles, 
            "Venta_Pintura": venta, 
            "Coste_Material": coste
        }])
        df_actualizado = pd.concat([df_total, nueva_fila], ignore_index=True)
        
        try:
            # Subir y sobreescribir la hoja de Google Sheets completa con el nuevo dato
            conn.update(data=df_actualizado)
            st.sidebar.success(f"¡Datos de {mes_input} guardados con éxito!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error al escribir en la base de datos: {e}")

# --- FILTRADO DE DATOS PARA MOSTRAR EN PANTALLA ---
if not df_total.empty and taller_seleccionado in df_total['Taller'].values:
    df = df_total[df_total['Taller'] == taller_seleccionado].copy()
else:
    # Datos por defecto si el taller seleccionado no tiene registros guardados aún
    df = pd.DataFrame({
        "Taller": [taller_seleccionado], "Mes": ["Sin Datos"], "Horas_Facturadas": [0], 
        "Horas_Reales": [1], "Paneles_Pintados": [1], "Venta_Pintura": [0.0], "Coste_Material": [0.0]
    })

# --- CÁLCULO DE KPIS CONSOLIDADOS ---
total_venta = pd.to_numeric(df['Venta_Pintura']).sum()
total_coste = pd.to_numeric(df['Coste_Material']).sum()
total_paneles = pd.to_numeric(df['Paneles_Pintados']).sum()
total_h_fact = pd.to_numeric(df['Horas_Facturadas']).sum()
total_h_real = pd.to_numeric(df['Horas_Reales']).sum()

margen_global = ((total_venta - total_coste) / total_venta) * 100 if total_venta > 0 else 0
coste_panel_global = total_coste / total_paneles if total_paneles > 0 else 0
eficiencia_global = (total_h_fact / total_h_real) * 100 if total_h_real > 0 else 0

# Columnas calculadas para la tabla histórica
df['Margen Bruto (%)'] = (((pd.to_numeric(df['Venta_Pintura']) - pd.to_numeric(df['Coste_Material'])) / pd.to_numeric(df['Venta_Pintura'])) * 100).round(1) if total_venta > 0 else 0
df['Coste por Panel (€)'] = (pd.to_numeric(df['Coste_Material']) / pd.to_numeric(df['Paneles_Pintados'])).round(2)
df['Eficiencia Pintores (%)'] = ((pd.to_numeric(df['Horas_Facturadas']) / pd.to_numeric(df['Horas_Reales'])) * 100).round(1)

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

# --- TABLA HISTÓRICA ---
st.markdown("### 📋 Histórico Analítico Filtro Taller")
st.dataframe(df[["Mes", "Horas_Facturadas", "Horas_Reales", "Paneles_Pintados", "Venta_Pintura", "Coste_Material", "Margen Bruto (%)", "Coste por Panel (€)", "Eficiencia Pintores (%)"]], 
             use_container_width=True, hide_index=True)
