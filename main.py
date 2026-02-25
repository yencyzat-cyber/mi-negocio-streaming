import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="NEXA-Stream Pro", layout="wide")

st.markdown("""
    <style>
    .stButton>button { border-radius: 15px; height: 32px; width: 100%; font-size: 12px; }
    .wa-button { 
        background-color: #25D366; color: white; padding: 4px 10px; 
        border-radius: 12px; text-decoration: none; font-weight: bold;
        display: inline-block; text-align: center; width: 100%; font-size: 11px;
    }
    .stTextInput>div>div>input { border-radius: 8px; height: 32px; }
    </style>
    """, unsafe_allow_html=True)

# ARCHIVOS DE DATOS
VENTAS_FILE = "ventas_data.csv"
INV_FILE = "inventario_yt.csv"
PLAT_FILE = "plataformas.csv"

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
    if os.path.exists(PLAT_FILE):
        plat = pd.read_csv(PLAT_FILE)['Nombre'].tolist()
    else:
        plat = ["YouTube Premium", "Netflix", "Disney+", "Google One", "Spotify"]
        pd.DataFrame(plat, columns=["Nombre"]).to_csv(PLAT_FILE, index=False)
    return df, inv, plat

df_ventas, df_inv, lista_plataformas = cargar_datos()

def limpiar_whatsapp(numero):
    solo_numeros = re.sub(r'\D', '', str(numero))
    if len(solo_numeros) == 9: return f"51{solo_numeros}"
    return solo_numeros

# --- DIÁLOGOS ---
@st.dialog("Editar Venta")
def editar_venta_popup(idx, row):
    c1, c2 = st.columns(2)
    prod = c1.selectbox("Plataforma", lista_plataformas, index=lista_plataformas.index(row['Producto']) if row['Producto'] in lista_plataformas else 0)
    venc_manual = c2.date_input("Vencimiento Actual", row['Vencimiento'])
    nom = st.text_input("Nombre Cliente", value=row['Cliente'])
    tel = st.text_input("WhatsApp", value=row['WhatsApp'])
    st.divider()
    ca, cb = st.columns(2); cc, cd = st.columns(2)
    mv, pv = ca.text_input("Correo", value=row['Correo']), cb.text_input("Clave", value=row['Pass'])
    perf, pin = cc.text_input("Perfil", value=row['Perfil']), cd.text_input("PIN", value=row['PIN'])

    if st.button("GUARDAR CAMBIOS"):
        df_ventas.at[idx, 'Cliente'], df_ventas.at[idx, 'WhatsApp'] = nom, limpiar_whatsapp(tel)
        df_ventas.at[idx, 'Producto'], df_ventas.at[idx, 'Vencimiento'] = prod, venc_manual
        df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'] = mv, pv
        df_ventas.at[idx, 'Perfil'], df_ventas.at[idx, 'PIN'] = perf, pin
        df_ventas.to_csv(VENTAS_FILE, index=False)
        st.rerun()

@st.dialog("Nueva Venta")
def nueva_venta_popup():
    c1, c2 = st.columns(2)
    prod = c1.selectbox("Plataforma", lista_plataformas)
    f_ini = c2.date_input("Fecha Inicio", datetime.now())
    nom, tel = st.text_input("Nombre Cliente"), st.text_input("WhatsApp")
    dur = st.radio("Plazo:", ["1 Mes", "2 Meses", "6 Meses", "1 Año", "Manual"], horizontal=True)
    if dur == "1 Mes": venc = f_ini + relativedelta(months=1)
    elif dur == "2 Meses": venc = f_ini + relativedelta(months=2)
    elif dur == "6 Meses": venc = f_ini + relativedelta(months=6)
    elif dur == "1 Año": venc = f_ini + relativedelta(years=1)
    else: venc = st.date_input("Fecha Final", f_ini + timedelta(days=30))
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
    if st.button("GUARDAR VENTA", type="primary"):
        nueva = pd.DataFrame([[ "🟢", nom, limpiar_whatsapp(tel), prod, mv, pv, perf_v, pin_v, venc ]], columns=df_ventas.columns)
        pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
        if prod == "YouTube Premium" and mv in df_inv['Correo'].values:
            i_idx = df_inv[df_inv['Correo'] == mv].index[0]
            df_inv.at[i_idx, 'Usos'] += 1
            df_inv.at[i_idx, 'Asignado_A'] = f"{nom} ({venc})"
            df_inv.to_csv(INV_FILE, index=False)
        st.rerun()

# --- INTERFAZ ---
st.title("🚀 NEXA-Stream Manager")
t1, t2 = st.tabs(["📊 Ventas", "⚙️ Config / Inv"])

with t1:
    h1, h2 = st.columns([1, 2])
    if h1.button("➕ NUEVA VENTA", type="primary"): nueva_venta_popup()
    search = h2.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed")
    st.divider()
    if not df_ventas.empty:
        mask = df_ventas.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        hoy = datetime.now().date()
        for idx, row in df_ventas[mask].sort_values(by="Vencimiento").iterrows():
            d = (row['Vencimiento'] - hoy).days
            col = "🔴" if d <= 0 else "🟠" if d <= 3 else "🟢"
            with st.container(border=True):
                ci, cw, ce, cd = st.columns([4, 0.8, 0.4, 0.4])
                ci.write(f"{col} **{row['Cliente']}** | {row['Producto']}")
                ci.caption(f"📧 {row['Correo']} | 👤 {row['Perfil']} | 📅 {row['Vencimiento']}")
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                cw.markdown(f'<br><a href="https://wa.me/{row["WhatsApp"]}?text={msj}" class="wa-button">📲 WA</a>', unsafe_allow_html=True)
                if ce.button("📝", key=f"e_{idx}"): editar_venta_popup(idx, row)
                if cd.button("🗑️", key=f"v_{idx}"):
                    df_ventas.drop(idx).to_csv(VENTAS_FILE, index=False); st.rerun()
    else: st.info("Sin ventas.")

with t2:
    st.info("Aquí puedes gestionar tus plataformas y correos de YouTube.")
    # (El código de Inventario y Plataformas iría aquí igual que el anterior)
