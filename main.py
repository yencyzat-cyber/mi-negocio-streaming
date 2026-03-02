import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
import io

# ==============================================================================
# BLOQUE 1: CONFIGURACIÓN Y VARIABLES DE ESTADO
# ==============================================================================
VERSION_APP = "4.5 (Pills UI, Custom Payments & Fixes)"

LINK_APP = "https://mi-negocio-streaming-chkfid6tmyepuartagxlrq.streamlit.app/" 
NUMERO_ADMIN = "51902028672" 

st.set_page_config(page_title="NEXA-Stream", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""
if 'acceso_yt' not in st.session_state: st.session_state.acceso_yt = "No"
if 'alertas_vistas' not in st.session_state: st.session_state.alertas_vistas = False 
if 'temp_emails' not in st.session_state: st.session_state.temp_emails = []
if 'nuevo_vend_usr' not in st.session_state: st.session_state.nuevo_vend_usr = None
if 'nuevo_vend_pwd' not in st.session_state: st.session_state.nuevo_vend_pwd = None
if 'nuevo_vend_nom' not in st.session_state: st.session_state.nuevo_vend_nom = None
if 'nuevo_vend_tel' not in st.session_state: st.session_state.nuevo_vend_tel = None
if 'toast_msg' not in st.session_state: st.session_state.toast_msg = None

if st.session_state.toast_msg:
    st.toast(st.session_state.toast_msg)
    st.session_state.toast_msg = None

st.markdown(f"""
    <style>
    .version-corner {{ position: fixed; bottom: 15px; right: 15px; background-color: rgba(0, 210, 106, 0.1); color: #00D26A; padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; z-index: 999999; pointer-events: none; border: 1px solid rgba(0, 210, 106, 0.4); }}
    </style>
    <div class="version-corner">v{VERSION_APP}</div>
""", unsafe_allow_html=True)

# ==============================================================================
# BLOQUE 2: CSS ADAPTATIVO
# ==============================================================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important; border: 1px solid rgba(128,128,128,0.2) !important; background-color: var(--secondary-background-color) !important; margin-bottom: 10px; transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stExpander"] summary p { font-weight: bold !important; font-size: 15px !important; }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover { transform: translateY(-2px); border-color: #00D26A !important; }
    
    .kpi-card { padding: 20px; border-radius: 15px; color: white; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .kpi-blue { background: linear-gradient(135deg, #0052D4, #007BFF); }
    .kpi-orange { background: linear-gradient(135deg, #C85A17, #FF8C00); }
    .kpi-red { background: linear-gradient(135deg, #900C3F, #DC3545); }
    .kpi-green { background: linear-gradient(135deg, #0F5132, #28A745); }
    .kpi-title { font-size: 14px; opacity: 0.9; margin-bottom: 5px; }
    .kpi-value { font-size: 28px; font-weight: bold; margin: 0; }
    
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-right: 8px; display: inline-block; margin-bottom: 5px;}
    .badge-netflix { background-color: rgba(229, 9, 20, 0.15); color: #E50914; border: 1px solid rgba(229, 9, 20, 0.3); }
    .badge-youtube { background-color: rgba(255, 0, 0, 0.15); color: #FF4444; border: 1px solid rgba(255, 0, 0, 0.3); }
    .badge-spotify { background-color: rgba(29, 185, 84, 0.15); color: #1DB954; border: 1px solid rgba(29, 185, 84, 0.3); }
    .badge-disney { background-color: rgba(17, 60, 207, 0.15); color: #4A7BFF; border: 1px solid rgba(74, 123, 255, 0.3); }
    .badge-default { background-color: rgba(128, 128, 128, 0.1); color: var(--text-color); border: 1px solid rgba(128, 128, 128, 0.5); }
    .badge-green { background-color: rgba(0, 210, 106, 0.15); color: #00D26A; border: 1px solid rgba(0, 210, 106, 0.3);}
    .badge-orange { background-color: rgba(255, 152, 0, 0.15); color: #FF9800; border: 1px solid rgba(255, 152, 0, 0.3);}
    .badge-red { background-color: rgba(244, 67, 54, 0.15); color: #F44336; border: 1px solid rgba(244, 67, 54, 0.3);}
    
    .stButton>button, .stLinkButton>a { border-radius: 10px !important; height: 38px !important; padding: 0px !important; display: flex !important; align-items: center !important; justify-content: center !important; width: 100% !important; font-size: 15px !important; font-weight: 600 !important; margin: 0px !important; transition: all 0.2s; }
    .stLinkButton>a { background-color: #25D366 !important; color: white !important; border: none !important; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea { border-radius: 10px; }
    
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; gap: 6px !important; }
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { min-width: 45% !important; flex: 1 1 auto !important; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# BLOQUE 3: CONEXIÓN A GOOGLE SHEETS Y AUTO-MIGRACIÓN
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
    if not data: return pd.DataFrame(columns=cols)
    return pd.DataFrame(data).copy()

def save_df(df, ws_name):
    ws = sh.worksheet(ws_name)
    ws.clear()
    df_str = df.fillna("").astype(str)
    ws.update(values=[df_str.columns.values.tolist()] + df_str.values.tolist(), range_name="A1")
    get_sheet_records.clear() 

# --- CARGAR TABLAS ---
cols_ventas = ["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento", "Vendedor", "Costo", "Precio", "Notas"]
df_ventas = load_df("Ventas", cols_ventas)
migr_ventas = False
if "Notas" not in df_ventas.columns: df_ventas["Notas"] = ""; migr_ventas = True
if migr_ventas: save_df(df_ventas, "Ventas")
df_ventas['Vencimiento'] = pd.to_datetime(df_ventas['Vencimiento'], errors='coerce').dt.date

df_ex_clientes = load_df("ExClientes", cols_ventas)
migr_ex = False
if "Notas" not in df_ex_clientes.columns: df_ex_clientes["Notas"] = ""; migr_ex = True
if migr_ex: save_df(df_ex_clientes, "ExClientes")

cols_inv = ["Correo", "Password", "Usos", "Asignado_A", "Last_Seller", "Vencimiento_Boveda"]
df_inv = load_df("Inventario", cols_inv)
migr_inv = False
for c in ["Last_Seller", "Vencimiento_Boveda"]:
    if c not in df_inv.columns: df_inv[c] = ""; migr_inv = True
if migr_inv: save_df(df_inv, "Inventario")
if not df_inv.empty: df_inv['Usos'] = pd.to_numeric(df_inv['Usos'], errors='coerce').fillna(0)

df_plat = load_df("Plataformas", ["Nombre", "Usa_Boveda"])
migr_plat = False
if "Usa_Boveda" not in df_plat.columns:
    df_plat["Usa_Boveda"] = df_plat["Nombre"].apply(lambda x: "Si" if "YouTube" in str(x) else "No")
    migr_plat = True
if "YouTube Premium" not in df_plat["Nombre"].values:
    df_plat = pd.concat([df_plat, pd.DataFrame([{"Nombre": "YouTube Premium", "Usa_Boveda": "Si"}])], ignore_index=True)
    migr_plat = True
if migr_plat: save_df(df_plat, "Plataformas")
lista_plataformas = df_plat['Nombre'].tolist()

cols_usuarios = ["Usuario", "Password", "Rol", "Telefono", "Acceso_YT", "Datos_Pago", "P_Bienvenida", "P_Rec", "P_Ven", "Tema"]
df_usuarios = load_df("Usuarios", cols_usuarios)
migr_usr = False

TXT_B = "¡Hola {cliente}! 🎉 Aquí tienes tus accesos nuevos de {producto}.\n\n📧 Correo: {correo}\n🔑 Clave: {password}\n📅 Vence el: {vencimiento}\n\n¡Disfruta tu servicio!"
TXT_R = "Hola {cliente} ⏰, te recuerdo que tu cuenta de {producto} vencerá el {vencimiento}. ¿Deseas ir renovando para no perder el servicio?\n\n💳 Puedes renovar aquí:\n{pagos}"
TXT_V = "🚨 Hola {cliente}, tu cuenta de {producto} ha VENCIDO.\n\nPara reactivar tu servicio de inmediato, por favor envía la renovación a:\n{pagos}"

for col in cols_usuarios:
    if col not in df_usuarios.columns: 
        df_usuarios[col] = ""
        migr_usr = True

for idx, row in df_usuarios.iterrows():
    modificado = False
    if not str(row.get('P_Bienvenida')).strip() or str(row.get('P_Bienvenida')).strip() == 'nan': 
        df_usuarios.at[idx, 'P_Bienvenida'] = TXT_B; modificado = True
    if not str(row.get('P_Rec')).strip() or str(row.get('P_Rec')).strip() == 'nan': 
        df_usuarios.at[idx, 'P_Rec'] = TXT_R; modificado = True
    if not str(row.get('P_Ven')).strip() or str(row.get('P_Ven')).strip() == 'nan': 
        df_usuarios.at[idx, 'P_Ven'] = TXT_V; modificado = True
    
    dp_actual = str(row.get('Datos_Pago', '')).strip()
    if not dp_actual.startswith('['): 
        json_inicial = json.dumps([{"Id": 1, "Titular": "Admin", "Activo": True, "Metodo": "Yape", "Cuenta": NUMERO_ADMIN}])
        df_usuarios.at[idx, 'Datos_Pago'] = json_inicial
        modificado = True
        
    if modificado: migr_usr = True

if df_usuarios.empty:
    json_base = json.dumps([{"Id": 1, "Titular": "Admin", "Activo": True, "Metodo": "Yape", "Cuenta": NUMERO_ADMIN}])
    df_usuarios = pd.DataFrame([["admin", "admin123", "Admin", "", "Si", json_base, TXT_B, TXT_R, TXT_V, "Sistema"]], columns=cols_usuarios)
    migr_usr = True

if migr_usr: save_df(df_usuarios, "Usuarios")

df_auditoria = load_df("Auditoria", ["Fecha", "Usuario", "Accion", "Detalle"])

# ==============================================================================
# FUNCIONES DE APOYO Y EXCEL
# ==============================================================================
def registrar_auditoria(accion, detalle):
    global df_auditoria
    usr = st.session_state.user if 'user' in st.session_state else "Sistema"
    f = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo = pd.DataFrame([[f, usr, accion, detalle]], columns=["Fecha", "Usuario", "Accion", "Detalle"])
    df_auditoria = pd.concat([df_auditoria, nuevo], ignore_index=True)
    save_df(df_auditoria, "Auditoria")

def generar_password_aleatoria():
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))

def generar_usuario(nombre):
    base = re.sub(r'[^a-zA-Z0-9]', '', str(nombre).split()[0].lower())
    return f"{base}{random.randint(100, 999)}"

def limpiar_whatsapp(numero):
    solo_numeros = re.sub(r'\D', '', str(numero))
    if len(solo_numeros) == 9: return f"51{solo_numeros}"
    return solo_numeros

def formatear_mes_anio(yyyy_mm):
    MESES = {'01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic'}
    try: y, m = yyyy_mm.split('-'); return f"{MESES[m]} {y}"
    except: return yyyy_mm

def procesar_plantilla(tipo, row_venta, mi_perfil):
    try:
        lista_pagos = json.loads(mi_perfil.get('Datos_Pago', '[]'))
        pagos_activos = [f"✅ {p['Metodo']}: {p['Cuenta']} ({p['Titular']})" for p in lista_pagos if p.get('Activo', False)]
        str_pagos = "\n".join(pagos_activos) if pagos_activos else "Consultar medio de pago."
    except:
        str_pagos = "Consultar medio de pago."

    if tipo == "Bienvenida": base = mi_perfil.get('P_Bienvenida', TXT_B)
    elif tipo == "Recordatorio": base = mi_perfil.get('P_Rec', TXT_R)
    else: base = mi_perfil.get('P_Ven', TXT_V)
        
    msj = str(base).replace("{cliente}", str(row_venta['Cliente'])).replace("{producto}", str(row_venta['Producto']))\
              .replace("{vencimiento}", str(row_venta['Vencimiento'])).replace("{correo}", str(row_venta['Correo']))\
              .replace("{password}", str(row_venta['Pass'])).replace("{pagos}", str_pagos)
    return f"https://wa.me/{row_venta['WhatsApp']}?text={quote(msj)}"

def generar_backup_excel():
    output = io.BytesIO()
    df_v = df_ventas.astype(str)
    df_i = df_inv.astype(str)
    df_u = df_usuarios.astype(str)
    df_a = df_auditoria.astype(str)
    df_e = df_ex_clientes.astype(str)
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_v.to_excel(writer, sheet_name='Ventas', index=False)
        df_i.to_excel(writer, sheet_name='Inventario', index=False)
        df_u.to_excel(writer, sheet_name='Usuarios', index=False)
        df_a.to_excel(writer, sheet_name='Auditoria_Logs', index=False)
        df_e.to_excel(writer, sheet_name='Papelera', index=False)
    
    registrar_auditoria("Descarga Backup", "Admin descargó el Excel Total.")
    return output.getvalue()

# ==============================================================================
# BLOQUE 5: DIÁLOGOS DE GESTIÓN GLOBALES (Evitan el Error de Sintaxis)
# ==============================================================================
@st.dialog("⏰ Centro de Cobranza Urgente")
def mostrar_popup_alertas(df_urgente, hoy, perfil):
    global df_ventas, df_ex_clientes
    st.warning("⚠️ **ATENCIÓN:** Tienes clientes por vencer.")
    for idx, row in df_urgente.sort_values(by="Vencimiento").iterrows():
        dias = (row['Vencimiento'] - hoy).days
        if dias == 3: estado_txt, badge_col = "Vence en 3 días", "badge-orange"
        elif dias <= 0: estado_txt, badge_col = "VENCIDO", "badge-red"
        else: estado_txt, badge_col = f"Vence en {dias} días", "badge-orange"

        wa_url = procesar_plantilla("Vencido" if dias <= 0 else "Recordatorio", row, perfil)
        
        with st.container(border=True):
            st.markdown(f"""<div style="margin-bottom: 5px;"><h4 style="margin:0;">👤 {row['Cliente']}</h4></div>
            <div><span class="badge badge-default">📺 {row['Producto']}</span><span class="badge {badge_col}">⚠️ {estado_txt}</span></div>""", unsafe_allow_html=True)
            st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
            ca1, ca2 = st.columns(2)
            with ca1: st.link_button("📲 Avisar", wa_url, use_container_width=True)
            with ca2:
                if st.button("🗑️ Papelera", key=f"al_del_{idx}", use_container_width=True):
                    df_ex_clientes = pd.concat([df_ex_clientes, pd.DataFrame([row])], ignore_index=True)
                    df_ventas = df_ventas.drop(idx)
                    save_df(df_ex_clientes, "ExClientes"); save_df(df_ventas, "Ventas")
                    registrar_auditoria("Borrado", f"Envió a papelera cliente {row['Cliente']}")
                    st.rerun()
    if st.button("Entendido, cerrar", type="primary", use_container_width=True):
        st.session_state.alertas_vistas = True; st.rerun()

@st.dialog("🔄 Renovar")
def renovar_venta_popup(idx, row):
    global df_ventas, df_inv, df_plat
    st.write(f"Renovando a: **{row['Cliente']}**")
    dur = st.radio("Plazo:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    fecha_base = max(datetime.now().date(), pd.to_datetime(row['Vencimiento']).date()) 
    if dur == "1 Mes": nueva_fecha = fecha_base + timedelta(days=30)
    elif dur == "2 Meses": nueva_fecha = fecha_base + timedelta(days=60)
    elif dur == "6 Meses": nueva_fecha = fecha_base + timedelta(days=180)
    else: nueva_fecha = fecha_base + timedelta(days=365)
    
    tipo_cta = st.radio("Credenciales:", ["Mantener misma cuenta", "Asignar cuenta nueva"], horizontal=True)
    mv, pv = row['Correo'], row['Pass'] 
    usa_boveda = False
    if not df_plat.empty and row['Producto'] in df_plat['Nombre'].values:
        usa_boveda = df_plat.loc[df_plat['Nombre'] == row['Producto'], 'Usa_Boveda'].values[0] == "Si"
            
    if tipo_cta == "Asignar cuenta nueva":
        ca, cb = st.columns(2)
        if usa_boveda and ((st.session_state.role == "Admin") or (st.session_state.acceso_yt == "Si")):
            disp = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
            if not disp.empty:
                with ca: mv = st.text_input("Auto-Correo", value=disp.iloc[0]['Correo'])
                with cb: pv = st.text_input("Nueva Clave", value=disp.iloc[0]['Password'])
            else:
                with ca: mv = st.text_input("Correo Manual")
                with cb: pv = st.text_input("Nueva Clave")
        else:
            with ca: mv = st.text_input("Nuevo Correo")
            with cb: pv = st.text_input("Nueva Clave")
            
    if st.button("CONFIRMAR RENOVACIÓN", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Vencimiento'], df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'] = nueva_fecha, mv, pv
        save_df(df_ventas, "Ventas")
        
        if tipo_cta == "Asignar cuenta nueva" and usa_boveda:
            idx_inv = df_inv[df_inv['Correo'] == mv].index
            if not idx_inv.empty:
                df_inv.at[idx_inv[0], 'Usos'] = int(df_inv.at[idx_inv[0], 'Usos']) + 1
                asig_p = str(df_inv.at[idx_inv[0], 'Asignado_A'])
                df_inv.at[idx_inv[0], 'Asignado_A'] = row['Cliente'] if asig_p == "Nadie" else f"{asig_p} | {row['Cliente']}"
                df_inv.at[idx_inv[0], 'Last_Seller'] = st.session_state.user
            else:
                df_inv = pd.concat([df_inv, pd.DataFrame([[mv, pv, 1, row['Cliente'], st.session_state.user, ""]], columns=df_inv.columns)], ignore_index=True)
            save_df(df_inv, "Inventario")
            
        registrar_auditoria("Renovación", f"Renovó cliente {row['Cliente']}")
        st.session_state.toast_msg = "🔄 ¡Renovación exitosa!"; st.rerun()

@st.dialog("📝 Editar Cliente")
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
    notas = st.text_area("Notas Secretas", value=row.get('Notas', ''))
    if st.button("ACTUALIZAR", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Cliente'], df_ventas.at[idx, 'WhatsApp'], df_ventas.at[idx, 'Producto'], df_ventas.at[idx, 'Vencimiento'] = nom, limpiar_whatsapp(tel), prod, venc
        df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'], df_ventas.at[idx, 'Perfil'], df_ventas.at[idx, 'Costo'], df_ventas.at[idx, 'Precio'] = m, p, perf, costo, precio
        df_ventas.at[idx, 'Notas'] = notas
        save_df(df_ventas, "Ventas")
        registrar_auditoria("Edición", f"Editó datos de {nom}")
        st.session_state.toast_msg = "💾 Cambios guardados."; st.rerun()

@st.dialog("➕ Nueva Venta")
def nueva_venta_popup():
    global df_ventas, df_inv, df_plat
    c1, c2 = st.columns(2)
    with c1: prod = st.selectbox("Plataforma", lista_plataformas)
    with c2: f_ini = st.date_input("Inicio", datetime.now())
    nom = st.text_input("Cliente", placeholder="Ej: Maria Lopez")
    tel = st.text_input("WhatsApp", placeholder="Ej: 999888777")
    
    c_costo, c_precio = st.columns(2)
    costo = c_costo.number_input("Costo (Pagas)", value=0.0, step=1.0)
    precio = c_precio.number_input("Precio Venta", value=0.0, step=1.0)
    dur = st.radio("Plazo:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    if dur == "1 Mes": venc = f_ini + timedelta(days=30)
    elif dur == "2 Meses": venc = f_ini + timedelta(days=60)
    elif dur == "6 Meses": venc = f_ini + timedelta(days=180)
    else: venc = f_ini + timedelta(days=365)
    
    st.divider()
    ca, cb = st.columns(2)
    usa_boveda = False
    if not df_plat.empty and prod in df_plat['Nombre'].values:
        usa_boveda = df_plat.loc[df_plat['Nombre'] == prod, 'Usa_Boveda'].values[0] == "Si"
    
    pv = ""
    if usa_boveda and ((st.session_state.role == "Admin") or (st.session_state.acceso_yt == "Si")):
        disp = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
        if not disp.empty:
            with ca: mv = st.text_input("Correo Auto", value=disp.iloc[0]['Correo'])
            with cb: pv = st.text_input("Clave", value=disp.iloc[0]['Password'])
        else: 
            with ca: mv = st.text_input("Correo Manual (Bóveda vacía)")
            with cb: pv_in = st.text_input("Clave Manual", placeholder="Deja vacío para auto-generar")
    else: 
        with ca: mv = st.text_input("Correo")
        with cb: pv_in = st.text_input("Clave", placeholder="Deja vacío para auto-generar")
        pv = pv_in

    notas = st.text_area("📝 Notas (Visible solo para ti)")
    
    if st.button("🚀 REGISTRAR VENTA", type="primary", use_container_width=True):
        if not pv and not usa_boveda: pv = generar_password_aleatoria()
        nueva = pd.DataFrame([[ "🟢", nom, limpiar_whatsapp(tel), prod, mv, pv, "nan", "nan", venc, st.session_state.user, costo, precio, notas ]], columns=df_ventas.columns)
        df_ventas = pd.concat([df_ventas, nueva], ignore_index=True)
        save_df(df_ventas, "Ventas")
        
        if usa_boveda:
            idx_inv = df_inv[df_inv['Correo'] == mv].index
            if not idx_inv.empty:
                df_inv.at[idx_inv[0], 'Usos'] = int(df_inv.at[idx_inv[0], 'Usos']) + 1
                asig_p = str(df_inv.at[idx_inv[0], 'Asignado_A'])
                df_inv.at[idx_inv[0], 'Asignado_A'] = nom if asig_p == "Nadie" else f"{asig_p} | {nom}"
                df_inv.at[idx_inv[0], 'Last_Seller'] = st.session_state.user
            else:
                df_inv = pd.concat([df_inv, pd.DataFrame([[mv, pv, 1, nom, st.session_state.user, ""]], columns=df_inv.columns)], ignore_index=True)
            save_df(df_inv, "Inventario")

        registrar_auditoria("Venta Nueva", f"Creó venta de {prod} para {nom}")
        st.session_state.toast_msg = "🎉 ¡Venta registrada!"; st.rerun()

@st.dialog("Modificar Cuenta de Bóveda")
def editar_boveda_popup(idx, row):
    global df_inv
    nP = st.text_input("Nueva Clave", value=row['Password'])
    nU = st.selectbox("Usos (Cupos Ocupados)", [0,1,2], index=int(row['Usos']))
    nA = st.text_input("Clientes Asignados", value=row['Asignado_A'])
    if st.button("Actualizar Bóveda", type="primary", use_container_width=True):
        df_inv.at[idx, 'Password'] = nP
        df_inv.at[idx, 'Usos'] = nU
        df_inv.at[idx, 'Asignado_A'] = nA
        save_df(df_inv, "Inventario")
        registrar_auditoria("Edición Bóveda", f"Editó usos de {row['Correo']}")
        st.rerun()

@st.dialog("Editar Vendedor")
def editar_vendedor_popup(idx, row):
    global df_usuarios
    st.write(f"Editando a: **{row['Usuario']}**")
    n_tel = st.text_input("Teléfono", value=row['Telefono'])
    n_pwd = st.text_input("Nueva Contraseña", value=row['Password'])
    n_acc = st.checkbox("✅ Acceso a Bóveda Auto", value=(row['Acceso_YT'] == 'Si'))
    if st.button("Actualizar Permisos", type="primary", use_container_width=True):
        df_usuarios.at[idx, 'Telefono'] = n_tel
        df_usuarios.at[idx, 'Password'] = n_pwd
        df_usuarios.at[idx, 'Acceso_YT'] = "Si" if n_acc else "No"
        save_df(df_usuarios, "Usuarios")
        st.session_state.toast_msg = "✅ Perfil actualizado."
        st.rerun()

@st.dialog("➕ Nuevo Medio de Pago")
def nuevo_pago_popup(mis_pagos_actuales):
    global df_usuarios
    t_p = st.selectbox("Plataforma Bancaria", ["Yape", "Plin", "BCP", "BBVA", "Interbank", "Agora", "Transferencia", "Otro"])
    
    metodo_final = t_p
    if t_p == "Otro":
        metodo_final = st.text_input("Escribe el nombre del Banco/App", placeholder="Ej: PayPal, Zelle...")
        
    n_t = st.text_input("Nombre de Persona Titular", placeholder="Ej: Juan Perez")
    n_c = st.text_input("Número (Celular o Cuenta Larga)", placeholder="Ej: 191-00000000000")
    
    if st.button("Guardar Método", type="primary", use_container_width=True):
        if metodo_final and n_c:
            nv_obj = {"Id": len(mis_pagos_actuales) + 1, "Titular": n_t, "Activo": True, "Metodo": metodo_final, "Cuenta": n_c}
            mis_pagos_actuales.append(nv_obj)
            idx_usr = df_usuarios[df_usuarios['Usuario'] == st.session_state.user].index[0]
            df_usuarios.at[idx_usr, 'Datos_Pago'] = json.dumps(mis_pagos_actuales)
            save_df(df_usuarios, "Usuarios")
            st.rerun()
        else:
            st.warning("Completa el nombre del método y el número.")

# ==============================================================================
# BLOQUE 4: SISTEMA DE LOGIN Y MENU PÍLDORA
# ==============================================================================
cookies = CookieController()
usuario_guardado = cookies.get('nexa_user_cookie')

if not st.session_state.logged_in and usuario_guardado:
    match = df_usuarios[df_usuarios['Usuario'] == usuario_guardado]
    if not match.empty:
        st.session_state.logged_in = True
        st.session_state.user = match.iloc[0]['Usuario']
        st.session_state.role = match.iloc[0]['Rol']
        st.session_state.acceso_yt = match.iloc[0]['Acceso_YT']

if not st.session_state.logged_in:
    st.markdown("""<div style="text-align: center; margin-top: 50px;">
        <h1 style="color: #00D26A; font-size: 50px; margin-bottom:0;">🚀 NEXA</h1>
        <h3 style="margin-top:0; color:var(--text-color); letter-spacing: 4px;">STREAM</h3>
    </div>""", unsafe_allow_html=True)
    c_log1, c_log2, c_log3 = st.columns([1,2,1])
    with c_log2:
        with st.container(border=True):
            with st.form("login_form"):
                u_in = st.text_input("Usuario")
                p_in = st.text_input("Contraseña", type="password")
                ingresar = st.form_submit_button("Acceder", type="primary", use_container_width=True)
                if ingresar:
                    match = df_usuarios[(df_usuarios['Usuario'] == u_in) & (df_usuarios['Password'] == p_in)]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user = match.iloc[0]['Usuario']; st.session_state.role = match.iloc[0]['Rol']
                        cookies.set('nexa_user_cookie', u_in); registrar_auditoria("Login", "Ingresó"); st.rerun()
                    else: st.error("❌ Credenciales incorrectas.")
    st.stop()

mi_perfil = df_usuarios[df_usuarios['Usuario'] == st.session_state.user].iloc[0]

cupos_libres = len(df_inv[df_inv['Usos'] < 2]) if not df_inv.empty else 0
color_salud = "#00D26A" if cupos_libres > 2 else ("#FF9800" if cupos_libres > 0 else "#F44336")

st.markdown(f"""<div style="display:flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(128,128,128,0.2);">
    <div style="display: flex; align-items: center;">
        <div style="width: 10px; height: 10px; background-color: {color_salud}; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px {color_salud};"></div>
        <h2 style="color:#00D26A; margin:0;">🚀 NEXA<span style="color:var(--text-color); font-size: 18px;">-Stream</span></h2>
    </div>
    <div style="text-align:right; font-size: 12px; opacity: 0.8;">👤 <b>{st.session_state.user}</b> <br> {st.session_state.role}</div>
</div>""", unsafe_allow_html=True)

opciones_menu = ["Ventas", "Métricas", "Bóveda", "Equipo", "Auditoría", "Mi Perfil"] if st.session_state.role == "Admin" else ["Ventas", "Métricas", "Papelera", "Mi Perfil"]
iconos_menu = ["cart-check-fill", "bar-chart-fill", "safe", "people-fill", "eye-fill", "person-badge-fill"] if st.session_state.role == "Admin" else ["cart-check-fill", "bar-chart-fill", "trash3-fill", "person-badge-fill"]

menu = option_menu(menu_title=None, options=opciones_menu, icons=iconos_menu, default_index=0, orientation="horizontal", styles={"container": {"background-color": "rgba(128,128,128,0.1)", "border-radius": "50px"}, "nav-link-selected": {"background-color": "#00D26A"}})

# ==============================================================================
# VISTAS PRINCIPALES V4.5
# ==============================================================================
if menu == "Ventas":
    if st.session_state.role == "Admin":
        tipo_filtro = st.selectbox("👥 Filtro Vendedores:", ["🌎 Todos", "👥 Equipo", "👑 Mi Cuenta"], label_visibility="collapsed")
        if tipo_filtro == "🌎 Todos": df_mostrar = df_ventas
        elif tipo_filtro == "👥 Equipo": df_mostrar = df_ventas[df_ventas['Vendedor'] != st.session_state.user]
        else: df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]
    else: df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]

    hoy = datetime.now().date()
    if not df_mostrar.empty:
        df_urgente = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy + timedelta(days=3)]
        if not st.session_state.alertas_vistas and not df_urgente.empty:
            mostrar_popup_alertas(df_urgente, hoy, mi_perfil)
        
    c1, c2 = st.columns([3, 1])
    with c1: 
        if st.button("➕ NUEVA VENTA", type="primary", use_container_width=True): nueva_venta_popup()
    with c2: 
        if st.button("🔔", use_container_width=True): st.session_state.alertas_vistas = False; st.rerun()
            
    with st.expander("🔍 Buscador y Filtros", expanded=False):
        filtro_est = st.radio("Estado:", ["Todas", "Activas", "Por Vencer", "Vencidas"], horizontal=True)
        cf1, cf2 = st.columns(2)
        search = cf1.text_input("Buscar Cliente:")
        filtro_plat = cf2.selectbox("Plataforma:", ["Todas"] + lista_plataformas)

    if search: df_mostrar = df_mostrar[df_mostrar.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    if filtro_plat != "Todas": df_mostrar = df_mostrar[df_mostrar['Producto'] == filtro_plat]
    if filtro_est != "Todas":
        if filtro_est == "Activas": df_mostrar = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date > hoy + timedelta(days=3)]
        elif filtro_est == "Por Vencer": df_mostrar = df_mostrar[(pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy + timedelta(days=3)) & (pd.to_datetime(df_mostrar['Vencimiento']).dt.date > hoy)]
        elif filtro_est == "Vencidas": df_mostrar = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy]

    st.write("---")

    ITEMS_POR_PAGINA = 50
    total_items = len(df_mostrar)
    if total_items > 0:
        df_mostrar = df_mostrar.sort_values(by="Vencimiento")
        total_paginas = (total_items - 1) // ITEMS_POR_PAGINA + 1
        if 'pagina_actual' not in st.session_state: st.session_state.pagina_actual = 1
        if st.session_state.pagina_actual > total_paginas: st.session_state.pagina_actual = total_paginas
        
        inicio_idx = (st.session_state.pagina_actual - 1) * ITEMS_POR_PAGINA
        df_pagina = df_mostrar.iloc[inicio_idx : inicio_idx + ITEMS_POR_PAGINA]
        
        st.caption(f"Mostrando {inicio_idx + 1} a {min(inicio_idx + ITEMS_POR_PAGINA, total_items)} de {total_items} clientes.")

        for idx, row in df_pagina.iterrows():
            d = (row['Vencimiento'] - hoy).days
            if d <= 0: est_emj, estado_txt, badge_col = "🔴", "Vencido", "badge-red"
            elif d <= 3: est_emj, estado_txt, badge_col = "🟠", f"Vence en {d} d.", "badge-orange"
            else: est_emj, estado_txt, badge_col = "🟢", "Activo", "badge-green"
                
            prod_b = "badge-youtube" if "YouTube" in row['Producto'] else "badge-netflix" if "Netflix" in row['Producto'] else "badge-spotify" if "Spotify" in row['Producto'] else "badge-default"
            
            url_cobro = procesar_plantilla("Vencido" if d <= 0 else "Recordatorio", row, mi_perfil)
            url_bienvenida = procesar_plantilla("Bienvenida", row, mi_perfil)
            
            titulo = f"{est_emj} {row['Cliente']} | 📺 {row['Producto']}"
            
            with st.expander(titulo):
                v_badge = f" • 🧑‍🚀 {row['Vendedor']}" if st.session_state.role == "Admin" else ""
                st.markdown(f"<div><span class='badge {prod_b}'>{row['Producto']}</span><span class='badge {badge_col}'>{estado_txt}</span></div>", unsafe_allow_html=True)
                st.write(f"📧 **{row['Correo']}** | 🔑 **{row['Pass']}**")
                st.caption(f"📅 Vence: {row['Vencimiento']} {v_badge}")
                if row.get('Notas'): st.info(f"📝 {row['Notas']}")
                
                st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                cols = st.columns(4)
                with cols[0]: st.link_button("📲 Cobrar", url_cobro, use_container_width=True)
                with cols[1]: st.link_button("📨 Accesos", url_bienvenida, use_container_width=True)
                with cols[2]: 
                    if st.button("🔄 Renovar", key=f"r_{idx}", use_container_width=True): renovar_venta_popup(idx, row)
                with cols[3]: 
                    if st.button("📝 Editar", key=f"e_{idx}", use_container_width=True): editar_venta_popup(idx, row)
                if st.button("🗑️ Enviar a Papelera", key=f"v_{idx}", use_container_width=True):
                    df_ex_clientes = pd.concat([df_ex_clientes, pd.DataFrame([row])], ignore_index=True)
                    df_ventas = df_ventas.drop(idx)
                    save_df(df_ex_clientes, "ExClientes"); save_df(df_ventas, "Ventas")
                    registrar_auditoria("Borrado", f"Envió a papelera a {row['Cliente']}")
                    st.rerun()
                    
        st.write("")
        cp1, cp2, cp3 = st.columns([1, 2, 1])
        with cp1:
            if st.button("⬅️ Anterior", disabled=(st.session_state.pagina_actual == 1), use_container_width=True):
                st.session_state.pagina_actual -= 1; st.rerun()
        with cp2: st.markdown(f"<div style='text-align:center; padding-top:10px;'>Página {st.session_state.pagina_actual} de {total_paginas}</div>", unsafe_allow_html=True)
        with cp3:
            if st.button("Siguiente ➡️", disabled=(st.session_state.pagina_actual == total_paginas), use_container_width=True):
                st.session_state.pagina_actual += 1; st.rerun()
    else: 
        st.info("No se encontraron clientes.")

elif menu == "Métricas":
    if st.session_state.role == "Admin": 
        tipo_filtro_dash = st.selectbox("Filtro Vendedores:", ["🌎 Todos", "👥 Equipo", "👑 Mi Cuenta"], label_visibility="collapsed")
        df_dash_base = df_ventas.copy() if tipo_filtro_dash == "🌎 Todos" else df_ventas[df_ventas['Vendedor'] != st.session_state.user].copy() if tipo_filtro_dash == "👥 Equipo" else df_ventas[df_ventas['Vendedor'] == st.session_state.user].copy()
    else: df_dash_base = df_ventas[df_ventas['Vendedor'] == st.session_state.user].copy()
        
    if df_dash_base.empty: st.warning("No hay suficientes datos.")
    else:
        df_dash_base['Vencimiento_dt'] = pd.to_datetime(df_dash_base['Vencimiento'], errors='coerce')
        df_dash_base['Periodo'] = df_dash_base['Vencimiento_dt'].dt.strftime('%Y-%m')
        periodos_disponibles = ["Histórico Global"] + sorted(df_dash_base['Periodo'].dropna().unique().tolist(), reverse=True)
        
        c_per, c_desc = st.columns([3, 1])
        with c_per: periodo_sel = st.selectbox("📅 Periodo:", periodos_disponibles, format_func=lambda x: x if x == "Histórico Global" else formatear_mes_anio(x), label_visibility="collapsed")
        df_dash = df_dash_base if periodo_sel == "Histórico Global" else df_dash_base[df_dash_base['Periodo'] == periodo_sel]
        
        with c_desc:
            st.download_button("📥 Descargar", data=df_dash.to_csv(index=False).encode('utf-8'), file_name='reporte.csv', mime='text/csv', use_container_width=True)
            
        st.write("---")
        if df_dash.empty: st.info("Sin ventas en este periodo.")
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
            with col1: st.markdown(f'<div class="kpi-card kpi-blue"><div class="kpi-title">👥 Activos</div><p class="kpi-value">{total_clientes}</p></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="kpi-card kpi-green"><div class="kpi-title">💰 Ganancia Neta</div><p class="kpi-value">S/ {total_ganancia:.2f}</p></div>', unsafe_allow_html=True)
            
            st.write("---")
            st.subheader("📊 Gráficos")
            cg1, cg2 = st.columns(2)
            with cg1:
                ventas_plat = df_dash['Producto'].value_counts().reset_index()
                ventas_plat.columns = ['Plataforma', 'Cant']
                st.altair_chart(alt.Chart(ventas_plat).mark_arc(innerRadius=50).encode(theta='Cant', color='Plataforma', tooltip=['Plataforma', 'Cant']).properties(height=250), use_container_width=True)
            with cg2:
                hist = df_dash_base.groupby('Periodo')['Precio'].sum().reset_index()
                st.altair_chart(alt.Chart(hist).mark_bar(color='#00D26A').encode(x='Periodo', y='Precio', tooltip=['Periodo', 'Precio']).properties(height=250), use_container_width=True)

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
                    st.rerun()

# BÓVEDA EN FORMATO PASTILLA (Imagen 12 Solucionada)
elif menu == "Bóveda" or menu == "Inventario":
    registrar_auditoria("Vista Bóveda", "Abrió la Bóveda de Cuentas.")
    st.header("🤖 Bóveda Inteligente")
    
    with st.expander("➕ AÑADIR CUENTAS A LA BÓVEDA", expanded=False):
        c_auto, c_man = st.tabs(["⚡ Generar Lote (IA)", "✏️ Manual"])
        with c_auto:
            if st.button("🔄 Generar 10 Correos", use_container_width=True):
                st.session_state.temp_emails = generar_lote_correos(10); st.rerun()
            if st.session_state.temp_emails:
                for i, acc in enumerate(st.session_state.temp_emails):
                    st.write(f"👤 {acc['Nombre']} | {acc['Correo']}")
                if st.button("✅ Guardar Lote", type="primary", use_container_width=True):
                    nuevos_df = pd.DataFrame([[acc['Correo'], acc['Pass'], 0, "Nadie", "Nadie", ""] for acc in st.session_state.temp_emails], columns=df_inv.columns)
                    df_inv = pd.concat([df_inv, nuevos_df], ignore_index=True); save_df(df_inv, "Inventario")
                    registrar_auditoria("Inventario", "Añadió lote IA a Bóveda")
                    st.session_state.temp_emails = []; st.rerun()
        with c_man:
            with st.form("add_manual_inv"):
                m = st.text_input("Correo Gmail")
                p = st.text_input("Contraseña")
                u = st.selectbox("Usos Actuales (0 = Nueva)", [0,1,2])
                if st.form_submit_button("Guardar en Bóveda", type="primary", use_container_width=True):
                    df_inv = pd.concat([df_inv, pd.DataFrame([[m, p, u, "Nadie", st.session_state.user, ""]], columns=df_inv.columns)], ignore_index=True)
                    save_df(df_inv, "Inventario")
                    registrar_auditoria("Inventario", "Añadió correo manual a Bóveda")
                    st.rerun()
                
    st.write("---")
    
    if df_inv.empty: 
        st.info("La bóveda está completamente vacía.")
    else:
        ITEMS_INV = 25
        t_inv = len(df_inv)
        t_pag_inv = (t_inv - 1) // ITEMS_INV + 1
        if 'pagina_inv' not in st.session_state: st.session_state.pagina_inv = 1
        
        df_mostrar_inv = df_inv.iloc[(st.session_state.pagina_inv - 1) * ITEMS_INV : st.session_state.pagina_inv * ITEMS_INV]
        
        for idx, row in df_mostrar_inv.iterrows():
            usos_restantes = 2 - int(pd.to_numeric(row['Usos'], errors='coerce'))
            badge_color = "badge-green" if usos_restantes > 0 else "badge-red"
            texto_badge = f"{usos_restantes} Cupos Libres" if usos_restantes > 0 else "LLENA"
            
            titulo_pastilla = f"📧 {row['Correo']} | 📊 Usos: {row['Usos']}"
            
            # Formato de Pastilla Desplegable
            with st.expander(titulo_pastilla):
                c_inf1, c_inf2 = st.columns(2)
                with c_inf1:
                    st.write(f"🔑 Contraseña: **{row['Password']}**")
                    st.caption(f"👥 Clientes: {row['Asignado_A']}")
                with c_inf2:
                    st.markdown(f"Status: <span class='badge {badge_color}'>{texto_badge}</span>", unsafe_allow_html=True)
                    st.caption(f"🧑‍🚀 Último Vendedor: {row['Last_Seller']}")
                
                st.markdown("---")
                cb1, cb2 = st.columns(2)
                with cb1:
                    if st.button("📝 Editar", key=f"ei_{idx}", use_container_width=True): 
                        editar_boveda_popup(idx, row)
                with cb2:
                    if st.button("🗑️ Eliminar", key=f"di_{idx}", use_container_width=True):
                        df_inv = df_inv.drop(idx); save_df(df_inv, "Inventario"); st.rerun()
        
        st.write("")
        c_p1, c_p2, c_p3 = st.columns([1, 2, 1])
        with c_p1:
            if st.button("⬅️ Ant.", disabled=(st.session_state.pagina_inv == 1), use_container_width=True): st.session_state.pagina_inv -= 1; st.rerun()
        with c_p2: st.markdown(f"<div style='text-align:center;'>Pág. {st.session_state.pagina_inv} de {t_pag_inv}</div>", unsafe_allow_html=True)
        with c_p3:
            if st.button("Sig. ➡️", disabled=(st.session_state.pagina_inv == t_pag_inv), use_container_width=True): st.session_state.pagina_inv += 1; st.rerun()

elif menu == "Equipo":
    with st.expander("➕ INTEGRAR VENDEDOR", expanded=False):
        with st.form("form_crear_vend"):
            nuevo_nom = st.text_input("Nombre de Pila")
            nuevo_tel = st.text_input("WhatsApp")
            dar_acceso_yt = st.checkbox("Dar acceso a la Bóveda Automática")
            if st.form_submit_button("Crear Perfil", type="primary", use_container_width=True):
                usr_generado = generar_usuario(nuevo_nom); pwd_generada = generar_password_aleatoria()
                json_base = json.dumps([{"Id": 1, "Titular": nuevo_nom, "Activo": True, "Metodo": "Yape", "Cuenta": limpiar_whatsapp(nuevo_tel)}])
                nu_df = pd.DataFrame([[usr_generado, pwd_generada, "Vendedor", limpiar_whatsapp(nuevo_tel), "Si" if dar_acceso_yt else "No", json_base, TXT_B, TXT_R, TXT_V, "Sistema"]], columns=df_usuarios.columns)
                df_usuarios = pd.concat([df_usuarios, nu_df], ignore_index=True); save_df(df_usuarios, "Usuarios")
                registrar_auditoria("Equipo", f"Creó vendedor {usr_generado}")
                st.success(f"✅ Usuario: {usr_generado} | Clave: {pwd_generada}")
    
    st.write("---")
    vendedores = df_usuarios[df_usuarios['Rol'] != 'Admin']
    for idx, row in vendedores.iterrows():
        with st.container(border=True):
            st.write(f"🧑‍🚀 **{row['Usuario']}** | 📱 {row['Telefono']}")
            st.caption(f"🔑 Clave: {row['Password']} | 📺 Bóveda: **{row['Acceso_YT']}**")
            c_edit, c_del = st.columns(2)
            with c_edit:
                if st.button("📝 Ajustes", key=f"eu_{idx}", use_container_width=True): 
                    editar_vendedor_popup(idx, row)
            with c_del:
                if st.button("🗑️ Despedir", key=f"du_{idx}", use_container_width=True):
                    df_usuarios = df_usuarios.drop(idx); save_df(df_usuarios, "Usuarios"); st.rerun()

elif menu == "Auditoría":
    registrar_auditoria("Vista Auditoría", "Revisó los Logs.")
    st.header("👁️ Ojo de Dios (Logs)")
    st.info("Todo movimiento queda registrado aquí.")
    
    if not df_auditoria.empty:
        df_auditoria['Fecha_dt'] = pd.to_datetime(df_auditoria['Fecha'])
        df_auditoria = df_auditoria.sort_values(by="Fecha_dt", ascending=False)
        
        c_p1, c_p2 = st.columns([3, 1])
        with c_p2:
            if st.button("🗑️ Purgar Historial", type="primary", use_container_width=True):
                df_auditoria = pd.DataFrame(columns=["Fecha", "Usuario", "Accion", "Detalle"])
                save_df(df_auditoria, "Auditoria")
                st.session_state.toast_msg = "Historial borrado."; st.rerun()
                
        for idx, row in df_auditoria.head(100).iterrows():
            st.markdown(f"<div style='border-bottom: 1px solid rgba(128,128,128,0.2); padding: 5px 0;'><b>{row['Usuario']}</b> ({row['Accion']}) - <span style='color:#aaa; font-size:12px;'>{row['Fecha']}</span><br><span style='font-size:14px;'>{row['Detalle']}</span></div>", unsafe_allow_html=True)
    else: st.write("Historial limpio.")

    st.divider()
    st.header("🛡️ Botón de Pánico")
    st.caption("Descarga una copia completa de toda la información en un formato Excel limpio.")
    
    # LA DESCARGA EN EXCEL QUE REPARA EL ERROR JSON (Imagen 9)
    excel_panico = generar_backup_excel()
    st.download_button(
        label="📥 DESCARGAR EXCEL TOTAL (Backup)",
        data=excel_panico,
        file_name=f"Backup_NEXA_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

elif menu == "Mi Perfil":
    st.header("⚙️ Ajustes Personales")
    
    with st.expander("💳 MIS MEDIOS DE PAGO", expanded=True):
        st.info("Marca con ✔️ los que quieras usar. Puedes eliminar o añadir nuevos.")
        
        try: mis_pagos = json.loads(mi_perfil.get('Datos_Pago', '[]'))
        except: mis_pagos = []
        
        if mis_pagos:
            for i, p in enumerate(mis_pagos):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 4, 1], vertical_alignment="center")
                    
                    with c1:
                        new_act = st.checkbox("Activo", value=p.get('Activo', True), key=f"act_p_{i}")
                        if new_act != p.get('Activo', True):
                            mis_pagos[i]['Activo'] = new_act
                            idx_usr = df_usuarios[df_usuarios['Usuario'] == st.session_state.user].index[0]
                            df_usuarios.at[idx_usr, 'Datos_Pago'] = json.dumps(mis_pagos)
                            save_df(df_usuarios, "Usuarios")
                            st.rerun()
                    with c2:
                        st.write(f"**{p['Metodo']}** - {p['Cuenta']}")
                        st.caption(f"A nombre de: {p.get('Titular', '')}")
                    with c3:
                        if st.button("🗑️", key=f"del_p_{i}"):
                            del mis_pagos[i]
                            idx_usr = df_usuarios[df_usuarios['Usuario'] == st.session_state.user].index[0]
                            df_usuarios.at[idx_usr, 'Datos_Pago'] = json.dumps(mis_pagos)
                            save_df(df_usuarios, "Usuarios")
                            st.rerun()
        else: st.caption("No tienes métodos de pago configurados.")

        st.write("")
        # BOTÓN CENTRADO Y PEQUEÑO (Resuelve Imagen 10)
        col_btn_spacer1, col_btn_main, col_btn_spacer2 = st.columns([1, 2, 1])
        with col_btn_main:
            if st.button("➕ Añadir Medio de Pago", type="primary", use_container_width=True):
                nuevo_pago_popup(mis_pagos)

    st.divider()
    with st.form("form_perfil"):
        st.subheader("💬 Mis Mensajes Auto-Generados")
        st.caption("Variables que puedes usar: `{cliente}`, `{producto}`, `{vencimiento}`, `{correo}`, `{password}`, `{pagos}`")
        pb = st.text_area("📨 Bienvenida / Accesos Nuevos", value=mi_perfil.get('P_Bienvenida', ''), height=150)
        pr = st.text_area("🟠 Recordatorio", value=mi_perfil.get('P_Rec', ''), height=150)
        pv = st.text_area("🔴 Cuenta Vencida", value=mi_perfil.get('P_Ven', ''), height=150)
        
        if st.form_submit_button("💾 Guardar Mensajes", type="primary", use_container_width=True):
            idx_usr = df_usuarios[df_usuarios['Usuario'] == st.session_state.user].index[0]
            df_usuarios.at[idx_usr, 'P_Bienvenida'] = pb
            df_usuarios.at[idx_usr, 'P_Rec'] = pr
            df_usuarios.at[idx_usr, 'P_Ven'] = pv
            save_df(df_usuarios, "Usuarios")
            st.session_state.toast_msg = "✅ Mensajes guardados."
            st.rerun()
            
    if st.session_state.role == "Admin":
        st.divider()
        st.subheader("🛠 Catálogo de Plataformas")
        with st.container(border=True):
            c_plat1, c_plat2, c_pbtn = st.columns([2, 1, 1], vertical_alignment="bottom")
            with c_plat1: nueva_p = st.text_input("Nueva Plataforma", label_visibility="collapsed")
            with c_plat2: usa_b = st.checkbox("Usa Bóveda")
            with c_pbtn:
                if st.button("➕ Añadir", use_container_width=True):
                    if nueva_p and nueva_p not in df_plat['Nombre'].tolist():
                        df_plat = pd.concat([df_plat, pd.DataFrame([{"Nombre": nueva_p, "Usa_Boveda": "Si" if usa_b else "No"}])], ignore_index=True)
                        save_df(df_plat, "Plataformas"); st.rerun()
        for idx, row in df_plat.iterrows():
            cp1, cp2, cp3 = st.columns([2, 1, 1], vertical_alignment="center")
            cp1.write(f"📺 {row['Nombre']}")
            cp2.caption("🤖 Bóveda" if row.get('Usa_Boveda', 'No') == "Si" else "✍️ Manual")
            if cp3.button("🗑️", key=f"del_p_{row['Nombre']}", use_container_width=True):
                df_plat = df_plat.drop(idx); save_df(df_plat, "Plataformas"); st.rerun()
