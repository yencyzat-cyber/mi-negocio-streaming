import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="NEXA-Stream Pro", layout="wide")

# CSS simplificado: Ahora usamos botones nativos para todo, garantizando alineación perfecta
st.markdown("""
    <style>
    .stButton>button, .stLinkButton>a { 
        border-radius: 8px; 
        height: 35px; 
        width: 100%; 
        font-size: 13px; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        padding: 0;
    }
    .stTextInput>div>div>input { border-radius: 8px; height: 35px; }
    </style>
    """, unsafe_allow_html=True)

# --- ARCHIVOS DE DATOS LOCALES ---
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

# --- INTERFAZ PRINCIPAL ---
st.title("🚀 NEXA-Stream Manager")

# SELECTOR DE VISTA (Móvil vs PC)
vista_actual = st.radio("🖥️ / 📱 Selecciona tu modo de vista:", ["📱 Vista Celular (Compacta)", "💻 Vista PC (Expandida)"], horizontal=True)
st.divider()

t1, t2 = st.tabs(["📊 Administración de Ventas", "⚙️ Configuración e Inventario"])

with t1:
    h1, h2 = st.columns([1, 2])
    if h1.button("➕ NUEVA VENTA", type="primary"): nueva_venta_popup()
    search = h2.text_input("", placeholder="🔍 Buscar cliente, plataforma...", label_visibility="collapsed")
    st.divider()
    
    if not df_ventas.empty:
        mask = df_ventas.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        hoy = datetime.now().date()
        for idx, row in df_ventas[mask].sort_values(by="Vencimiento").iterrows():
            d = (row['Vencimiento'] - hoy).days
            col = "🔴" if d <= 0 else "🟠" if d <= 3 else "🟢"
            
            msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}.%20¿Renovamos?"
            wa_enlace = f"https://wa.me/{row['WhatsApp']}?text={msj}"
            
            with st.container(border=True):
                if vista_actual == "📱 Vista Celular (Compacta)":
                    # VISTA MÓVIL: Tarjeta apilada, botones abajo alineados
                    ci = st.container()
                    ci.write(f"{col} **{row['Cliente']}** | {row['Producto']}")
                    ci.caption(f"📧 {row['Correo']} | 📅 Vence: {row['Vencimiento']}")
                    
                    # Fila de botones milimétricamente alineada
                    cw, ce, cd = st.columns([2, 1, 1])
                    cw.link_button("📲 WA", wa_enlace, use_container_width=True)
                    if ce.button("📝", key=f"e_{idx}", use_container_width=True): editar_venta_popup(idx, row)
                    if cd.button("🗑️", key=f"v_{idx}", use_container_width=True):
                        df_ventas.drop(idx).to_csv(VENTAS_FILE, index=False); st.rerun()
                
                else:
                    # VISTA PC: Todo en una sola línea ancha
                    col1, col2, col3, cw, ce, cd = st.columns([2, 2, 2, 1, 0.5, 0.5])
                    col1.write(f"{col} **{row['Cliente']}**")
                    col2.write(f"📺 {row['Producto']}")
                    col3.write(f"📅 Vence: {row['Vencimiento']}")
                    cw.link_button("📲 WhatsApp", wa_enlace, use_container_width=True)
                    if ce.button("📝 Editar", key=f"e_pc_{idx}", use_container_width=True): editar_venta_popup(idx, row)
                    if cd.button("🗑️ Borrar", key=f"v_pc_{idx}", use_container_width=True):
                        df_ventas.drop(idx).to_csv(VENTAS_FILE, index=False); st.rerun()
    else: st.info("No hay ventas registradas.")

with t2:
    b1, b2 = st.columns(2)
    csv_ventas = df_ventas.to_csv(index=False).encode('utf-8')
    csv_inv = df_inv.to_csv(index=False).encode('utf-8')
    b1.download_button("📥 Descargar Backup Ventas", data=csv_ventas, file_name="backup_ventas.csv", mime="text/csv", use_container_width=True)
    b2.download_button("📥 Descargar Backup Inventario", data=csv_inv, file_name="backup_inventario.csv", mime="text/csv", use_container_width=True)
    
    st.divider()
    col_inv, col_plat = st.columns([2, 1]) if vista_actual == "💻 Vista PC (Expandida)" else st.columns([1, 1])
    
    with col_plat:
        st.subheader("🛠 Plataformas")
        nueva_p = st.text_input("Agregar Plataforma")
        if st.button("Añadir", use_container_width=True):
            if nueva_p and nueva_p not in lista_plataformas:
                lista_plataformas.append(nueva_p)
                pd.DataFrame(lista_plataformas, columns=["Nombre"]).to_csv(PLAT_FILE, index=False)
                st.rerun()
        st.write("---")
        for p in lista_plataformas:
            cp1, cp2 = st.columns([3, 1])
            cp1.write(p)
            if cp2.button("🗑️", key=f"del_p_{p}", use_container_width=True):
                lista_plataformas.remove(p)
                pd.DataFrame(lista_plataformas, columns=["Nombre"]).to_csv(PLAT_FILE, index=False)
                st.rerun()

    with col_inv:
        st.subheader("📦 Inventario YouTube")
        if st.button("➕ AGREGAR CORREO YT", use_container_width=True):
            @st.dialog("Nuevo Gmail")
            def add_yt():
                m, p = st.text_input("Gmail"), st.text_input("Clave")
                u = st.selectbox("Usos iniciales", [0,1,2])
                if st.button("GUARDAR"):
                    ni = pd.DataFrame([[m, p, u, "Nadie"]], columns=df_inv.columns)
                    pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False); st.rerun()
            add_yt()
            
        for idx, row in df_inv.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1]) if vista_actual == "📱 Vista Celular (Compacta)" else st.columns([4, 0.5, 0.5])
                c1.write(f"📧 **{row['Correo']}** (Usos: {row['Usos']})")
                c1.caption(f"👤 Asignado a: {row['Asignado_A']}")
                if c2.button("📝", key=f"ed_i_{idx}", use_container_width=True):
                    @st.dialog("Editar")
                    def edit_inv():
                        nu = st.selectbox("Usos", [0,1,2], index=int(row['Usos']))
                        na = st.text_input("Asignado a", value=row['Asignado_A'])
                        if st.button("GUARDAR"):
                            df_inv.at[idx, 'Usos'], df_inv.at[idx, 'Asignado_A'] = nu, na
                            df_inv.to_csv(INV_FILE, index=False); st.rerun()
                    edit_inv()
                if c3.button("🗑️", key=f"del_i_{idx}", use_container_width=True):
                    df_inv.drop(idx).to_csv(INV_FILE, index=False); st.rerun()
