import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

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
        if 'Asignado_A' not in inv.columns: inv['Asignado_A'] = "Nadie"
    else:
        inv = pd.DataFrame(columns=["Correo", "Password", "Usos", "Asignado_A"])
    return df, inv

df_ventas, df_inv = cargar_datos()

# --- DIÁLOGOS ---
@st.dialog("Editar Correo")
def editar_inv_popup(index, row):
    nm = st.text_input("Correo", value=row['Correo'])
    np = st.text_input("Clave", value=row['Password'])
    nu = st.selectbox("Usos", [0, 1, 2], index=int(row['Usos']))
    na = st.text_input("Asignado a (Nombre y Fecha)", value=row['Asignado_A'])
    if st.button("GUARDAR CAMBIOS"):
        df_inv.at[index, 'Correo'], df_inv.at[index, 'Password'] = nm, np
        df_inv.at[index, 'Usos'], df_inv.at[index, 'Asignado_A'] = nu, na
        df_inv.to_csv(INV_FILE, index=False); st.rerun()

@st.dialog("Eliminar")
def borrar_confirmar(index, tipo):
    st.warning("¿Confirmas la eliminación?")
    if st.button("SÍ, ELIMINAR", type="primary"):
        if tipo == "venta": pd.read_csv(VENTAS_FILE).drop(index).to_csv(VENTAS_FILE, index=False)
        else: pd.read_csv(INV_FILE).drop(index).to_csv(INV_FILE, index=False)
        st.rerun()

@st.dialog("Nueva Venta")
def nueva_venta_popup():
    c1, c2 = st.columns(2)
    prod = c1.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max"])
    f_ini = c2.date_input("Inicio", datetime.now())
    nom, tel = st.text_input("Cliente"), st.text_input("WhatsApp (51...)")
    st.divider()
    ca, cb = st.columns(2); cc, cd = st.columns(2)
    venc = f_ini + timedelta(days=30)

    if prod == "YouTube Premium" and not df_inv.empty:
        disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
        if not disponibles.empty:
            sug = disponibles.iloc[0]
            mv, pv = ca.text_input("Correo", value=sug['Correo']), cb.text_input("Clave", value=sug['Password'])
        else: st.error("Sin cupos YT"); mv, pv = ca.text_input("Correo"), cb.text_input("Clave")
        perf_v, pin_v = "N/A", "N/A"
    else:
        mv, pv, perf_v, pin_v = ca.text_input("Correo"), cb.text_input("Clave"), cc.text_input("Perfil"), cd.text_input("PIN")

    if st.button("CONFIRMAR VENTA", type="primary", use_container_width=True):
        nueva = pd.DataFrame([[ "🟢", nom, tel, prod, mv, pv, perf_v, pin_v, venc ]], columns=df_ventas.columns)
        pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
        if prod == "YouTube Premium" and mv in df_inv['Correo'].values:
            idx = df_inv[df_inv['Correo'] == mv].index[0]
            df_inv.at[idx, 'Usos'] += 1
            df_inv.at[idx, 'Asignado_A'] = f"{nom} (Vence: {venc})"
            df_inv.to_csv(INV_FILE, index=False)
        st.rerun()

# --- INTERFAZ ---
st.title("🚀 NEXA-Stream Manager")
t1, t2 = st.tabs(["📊 Ventas", "📦 Inventario YT"])

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
                ci.caption(f"📧 {row['Correo']} | 👤 {row['Perfil']} | 📅 {row['Vencimiento']}")
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                cw.markdown(f'<br><a href="https://wa.me/{row["WhatsApp"]}?text={msj}" class="wa-button">📲 WhatsApp</a>', unsafe_allow_html=True)
                if cd.button("🗑️", key=f"v_{idx}"): borrar_confirmar(idx, "venta")
    else: st.info("Sin ventas.")

with t2:
    st.subheader("Control de Inventario")
    if st.button("➕ AGREGAR CORREO NUEVO"):
        @st.dialog("Nuevo")
        def add():
            m, p, u = st.text_input("Gmail"), st.text_input("Clave"), st.selectbox("Usos", [0,1,2])
            if st.button("GUARDAR"):
                ni = pd.DataFrame([[m,p,u,"Nadie"]], columns=df_inv.columns)
                pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False); st.rerun()
        add()

    for idx, row in df_inv.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 0.5, 0.5])
            with c1:
                st.write(f"📧 **{row['Correo']}** (Usos: {row['Usos']})")
                st.caption(f"👤 **Asignado a:** {row['Asignado_A']}")
            if c2.button("📝", key=f"ed_{idx}"): editar_inv_popup(idx, row)
            if c3.button("🗑️", key=f"d_{idx}"): borrar_confirmar(idx, "inv")
