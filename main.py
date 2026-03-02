import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import random
import string
import json
import altair as alt
from urllib.parse import quote
import gspread
from google.oauth2.service_account import Credentials
from streamlit_cookies_controller import CookieController
from streamlit_option_menu import option_menu

# ==============================================================================
# BLOQUE 1: CONFIGURACIÓN Y VERSIÓN
# ==============================================================================
VERSION_APP = "3.7 (UX Apple Pill Menu)"

LINK_APP = "https://mi-negocio-streaming-chkfid6tmyepuartagxlrq.streamlit.app/" 
NUMERO_ADMIN = "51902028672" 

st.set_page_config(page_title="NEXA-Stream", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

if 'toast_msg' not in st.session_state:
    st.session_state.toast_msg = None

if st.session_state.toast_msg:
    st.toast(st.session_state.toast_msg)
    st.session_state.toast_msg = None

st.markdown(f"""
    <style>
    .version-corner {{
        position: fixed; bottom: 15px; right: 15px; background-color: rgba(0, 210, 106, 0.2);
        color: #00D26A; padding: 4px 10px; border-radius: 12px; font-size: 10px;
        font-weight: bold; z-index: 999999; pointer-events: none; border: 1px solid #00D26A;
    }}
    </style>
    <div class="version-corner">v{VERSION_APP}</div>
""", unsafe_allow_html=True)

# ==============================================================================
# BLOQUE 2: CSS MÓVIL Y ESTILOS PREMIUM
# ==============================================================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    
    /* ELIMINAR BARRA LATERAL POR COMPLETO */
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    /* ACORDEONES (Expanders) PERSONALIZADOS */
    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #2A2F3D !important;
        background-color: #1A1E2C !important;
        margin-bottom: 10px;
    }
    div[data-testid="stExpander"] summary p { font-weight: bold !important; font-size: 15px !important; }
    
    /* BADGES (ETIQUETAS) */
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-right: 8px; display: inline-block; margin-bottom: 5px;}
    .badge-netflix { background-color: rgba(229, 9, 20, 0.15); color: #E50914; border: 1px solid #E50914; }
    .badge-youtube { background-color: rgba(255, 0, 0, 0.15); color: #FF4444; border: 1px solid #FF4444; }
    .badge-spotify { background-color: rgba(29, 185, 84, 0.15); color: #1DB954; border: 1px solid #1DB954; }
    .badge-disney { background-color: rgba(17, 60, 207, 0.2); color: #4A7BFF; border: 1px solid #4A7BFF; }
    .badge-default { background-color: rgba(255, 255, 255, 0.1); color: #FFF; border: 1px solid #777; }
    .badge-green { background-color: rgba(0, 210, 106, 0.15); color: #00D26A; border: 1px solid #00D26A;}
    .badge-orange { background-color: rgba(255, 152, 0, 0.15); color: #FF9800; border: 1px solid #FF9800;}
    .badge-red { background-color: rgba(244, 67, 54, 0.15); color: #F44336; border: 1px solid #F44336;}
    
    /* DASHBOARD KPI CARDS */
    .kpi-card { padding: 20px; border-radius: 15px; color: white; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    .kpi-blue { background: linear-gradient(135deg, #0052D4, #007BFF); }
    .kpi-orange { background: linear-gradient(135deg, #C85A17, #FF8C00); }
    .kpi-red { background: linear-gradient(135deg, #900C3F, #DC3545); }
    .kpi-green { background: linear-gradient(135deg, #0F5132, #28A745); }
    .kpi-title { font-size: 14px; opacity: 0.9; margin-bottom: 5px; }
    .kpi-value { font-size: 28px; font-weight: bold; margin: 0; }
    
    /* BOTONES */
    .stButton>button, .stLinkButton>a { border-radius: 10px !important; height: 38px !important; padding: 0px !important; display: flex !important; align-items: center !important; justify-content: center !important; width: 100% !important; font-size: 15px !important; font-weight: 600 !important; margin: 0px !important; transition: all 0.2s; }
    .stLinkButton>a { background-color: #25D366 !important; color: white !important; border: none !important; }
    .stLinkButton>a:hover { background-color: #20BA59 !important; transform: scale(1.02); }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div { border-radius: 10px; height: 38px; }
    
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 6px !important; }
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { width: 25% !important; min-width: 0 !important; flex: 1 1 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# BLOQUE 3: CONEXIÓN A GOOGLE SHEETS
# ==============================================================================
@st.cache_resource
def init_gsheets():
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_JSON"])
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url(st.secrets["URL_EXCEL"])
    except Exception as e:
        st.error("Error al conectar con Google Sheets. Verifica tus Secrets.")
        st.stop()

sh = init_gsheets()

@st.cache_data(ttl=60, show_spinner=False)
def get_sheet_records(ws_name):
    try:
        ws = sh.worksheet(ws_name)
        return ws.get_all_records(), True
    except gspread.exceptions.WorksheetNotFound:
        return [], False

def load_df(ws_name, cols):
    data, exists = get_sheet_records(ws_name)
    if not exists:
        ws = sh.add_worksheet(title=ws_name, rows="1000", cols="20")
        ws.update(values=[cols], range_name="A1")
        get_sheet_records.clear() 
        return pd.DataFrame(columns=cols)
    if not data:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(data).copy()

def save_df(df, ws_name):
    ws = sh.worksheet(ws_name)
    ws.clear()
    df_str = df.fillna("").astype(str)
    ws.update(values=[df_str.columns.values.tolist()] + df_str.values.tolist(), range_name="A1")
    get_sheet_records.clear() 

# --- CARGAR TABLAS ---
cols_ventas = ["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento", "Vendedor", "Costo", "Precio"]
df_ventas = load_df("Ventas", cols_ventas)
df_ventas['Vencimiento'] = pd.to_datetime(df_ventas['Vencimiento'], errors='coerce').dt.date

df_ex_clientes = load_df("ExClientes", cols_ventas)
df_inv = load_df("Inventario", ["Correo", "Password", "Usos", "Asignado_A"])

df_plat = load_df("Plataformas", ["Nombre"])
if df_plat.empty:
    lista_plataformas = ["YouTube Premium", "Netflix", "Disney+", "Google One", "Spotify"]
    save_df(pd.DataFrame(lista_plataformas, columns=["Nombre"]), "Plataformas")
else:
    lista_plataformas = df_plat['Nombre'].tolist()

df_usuarios = load_df("Usuarios", ["Usuario", "Password", "Rol", "Telefono", "Acceso_YT"])
if df_usuarios.empty:
    df_usuarios = pd.DataFrame([["admin", "admin123", "Admin", "N/A", "Si"]], columns=["Usuario", "Password", "Rol", "Telefono", "Acceso_YT"])
    save_df(df_usuarios, "Usuarios")

DEFAULT_TEMPLATES = {
    "recordatorio": "Hola {cliente}, te recordamos que tu cuenta de {producto} vencerá el {vencimiento}. ¿Deseas ir renovando para no perder el servicio?",
    "vencido": "🚨 Hola {cliente}, tu cuenta de {producto} ha VENCIDO el {vencimiento}. Por favor comunícate con nosotros para reactivar tu servicio.",
    "vendedor": "Hola {nombre}, bienvenido al equipo. Aquí tienes tu acceso al sistema NEXA-Stream.\n\n👤 Usuario: {usuario}\n🔑 Contraseña: {password}\n🌐 Link de acceso: {link}"
}

df_conf = load_df("Config", ["Clave", "Valor"])
if df_conf.empty:
    df_conf = pd.DataFrame(list(DEFAULT_TEMPLATES.items()), columns=["Clave", "Valor"])
    save_df(df_conf, "Config")
    plantillas_wa = DEFAULT_TEMPLATES
else:
    plantillas_wa = dict(zip(df_conf['Clave'], df_conf['Valor']))

def save_templates(templates_dict):
    df_conf_updated = pd.DataFrame(list(templates_dict.items()), columns=["Clave", "Valor"])
    save_df(df_conf_updated, "Config")

def generar_password_aleatoria(longitud=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(longitud))

def generar_usuario(nombre):
    base = re.sub(r'[^a-zA-Z0-9]', '', str(nombre).split()[0].lower())
    return f"{base}{random.randint(100, 999)}"

def limpiar_whatsapp(numero):
    solo_numeros = re.sub(r'\D', '', str(numero))
    if len(solo_numeros) == 9: return f"51{solo_numeros}"
    return solo_numeros

def generar_lote_correos(cantidad=10):
    lote = []
    NOMBRES = ["Juan", "Carlos", "Jose", "Luis", "David", "Javier", "Daniel", "Maria", "Ana", "Rosa", "Carmen", "Sofia"]
    APELLIDOS = ["Garcia", "Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez", "Sanchez", "Ramirez", "Cruz", "Flores"]
    for _ in range(cantidad):
        n, a = random.choice(NOMBRES), random.choice(APELLIDOS)
        usr = f"{n.lower()}.{a.lower()}.prem{random.randint(1000, 9999)}"
        lote.append({"Nombre": n, "Apellido": a, "Usuario": usr, "Correo": f"{usr}@gmail.com", "Pass": generar_password_aleatoria()})
    return lote

def formatear_mes_anio(yyyy_mm):
    MESES = {'01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic'}
    y, m = yyyy_mm.split('-')
    return f"{MESES[m]} {y}"

# ==============================================================================
# BLOQUE 4: SISTEMA DE LOGIN Y AUTO-GUARDADO
# ==============================================================================
cookies = CookieController()
usuario_guardado = cookies.get('nexa_user_cookie')

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.role = ""
    st.session_state.acceso_yt = "No"
    st.session_state.alertas_vistas = False 
    st.session_state.temp_emails = [] 

if 'nuevo_vend_usr' not in st.session_state: st.session_state.nuevo_vend_usr = None
if 'nuevo_vend_pwd' not in st.session_state: st.session_state.nuevo_vend_pwd = None
if 'nuevo_vend_nom' not in st.session_state: st.session_state.nuevo_vend_nom = None
if 'nuevo_vend_tel' not in st.session_state: st.session_state.nuevo_vend_tel = None

if not st.session_state.logged_in and usuario_guardado:
    match = df_usuarios[df_usuarios['Usuario'] == usuario_guardado]
    if not match.empty:
        st.session_state.logged_in = True
        st.session_state.user = match.iloc[0]['Usuario']
        st.session_state.role = match.iloc[0]['Rol']
        st.session_state.acceso_yt = match.iloc[0]['Acceso_YT']
        st.session_state.alertas_vistas = False

if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; margin-bottom: 30px;">
            <h1 style="color: #00D26A; font-size: 50px; margin-bottom:0; text-shadow: 0 0 15px rgba(0,210,106,0.5);">🚀 NEXA</h1>
            <h3 style="margin-top:0; color: white; letter-spacing: 4px;">STREAM</h3>
        </div>
    """, unsafe_allow_html=True)
    
    c_log1, c_log2, c_log3 = st.columns([1,2,1])
    with c_log2:
        with st.container(border=True):
            with st.form("login_form"):
                u_in = st.text_input("Usuario", autocomplete="username", placeholder="ej: admin")
                p_in = st.text_input("Contraseña", type="password", autocomplete="current-password", placeholder="••••••••")
                st.write("")
                ingresar = st.form_submit_button("Acceder al Sistema", type="primary", use_container_width=True)
                
                if ingresar:
                    match = df_usuarios[(df_usuarios['Usuario'] == u_in) & (df_usuarios['Password'] == p_in)]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user = match.iloc[0]['Usuario']
                        st.session_state.role = match.iloc[0]['Rol']
                        st.session_state.acceso_yt = match.iloc[0]['Acceso_YT']
                        st.session_state.alertas_vistas = False
                        cookies.set('nexa_user_cookie', match.iloc[0]['Usuario'])
                        st.session_state.toast_msg = f"👋 ¡Bienvenido, {match.iloc[0]['Usuario']}!"
                        st.rerun()
                    else: 
                        st.error("❌ Credenciales incorrectas.")
    st.stop()

# ==============================================================================
# BLOQUE 5: DIÁLOGOS DE GESTIÓN (Pop-Ups)
# ==============================================================================
@st.dialog("⏰ Centro de Cobranza Urgente")
def mostrar_popup_alertas(df_urgente, hoy):
    global df_ventas, df_ex_clientes
    st.warning("⚠️ **ATENCIÓN:** Gestión inmediata requerida.")
    for idx, row in df_urgente.sort_values(by="Vencimiento").iterrows():
        dias = (row['Vencimiento'] - hoy).days
        if dias == 3: estado_txt, badge_col = "Vence en 3 días", "badge-orange"
        elif dias == 2: estado_txt, badge_col = "Vence en 2 días", "badge-orange"
        elif dias == 1: estado_txt, badge_col = "Vence en 1 día", "badge-orange"
        elif dias <= 0: estado_txt, badge_col = "VENCIDO", "badge-red"
        else: estado_txt, badge_col = "Activo", "badge-green"

        prod_b = "badge-youtube" if "YouTube" in row['Producto'] else "badge-netflix" if "Netflix" in row['Producto'] else "badge-spotify" if "Spotify" in row['Producto'] else "badge-disney" if "Disney" in row['Producto'] else "badge-default"
        texto_base = plantillas_wa["vencido"] if dias <= 0 else plantillas_wa["recordatorio"]
        texto_wa = texto_base.replace("{cliente}", str(row['Cliente'])).replace("{producto}", str(row['Producto'])).replace("{vencimiento}", str(row['Vencimiento']))
        wa_url = f"https://wa.me/{row['WhatsApp']}?text={quote(texto_wa)}"
        
        with st.container(border=True):
            st.markdown(f"""
            <div style="margin-bottom: 5px;"><h4 style="margin:0;">👤 {row['Cliente']}</h4></div>
            <div><span class="badge {prod_b}">📺 {row['Producto']}</span><span class="badge {badge_col}">⚠️ {estado_txt}</span></div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
            ca1, ca2 = st.columns(2)
            with ca1: st.link_button("📲 Avisar", wa_url, use_container_width=True)
            with ca2:
                if st.button("🗑️ Papelera", key=f"alerta_del_{idx}", use_container_width=True):
                    df_ex_clientes = pd.concat([df_ex_clientes, pd.DataFrame([row])], ignore_index=True)
                    save_df(df_ex_clientes, "ExClientes")
                    df_ventas = df_ventas.drop(idx)
                    save_df(df_ventas, "Ventas")
                    st.session_state.toast_msg = "🗑️ Movido a papelera."
                    st.rerun()
    if st.button("Entendido, cerrar", type="primary", use_container_width=True):
        st.session_state.alertas_vistas = True
        st.rerun()

@st.dialog("🔄 Renovar")
def renovar_venta_popup(idx, row):
    global df_ventas
    st.write(f"Renovando a: **{row['Cliente']}**")
    dur = st.radio("Plazo:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    hoy = datetime.now().date()
    fecha_base = max(hoy, pd.to_datetime(row['Vencimiento']).date()) 
    if dur == "1 Mes": nueva_fecha = fecha_base + timedelta(days=30)
    elif dur == "2 Meses": nueva_fecha = fecha_base + timedelta(days=60)
    elif dur == "6 Meses": nueva_fecha = fecha_base + timedelta(days=180)
    else: nueva_fecha = fecha_base + timedelta(days=365)
    
    st.info(f"📅 Nuevo vencimiento: **{nueva_fecha}**")
    tipo_cta = st.radio("Credenciales:", ["Mantener misma cuenta", "Asignar cuenta nueva"], horizontal=True)
    mv, pv = row['Correo'], row['Pass'] 
    
    if tipo_cta == "Asignar cuenta nueva":
        ca, cb = st.columns(2)
        if row['Producto'] == "YouTube Premium" and ((st.session_state.role == "Admin") or (st.session_state.acceso_yt == "Si")):
            disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
            if not disponibles.empty:
                with ca: mv = st.text_input("Auto-Correo", value=disponibles.iloc[0]['Correo'])
                with cb: pv = st.text_input("Nueva Clave", value=disponibles.iloc[0]['Password'])
            else:
                with ca: mv = st.text_input("Nuevo Correo")
                with cb: pv = st.text_input("Nueva Clave")
        else:
            with ca: mv = st.text_input("Nuevo Correo")
            with cb: pv = st.text_input("Nueva Clave")
            
    if st.button("CONFIRMAR RENOVACIÓN", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Vencimiento'] = nueva_fecha
        df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'] = mv, pv
        save_df(df_ventas, "Ventas")
        st.session_state.toast_msg = "🔄 ¡Renovación exitosa!"
        st.rerun()

@st.dialog("📝 Editar")
def editar_venta_popup(idx, row):
    global df_ventas
    prod = st.selectbox("Plataforma", lista_plataformas, index=lista_plataformas.index(row['Producto']) if row['Producto'] in lista_plataformas else 0)
    nom = st.text_input("Nombre", value=row['Cliente'])
    tel = st.text_input("WhatsApp", value=row['WhatsApp'])
    venc = st.date_input("Vencimiento", row['Vencimiento'])
    c_costo, c_precio = st.columns(2)
    costo = c_costo.number_input("Costo", value=float(row['Costo']) if not pd.isna(row.get('Costo')) else 0.0, step=1.0)
    precio = c_precio.number_input("Precio", value=float(row['Precio']) if not pd.isna(row.get('Precio')) else 0.0, step=1.0)
    m = st.text_input("Correo", value=row['Correo'])
    p = st.text_input("Pass", value=row['Pass'])
    perf = st.text_input("Perfil", value=row['Perfil'])
    if st.button("ACTUALIZAR", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Cliente'], df_ventas.at[idx, 'WhatsApp'], df_ventas.at[idx, 'Producto'], df_ventas.at[idx, 'Vencimiento'] = nom, limpiar_whatsapp(tel), prod, venc
        df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'], df_ventas.at[idx, 'Perfil'], df_ventas.at[idx, 'Costo'], df_ventas.at[idx, 'Precio'] = m, p, perf, costo, precio
        save_df(df_ventas, "Ventas")
        st.session_state.toast_msg = "💾 Cambios guardados."
        st.rerun()

@st.dialog("➕ Nueva Venta")
def nueva_venta_popup():
    global df_ventas
    c1, c2 = st.columns(2)
    with c1: prod = st.selectbox("Plataforma", lista_plataformas)
    with c2: f_ini = st.date_input("Inicio", datetime.now())
    nom = st.text_input("Cliente", placeholder="Ej: Maria Lopez")
    tel = st.text_input("WhatsApp", placeholder="Ej: 999888777")
    c_costo, c_precio = st.columns(2)
    costo = c_costo.number_input("Costo cuenta", value=0.0, step=1.0)
    precio = c_precio.number_input("Precio Venta", value=0.0, step=1.0)
    dur = st.radio("Plazo:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    if dur == "1 Mes": venc = f_ini + timedelta(days=30)
    elif dur == "2 Meses": venc = f_ini + timedelta(days=60)
    elif dur == "6 Meses": venc = f_ini + timedelta(days=180)
    else: venc = f_ini + timedelta(days=365)
    
    ca, cb = st.columns(2)
    if prod == "YouTube Premium" and ((st.session_state.role == "Admin") or (st.session_state.acceso_yt == "Si")):
        disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
        if not disponibles.empty:
            with ca: mv = st.text_input("Correo Auto", value=disponibles.iloc[0]['Correo'])
            with cb: pv = st.text_input("Clave", value=disponibles.iloc[0]['Password'])
        else: 
            with ca: mv = st.text_input("Correo Manual")
            with cb: pv = st.text_input("Pass Manual")
    else: 
        with ca: mv = st.text_input("Correo")
        with cb: pv = st.text_input("Pass")
    
    if st.button("🚀 REGISTRAR VENTA", type="primary", use_container_width=True):
        nueva = pd.DataFrame([[ "🟢", nom, limpiar_whatsapp(tel), prod, mv, pv, "nan", "nan", venc, st.session_state.user, costo, precio ]], columns=df_ventas.columns)
        df_ventas = pd.concat([df_ventas, nueva], ignore_index=True)
        save_df(df_ventas, "Ventas")
        st.session_state.toast_msg = "🎉 ¡Venta registrada!"
        st.rerun()

# ==============================================================================
# BLOQUE 6: ENCABEZADO 100% MÓVIL Y MENÚ PÍLDORA (ESTILO iOS)
# ==============================================================================

# Encabezado súper limpio
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 5px 0px 15px 0px; margin-bottom: 5px;">
        <h2 style="color:#00D26A; margin:0; padding:0; line-height: 1;">🚀 NEXA<span style="color:white; font-size: 18px;">-Stream</span></h2>
        <div style="text-align:right; color:#aaa; font-size: 13px; line-height: 1.2;">
            👤 <b>{st.session_state.user}</b> <br> <span style="font-size: 11px;">{st.session_state.role}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# EL NUEVO MENÚ PÍLDORA FLOTANTE (ESTILO APPLE)
if st.session_state.role == "Admin":
    opciones_menu = ["Ventas", "Métricas", "Inventario", "Equipo", "Ajustes", "Salir"]
    iconos_menu = ["cart-check-fill", "bar-chart-fill", "youtube", "people-fill", "gear-fill", "box-arrow-right"]
else:
    opciones_menu = ["Ventas", "Métricas", "Papelera", "Salir"]
    iconos_menu = ["cart-check-fill", "bar-chart-fill", "trash3-fill", "box-arrow-right"]

menu = option_menu(
    menu_title=None,
    options=opciones_menu,
    icons=iconos_menu,
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {
            "padding": "6px", 
            "background-color": "rgba(26, 30, 44, 0.6)", 
            "border": "1px solid #2A2F3D", 
            "border-radius": "50px", # Borde píldora 100% redondeado
            "margin-bottom": "25px",
            "box-shadow": "0 8px 20px rgba(0,0,0,0.4)"
        },
        "icon": {
            "font-size": "15px", 
            "transition": "all 0.3s ease-in-out"
        },
        "nav-link": {
            "font-size": "12px", 
            "text-align": "center", 
            "margin": "0px 2px", 
            "padding": "8px 10px", 
            "--hover-color": "rgba(255,255,255,0.05)", 
            "border-radius": "50px", # Efecto de píldora individual al pasar el mouse
            "color": "#7A8295", # Texto apagado para opciones inactivas
            "transition": "all 0.4s cubic-bezier(0.25, 1, 0.5, 1)" # Animación de deslizamiento fluido iOS
        },
        "nav-link-selected": {
            "background-color": "#00D26A", 
            "color": "#0B0F19", # Texto oscuro sobre neón brilla muchísimo más (Premium)
            "font-weight": "800", 
            "border-radius": "50px",
            "box-shadow": "0 0 15px rgba(0, 210, 106, 0.4)" 
        },
    }
)

if menu == "Salir":
    cookies.remove('nexa_user_cookie') 
    st.session_state.logged_in = False
    st.rerun()

# ==============================================================================
# VISTAS PRINCIPALES
# ==============================================================================

if menu == "Ventas":
    if st.session_state.role == "Admin":
        cupos_disponibles = len(df_inv[df_inv['Usos'] < 2]) if not df_inv.empty else 0
        if cupos_disponibles <= 2:
            st.error(f"🚨 **¡ALERTA INVENTARIO!** Quedan **{cupos_disponibles}** cupos de YouTube automáticos.")

    if st.session_state.role == "Admin":
        tipo_filtro = st.selectbox("👥 Filtro Vendedores:", ["🌎 Todos", "👥 Equipo", "👑 Mi Cuenta", "🎯 Buscar..."], label_visibility="collapsed")
        if tipo_filtro == "🌎 Todos": df_mostrar = df_ventas
        elif tipo_filtro == "👥 Equipo": df_mostrar = df_ventas[df_ventas['Vendedor'] != st.session_state.user]
        elif tipo_filtro == "👑 Mi Cuenta": df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]
        else:
            lista_v = sorted(list(set(df_ventas['Vendedor'].dropna().tolist() + df_usuarios['Usuario'].tolist())))
            vend_sel = st.multiselect("Seleccionar:", lista_v, default=lista_v)
            df_mostrar = df_ventas[df_ventas['Vendedor'].isin(vend_sel)]
    else: df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]

    hoy = datetime.now().date()
    if not df_mostrar.empty:
        df_urgente = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy + timedelta(days=3)]
        if not st.session_state.alertas_vistas and not df_urgente.empty:
            mostrar_popup_alertas(df_urgente, hoy)
        
    c1, c2 = st.columns([3, 1])
    with c1: 
        if st.button("➕ CREAR NUEVA VENTA", type="primary", use_container_width=True): nueva_venta_popup()
    with c2: 
        if st.button("🔔 Alertas", use_container_width=True):
            st.session_state.alertas_vistas = False
            st.rerun()
            
    with st.expander("🔍 Mostrar Filtros Avanzados", expanded=False):
        filtro_est = st.radio("Estado:", ["🌎 Todas", "🟢 Activas", "🟠 Por Vencer", "🔴 Vencidas"], horizontal=True)
        cf1, cf2 = st.columns(2)
        search = cf1.text_input("Buscar Cliente:")
        filtro_plat = cf2.selectbox("Plataforma:", ["Todas"] + lista_plataformas)

    if search: mask_search = df_mostrar.apply(lambda r: search.lower() in str(r).lower(), axis=1); df_mostrar = df_mostrar[mask_search]
    if filtro_plat != "Todas": df_mostrar = df_mostrar[df_mostrar['Producto'] == filtro_plat]
    if filtro_est != "🌎 Todas":
        if filtro_est == "🟢 Activas": df_mostrar = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date > hoy + timedelta(days=3)]
        elif filtro_est == "🟠 Por Vencer":
            mask_vencer = (pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy + timedelta(days=3)) & (pd.to_datetime(df_mostrar['Vencimiento']).dt.date > hoy)
            df_mostrar = df_mostrar[mask_vencer]
        elif filtro_est == "🔴 Vencidas": df_mostrar = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy]

    st.write("---")

    if not df_mostrar.empty:
        for idx, row in df_mostrar.sort_values(by="Vencimiento").iterrows():
            d = (row['Vencimiento'] - hoy).days
            
            if d <= 0: est_emj, estado_txt, badge_col = "🔴", "Vencido", "badge-red"
            elif d <= 3: est_emj, estado_txt, badge_col = "🟠", f"Vence en {d} d.", "badge-orange"
            else: est_emj, estado_txt, badge_col = "🟢", "Activo", "badge-green"
                
            prod_badge = "badge-youtube" if "YouTube" in row['Producto'] else "badge-netflix" if "Netflix" in row['Producto'] else "badge-spotify" if "Spotify" in row['Producto'] else "badge-disney" if "Disney" in row['Producto'] else "badge-default"

            texto_base = plantillas_wa["vencido"] if d <= 0 else plantillas_wa["recordatorio"]
            texto_wa = texto_base.replace("{cliente}", str(row['Cliente'])).replace("{producto}", str(row['Producto'])).replace("{vencimiento}", str(row['Vencimiento']))
            wa_url = f"https://wa.me/{row['WhatsApp']}?text={quote(texto_wa)}"
            
            titulo_acordeon = f"{est_emj} {row['Cliente']} | 📺 {row['Producto']}"
            
            with st.expander(titulo_acordeon):
                vendedor_badge = f" • 🧑‍🚀 {row['Vendedor']}" if st.session_state.role == "Admin" else ""
                st.markdown(f"""
                <div>
                    <span class="badge {prod_badge}">📺 {row['Producto']}</span>
                    <span class="badge {badge_col}">⏱️ {estado_txt}</span>
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"📧 **{row['Correo']}** | 🔑 **{row['Pass']}**")
                st.caption(f"📅 Vence: {row['Vencimiento']} {vendedor_badge}")
                
                st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                cols = st.columns(4)
                with cols[0]: st.link_button("📲 Avisar", wa_url, use_container_width=True)
                with cols[1]: 
                    if st.button("🔄 Renovar", key=f"r_{idx}", use_container_width=True): renovar_venta_popup(idx, row)
                with cols[2]: 
                    if st.button("📝 Editar", key=f"e_{idx}", use_container_width=True): editar_venta_popup(idx, row)
                with cols[3]:
                    if st.button("🗑️ Borrar", key=f"v_{idx}", use_container_width=True):
                        df_ex_clientes = pd.concat([df_ex_clientes, pd.DataFrame([row])], ignore_index=True)
                        save_df(df_ex_clientes, "ExClientes")
                        df_ventas = df_ventas.drop(idx)
                        save_df(df_ventas, "Ventas")
                        st.session_state.toast_msg = "🗑️ Enviado a papelera."
                        st.rerun()
    else: 
        st.info("No se encontraron clientes.")

elif menu == "Métricas":
    if st.session_state.role == "Admin": 
        tipo_filtro_dash = st.selectbox("Filtro Vendedores:", ["🌎 Todos", "👥 Equipo", "👑 Mi Cuenta"], label_visibility="collapsed")
        if tipo_filtro_dash == "🌎 Todos": df_dash_base = df_ventas.copy()
        elif tipo_filtro_dash == "👥 Equipo": df_dash_base = df_ventas[df_ventas['Vendedor'] != st.session_state.user].copy()
        else: df_dash_base = df_ventas[df_ventas['Vendedor'] == st.session_state.user].copy()
    else: df_dash_base = df_ventas[df_ventas['Vendedor'] == st.session_state.user].copy()
        
    if df_dash_base.empty: st.warning("No hay suficientes datos registrados.")
    else:
        df_dash_base['Vencimiento_dt'] = pd.to_datetime(df_dash_base['Vencimiento'], errors='coerce')
        df_dash_base['Periodo'] = df_dash_base['Vencimiento_dt'].dt.strftime('%Y-%m')
        periodos_disponibles = sorted(df_dash_base['Periodo'].dropna().unique().tolist(), reverse=True)
        opciones_periodos = ["Histórico Global"] + periodos_disponibles
        
        c_per, c_desc = st.columns([3, 1])
        with c_per:
            periodo_sel = st.selectbox("📅 Periodo:", opciones_periodos, format_func=lambda x: "Histórico Global" if x == "Histórico Global" else formatear_mes_anio(x), label_visibility="collapsed")
        
        if periodo_sel != "Histórico Global": df_dash = df_dash_base[df_dash_base['Periodo'] == periodo_sel]
        else: df_dash = df_dash_base
        
        with c_desc:
            csv_data = df_dash.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Exportar Excel", data=csv_data, file_name='reporte_nexa.csv', mime='text/csv', use_container_width=True)
            
        st.write("---")
        if df_dash.empty: st.info("No hay ventas en este periodo.")
        else:
            df_dash['Costo'] = pd.to_numeric(df_dash['Costo'], errors='coerce').fillna(0)
            df_dash['Precio'] = pd.to_numeric(df_dash['Precio'], errors='coerce').fillna(0)
            total_ingresos = df_dash['Precio'].sum()
            total_costos = df_dash['Costo'].sum()
            total_ganancia = total_ingresos - total_costos
            total_clientes = len(df_dash)
            
            hoy = datetime.now().date()
            vencidos = len(df_dash[pd.to_datetime(df_dash['Vencimiento']).dt.date <= hoy])
            por_vencer = len(df_dash[(pd.to_datetime(df_dash['Vencimiento']).dt.date <= hoy + timedelta(days=3)) & (pd.to_datetime(df_dash['Vencimiento']).dt.date > hoy)])
            
            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)
            
            with col1:
                st.markdown(f'<div class="kpi-card kpi-blue"><div class="kpi-title">👥 Clientes Activos</div><p class="kpi-value">{total_clientes}</p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="kpi-card kpi-green"><div class="kpi-title">💰 Ganancia Neta</div><p class="kpi-value">S/ {total_ganancia:.2f}</p></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="kpi-card kpi-orange"><div class="kpi-title">⚠️ Por Vencer (3 días)</div><p class="kpi-value">{por_vencer}</p></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="kpi-card kpi-red"><div class="kpi-title">🔴 Cuentas Vencidas</div><p class="kpi-value">{vencidos}</p></div>', unsafe_allow_html=True)
            
            st.write("---")
            
            st.subheader("📊 Análisis Gráfico")
            cg1, cg2 = st.columns(2)
            
            with cg1:
                st.caption("Distribución por Plataforma")
                ventas_plat = df_dash['Producto'].value_counts().reset_index()
                ventas_plat.columns = ['Plataforma', 'Cantidad']
                grafico_anillo = alt.Chart(ventas_plat).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Cantidad", type="quantitative"),
                    color=alt.Color(field="Plataforma", type="nominal", legend=alt.Legend(title="Plataformas", orient="bottom", labelColor="white", titleColor="white")),
                    tooltip=['Plataforma', 'Cantidad']
                ).properties(height=300).configure_view(strokeWidth=0)
                st.altair_chart(grafico_anillo, use_container_width=True)
                
            with cg2:
                st.caption("Evolución de Ingresos (Mensual)")
                historico_ingresos = df_dash_base.groupby('Periodo')['Precio'].sum().reset_index()
                grafico_barras = alt.Chart(historico_ingresos).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color='#00D26A').encode(
                    x=alt.X('Periodo:N', title='', axis=alt.Axis(labelColor='white')),
                    y=alt.Y('Precio:Q', title='Ingresos (S/)', axis=alt.Axis(labelColor='white', titleColor='white')),
                    tooltip=['Periodo', 'Precio']
                ).properties(height=300).configure_view(strokeWidth=0)
                st.altair_chart(grafico_barras, use_container_width=True)

elif menu == "Papelera":
    df_ex_mostrar = df_ex_clientes if st.session_state.role == "Admin" else df_ex_clientes[df_ex_clientes['Vendedor'] == st.session_state.user]
    if df_ex_mostrar.empty: st.info("La papelera está limpia.")
    else:
        for idx, row in df_ex_mostrar.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(f"🚫 **{row['Cliente']}** ({row['Producto']}) - Tel: {row['WhatsApp']}")
                if c2.button("🗑️ Destruir", key=f"ex_{idx}", use_container_width=True):
                    df_ex_clientes = df_ex_clientes.drop(idx)
                    save_df(df_ex_clientes, "ExClientes")
                    st.session_state.toast_msg = "✅ Borrado permanente."
                    st.rerun()

elif menu == "Inventario":
    with st.expander("➕ CREAR NUEVAS CUENTAS (BÓVEDA)", expanded=False):
        c_auto, c_man = st.tabs(["⚡ Generador con IA", "✏️ Ingreso Manual"])
        
        with c_auto:
            st.info("Genera 10 correos listos para copiar y pegar en Google.")
            if st.button("🔄 Generar 10 Correos", use_container_width=True):
                st.session_state.temp_emails = generar_lote_correos(10)
                st.rerun()
            if st.session_state.temp_emails:
                for i, acc in enumerate(st.session_state.temp_emails):
                    with st.container(border=True):
                        st.write(f"👤 **{acc['Nombre']} {acc['Apellido']}**")
                        c1, c2 = st.columns(2)
                        with c1: st.code(acc['Usuario'], language=None)
                        with c2: st.code(acc['Pass'], language=None)
                        if st.button("🗑️ Descartar", key=f"del_tmp_{i}", use_container_width=True):
                            st.session_state.temp_emails.pop(i)
                            st.rerun()
                if st.button("✅ Guardar Todo", type="primary", use_container_width=True):
                    nuevos_df = pd.DataFrame([[acc['Correo'], acc['Pass'], 0, "Nadie"] for acc in st.session_state.temp_emails], columns=df_inv.columns)
                    df_inv = pd.concat([df_inv, nuevos_df], ignore_index=True)
                    save_df(df_inv, "Inventario")
                    st.session_state.temp_emails = []
                    st.session_state.toast_msg = "✅ Banco actualizado."
                    st.rerun()
                    
        with c_man:
            m = st.text_input("Gmail")
            p = st.text_input("Contraseña")
            u = st.selectbox("Usos (Cupos Ocupados)", [0,1,2])
            if st.button("Guardar en Bóveda", type="primary", use_container_width=True):
                ni = pd.DataFrame([[m, p, u, "Nadie"]], columns=df_inv.columns)
                df_inv = pd.concat([df_inv, ni], ignore_index=True)
                save_df(df_inv, "Inventario")
                st.session_state.toast_msg = "✅ Correo guardado."
                st.rerun()
                
    st.write("---")
    st.subheader("📚 Cuentas Registradas")
        
    for idx, row in df_inv.iterrows():
        with st.container(border=True):
            st.write(f"📧 **{row['Correo']}** (Usos: {row['Usos']})")
            st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📝 Ajustar", key=f"ei_{idx}", use_container_width=True): 
                    @st.dialog("Modificar")
                    def edi():
                        global df_inv
                        nu = st.selectbox("Usos", [0,1,2], index=int(row['Usos']))
                        na = st.text_input("Asignado a", value=row['Asignado_A'])
                        if st.button("Actualizar Bóveda"):
                            df_inv.at[idx, 'Usos'], df_inv.at[idx, 'Asignado_A'] = nu, na
                            save_df(df_inv, "Inventario")
                            st.rerun()
                    edi()
            with c2:
                if st.button("🗑️ Eliminar", key=f"di_{idx}", use_container_width=True):
                    df_inv = df_inv.drop(idx)
                    save_df(df_inv, "Inventario")
                    st.session_state.toast_msg = "🗑️ Cuenta descartada."
                    st.rerun()

elif menu == "Equipo":
    with st.expander("➕ INTEGRAR NUEVO VENDEDOR", expanded=False):
        if st.session_state.nuevo_vend_usr:
            usr_gen = st.session_state.nuevo_vend_usr
            pwd_gen = st.session_state.nuevo_vend_pwd
            nom_gen = st.session_state.nuevo_vend_nom
            tel_gen = st.session_state.nuevo_vend_tel
            texto_wa = plantillas_wa["vendedor"].replace("{nombre}", nom_gen).replace("{usuario}", usr_gen).replace("{password}", pwd_gen).replace("{link}", LINK_APP)
            enlace_wa = f"https://wa.me/{tel_gen}?text={quote(texto_wa)}"
            st.success("✅ ¡Credenciales Generadas!")
            st.info(f"**Usuario:** {usr_gen} | **Clave:** {pwd_gen}")
            col_wa, col_ok = st.columns(2)
            col_wa.link_button("📲 Mandar por WhatsApp", enlace_wa, use_container_width=True)
            if col_ok.button("✅ Ocultar", use_container_width=True):
                st.session_state.nuevo_vend_usr = None
                st.rerun()
        else:
            with st.form("form_crear_vend"):
                col1, col2 = st.columns(2)
                nuevo_nom = col1.text_input("Nombre de Pila (Ej: Juan)")
                nuevo_tel = col2.text_input("WhatsApp (Ej: 999888777)")
                dar_acceso_yt = st.checkbox("Dar acceso a la Bóveda Automática YT")
                if st.form_submit_button("Crear Perfil", type="primary", use_container_width=True):
                    if nuevo_nom and nuevo_tel:
                        usr_generado = generar_usuario(nuevo_nom)
                        pwd_generada = generar_password_aleatoria()
                        tel_limpio = limpiar_whatsapp(nuevo_tel)
                        acceso = "Si" if dar_acceso_yt else "No"
                        nu_df = pd.DataFrame([[usr_generado, pwd_generada, "Vendedor", tel_limpio, acceso]], columns=["Usuario", "Password", "Rol", "Telefono", "Acceso_YT"])
                        df_usuarios = pd.concat([df_usuarios, nu_df], ignore_index=True)
                        save_df(df_usuarios, "Usuarios")
                        st.session_state.nuevo_vend_usr = usr_generado
                        st.session_state.nuevo_vend_pwd = pwd_generada
                        st.session_state.nuevo_vend_nom = nuevo_nom
                        st.session_state.nuevo_vend_tel = tel_limpio
                        st.session_state.toast_msg = "✅ Usuario creado."
                        st.rerun()
                    else: st.warning("⚠️ Faltan datos.")
    
    st.write("---")
    st.subheader("👥 Personal Activo")
    vendedores = df_usuarios[df_usuarios['Rol'] != 'Admin']
    if vendedores.empty: st.info("No hay equipo registrado.")
    else:
        for idx, row in vendedores.iterrows():
            with st.container(border=True):
                st.write(f"🧑‍🚀 **{row['Usuario']}** | 📱 {row['Telefono']}")
                st.caption(f"🔑 Clave: {row['Password']} | 📺 Bóveda YT: **{row['Acceso_YT']}**")
                st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                c_edit, c_del = st.columns(2)
                with c_edit:
                    if st.button("📝 Ajustes", key=f"eu_{idx}", use_container_width=True): 
                        @st.dialog("Editar Vendedor")
                        def editar_vendedor_popup(i, r):
                            global df_usuarios
                            st.write(f"Editando a: **{r['Usuario']}**")
                            n_tel = st.text_input("Teléfono", value=r['Telefono'])
                            n_pwd = st.text_input("Nueva Contraseña", value=r['Password'])
                            n_acc = st.checkbox("✅ Acceso a YouTube Auto", value=(r['Acceso_YT'] == 'Si'))
                            if st.button("Actualizar Permisos", type="primary", use_container_width=True):
                                df_usuarios.at[i, 'Telefono'] = n_tel
                                df_usuarios.at[i, 'Password'] = n_pwd
                                df_usuarios.at[i, 'Acceso_YT'] = "Si" if n_acc else "No"
                                save_df(df_usuarios, "Usuarios")
                                st.session_state.toast_msg = "✅ Perfil actualizado."
                                st.rerun()
                        editar_vendedor_popup(idx, row)
                with c_del:
                    if st.button("🗑️ Despedir", key=f"du_{idx}", use_container_width=True):
                        df_usuarios = df_usuarios.drop(idx)
                        save_df(df_usuarios, "Usuarios")
                        st.session_state.toast_msg = "🗑️ Vendedor retirado."
                        st.rerun()

elif menu == "Ajustes":
    if st.session_state.role != "Admin" and st.session_state.acceso_yt == "No":
        st.info("🔓 **Desbloquea Bóveda**\nAccede a YouTube Automático.")
        msj_up_menu = f"Hola Admin, soy {st.session_state.user}. Quiero adquirir el acceso a la bóveda de YouTube por S/ 5.00."
        st.link_button("📲 Solicitar Activación al Administrador", f"https://wa.me/{NUMERO_ADMIN}?text={quote(msj_up_menu)}", use_container_width=True)
        st.divider()
        
    with st.expander("📝 Configurar Bot de WhatsApp", expanded=False):
        st.info("Variables: `{cliente}`, `{producto}`, `{vencimiento}`, `{nombre}`, `{usuario}`, `{password}`, `{link}`.")
        with st.form("form_plantillas"):
            rec = st.text_area("🟠 Mensaje de Recordatorio", value=plantillas_wa.get("recordatorio", ""), height=80)
            ven = st.text_area("🔴 Mensaje de Vencimiento", value=plantillas_wa.get("vencido", ""), height=80)
            ven_new = st.text_area("🧑‍🚀 Bienvenida a Vendedor", value=plantillas_wa.get("vendedor", ""), height=100)
            if st.form_submit_button("💾 Guardar Textos", type="primary", use_container_width=True):
                plantillas_wa["recordatorio"] = rec
                plantillas_wa["vencido"] = ven
                plantillas_wa["vendedor"] = ven_new
                save_templates(plantillas_wa)
                st.session_state.toast_msg = "✅ ¡Textos actualizados!"
                st.rerun()
    st.divider()
    st.subheader("🛠 Plataformas")
    c_plat, c_pbtn = st.columns([3, 1])
    with c_plat: nueva_p = st.text_input("Nueva", label_visibility="collapsed", placeholder="Ej: Crunchyroll")
    with c_pbtn:
        if st.button("➕", use_container_width=True):
            if nueva_p and nueva_p not in lista_plataformas:
                lista_plataformas.append(nueva_p)
                save_df(pd.DataFrame(lista_plataformas, columns=["Nombre"]), "Plataformas")
                st.session_state.toast_msg = f"✅ {nueva_p} añadida."
                st.rerun()
    for p in lista_plataformas:
        cp1, cp2 = st.columns([4, 1])
        cp1.write(f"📺 {p}")
        if cp2.button("🗑️", key=f"del_p_{p}", use_container_width=True):
            lista_plataformas.remove(p)
            save_df(pd.DataFrame(lista_plataformas, columns=["Nombre"]), "Plataformas")
            st.session_state.toast_msg = "🗑️ Eliminada."
            st.rerun()
