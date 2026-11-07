"""
pages/acerca.py - Vista informativa sobre la arquitectura del sistema.
"""
import streamlit as st


def render():
    """Renderiza la vista de información del sistema."""
    st.title("ℹ️ Arquitectura del Sistema - Proyecto A")
    st.markdown("""
    ### Principio de Separación de Responsabilidades
    1. **Lógica Determinista (FastAPI + Python Puro):**
       - El cálculo de scoring y la detección de brechas se realizan de forma matemática y determinista.
       - No se utiliza LLM para calcular porcentajes, evitando sesgos o alucinaciones numéricas.
    2. **Inteligencia Artificial (LLM - Gemini / Ollama):**
       - Actúa únicamente para elaborar el plan pedagógico y ruta de aprendizaje basado exclusivamente en la lista de skills faltantes.
    3. **Automatización Low-Code (n8n):**
       - Orquesta los eventos: Webhooks, llamadas HTTP y bifurcaciones condicionales (Scoring >= 70%).
    4. **Presentación (Streamlit):**
       - Interfaz desacoplada con soporte dual (API REST de FastAPI o motor autónomo de alta disponibilidad).
    """)
