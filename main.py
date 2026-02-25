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
        df['Vencimiento'] = pd.to_datetime(df['Vencimiento']).dt.date
    else:
        df = pd.DataFrame(columns=["Estado", "Cliente", "WhatsApp", "Producto", "Detalles", "Vencimiento"])
    
    if os.path.exists(INV_FILE):
        inv = pd.read_csv(INV_FILE)
    else:
        inv = pd.DataFrame(columns=["Correo", "Password", "Usos"])
    return df, inv

df_ventas, df_inv = cargar_datos()

# --- INTERFAZ ---
st.title("🚀 NEXA-Stream: Control Total")

tabs = st.tabs(["📊 Administración General", "📦 Inventario YouTube"])

# --- PESTAÑA 2: INVENTARIO (Configuramos esto primero para tener correos) ---
with tabs[1]:
    st.subheader("Gestión de Correos Gmail")
    with st.expander("➕ Agregar Correo Nuevo"):
        c1, c2 = st.columns(2)
        new_mail = c1.text_input("Correo Gmail")
        new_pass = c2.text_input("Contraseña")
        if st.button("Registrar en Inventario"):
            nuevo_item = pd.DataFrame([[new_mail, new_pass, 0]], columns=["Correo", "Password", "Usos"])
            df_inv = pd.concat([df_inv, nuevo_item], ignore_index=True)
            df_inv.to_csv(INV_FILE, index=False)
            st.success("Correo agregado!")
            st.rerun()

    st.dataframe(df_inv, use_container_width=True)

# --- PESTAÑA 1: ADMINISTRACIÓN (Con Pop-up) ---
with tabs[0]:
    # BOTÓN PARA ABRIR EL POP-UP (Modal)
    if st.button("➕ NUEVA VENTA (Abrir Formulario)"):
        st.dialog("Registro de Venta rápida")

    # CONTENIDO DEL POP-UP (Usando st.dialog)
    @st.dialog("Registrar Venta")
    def nueva_venta_popup():
        col1, col2 = st.columns(2)
        with col1:
            prod = st.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One"])
            nom = st.text_input("Nombre Cliente")
            tel = st.text_input("WhatsApp (ej: 51999...)")
        with col2:
            f_ini = st.date_input("Inicio", datetime.now())
            venc = f_ini + timedelta(days=30)
            
            detalles_final = ""
            if prod == "YouTube Premium" and not df_inv.empty:
                # Lógica: elegir el que tiene menos usos
                sugerido = df_inv.sort_values(by="Usos").iloc[0]
                detalles_final = f"Cuenta: {sugerido['Correo']} | Clave: {sugerido['Password']}"
                st.info(f"Asignado: {sugerido['Correo']}")
            else:
                detalles_final = st.text_area("Datos de la cuenta")

        if st.button("CONFIRMAR Y GUARDAR"):
            # Guardar Venta
            nueva = pd.DataFrame([["🟢 ACTIVO", nom, tel, prod, detalles_final, venc]], 
                                 columns=["Estado", "Cliente", "WhatsApp", "Producto", "Detalles", "Vencimiento"])
            df_v = pd.concat([df_ventas, nueva], ignore_index=True)
            df_v.to_csv(VENTAS_FILE, index=False)
            
            # Si fue YouTube, sumamos un uso al inventario
            if prod == "YouTube Premium" and not df_inv.empty:
                idx = df_inv.sort_values(by="Usos").index[0]
                df_inv.at[idx, 'Usos'] += 1
                df_inv.to_csv(INV_FILE, index=False)
            
            st.success("Venta Exitosa")
            st.rerun()

    if "abrir_form" in st.session_state:
        nueva_venta_popup()

    # --- TABLA DE VENTAS CON ALERTAS ---
    st.divider()
    hoy = datetime.now().date()
    
    if not df_ventas.empty:
        # Lógica de colores
        def get_status(v):
            d = (v - hoy).days
            if d <= 0: return "🔴 VENCIDO"
            if d <= 3: return "🟠 COBRAR"
            return "🟢 ACTIVO"

        df_ventas['Estado'] = df_ventas['Vencimiento'].apply(get_status)
        df_display = df_ventas.sort_values(by="Vencimiento")

        for _, row in df_display.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                c1.write(f"**{row['Estado']}**")
                c2.write(f"👤 {row['Cliente']} | 📺 {row['Producto']}\n\n📅 Vence: {row['Vencimiento']}")
                
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                link = f"https://wa.me/{row['WhatsApp']}?text={msj}"
                c3.markdown(f"[📲 Cobrar]({link})")
    else:
        st.info("Aún no tienes ventas registradas.")
