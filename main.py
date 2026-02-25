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
        # Convertir a fecha y manejar errores
        df['Vencimiento'] = pd.to_datetime(df['Vencimiento'], errors='coerce').dt.date
    else:
        df = pd.DataFrame(columns=["Estado", "Cliente", "WhatsApp", "Producto", "Detalles", "Vencimiento"])
    
    if os.path.exists(INV_FILE):
        inv = pd.read_csv(INV_FILE)
    else:
        inv = pd.DataFrame(columns=["Correo", "Password", "Usos"])
    return df, inv

df_ventas, df_inv = cargar_datos()

# --- LÓGICA DEL POP-UP (DEFINICIÓN) ---
@st.dialog("Registrar Nueva Venta")
def nueva_venta_popup():
    col1, col2 = st.columns(2)
    with col1:
        prod = st.selectbox("Plataforma", ["YouTube Premium", "Netflix", "Disney+", "Google One", "HBO Max"])
        nom = st.text_input("Nombre Cliente")
        tel = st.text_input("WhatsApp (ej: 51999888777)")
    with col2:
        f_ini = st.date_input("Inicio", datetime.now())
        venc = f_ini + timedelta(days=30)
        
        detalles_final = ""
        if prod == "YouTube Premium" and not df_inv.empty:
            # Seleccionar el correo con menos usos
            sugerido = df_inv.sort_values(by="Usos").iloc[0]
            detalles_final = f"Cuenta: {sugerido['Correo']} | Clave: {sugerido['Password']}"
            st.info(f"Sugerido: {sugerido['Correo']}")
        else:
            detalles_final = st.text_area("Datos de la cuenta (Correo/Pass/Perfil)")

    if st.button("CONFIRMAR Y GUARDAR"):
        if nom and tel:
            nueva = pd.DataFrame([[ "🟢 ACTIVO", nom, tel, prod, detalles_final, venc ]], 
                                 columns=["Estado", "Cliente", "WhatsApp", "Producto", "Detalles", "Vencimiento"])
            df_actualizado = pd.concat([df_ventas, nueva], ignore_index=True)
            df_actualizado.to_csv(VENTAS_FILE, index=False)
            
            # Sumar uso si es YouTube
            if prod == "YouTube Premium" and not df_inv.empty:
                idx = df_inv.sort_values(by="Usos").index[0]
                df_inv.at[idx, 'Usos'] += 1
                df_inv.to_csv(INV_FILE, index=False)
            
            st.success("¡Venta Guardada!")
            st.rerun()
        else:
            st.error("Por favor llena Nombre y WhatsApp")

# --- INTERFAZ ---
st.title("🚀 NEXA-Stream: Control Total")

tabs = st.tabs(["📊 Administración General", "📦 Inventario YouTube"])

# --- PESTAÑA 2: INVENTARIO ---
with tabs[1]:
    st.subheader("Gestión de Correos Gmail")
    with st.expander("➕ Agregar Correo Nuevo"):
        c1, c2 = st.columns(2)
        new_mail = c1.text_input("Correo Gmail")
        new_pass = c2.text_input("Contraseña")
        if st.button("Registrar en Inventario"):
            nuevo_item = pd.DataFrame([[new_mail, new_pass, 0]], columns=["Correo", "Password", "Usos"])
            df_inv_new = pd.concat([df_inv, nuevo_item], ignore_index=True)
            df_inv_new.to_csv(INV_FILE, index=False)
            st.success("Correo agregado!")
            st.rerun()

    st.dataframe(df_inv, use_container_width=True)

# --- PESTAÑA 1: ADMINISTRACIÓN ---
with tabs[0]:
    # El botón ahora dispara el diálogo directamente
    if st.button("➕ NUEVA VENTA (Abrir Formulario)", type="primary"):
        nueva_venta_popup()

    st.divider()
    hoy = datetime.now().date()
    
    if not df_ventas.empty:
        # Re-calcular estados antes de mostrar
        def get_status(v):
            if pd.isna(v): return "⚪ SIN FECHA"
            d = (v - hoy).days
            if d <= 0: return "🔴 VENCIDO"
            if d <= 3: return "🟠 COBRAR"
            return "🟢 ACTIVO"

        df_ventas['Estado'] = df_ventas['Vencimiento'].apply(get_status)
        df_display = df_ventas.sort_values(by="Vencimiento")

        for index, row in df_display.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
                
                c1.subheader(row['Estado'])
                c2.write(f"👤 **{row['Cliente']}** | 📺 {row['Producto']}")
                c2.write(f"🔑 {row['Detalles']}")
                c2.write(f"📅 Vence: {row['Vencimiento']}")
                
                # Botón WhatsApp
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                link = f"https://wa.me/{row['WhatsApp']}?text={msj}"
                c3.markdown(f"[📲 Cobrar]({link})")
                
                # BOTÓN FINALIZAR (Borrar)
                if c4.button("🗑️ Finalizar", key=f"del_{index}"):
                    df_final = df_ventas.drop(index)
                    df_final.to_csv(VENTAS_FILE, index=False)
                    st.warning(f"Venta de {row['Cliente']} eliminada.")
                    st.rerun()
    else:
        st.info("No hay ventas registradas. Usa el botón de arriba para empezar.")
