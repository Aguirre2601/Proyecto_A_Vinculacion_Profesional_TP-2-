# MEMORY.md

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual

- Proyecto con Docker Compose: Streamlit (8501), FastAPI/SQLite (8000) y n8n (5678).
- Frontend dividido por vistas: `frontend/app.py` es el punto de entrada y define la navegación con `st.navigation`/`st.Page`; `common.py` centraliza estado y helpers; `pages/` contiene `main_page.py` (bienvenida), `postulacion.py`, `estudiantes.py`, `ofertas.py`, `historial.py`, `acerca.py` y `error.py`, cada uno con `render()`; `app.py` importa `from pages...`. `requirements.txt` exige `streamlit>=1.36.0`.
- Validado con `streamlit.testing.v1.AppTest`: las vistas renderizan sin excepciones; `error.py` redirige y vuelve al inicio; el match se calcula en n8n Workflow 1 y los fallos se derivan a `error.py`.
- Backend: estructura `app/database/{database.py,models.py}`, `app/api/` y `app/schemas.py`. Se eliminó `app/services/matcher.py` y el endpoint `/postulaciones/match`; el backend solo persiste el match de n8n. Endpoints `/health`, `/estudiantes`, `/ofertas`, `/postulaciones` y `/postulaciones/registrar` responden.
- IA configurada en n8n: credencial `Header Auth account` (`httpHeaderAuth`, id `tRgxbBB45n5mrOcZ`, header `x-goog-api-key`) y modelo fijo `gemini-3.1-flash-lite` en la URL del nodo HTTP Request del Workflow 2. No hay variables `GEMINI_*` en `.env`, `.env.example` ni `compose.yaml`.
- `n8n/readme.md` documenta los 3 workflows (evento, datos, validación, respuesta y fallas); cada descripción queda bajo 500 palabras.
- `README1.md` y `prompts/` fueron eliminados; `AGENTS.md` ya no los referencia.
- `README.md` actualizado con la estructura actual (`backend/app/...`, `frontend/pages/`, `st.navigation`) y la configuración de Gemini en n8n.
- Contenedores recreados sin variables `GEMINI_*`; backend/frontend healthy y n8n responde 200. El Workflow 2 activo (`2T30jWBDDKcEejwI`) usa Header Auth y la URL fija de Gemini.
- Flujo completo probado tras el cambio a Header Auth: el Workflow 1 calcula el match, persiste y el Workflow 2 devuelve `ia_feedback` con `ia_origen: Google Gemini gemini-3.1-flash-lite` (Valeria vs Backend: 60% + plan real). La credencial `Header Auth account` tenía el header `KeyLowCode`; se corrigió a `x-goog-api-key`. Quedan 3 workflows activos: `j0jBbSZYQFeF4b1q` (W1), `2T30jWBDDKcEejwI` (W2) y `gM14StIzDBM91hH3` (W3).

## Decisiones (y por qué)

- Frontend: navegación con `st.navigation`/`st.Page` y un `render()` por módulo; cada `st.Page` usa un `url_path` único porque todos los callables se llaman `render`.
- Error global: `error.py` es una página oculta de `st.navigation`; `common.ir_a_error()` guarda el detalle y usa `st.switch_page` para volver al inicio. Los fallos de backend se derivan a `error.py`.
- Backend: ORM separado en `app/database/models.py` y conexión en `app/database/database.py` para no mezclar responsabilidades.
- `init_db()` importa los modelos de forma perezosa (`from app.database import models`) para evitar el ciclo database ↔ models.
- Sin archivo `router.py`: `app/main.py` incluye directamente los routers de `app/api/`.
- Usar `gemini-3.1-flash-lite` para la demo: `gemini-3.8-flash` está saturado y devuelve 503/timeout; `gemini-1.5-flash` ya no existe y `gemini-2.5-flash` no está disponible para claves nuevas.
- n8n usa la credencial `Header Auth account` y la URL fija `.../models/gemini-3.1-flash-lite:generateContent`; no requiere `N8N_BLOCK_ENV_ACCESS_IN_NODE`.
- Se deshabilitó el fallback offline de datos y scoring: sin backend se muestra `error.py`; solo Gemini y n8n conservan su fallback.
- El frontend llama a `POST /webhook/postulacion` (Workflow 1) con los objetos completos `estudiante` y `oferta`; el Workflow 1 calcula el match en un Code node, persiste con `POST /postulaciones/registrar` y, si hay skills faltantes, llama al Workflow 2, que devuelve `ia_feedback` e `ia_origen`.

## Aprendizajes y errores a evitar

- No versionar claves: `.env.example` tenía una clave real; debe rotarse.
- Dentro del contenedor el WORKDIR es `/app`; los imports deben ser `app...`, no `backend.app...`.
- Streamlit ejecuta con `/app` como raíz; en `frontend/app.py` usar `from pages...`, no `from frontend.pages...`.
- Un directorio `pages/` activa la navegación automática v1; `st.navigation` la desactiva y requiere `url_path` únicos.
- Para cambiar a una página definida por callable hay que pasar el objeto `st.Page` a `st.switch_page`, no una ruta.
- `streamlit.testing.v1.AppTest` permite ejecutar y validar cada vista sin navegador.
- Verificar modelos con `ListModels` antes de asumir un nombre; Google retira modelos y los reemplaza.
- Editar el JSON de un workflow **no** actualiza el workflow ya importado en n8n (vive en el volumen `tp_n8n_data`).
- Para actualizar un workflow activo sin duplicarlo: `PUT /api/v1/workflows/{id}` con una API key temporal con scopes `workflow:read`, `workflow:update` y `workflow:activate`; el `PUT` re-publica la versión activa.
- Header Auth para Gemini: el header debe ser `x-goog-api-key`; un nombre distinto (p. ej. `KeyLowCode`) devuelve `403 Permission denied on the service`.
- Reimportar con `n8n import:workflow` crea un ID nuevo y deja el anterior inactivo; verificar `n8n list:workflow` y eliminar duplicados para evitar colisiones de webhook.
- En Pydantic v2 usar `min_length`, no `min_items`.
- La consola de PowerShell muestra acentos como `�` aunque los archivos estén en UTF-8; no “corregir” la codificación por eso.

## Próximos pasos

- Rotar la clave de Gemini que estuvo expuesta y actualizar la credencial `Header Auth account` si cambia.
- Probar el botón desde la UI real (`http://localhost:8501/postulacion`).
