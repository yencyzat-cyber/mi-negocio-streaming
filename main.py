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

# ==============================================================================
# BLOQUE 1: CONFIGURACIÓN Y VERSIÓN
# ==============================================================================
VERSION_APP = "1.13 (Botones Descriptivos y Diseño Nativo)"

LINK_APP = "https://mi-negocio-streaming-chkfid6tmyepuartagxlrq.streamlit.app/" 

st.set_page_config(page_title="NEXA-Stream Manager", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# BLOQUE 2: CSS MÓVIL Y ESTILOS
# ==============================================================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    /* Diseño limpio y responsivo para los botones con texto */
    .stButton>button, .stLinkButton>a {
        border-radius: 8px !important; height: 38px !important; padding: 0px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        width: 100% !important; font-size: 15px !important; margin-bottom: 5px !important;
    }
    .stLinkButton>a { background-color: #25D366 !important; color: white !important; border: none !important; font-weight: bold !important; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div { border-radius: 8px; height: 38px; }
    div[data-testid="metric-container"] { background-color: #1e1e1e; border: 1px solid #333; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# BLOQUE 3: FUNCIONES DE DATOS, SEGURIDAD Y PLANTILLAS
# ==============================================================================
VENTAS_FILE = "ventas_data.csv"
INV_FILE = "inventario_yt.csv"
PLAT_FILE = "plataformas.csv"
USUARIOS_FILE = "usuarios.csv"
EX_CLIENTES_FILE = "ex_clientes.csv"
WA_TEMPLATES_FILE = "wa_templates.json"

DEFAULT_TEMPLATES = {
    "recordatorio": "Hola {cliente}, te recordamos que tu cuenta de {producto} vencerá el {vencimiento}. ¿Deseas ir renovando para no perder el servicio?",
    "vencido": "🚨 Hola {cliente}, tu cuenta de {producto} ha VENCIDO el {vencimiento}. Por favor comunícate con nosotros para reactivar tu servicio.",
    "vendedor": "Hola {nombre}, bienvenido al equipo. Aquí tienes tu acceso al sistema NEXA-Stream.\n\n👤 Usuario: {usuario}\n🔑 Contraseña: {password}\n🌐 Link de acceso: {link}"
}

def load_templates():
    if os.path.exists(WA_TEMPLATES_FILE):
        try:
            with open(WA_TEMPLATES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return DEFAULT_TEMPLATES
    return DEFAULT_TEMPLATES

def save_templates(templates_dict):
    with open(WA_TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates_dict, f, ensure_ascii=False, indent=4)

def generar_password_aleatoria(longitud=6):
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for i in range(longitud))

def generar_usuario(nombre):
    base = re.sub(r'[^a-zA-Z0-9]', '', str(nombre).split()[0].lower())
    return f"{base}{random.randint(100, 999)}"

def cargar_datos():
    if os.path.exists(VENTAS_FILE):
        df = pd.read_csv(VENTAS_FILE)
        df['Vencimiento'] = pd.to_datetime(df['Vencimiento'], errors='coerce').dt.date
        cambios = False
        if 'Vendedor' not in df.columns: df['Vendedor'] = 'admin'; cambios = True
        if 'Costo' not in df.columns: df['Costo'] = 0.0; cambios = True
        if 'Precio' not in df.columns: df['Precio'] = 0.0; cambios = True
        if cambios: df.to_csv(VENTAS_FILE, index=False)
    else:
        df = pd.DataFrame(columns=["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento", "Vendedor", "Costo", "Precio"])
    
    if os.path.exists(EX_CLIENTES_FILE): df_ex = pd.read_csv(EX_CLIENTES_FILE)
    else: df_ex = pd.DataFrame(columns=df.columns)

    if os.path.exists(INV_FILE): inv = pd.read_csv(INV_FILE)
    else: inv = pd.DataFrame(columns=["Correo", "Password", "Usos", "Asignado_A"])
        
    if os.path.exists(PLAT_FILE): plat = pd.read_csv(PLAT_FILE)['Nombre'].tolist()
    else:
        plat = ["YouTube Premium", "Netflix", "Disney+", "Google One", "Spotify"]
        pd.DataFrame(plat, columns=["Nombre"]).to_csv(PLAT_FILE, index=False)
        
    return df, df_ex, inv, plat

df_ventas, df_ex_clientes, df_inv, lista_plataformas = cargar_datos()

def limpiar_whatsapp(numero):
    solo_numeros = re.sub(r'\D', '', str(numero))
    if len(solo_numeros) == 9: return f"51{solo_numeros}"
    return solo_numeros

plantillas_wa = load_templates()

# ==============================================================================
# BLOQUE 4: SISTEMA DE LOGIN Y SESIÓN
# ==============================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.role = ""
    st.session_state.acceso_yt = "No"

if 'nuevo_vend_usr' not in st.session_state: st.session_state.nuevo_vend_usr = None
if 'nuevo_vend_pwd' not in st.session_state: st.session_state.nuevo_vend_pwd = None
if 'nuevo_vend_nom' not in st.session_state: st.session_state.nuevo_vend_nom = None
if 'nuevo_vend_tel' not in st.session_state: st.session_state.nuevo_vend_tel = None

if not os.path.exists(USUARIOS_FILE):
    pd.DataFrame([["admin", "admin123", "Admin", "N/A", "Si"]], columns=["Usuario", "Password", "Rol", "Telefono", "Acceso_YT"]).to_csv(USUARIOS_FILE, index=False)

df_usuarios = pd.read_csv(USUARIOS_FILE)

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
# BLOQUE 5: DIÁLOGOS DE GESTIÓN Y RENOVACIONES
# ==============================================================================
@st.dialog("🔄 Renovar Suscripción")
def renovar_venta_popup(idx, row):
    st.write(f"Renovando cuenta de: **{row['Cliente']}** (📺 {row['Producto']})")
    dur = st.radio("Plazo de renovación:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    
    hoy = datetime.now().date()
    venc_actual = pd.to_datetime(row['Vencimiento']).date()
    fecha_base = max(hoy, venc_actual) 
    
    if dur == "1 Mes": nueva_fecha = fecha_base + timedelta(days=30)
    elif dur == "2 Meses": nueva_fecha = fecha_base + timedelta(days=60)
    elif dur == "6 Meses": nueva_fecha = fecha_base + timedelta(days=180)
    else: nueva_fecha = fecha_base + timedelta(days=365)
    
    st.info(f"📅 El nuevo vencimiento será el: **{nueva_fecha}**")
    st.divider()
    
    tipo_cta = st.radio("Credenciales para este nuevo periodo:", ["Mantener la misma cuenta", "Asignar cuenta nueva (Rotativa)"], horizontal=True)
    mv, pv = row['Correo'], row['Pass'] 
    
    if tipo_cta == "Asignar cuenta nueva (Rotativa)":
        ca, cb = st.columns(2)
        tiene_acceso_inventario = (st.session_state.role == "Admin") or (st.session_state.acceso_yt == "Si")
        if row['Producto'] == "YouTube Premium" and tiene_acceso_inventario:
            disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
            if not disponibles.empty:
                sug = disponibles.iloc[0]
                with ca: mv = st.text_input("Nuevo Correo (Automático)", value=sug['Correo'])
                with cb: pv = st.text_input("Nueva Clave", value=sug['Password'])
            else:
                st.warning("No hay cupos en inventario.")
                with ca: mv = st.text_input("Nuevo Correo Manual")
                with cb: pv = st.text_input("Nueva Clave Manual")
        else:
            with ca: mv = st.text_input("Nuevo Correo")
            with cb: pv = st.text_input("Nueva Clave")
            
    if st.button("CONFIRMAR RENOVACIÓN", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Vencimiento'] = nueva_fecha
        df_ventas.at[idx, 'Correo'] = mv
        df_ventas.at[idx, 'Pass'] = pv
        df_ventas.to_csv(VENTAS_FILE, index=False)
        st.success("¡Renovado con éxito!")
        st.rerun()

@st.dialog("Editar Registro")
def editar_venta_popup(idx, row):
    prod = st.selectbox("Plataforma", lista_plataformas, index=lista_plataformas.index(row['Producto']) if row['Producto'] in lista_plataformas else 0)
    nom = st.text_input("Nombre", value=row['Cliente'])
    tel = st.text_input("WhatsApp", value=row['WhatsApp'])
    venc = st.date_input("Vencimiento", row['Vencimiento'])
    st.divider()
    c_costo, c_precio = st.columns(2)
    val_costo = float(row['Costo']) if not pd.isna(row.get('Costo')) else 0.0
    val_precio = float(row['Precio']) if not pd.isna(row.get('Precio')) else 0.0
    costo = c_costo.number_input("Costo (Lo que pagas)", value=val_costo, step=1.0)
    precio = c_precio.number_input("Precio de Venta", value=val_precio, step=1.0)
    st.divider()
    m = st.text_input("Correo", value=row['Correo'])
    p = st.text_input("Pass", value=row['Pass'])
    perf = st.text_input("Perfil", value=row['Perfil'])
    if st.button("ACTUALIZAR", type="primary", use_container_width=True):
        df_ventas.at[idx, 'Cliente'], df_ventas.at[idx, 'WhatsApp'] = nom, limpiar_whatsapp(tel)
        df_ventas.at[idx, 'Producto'], df_ventas.at[idx, 'Vencimiento'] = prod, venc
        df_ventas.at[idx, 'Correo'], df_ventas.at[idx, 'Pass'], df_ventas.at[idx, 'Perfil'] = m, p, perf
        df_ventas.at[idx, 'Costo'], df_ventas.at[idx, 'Precio'] = costo, precio
        df_ventas.to_csv(VENTAS_FILE, index=False)
        st.rerun()

@st.dialog("Nueva Venta")
def nueva_venta_popup():
    c1, c2 = st.columns(2)
    with c1: prod = st.selectbox("Plataforma", lista_plataformas)
    with c2: f_ini = st.date_input("Inicio", datetime.now())
    nom = st.text_input("Nombre Cliente")
    tel = st.text_input("WhatsApp (ej: 999888777)")
    c_costo, c_precio = st.columns(2)
    costo = c_costo.number_input("Costo de la cuenta", value=0.0, step=1.0)
    precio = c_precio.number_input("Precio de Venta", value=0.0, step=1.0)
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
                    with ca: mv = st.text_input("Correo Auto-asignado", value=sug['Correo'])
                    with cb: pv = st.text_input("Clave", value=sug['Password'])
                else: 
                    st.warning("No hay cupos automáticos.")
                    with ca: mv = st.text_input("Correo")
                    with cb: pv = st.text_input("Pass")
            else:
                st.warning("Inventario vacío.")
                with ca: mv = st.text_input("Correo")
                with cb: pv = st.text_input("Pass")
        else:
            st.info("Ingresa la cuenta asignada.")
            with ca: mv = st.text_input("Correo")
            with cb: pv = st.text_input("Clave")
    else: 
        with ca: mv = st.text_input("Correo")
        with cb: pv = st.text_input("Pass")
    
    if st.button("REGISTRAR VENTA", type="primary", use_container_width=True):
        nueva = pd.DataFrame([[ "🟢", nom, limpiar_whatsapp(tel), prod, mv, pv, "nan", "nan", venc, st.session_state.user, costo, precio ]], columns=df_ventas.columns)
        pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
        st.rerun()

# ==============================================================================
# BLOQUE 6: NAVEGACIÓN LATERAL
# ==============================================================================
with st.sidebar:
    st.title("🚀 NEXA-Stream")
    st.caption(f"👤 {st.session_state.user} | Nivel: {st.session_state.role}")
    st.divider()
    
    menu_opciones = ["📊 Panel de Ventas", "📈 Dashboard", "📂 Ex-Clientes"]
    if st.session_state.role == "Admin":
        menu_opciones.append("📦 Inventario YT")
        menu_opciones.append("👥 Vendedores")
        menu_opciones.append("⚙️ Configuración")
        
    menu = st.radio("Navegación", menu_opciones, label_visibility="collapsed")
    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==============================================================================
# VISTAS PRINCIPALES (DISEÑO MÓVIL ESTANDARIZADO)
# ==============================================================================

if menu == "📊 Panel de Ventas":
    st.header("Gestión de Suscripciones")
    
    if st.session_state.role == "Admin":
        cupos_disponibles = len(df_inv[df_inv['Usos'] < 2]) if not df_inv.empty else 0
        if cupos_disponibles <= 2:
            st.error(f"🚨 **¡ATENCIÓN INVENTARIO!** Solo quedan **{cupos_disponibles}** cupos de YouTube Premium automáticos.")

    if st.session_state.role == "Admin":
        filtro_admin = st.selectbox("Vista de datos:", ["Todos los vendedores", f"Solo mis ventas ({st.session_state.user})"])
        df_mostrar = df_ventas if filtro_admin == "Todos los vendedores" else df_ventas[df_ventas['Vendedor'] == st.session_state.user]
    else:
        df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]

    hoy = datetime.now().date()
    
    h1, h2 = st.columns([1, 2])
    with h1: 
        if st.button("➕ NUEVA VENTA", type="primary", use_container_width=True): nueva_venta_popup()
    with h2: 
        search = st.text_input("", placeholder="🔍 Buscar cliente...", label_visibility="collapsed")
        
    c_f1, c_f2 = st.columns(2)
    filtro_plat = c_f1.selectbox("Plataforma", ["Todas"] + lista_plataformas, label_visibility="collapsed")
    filtro_est = c_f2.selectbox("Estado", ["Todos", "🟢 Activos", "🟠 Por Vencer (3 días)", "🔴 Vencidos"], label_visibility="collapsed")

    if search:
        mask_search = df_mostrar.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        df_mostrar = df_mostrar[mask_search]
    if filtro_plat != "Todas":
        df_mostrar = df_mostrar[df_mostrar['Producto'] == filtro_plat]
    if filtro_est != "Todos":
        if filtro_est == "🟢 Activos": df_mostrar = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date > hoy + timedelta(days=3)]
        elif filtro_est == "🟠 Por Vencer (3 días)":
            mask_vencer = (pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy + timedelta(days=3)) & (pd.to_datetime(df_mostrar['Vencimiento']).dt.date > hoy)
            df_mostrar = df_mostrar[mask_vencer]
        elif filtro_est == "🔴 Vencidos": df_mostrar = df_mostrar[pd.to_datetime(df_mostrar['Vencimiento']).dt.date <= hoy]

    st.write("---")

    if not df_mostrar.empty:
        for idx, row in df_mostrar.sort_values(by="Vencimiento").iterrows():
            d = (row['Vencimiento'] - hoy).days
            col = "🔴" if d <= 0 else "🟠" if d <= 3 else "🟢"
            
            if d <= 0: texto_base = plantillas_wa["vencido"]
            else: texto_base = plantillas_wa["recordatorio"]
                
            texto_wa = texto_base.replace("{cliente}", str(row['Cliente'])).replace("{producto}", str(row['Producto'])).replace("{vencimiento}", str(row['Vencimiento']))
            wa_url = f"https://wa.me/{row['WhatsApp']}?text={quote(texto_wa)}"
            
            with st.container(border=True):
                vendedor_badge = f" 🧑‍💼 {row['Vendedor']}" if st.session_state.role == "Admin" and 'filtro_admin' in locals() and filtro_admin == "Todos los vendedores" else ""
                
                st.write(f"{col} **{row['Cliente']}** | {row['Producto']}")
                st.caption(f"📧 {row['Correo']} | 📅 {row['Vencimiento']}{vendedor_badge}")
                
                # Botones ahora con texto explicativo usando columnas de Streamlit nativas
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    st.link_button("📲 Notificar", wa_url, use_container_width=True)
                    if st.button("📝 Editar", key=f"e_{idx}", use_container_width=True): editar_venta_popup(idx, row)
                with btn_col2:
                    if st.button("🔄 Renovar", key=f"r_{idx}", use_container_width=True): renovar_venta_popup(idx, row)
                    if st.button("🗑️ Papelera", key=f"v_{idx}", use_container_width=True):
                        df_ex_clientes = pd.concat([df_ex_clientes, pd.DataFrame([row])], ignore_index=True)
                        df_ex_clientes.to_csv(EX_CLIENTES_FILE, index=False)
                        df_ventas.drop(idx).to_csv(VENTAS_FILE, index=False); st.rerun()
    else: st.info("No hay registros que coincidan con los filtros.")

elif menu == "📈 Dashboard":
    st.header("Análisis de Rendimiento")
    if st.session_state.role == "Admin": df_dash = df_ventas
    else: df_dash = df_ventas[df_ventas['Vendedor'] == st.session_state.user]
        
    if df_dash.empty: st.warning("No hay suficientes datos.")
    else:
        df_dash['Costo'] = pd.to_numeric(df_dash['Costo'], errors='coerce').fillna(0)
        df_dash['Precio'] = pd.to_numeric(df_dash['Precio'], errors='coerce').fillna(0)
        total_ingresos = df_dash['Precio'].sum()
        total_costos = df_dash['Costo'].sum()
        total_ganancia = total_ingresos - total_costos
        total_clientes = len(df_dash)
        
        c1, c2 = st.columns(2)
        c1.metric("👥 Clientes", f"{total_clientes}")
        c2.metric("💰 Ventas", f"${total_ingresos:.2f}")
        c3, c4 = st.columns(2)
        c3.metric("📉 Costos", f"${total_costos:.2f}")
        c4.metric("🚀 GANANCIA", f"${total_ganancia:.2f}")
        
        st.divider()
        st.subheader("Distribución por Plataforma")
        ventas_plat = df_dash['Producto'].value_counts().reset_index()
        ventas_plat.columns = ['Plataforma', 'Cantidad']
        grafico_anillo = alt.Chart(ventas_plat).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="Cantidad", type="quantitative"),
            color=alt.Color(field="Plataforma", type="nominal", legend=alt.Legend(title="Plataformas", orient="bottom")),
            tooltip=['Plataforma', 'Cantidad']
        ).properties(height=350).configure_view(strokeWidth=0)
        st.altair_chart(grafico_anillo, use_container_width=True)

elif menu == "📂 Ex-Clientes":
    st.header("Historial y Papelera")
    df_ex_mostrar = df_ex_clientes if st.session_state.role == "Admin" else df_ex_clientes[df_ex_clientes['Vendedor'] == st.session_state.user]
    if df_ex_mostrar.empty: st.info("La papelera está vacía.")
    else:
        for idx, row in df_ex_mostrar.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.write(f"🚫 **{row['Cliente']}** ({row['Producto']}) - Tel: {row['WhatsApp']}")
                if c2.button("🗑️ Borrar Definitivo", key=f"ex_{idx}", use_container_width=True):
                    df_ex_clientes.drop(idx).to_csv(EX_CLIENTES_FILE, index=False); st.rerun()

elif menu == "📦 Inventario YT":
    st.header("Inventario YouTube")
    if st.button("➕ NUEVO CORREO", type="primary", use_container_width=True):
        @st.dialog("Registrar Correo")
        def add():
            m = st.text_input("Gmail")
            p = st.text_input("Contraseña")
            u = st.selectbox("Usos", [0,1,2])
            if st.button("Guardar"):
                ni = pd.DataFrame([[m, p, u, "Nadie"]], columns=df_inv.columns)
                pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False); st.rerun()
        add()
    for idx, row in df_inv.iterrows():
        with st.container(border=True):
            st.write(f"📧 **{row['Correo']}** (Usos: {row['Usos']})")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📝 Editar", key=f"ei_{idx}", use_container_width=True): 
                    @st.dialog("Modificar")
                    def edi():
                        nu = st.selectbox("Usos", [0,1,2], index=int(row['Usos']))
                        na = st.text_input("Asignado a", value=row['Asignado_A'])
                        if st.button("Actualizar"):
                            df_inv.at[idx, 'Usos'], df_inv.at[idx, 'Asignado_A'] = nu, na
                            df_inv.to_csv(INV_FILE, index=False); st.rerun()
                    edi()
            with c2:
                if st.button("🗑️ Borrar", key=f"di_{idx}", use_container_width=True): 
                    df_inv.drop(idx).to_csv(INV_FILE, index=False); st.rerun()

elif menu == "👥 Vendedores":
    st.header("Control de Personal")
    @st.dialog("Editar Vendedor")
    def editar_vendedor_popup(idx, row):
        st.write(f"Editando a: **{row['Usuario']}**")
        n_tel = st.text_input("Teléfono", value=row['Telefono'])
        n_pwd = st.text_input("Nueva Contraseña", value=row['Password'])
        n_acc = st.checkbox("✅ Acceso a YouTube Auto", value=(row['Acceso_YT'] == 'Si'))
        if st.button("Actualizar", type="primary", use_container_width=True):
            df_usuarios.at[idx, 'Telefono'] = n_tel
            df_usuarios.at[idx, 'Password'] = n_pwd
            df_usuarios.at[idx, 'Acceso_YT'] = "Si" if n_acc else "No"
            df_usuarios.to_csv(USUARIOS_FILE, index=False); st.rerun()
            
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
                        df_usuarios.to_csv(USUARIOS_FILE, index=False)
                        st.session_state.nuevo_vend_usr = usr_generado
                        st.session_state.nuevo_vend_pwd = pwd_generada
                        st.session_state.nuevo_vend_nom = nuevo_nom
                        st.session_state.nuevo_vend_tel = tel_limpio
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
                c_edit, c_del = st.columns(2)
                with c_edit:
                    if st.button("📝 Editar", key=f"eu_{idx}", use_container_width=True): editar_vendedor_popup(idx, row)
                with c_del:
                    if st.button("🗑️ Borrar", key=f"du_{idx}", use_container_width=True):
                        df_usuarios.drop(idx).to_csv(USUARIOS_FILE, index=False); st.rerun()

elif menu == "⚙️ Configuración":
    st.header("Configuración del Sistema")
    st.subheader("📝 Editar Plantillas de WhatsApp")
    st.info("Usa `{cliente}`, `{producto}` y `{vencimiento}`. Para el vendedor usa `{nombre}`, `{usuario}`, `{password}` y `{link}`.")
    with st.form("form_plantillas"):
        rec = st.text_area("1️⃣ Recordatorio (Cuenta Activa / Por vencer)", value=plantillas_wa["recordatorio"], height=80)
        ven = st.text_area("2️⃣ Cuenta Vencida (Al llegar a 0 días)", value=plantillas_wa["vencido"], height=80)
        ven_new = st.text_area("3️⃣ Mensaje para Vendedor Nuevo", value=plantillas_wa["vendedor"], height=100)
        if st.form_submit_button("💾 Guardar Plantillas", type="primary", use_container_width=True):
            plantillas_wa["recordatorio"] = rec
            plantillas_wa["vencido"] = ven
            plantillas_wa["vendedor"] = ven_new
            save_templates(plantillas_wa)
            st.success("¡Plantillas guardadas y activas!")
            st.rerun()
    st.divider()
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
        if cp2.button("🗑️", key=f"del_p_{p}", use_container_width=True):
            lista_plataformas.remove(p); pd.DataFrame(lista_plataformas, columns=["Nombre"]).to_csv(PLAT_FILE, index=False); st.rerun()
