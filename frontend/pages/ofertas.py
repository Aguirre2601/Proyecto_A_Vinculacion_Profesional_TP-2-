"""
pages/ofertas.py - Vista del catálogo de ofertas laborales.
"""
import requests
import streamlit as st

from common import api_online, get_backend_url, obtener_ofertas


def render():
    """Renderiza la vista de publicación y consulta de ofertas."""
    online = api_online()
    backend_url = get_backend_url()

    st.title("💼 Ofertas Laborales y Puestos Requeridos")
    st.markdown("Publicación y consulta de búsquedas con guardado en SQLite.")

    with st.expander("➕ Publicar Nueva Oferta Laboral"):
        with st.form("form_oferta", clear_on_submit=True):
            o_puesto = st.text_input("Título del Puesto", placeholder="Ej. Backend Developer Python Jr")
            o_empresa = st.text_input("Empresa", placeholder="Ej. Globant")
            o_skills_raw = st.text_area(
                "Habilidades Requeridas (separadas por coma)",
                placeholder="Python, FastAPI, Docker, PostgreSQL, Git"
            )
            o_desc = st.text_area("Descripción de la posición (opcional)")

            sub_ofr = st.form_submit_button("Publicar Oferta", type="primary")
            if sub_ofr:
                skills_req = [s.strip() for s in o_skills_raw.split(",") if s.strip()]
                if not o_puesto or not o_empresa or not skills_req:
                    st.error("Puesto, empresa y al menos una habilidad requerida son obligatorios.")
                else:
                    payload_ofr = {
                        "puesto": o_puesto.strip(),
                        "empresa": o_empresa.strip(),
                        "skills_requeridas": skills_req,
                        "descripcion": o_desc.strip() if o_desc else ""
                    }
                    if online:
                        try:
                            resp_ofr = requests.post(f"{backend_url}/ofertas", json=payload_ofr, timeout=4)
                            if resp_ofr.status_code == 201:
                                creada_ofr = resp_ofr.json()
                                st.session_state.ofertas.append(creada_ofr)
                                st.success(f"✅ ¡Oferta '{o_puesto}' guardada permanentemente en SQLite! (ID #{creada_ofr['id']})")
                            else:
                                st.error(f"❌ Error al publicar ({resp_ofr.status_code}): {resp_ofr.text}")
                        except Exception as ex:
                            st.error(f"❌ Error de conexión al guardar oferta: {ex}")
                    else:
                        nueva_ofr_local = {
                            "id": len(st.session_state.ofertas) + 1,
                            "puesto": o_puesto.strip(),
                            "empresa": o_empresa.strip(),
                            "skills_requeridas": skills_req,
                            "descripcion": o_desc.strip() if o_desc else ""
                        }
                        st.session_state.ofertas.append(nueva_ofr_local)
                        st.warning("⚠️ Oferta guardada SOLO TEMPORALMENTE en RAM de la pestaña. Conecta el Backend para persistir permanentemente en SQLite.")

    st.divider()
    st.subheader("Catálogo de Búsquedas Activas")

    col_f1, col_f2 = st.columns(2)
    f_puesto = col_f1.text_input("Filtrar por puesto", placeholder="Buscar por palabra clave...")
    f_empresa = col_f2.text_input("Filtrar por empresa", placeholder="Buscar por empresa...")

    ofertas_list = obtener_ofertas(f_puesto, f_empresa)
    for o in ofertas_list:
        with st.container():
            st.markdown(f"### 📌 {o['puesto']}")
            st.markdown(f"**Empresa:** {o['empresa']} | **ID:** #{o['id']}")
            if o.get("descripcion"):
                st.write(o["descripcion"])
            st.markdown(f"**Skills Requeridas:** {' • '.join([f'`{s}`' for s in o['skills_requeridas']])}")
            st.divider()
