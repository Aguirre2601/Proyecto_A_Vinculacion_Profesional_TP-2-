"""
pages/historial.py - Vista del historial de postulaciones y planes IA.
"""
import requests
import streamlit as st

from common import api_online, get_backend_url


def render():
    """Renderiza la vista de historial de postulaciones."""
    online = api_online()
    backend_url = get_backend_url()

    st.title("📋 Historial de Postulaciones y Recomendaciones LLM")
    st.markdown("Consulta de postulaciones registradas con sus planes formativos persistidos en base de datos.")

    postulaciones_db = []
    if online:
        try:
            r = requests.get(f"{backend_url}/postulaciones", timeout=3)
            if r.status_code == 200:
                postulaciones_db = r.json()
        except Exception:
            pass

    postulaciones = postulaciones_db if postulaciones_db else st.session_state.postulaciones
    if postulaciones:
        for p in reversed(postulaciones):
            titulo_post = f"Postulacion #{p['id']} - Scoring: {p['scoring']:.1f}% ({p['estado']}) - Estudiante ID #{p['estudiante_id']}"
            with st.expander(titulo_post):
                st.write(f"**Puesto / Oferta ID:** #{p['oferta_id']}")
                st.write(f"**Skills Coincidentes:** {', '.join(p['skills_coincidentes']) if p['skills_coincidentes'] else 'Ninguna'}")
                st.write(f"**Skills Faltantes:** {', '.join(p['skills_faltantes']) if p['skills_faltantes'] else 'Ninguna'}")
                if p.get("ia_feedback"):
                    st.markdown("---")
                    st.markdown("#### 🤖 Recomendación Formativa Almacenada en SQLite:")
                    st.markdown(p["ia_feedback"])
    else:
        st.info("Aún no hay postulaciones registradas en la base de datos. Ve a la pestaña '🎯 Postulación y Matching' para calcular una.")
