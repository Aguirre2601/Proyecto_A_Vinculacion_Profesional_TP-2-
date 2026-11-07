"""
main_page.py - Página de bienvenida.
"""
import streamlit as st

from common import api_online, get_backend_url, get_gemini_model


def render():
    """Renderiza la página de inicio."""
    st.title("🎓 Plataforma de Vinculación Profesional")
    st.markdown("### Bienvenido/a")
    st.markdown(
        "Este sistema conecta **estudiantes universitarios** con **ofertas laborales** "
        "y calcula la compatibilidad técnica de forma determinista. Si el perfil no "
        "alcanza el umbral del 70%, genera un plan de formación personalizado con IA."
    )

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🎯 Matching determinista")
        st.write("Calculá el porcentaje de compatibilidad y detectá las habilidades faltantes.")
    with col2:
        st.markdown("#### 💼 Ofertas y estudiantes")
        st.write("Registrá perfiles, publicá ofertas y consultá el catálogo disponible.")
    with col3:
        st.markdown("#### 🤖 Planes con IA")
        st.write("Generá una ruta de aprendizaje enfocada en las brechas detectadas.")

    st.divider()
    st.subheader("🚀 Cómo empezar")
    st.markdown(
        "1. **Registrá estudiantes** en *Gestión de Estudiantes*.\n"
        "2. **Publicá ofertas** en *Catálogo de Ofertas*.\n"
        "3. **Calculá el match** en *Postulación y Matching*.\n"
        "4. **Generá el plan de formación** si el scoring es menor a 70%.\n"
        "5. **Consultá el historial** en *Historial y Planes IA*."
    )

    st.divider()
    if api_online():
        st.success(f"🟢 Backend conectado en {get_backend_url()}")
    else:
        st.warning(
            "🟡 Backend desconectado. La aplicación funciona en modo temporal "
            "con datos en memoria; los cambios se pierden al recargar."
        )

    st.info(f"🤖 Modelo de IA configurado: **{get_gemini_model()}**")
