# MEMORY.md

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Proyecto con Docker Compose: Streamlit (8501), FastAPI/SQLite (8000) y n8n (5678).
- Frontend dividido por vistas: `frontend/app.py` es el punto de entrada y define la navegación con `st.navigation`/`st.Page`; `common.py` centraliza semillas, estado y helpers; `pages/` contiene `main_page.py` (bienvenida), `postulacion.py`, `estudiantes.py`, `ofertas.py`, `historial.py` y `acerca.py`, cada uno con `render()`; `app.py` importa `from pages...`. `requirements.txt` exige `streamlit>=1.36.0`.
- Validado con `streamlit.testing.v1.AppTest`: las 6 páginas renderizan sin excepciones, con backend online y offline; el match offline devuelve 60% (3/5).
- Backend: estructura `app/database/{database.py,models.py}`, `app/api/`, `app/services/` y `app/schemas.py`. Imports corregidos a `app.database...`; contenedor healthy y endpoints `/health`, `/estudiantes`, `/ofertas` y `/postulaciones` responden 200.
- Modelo de IA unificado en `GEMINI_MODEL=gemini-3.8-flash` (`.env`, `.env.example`, `compose.yaml`, frontend y workflow 2 de n8n).
- `n8n/readme.md` documenta los 3 workflows (evento, datos, validación, respuesta y fallas); cada descripción queda bajo 500 palabras.
- `README1.md` y `prompts/` fueron eliminados; `AGENTS.md` ya no los referencia.
- `README.md` actualizado con la estructura actual (`backend/app/...`, `frontend/pages/`, `st.navigation`) y `GEMINI_MODEL`.

## Decisiones (y por qué)

- Frontend: navegación con `st.navigation`/`st.Page` y un `render()` por módulo; cada `st.Page` usa un `url_path` único porque todos los callables se llaman `render`.
- Backend: ORM separado en `app/database/models.py` y conexión en `app/database/database.py` para no mezclar responsabilidades.
- `init_db()` importa los modelos de forma perezosa (`from app.database import models`) para evitar el ciclo database ↔ models.
- Sin archivo `router.py`: `app/main.py` incluye directamente los routers de `app/api/`.
- Usar `gemini-3.8-flash`: `gemini-1.5-flash` ya no existe y `gemini-2.5-flash` no está disponible para claves nuevas.
- n8n lee el modelo con `$env.GEMINI_MODEL`; requiere `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.
- Se conserva el modo offline del frontend para que la demo funcione sin backend.

## Aprendizajes y errores a evitar

- No versionar claves: `.env.example` tenía una clave real; debe rotarse.
- Dentro del contenedor el WORKDIR es `/app`; los imports deben ser `app...`, no `backend.app...`.
- Streamlit ejecuta con `/app` como raíz; en `frontend/app.py` usar `from pages...`, no `from frontend.pages...`.
- Un directorio `pages/` activa la navegación automática v1; `st.navigation` la desactiva y requiere `url_path` únicos.
- `streamlit.testing.v1.AppTest` permite ejecutar y validar cada vista sin navegador.
- Verificar modelos con `ListModels` antes de asumir un nombre; Google retira modelos y los reemplaza.
- Editar el JSON de un workflow **no** actualiza el workflow ya importado en n8n (vive en el volumen `tp_n8n_data`).
- En Pydantic v2 usar `min_length`, no `min_items`.
- La consola de PowerShell muestra acentos como `�` aunque los archivos estén en UTF-8; no “corregir” la codificación por eso.

## Próximos pasos

- Probar el flujo completo de matching + IA + n8n desde la UI.
- Recrear contenedores: `docker compose up -d --force-recreate n8n frontend`.
- Reimportar o editar el workflow 2 en n8n para que tome `$env.GEMINI_MODEL`.
- Rotar la clave de Gemini que estuvo expuesta.
