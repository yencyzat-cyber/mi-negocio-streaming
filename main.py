import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="NEXA-Stream Pro", layout="wide")

st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 38px; width: 100%; }
    .stTextInput>div>div>input { border-radius: 10px; }
    .wa-button { 
        background-color: #25D366; 
        color: white; 
        padding: 8px 15px; 
        border-radius: 15px; 
        text-decoration: none; 
        font-weight: bold;
        display: inline-block;
        text-align: center;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# ARCHIVOS DE DATOS
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
        # Aseguramos que exista la columna de asignación
        if 'Asignado_A' not in inv.columns:
            inv['Asignado_A'] = "Nadie"
    else:
        inv = pd.DataFrame(columns=["Correo", "Password", "Usos", "Asignado_A"])
    return df, inv

df_ventas, df_inv = cargar_datos()

# --- DIÁLOGOS ---
@st.dialog("Editar Correo")
def editar_inv_popup(index, row):
    new_m = st.text_input("Correo", value=row['Correo'])
    new_p = st.text_input("Clave", value=row['Password'])
    new_u = st.selectbox("Usos", [0, 1, 2], index=int(row['Usos']))
    new_a = st.text_input("Asignado a", value=row['Asignado_A'])
    if st.button("GUARDAR CAMBIOS"):
        df_inv.at[index, 'Correo'] = new_m
        df_inv.at[index, 'Password'] = new_p
        df_inv.at[index, 'Usos'] = new_u
        df_inv.at[index, 'Asignado_A'] = new_a
        df_inv.to_csv(INV_FILE, index=False)
        st.rerun()

@st.dialog("Eliminar del Sistema")
def borrar_confirmar(index, tipo, nombre):
    st.warning(f"¿Estás seguro de eliminar a **{nombre}**?")
    if st.button("SÍ, ELIMINAR", type="primary"):
        if tipo == "venta":
            df_v = df_ventas.drop(index)
            df_v.to_csv(VENTAS_FILE, index=False)
        else:
            df_i = df_inv.drop(index)
            df_i.to_csv(INV_FILE, index=False)
        st.rerun()

@st.dialog("Nueva Venta")
def nueva_venta_popup():
    c1, c2 = st.columns(2)
    prod = c1.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max", "Prime Video"])
    f_ini = c2.date_input("Inicio", datetime.now())
    nom = st.text_input("Nombre Cliente")
    tel = st.text_input("WhatsApp (51...)")
    
    st.divider()
    ca, cb = st.columns(2); cc, cd = st.columns(2)
    venc = f_ini + timedelta(days=30)

    if prod == "YouTube Premium" and not df_inv.empty:
        disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
        if not disponibles.empty:
            sug = disponibles.iloc[0]
            m_v = ca.text_input("Correo", value=sug['Correo'])
            p_v = cb.text_input("Clave", value=sug['Password'])
        else:
            st.error("Sin cupos en YT"); m_v = ca.text_input("Correo"); p_v = cb.text_input("Clave")
        perf_v, pin_v = "N/A", "N/A"
    else:
        m_v, p_v = ca.text_input("Correo"), cb.text_input("Clave")
        perf_v, pin_v = cc.text_input("Perfil"), cd.text_input("PIN")

    if st.button("CONFIRMAR VENTA", type="primary", use_container_width=True):
        if nom and tel and m_v:
            nueva = pd.DataFrame([[ "🟢", nom, tel, prod, m_v, p_v, perf_v, pin_v, venc ]], 
                                 columns=["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento"])
            pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
            
            # Actualizar historial en Inventario
            if prod == "YouTube Premium" and m_v in df_inv['Correo'].values:
                idx = df_inv[df_inv['Correo'] == m_v].index[0]
                df_inv.at[idx, 'Usos'] += 1
                df_inv.at[idx, 'Asignado_A'] = f"{nom} ({venc})"
                df_inv.to_csv(INV_FILE, index=False)
            st.rerun()

# --- INTERFAZ ---
st.title("🚀 NEXA-Stream Manager")
t1, t2 = st.tabs(["📊 Administración", "📦 Inventario YT"])

with t1:
    h1, h2 = st.columns([1, 2])
    with h1: 
        if st.button("➕ NUEVA VENTA", type="primary"): nueva_venta_popup()
    with h2: 
        search = st.text_input("", placeholder="🔍 Buscar cliente...", label_visibility="collapsed")

    st.divider()
    if not df_ventas.empty:
        mask = df_ventas.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        hoy = datetime.now().date()
        for idx, row in df_ventas[mask].sort_values(by="Vencimiento").iterrows():
            d = (row['Vencimiento'] - hoy).days
            col = "🔴" if d <= 0 else "🟠" if d <= 3 else "🟢"
            with st.container(border=True):
                c_inf, c_wa, c_del = st.columns([4, 1.2, 0.4])
                with c_inf:
                    st.write(f"{col} **{row['Cliente']}** | {row['Producto']}")
                    st.caption(f"📧 {row['Correo']} | 👤 Perfil: {row['Perfil']} | 📅 Vence: {row['Vencimiento']}")
                with c_wa:
                    msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                    st.markdown(f'<br><a href="https://wa.me/{row["WhatsApp"]}?text={msj}" class="wa-button">📲 WhatsApp</a>', unsafe_allow_html=True)
                if c_del.button("🗑️", key=f"v_{idx}"): borrar_confirmar(idx, "venta", row['Cliente'])
    else: st.info("No hay ventas registradas.")

with t2:
    st.subheader("Control de Inventario")
    if st.button("➕ AGREGAR CORREO NUEVO"):
        @st.dialog("Nuevo Correo")
        def add_inv():
            m = st.text_input("Gmail"); p = st.text_input("Clave"); u = st.selectbox("Usos", [0,1,2])
            if st.button("GUARDAR"):
                ni = pd.DataFrame([[m, p, u, "Nadie"]], columns=["Correo", "Password", "Usos", "Asignado_A"])
                pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False); st.rerun()
        add_inv()

    for idx, row in df_inv.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 2, 0.5, 0.5])
            c1.write(f"📧 **{row['Correo']}**")
            c1.caption(f"Usos: {row['Usos']}")
            c2.write(f"👤 **Asignado a:**")
            c2.caption(row['Asignado_A'])
            if c3.button("📝", key=f"ed_{idx}"): editar_inv_popup(idx, row)
            if c4.button("🗑️", key=f"d_{idx}"): borrar_confirmar(idx, "inv", row['Correo'])
