"""
common.py - Utilidades compartidas del frontend.
Datos semilla, estado de sesión, configuración y helpers de API.
"""
import os
import requests
import streamlit as st

# Datos semilla locales para resguardo en caso de backend sin conexión
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
    """Inicializa el estado local del frontend."""
    if "estudiantes" not in st.session_state:
        st.session_state.estudiantes = list(SEED_ESTUDIANTES)
    if "ofertas" not in st.session_state:
        st.session_state.ofertas = list(SEED_OFERTAS)
    if "postulaciones" not in st.session_state:
        st.session_state.postulaciones = []


def get_backend_url() -> str:
    """URL del backend configurada en la barra lateral."""
    default = os.getenv("BACKEND_API_URL", "http://backend:8000")
    return st.session_state.get("backend_url", default).rstrip("/")

BACKEND_HEALTH_URL = "http://backend:8000/health"
def api_online() -> bool:
    """Indica si el backend respondió correctamente al healthcheck."""
    try:
        # Hacemos una petición rápida con un timeout corto de 2 segundos
        respuesta = requests.get(BACKEND_HEALTH_URL, timeout=2)
        
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
    """Modelo de Gemini configurado por variable de entorno."""
    default = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
    return st.session_state.get("gemini_model", default)


def match_determinista(student_skills: list, required_skills: list):
    """Algoritmo determinista local de resguardo."""
    student_set = {s.strip().lower() for s in student_skills if s and s.strip()}
    matching = [s.strip() for s in required_skills if s.strip().lower() in student_set]
    missing = [s.strip() for s in required_skills if s.strip().lower() not in student_set]
    total = len(matching) + len(missing)
    if total == 0:
        return 0.0, [], [], "(0 / 0) * 100 = 0.0%"
    score = round((len(matching) / total) * 100.0, 2)
    formula = f"({len(matching)} / {total}) * 100 = {score}%"
    return score, matching, missing, formula


def obtener_estudiantes():
    """Obtiene estudiantes desde la API o desde la memoria local."""
    if api_online():
        try:
            r = requests.get(f"{get_backend_url()}/estudiantes", timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    return st.session_state.estudiantes


def obtener_ofertas(filtro_puesto=None, filtro_empresa=None):
    """Obtiene ofertas desde la API o desde la memoria local."""
    if api_online():
        try:
            params = {}
            if filtro_puesto:
                params["puesto"] = filtro_puesto
            if filtro_empresa:
                params["empresa"] = filtro_empresa
            r = requests.get(f"{get_backend_url()}/ofertas", params=params, timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

    res = list(st.session_state.ofertas)
    if filtro_puesto:
        res = [o for o in res if filtro_puesto.lower() in o["puesto"].lower()]
    if filtro_empresa:
        res = [o for o in res if filtro_empresa.lower() in o["empresa"].lower()]
    return res
