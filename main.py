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

# --- DIÁLOGOS ---
@st.dialog("¿Eliminar Venta?")
def confirmar_eliminar(index, nombre):
    st.warning(f"¿Finalizar venta de **{nombre}**?")
    if st.button("SÍ, ELIMINAR", type="primary"):
        df_final = df_ventas.drop(index)
        df_final.to_csv(VENTAS_FILE, index=False)
        st.rerun()

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
    c_mail, c_pass = st.columns(2)
    c_perf, c_pin = st.columns(2)

    if prod == "YouTube Premium" and not df_inv.empty:
        # Filtrar solo los que tienen menos de 2 usos
        disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
        if not disponibles.empty:
            sugerido = disponibles.iloc[0]
            mail_val = c_mail.text_input("Correo", value=sugerido['Correo'])
            pass_val = c_pass.text_input("Contraseña", value=sugerido['Password'])
        else:
            st.error("⚠️ No hay correos con cupos disponibles en inventario.")
            mail_val = c_mail.text_input("Correo")
            pass_val = c_pass.text_input("Contraseña")
        perf_val = "N/A"
        pin_val = "N/A"
    else:
        mail_val = c_mail.text_input("Correo")
        pass_val = c_pass.text_input("Contraseña")
        perf_val = c_perf.text_input("Perfil")
        pin_val = c_pin.text_input("PIN")

    if st.button("GUARDAR VENTA", use_container_width=True, type="primary"):
        if nom and tel and mail_val:
            nueva = pd.DataFrame([[ "🟢", nom, tel, prod, mail_val, pass_val, perf_val, pin_val, venc ]], 
                                 columns=["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento"])
            pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
            
            if prod == "YouTube Premium" and not df_inv.empty:
                idx = df_inv[df_inv['Correo'] == mail_val].index[0]
                df_inv.at[idx, 'Usos'] += 1
                df_inv.to_csv(INV_FILE, index=False)
            st.rerun()

# --- INTERFAZ ---
st.title("🚀 NEXA-Stream Manager")
t1, t2 = st.tabs(["📊 Administración", "📦 Inventario YT"])

with t2:
    st.subheader("Control de Inventario YouTube")
    with st.expander("➕ Cargar Correo Existente o Nuevo"):
        c1, c2, c3 = st.columns([2, 1, 1])
        m = c1.text_input("Gmail")
        p = c2.text_input("Clave")
        u = c3.selectbox("Usos actuales", [0, 1, 2], help="0=Nuevo, 1=Usado una vez, 2=Agotado")
        if st.button("Agregar al Inventario"):
            ni = pd.DataFrame([[m, p, u]], columns=["Correo", "Password", "Usos"])
            pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False)
            st.success("Guardado")
            st.rerun()
    
    # Mostrar tabla de inventario con colores según uso
    def color_usos(val):
        color = 'green' if val == 0 else 'orange' if val == 1 else 'red'
        return f'color: {color}; font-weight: bold'
    
    st.dataframe(df_inv.style.applymap(color_usos, subset=['Usos']), use_container_width=True)

with t1:
    col_bus, col_add = st.columns([3, 1])
    search = col_bus.text_input("🔍 Buscar cliente o plataforma...")
    if col_add.button("➕ NUEVA VENTA", type="primary", use_container_width=True):
        nueva_venta_popup()

    st.divider()
    hoy = datetime.now().date()
    
    if not df_ventas.empty:
        # Filtrar por búsqueda
        mask = df_ventas.apply(lambda row: search.lower() in str(row).lower(), axis=1)
        df_filtrado = df_ventas[mask].sort_values(by="Vencimiento")

        for index, row in df_filtrado.iterrows():
            dias = (row['Vencimiento'] - hoy).days
            color = "🔴" if dias <= 0 else "🟠" if dias <= 3 else "🟢"
            
            with st.container(border=True):
                c_inf, c_wa, c_del = st.columns([4, 1, 0.5])
                with c_inf:
                    st.write(f"{color} **{row['Cliente']}** | {row['Producto']} (Vence: {row['Vencimiento']})")
                    st.caption(f"📧 {row['Correo']} | 🔑 {row['Pass']} | 👤 {row['Perfil']} | 📍 PIN: {row['PIN']}")
                
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
                c_wa.markdown(f"<br>[📲 Cobrar](https://wa.me/{row['WhatsApp']}?text={msj})", unsafe_allow_html=True)
                
                if c_del.button("🗑️", key=f"del_{index}"):
                    confirmar_eliminar(index, row['Cliente'])
    else:
        st.info("Lista vacía.")
