import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NEXA-Stream Pro", layout="wide")

# ARCHIVOS DE DATOS
VENTAS_FILE = "ventas_data.csv"
INV_FILE = "inventario_yt.csv"

# CARGAR DATOS
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

# --- DIÁLOGO DE CONFIRMACIÓN PARA ELIMINAR ---
@st.dialog("¿Eliminar Venta?")
def confirmar_eliminar(index, nombre):
    st.warning(f"¿Estás seguro de que deseas finalizar la venta de **{nombre}**? Esta acción no se puede deshacer.")
    if st.button("SÍ, ELIMINAR DEFINITIVAMENTE", type="primary"):
        df_final = df_ventas.drop(index)
        df_final.to_csv(VENTAS_FILE, index=False)
        st.success("Venta eliminada correctamente.")
        st.rerun()

# --- DIÁLOGO DE NUEVA VENTA (ESTRUCTURADO) ---
@st.dialog("Registrar Nueva Venta")
def nueva_venta_popup():
    col1, col2 = st.columns(2)
    with col1:
        prod = st.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max", "Prime Video"])
        nom = st.text_input("Nombre Cliente")
        tel = st.text_input("WhatsApp (ej: 51999888777)")
    with col2:
        f_ini = st.date_input("Inicio", datetime.now())
        venc = f_ini + timedelta(days=30)

    st.divider()
    st.subheader("Datos de Acceso")
    
    c_mail, c_pass = st.columns(2)
    c_perf, c_pin = st.columns(2)

    # Lógica Automática para YouTube
    if prod == "YouTube Premium" and not df_inv.empty:
        sugerido = df_inv.sort_values(by="Usos").iloc[0]
        mail_val = c_mail.text_input("Correo", value=sugerido['Correo'])
        pass_val = c_pass.text_input("Contraseña", value=sugerido['Password'])
        perf_val = c_perf.text_input("Perfil", value="N/A", disabled=True)
        pin_val = c_pin.text_input("PIN", value="N/A", disabled=True)
    else:
        mail_val = c_mail.text_input("Correo")
        pass_val = c_pass.text_input("Contraseña")
        perf_val = c_perf.text_input("Perfil (Ej: Perfil 3)")
        pin_val = c_pin.text_input("PIN (Ej: 1234)")

    if st.button("CONFIRMAR Y GUARDAR VENTA", use_container_width=True, type="primary"):
        if nom and tel and mail_val:
            nueva = pd.DataFrame([[ "🟢 ACTIVO", nom, tel, prod, mail_val, pass_val, perf_val, pin_val, venc ]], 
                                 columns=["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento"])
            df_actualizado = pd.concat([df_ventas, nueva], ignore_index=True)
            df_actualizado.to_csv(VENTAS_FILE, index=False)
            
            if prod == "YouTube Premium" and not df_inv.empty:
                idx = df_inv.sort_values(by="Usos").index[0]
                df_inv.at[idx, 'Usos'] += 1
                df_inv.to_csv(INV_FILE, index=False)
            
            st.success("¡Venta Guardada!")
            st.rerun()
        else:
            st.error("Faltan datos obligatorios (Nombre, WhatsApp, Correo)")

# --- INTERFAZ PRINCIPAL ---
st.title("🚀 NEXA-Stream Manager")
t1, t2 = st.tabs(["📊 Ventas", "📦 Inventario YT"])

with t2:
    st.subheader("Configuración de Gmails para YouTube")
    with st.expander("➕ Agregar Correo a Rotación"):
        c1, c2 = st.columns(2)
        m = c1.text_input("Nuevo Gmail")
        p = c2.text_input("Nueva Clave")
        if st.button("Guardar en Inventario"):
            ni = pd.DataFrame([[m, p, 0]], columns=["Correo", "Password", "Usos"])
            df_inv = pd.concat([df_inv, ni], ignore_index=True)
            df_inv.to_csv(INV_FILE, index=False)
            st.rerun()
    st.dataframe(df_inv, use_container_width=True)

with t1:
    if st.button("➕ NUEVA VENTA", type="primary"):
        nueva_venta_popup()

    st.divider()
    hoy = datetime.now().date()
    
    if not df_ventas.empty:
        df_ventas['Vencimiento'] = pd.to_datetime(df_ventas['Vencimiento']).dt.date
        for index, row in df_ventas.sort_values(by="Vencimiento").iterrows():
            dias = (row['Vencimiento'] - hoy).days
            color = "🔴" if dias <= 0 else "🟠" if dias <= 3 else "🟢"
            
            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.write(f"{color} **{row['Cliente']}** | {row['Producto']} (Vence: {row['Vencimiento']})")
                    st.caption(f"📧 {row['Correo']} | 🔑 {row['Pass']} | 👤 {row['Perfil']} | 📍 PIN: {row['PIN']}")
                
                with col_btn:
                    # Link WhatsApp
                    msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                    st.markdown(f"[📲 Cobrar](https://wa.me/{row['WhatsApp']}?text={msj})")
                    # Botón Finalizar con confirmación
                    if st.button("🗑️", key=f"del_{index}"):
                        confirmar_eliminar(index, row['Cliente'])
    else:
        st.info("Sin ventas activas.")
