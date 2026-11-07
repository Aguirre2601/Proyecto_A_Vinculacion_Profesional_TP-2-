"""
pages/estudiantes.py - Vista de gestión de estudiantes.
"""
import requests
import streamlit as st

from common import api_online, get_backend_url, obtener_estudiantes


def render():
    """Renderiza la vista de registro y listado de estudiantes."""
    online = api_online()
    backend_url = get_backend_url()

    st.title("👨‍🎓 Registro de Estudiantes")
    st.markdown("Alta de perfiles de alumnos con validación estricta y guardado permanente en SQLite.")

    with st.form("form_estudiante", clear_on_submit=True):
        f_nombre = st.text_input("Nombre y Apellido", placeholder="Ej. Camila Navarro")
        f_email = st.text_input("Correo Institucional", placeholder="ejemplo@universidad.edu.ar")
        f_carrera = st.selectbox(
            "Carrera",
            [
                "Ingeniería en Sistemas de Información",
                "Ingeniería Informática",
                "Licenciatura en Ciencias de la Computación",
                "Tecnicatura Universitaria en Programación",
                "Ingeniería Electrónica"
            ]
        )
        f_skills_raw = st.text_area(
            "Habilidades / Tecnologías (separadas por coma)",
            placeholder="Python, FastAPI, Docker, SQL, Git, Linux"
        )

        submitted = st.form_submit_button("Guardar Estudiante", type="primary")
        if submitted:
            skills_list = [s.strip() for s in f_skills_raw.split(",") if s.strip()]
            if not f_nombre or not f_email or not skills_list:
                st.error("Por favor completa todos los campos obligatorios y al menos una habilidad.")
            else:
                email_limpio = f_email.strip().lower()
                if "@" in email_limpio and "." not in email_limpio.split("@")[-1]:
                    email_limpio = f"{email_limpio}.com"
                payload = {
                    "nombre": f_nombre.strip(),
                    "email": email_limpio,
                    "carrera": f_carrera,
                    "skills": skills_list
                }

                if online:
                    try:
                        resp = requests.post(f"{backend_url}/estudiantes", json=payload, timeout=4)
                        if resp.status_code == 201:
                            creado = resp.json()
                            st.session_state.estudiantes.append(creado)
                            st.success(f"✅ ¡Estudiante '{f_nombre}' guardado de forma PERMANENTE en la base de datos SQLite! (ID #{creado['id']})")
                        elif resp.status_code == 400:
                            st.error(f"❌ Error al registrar: {resp.json().get('detail', 'El correo ya existe')}")
                        elif resp.status_code == 422:
                            st.error(f"❌ Formato de correo inválido: Asegúrate de incluir un email completo con '@' y '.com' (ejemplo: {email_limpio}).")
                        else:
                            st.error(f"❌ Error en Backend ({resp.status_code}): {resp.text}")
                    except Exception as ex:
                        st.error(f"❌ Error de conexión con el Backend: {ex}")
                else:
                    nuevo_local = {
                        "id": len(st.session_state.estudiantes) + 1,
                        "nombre": f_nombre.strip(),
                        "email": email_limpio,
                        "carrera": f_carrera,
                        "skills": skills_list
                    }
                    st.session_state.estudiantes.append(nuevo_local)
                    st.warning(f"⚠️ Estudiante '{f_nombre}' guardado SOLO TEMPORALMENTE en la memoria RAM del navegador. Como el Backend FastAPI no está conectado, este dato se perderá si recargas la página o reinicias. Levanta el Backend para persistir permanentemente.")

    st.divider()
    st.subheader("Estudiantes Registrados")
    est_list = obtener_estudiantes()
    for e in est_list:
        titulo_est = f"Estudiante: {e['nombre']} | {e['carrera']} (ID: {e['id']})"
        with st.expander(titulo_est):
            st.write(f"**Email:** {e['email']}")
            st.write(f"**Skills:** {', '.join(e['skills'])}")
