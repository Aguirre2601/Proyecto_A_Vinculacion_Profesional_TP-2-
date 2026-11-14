# AGENTS.md

## Proyecto

**Plataforma de Vinculación y Desarrollo Profesional (Proyecto A)** — sistema de matching entre estudiantes universitarios y ofertas laborales.

- **Objetivo:** calcular la compatibilidad técnica de forma determinista, detectar brechas de habilidades, generar un plan formativo con IA y automatizar el flujo con n8n.
- **Stack:** Streamlit (frontend) + FastAPI/SQLAlchemy/SQLite (backend) + n8n (automatización) + Google Gemini 3.8 Flash (IA opcional).
- **Principio central:** el scoring **nunca** lo calcula un LLM. La IA solo redacta el plan de mejora a partir de las habilidades faltantes.
- **Estado:** funcional con Docker Compose (3 servicios). El frontend requiere el backend; si falla, muestra la página global de error.

## Comandos

```bash
# Preparar entorno (una sola vez)
Copy-Item .env.example .env      # Windows PowerShell
cp .env.example .env             # Linux / macOS

# Docker: ciclo de vida
docker compose up -d --build     # construir y levantar
docker compose ps                # estado de contenedores
docker compose logs -f backend   # logs en vivo (Ctrl+C para salir)
docker compose stop              # detener conservando contenedores y datos
docker compose start             # volver a iniciar
docker compose restart backend   # reiniciar un servicio
docker compose down              # eliminar contenedores y red (conserva datos)
docker compose down -v           # DESTRUCTIVO: elimina también el volumen de n8n
docker compose build --no-cache  # reconstruir sin caché
docker compose config --quiet    # validar compose.yaml

# Verificación rápida
curl http://localhost:8000/health
python -m py_compile backend/app/main.py backend/app/database/database.py backend/app/database/models.py backend/app/schemas.py backend/app/api/estudiantes.py backend/app/api/ofertas.py backend/app/api/postulaciones.py backend/app/api/health.py frontend/app.py frontend/common.py frontend/pages/main_page.py frontend/pages/postulacion.py frontend/pages/estudiantes.py frontend/pages/ofertas.py frontend/pages/historial.py frontend/pages/acerca.py frontend/pages/error.py
python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('n8n/*.json')]"
```

**URLs:** frontend `http://localhost:8501` · API `http://localhost:8000` · Swagger `http://localhost:8000/docs` · n8n `http://localhost:5678`.

## Arquitectura

| Servicio | Tecnología | Puerto | Responsabilidad |
|---|---|---|---|
| `frontend` | Streamlit | 8501 | Interfaz de usuario, cliente HTTP del backend y página global de error. |
| `backend` | FastAPI + SQLAlchemy | 8000 | API REST, validación y persistencia SQLite; el scoring lo calcula n8n. |
| `n8n` | n8n | 5678 | Orquestación Low-Code mediante webhooks. |

- **Red Docker:** `app-network` (los servicios se resuelven por nombre: `http://backend:8000`, `http://n8n:5678`).
- **Persistencia:** SQLite en `backend/data/vinculacion.db`, montado desde el host.
- **Volumen n8n:** `tp_n8n_data`.
- **Backend:** entrypoint `uvicorn app.main:app`; `/health` con healthcheck; el frontend espera `service_healthy`.
- **CORS:** abierto (`*`) para permitir Streamlit y n8n.

### Flujo de datos

```text
Streamlit ──► POST /estudiantes | /ofertas ──► FastAPI ──► SQLite
Streamlit ──► POST /webhook/postulacion (Workflow 1) ──► Code node: match determinista
                                                              │
                                                  POST /postulaciones/registrar ──► SQLite
                                                              │
                                          (skills faltantes) ──► Workflow 2 (Gemini)
                                                              │        │
                                                              │        └── POST /postulaciones/{id}/ia-feedback
                                                              │        └── Workflow 3 (notificación simulada)
                                                              │
                                              match + ia_feedback ──► Streamlit

El backend solo persiste el match que calcula n8n; no recalcula el scoring.
```

## Estructura

```text
.
├── compose.yaml                 # Orquestación: n8n + backend + frontend
├── .env.example                 # Plantilla de variables (sin claves reales)
├── .gitignore                   # Excluye .env, SQLite y cachés
├── AGENTS.md                    # Reglas para agentes (este archivo)
├── MEMORY.md                    # Estado y decisiones entre sesiones
├── README.md                    # Documentación del proyecto
├── BitacoraIA.md                # Bitácora de uso de IA
├── backend/
│   ├── app/
│   │   ├── main.py              # Configuración FastAPI + CORS + routers
│   │   ├── schemas.py           # Esquemas Pydantic v2
│   │   ├── database/
│   │   │   ├── database.py      # Engine, sesión, get_db e init_db
│   │   │   └── models.py        # Modelos ORM SQLAlchemy
│   │   ├── api/
│   │   │   ├── estudiantes.py   # Endpoints de estudiantes
│   │   │   ├── ofertas.py       # Endpoints de ofertas
│   │   │   ├── postulaciones.py # Persistencia, historial e ia-feedback
│   │   │   └── health.py        # /health
│   ├── data/                    # SQLite persistente (no versionar .db)
│   └── Dockerfile / requirements.txt / .dockerignore
├── frontend/
│   ├── app.py                   # Punto de entrada: config, sidebar y router
│   ├── common.py                # Datos semilla, estado y helpers compartidos
│   ├── pages/
│   │   ├── main_page.py         # Página de bienvenida
│   │   ├── postulacion.py       # Vista 1: matching y plan IA
│   │   ├── estudiantes.py       # Vista 2: gestión de estudiantes
│   │   ├── ofertas.py           # Vista 3: catálogo de ofertas
│   │   ├── historial.py         # Vista 4: historial y planes IA
│   │   ├── acerca.py            # Vista 5: arquitectura del sistema
│   │   └── error.py             # Página global de error y retorno al inicio
│   ├── Dockerfile / requirements.txt / .dockerignore
└── n8n/
    ├── readme.md                    # Documentación de los workflows
    ├── workflow_1_prescoring.json
    ├── workflow_2_enriquecimiento_ia.json
    └── workflow_3_notificacion_reporte.json
```

## Reglas de negocio

- **Fórmula:** `Scoring = (|Skills Estudiante ∩ Skills Oferta| / |Skills Oferta|) * 100`, redondeada a 2 decimales.
- **Umbral:** `>= 70.0` → `"Apta para entrevista"`; `< 70.0` → `"En desarrollo formativo"`.
- **Comparación de skills:** insensible a mayúsculas/minúsculas y con `strip()`; se conserva el casing de la oferta en la respuesta.
- **Oferta sin skills:** scoring `0.0` (evita división por cero).
- **Validaciones:** al menos 1 skill; nombre 2–120; carrera 3–150; email con `@` (se agrega `.com` si el dominio no tiene punto) y en minúsculas.
- **Email duplicado:** `HTTP 400`. Datos inválidos: `HTTP 422`. Recurso inexistente: `HTTP 404`.
- **Persistencia:** tablas `estudiantes`, `ofertas`, `postulaciones`; las listas de skills se guardan como JSON en columnas `Text`.
- **Trazabilidad:** cada match crea una fila en `postulaciones` con scoring, skills coincidentes/faltantes y estado.
- **Match en n8n:** el frontend llama a `POST /webhook/postulacion`; el Code node del Workflow 1 calcula el match con la fórmula y el umbral, y el resultado se persiste con `POST /postulaciones/registrar`. El backend no recalcula el scoring.

## Integración con IA

- **Proveedor:** Google Gemini, configurado en n8n con la credencial **Header Auth account** (`httpHeaderAuth`, header `x-goog-api-key`) y el modelo fijo `gemini-3.1-flash-lite` en el nodo HTTP Request del Workflow 2. No se usan variables `GEMINI_*` en `.env` ni en `compose.yaml`.
- **Sin credencial o sin red:** el Workflow 1 devuelve el match con `ia_feedback: null` e `ia_error`; la app sigue funcionando y el frontend muestra un aviso.
- **El LLM nunca calcula el scoring ni inventa habilidades.** Solo redacta el plan.
- **Prompt en vivo:** está embebido en el nodo `Armar Prompt con Skills Faltantes` de `n8n/workflow_2_enriquecimiento_ia.json`; su especificación está resumida en este archivo.
- **Especificación del prompt (resumen):**
  - Rol: Asesor Técnico de Empleabilidad y Mentor Senior en Ingeniería de Software.
  - Variables: estudiante, carrera, puesto, empresa, scoring, skills coincidentes y **skills faltantes**.
  - Regla: basar las recomendaciones **exclusivamente** en las skills faltantes.
  - Salida obligatoria en Markdown con: `### Diagnóstico de Brecha Formativa`, `### Ruta de Aprendizaje Acelerada (Estimación en Semanas)`, `### Mini Proyecto Integrador de Portfolio`, `### Recursos y Cursos Gratuitos Recomendados`.
- **n8n:** el Workflow 2 usa la credencial `Header Auth account` y la URL fija `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent`; no requiere `N8N_BLOCK_ENV_ACCESS_IN_NODE`.
- **Seguridad:** la clave vive cifrada en la credencial de n8n; nunca versionarla ni imprimirla. `.env` está en `.gitignore`.

## Automatización n8n

| Workflow | Webhook | Acción |
|---|---|---|
| 1 | `POST /webhook/postulacion` | Calcula el match en un Code node, persiste vía `/postulaciones/registrar` y llama al Workflow 2 si hay skills faltantes. |
| 2 | `POST /webhook/ia-enrichment` | Arma el prompt, llama a Gemini, guarda el feedback y lo devuelve al Workflow 1. |
| 3 | `POST /webhook/notificacion-reporte` | Simula el correo si hay feedback. |

- Los workflows se **importan manualmente** (Workflows → Import from File) y deben quedar **Active**.
- Orden de dependencia: workflow 3 activo ← workflow 2 ← workflow 1.
- **Test:** `/webhook-test/...` requiere clic previo en “Test workflow”. **Producción:** `/webhook/...` requiere workflow activo.
- El envío de correo del workflow 3 es simulado (nodo Set); no envía emails reales.

## Convenciones

- Todos los textos de la interfaz en español.
- Fechas siempre en hora local del sistema.
  - Nota: el código actual usa `datetime.utcnow` (UTC). No cambiar el formato de fechas sin consultar.
- Python con `snake_case`, type hints y docstrings en español.
- Pydantic v2: usar `min_length`/`max_length` (no `min_items`), `field_validator` y `from_attributes`.
- Endpoints REST en español y sustantivos en plural (`/estudiantes`, `/ofertas`, `/postulaciones`).
- La fórmula y el umbral están implementados únicamente en el Code node `Calcular Match Determinista` del Workflow 1; el backend no recalcula el scoring.
- El frontend no usa fallback offline para datos ni scoring: si el backend o n8n fallan, muestra `frontend/pages/error.py`.
- Cada vista del frontend vive en `frontend/pages/` y expone `render()`; `app.py` configura, dibuja la sidebar y define la navegación con `st.navigation`/`st.Page` (cada página con `url_path` único).
- Los errores no controlados y los fallos de guardado se derivan a `frontend/pages/error.py`. Si falla solo la IA, el match se conserva y el frontend muestra `ia_error`.
- No incluir secretos, tokens ni datos personales en el repositorio ni en `MEMORY.md`.

## Forma de trabajar

- Haz solo lo que se te pide; no añadas funciones, refactors ni dependencias por iniciativa propia.
- Lee `MEMORY.md` al empezar y actualízalo al terminar.
- Antes de crear archivos nuevos o cambiar el formato de datos guardados, pregunta.
- Antes de borrar o mover archivos existentes, confirma con el usuario.
- Verifica los cambios con `py_compile`, validación de JSON y `docker compose config --quiet`.
- Si un cambio afecta la UI, mantén el español y el diseño de 5 vistas.
- Si un cambio afecta el scoring, respeta la fórmula y el umbral del 70%.

## Memoria

- Al empezar, lee `MEMORY.md` para conocer el estado del proyecto y las decisiones tomadas.
- Al terminar una tarea, actualízalo: estado actual, decisiones importantes (con su porqué) y errores a evitar.
- Mantenlo breve (máximo ~50 líneas): resume o elimina lo que ya no aporte.
- Si algo se convierte en una regla permanente, propón moverlo a `AGENTS.md` en lugar de dejarlo en la memoria.
- No guardes nunca datos sensibles (claves, tokens, datos personales).

## Límites

- Siempre:.
- Siempre: actualiza `MEMORY.md` al finalizar cada tarea.
- Pregunta antes: de crear archivos nuevos, cambiar el formato de los datos guardados.
- Nunca: añadir dependencias externas, ni usar servicios en la nube, ni guardar datos fuera del archivo SQLite local.
  - La integración existente con Gemini es opcional y ya forma parte del proyecto; no agregar nuevas integraciones cloud.
