# Workflows de n8n

Automatización del flujo de postulaciones: pre-scoring determinista, enriquecimiento con IA y notificación simulada.

**Requisitos:** `GEMINI_API_KEY` y `GEMINI_MODEL` en `.env`; `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`; workflows importados y **Active**. Dependencia: Workflow 3 activo ← Workflow 2 ← Workflow 1.

| Workflow | Webhook | Acción |
|---|---|---|
| 1. Pre-scoring | `POST /webhook/postulacion` | Llama a `/postulaciones/match` y bifurca por scoring |
| 2. Enriquecimiento IA | `POST /webhook/ia-enrichment` | Genera el plan con Gemini y lo guarda |
| 3. Notificación | `POST /webhook/notificacion-reporte` | Simula el envío del informe |

---

## Workflow 1 — Ingreso y Pre-scoring Determinista

**1. Evento que inicia el flujo:** webhook `POST /webhook/postulacion` (test: `/webhook-test/postulacion`). Usa `responseMode: responseNode`.

**2. Datos de entrada:**

```json
{ "estudiante_id": 1, "oferta_id": 1 }
```

**3. Validación y transformación:** n8n reenvía el body a `POST http://backend:8000/postulaciones/match`. El backend valida con Pydantic (`MatchRequest`, IDs `> 0`), calcula el scoring determinista y persiste. Luego el nodo IF evalúa `scoring >= 70`; los nodos Set agregan `resultado` y `mensaje` (`APTA_PARA_ENTREVISTA` o `EN_DESARROLLO_FORMATIVO`). Si el scoring es menor a 70, n8n llama al Workflow 2 con `postulacion_id`, `estudiante_id`, `estudiante_nombre`, `oferta_puesto`, `empresa`, `scoring`, `skills_coincidentes` y `skills_faltantes`.

**4. Respuesta devuelta:**

```json
{
  "status": "ok",
  "postulacion_id": 1,
  "scoring": 60.0,
  "estado": "En desarrollo formativo",
  "detalles": {}
}
```

`detalles` contiene la salida del Set si el scoring es ≥ 70, o la respuesta del Workflow 2 si es menor.

**5. Reconocimiento de fallas:** sin rama de error ni logging propio. Si el backend falla o supera el timeout de 10 s, la ejecución se detiene y queda en rojo en **Executions**; el cliente recibe el error por defecto de n8n. No hay reintentos ni `onError`.

---

## Workflow 2 — Agente de Enriquecimiento con IA

**1. Evento que inicia el flujo:** webhook `POST /webhook/ia-enrichment`, invocado por el Workflow 1 cuando el scoring es menor a 70 (también manual).

**2. Datos de entrada:**

```json
{
  "postulacion_id": 1,
  "estudiante_id": 1,
  "estudiante_nombre": "Valeria Gómez",
  "oferta_puesto": "Backend Junior",
  "empresa": "Fintech Innova",
  "scoring": 60.0,
  "skills_coincidentes": ["Python"],
  "skills_faltantes": ["Docker", "PostgreSQL"]
}
```

**3. Validación y transformación:** el nodo Set construye `prompt_construido` con los datos y las skills faltantes. Luego se llama a Gemini (`/v1beta/models/{GEMINI_MODEL}:generateContent`) con el prompt escapado. El texto generado se envía a `POST http://backend:8000/postulaciones/{id}/ia-feedback`; el backend valida con Pydantic (`IAFeedbackRequest`, mínimo 5 caracteres) y verifica que la postulación exista. Finalmente se dispara el Workflow 3. El prompt de n8n es una versión reducida del usado en el frontend: no incluye carrera ni recursos gratuitos.

**4. Respuesta devuelta:**

```json
{ "status": "enriquecido", "postulacion_id": 1, "feedback_guardado": true }
```

`feedback_guardado` está hardcodeado; no se verifica la respuesta real del backend.

**5. Reconocimiento de fallas:** si falta la clave/modelo, Gemini devuelve 4xx; si supera el timeout de 20 s o el backend rechaza el feedback, la ejecución se detiene y **no se llama al Workflow 3**. No hay fallback offline ni reintentos. La falla queda en **Executions** y en `docker compose logs n8n`.

---

## Workflow 3 — Notificación y Reporte Condicional

**1. Evento que inicia el flujo:** webhook `POST /webhook/notificacion-reporte`, invocado por el Workflow 2 tras guardar el feedback.

**2. Datos de entrada:**

```json
{
  "postulacion_id": 1,
  "estudiante_nombre": "Valeria Gómez",
  "oferta_puesto": "Backend Junior",
  "feedback": "### Diagnóstico de Brecha Formativa..."
}
```

**3. Validación y transformación:** el nodo IF comprueba que `body.feedback` no esté vacío. Si existe, el Set arma `correo_asunto`, `correo_cuerpo_html` y `estado_envio = "SIMULADO_ENVIADO_EXITOSAMENTE"`. Si no existe, devuelve `estado_envio = "OMITIDO_SIN_FEEDBACK"` y un `motivo`. No se envía un correo real.

**4. Respuesta devuelta:**

```json
{
  "status": "completado",
  "resultado": {
    "correo_asunto": "Tu Plan Personalizado de Desarrollo Profesional - Postulación #1",
    "correo_cuerpo_html": "<div>...</div>",
    "estado_envio": "SIMULADO_ENVIADO_EXITOSAMENTE"
  }
}
```

Sin feedback, `resultado` contiene `estado_envio: "OMITIDO_SIN_FEEDBACK"` y `motivo`.

**5. Reconocimiento de fallas:** la rama sin feedback no es un error, es una bifurcación de negocio. Un body inválido hace fallar el webhook. Al no enviarse correos reales no hay errores SMTP. Sin rama de error ni logging propio; se consulta **Executions**.

---

## Fallas generales y pruebas

Los tres workflows usan el manejo por defecto de n8n: un HTTP no-2xx detiene la ejecución, que queda registrada en **Executions**; no hay `errorWorkflow`, `onError`, `continueOnFail` ni `retryOnFail`. Los logs se ven con `docker compose logs -f n8n`.

```bash
# Workflow 1
curl -X POST http://localhost:5678/webhook/postulacion \
  -H "Content-Type: application/json" \
  -d '{"estudiante_id":1,"oferta_id":1}'

# Workflow 3
curl -X POST http://localhost:5678/webhook/notificacion-reporte \
  -H "Content-Type: application/json" \
  -d '{"postulacion_id":1,"estudiante_nombre":"Valeria","oferta_puesto":"Backend","feedback":"Plan de prueba"}'
```

Para modo test usar `/webhook-test/...` y hacer clic antes en **Test workflow**.
