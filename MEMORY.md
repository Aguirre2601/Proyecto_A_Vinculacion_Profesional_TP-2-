# MEMORY.md

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Proyecto funcional con Docker Compose: Streamlit (8501), FastAPI/SQLite (8000) y n8n (5678).
- `README1.md` creado con documentación completa (objetivo, componentes, requisitos, instalación, ejecución, comandos Docker, estructura).
- `AGENTS.md` completado con arquitectura, comandos, reglas de negocio, IA, n8n y convenciones.
- Correcciones aplicadas: clave real eliminada de `.env.example`; `GEMINI_API_KEY` y `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` añadidos a n8n; healthcheck del backend; `.gitignore`, `.dockerignore` y `backend/data/.gitkeep`; `min_items` → `min_length`.
- Validado: `py_compile`, JSON de workflows y `docker compose config --quiet`.

## Decisiones (y por qué)

- No mover ni renombrar carpetas: `backend/`, `frontend/`, `n8n/` ya son correctas.
- Los workflows de n8n se importan manualmente para evitar duplicados en cada arranque.
- Se conserva el modo offline del frontend para que la demo funcione sin backend.
- El prompt del LLM se documentó en `AGENTS.md`.
- No se cambia el formato de fechas (código usa UTC y la convención pide hora local) sin consultar.

## Aprendizajes y errores a evitar

- No versionar claves: `.env.example` tenía una clave real; debe rotarse.
- n8n bloquea `$env` por defecto; el workflow 2 necesita `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.
- En Pydantic v2 usar `min_length`, no `min_items`.
- La consola de PowerShell muestra acentos como `�` aunque los archivos estén en UTF-8; no “corregir” la codificación por eso.

## Próximos pasos

- Eliminar `prompts/prompt_maestro_llm.md` cuando el usuario lo confirme (contenido consolidado en `AGENTS.md`).
- Rotar la clave de Gemini que estuvo expuesta.
- Opcional: ejecutar `docker compose up -d --build` y probar el flujo completo.
