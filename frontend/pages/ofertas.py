"""
pages/ofertas.py - Vista del catálogo de ofertas laborales.
"""
import requests
import streamlit as st

from common import api_online, get_backend_url, ir_a_error, obtener_ofertas


SKILLS_SUGERIDAS = [
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust",
    "PHP", "Ruby", "Kotlin", "Swift", "HTML", "CSS", "React", "Angular", "Vue",
    "Node.js", "FastAPI", "Django", "Flask", "Spring Boot", "SQL", "PostgreSQL",
    "MySQL", "SQLite", "MongoDB", "Redis", "Docker", "Kubernetes", "Git", "GitHub",
    "Linux", "Windows", "AWS", "Azure", "Google Cloud", "REST API", "GraphQL",
    "Pandas", "NumPy", "Machine Learning", "Data Analysis", "Power BI", "Excel",
    "Figma", "Scrum", "Agile", "Testing", "CI/CD"
]


def render():
    """Renderiza la vista de publicación y consulta."""
    online = api_online()
    backend_url = get_backend_url()

    st.title("💼 Ofertas Laborales y Puestos Requeridos")
    st.markdown("Publicación y consulta de búsquedas con guardado en SQLite.")

    with st.expander("➕ Publicar Nueva Oferta Laboral"):
        with st.form("form_oferta", clear_on_submit=True):
            o_puesto = st.text_input("Título del Puesto", placeholder="Ej. Backend Developer Python Jr")
            o_empresa = st.text_input("Empresa", placeholder="Ej. Globant")
            skills_req = st.multiselect(
                "Habilidades Requeridas",
                options=SKILLS_SUGERIDAS,
                accept_new_options=True,
                placeholder="Seleccioná o escribí una habilidad y presioná Enter",
                help="Podés elegir habilidades sugeridas, escribir otras nuevas y eliminar etiquetas individualmente."
            )
            o_desc = st.text_area("Descripción de la posición (opcional)")

            sub_ofr = st.form_submit_button("Publicar Oferta", type="primary")
            if sub_ofr:
                skills_req = [s.strip() for s in skills_req if s and s.strip()]
                if not o_puesto.strip() or not o_empresa.strip() or not skills_req:
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
                            ir_a_error(ex, "No se pudo publicar la oferta")
                    else:
                        ir_a_error("Backend desconectado", "No se puede publicar la oferta")

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
