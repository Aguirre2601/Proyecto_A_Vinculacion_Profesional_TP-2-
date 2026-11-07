"""
app.py - Punto de entrada del frontend Streamlit.
Define la configuración global, la barra lateral y conecta las páginas.
"""
import os

import requests
import streamlit as st

from common import get_gemini_model, init_session_state
from pages import acerca, estudiantes, historial, main_page, ofertas, postulacion

# Configuración de página
st.set_page_config(
    page_title="Plataforma de Vinculación Profesional",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session_state()

# Barra lateral: identidad y navegación
# st.sidebar.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
# st.sidebar.title("TP: Vinculación Profesional")
# st.sidebar.caption("Proyecto A - Arquitectura con Separación de Responsabilidades")
# 
pg = st.navigation(
    [
        st.Page(main_page.render, title="Inicio", icon="🏠", url_path="inicio", default=True),
        st.Page(postulacion.render, title="Postulación y Matching", icon="🎯", url_path="postulacion"),
        st.Page(estudiantes.render, title="Gestión de Estudiantes", icon="👨‍🎓", url_path="estudiantes"),
        st.Page(ofertas.render, title="Catálogo de Ofertas", icon="💼", url_path="ofertas"),
        st.Page(historial.render, title="Historial y Planes IA", icon="📋", url_path="historial"),
        st.Page(acerca.render, title="Acerca del Sistema", icon="ℹ️", url_path="acerca"),
    ]
)

# st.sidebar.divider()
# st.sidebar.subheader("⚙️ Estado de Conexión")
# default_env_url = os.getenv("BACKEND_API_URL", "http://backend:8000")
# backend_url_input = st.sidebar.text_input(
#     "URL Backend FastAPI:",
#     value=default_env_url,
#     help="Usa http://backend:8000 en Docker o http://localhost:8000 en tu máquina."
# ).rstrip("/")
# 
# # Configuración de IA (Google Gemini)
# gemini_env_key = os.getenv("GEMINI_API_KEY", "")
# if gemini_env_key == "tu_api_key_de_gemini_aqui":
#     gemini_env_key = ""
# 
# gemini_model = get_gemini_model()
# 
# st.sidebar.divider()
# st.sidebar.subheader("🤖 Motor de IA (Google Gemini)")
# gemini_key_input = st.sidebar.text_input(
#     "API Key de Gemini (Opcional):",
#     value=gemini_env_key,
#     type="password",
#     help="Obtén tu clave gratis en https://aistudio.google.com/. Si la dejas vacía, se usará el generador pedagógico offline."
# )
# 
# if gemini_key_input:
#     st.sidebar.success(f"🟢 {gemini_model} Conectado")
# else:
#     st.sidebar.info("🟡 Modo IA Offline (Plantilla Estructurada)")
# 
# # Comprobar si el backend FastAPI responde
# api_online = False
# try:
#     test_res = requests.get(f"{backend_url_input}/health", timeout=1.5)
#     if test_res.status_code == 200:
#         api_online = True
# except Exception:
#     # Intentar con localhost si backend falló (ejecución sin Docker)
#     if "backend:8000" in backend_url_input:
#         try:
#             local_test = requests.get("http://localhost:8000/health", timeout=1.5)
#             if local_test.status_code == 200:
#                 backend_url_input = "http://localhost:8000"
#                 api_online = True
#         except Exception:
#             pass
# 
# if api_online:
#     st.sidebar.success(f"🟢 Backend Conectado ({backend_url_input})")
#     st.sidebar.caption("💾 Base de datos SQLite persistente activa.")
# else:
#     st.sidebar.error(f"🔴 Backend Desconectado ({backend_url_input})")
#     st.sidebar.caption("⚠️ Advertencia: Guardado temporal en memoria RAM. Para persistir datos permanentemente, inicia el Backend.")
# 
# # Guardar configuración para que la lean las páginas
# st.session_state.backend_url = backend_url_input
# st.session_state.api_online = api_online
# st.session_state.gemini_key = gemini_key_input
# st.session_state.gemini_model = gemini_model
# 
# Ejecutar la página seleccionada
pg.run()
