"""
common.py - Utilidades compartidas del frontend.
Estado de sesión, configuración y helpers de API.
"""
import os
import requests
import streamlit as st

# Datos semilla conservados solo como referencia.
# El frontend ya no los carga: sin backend se muestra la página de error.
SEED_ESTUDIANTES = [
    {
        "id": 1,
        "nombre": "Valeria Gómez",
        "email": "valeria.gomez@universidad.edu.ar",
        "carrera": "Ingeniería en Sistemas de Información",
        "skills": ["Python", "SQL", "FastAPI", "Git"]
    },
    {
        "id": 2,
        "nombre": "Lucas Morales",
        "email": "lucas.morales@universidad.edu.ar",
        "carrera": "Licenciatura en Ciencias de la Computación",
        "skills": ["JavaScript", "React", "HTML", "CSS", "Git"]
    },
    {
        "id": 3,
        "nombre": "Sofía Benítez",
        "email": "sofia.benitez@universidad.edu.ar",
        "carrera": "Ingeniería Informática",
        "skills": ["Python", "Docker", "PostgreSQL", "Linux", "FastAPI", "Pandas"]
    }
]

SEED_OFERTAS = [
    {
        "id": 1,
        "puesto": "Desarrollador Backend Junior (Python / FastAPI)",
        "empresa": "Fintech Innova",
        "descripcion": "Desarrollo de microservicios transaccionales con FastAPI y Docker.",
        "skills_requeridas": ["Python", "FastAPI", "Docker", "PostgreSQL", "Git"]
    },
    {
        "id": 2,
        "puesto": "Data Engineer Trainee",
        "empresa": "DataCloud Analytics",
        "descripcion": "Construcción de pipelines ETL y consultas analíticas.",
        "skills_requeridas": ["Python", "SQL", "Pandas", "Docker", "Airflow"]
    },
    {
        "id": 3,
        "puesto": "Fullstack Developer Jr",
        "empresa": "AgileTech Solutions",
        "descripcion": "Integración de frontend React con backend FastAPI.",
        "skills_requeridas": ["Python", "FastAPI", "JavaScript", "React", "Docker"]
    }
]


def init_session_state():
    """Inicializa el estado local del frontend (solo caché de datos confirmados)."""
    # Sin datos semilla: el frontend ya no funciona en modo offline.
    if "estudiantes" not in st.session_state:
        st.session_state.estudiantes = []
    if "ofertas" not in st.session_state:
        st.session_state.ofertas = []
    if "postulaciones" not in st.session_state:
        st.session_state.postulaciones = []


def get_backend_url() -> str:
    """URL del backend configurada en la barra lateral."""
    default = os.getenv("BACKEND_API_URL", "http://backend:8000")
    return st.session_state.get("backend_url", default).rstrip("/")


def get_n8n_url() -> str:
    """URL base de los webhooks de n8n."""
    default = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook")
    return st.session_state.get("n8n_url", default).rstrip("/")


def api_online() -> bool:
    """Indica si el backend respondió correctamente al healthcheck."""
    try:
        # Hacemos una petición rápida con un timeout corto de 2 segundos
        respuesta = requests.get(f"{get_backend_url()}/health", timeout=2)
        
        if respuesta.status_code == 200 and respuesta.json().get("status") == "ok":
            st.session_state["api_online"] = True
        else:
            st.session_state["api_online"] = False
            
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        # Si el servidor no responde o da error de conexión
        st.session_state["api_online"] = False

    return st.session_state["api_online"]


def get_gemini_key() -> str:
    """Clave de Gemini ingresada en la main_page."""
    return st.session_state.get("gemini_key", "")


def get_gemini_model() -> str:
    """Modelo de Gemini configurado en n8n (se muestra en la UI)."""
    default = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip() or "gemini-3.1-flash-lite"
    return st.session_state.get("gemini_model", default)


def ir_a_error(excepcion=None, contexto: str = ""):
    """Redirige a la página global de error y guarda el detalle técnico."""
    detalle = str(excepcion) if excepcion is not None else ""
    if contexto:
        detalle = f"{contexto}: {detalle}" if detalle else contexto

    st.session_state["error_detalle"] = detalle or "Error desconocido."
    pagina_error = st.session_state.get("_error_page_obj")
    if pagina_error is not None:
        st.switch_page(pagina_error)
    else:
        st.session_state["error_activo"] = True
        st.rerun()


# Fallback local deshabilitado: el match debe calcularlo el backend.
# def match_determinista(student_skills: list, required_skills: list):
#     """Algoritmo determinista local de resguardo."""
#     student_set = {s.strip().lower() for s in student_skills if s and s.strip()}
#     matching = [s.strip() for s in required_skills if s.strip().lower() in student_set]
#     missing = [s.strip() for s in required_skills if s.strip().lower() not in student_set]
#     total = len(matching) + len(missing)
#     if total == 0:
#         return 0.0, [], [], "(0 / 0) * 100 = 0.0%"
#     score = round((len(matching) / total) * 100.0, 2)
#     formula = f"({len(matching)} / {total}) * 100 = {score}%"
#     return score, matching, missing, formula


def obtener_estudiantes():
    """Obtiene estudiantes desde la API. Sin fallback a memoria local."""
    if not api_online():
        ir_a_error("Backend desconectado", "No se pueden obtener los estudiantes")

    try:
        r = requests.get(f"{get_backend_url()}/estudiantes", timeout=3)
    except Exception as ex:
        ir_a_error(ex, "No se pudieron obtener los estudiantes")
        raise

    if r.status_code == 200:
        return r.json()

    ir_a_error(f"HTTP {r.status_code}", "No se pudieron obtener los estudiantes")
    raise RuntimeError(f"HTTP {r.status_code} al obtener estudiantes")


def obtener_ofertas(filtro_puesto=None, filtro_empresa=None):
    """Obtiene ofertas desde la API. Sin fallback a memoria local."""
    if not api_online():
        ir_a_error("Backend desconectado", "No se pueden obtener las ofertas")

    try:
        params = {}
        if filtro_puesto:
            params["puesto"] = filtro_puesto
        if filtro_empresa:
            params["empresa"] = filtro_empresa
        r = requests.get(f"{get_backend_url()}/ofertas", params=params, timeout=3)
    except Exception as ex:
        ir_a_error(ex, "No se pudieron obtener las ofertas")
        raise

    if r.status_code == 200:
        return r.json()

    ir_a_error(f"HTTP {r.status_code}", "No se pudieron obtener las ofertas")
    raise RuntimeError(f"HTTP {r.status_code} al obtener ofertas")
