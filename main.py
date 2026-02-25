import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NEXA-Stream Pro", layout="wide")

# Estilo CSS para mejorar la estética de los botones y entradas
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; }
    .stTextInput>div>div>input { border-radius: 10px; }
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
    else:
        inv = pd.DataFrame(columns=["Correo", "Password", "Usos"])
    return df, inv

df_ventas, df_inv = cargar_datos()

# --- DIÁLOGOS ---
@st.dialog("¿Finalizar Venta?")
def confirmar_eliminar(index, nombre):
    st.write(f"¿Estás seguro de que deseas eliminar la suscripción de **{nombre}**?")
    c1, c2 = st.columns(2)
    if c1.button("SÍ, ELIMINAR", type="primary"):
        df_final = df_ventas.drop(index)
        df_final.to_csv(VENTAS_FILE, index=False)
        st.rerun()
    if c2.button("CANCELAR"):
        st.rerun()

@st.dialog("Registrar Nueva Venta")
def nueva_venta_popup():
    c1, c2 = st.columns(2)
    prod = c1.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max", "Prime Video"])
    f_ini = c2.date_input("Fecha Inicio", datetime.now())
    
    nom = st.text_input("Nombre del Cliente")
    tel = st.text_input("WhatsApp (ej: 51999888777)")
    
    st.divider()
    st.write("🔑 **Datos de Acceso**")
    
    col_a, col_b = st.columns(2)
    col_c, col_d = st.columns(2)
    
    venc = f_ini + timedelta(days=30)

    # Lógica de Inventario YT
    if prod == "YouTube Premium" and not df_inv.empty:
        disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
        if not disponibles.empty:
            sug = disponibles.iloc[0]
            mail_val = col_a.text_input("Correo", value=sug['Correo'])
            pass_val = col_b.text_input("Contraseña", value=sug['Password'])
        else:
            st.error("No hay correos con cupos!")
            mail_val = col_a.text_input("Correo")
            pass_val = col_b.text_input("Contraseña")
        perf_val = col_c.text_input("Perfil", value="N/A", disabled=True)
        pin_val = col_d.text_input("PIN", value="N/A", disabled=True)
    else:
        mail_val = col_a.text_input("Correo")
        pass_val = col_b.text_input("Contraseña")
        perf_val = col_c.text_input("Perfil")
        pin_val = col_d.text_input("PIN")

    if st.button("GUARDAR VENTA", type="primary"):
        if nom and tel and mail_val:
            nueva = pd.DataFrame([[ "🟢", nom, tel, prod, mail_val, pass_val, perf_val, pin_val, venc ]], 
                                 columns=["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento"])
            pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
            
            if prod == "YouTube Premium" and not df_inv.empty:
                idx = df_inv[df_inv['Correo'] == mail_val].index[0]
                df_inv.at[idx, 'Usos'] += 1
                df_inv.to_csv(INV_FILE, index=False)
            st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.title("🚀 NEXA-Stream Manager")

t1, t2 = st.tabs(["📊 Administración", "📦 Inventario YT"])

with t1:
    # CABECERA ORGANIZADA: Botón Izquierda, Buscador Derecha
    head_col1, head_col2 = st.columns([1, 2])
    
    with head_col1:
        if st.button("➕ NUEVA VENTA", type="primary"):
            nueva_venta_popup()
            
    with head_col2:
        search = st.text_input("", placeholder="🔍 Buscar cliente o cuenta...")

    st.divider()
    
    if not df_ventas.empty:
        mask = df_ventas.apply(lambda row: search.lower() in str(row).lower(), axis=1)
        df_f = df_ventas[mask].sort_values(by="Vencimiento")
        
        hoy = datetime.now().date()
        for index, row in df_f.iterrows():
            dias = (row['Vencimiento'] - hoy).days
            status_color = "🔴" if dias <= 0 else "🟠" if dias <= 3 else "🟢"
            
            with st.container(border=True):
                c_inf, c_wa, c_del = st.columns([4, 1, 0.5])
                with c_inf:
                    st.write(f"{status_color} **{row['Cliente']}** | {row['Producto']}")
                    st.caption(f"📧 {row['Correo']} | 🔑 {row['Pass']} | 👤 {row['Perfil']} | 📍 PIN: {row['PIN']} | 📅 Vence: {row['Vencimiento']}")
                
                with c_wa:
                    msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                    st.markdown(f"<br>[📲 Cobrar](https://wa.me/{row['WhatsApp']}?text={msj})", unsafe_allow_html=True)
                
                if c_del.button("🗑️", key=f"del_{index}"):
                    confirmar_eliminar(index, row['Cliente'])
    else:
        st.info("Lista vacía. Comienza registrando tu primera venta.")

with t2:
    st.subheader("Configuración de Inventario")
    with st.expander("➕ Cargar Gmail"):
        ca, cb, cc = st.columns([2,1,1])
        m = ca.text_input("Gmail")
        p = cb.text_input("Clave")
        u = cc.selectbox("Usos", [0, 1, 2])
        if st.button("Agregar Correo"):
            ni = pd.DataFrame([[m, p, u]], columns=["Correo", "Password", "Usos"])
            pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False)
            st.rerun()
    st.dataframe(df_inv, use_container_width=True)
