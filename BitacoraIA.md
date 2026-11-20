## Bitacora IA

---

## Registro de uso de IA

| Prompt | Estado | Verificación |
|--------|--------|--------------|
| "Actualiza el Agents.md, el README.md y el  frontend/pages/acerca.py , MEMORY.md  y el comando py_complie . RE build el backend y proba /health " | Aceptado | Se observaron los cambios en cada archivo correspondiente y el estado de /health. |
| "Revisá por qué el backend no encuentra los módulos después de mover la API a `backend/app/api/`; indicá qué imports y entrypoint hay que corregir." | Aceptado | Se comparó `backend/app/main.py`, `backend/app/api/postulaciones.py` y `backend/Dockerfile`; se confirmó `uvicorn app.main:app` y los imports `app...`. |
| "Implementá `POST /postulaciones/registrar` para persistir el match que calcula n8n, sin recalcular el scoring en FastAPI." | Aceptado | Se probó con `curl` y se consultó la tabla `postulaciones` en `backend/data/vinculacion.db`; el scoring persistido coincidió con el enviado. |
| "Verificá el flujo completo con la credencial Header Auth de n8n: match, persistencia y plan IA con `ia_origen`; dejá evidencia en la bitácora." | Aceptado | Se ejecutó el flujo Workflow 1 → 2 → 3; resultado: 60 %, `ia_origen: Google Gemini gemini-3.1-flash-lite`, `ia_error: null`; se revisaron las ejecuciones en n8n. |

---
