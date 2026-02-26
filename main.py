import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="NEXA-Stream Pro", layout="wide")

st.markdown("""
    <style>
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
    }
    .element-container:has(.fila-botones) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 33.33% !important;
        min-width: 0 !important;
        flex: 1 1 0px !important;
    }
    .stButton>button, .stLinkButton>a {
        border-radius: 8px !important;
        height: 40px !important;
        padding: 0px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        font-size: 20px !important; 
        margin: 0px !important;
    }
    .stLinkButton>a { background-color: #25D366 !important; color: white !important; border: none !important; }
    .stTextInput>div>div>input { border-radius: 8px; height: 38px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ARCHIVOS DE DATOS ---
VENTAS_FILE = "ventas_data.csv"
INV_FILE = "inventario_yt.csv"
PLAT_FILE = "plataformas.csv"
USUARIOS_FILE = "usuarios.csv"

# --- 3. SISTEMA DE LOGIN ESTRICTO ---
# Se verifica si el usuario ya inició sesión en esta ventana
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.role = ""

# Si no existe el archivo de usuarios, crea el Administrador maestro
if not os.path.exists(USUARIOS_FILE):
    pd.DataFrame([["admin", "admin123", "Admin"]], columns=["Usuario", "Password", "Rol"]).to_csv(USUARIOS_FILE, index=False)

df_usuarios = pd.read_csv(USUARIOS_FILE)

# PANTALLA DE BLOQUEO (Si no está logueado, de aquí no pasa)
if not st.session_state.logged_in:
    st.title("🔐 Acceso Privado NEXA-Stream")
    st.info("Por favor, identifícate para acceder a tu base de datos.")
    with st.container(border=True):
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Contraseña", type="password")
        if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
            match = df_usuarios[(df_usuarios['Usuario'] == u_in) & (df_usuarios['Password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user = match.iloc[0]['Usuario']
                st.session_state.role = match.iloc[0]['Rol']
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")
    st.stop() # <- ESTA ES LA LÍNEA QUE BLOQUEA EL RESTO DEL CÓDIGO

# --- 4. CARGA DE DATOS PRINCIPALES ---
def cargar_datos():
    if os.path.exists(VENTAS_FILE):
        df = pd.read_csv(VENTAS_FILE)
        df['Vencimiento'] = pd.to_datetime(df['Vencimiento'], errors='coerce').dt.date
        # Si las ventas antiguas no tienen vendedor, se te asignan a ti (admin)
        if 'Vendedor' not in df.columns:
            df['Vendedor'] = 'admin'
            df.to_csv(VENTAS_FILE, index=False)
    else:
        df = pd.DataFrame(columns=["Estado", "Cliente", "WhatsApp", "Producto", "Correo", "Pass", "Perfil", "PIN", "Vencimiento", "Vendedor"])
    
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

# --- 5. DIÁLOGOS DE EDICIÓN Y NUEVA VENTA ---
@st.dialog("Editar Venta")
def editar_venta_popup(idx, row):
    prod = st.selectbox("Plataforma", lista_plataformas, index=lista_plataformas.index(row['Producto']) if row['Producto'] in lista_plataformas else 0)
    nom = st.text_input("Nombre", value=row['Cliente'])
    tel = st.text_input("WhatsApp", value=row['WhatsApp'])
    venc = st.date_input("Vencimiento", row['Vencimiento'])
    st.divider()
    m = st.text_input("Correo", value=row['Correo'])
    p = st.text_input("Pass", value=row['Pass'])
    perf = st.text_input("Perfil", value=row['Perfil'])
    if st.button("GUARDAR CAMBIOS", type="primary", use_container_width=True):
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
    tel = st.text_input("WhatsApp")
    dur = st.radio("Plazo:", ["1 Mes", "2 Meses", "6 Meses", "1 Año"], horizontal=True)
    if dur == "1 Mes": venc = f_ini + relativedelta(months=1)
    elif dur == "2 Meses": venc = f_ini + relativedelta(months=2)
    elif dur == "6 Meses": venc = f_ini + relativedelta(months=6)
    else: venc = f_ini + relativedelta(years=1)
    
    st.divider()
    ca, cb = st.columns(2)
    if prod == "YouTube Premium" and not df_inv.empty:
        disponibles = df_inv[df_inv['Usos'] < 2].sort_values(by="Usos")
        if not disponibles.empty:
            sug = disponibles.iloc[0]
            with ca: mv = st.text_input("Correo", value=sug['Correo'])
            with cb: pv = st.text_input("Pass", value=sug['Password'])
        else: 
            st.error("Sin cupos YT")
            with ca: mv = st.text_input("Correo")
            with cb: pv = st.text_input("Pass")
    else: 
        with ca: mv = st.text_input("Correo")
        with cb: pv = st.text_input("Pass")
    
    if st.button("CONFIRMAR VENTA", type="primary", use_container_width=True):
        # AL GUARDAR SE REGISTRA EL VENDEDOR QUE INICIÓ SESIÓN
        nueva = pd.DataFrame([[ "🟢", nom, limpiar_whatsapp(tel), prod, mv, pv, "nan", "nan", venc, st.session_state.user ]], columns=df_ventas.columns)
        pd.concat([df_ventas, nueva], ignore_index=True).to_csv(VENTAS_FILE, index=False)
        st.rerun()

# --- 6. INTERFAZ PRINCIPAL (DESPUÉS DEL LOGIN) ---
c_title, c_logout = st.columns([4, 1])
c_title.title("🚀 NEXA-Stream")
if c_logout.button("🚪 Salir", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

st.success(f"👤 Conectado como: **{st.session_state.user}** (Nivel: {st.session_state.role})")
vista = st.radio("Modo de vista:", ["📱 Vista Celular", "💻 Vista PC"], horizontal=True, label_visibility="collapsed")

t1, t2 = st.tabs(["📊 Ventas", "⚙️ Configuración / Perfiles"])

with t1:
    h1, h2 = st.columns([1, 2])
    with h1: 
        if st.button("➕ NUEVA VENTA", type="primary", use_container_width=True): nueva_venta_popup()
    with h2: 
        search = st.text_input("", placeholder="🔍 Buscar cliente...", label_visibility="collapsed")
    
    # LÓGICA DE VISIBILIDAD DE VENTAS SEGÚN EL ROL
    if st.session_state.role == "Admin":
        filtro_admin = st.radio("Filtro Administrador:", ["Solo mis ventas", "Ver global (Todos los vendedores)"], horizontal=True)
        if filtro_admin == "Solo mis ventas":
            df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]
        else:
            df_mostrar = df_ventas
    else:
        # Los vendedores normales solo pueden ver su propia base de datos
        df_mostrar = df_ventas[df_ventas['Vendedor'] == st.session_state.user]

    st.divider()

    if not df_mostrar.empty:
        mask = df_mostrar.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        for idx, row in df_mostrar[mask].sort_values(by="Vencimiento").iterrows():
            hoy = datetime.now().date()
            d = (row['Vencimiento'] - hoy).days
            col = "🔴" if d <= 0 else "🟠" if d <= 3 else "🟢"
            
            with st.container(border=True):
                msj = f"Hola%20{row['Cliente']},%20tu%20cuenta%20de%20{row['Producto']}%20vence%20el%20{row['Vencimiento']}."
                wa_url = f"https://wa.me/{row['WhatsApp']}?text={msj}"
                
                vendedor_badge = f" *(Por: {row['Vendedor']})*" if st.session_state.role == "Admin" and filtro_admin == "Ver global (Todos los vendedores)" else ""

                if vista == "📱 Vista Celular":
                    st.write(f"{col} **{row['Cliente']}** | {row['Producto']}{vendedor_badge}")
                    st.caption(f"📧 {row['Correo']} | 📅 {row['Vencimiento']}")
                    
                    st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                    cols = st.columns(3)
                    with cols[0]:
                        st.link_button("📲", wa_url, use_container_width=True)
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
    else: st.info("No hay ventas registradas o visibles para tu perfil.")

with t2:
    st.download_button("📥 Descargar Respaldo (Backup)", df_ventas.to_csv(index=False).encode('utf-8'), "ventas_backup.csv", use_container_width=True)
    
    # --- CREACIÓN DE VENDEDORES (SOLO PARA ADMIN) ---
    if st.session_state.role == "Admin":
        st.divider()
        st.subheader("👥 Gestión de Perfiles / Vendedores")
        with st.expander("Crear Nuevo Perfil de Vendedor"):
            c_nu, c_np = st.columns(2)
            with c_nu: nu_usr = st.text_input("Usuario del Vendedor")
            with c_np: nu_pass = st.text_input("Contraseña del Vendedor")
            if st.button("Crear Perfil", type="primary"):
                if nu_usr and nu_pass:
                    nu_df = pd.DataFrame([[nu_usr, nu_pass, "Vendedor"]], columns=["Usuario", "Password", "Rol"])
                    pd.concat([df_usuarios, nu_df], ignore_index=True).to_csv(USUARIOS_FILE, index=False)
                    st.success(f"✅ Vendedor '{nu_usr}' creado correctamente.")
                    st.rerun()
    
    st.divider()
    col_inv, col_plat = st.columns(2)
    
    with col_plat:
        st.subheader("🛠 Plataformas")
        nueva_p = st.text_input("Agregar Plataforma")
        if st.button("Añadir", use_container_width=True):
            if nueva_p and nueva_p not in lista_plataformas:
                lista_plataformas.append(nueva_p)
                pd.DataFrame(lista_plataformas, columns=["Nombre"]).to_csv(PLAT_FILE, index=False); st.rerun()
        for p in lista_plataformas:
            cp1, cp2 = st.columns([3, 1])
            with cp1: st.write(p)
            with cp2: 
                if st.button("🗑️", key=f"del_p_{p}", use_container_width=True):
                    lista_plataformas.remove(p)
                    pd.DataFrame(lista_plataformas, columns=["Nombre"]).to_csv(PLAT_FILE, index=False); st.rerun()

    with col_inv:
        st.subheader("📦 Inventario YT")
        if st.button("➕ AGREGAR CORREO", use_container_width=True):
            @st.dialog("Nuevo")
            def add():
                m = st.text_input("Correo")
                p = st.text_input("Pass")
                u = st.selectbox("Usos", [0,1,2])
                if st.button("Guardar"):
                    ni = pd.DataFrame([[m, p, u, "Nadie"]], columns=df_inv.columns)
                    pd.concat([df_inv, ni], ignore_index=True).to_csv(INV_FILE, index=False); st.rerun()
            add()
        for idx, row in df_inv.iterrows():
            with st.container(border=True):
                st.write(f"📧 {row['Correo']} (Usos: {row['Usos']})")
                st.markdown('<div class="fila-botones"></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📝", key=f"ei_{idx}", use_container_width=True): 
                        @st.dialog("Editar")
                        def edi():
                            nu = st.selectbox("Usos", [0,1,2], index=int(row['Usos']))
                            na = st.text_input("Asignado a", value=row['Asignado_A'])
                            if st.button("Guardar"):
                                df_inv.at[idx, 'Usos'], df_inv.at[idx, 'Asignado_A'] = nu, na
                                df_inv.to_csv(INV_FILE, index=False); st.rerun()
                        edi()
                with c2:
                    if st.button("🗑️", key=f"di_{idx}", use_container_width=True): 
                        df_inv.drop(idx).to_csv(INV_FILE, index=False); st.rerun()
