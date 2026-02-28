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
VERSION_APP = "3.1 (UX Premium & Fix Definitivo)"

LINK_APP = "https://mi-negocio-streaming-chkfid6tmyepuartagxlrq.streamlit.app/" 
NUMERO_ADMIN = "51902028672" 

st.set_page_config(page_title="NEXA-Stream", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# Sistema inteligente de Notificaciones Toast
if 'toast_msg' not in st.session_state:
    st.session_state.toast_msg = None

if st.session_state.toast_msg:
    st.toast(st.session_state.toast_msg)
    st.session_state.toast_msg = None

st.markdown(f"""
    <style>
    .version-corner {{
        position: fixed; top: 15px; right: 70px; background-color: rgba(0, 210, 106, 0.2);
        color: #00D26A; padding: 4px 10px; border-radius: 12px; font-size: 12px;
        font-weight: bold; z-index: 999999; pointer-events: none; border: 1px solid #00D26A;
    }}
    </style>
    <div class="version-corner">v{VERSION_APP}</div>
""", unsafe_allow_html=True)

# ==============================================================================
# BLOQUE 2: CSS MÓVIL, TARJETAS FLOTANTES Y ESTILOS PREMIUM
# ==============================================================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    
    /* Efecto Hover en las Tarjetas (Containers) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border: 1px solid #2A2F3D !important;
        background-color: #1A1E2C !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(0, 210, 106, 0.15) !important;
        border-color: #00D26A !important;
    }
    
    /* Hero Metrics (Dashboard) */
    div[data-testid="metric-container"] { 
        background: linear-gradient(145deg, #1A1E2C, #131620) !important; 
        border: 1px solid #2A2F3D !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important; 
        padding: 20px !important; 
        border-radius: 16px !important; 
    }
    
    /* Etiquetas (Badges) estilo Apple */
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-right: 8px; display: inline-block; margin-bottom: 5px;}
    .badge-netflix { background-color: rgba(229, 9, 20, 0.15); color: #E50914; border: 1px solid #E50914; }
    .badge-youtube { background-color: rgba(255, 0, 0, 0.15); color: #FF4444; border: 1px solid #FF4444; }
    .badge-spotify { background-color: rgba(29, 185, 84, 0.15); color: #1DB954; border: 1px solid #1DB954; }
    .badge-disney { background-color: rgba(17, 60, 207, 0.2); color: #4A7BFF; border: 1px solid #4A7BFF; }
    .badge-default { background-color: rgba(255, 255, 255, 0.1); color: #FFF; border: 1px solid #777; }
    .badge-green { background-color: rgba(0, 210, 106, 0.15); color: #00D26A; border: 1px solid #00D26A;}
    .badge-orange { background-color: rgba(255, 152, 0, 0.15); color: #FF9800; border: 1px solid #FF9800;}
    .badge-red { background-color: rgba(244, 67, 54, 0.15); color: #F44336; border: 1px solid #F44336;}
    
    /* Botones más curvos */
    .stButton>button, .stLinkButton>a { border-radius: 10px !important; height: 38px !important; padding: 0px !important; display: flex !important; align-items: center !important; justify-content: center !important; width: 100% !important; font-size: 15px !important; font-weight: 600 !important; margin: 0px !important; transition: all 0.2s; }
    .stLinkButton>a { background-color: #25D366 !important; color: white !important; border: none !important; }
    .stLinkButton>a:hover { background-color: #20BA59 !important; transform: scale(1.02); }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div { border-radius: 10px; height: 38px; }
    
    /* Distribución de botones */
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 6px !important; }
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { width: 25% !important; min-width: 0 !important; flex: 1 1 0px !important; }
    .element-container:has(.fila-alerta) + .element-container > div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 6px !important; }
    .element-container:has(.fila-alerta) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { width: 50% !important; min-width: 0 !important; flex: 1 1 0px !important; }
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

NOMBRES = ["Juan", "Carlos", "Jose", "Luis", "David", "Javier", "Daniel", "Maria", "Ana", "Rosa", "Carmen", "Sofia", "Lucia"]
APELLIDOS = ["Garcia", "Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez", "Sanchez", "Ramirez", "Cruz", "Flores", "Gomez"]

def generar_lote_correos(cantidad=10):
    lote = []
    for _ in range(cantidad):
        n, a = random.choice(NOMBRES), random.choice(APELLIDOS)
        usr = f"{n.lower()}.{a.lower()}.prem{random.randint(1000, 9999)}"
        lote.append({"Nombre": n, "Apellido": a, "Usuario": usr, "Correo": f"{usr}@gmail.com", "Pass": generar_password_aleatoria()})
    return lote

MESES_NOMBRES = {'01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril', '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto', '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'}
def formatear_mes_anio(yyyy_mm):
    y, m = yyyy_mm.split('-')
    return f"{MESES_NOMBRES[m]} {y}"

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
    st.title("🚀 Portal NEXA-Stream")
    st.markdown("Bienvenido al sistema de gestión inteligente.")
    st.write("---")
    c_log1, c_log2, c_log3 = st.columns([1,2,1])
    with c_log2:
        with st.container(border=True):
            st.subheader("🔐 Iniciar Sesión")
            with st.form("login_form"):
                u_in = st.text_input("Usuario", autocomplete="username", placeholder="ej: admin")
                p_in = st.text_input("Contraseña", type="password", autocomplete="current-password", placeholder="••••••••")
                st.write("")
                ingresar = st.form_submit_button("Acceder al Dashboard", type="primary", use_container_width=True)
                
                if ingresar:
                    match = df_usuarios[(df_usuarios['Usuario'] == u_in) & (df_usuarios['Password'] == p_in)]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user = match.iloc[0]['Usuario']
                        st.session_state.role = match.iloc[0]['Rol']
                        st.session_state.acceso_yt = match.iloc[0]['Acceso_YT']
                        st.session_state.alertas_vistas = False
                        cookies.set('nexa_user_cookie', match.iloc[0]['Usuario'])
                        st.session_state.toast_msg = f"👋 ¡Hola de nuevo, {match.iloc[0]['Usuario']}!"
                        st.rerun()
                    else: 
                        st.error("❌ Credenciales incorrectas.")
    st.stop()

# ==============================================================================
# BLOQUE 5: DIÁLOGOS DE GESTIÓN
# ==============================================================================
@st.dialog("⏰ Centro de Cobranza Urgente")
def mostrar_popup_alertas(df_urgente, hoy):
    global df_ventas, df_ex_clientes
    st.warning("⚠️ **ATENCIÓN:** Los siguientes clientes requieren gestión inmediata.")
    st.write("---")
    for idx, row in df_urgente.sort_values(by="Vencimiento").iterrows():
        dias = (row['Vencimiento'] - hoy).days
        if dias == 3: estado_txt, badge_col = "Vence en 3 días", "badge-orange"
        elif dias == 2: estado_txt, badge_col = "Vence en 2 días", "badge-orange"
        elif dias == 1: estado_txt, badge_col = "Vence en 1 día", "badge-orange"
        elif dias == 0: estado_txt, badge_col = "VENCE HOY", "badge-red"
        elif dias == -1: estado_txt, badge_col = "Vencido (1 día)", "badge-red"
        else: estado_txt, badge_col = f"Vencido ({abs(dias)} días)", "badge-red"

        prod_b = "badge-youtube" if "YouTube" in row['Producto'] else "badge-netflix" if "Netflix" in row['Producto'] else "badge-spotify" if "Spotify" in row['Producto'] else "badge-disney" if "Disney" in row['Producto'] else "badge-default"

        if dias <= 0: texto_base = plantillas_wa["vencido"]
        else: texto_base = plantillas_wa["recordatorio"]
            
        texto_wa = texto_base.replace("{cliente}", str(row['Cliente'])).replace("{producto}", str(row['Producto'])).replace("{vencimiento}", str(row['Vencimiento']))
        wa_url = f"https://wa.me/{row['WhatsApp']}?text={quote(texto_wa)}"
        
        with st.container(border=True):
            st.markdown(f"""
            <div style="margin-bottom: 5px;">
                <h4 style="margin:0; padding:0; display:inline-block; margin-right: 10px;">👤 {row['Cliente']}</h4>
            </div>
            <div>
                <span class="badge {prod_b}">📺 {row['Producto']}</span>
                <span class="badge {badge_col}">⚠️ {estado_txt}</span>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"📧 {row['Correo']} | 🔑 {row['Pass']}")
            st.markdown('<div class="fila-alerta"></div>', unsafe_allow_html=True)
            ca1, ca2 = st.columns(2)
            with ca1: st.link_button("📲 Enviar Mensaje", wa_url, use_container_width=True)
            with ca2:
                if st.button("🗑️ A Papelera", key=f"alerta_del_{idx}", use_container_width=True):
                    df_ex_clientes = pd.concat([df_ex_clientes, pd.DataFrame([row])], ignore_index=True)
                    save_df(df_ex_clientes, "ExClientes")
                    df_ventas = df_ventas.drop(idx)
                    save_df(df_ventas, "Ventas")
                    st.session_state.toast_msg = "🗑️ Cliente movido a la papelera."
                    st.rerun()
    st.write("---")
    if st.button("Entendido, cerrar por ahora", type="primary", use_container_width=True):
        st.session_state.alertas_vistas = True
        st.rerun()

@st.dialog("🔄 Renovar Suscripción")
def renovar_venta_popup(idx, row):
    global df_ventas
    st.write(f"Renovando a: **{row['Cliente']}** (📺 {row['Producto']})")
    if row['Producto'] == "YouTube Premium":
        st.error(f"⚠️ **RECUERDA:** Saca el correo actual (**{row['Correo']}**) del grupo familiar ANTES de renovar.")
        
    dur = st.radio("Plazo de renovación:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    hoy = datetime.now().date()
    venc_actual = pd.to_datetime(row['Vencimiento']).date()
    fecha_base = max(hoy, venc_actual) 
    if dur == "1 Mes": nueva_fecha = fecha_base + timedelta(days=30)
    elif dur == "2 Meses": nueva_fecha = fecha_base + timedelta(days=60)
    elif dur == "6 Meses": nueva_fecha = fecha_base + timedelta(days=180)
    else: nueva_fecha = fecha_base + timedelta(days=365)
    
    st.info(f"📅 Nuevo vencimiento: **{nueva_fecha}**")
    st.divider()
    tipo_cta = st.radio("Credenciales para este periodo:", ["Mantener misma cuenta", "Asignar cuenta nueva (Rotativa)"], horizontal=True)
    mv, pv = row['Correo'], row['Pass'] 
    
    if tipo_cta == "Asignar cuenta nueva (Rotativa)":
        ca, cb = st.columns(2)
        tiene_acceso_inventario = (st.session_state.role == "Admin") or (st.session_state.acceso_yt == "Si")
        
        if row['Producto'] == "YouTube Premium":
            if tiene_acceso_inventario:
                disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
                if not disponibles.empty:
                    sug = disponibles.iloc[0]
                    with ca: mv = st.text_input("Auto-Correo", value=sug['Correo'])
                    with cb: pv = st.text_input("Nueva Clave", value=sug['Password'])
                else:
                    st.warning("Inventario Vacío.")
                    with ca: mv = st.text_input("Nuevo Correo Manual")
                    with cb: pv = st.text_input("Nueva Clave Manual")
            else:
                st.warning("🚀 **¡Automatiza tus renovaciones!** (S/ 5.00)")
                msj_up = f"Hola Admin, soy {st.session_state.user}. Quiero activar mi acceso a la bóveda de YouTube Premium."
                st.link_button("📲 Solicitar Activación", f"https://wa.me/{NUMERO_ADMIN}?text={quote(msj_up)}", use_container_width=True)
                with ca: mv = st.text_input("Correo Manual")
                with cb: pv = st.text_input("Clave Manual")
        else:
            with ca: mv = st.text_input("Nuevo Correo")
            with cb: pv = st.text_input("Nueva Clave")
            
    if st.button("CONFIRMAR RENOVACIÓN", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Vencimiento'] = nueva_fecha
        df_ventas.at[idx, 'Correo'] = mv
        df_ventas.at[idx, 'Pass'] = pv
        save_df(df_ventas, "Ventas")
        st.session_state.toast_msg = "🔄 ¡Renovación exitosa!"
        st.rerun()

@st.dialog("📝 Editar Registro")
def editar_venta_popup(idx, row):
    global df_ventas
    prod = st.selectbox("Plataforma", lista_plataformas, index=lista_plataformas.index(row['Producto']) if row['Producto'] in lista_plataformas else 0)
    nom = st.text_input("Nombre", value=row['Cliente'])
    tel = st.text_input("WhatsApp", value=row['WhatsApp'])
    venc = st.date_input("Vencimiento", row['Vencimiento'])
    st.divider()
    c_costo, c_precio = st.columns(2)
    val_costo = float(row['Costo']) if not pd.isna(row.get('Costo')) else 0.0
    val_precio = float(row['Precio']) if not pd.isna(row.get('Precio')) else 0.0
    costo = c_costo.number_input("Costo (Pagas)", value=val_costo, step=1.0)
    precio = c_precio.number_input("Precio Venta", value=val_precio, step=1.0)
    st.divider()
    m = st.text_input("Correo", value=row['Correo'])
    p = st.text_input("Pass", value=row['Pass'])
    perf = st.text_input("Perfil", value=row['Perfil'])
    if st.button("ACTUALIZAR", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Cliente'], df_ventas.at[idx, 'WhatsApp'] = nom, limpiar_whatsapp(tel)
        df_ventas.at[idx, 'Producto'], df_ventas.at[idx, 'Vencimiento'] = prod, venc
        df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'], df_ventas.at[idx, 'Perfil'] = m, p, perf
        df_ventas.at[idx, 'Costo'], df_ventas.at[idx, 'Precio'] = costo, precio
        save_df(df_ventas, "Ventas")
        st.session_state.toast_msg = "💾 Cambios guardados."
        st.rerun()

@st.dialog("➕ Nueva Venta")
def nueva_venta_popup():
    global df_ventas
    c1, c2 = st.columns(2)
    with c1: prod = st.selectbox("Plataforma", lista_plataformas)
    with c2: f_ini = st.date_input("Inicio", datetime.now())
    nom = st.text_input("Nombre Cliente", placeholder="Ej: Maria Lopez")
    tel = st.text_input("WhatsApp", placeholder="Ej: 999888777")
    c_costo, c_precio = st.columns(2)
    costo = c_costo.number_input("Costo cuenta", value=0.0, step=1.0)
    precio = c_precio.number_input("Precio Venta", value=0.0, step=1.0)
    dur = st.radio("Plazo:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    if dur == "1 Mes": venc = f_ini + timedelta(days=30)
    elif dur == "2 Meses": venc = f_ini + timedelta(days=60)
    elif dur == "6 Meses": venc = f_ini + timedelta(days=180)
    else: venc = f_ini + timedelta(days=365)
    
    st.divider()
    ca, cb = st.columns(2)
    tiene_acceso_inventario = (st.session_state.role == "Admin") or (st.session_state.acceso_yt == "Si")
    
    if prod == "YouTube Premium":
        if tiene_acceso_inventario:
            if not df_inv.empty:
                disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
                if not disponibles.empty:
                    sug = disponibles.iloc[0]
                    with ca: mv = st.text_input("Correo Auto", value=sug['Correo'])
                    with cb: pv = st.text_input("Clave", value=sug['Password'])
                else: 
                    st.warning("Inventario sin cupos.")
                    with ca: mv = st.text_input("Correo Manual")
                    with cb: pv = st.text_input("Pass Manual")
            else:
                st.warning("Inventario vacío.")
                with ca: mv = st.text_input("Correo")
                with cb: pv = st.text_input("Pass")
        else:
            st.warning("🚀 **Obtén auto-asignación YT**")
            msj_up = f"Hola Admin, soy {st.session_state.user}. Quiero activar la bóveda de YouTube."
            st.link_button("📲 Solicitar Activación", f"https://wa.me/{NUMERO_ADMIN}?text={quote(msj_up)}", use_container_width=True)
            with ca: mv = st.text_input("Correo Manual")
            with cb: pv = st.text_input("Clave Manual")
    else: 
        with ca: mv = st.text_input("Correo")
        with cb: pv = st.text_input("Pass")
    
    if st.button("🚀 REGISTRAR VENTA", type="primary", use_container_width=True):
        nueva = pd.DataFrame([[ "🟢", nom, limpiar_whatsapp(tel), prod, mv, pv, "nan", "nan", venc, st.session_state.user, costo, precio ]], columns=df_ventas.columns)
        df_ventas = pd.concat([df_ventas, nueva], ignore_index=True)
        save_df(df_ventas, "Ventas")
        st.session_state.toast_msg = "🎉 ¡Nueva venta registrada!"
        st.rerun()

# ==============================================================================
# BLOQUE 6: NAVEGACIÓN LATERAL PREMIUM
# ==============================================================================
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding-bottom: 20px;">
            <h1 style="color: #00D26A; margin-bottom:0;">NEXA</h1>
            <h3 style="margin-top:0; color: white;">STREAM</h3>
            <p style="color: #888; font-size: 14px;">👤 {user} | {rol}</p>
        </div>
    """.format(user=st.session_state.user, rol=st.session_state.role), unsafe_allow_html=True)
    
    if st.session_state.role != "Admin" and st.session_state.acceso_yt == "No":
        st.info("🔓 **Mejora tu cuenta**\nAccede a la bóveda de YouTube.")
        
    st.divider()
    
    if st.session_state.role == "Admin":
        opciones_menu = ["Panel de Ventas", "Dashboard", "Ex-Clientes", "Inventario YT", "Vendedores", "Configuración"]
        iconos_menu = ["cart-check-fill", "bar-chart-fill", "trash3-fill", "youtube", "people-fill", "gear-fill"]
    else:
        opciones_menu = ["Panel de Ventas", "Dashboard", "Ex-Clientes"]
        iconos_menu = ["cart-check-fill", "bar-chart-fill", "trash3-fill"]

    menu = option_menu(
        menu_title=None,
        options=opciones_menu,
        icons=iconos_menu,
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00D26A", "font-size": "18px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"2px", "--hover-color": "#262730"},
            "nav-link-selected": {"background-color": "#00D26A", "color": "white", "font-weight": "bold"},
        }
    )
    
    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        cookies.remove('nexa_user_cookie') 
        st.session_state.logged_in = False
        st.rerun()

# ==============================================================================
# VISTAS PRINCIPALES
# ==============================================================================

if menu == "Panel de Ventas":
    st.header("🎯 Gestión de Suscripciones")
    
    if st.session_state.role == "Admin":
        cupos_disponibles = len(df_inv[df_inv['Usos'] < 2]) if not df_inv.empty else 0
        if cupos_disponibles <= 2:
            st.error(f"🚨 **¡ATENCIÓN!** Solo quedan **{cupos_disponibles}** cupos automáticos.")

    if st.session_state.role == "Admin":
        tipo_filtro = st.selectbox("👥 Filtro de Vendedores:", ["🌎 Mostrar Todos", "👥 Todos sin Admin", "👑 Solo Admin", "🎯 Personalizado..."], label_visibility="collapsed")
        if tipo_filtro == "🌎 Mostrar Todos": df_mostrar = df_ventas
        elif tipo_filtro == "👥 Todos sin Admin": df_mostrar = df_ventas[df_ventas['Vendedor'] != st.session_state.user]
        elif tipo_filtro == "👑 Solo Admin": df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]
        else:
            lista_v = sorted(list(set(df_ventas['Vendedor'].dropna().tolist() + df_usuarios['Usuario'].tolist())))
            vend_sel = st.multiselect("Vendedores:", lista_v, default=lista_v)
            df_mostrar = df_ventas[df_ventas['Vendedor'].isin(vend_sel)]
    else: df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]

    hoy = datetime.now().date()
    if not df_mostrar.empty:
        df_urgente = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy + timedelta(days=3)]
        if not st.session_state.alertas_vistas and not df_urgente.empty:
            mostrar_popup_alertas(df_urgente, hoy)
        
    h1, h2 = st.columns([3, 1])
    with h1: 
        if st.button("➕ REGISTRAR NUEVA VENTA", type="primary", use_container_width=True): nueva_venta_popup()
    with h2: 
        if st.button("🔔 Alertas", use_container_width=True):
            st.session_state.alertas_vistas = False
            st.rerun()
            
    st.write("")
    filtro_est = st.radio("Estado de Cuenta:", ["🌎 Todas", "🟢 Activas", "🟠 Por Vencer", "🔴 Vencidas"], horizontal=True, label_visibility="collapsed")
    
    c_f1, c_f2 = st.columns([2, 1])
    search = c_f1.text_input("", placeholder="🔍 Buscar por nombre o número...", label_visibility="collapsed")
    filtro_plat = c_f2.selectbox("Plataforma", ["Todas las Plataformas"] + lista_plataformas, label_visibility="collapsed")

    if search: mask_search = df_mostrar.apply(lambda r: search.lower() in str(r).lower(), axis=1); df_mostrar = df_mostrar[mask_search]
    if filtro_plat != "Todas las Plataformas": df_mostrar = df_mostrar[df_mostrar['Producto'] == filtro_plat]
    
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
            
            if d <= 0: estado_txt, badge_col = "Vencido", "badge-red"
            elif d <= 3: estado_txt, badge_col = f"Vence en {d} d.", "badge-orange"
            else: estado_txt, badge_col = "Activo", "badge-green"
                
            prod_badge = "badge-youtube" if "YouTube" in row['Producto'] else "badge-netflix" if "Netflix" in row['Producto'] else "badge-spotify" if "Spotify" in row['Producto'] else "badge-disney" if "Disney" in row['Producto'] else "badge-default"

            if d <= 0: texto_base = plantillas_wa["vencido"]
            else: texto_base = plantillas_wa["recordatorio"]
                
            texto_wa = texto_base.replace("{cliente}", str(row['Cliente'])).replace("{producto}", str(row['Producto'])).replace("{vencimiento}", str(row['Vencimiento']))
            wa_url = f"https://wa.me/{row['WhatsApp']}?text={quote(texto_wa)}"
            
            with st.container(border=True):
                vendedor_badge = f" • 🧑‍💼 {row['Vendedor']}" if st.session_state.role == "Admin" else ""
                st.markdown(f"""
                <div style="margin-bottom: 5px;">
                    <h4 style="margin:0; padding:0; display:inline-block; margin-right: 10px;">👤 {row['Cliente']}</h4>
                </div>
                <div>
                    <span class="badge {prod_badge}">📺 {row['Producto']}</span>
                    <span class="badge {badge_col}">⏱️ {estado_txt}</span>
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"📧 {row['Correo']} | 🔑 {row['Pass']} | 📅 Vence: {row['Vencimiento']} {vendedor_badge}")
                
                st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                cols = st.columns(4)
                with cols[0]: st.link_button("📲 Notificar", wa_url, use_container_width=True)
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
        st.info("No hay registros que coincidan con la búsqueda.")

elif menu == "Dashboard":
    st.header("📈 Análisis Financiero")
    
    if st.session_state.role == "Admin": 
        tipo_filtro_dash = st.selectbox("Filtro de Vendedores:", 
            ["🌎 Mostrar Todos", "👥 Todos sin Admin", "👑 Solo Admin", "🎯 Seleccionar específicos..."], key="filt_dash", label_visibility="collapsed")
        if tipo_filtro_dash == "🌎 Mostrar Todos": df_dash_base = df_ventas.copy()
        elif tipo_filtro_dash == "👥 Todos sin Admin": df_dash_base = df_ventas[df_ventas['Vendedor'] != st.session_state.user].copy()
        elif tipo_filtro_dash == "👑 Solo Admin": df_dash_base = df_ventas[df_ventas['Vendedor'] == st.session_state.user].copy()
        else:
            lista_v = sorted(list(set(df_ventas['Vendedor'].dropna().tolist() + df_usuarios['Usuario'].tolist())))
            vend_sel_dash = st.multiselect("Marca los vendedores:", lista_v, default=lista_v, key="mult_dash")
            df_dash_base = df_ventas[df_ventas['Vendedor'].isin(vend_sel_dash)].copy()
    else: df_dash_base = df_ventas[df_ventas['Vendedor'] == st.session_state.user].copy()
        
    if df_dash_base.empty: st.warning("No hay suficientes datos registrados.")
    else:
        df_dash_base['Vencimiento_dt'] = pd.to_datetime(df_dash_base['Vencimiento'], errors='coerce')
        df_dash_base['Periodo'] = df_dash_base['Vencimiento_dt'].dt.strftime('%Y-%m')
        periodos_disponibles = sorted(df_dash_base['Periodo'].dropna().unique().tolist(), reverse=True)
        opciones_periodos = ["Histórico Global"] + periodos_disponibles
        formato_opciones = lambda x: "Histórico Global (Todo)" if x == "Histórico Global" else formatear_mes_anio(x)
        
        st.write("")
        periodo_sel = st.radio("📅 Selecciona el periodo mensual:", opciones_periodos, format_func=formato_opciones, horizontal=True)
        
        if periodo_sel != "Histórico Global": df_dash = df_dash_base[df_dash_base['Periodo'] == periodo_sel]
        else: df_dash = df_dash_base
            
        st.write("---")
        if df_dash.empty: st.info("No hay ventas en este periodo.")
        else:
            df_dash['Costo'] = pd.to_numeric(df_dash['Costo'], errors='coerce').fillna(0)
            df_dash['Precio'] = pd.to_numeric(df_dash['Precio'], errors='coerce').fillna(0)
            total_ingresos = df_dash['Precio'].sum()
            total_costos = df_dash['Costo'].sum()
            total_ganancia = total_ingresos - total_costos
            total_clientes = len(df_dash)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👥 Clientes Activos", f"{total_clientes}")
            c2.metric("💰 Ventas Brutas", f"S/ {total_ingresos:.2f}")
            c3.metric("📉 Costos", f"S/ {total_costos:.2f}")
            c4.metric("🚀 GANANCIA NETA", f"S/ {total_ganancia:.2f}")
            
            st.write("---")
            st.subheader("Distribución de Plataformas")
            ventas_plat = df_dash['Producto'].value_counts().reset_index()
            ventas_plat.columns = ['Plataforma', 'Cantidad']
            grafico_anillo = alt.Chart(ventas_plat).mark_arc(innerRadius=60).encode(
                theta=alt.Theta(field="Cantidad", type="quantitative"),
                color=alt.Color(field="Plataforma", type="nominal", legend=alt.Legend(title="Plataformas", orient="bottom", labelColor="white", titleColor="white")),
                tooltip=['Plataforma', 'Cantidad']
            ).properties(height=350).configure_view(strokeWidth=0).configure_legend(labelFontSize=14, titleFontSize=15)
            st.altair_chart(grafico_anillo, use_container_width=True)

elif menu == "Ex-Clientes":
    st.header("📂 Historial y Papelera")
    df_ex_mostrar = df_ex_clientes if st.session_state.role == "Admin" else df_ex_clientes[df_ex_clientes['Vendedor'] == st.session_state.user]
    if df_ex_mostrar.empty: st.info("La papelera está limpia.")
    else:
        for idx, row in df_ex_mostrar.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(f"🚫 **{row['Cliente']}** ({row['Producto']}) - Tel: {row['WhatsApp']}")
                if c2.button("🗑️ Borrar Definitivo", key=f"ex_{idx}", use_container_width=True):
                    df_ex_clientes = df_ex_clientes.drop(idx)
                    save_df(df_ex_clientes, "ExClientes")
                    st.session_state.toast_msg = "✅ Borrado permanentemente."
                    st.rerun()

elif menu == "Inventario YT":
    st.header("📦 Inventario YouTube")
    
    with st.expander("⚡ Asistente de Creación Masiva", expanded=True):
        st.info("💡 Toca el ícono de copiar al lado de cada bloque para pegarlo directamente en Google.")
        if st.button("🔄 Generar 10 Perfiles", use_container_width=True):
            st.session_state.temp_emails = generar_lote_correos(10)
            st.rerun()
        if st.session_state.temp_emails:
            st.write("---")
            for i, acc in enumerate(st.session_state.temp_emails):
                with st.container(border=True):
                    st.write(f"👤 **{acc['Nombre']} {acc['Apellido']}**")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("Nombre:")
                        st.code(acc['Nombre'], language=None)
                        st.caption("Usuario (Sin @):")
                        st.code(acc['Usuario'], language=None)
                    with c2:
                        st.caption("Apellido:")
                        st.code(acc['Apellido'], language=None)
                        st.caption("Contraseña:")
                        st.code(acc['Pass'], language=None)
                    
                    if st.button("🗑️ Descartar Cuenta", key=f"del_tmp_{i}", use_container_width=True):
                        st.session_state.temp_emails.pop(i)
                        st.rerun()
            st.write("---")
            if st.button("✅ Confirmar y Guardar en Inventario", type="primary", use_container_width=True):
                nuevos_df = pd.DataFrame([[acc['Correo'], acc['Pass'], 0, "Nadie"] for acc in st.session_state.temp_emails], columns=df_inv.columns)
                df_inv = pd.concat([df_inv, nuevos_df], ignore_index=True)
                save_df(df_inv, "Inventario")
                st.session_state.temp_emails = []
                st.session_state.toast_msg = "✅ Lote guardado con éxito."
                st.rerun()
                
    st.write("---")
    
    if st.button("➕ NUEVO CORREO MANUAL", type="primary", use_container_width=True):
        @st.dialog("Registrar Correo")
        def add():
            global df_inv
            m = st.text_input("Gmail")
            p = st.text_input("Contraseña")
            u = st.selectbox("Usos", [0,1,2])
            if st.button("Guardar"):
                ni = pd.DataFrame([[m, p, u, "Nadie"]], columns=df_inv.columns)
                df_inv = pd.concat([df_inv, ni], ignore_index=True)
                save_df(df_inv, "Inventario")
                st.session_state.toast_msg = "✅ Correo guardado."
                st.rerun()
        add()
    for idx, row in df_inv.iterrows():
        with st.container(border=True):
            st.write(f"📧 **{row['Correo']}** (Usos: {row['Usos']})")
            st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📝 Editar", key=f"ei_{idx}", use_container_width=True): 
                    @st.dialog("Modificar")
                    def edi():
                        global df_inv
                        nu = st.selectbox("Usos", [0,1,2], index=int(row['Usos']))
                        na = st.text_input("Asignado a", value=row['Asignado_A'])
                        if st.button("Actualizar"):
                            df_inv.at[idx, 'Usos'], df_inv.at[idx, 'Asignado_A'] = nu, na
                            save_df(df_inv, "Inventario")
                            st.rerun()
                    edi()
            with c2:
                if st.button("🗑️ Borrar", key=f"di_{idx}", use_container_width=True):
                    df_inv = df_inv.drop(idx)
                    save_df(df_inv, "Inventario")
                    st.session_state.toast_msg = "🗑️ Borrado del inventario."
                    st.rerun()

elif menu == "Vendedores":
    st.header("👥 Control de Personal")
    @st.dialog("Editar Vendedor")
    def editar_vendedor_popup(idx, row):
        global df_usuarios
        st.write(f"Editando a: **{row['Usuario']}**")
        n_tel = st.text_input("Teléfono", value=row['Telefono'])
        n_pwd = st.text_input("Nueva Contraseña", value=row['Password'])
        n_acc = st.checkbox("✅ Acceso a YouTube Auto", value=(row['Acceso_YT'] == 'Si'))
        if st.button("Actualizar", type="primary", use_container_width=True):
            df_usuarios.at[idx, 'Telefono'] = n_tel
            df_usuarios.at[idx, 'Password'] = n_pwd
            df_usuarios.at[idx, 'Acceso_YT'] = "Si" if n_acc else "No"
            save_df(df_usuarios, "Usuarios")
            st.session_state.toast_msg = "✅ Vendedor actualizado."
            st.rerun()
            
    if st.session_state.nuevo_vend_usr:
        usr_gen = st.session_state.nuevo_vend_usr
        pwd_gen = st.session_state.nuevo_vend_pwd
        nom_gen = st.session_state.nuevo_vend_nom
        tel_gen = st.session_state.nuevo_vend_tel
        texto_wa = plantillas_wa["vendedor"].replace("{nombre}", nom_gen).replace("{usuario}", usr_gen).replace("{password}", pwd_gen).replace("{link}", LINK_APP)
        enlace_wa = f"https://wa.me/{tel_gen}?text={quote(texto_wa)}"
        st.success("✅ ¡PERFIL CREADO CON ÉXITO!")
        st.info(f"**Usuario:** {usr_gen} | **Contraseña:** {pwd_gen}")
        col_wa, col_ok = st.columns(2)
        col_wa.link_button("📲 Enviar clave", enlace_wa, use_container_width=True)
        if col_ok.button("✅ Ocultar", use_container_width=True):
            st.session_state.nuevo_vend_usr = None
            st.rerun()
    else:
        with st.container(border=True):
            st.subheader("➕ Generar Nuevo Perfil")
            with st.form("form_crear_vend"):
                col1, col2 = st.columns(2)
                nuevo_nom = col1.text_input("Nombre (ej: Juan)")
                nuevo_tel = col2.text_input("WhatsApp (ej: 999888777)")
                dar_acceso_yt = st.checkbox("Dar acceso al Relleno Automático de YouTube")
                if st.form_submit_button("Crear Perfil y Generar Clave", type="primary", use_container_width=True):
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
                        st.session_state.toast_msg = "✅ Perfil creado."
                        st.rerun()
                    else: st.warning("⚠️ Llenar Nombre y Teléfono.")
    st.write("---")
    vendedores = df_usuarios[df_usuarios['Rol'] != 'Admin']
    if vendedores.empty: st.info("Sin vendedores.")
    else:
        for idx, row in vendedores.iterrows():
            with st.container(border=True):
                st.write(f"👤 **{row['Usuario']}** | 📱 {row['Telefono']}")
                st.caption(f"🔑 Clave: {row['Password']} | 📺 Auto-asignar YT: **{row['Acceso_YT']}**")
                st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                c_edit, c_del = st.columns(2)
                with c_edit:
                    if st.button("📝 Editar", key=f"eu_{idx}", use_container_width=True): editar_vendedor_popup(idx, row)
                with c_del:
                    if st.button("🗑️ Borrar", key=f"du_{idx}", use_container_width=True):
                        df_usuarios = df_usuarios.drop(idx)
                        save_df(df_usuarios, "Usuarios")
                        st.session_state.toast_msg = "🗑️ Vendedor eliminado."
                        st.rerun()

elif menu == "Configuración":
    st.header("⚙️ Configuración General")
    with st.expander("📝 Editar Plantillas de WhatsApp", expanded=False):
        st.info("Usa `{cliente}`, `{producto}` y `{vencimiento}`. Para el vendedor usa `{nombre}`, `{usuario}`, `{password}` y `{link}`.")
        with st.form("form_plantillas"):
            rec = st.text_area("1️⃣ Recordatorio (Cuenta Activa / Por vencer)", value=plantillas_wa.get("recordatorio", ""), height=80)
            ven = st.text_area("2️⃣ Cuenta Vencida (Al llegar a 0 días)", value=plantillas_wa.get("vencido", ""), height=80)
            ven_new = st.text_area("3️⃣ Mensaje para Vendedor Nuevo", value=plantillas_wa.get("vendedor", ""), height=100)
            if st.form_submit_button("💾 Guardar Plantillas", type="primary", use_container_width=True):
                plantillas_wa["recordatorio"] = rec
                plantillas_wa["vencido"] = ven
                plantillas_wa["vendedor"] = ven_new
                save_templates(plantillas_wa)
                st.session_state.toast_msg = "✅ ¡Plantillas guardadas!"
                st.rerun()
    st.divider()
    st.subheader("🛠 Plataformas")
    c_plat, c_pbtn = st.columns([3, 1])
    with c_plat: nueva_p = st.text_input("Nueva", label_visibility="collapsed", placeholder="Escribe el nombre...")
    with c_pbtn:
        if st.button("➕ Añadir", use_container_width=True):
            if nueva_p and nueva_p not in lista_plataformas:
                lista_plataformas.append(nueva_p)
                save_df(pd.DataFrame(lista_plataformas, columns=["Nombre"]), "Plataformas")
                st.session_state.toast_msg = f"✅ Plataforma {nueva_p} añadida."
                st.rerun()
    for p in lista_plataformas:
        cp1, cp2 = st.columns([4, 1])
        cp1.write(f"📺 {p}")
        if cp2.button("🗑️ Borrar", key=f"del_p_{p}", use_container_width=True):
            lista_plataformas.remove(p)
            save_df(pd.DataFrame(lista_plataformas, columns=["Nombre"]), "Plataformas")
            st.session_state.toast_msg = "🗑️ Plataforma eliminada."
            st.rerun()
