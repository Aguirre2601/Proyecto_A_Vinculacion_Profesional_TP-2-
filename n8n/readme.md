# Workflows de n8n

Automatización del flujo de postulaciones: pre-scoring determinista, enriquecimiento con IA y notificación simulada.

**Requisitos:** credencial **Header Auth account** (`x-goog-api-key`) con una clave válida de Gemini; workflows importados y **Active**. No se usan variables `GEMINI_*` ni `N8N_BLOCK_ENV_ACCESS_IN_NODE`. Dependencia: Workflow 3 activo ← Workflow 2 ← Workflow 1.

| Workflow | Webhook | Acción |
|---|---|---|
| 1. Pre-scoring | `POST /webhook/postulacion` | Calcula el match en un Code node, lo persiste vía `/postulaciones/registrar` y, si hay skills faltantes, llama al Workflow 2 |
| 2. Enriquecimiento IA | `POST /webhook/ia-enrichment` | Genera el plan con Gemini, lo guarda y devuelve `ia_feedback` al Workflow 1 |
| 3. Notificación | `POST /webhook/notificacion-reporte` | Simula el envío del informe |

---

## Workflow 1 — Ingreso y Pre-scoring Determinista

**1. Evento que inicia el flujo:** webhook `POST /webhook/postulacion` (test: `/webhook-test/postulacion`). Usa `responseMode: responseNode`.

**2. Datos de entrada:** el frontend envía los objetos completos del estudiante y la oferta:

```json
{
  "estudiante": {
    "id": 1,
    "nombre": "Valeria Gómez",
    "carrera": "Ingeniería en Sistemas",
    "skills": ["Python", "SQL", "FastAPI", "Git"]
  },
  "oferta": {
    "id": 1,
    "puesto": "Backend Junior",
    "empresa": "Fintech Innova",
    "skills_requeridas": ["Python", "FastAPI", "Docker", "PostgreSQL", "Git"]
  }
}
```

**3. Validación y transformación:** el Code node `Calcular Match Determinista` normaliza las skills (minúsculas y `trim`), calcula la intersección, las faltantes y el scoring con la fórmula determinista del proyecto. Luego `Registrar Postulación en Backend` llama a `POST http://backend:8000/postulaciones/registrar` para persistir el resultado y obtener `postulacion_id`. El IF `¿Hay Skills Faltantes?` evalúa `skills_faltantes.length > 0`; si hay brechas, llama al Workflow 2 con `postulacion_id`, `estudiante_id`, `estudiante_nombre`, `oferta_puesto`, `empresa`, `scoring`, `skills_coincidentes` y `skills_faltantes`. Si no hay brechas, responde directamente sin IA.

**4. Respuesta devuelta:** incluye el match y, si se ejecutó el Workflow 2, el plan formativo:

```json
{
  "postulacion_id": 1,
  "estudiante_id": 1,
  "estudiante_nombre": "Valeria Gómez",
  "oferta_id": 1,
  "oferta_puesto": "Backend Junior",
  "empresa": "Fintech Innova",
  "scoring": 60.0,
  "skills_coincidentes": ["Python", "FastAPI", "Git"],
  "skills_faltantes": ["Docker", "PostgreSQL"],
  "formula": "(3 / 5) * 100 = 60.0%",
  "estado": "En desarrollo formativo",
  "ia_feedback": "### Diagnóstico de Brecha Formativa...",
  "ia_origen": "Google Gemini gemini-3.1-flash-lite",
  "ia_error": null
}
```

**5. Reconocimiento de fallas:** si el backend falla o supera el timeout de 10 s, la ejecución se detiene y el cliente recibe el error por defecto de n8n. Si el Workflow 2 falla o supera el timeout de 90 s, el nodo `Disparar Workflow 2` usa `onError: continueRegularOutput` y la respuesta incluye `ia_feedback: null` con el detalle en `ia_error`; el match no se pierde. Las ejecuciones quedan en **Executions**.

---

## Workflow 2 — Agente de Enriquecimiento con IA

**1. Evento que inicia el flujo:** webhook `POST /webhook/ia-enrichment`, invocado por el Workflow 1 cuando hay skills faltantes (también manual).

**2. Datos de entrada:**

```json
{
  "postulacion_id": 1,
  "estudiante_id": 1,
  "estudiante_nombre": "Valeria Gómez",
  "oferta_puesto": "Backend Junior",
  "empresa": "Fintech Innova",
  "scoring": 60.0,
  "skills_coincidentes": ["Python", "FastAPI", "Git"],
  "skills_faltantes": ["Docker", "PostgreSQL"]
}
```

**3. Validación y transformación:** el nodo Set construye `prompt_construido` con los datos y las skills faltantes. Luego se llama a Gemini (`/v1beta/models/gemini-3.1-flash-lite:generateContent`) usando la credencial `Header Auth account` (`x-goog-api-key`), sin clave en la URL, con un body JSON seguro (`JSON.stringify`). El texto generado se envía a `POST http://backend:8000/postulaciones/{id}/ia-feedback`; el backend valida con Pydantic (`IAFeedbackRequest`, mínimo 5 caracteres) y verifica que la postulación exista. Finalmente se dispara el Workflow 3. El prompt de n8n es una versión reducida del usado en el frontend: no incluye carrera ni recursos gratuitos.

**4. Respuesta devuelta:** incluye el texto del plan para que el Workflow 1 lo devuelva al frontend:

```json
{
  "status": "enriquecido",
  "postulacion_id": 1,
  "feedback_guardado": true,
  "ia_feedback": "### Diagnóstico de Brecha Formativa...",
  "ia_origen": "Google Gemini gemini-3.1-flash-lite"
}
```

**5. Reconocimiento de fallas:** si falta la credencial o la clave es inválida, Gemini devuelve 4xx; si supera el timeout de 60 s o el backend rechaza el feedback, la ejecución se detiene y **no se llama al Workflow 3**. El Workflow 1 captura la falla con `onError: continueRegularOutput` y devuelve el match con `ia_error`. No hay fallback offline ni reintentos. La falla queda en **Executions** y en `docker compose logs n8n`.

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

Los workflows usan el manejo por defecto de n8n: un HTTP no-2xx detiene la ejecución, que queda registrada en **Executions**. La excepción es el nodo `Disparar Workflow 2` del Workflow 1, que usa `onError: continueRegularOutput` para devolver el match aunque falle la IA. Los logs se ven con `docker compose logs -f n8n`.

```bash
# Workflow 1 (enviar los objetos completos del estudiante y la oferta)
curl -X POST http://localhost:5678/webhook/postulacion \
  -H "Content-Type: application/json" \
  -d '{"estudiante":{"id":1,"nombre":"Valeria Gómez","carrera":"Ingeniería en Sistemas","skills":["Python","SQL","FastAPI","Git"]},"oferta":{"id":1,"puesto":"Backend Junior","empresa":"Fintech Innova","skills_requeridas":["Python","FastAPI","Docker","PostgreSQL","Git"]}}'

# Workflow 3
curl -X POST http://localhost:5678/webhook/notificacion-reporte \
  -H "Content-Type: application/json" \
  -d '{"postulacion_id":1,"estudiante_nombre":"Valeria","oferta_puesto":"Backend","feedback":"Plan de prueba"}'
```

Para modo test usar `/webhook-test/...` y hacer clic antes en **Test workflow**.
