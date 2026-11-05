# MEMORY.md

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Proyecto funcional con Docker Compose: Streamlit (8501), FastAPI/SQLite (8000) y n8n (5678).
- Backend reorganizado en el paquete `backend/app/`: `main.py` solo configura FastAPI/CORS/routers; endpoints en `app/api/`; ORM en `app/models.py`; Pydantic en `app/schemas.py`; conexión en `app/basededatos.py`; matcher en `app/services/`.
- Archivos viejos de `backend/` eliminados (`main.py`, `models.py`, `database.py`, `services/`). Dockerfile usa `uvicorn app.main:app`.
- Modelo de IA unificado en `GEMINI_MODEL=gemini-3.8-flash` (`.env`, `.env.example`, `compose.yaml`, `frontend/app.py` y workflow 2 de n8n).
- `README1.md` y `prompts/` fueron eliminados; `AGENTS.md` ya no los referencia.
- Validado: backend reconstruido, contenedor healthy y endpoints `/estudiantes`, `/ofertas`, `/postulaciones/match` y `/postulaciones` responden 200.

## Decisiones (y por qué)

- Migración opción A: ORM separado (`models.py`) de la conexión (`basededatos.py`) para evitar mezclar responsabilidades.
- `init_db()` importa los modelos de forma perezosa (`from app import models`) para evitar el ciclo basededatos ↔ models.
- Sin archivo `router.py`: `app/main.py` incluye directamente los routers de `app/api/`.
- Usar `gemini-3.8-flash`: `gemini-1.5-flash` ya no existe y `gemini-2.5-flash` no está disponible para claves nuevas.
- El modelo se lee de `GEMINI_MODEL` con default `gemini-3.8-flash`.
- n8n lee el modelo con `$env.GEMINI_MODEL`; requiere `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.
- Se conserva el modo offline del frontend para que la demo funcione sin backend.

## Aprendizajes y errores a evitar

- No versionar claves: `.env.example` tenía una clave real; debe rotarse.
- Verificar modelos con `ListModels` antes de asumir un nombre; Google retira modelos y los reemplaza.
- Editar el JSON de un workflow **no** actualiza el workflow ya importado en n8n (vive en el volumen `tp_n8n_data`).
- En Pydantic v2 usar `min_length`, no `min_items`.
- Al mover el backend a `app/`, actualizar el `CMD` del Dockerfile a `app.main:app` y todos los imports a `from app...`.
- La consola de PowerShell muestra acentos como `�` aunque los archivos estén en UTF-8; no “corregir” la codificación por eso.

## Próximos pasos

- Actualizar las rutas viejas que aún figuran en `README.md`.
- Recrear contenedores: `docker compose up -d --force-recreate n8n frontend`.
- Reimportar o editar el workflow 2 en n8n para que tome `$env.GEMINI_MODEL`.
- Rotar la clave de Gemini que estuvo expuesta.
