import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NEXA-Stream Pro", layout="wide")

st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 35px; width: 100%; font-size: 14px; }
    .wa-button { 
        background-color: #25D366; color: white; padding: 6px 10px; 
        border-radius: 15px; text-decoration: none; font-weight: bold;
        display: inline-block; text-align: center; width: 100%; font-size: 13px;
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

def limpiar_whatsapp(numero):
    solo_numeros = re.sub(r'\D', '', str(numero))
    if len(solo_numeros) == 9:
        return f"51{solo_numeros}"
    return solo_numeros

# --- DIÁLOGOS ---
@st.dialog("Editar Venta")
def editar_venta_popup(idx, row):
    c1, c2 = st.columns(2)
    prod = c1.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max", "Prime Video"], index=["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max", "Prime Video"].index(row['Producto']) if row['Producto'] in ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max", "Prime Video"] else 0)
    # Intentar obtener la fecha de inicio (30 días antes del vencimiento como fallback)
    f_default = row['Vencimiento'] - timedelta(days=30)
    f_ini = c2.date_input("Nueva Fecha Inicio", f_default)
    
    nom = st.text_input("Nombre Cliente", value=row['Cliente'])
    tel = st.text_input("WhatsApp", value=row['WhatsApp'])
    
    duracion = st.radio("Nueva Duración:", ["1 Mes", "2 Meses", "6 Meses", "1 Año", "Personalizado"], horizontal=True)
    if duracion == "1 Mes": venc = f_ini + relativedelta(months=1)
    elif duracion == "2 Meses": venc = f_ini + relativedelta(months=2)
    elif duracion == "6 Meses": venc = f_ini + relativedelta(months=6)
    elif duracion == "1 Año": venc = f_ini + relativedelta(years=1)
    else: venc = st.date_input("Vencimiento Manual", row['Vencimiento'])

    st.divider()
    ca, cb = st.columns(2); cc, cd = st.columns(2)
    mv = ca.text_input("Correo", value=row['Correo'])
    pv = cb.text_input("Clave", value=row['Pass'])
    perf = cc.text_input("Perfil", value=row['Perfil'])
    pin = cd.text_input("PIN", value=row['PIN'])

    if st.button("ACTUALIZAR DATOS"):
        df_ventas.at[idx, 'Cliente'], df_ventas.at[idx, 'WhatsApp'] = nom, limpiar_whatsapp(tel)
        df_ventas.at[idx, 'Producto'], df_ventas.at[idx, 'Vencimiento'] = prod, venc
        df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'] = mv, pv
        df_ventas.at[idx, 'Perfil'], df_ventas.at[idx, 'PIN'] = perf, pin
        df_ventas.to_csv(VENTAS_FILE, index=False)
        
        # Actualizar Inventario si es YT
        if prod == "YouTube Premium" and mv in df_inv['Correo'].values:
            i_idx = df_inv[df_inv['Correo'] == mv].index[0]
            df_inv.at[i_idx, 'Asignado_A'] = f"{nom} (Vence: {venc})"
            df_inv.to_csv(INV_FILE, index=False)
        st.rerun()

@st.dialog("Nueva Venta")
def nueva_venta_popup():
    c1, c2 = st.columns(2)
    prod = c1.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max", "Prime Video"])
    f_ini = c2.date_input("Fecha de Inicio", datetime.now())
    nom = st.text_input("Nombre Cliente")
    tel = st.text_input("WhatsApp")
    
    duracion = st.radio("Duración:", ["1 Mes", "2 Meses", "6 Meses", "1 Año", "Personalizado"], horizontal=True)
    if duracion == "1 Mes": venc = f_ini + relativedelta(months=1)
    elif duracion == "2 Meses": venc = f_ini + relativedelta(months=2)
    elif duracion == "6 Meses": venc = f_ini + relativedelta(months=6)
    elif duracion == "1 Año": venc = f_ini + relativedelta(years=1)
    else: venc = st.date_input("Vencimiento Manual", f_ini + timedelta(days=30))

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

    if st.button("CONFIRMAR VENTA", type="primary"):
        tel_limpio = limpiar_whatsapp(tel)
        nueva = pd.DataFrame([[ "🟢", nom, tel_limpio, prod, mv, pv, perf_v, pin_v, venc ]], columns=df_ventas.columns)
        pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
        if prod == "YouTube Premium" and mv in df_inv['Correo'].values:
            idx = df_inv[df_inv['Correo'] == mv].index[0]
            df_inv.at[idx, 'Usos'] += 1
            df_inv.at[idx, 'Asignado_A'] = f"{nom} (Vence: {venc})"
            df_inv.to_csv(INV_FILE, index=False)
        st.rerun()

# --- INTERFAZ ---
st.title("🚀 NEXA-Stream Manager")
t1, t2 = st.tabs(["📊 Administración", "📦 Inventario YT"])

with t1:
    h1, h2 = st.columns([1, 2])
    if h1.button("➕ NUEVA VENTA", type="primary"): nueva_venta_popup()
    search = h2.text_input("", placeholder="🔍 Buscar cliente...", label_visibility="collapsed")
    st.divider()
    if not df_ventas.empty:
        mask = df_ventas.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        hoy = datetime.now().date()
        for idx, row in df_ventas[mask].sort_values(by="Vencimiento").iterrows():
            d = (row['Vencimiento'] - hoy).days
            col = "🔴" if d <= 0 else "🟠" if d <= 3 else "🟢"
            with st.container(border=True):
                ci, cw, ce, cd = st.columns([4, 1, 0.5, 0.4])
                ci.write(f"{col} **{row['Cliente']}** | {row['Producto']}")
                ci.caption(f"📧 {row['Correo']} | 📅 Vence: {row['Vencimiento']} | 👤 {row['Perfil']}")
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                cw.markdown(f'<br><a href="https://wa.me/{row["WhatsApp"]}?text={msj}" class="wa-button">📲 WA</a>', unsafe_allow_html=True)
                if ce.button("📝", key=f"e_{idx}"): editar_venta_popup(idx, row)
                if cd.button("🗑️", key=f"v_{idx}"):
                    df_ventas.drop(idx).to_csv(VENTAS_FILE, index=False); st.rerun()
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
            c1.write(f"📧 **{row['Correo']}** (Usos: {row['Usos']})")
            c1.caption(f"👤 **Asignado a:** {row['Asignado_A']}")
            if c2.button("📝", key=f"ed_{idx}"):
                @st.dialog("Editar")
                def edit():
                    nu = st.selectbox("Usos", [0,1,2], index=int(row['Usos']))
                    if st.button("GUARDAR"):
                        df_inv.at[idx, 'Usos'] = nu; df_inv.to_csv(INV_FILE, index=False); st.rerun()
                edit()
            if c3.button("🗑️", key=f"d_{idx}"):
                df_inv.drop(idx).to_csv(INV_FILE, index=False); st.rerun()
