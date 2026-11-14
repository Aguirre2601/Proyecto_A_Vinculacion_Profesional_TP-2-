"""
pages/postulacion.py - Vista de postulación: el Workflow 1 de n8n calcula el
match determinista y el Workflow 2 genera el plan formativo con IA.
"""
import requests
import streamlit as st

from common import (
    api_online,
    get_n8n_url,
    ir_a_error,
    obtener_estudiantes,
    obtener_ofertas,
)


def render():
    """Renderiza la vista de postulación y delega el cálculo a n8n."""
    online = api_online()
    n8n_url = get_n8n_url()

    st.title("🎯 Postulación y Cálculo Determinista de Compatibilidad")
    st.markdown(
        "Esta vista delega el cálculo determinista y la generación del plan "
        "formativo a los workflows de n8n."
    )
    st.info("Fórmula oficial evaluada: **Scoring = (|Skills Estudiante ∩ Skills Oferta| / |Skills Oferta|) * 100**")

    estudiantes = obtener_estudiantes()
    ofertas = obtener_ofertas()

    if not estudiantes or not ofertas:
        st.warning("⚠️ Debes tener al menos un estudiante y una oferta registrados.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Seleccionar Estudiante")
        opciones_est = {f"{e['nombre']} ({e['carrera']})": e for e in estudiantes}
        seleccion_est_label = st.selectbox("Estudiante:", list(opciones_est.keys()))
        est_seleccionado = opciones_est[seleccion_est_label]
        st.info(f"**Habilidades declaradas:** {', '.join(est_seleccionado['skills'])}")

    with col2:
        st.subheader("2. Seleccionar Oferta Laboral")
        opciones_ofr = {f"{o['puesto']} en {o['empresa']}": o for o in ofertas}
        seleccion_ofr_label = st.selectbox("Oferta de Trabajo:", list(opciones_ofr.keys()))
        ofr_seleccionada = opciones_ofr[seleccion_ofr_label]
        st.info(f"**Habilidades requeridas:** {', '.join(ofr_seleccionada['skills_requeridas'])}")

    st.divider()

    if "match_actual" not in st.session_state:
        st.session_state.match_actual = None

    if st.button("🚀 Calcular Compatibilidad Determinista", type="primary", use_container_width=True):
        with st.spinner("Ejecutando Workflow 1 de n8n y generando el plan con IA..."):
            if not online:
                ir_a_error("Backend desconectado", "No se puede ejecutar el Workflow 1 de n8n")
                return

            # El Workflow 1 recibe los datos completos y calcula el match internamente.
            payload_n8n = {
                "estudiante": est_seleccionado,
                "oferta": ofr_seleccionada,
            }

            try:
                resp = requests.post(
                    f"{n8n_url}/postulacion",
                    json=payload_n8n,
                    timeout=120
                )
            except Exception as ex:
                ir_a_error(ex, "No se pudo ejecutar el Workflow 1 de n8n")
                raise

            if resp.status_code != 200:
                ir_a_error(
                    f"HTTP {resp.status_code}: {resp.text}",
                    "No se pudo ejecutar el Workflow 1 de n8n"
                )
                return

            try:
                data = resp.json()
                scoring = data["scoring"]
                skills_match = data["skills_coincidentes"]
                skills_miss = data["skills_faltantes"]
                formula = data["formula"]
                postulacion_id = data["postulacion_id"]
            except Exception as ex:
                ir_a_error(ex, "Respuesta inválida del Workflow 1 de n8n")
                raise

            estado = data.get("estado") or (
                "Apta para entrevista" if scoring >= 70.0 else "En desarrollo formativo"
            )

            nuevo_registro = {
                "id": postulacion_id,
                "estudiante_id": data.get("estudiante_id", est_seleccionado["id"]),
                "estudiante_nombre": data.get("estudiante_nombre", est_seleccionado["nombre"]),
                "oferta_id": data.get("oferta_id", ofr_seleccionada["id"]),
                "oferta_puesto": data.get("oferta_puesto", ofr_seleccionada["puesto"]),
                "empresa": data.get("empresa", ofr_seleccionada["empresa"]),
                "scoring": scoring,
                "skills_coincidentes": skills_match,
                "skills_faltantes": skills_miss,
                "formula": formula,
                "estado": estado,
                "ia_feedback": data.get("ia_feedback"),
                "ia_origen": data.get("ia_origen"),
                "ia_error": data.get("ia_error"),
            }
            st.session_state.match_actual = nuevo_registro
            st.session_state.postulaciones.append(nuevo_registro)

    # Mostrar resultados si hay un match calculado
    if st.session_state.match_actual:
        m = st.session_state.match_actual
        st.success("✅ Cálculo determinista completado exitosamente por n8n")

        m1, m2, m3 = st.columns([1, 1, 1])
        m1.metric("Puntaje de Compatibilidad", f"{m['scoring']:.1f}%")
        m2.metric("Estado de la Postulación", m['estado'])
        m3.metric("Fórmula Evaluada", m['formula'])

        st.progress(int(m['scoring']) / 100)

        if m['scoring'] >= 70:
            st.markdown("🟢 **Candidato Apto:** Supera el umbral de corte del 70%. Pasa a etapa de entrevista.")
        else:
            st.markdown("🟡 **En Desarrollo Formativo:** No alcanza el 70% requerido. Requiere plan de mejora.")

        c_match, c_miss = st.columns(2)
        with c_match:
            st.markdown("### ✅ Habilidades Coincidentes (Intersección)")
            if m['skills_coincidentes']:
                for s in m['skills_coincidentes']:
                    st.markdown(f"- 🟢 **{s}**")
            else:
                st.write("Ninguna habilidad en común.")

        with c_miss:
            st.markdown("### ❌ Habilidades Faltantes (Brecha)")
            if m['skills_faltantes']:
                for s in m['skills_faltantes']:
                    st.markdown(f"- 🔴 **{s}**")
            else:
                st.write("No faltan habilidades. Perfil 100% cubierto.")

        # Plan formativo devuelto por el Workflow 2 a través del Workflow 1.
        if m.get("ia_feedback"):
            st.divider()
            st.markdown("### 🤖 Plan de Formación Generado con IA")
            st.success(f"Plan generado por n8n [{m.get('ia_origen', 'IA')}]")
            st.markdown(m["ia_feedback"])
        elif m.get("ia_error"):
            st.divider()
            st.warning(f"No se pudo generar el plan IA con n8n: {m['ia_error']}")
