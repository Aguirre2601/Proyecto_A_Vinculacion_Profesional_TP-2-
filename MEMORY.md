# MEMORY.md

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Proyecto funcional con Docker Compose: Streamlit (8501), FastAPI/SQLite (8000) y n8n (5678).
- `AGENTS.md` completado con arquitectura, comandos, reglas de negocio, IA, n8n y convenciones.
- Modelo de IA unificado en `GEMINI_MODEL=gemini-3.8-flash` (`.env`, `.env.example`, `compose.yaml`, `frontend/app.py` y workflow 2 de n8n).
- Correcciones previas: clave real eliminada de `.env.example`; `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`; healthcheck del backend; `.gitignore`, `.dockerignore` y `backend/data/.gitkeep`; `min_items` → `min_length`.
- `README1.md` y `prompts/` fueron eliminados; `AGENTS.md` ya no los referencia.
- Validado: `py_compile`, JSON del workflow 2, `docker compose config --quiet` y una llamada real a Gemini con `gemini-3.8-flash` (respuesta OK).

## Decisiones (y por qué)

- Usar `gemini-3.8-flash`: `gemini-1.5-flash` ya no existe y `gemini-2.5-flash` no está disponible para claves nuevas; la propia API recomienda 3.8.
- El modelo se lee de `GEMINI_MODEL` con default `gemini-3.8-flash`, para poder cambiarlo sin tocar código.
- n8n lee el modelo con `$env.GEMINI_MODEL`; requiere `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.
- Los workflows de n8n se importan manualmente para evitar duplicados en cada arranque.
- Se conserva el modo offline del frontend para que la demo funcione sin backend.
- No se cambia el formato de fechas (código usa UTC y la convención pide hora local) sin consultar.

## Aprendizajes y errores a evitar

- No versionar claves: `.env.example` tenía una clave real; debe rotarse.
- Verificar modelos con `ListModels` antes de asumir un nombre; Google retira modelos y los reemplaza.
- Editar el JSON de un workflow **no** actualiza el workflow ya importado en n8n (vive en el volumen `tp_n8n_data`).
- En Pydantic v2 usar `min_length`, no `min_items`.
- La consola de PowerShell muestra acentos como `�` aunque los archivos estén en UTF-8; no “corregir” la codificación por eso.

## Próximos pasos

- Recrear contenedores: `docker compose up -d --force-recreate n8n frontend`.
- Reimportar o editar el workflow 2 en n8n para que tome `$env.GEMINI_MODEL`.
- Rotar la clave de Gemini que estuvo expuesta.
