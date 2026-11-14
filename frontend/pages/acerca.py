"""
pages/acerca.py - Vista informativa sobre la arquitectura del sistema.
"""
import streamlit as st


def render():
    """Renderiza la vista de información del sistema."""
    st.title("ℹ️ Arquitectura del Sistema - Proyecto A")
    st.markdown("""
    ### Principio de Separación de Responsabilidades
    1. **Lógica Determinista (n8n Workflow 1):**
       - El cálculo de scoring y la detección de brechas se ejecutan en el Code node del Workflow 1 de n8n.
       - El backend solo persiste el resultado que n8n envía a `/postulaciones/registrar`; no recalcula el scoring.
       - No se utiliza LLM para calcular porcentajes, evitando sesgos o alucinaciones numéricas.
    2. **Inteligencia Artificial (LLM - Google Gemini):**
       - Actúa únicamente para elaborar el plan pedagógico y ruta de aprendizaje basado exclusivamente en la lista de skills faltantes.
       - La clave se guarda en la credencial `Header Auth account` de n8n; el modelo `gemini-3.1-flash-lite` está fijado en el nodo HTTP Request del Workflow 2.
    3. **Automatización Low-Code (n8n):**
       - Orquesta los eventos: Webhooks, cálculo determinista, persistencia y bifurcaciones condicionales según las skills faltantes.
    4. **Presentación (Streamlit):**
       - Interfaz desacoplada que llama al webhook del Workflow 1 y muestra una página de error si el backend o n8n no responden.
    """)
