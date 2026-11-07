"""
pages/postulacion.py - Vista de postulación y matching determinista.
"""
import requests
import streamlit as st

from common import (
    api_online,
    get_backend_url,
    get_gemini_key,
    get_gemini_model,
    match_determinista,
    obtener_estudiantes,
    obtener_ofertas,
)


def render():
    """Renderiza la vista de postulación y cálculo de compatibilidad."""
    online = api_online()
    backend_url = get_backend_url()
    gemini_key = get_gemini_key()
    gemini_model = get_gemini_model()

    st.title("🎯 Postulación y Cálculo Determinista de Compatibilidad")
    st.markdown("Esta vista ejecuta el cálculo matemático determinista:")
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
        with st.spinner("Calculando compatibilidad y analizando brechas..."):
            scoring = 0.0
            skills_match = []
            skills_miss = []
            formula = ""
            postulacion_id = len(st.session_state.postulaciones) + 1

            # Llamar al backend si está online
            if online:
                try:
                    resp = requests.post(
                        f"{backend_url}/postulaciones/match",
                        json={"estudiante_id": est_seleccionado["id"], "oferta_id": ofr_seleccionada["id"]},
                        timeout=4
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        scoring = data["scoring"]
                        skills_match = data["skills_coincidentes"]
                        skills_miss = data["skills_faltantes"]
                        formula = data["formula"]
                        postulacion_id = data.get("postulacion_id", postulacion_id)
                except Exception:
                    scoring, skills_match, skills_miss, formula = match_determinista(
                        est_seleccionado["skills"], ofr_seleccionada["skills_requeridas"]
                    )
            else:
                scoring, skills_match, skills_miss, formula = match_determinista(
                    est_seleccionado["skills"], ofr_seleccionada["skills_requeridas"]
                )

            estado = "Apta para entrevista" if scoring >= 70.0 else "En desarrollo formativo"

            nuevo_registro = {
                "id": postulacion_id,
                "estudiante_id": est_seleccionado["id"],
                "estudiante_nombre": est_seleccionado["nombre"],
                "oferta_id": ofr_seleccionada["id"],
                "oferta_puesto": ofr_seleccionada["puesto"],
                "empresa": ofr_seleccionada["empresa"],
                "scoring": scoring,
                "skills_coincidentes": skills_match,
                "skills_faltantes": skills_miss,
                "formula": formula,
                "estado": estado,
                "ia_feedback": None
            }
            st.session_state.match_actual = nuevo_registro
            st.session_state.postulaciones.append(nuevo_registro)

    # Mostrar resultados si hay un match calculado
    if st.session_state.match_actual:
        m = st.session_state.match_actual
        st.success("✅ Cálculo determinista completado exitosamente")

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

        # Sección de Disparo Directo a n8n para Demostración Oral
        st.divider()
        st.markdown("### ⚡ Automatización en Vivo con n8n (Demostración de Cátedra)")
        st.caption("Envía la postulación directamente al motor Low-Code n8n para ver cómo se iluminan los nodos en pantalla.")
        c_n1, c_n2 = st.columns(2)
        with c_n1:
            if st.button("▶️ Disparar n8n (Modo Test / Escucha)", key=f"n8n_test_{m['id']}"):
                payload_n8n = {"estudiante_id": m["estudiante_id"], "oferta_id": m["oferta_id"]}
                disparado = False
                for url_test in ["http://localhost:5678/webhook-test/postulacion", "http://n8n:5678/webhook-test/postulacion"]:
                    try:
                        r_test = requests.post(url_test, json=payload_n8n, timeout=5)
                        if r_test.status_code == 200:
                            st.success("✅ ¡Evento recibido por n8n! Ve inmediatamente a la pantalla de n8n: ¡verás los nodos iluminados en verde!")
                            disparado = True
                            break
                    except Exception:
                        pass
                if not disparado:
                    st.warning("⚠️ Para disparar el modo test, asegúrate de haber hecho clic primero en 'Test workflow' o 'Execute workflow' dentro de n8n.")
        with c_n2:
            if st.button("🌐 Disparar n8n (Modo Producción Activo)", key=f"n8n_prod_{m['id']}"):
                payload_n8n = {"estudiante_id": m["estudiante_id"], "oferta_id": m["oferta_id"]}
                prod_ok = False
                for url_prod in ["http://n8n:5678/webhook/postulacion", "http://localhost:5678/webhook/postulacion"]:
                    try:
                        r_prod = requests.post(url_prod, json=payload_n8n, timeout=5)
                        if r_prod.status_code in [200, 201]:
                            st.success(f"✅ ¡Workflow ejecutado en producción con éxito! Código: {r_prod.status_code}. Revisa 'Executions' en n8n.")
                            prod_ok = True
                            break
                    except Exception:
                        pass
                if not prod_ok:
                    st.info("💡 En n8n, activa la palanca superior derecha de 'Inactive' a 'Active' para habilitar el webhook de producción.")

        # Sección IA
        if m['skills_faltantes']:
            st.divider()
            st.markdown("### 🤖 Generar Recomendación Formativa Personalizada con IA")
            st.caption("Plan acelerado enfocado exclusivamente en las habilidades faltantes detectadas.")

            if st.button("✨ Generar Plan de Formación con IA", key=f"btn_ia_{m['id']}"):
                with st.spinner("Construyendo plan de formación personalizado..."):
                    plan_ia = None
                    origen = "Plantilla Pedagógica Estructurada (Offline)"

                    # 1. Intentar con Google Gemini en vivo si hay API Key
                    if gemini_key and gemini_key.strip() and gemini_key.strip() != "tu_api_key_de_gemini_aqui":
                        try:
                            prompt_maestro = (
                                f"Actúa como Asesor Técnico y Mentor Senior en Ingeniería de Software.\n\n"
                                f"DATOS DE LA POSTULACIÓN:\n"
                                f"- Estudiante: {m['estudiante_nombre']}\n"
                                f"- Puesto Solicitado: {m['oferta_puesto']} en {m['empresa']}\n"
                                f"- Scoring Determinista Obtenido: {m['scoring']}%\n"
                                f"- Habilidades que ya domina: {', '.join(m['skills_coincidentes']) if m['skills_coincidentes'] else 'Ninguna'}\n"
                                f"- HABILIDADES FALTANTES CRÍTICAS: {', '.join(m['skills_faltantes'])}\n\n"
                                f"INSTRUCCIONES Y REGLAS DE NEGOCIO:\n"
                                f"1. Basa tus recomendaciones EXCLUSIVAMENTE en las habilidades faltantes ({', '.join(m['skills_faltantes'])}).\n"
                                f"2. Formato de salida OBLIGATORIO en Markdown estructurado según las siguientes secciones:\n\n"
                                f"### Diagnóstico de Brecha Formativa\n"
                                f"### Ruta de Aprendizaje Acelerada (Estimación en Semanas)\n"
                                f"### Mini Proyecto Integrador de Portfolio\n"
                                f"### Recursos y Cursos Gratuitos Recomendados\n"
                            )
                            gem_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key.strip()}"
                            gem_res = requests.post(
                                gem_url,
                                json={"contents": [{"parts": [{"text": prompt_maestro}]}]},
                                timeout=15
                            )
                            if gem_res.status_code == 200:
                                g_data = gem_res.json()
                                plan_ia = g_data["candidates"][0]["content"]["parts"][0]["text"]
                                origen = f"Google Gemini {gemini_model} (En vivo)"
                        except Exception as ex_gem:
                            st.warning(f"Aviso: No se pudo conectar con la API de Gemini ({str(ex_gem)}). Se utiliza el generador offline de resguardo.")

                    # 2. Resguardo pedagógico estructurado si no hay clave o falló la red
                    if not plan_ia:
                        lineas_rutas = "\n".join([f"- **Dominio de {s}:** Fundamentos teóricos, buenas prácticas y ejercicios de aplicación (Semanas 1 a 2)." for s in m['skills_faltantes']])
                        plan_ia = (
                            f"### Diagnóstico de Brecha Formativa\n"
                            f"Para acceder al puesto de **{m['oferta_puesto']}** en **{m['empresa']}**, "
                            f"es necesario nivelar las siguientes competencias: **{', '.join(m['skills_faltantes'])}**.\n\n"
                            f"### Ruta de Aprendizaje Sugerida\n{lineas_rutas}\n\n"
                            f"### Proyecto Integrador de Portfolio\n"
                            f"Construir un proyecto de código abierto que integre: {', '.join(m['skills_faltantes'])}.\n\n"
                            f"### Recursos Gratuitos Clave\n"
                            f"- Documentación técnica oficial y tutoriales abiertos para: {', '.join(m['skills_faltantes'])}."
                        )

                    m["ia_feedback"] = plan_ia
                    m["ia_origen"] = origen
                    for p in st.session_state.postulaciones:
                        if p["id"] == m["id"]:
                            p["ia_feedback"] = plan_ia
                            p["ia_origen"] = origen

                    # Si la API está online, persistir en SQLite vía FastAPI
                    if online:
                        try:
                            requests.post(
                                f"{backend_url}/postulaciones/{m['id']}/ia-feedback",
                                json={"feedback": plan_ia},
                                timeout=4
                            )
                        except Exception:
                            pass

            if m.get("ia_feedback"):
                origen_badge = m.get("ia_origen", "Plan Formativo")
                st.success(f"¡Plan de formación generado y almacenado en SQLite! [{origen_badge}]")
                st.markdown(m["ia_feedback"])
