"""
app.py - Frontend en Streamlit para la Plataforma de Vinculación Profesional
Proyecto A: Arquitectura Desacoplada con Soporte Dual (API REST + Modo Autónomo Integrado)
"""
import os
import json
import requests
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Plataforma de Vinculación Profesional",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Datos semilla locales para resguardo en caso de backend sin conexión
SEED_ESTUDIANTES = [
    {
        "id": 1,
        "nombre": "Valeria Gómez",
        "email": "valeria.gomez@universidad.edu.ar",
        "carrera": "Ingeniería en Sistemas de Información",
        "skills": ["Python", "SQL", "FastAPI", "Git"]
    },
    {
        "id": 2,
        "nombre": "Lucas Morales",
        "email": "lucas.morales@universidad.edu.ar",
        "carrera": "Licenciatura en Ciencias de la Computación",
        "skills": ["JavaScript", "React", "HTML", "CSS", "Git"]
    },
    {
        "id": 3,
        "nombre": "Sofía Benítez",
        "email": "sofia.benitez@universidad.edu.ar",
        "carrera": "Ingeniería Informática",
        "skills": ["Python", "Docker", "PostgreSQL", "Linux", "FastAPI", "Pandas"]
    }
]

SEED_OFERTAS = [
    {
        "id": 1,
        "puesto": "Desarrollador Backend Junior (Python / FastAPI)",
        "empresa": "Fintech Innova",
        "descripcion": "Desarrollo de microservicios transaccionales con FastAPI y Docker.",
        "skills_requeridas": ["Python", "FastAPI", "Docker", "PostgreSQL", "Git"]
    },
    {
        "id": 2,
        "puesto": "Data Engineer Trainee",
        "empresa": "DataCloud Analytics",
        "descripcion": "Construcción de pipelines ETL y consultas analíticas.",
        "skills_requeridas": ["Python", "SQL", "Pandas", "Docker", "Airflow"]
    },
    {
        "id": 3,
        "puesto": "Fullstack Developer Jr",
        "empresa": "AgileTech Solutions",
        "descripcion": "Integración de frontend React con backend FastAPI.",
        "skills_requeridas": ["Python", "FastAPI", "JavaScript", "React", "Docker"]
    }
]

# Inicializar sesión local
if "estudiantes" not in st.session_state:
    st.session_state.estudiantes = list(SEED_ESTUDIANTES)

if "ofertas" not in st.session_state:
    st.session_state.ofertas = list(SEED_OFERTAS)

if "postulaciones" not in st.session_state:
    st.session_state.postulaciones = []

# Configuración de URL de Backend
default_env_url = os.getenv("BACKEND_API_URL", "http://backend:8000")

# Barra lateral de navegación
st.sidebar.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
st.sidebar.title("TP: Vinculación Profesional")
st.sidebar.caption("Proyecto A - Arquitectura con Separación de Responsabilidades")

menu = st.sidebar.radio(
    "Navegación",
    [
        "🎯 Postulación y Matching",
        "👨‍🎓 Gestión de Estudiantes",
        "💼 Catálogo de Ofertas",
        "📋 Historial y Planes IA",
        "ℹ️ Acerca del Sistema"
    ]
)

st.sidebar.divider()
st.sidebar.subheader("⚙️ Estado de Conexión")
backend_url_input = st.sidebar.text_input(
    "URL Backend FastAPI:",
    value=default_env_url,
    help="Usa http://backend:8000 en Docker o http://localhost:8000 en tu máquina."
).rstrip("/")

# Configuración de IA (Google Gemini)
gemini_env_key = os.getenv("GEMINI_API_KEY", "")
if gemini_env_key == "tu_api_key_de_gemini_aqui":
    gemini_env_key = ""

gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"

st.sidebar.divider()
st.sidebar.subheader("🤖 Motor de IA (Google Gemini)")
gemini_key_input = st.sidebar.text_input(
    "API Key de Gemini (Opcional):",
    value=gemini_env_key,
    type="password",
    help="Obtén tu clave gratis en https://aistudio.google.com/. Si la dejas vacía, se usará el generador pedagógico offline."
)

if gemini_key_input:
    st.sidebar.success(f"🟢 {gemini_model} Conectado")
else:
    st.sidebar.info("🟡 Modo IA Offline (Plantilla Estructurada)")

# Comprobar si el backend FastAPI responde
api_online = False
try:
    test_res = requests.get(f"{backend_url_input}/health", timeout=1.5)
    if test_res.status_code == 200:
        api_online = True
except Exception:
    # Intentar con localhost si backend falló (ejecución sin Docker)
    if "backend:8000" in backend_url_input:
        try:
            local_test = requests.get("http://localhost:8000/health", timeout=1.5)
            if local_test.status_code == 200:
                backend_url_input = "http://localhost:8000"
                api_online = True
        except Exception:
            pass

BACKEND_URL = backend_url_input

if api_online:
    st.sidebar.success(f"🟢 Backend Conectado ({BACKEND_URL})")
    st.sidebar.caption("💾 Base de datos SQLite persistente activa.")
else:
    st.sidebar.error(f"🔴 Backend Desconectado ({BACKEND_URL})")
    st.sidebar.caption("⚠️ Advertencia: Guardado temporal en memoria RAM. Para persistir datos permanentemente, inicia el Backend.")

# Algoritmo determinista local de resguardo
def match_determinista(student_skills: list, required_skills: list):
    student_set = {s.strip().lower() for s in student_skills if s and s.strip()}
    matching = [s.strip() for s in required_skills if s.strip().lower() in student_set]
    missing = [s.strip() for s in required_skills if s.strip().lower() not in student_set]
    total = len(matching) + len(missing)
    if total == 0:
        return 0.0, [], [], "(0 / 0) * 100 = 0.0%"
    score = round((len(matching) / total) * 100.0, 2)
    formula = f"({len(matching)} / {total}) * 100 = {score}%"
    return score, matching, missing, formula


# Obtener estudiantes (API SQLite o Memoria)
def obtener_estudiantes():
    if api_online:
        try:
            r = requests.get(f"{BACKEND_URL}/estudiantes", timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    return st.session_state.estudiantes


# Obtener ofertas (API SQLite o Memoria)
def obtener_ofertas(filtro_puesto=None, filtro_empresa=None):
    if api_online:
        try:
            params = {}
            if filtro_puesto:
                params["puesto"] = filtro_puesto
            if filtro_empresa:
                params["empresa"] = filtro_empresa
            r = requests.get(f"{BACKEND_URL}/ofertas", params=params, timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    
    res = list(st.session_state.ofertas)
    if filtro_puesto:
        res = [o for o in res if filtro_puesto.lower() in o["puesto"].lower()]
    if filtro_empresa:
        res = [o for o in res if filtro_empresa.lower() in o["empresa"].lower()]
    return res


# =========================================================================
# VISTA 1: POSTULACIÓN Y CÁLCULO DETERMINISTA
# =========================================================================
if menu == "🎯 Postulación y Matching":
    st.title("🎯 Postulación y Cálculo Determinista de Compatibilidad")
    st.markdown("Esta vista ejecuta el cálculo matemático determinista:")
    st.info("Fórmula oficial evaluada: **Scoring = (|Skills Estudiante ∩ Skills Oferta| / |Skills Oferta|) * 100**")

    estudiantes = obtener_estudiantes()
    ofertas = obtener_ofertas()

    if not estudiantes or not ofertas:
        st.warning("⚠️ Debes tener al menos un estudiante y una oferta registrados.")
    else:
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
                if api_online:
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/postulaciones/match",
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
                        if gemini_key_input and gemini_key_input.strip() and gemini_key_input.strip() != "tu_api_key_de_gemini_aqui":
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
                                gem_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key_input.strip()}"
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
                        if api_online:
                            try:
                                requests.post(
                                    f"{BACKEND_URL}/postulaciones/{m['id']}/ia-feedback",
                                    json={"feedback": plan_ia},
                                    timeout=4
                                )
                            except Exception:
                                pass

                if m.get("ia_feedback"):
                    origen_badge = m.get("ia_origen", "Plan Formativo")
                    st.success(f"¡Plan de formación generado y almacenado en SQLite! [{origen_badge}]")
                    st.markdown(m["ia_feedback"])


# =========================================================================
# VISTA 2: GESTIÓN DE ESTUDIANTES
# =========================================================================
elif menu == "👨‍🎓 Gestión de Estudiantes":
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

                if api_online:
                    try:
                        resp = requests.post(f"{BACKEND_URL}/estudiantes", json=payload, timeout=4)
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


# =========================================================================
# VISTA 3: CATÁLOGO DE OFERTAS
# =========================================================================
elif menu == "💼 Catálogo de Ofertas":
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
                    if api_online:
                        try:
                            resp_ofr = requests.post(f"{BACKEND_URL}/ofertas", json=payload_ofr, timeout=4)
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
                        st.warning(f"⚠️ Oferta guardada SOLO TEMPORALMENTE en RAM de la pestaña. Conecta el Backend para persistir permanentemente en SQLite.")

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


# =========================================================================
# VISTA 4: HISTORIAL Y PLANES IA
# =========================================================================
elif menu == "📋 Historial y Planes IA":
    st.title("📋 Historial de Postulaciones y Recomendaciones LLM")
    st.markdown("Consulta de postulaciones registradas con sus planes formativos persistidos en base de datos.")

    postulaciones_db = []
    if api_online:
        try:
            r = requests.get(f"{BACKEND_URL}/postulaciones", timeout=3)
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


# =========================================================================
# VISTA 5: ACERCA DEL SISTEMA Y ARQUITECTURA
# =========================================================================
elif menu == "ℹ️ Acerca del Sistema":
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
