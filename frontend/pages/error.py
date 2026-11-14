"""
pages/error.py - Página global de error del frontend.
"""
import re

import streamlit as st


def _sanitizar_detalle(detalle: str) -> str:
    """Oculta claves que puedan venir dentro de un mensaje de error."""
    return re.sub(
        r"(key|api_key)=([^&\s]+)",
        r"\1=***",
        detalle,
        flags=re.IGNORECASE,
    )


def render():
    """Muestra un mensaje de error y permite volver a la página de inicio."""
    st.title("⚠️ Algo salió mal")
    st.error(
        "Ocurrió un error inesperado mientras se mostraba esta página. "
        "Podés volver al inicio e intentarlo de nuevo."
    )

    detalle = st.session_state.get("error_detalle")
    if detalle:
        with st.expander("Ver detalle técnico"):
            st.code(_sanitizar_detalle(str(detalle)), language="text")

    if st.button("🏠 Volver al inicio", type="primary", use_container_width=True):
        st.session_state.pop("error_detalle", None)
        pagina_inicio = st.session_state.get("_main_page_obj")
        if pagina_inicio is not None:
            st.switch_page(pagina_inicio)
        else:
            st.rerun()
