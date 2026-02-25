import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NEXA-Stream Pro", layout="wide")

st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 38px; width: 100%; }
    .wa-button { 
        background-color: #25D366; color: white; padding: 8px 15px; 
        border-radius: 15px; text-decoration: none; font-weight: bold;
        display: inline-block; text-align: center; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# ARCHIVOS
VENTAS_FILE = "ventas_data.csv"
INV_FILE = "inventario_yt.csv"

def cargar_datos():
    if os.path.exists(VENTAS_FILE):
        df = pd.read_csv(VENTAS_FILE)
        df['Vencimiento'] = pd.to_datetime(df['Vencimiento'], errors='coerce').dt.date
    else:
        df = pd.DataFrame(columns=["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento"])
    if os.path.exists(INV_FILE):
        inv = pd.read_csv(INV_FILE)
    else:
        inv = pd.DataFrame(columns=["Correo", "Password", "Usos", "Asignado_A"])
    return df, inv

df_ventas, df_inv = cargar_datos()

# --- DIÁLOGOS ---
@st.dialog("Nueva Venta")
def nueva_venta_popup():
    c1, c2 = st.columns(2)
    prod = c1.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max", "Prime Video", "Paramount+"])
    f_ini = c2.date_input("Fecha de Inicio", datetime.now())
    
    nom = st.text_input("Nombre del Cliente")
    tel = st.text_input("WhatsApp (ej: 51999888777)")
    
    # NUEVO: Selector de Duración
    st.write("⏳ **Duración del Servicio**")
    duracion = st.radio("Selecciona el tiempo:", 
                        ["1 Mes", "2 Meses", "6 Meses", "1 Año", "Personalizado"], 
                        horizontal=True)
    
    if duracion == "1 Mes": venc = f_ini + relativedelta(months=1)
    elif duracion == "2 Meses": venc = f_ini + relativedelta(months=2)
    elif duracion == "6 Meses": venc = f_ini + relativedelta(months=6)
    elif duracion == "1 Año": venc = f_ini + relativedelta(years=1)
    else: venc = st.date_input("Fecha de Vencimiento Manual", f_ini + timedelta(days=30))

    st.info(f"📅 El servicio vencerá el: **{venc}**")
    st.divider()
    
    ca, cb = st.columns(2); cc, cd = st.columns(2)
    if prod == "YouTube Premium" and not df_inv.empty:
        disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
        if not disponibles.empty:
            sug = disponibles.iloc[0]
            mv, pv = ca.text_input("Correo", value=sug['Correo']), cb.text_input("Clave", value=sug['Password'])
        else: st.error("Sin cupos YT"); mv, pv = ca.text_input("Correo"), cb.text_input("Clave")
        perf_v, pin_v = "N/A", "N/A"
    else:
        mv, pv, perf_v, pin_v = ca.text_input("Correo"), cb.text_input("Clave"), cc.text_input("Perfil"), cd.text_input("PIN")

    if st.button("CONFIRMAR Y GUARDAR VENTA", type="primary", use_container_width=True):
        if nom and tel and mv:
            nueva = pd.DataFrame([[ "🟢", nom, tel, prod, mv, pv, perf_v, pin_v, venc ]], columns=df_ventas.columns)
            pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
            if prod == "YouTube Premium" and mv in df_inv['Correo'].values:
                idx = df_inv[df_inv['Correo'] == mv].index[0]
                df_inv.at[idx, 'Usos'] += 1
                df_inv.at[idx, 'Asignado_A'] = f"{nom} (Vence: {venc})"
                df_inv.to_csv(INV_FILE, index=False)
            st.success("Venta guardada")
            st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.title("🚀 NEXA-Stream Manager")
t1, t2 = st.tabs(["📊 Administración", "📦 Inventario YT"])

with t1:
    h1, h2 = st.columns([1, 2])
    with h1: 
        if st.button("➕ NUEVA VENTA", type="primary"): nueva_venta_popup()
    with h2: search = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed")
    st.divider()
    
    if not df_ventas.empty:
        mask = df_ventas.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        hoy = datetime.now().date()
        for idx, row in df_ventas[mask].sort_values(by="Vencimiento").iterrows():
            d = (row['Vencimiento'] - hoy).days
            col = "🔴" if d <= 0 else "🟠" if d <= 3 else "🟢"
            with st.container(border=True):
                ci, cw, cd = st.columns([4, 1.2, 0.4])
                ci.write(f"{col} **{row['Cliente']}** | {row['Producto']}")
                ci.caption(f"📧 {row['Correo']} | 👤 Perfil: {row['Perfil']} | 📅 Vence: {row['Vencimiento']}")
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                cw.markdown(f'<br><a href="https://wa.me/{row["WhatsApp"]}?text={msj}" class="wa-button">📲 WhatsApp</a>', unsafe_allow_html=True)
                if cd.button("🗑️", key=f"v_{idx}"):
                    @st.dialog("Eliminar")
                    def confirm_del():
                        st.warning(f"¿Finalizar venta de {row['Cliente']}?")
                        if st.button("SÍ, ELIMINAR"):
                            df_ventas.drop(idx).to_csv(VENTAS_FILE, index=False); st.rerun()
                    confirm_del()
    else: st.info("Sin ventas.")

with t2:
    # (El código de Inventario se mantiene igual pero ahora muestra la fecha calculada)
    st.subheader("Control de Inventario")
    if st.button("➕ AGREGAR CORREO NUEVO"):
        @st.dialog("Nuevo")
        def add():
            m, p, u = st.text_input("Gmail"), st.text_input("Clave"), st.selectbox("Usos", [0,1,2])
            if st.button("GUARDAR"):
                ni = pd.DataFrame([[m,p,u,"Nadie"]], columns=["Correo", "Password", "Usos", "Asignado_A"])
                pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False); st.rerun()
        add()

    for idx, row in df_inv.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 0.5, 0.5])
            with c1:
                st.write(f"📧 **{row['Correo']}** (Usos: {row['Usos']})")
                st.caption(f"👤 **Asignado a:** {row['Asignado_A']}")
            if c2.button("📝", key=f"ed_{idx}"):
                @st.dialog("Editar")
                def edit():
                    nm = st.text_input("Correo", value=row['Correo'])
                    nu = st.selectbox("Usos", [0,1,2], index=int(row['Usos']))
                    if st.button("GUARDAR"):
                        df_inv.at[idx, 'Correo'], df_inv.at[idx, 'Usos'] = nm, nu
                        df_inv.to_csv(INV_FILE, index=False); st.rerun()
                edit()
            if c3.button("🗑️", key=f"d_{idx}"):
                df_inv.drop(idx).to_csv(INV_FILE, index=False); st.rerun()
