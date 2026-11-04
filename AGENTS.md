# AGENTS.md

## Proyecto

**Plataforma de Vinculación y Desarrollo Profesional (Proyecto A)** — sistema de matching entre estudiantes universitarios y ofertas laborales.

- **Objetivo:** calcular la compatibilidad técnica de forma determinista, detectar brechas de habilidades, generar un plan formativo con IA y automatizar el flujo con n8n.
- **Stack:** Streamlit (frontend) + FastAPI/SQLAlchemy/SQLite (backend) + n8n (automatización) + Google Gemini 1.5 Flash (IA opcional).
- **Principio central:** el scoring **nunca** lo calcula un LLM. La IA solo redacta el plan de mejora a partir de las habilidades faltantes.
- **Estado:** funcional con Docker Compose (3 servicios). El frontend tiene modo autónomo en memoria si el backend no responde.

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
python -m py_compile backend/main.py backend/models.py backend/database.py backend/services/matcher.py frontend/app.py
python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('n8n/*.json')]"
```

**URLs:** frontend `http://localhost:8501` · API `http://localhost:8000` · Swagger `http://localhost:8000/docs` · n8n `http://localhost:5678`.

## Arquitectura

| Servicio | Tecnología | Puerto | Responsabilidad |
|---|---|---|---|
| `frontend` | Streamlit | 8501 | Interfaz de usuario, fallback offline, cliente HTTP del backend. |
| `backend` | FastAPI + SQLAlchemy | 8000 | API REST, validación, scoring determinista, persistencia SQLite. |
| `n8n` | n8n | 5678 | Orquestación Low-Code mediante webhooks. |

- **Red Docker:** `app-network` (los servicios se resuelven por nombre: `http://backend:8000`, `http://n8n:5678`).
- **Persistencia:** SQLite en `backend/data/vinculacion.db`, montado desde el host.
- **Volumen n8n:** `tp_n8n_data`.
- **Backend:** `/health` con healthcheck; el frontend espera `service_healthy`.
- **CORS:** abierto (`*`) para permitir Streamlit y n8n.

### Flujo de datos

```text
Streamlit ──► POST /estudiantes | /ofertas | /postulaciones/match ──► FastAPI
                                                                      │
                                                        matcher.py (puro)
                                                                      │
                                                                   SQLite
                                                                      │
                                     (scoring < 70%) ──► plan IA ──► POST /postulaciones/{id}/ia-feedback

n8n: workflow 1 (pre-scoring) ──► workflow 2 (IA) ──► workflow 3 (notificación simulada)
```

## Estructura

```text
.
├── compose.yaml                 # Orquestación: n8n + backend + frontend
├── .env.example                 # Plantilla de variables (sin claves reales)
├── .gitignore                   # Excluye .env, SQLite y cachés
├── AGENTS.md                    # Reglas para agentes (este archivo)
├── MEMORY.md                    # Estado y decisiones entre sesiones
├── README.md / README1.md       # Documentación del proyecto
├── BitacoraIA.md                # Bitácora de uso de IA
├── backend/
│   ├── main.py                  # Endpoints FastAPI
│   ├── models.py                # Esquemas Pydantic v2
│   ├── database.py              # ORM SQLAlchemy + datos semilla
│   ├── services/matcher.py      # Algoritmo determinista puro
│   ├── data/                    # SQLite persistente (no versionar .db)
│   ├── Dockerfile / requirements.txt / .dockerignore
├── frontend/
│   ├── app.py                   # 5 vistas Streamlit + prompt IA en vivo
│   ├── Dockerfile / requirements.txt / .dockerignore
├── n8n/
│   ├── workflow_1_prescoring.json
│   ├── workflow_2_enriquecimiento_ia.json
│   └── workflow_3_notificacion_reporte.json
└── prompts/
    └── prompt_maestro_llm.md    # Referencia del prompt (consolidado en este archivo)
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

## Integración con IA

- **Proveedor:** Google Gemini 1.5 Flash, clave opcional en `GEMINI_API_KEY` (`.env`).
- **Sin clave o sin red:** el frontend usa una plantilla pedagógica offline; la app debe seguir funcionando.
- **El LLM nunca calcula el scoring ni inventa habilidades.** Solo redacta el plan.
- **Prompt en vivo:** está embebido en `frontend/app.py` (vista de matching). `prompts/prompt_maestro_llm.md` es solo referencia.
- **Especificación del prompt (resumen):**
  - Rol: Asesor Técnico de Empleabilidad y Mentor Senior en Ingeniería de Software.
  - Variables: estudiante, carrera, puesto, empresa, scoring, skills coincidentes y **skills faltantes**.
  - Regla: basar las recomendaciones **exclusivamente** en las skills faltantes.
  - Salida obligatoria en Markdown con: `### Diagnóstico de Brecha Formativa`, `### Ruta de Aprendizaje Acelerada (Estimación en Semanas)`, `### Mini Proyecto Integrador de Portfolio`, `### Recursos y Cursos Gratuitos Recomendados`.
- **n8n:** el workflow 2 lee `$env.GEMINI_API_KEY`; requiere `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` en `compose.yaml`.
- **Seguridad:** nunca versionar ni imprimir la clave. `.env` está en `.gitignore`.

## Automatización n8n

| Workflow | Webhook | Acción |
|---|---|---|
| 1 | `POST /webhook/postulacion` | Llama a `/postulaciones/match` y bifurca por scoring. |
| 2 | `POST /webhook/ia-enrichment` | Arma el prompt, llama a Gemini y guarda el feedback. |
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
- La lógica determinista vive en `backend/services/matcher.py` y debe permanecer pura (sin DB ni HTTP).
- Mantener el modo offline del frontend; no romper la demo sin backend.
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
