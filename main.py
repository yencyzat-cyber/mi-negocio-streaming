import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# CONFIGURACIÓN Y ESTILO
st.set_page_config(page_title="NEXA-Stream", layout="wide")

# ARCHIVO LOCAL PARA GUARDAR DATOS (Costo 0)
DATA_FILE = "ventas_data.csv"

# CARGAR DATOS
if os.path.exists(DATA_FILE):
    df_ventas = pd.read_csv(DATA_FILE)
    df_ventas['Vencimiento'] = pd.to_datetime(df_ventas['Vencimiento']).dt.date
else:
    df_ventas = pd.DataFrame(columns=["Estado", "Cliente", "WhatsApp", "Producto", "Detalles", "Vencimiento"])

# LISTA DE CORREOS YOUTUBE (Puedes editar esto después)
if 'inventario_yt' not in st.session_state:
    st.session_state.inventario_yt = [
        {"correo": "ejemplo1@gmail.com", "pass": "123", "usos": 0},
        {"correo": "ejemplo2@gmail.com", "pass": "456", "usos": 0}
    ]

# INTERFAZ
st.title("📱 NEXA-Stream Manager")

# REGISTRO
with st.expander("➕ NUEVA VENTA"):
    col1, col2 = st.columns(2)
    with col1:
        prod = st.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One"])
        nom = st.text_input("Nombre Cliente")
        tel = st.text_input("WhatsApp (ej: 51999888777)")
    with col2:
        f_ini = st.date_input("Inicio", datetime.now())
        venc = f_ini + timedelta(days=30)
        
        if prod == "YouTube Premium":
            correo_sug = sorted(st.session_state.inventario_yt, key=lambda x: x['usos'])[0]
            detalles = f"Cuenta: {correo_sug['correo']} | Clave: {correo_sug['pass']}"
            st.info(f"Sugerido: {correo_sug['correo']}")
        else:
            detalles = st.text_area("Datos (Correo/Pass/Perfil)")

    if st.button("GUARDAR EN EL SISTEMA"):
        nueva = pd.DataFrame([[ "🟢 ACTIVO", nom, tel, prod, detalles, venc ]], 
                             columns=["Estado", "Cliente", "WhatsApp", "Producto", "Detalles", "Vencimiento"])
        df_ventas = pd.concat([df_ventas, nueva], ignore_index=True)
        df_ventas.to_csv(DATA_FILE, index=False)
        st.success("¡Venta Guardada!")

# TABLA CENTRALIZADA
st.subheader("📋 Administración General")
hoy = datetime.now().date()

def aplicar_color(row):
    diff = (row['Vencimiento'] - hoy).days
    if diff <= 0: return "🔴 VENCIDO"
    if diff <= 3: return "🟠 COBRAR"
    return "🟢 ACTIVO"

if not df_ventas.empty:
    df_ventas['Estado'] = df_ventas.apply(aplicar_color, axis=1)
    df_ventas = df_ventas.sort_values(by="Vencimiento")
    
    for index, row in df_ventas.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
            c1.write(row['Estado'])
            c2.write(f"**{row['Cliente']}** ({row['Producto']})")
            c3.write(row['Vencimiento'])
            # Botón WhatsApp
            msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
            link = f"https://wa.me/{row['WhatsApp']}?text={msj}"
            c4.markdown(f"[📲 Cobrar]({link})")
            st.divider()
