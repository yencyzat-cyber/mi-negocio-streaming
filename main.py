import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import random
import string

# ==============================================================================
# BLOQUE 1: CONFIGURACIÓN Y VERSIÓN
# ==============================================================================
VERSION_APP = "1.4 (Gestión de Personal y Accesos)"

st.set_page_config(page_title="NEXA-Stream Manager", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# BLOQUE 2: CSS MÓVIL Y ESTILOS
# ==============================================================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important; flex-wrap: nowrap !important; gap: 5px !important;
    }
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 33.33% !important; min-width: 0 !important; flex: 1 1 0px !important;
    }
    .stButton>button, .stLinkButton>a {
        border-radius: 8px !important; height: 40px !important; padding: 0px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        width: 100% !important; font-size: 18px !important; margin: 0px !important;
    }
    .stLinkButton>a { background-color: #25D366 !important; color: white !important; border: none !important; }
    .stTextInput>div>div>input { border-radius: 8px; height: 38px; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# BLOQUE 3: FUNCIONES DE DATOS Y SEGURIDAD
# ==============================================================================
VENTAS_FILE = "ventas_data.csv"
INV_FILE = "inventario_yt.csv"
PLAT_FILE = "plataformas.csv"
USUARIOS_FILE = "usuarios.csv"

def generar_password_aleatoria(longitud=6):
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for i in range(longitud))

def cargar_datos():
    if os.path.exists(VENTAS_FILE):
        df = pd.read_csv(VENTAS_FILE)
        df['Vencimiento'] = pd.to_datetime(df['Vencimiento'], errors='coerce').dt.date
        if 'Vendedor' not in df.columns:
            df['Vendedor'] = 'admin'
            df.to_csv(VENTAS_FILE, index=False)
    else:
        df = pd.DataFrame(columns=["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento", "Vendedor"])
    
    if os.path.exists(INV_FILE): inv = pd.read_csv(INV_FILE)
    else: inv = pd.DataFrame(columns=["Correo", "Password", "Usos", "Asignado_A"])
        
    if os.path.exists(PLAT_FILE): plat = pd.read_csv(PLAT_FILE)['Nombre'].tolist()
    else:
        plat = ["YouTube Premium", "Netflix", "Disney+", "Google One", "Spotify"]
        pd.DataFrame(plat, columns=["Nombre"]).to_csv(PLAT_FILE, index=False)
        
    return df, inv, plat

df_ventas, df_inv, lista_plataformas = cargar_datos()

def limpiar_whatsapp(numero):
    solo_numeros = re.sub(r'\D', '', str(numero))
    if len(solo_numeros) == 9: return f"51{solo_numeros}"
    return solo_numeros

# ==============================================================================
# BLOQUE 4: SISTEMA DE LOGIN Y SESIÓN
# ==============================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.role = ""
    st.session_state.acceso_yt = "Si"

# Parcheamos el CSV de usuarios para asegurar que existan las columnas nuevas
if not os.path.exists(USUARIOS_FILE):
    pd.DataFrame([["admin", "admin123", "Admin", "N/A", "Si"]], columns=["Usuario", "Password", "Rol", "Telefono", "Acceso_YT"]).to_csv(USUARIOS_FILE, index=False)

df_usuarios = pd.read_csv(USUARIOS_FILE)
cambios_db_usr = False
if 'Telefono' not in df_usuarios.columns:
    df_usuarios['Telefono'] = "N/A"
    cambios_db_usr = True
if 'Acceso_YT' not in df_usuarios.columns:
    df_usuarios['Acceso_YT'] = "No" # Por defecto los viejos vendedores no tienen acceso
    df_usuarios.loc[df_usuarios['Rol'] == 'Admin', 'Acceso_YT'] = "Si"
    cambios_db_usr = True
if cambios_db_usr:
    df_usuarios.to_csv(USUARIOS_FILE, index=False)

# --- PANTALLA DE BLOQUEO ---
if not st.session_state.logged_in:
    st.title("🔐 Portal NEXA-Stream")
    st.caption(f"Versión: {VERSION_APP}")
    with st.container(border=True):
        st.subheader("Iniciar Sesión")
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Contraseña", type="password")
        if st.button("Acceder", type="primary", use_container_width=True):
            match = df_usuarios[(df_usuarios['Usuario'] == u_in) & (df_usuarios['Password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user = match.iloc[0]['Usuario']
                st.session_state.role = match.iloc[0]['Rol']
                st.session_state.acceso_yt = match.iloc[0]['Acceso_YT']
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas.")
    st.stop()

# ==============================================================================
# BLOQUE 5: DIÁLOGOS DE GESTIÓN
# ==============================================================================
@st.dialog("Editar Registro")
def editar_venta_popup(idx, row):
    prod = st.selectbox("Plataforma", lista_plataformas, index=lista_plataformas.index(row['Producto']) if row['Producto'] in lista_plataformas else 0)
    nom = st.text_input("Nombre", value=row['Cliente'])
    tel = st.text_input("WhatsApp", value=row['WhatsApp'])
    venc = st.date_input("Vencimiento", row['Vencimiento'])
    st.divider()
    m = st.text_input("Correo", value=row['Correo'])
    p = st.text_input("Pass", value=row['Pass'])
    perf = st.text_input("Perfil", value=row['Perfil'])
    if st.button("ACTUALIZAR", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Cliente'], df_ventas.at[idx, 'WhatsApp'] = nom, limpiar_whatsapp(tel)
        df_ventas.at[idx, 'Producto'], df_ventas.at[idx, 'Vencimiento'] = prod, venc
        df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'], df_ventas.at[idx, 'Perfil'] = m, p, perf
        df_ventas.to_csv(VENTAS_FILE, index=False)
        st.rerun()

@st.dialog("Nueva Venta")
def nueva_venta_popup():
    c1, c2 = st.columns(2)
    with c1: prod = st.selectbox("Plataforma", lista_plataformas)
    with c2: f_ini = st.date_input("Inicio", datetime.now())
    nom = st.text_input("Nombre Cliente")
    tel = st.text_input("WhatsApp (ej: 999888777)")
    dur = st.radio("Plazo:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    if dur == "1 Mes": venc = f_ini + timedelta(days=30)
    elif dur == "2 Meses": venc = f_ini + timedelta(days=60)
    elif dur == "6 Meses": venc = f_ini + timedelta(days=180)
    else: venc = f_ini + timedelta(days=365)
    
    st.divider()
    ca, cb = st.columns(2)
    
    # LÓGICA DE ACCESO A YOUTUBE
    tiene_acceso_inventario = (st.session_state.role == "Admin") or (st.session_state.acceso_yt == "Si")
    
    if prod == "YouTube Premium":
        if tiene_acceso_inventario:
            if not df_inv.empty:
                disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
                if not disponibles.empty:
                    sug = disponibles.iloc[0]
                    with ca: mv = st.text_input("Correo Auto-asignado", value=sug['Correo'])
                    with cb: pv = st.text_input("Clave", value=sug['Password'])
                else: 
                    st.warning("No hay cupos en el inventario. Ingresa manual.")
                    with ca: mv = st.text_input("Correo")
                    with cb: pv = st.text_input("Pass")
            else:
                st.warning("Inventario vacío. Ingresa manual.")
                with ca: mv = st.text_input("Correo")
                with cb: pv = st.text_input("Pass")
        else:
            st.info("🔒 No tienes acceso al inventario automático. Registra la cuenta asignada manualmente.")
            with ca: mv = st.text_input("Correo Asignado")
            with cb: pv = st.text_input("Clave")
    else: 
        with ca: mv = st.text_input("Correo")
        with cb: pv = st.text_input("Pass")
    
    if st.button("REGISTRAR VENTA", type="primary", use_container_width=True):
        nueva = pd.DataFrame([[ "🟢", nom, limpiar_whatsapp(tel), prod, mv, pv, "nan", "nan", venc, st.session_state.user ]], columns=df_ventas.columns)
        pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
        st.rerun()

# --- DIÁLOGO PARA EDITAR VENDEDORES ---
@st.dialog("Editar Vendedor")
def editar_vendedor_popup(idx, row):
    st.write(f"Editando a: **{row['Usuario']}**")
    n_tel = st.text_input("Teléfono", value=row['Telefono'])
    n_pwd = st.text_input("Nueva Contraseña (Dejar igual si no quieres cambiar)", value=row['Password'])
    n_acc = st.checkbox("✅ Dar acceso al Inventario automático de YouTube", value=(row['Acceso_YT'] == 'Si'))
    
    if st.button("Actualizar Perfil", type="primary", use_container_width=True):
        df_usuarios.at[idx, 'Telefono'] = n_tel
        df_usuarios.at[idx, 'Password'] = n_pwd
        df_usuarios.at[idx, 'Acceso_YT'] = "Si" if n_acc else "No"
        df_usuarios.to_csv(USUARIOS_FILE, index=False)
        st.success("Actualizado")
        st.rerun()

# ==============================================================================
# BLOQUE 6: NAVEGACIÓN LATERAL
# ==============================================================================
with st.sidebar:
    st.title("🚀 NEXA-Stream")
    st.caption(f"Usuario: {st.session_state.user} | Rol: {st.session_state.role}")
    st.divider()
    
    # Construcción dinámica del menú
    menu_opciones = ["📊 Panel de Ventas"]
    if st.session_state.role == "Admin" or st.session_state.acceso_yt == "Si":
        menu_opciones.append("📦 Inventario YT")
    if st.session_state.role == "Admin":
        menu_opciones.append("👥 Gestión de Vendedores")
        menu_opciones.append("⚙️ Configuración")
        
    menu = st.radio("Navegación", menu_opciones, label_visibility="collapsed")
    
    st.divider()
    vista = st.radio("Dispositivo:", ["📱 Móvil", "💻 PC"], horizontal=True)
    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==============================================================================
# VISTAS PRINCIPALES
# ==============================================================================

# --- VISTA 1: VENTAS ---
if menu == "📊 Panel de Ventas":
    st.header("Gestión de Suscripciones")
    h1, h2 = st.columns([1, 2])
    with h1: 
        if st.button("➕ NUEVA VENTA", type="primary", use_container_width=True): nueva_venta_popup()
    with h2: 
        search = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed")
    
    if st.session_state.role == "Admin":
        filtro_admin = st.selectbox("Vista de datos:", ["Todos los vendedores", f"Solo mis ventas ({st.session_state.user})"])
        df_mostrar = df_ventas if filtro_admin == "Todos los vendedores" else df_ventas[df_ventas['Vendedor'] == st.session_state.user]
    else:
        df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]

    st.write("---")
    if not df_mostrar.empty:
        mask = df_mostrar.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        for idx, row in df_mostrar[mask].sort_values(by="Vencimiento").iterrows():
            hoy = datetime.now().date()
            d = (row['Vencimiento'] - hoy).days
            col = "🔴" if d <= 0 else "🟠" if d <= 3 else "🟢"
            
            with st.container(border=True):
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}."
                wa_url = f"https://wa.me/{row['WhatsApp']}?text={msj}"
                vendedor_badge = f" 🧑‍💼 {row['Vendedor']}" if st.session_state.role == "Admin" and filtro_admin == "Todos los vendedores" else ""

                if vista == "📱 Móvil":
                    st.write(f"{col} **{row['Cliente']}** | {row['Producto']}")
                    st.caption(f"📧 {row['Correo']} | 📅 {row['Vencimiento']}{vendedor_badge}")
                    st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                    cols = st.columns(3)
                    with cols[0]: st.link_button("📲", wa_url, use_container_width=True)
                    with cols[1]: 
                        if st.button("📝", key=f"e_{idx}", use_container_width=True): editar_venta_popup(idx, row)
                    with cols[2]:
                        if st.button("🗑️", key=f"v_{idx}", use_container_width=True):
                            df_ventas.drop(idx).to_csv(VENTAS_FILE, index=False); st.rerun()
                else:
                    c1, c2, c3, c4, c5 = st.columns([3, 1.5, 0.5, 0.5, 0.5])
                    with c1: st.write(f"{col} **{row['Cliente']}** | 📧 {row['Correo']}{vendedor_badge}")
                    with c2: st.write(f"📺 {row['Producto']}")
                    with c3: st.link_button("📲", wa_url, use_container_width=True)
                    with c4: 
                        if st.button("📝", key=f"epc_{idx}", use_container_width=True): editar_venta_popup(idx, row)
                    with c5: 
                        if st.button("🗑️", key=f"vpc_{idx}", use_container_width=True):
                            df_ventas.drop(idx).to_csv(VENTAS_FILE, index=False); st.rerun()
    else: st.info("No hay registros.")

# --- VISTA 2: INVENTARIO YT ---
elif menu == "📦 Inventario YT":
    st.header("Inventario de Correos YouTube")
    if st.button("➕ AGREGAR NUEVO CORREO", type="primary", use_container_width=vista=="📱 Móvil"):
        @st.dialog("Registrar Correo")
        def add():
            m = st.text_input("Gmail")
            p = st.text_input("Contraseña")
            u = st.selectbox("Usos actuales", [0,1,2])
            if st.button("Guardar"):
                ni = pd.DataFrame([[m, p, u, "Nadie"]], columns=df_inv.columns)
                pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False); st.rerun()
        add()
        
    st.write("---")
    for idx, row in df_inv.iterrows():
        with st.container(border=True):
            st.write(f"📧 **{row['Correo']}** (Usos: {row['Usos']})")
            if vista == "📱 Móvil": st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2) if vista == "📱 Móvil" else st.columns([1, 10])
            with c1:
                if st.button("📝", key=f"ei_{idx}", use_container_width=True): 
                    @st.dialog("Modificar Correo")
                    def edi():
                        nu = st.selectbox("Usos", [0,1,2], index=int(row['Usos']))
                        na = st.text_input("Asignado a", value=row['Asignado_A'])
                        if st.button("Actualizar"):
                            df_inv.at[idx, 'Usos'], df_inv.at[idx, 'Asignado_A'] = nu, na
                            df_inv.to_csv(INV_FILE, index=False); st.rerun()
                    edi()
            with c2:
                if st.button("🗑️", key=f"di_{idx}", use_container_width=True): 
                    df_inv.drop(idx).to_csv(INV_FILE, index=False); st.rerun()

# --- VISTA 3: GESTIÓN DE VENDEDORES (SOLO ADMIN) ---
elif menu == "👥 Gestión de Vendedores":
    st.header("Control de Personal")
    
    # 1. CREACIÓN DE VENDEDOR CON FORMULARIO SEGURO
    with st.container(border=True):
        st.subheader("➕ Generar Nuevo Perfil")
        with st.form("form_crear_vendedor", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nuevo_usr = col1.text_input("Nombre de Usuario (Obligatorio)")
            nuevo_tel = col2.text_input("Teléfono/WhatsApp (Obligatorio)")
            dar_acceso_yt = st.checkbox("Dar acceso a la Base de Datos automática de YouTube Premium")
            
            submit_btn = st.form_submit_button("Crear Vendedor y Generar Clave", type="primary", use_container_width=True)
            
            if submit_btn:
                if nuevo_usr and nuevo_tel:
                    if nuevo_usr in df_usuarios['Usuario'].values:
                        st.error("Ese usuario ya existe. Elige otro nombre.")
                    else:
                        clave = generar_password_aleatoria()
                        acceso = "Si" if dar_acceso_yt else "No"
                        nu_df = pd.DataFrame([[nuevo_usr, clave, "Vendedor", nuevo_tel, acceso]], columns=["Usuario", "Password", "Rol", "Telefono", "Acceso_YT"])
                        df_usuarios = pd.concat([df_usuarios, nu_df], ignore_index=True)
                        df_usuarios.to_csv(USUARIOS_FILE, index=False)
                        
                        st.success("✅ ¡VENDEDOR CREADO CON ÉXITO!")
                        st.info(f"Copia y envía esta información al vendedor:\n\n**👤 Usuario:** {nuevo_usr}\n**🔑 Contraseña:** {clave}\n\n*(Guárdala bien, luego no podrás verla aquí sin entrar a editarlo)*")
                else:
                    st.warning("Debes llenar el Usuario y el Teléfono.")

    st.write("---")
    st.subheader("📋 Lista de Vendedores Activos")
    
    vendedores = df_usuarios[df_usuarios['Rol'] != 'Admin']
    if vendedores.empty:
        st.info("Aún no tienes vendedores registrados.")
    else:
        for idx, row in vendedores.iterrows():
            with st.container(border=True):
                st.write(f"👤 **{row['Usuario']}** | 📱 {row['Telefono']}")
                st.caption(f"🔑 Clave actual: {row['Password']} | 📺 Acceso YT Auto: **{row['Acceso_YT']}**")
                
                if vista == "📱 Móvil": st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                c_edit, c_del = st.columns(2) if vista == "📱 Móvil" else st.columns([1, 10])
                
                with c_edit:
                    if st.button("📝 Editar", key=f"eu_{idx}", use_container_width=True):
                        editar_vendedor_popup(idx, row)
                with c_del:
                    if st.button("🗑️ Borrar", key=f"du_{idx}", use_container_width=True):
                        df_usuarios.drop(idx).to_csv(USUARIOS_FILE, index=False); st.rerun()

# --- VISTA 4: CONFIGURACIÓN GENERAL (SOLO ADMIN) ---
elif menu == "⚙️ Configuración":
    st.header("Configuración del Sistema")
    
    st.subheader("🛠 Plataformas")
    c_plat, c_pbtn = st.columns([3, 1])
    with c_plat: nueva_p = st.text_input("Nueva", label_visibility="collapsed")
    with c_pbtn:
        if st.button("Añadir", use_container_width=True):
            if nueva_p and nueva_p not in lista_plataformas:
                lista_plataformas.append(nueva_p)
                pd.DataFrame(lista_plataformas, columns=["Nombre"]).to_csv(PLAT_FILE, index=False); st.rerun()
                
    for p in lista_plataformas:
        cp1, cp2 = st.columns([4, 1])
        cp1.write(f"📺 {p}")
        if cp2.button("🗑️", key=f"del_p_{p}"):
            lista_plataformas.remove(p); pd.DataFrame(lista_plataformas, columns=["Nombre"]).to_csv(PLAT_FILE, index=False); st.rerun()
            
    st.divider()
    st.subheader("💾 Copias de Seguridad")
    st.download_button("📥 Descargar Backup Completo (Ventas)", df_ventas.to_csv(index=False).encode('utf-8'), "ventas_backup.csv", use_container_width=True)
