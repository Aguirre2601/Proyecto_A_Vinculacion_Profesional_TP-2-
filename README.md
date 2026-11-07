# Plataforma de Vinculación y Desarrollo Profesional — Proyecto A

## 1. Título del software

**Plataforma de Vinculación y Desarrollo Profesional (Proyecto A)**
Sistema de matching determinista entre estudiantes universitarios y ofertas laborales, con enriquecimiento mediante Inteligencia Artificial y automatización Low-Code.

---

## 2. ¿Qué hace?

La plataforma permite que estudiantes universitarios se postulen a ofertas laborales y obtengan un **porcentaje de compatibilidad técnica calculado de forma determinista**, junto con un listado exacto de las habilidades que dominan y las que les faltan.

A partir de esa brecha, el sistema puede generar un **plan de formación personalizado** (con Google Gemini o con un generador pedagógico offline) y almacenarlo en la base de datos. Adicionalmente, un conjunto de workflows de **n8n** automatiza el flujo completo: recepción de la postulación, pre-scoring, enriquecimiento con IA y notificación final.

El principio central es la **separación de responsabilidades**:

- El **scoring nunca lo calcula un LLM**: se calcula con una fórmula matemática determinista en Python.
- La **IA solo redacta el plan de mejora** a partir de las habilidades faltantes detectadas.
- **n8n** orquesta los eventos y las bifurcaciones del proceso.

---

## 3. Objetivo

Diseñar e implementar una arquitectura desacoplada que:

1. Valide y registre perfiles de estudiantes y ofertas laborales.
2. Calcule la compatibilidad con la fórmula:

   ```text
   Scoring = (|Skills Estudiante ∩ Skills Oferta| / |Skills Oferta|) * 100
   ```

3. Determine el estado de la postulación:
   - **Apta para entrevista** si `Scoring >= 70%`.
   - **En desarrollo formativo** si `Scoring < 70%`.
4. Genere y persista una recomendación formativa para cerrar la brecha de habilidades.
5. Automatice el flujo mediante webhooks y workflows Low-Code.
6. Ofrecer una interfaz web amigable y tolerante a fallos (modo autónomo si el backend no está disponible).

---

## 4. Componentes

| Componente | Tecnología | Puerto por defecto | Función |
|---|---|---|---|
| **Frontend** | Streamlit (Python) | `8501` | Interfaz de usuario: postulaciones, alta de estudiantes/ofertas, historial y planes IA. |
| **Backend** | FastAPI + SQLAlchemy (Python) | `8000` | API REST, validación de datos, cálculo determinista, persistencia SQLite. |
| **Base de datos** | SQLite | — | Persistencia en `backend/data/vinculacion.db` (volumen del host). |
| **Automatización** | n8n | `5678` | Orquestación Low-Code mediante 3 workflows encadenados. |
| **Motor de IA** | Google Gemini (opcional, configurable con `GEMINI_MODEL`) | — | Generación del plan formativo con `gemini-3.8-flash` por defecto. Si no hay clave, se usa una plantilla offline. |

### Flujo funcional

```text
Usuario (Streamlit)
        │
        ├── POST /estudiantes ──────────────► SQLite
        ├── POST /ofertas ──────────────────► SQLite
        └── POST /postulaciones/match ──────► Matcher determinista ──► SQLite
                    │
                    └── (Scoring < 70%) ──► Plan IA (Gemini / offline)
                                              │
                                              └── POST /postulaciones/{id}/ia-feedback

n8n (opcional, demostración de automatización)
Workflow 1 (Webhook) ──► Backend /postulaciones/match
        ├── Scoring >= 70% ──► respuesta APTA_PARA_ENTREVISTA
        └── Scoring < 70%  ──► Workflow 2 (Gemini) ──► Backend ia-feedback
                                                        └──► Workflow 3 (notificación simulada)
```

### Workflows de n8n incluidos

| Archivo | Webhook | Función |
|---|---|---|
| `n8n/workflow_1_prescoring.json` | `POST /webhook/postulacion` | Recibe la postulación, llama al backend y bifurca según el scoring (>= 70%). |
| `n8n/workflow_2_enriquecimiento_ia.json` | `POST /webhook/ia-enrichment` | Construye el prompt con las skills faltantes, llama a Gemini y guarda el feedback. |
| `n8n/workflow_3_notificacion_reporte.json` | `POST /webhook/notificacion-reporte` | Simula el envío del informe al estudiante si existe feedback de IA. |

---

## 5. Requisitos

### Obligatorios

- **Docker Desktop** 24 o superior (Windows, macOS o Linux).
- **Docker Compose v2** (incluido en Docker Desktop; comando `docker compose`).
- **Git**.
- **4 GB de RAM** libres recomendados.
- Navegador web moderno (Chrome, Edge, Firefox).
- Puertos libres: **8501**, **8000** y **5678**.

### Opcionales

- **Clave de API de Google Gemini** para generar planes con IA en vivo.
  Se obtiene gratis en <https://aistudio.google.com/>.
  Sin clave, el sistema funciona igual usando el generador pedagógico offline.
- **Python 3.11+** solo si se desea ejecutar los servicios sin Docker.

> Con Docker **no es necesario instalar Python ni las dependencias** de `requirements.txt` en la máquina anfitriona.

---

## 6. Instrucciones de instalación

### 6.1 Obtener el proyecto

```bash
git clone <URL_DEL_REPOSITORIO>
cd "Proyecto_A_Vinculacion_Profesional_TP"
```

### 6.2 Crear el archivo de variables de entorno

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**

```bash
cp .env.example .env
```

Editar `.env` y, si se desea usar IA en vivo, completar:

```env
GEMINI_API_KEY=TU_CLAVE_DE_GEMINI
GEMINI_MODEL=gemini-3.8-flash
```

> Si `GEMINI_API_KEY` se deja vacía, el sistema usará automáticamente el plan formativo offline. `GEMINI_MODEL` es opcional y su valor por defecto es `gemini-3.8-flash`.

### 6.3 Construir las imágenes

```bash
docker compose build
```

### 6.4 (Opcional) Verificar la configuración

```bash
docker compose config
```

---

## 7. Instrucciones de ejecución

### 7.1 Iniciar los servicios

```bash
# Construir (si hace falta) y levantar todo en segundo plano
docker compose up -d --build

# Ver el estado de los contenedores
docker compose ps
```

### 7.2 Verificar que todo esté operativo

```bash
# Estado de salud del backend
curl http://localhost:8000/health

# Seguir los logs en vivo (Ctrl+C para salir)
docker compose logs -f

# Logs de un servicio puntual
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f n8n
```

### 7.3 Acceder a la aplicación

| Servicio | URL |
|---|---|
| **Frontend (Streamlit)** | <http://localhost:8501> |
| **Backend (API)** | <http://localhost:8000> |
| **Documentación Swagger** | <http://localhost:8000/docs> |
| **Documentación ReDoc** | <http://localhost:8000/redoc> |
| **n8n** | <http://localhost:5678> |

### 7.4 Detener los servicios

```bash
# Detener los contenedores sin eliminarlos (conserva datos)
docker compose stop

# Volver a iniciarlos
docker compose start

# Reiniciar un servicio puntual
docker compose restart backend

# Detener y eliminar contenedores y redes (conserva volúmenes/datos)
docker compose down

# Detener y eliminar TODO, incluidos los datos de n8n (¡destructivo!)
docker compose down -v
```

> La base SQLite se guarda en `backend/data/vinculacion.db` y **no se borra** con `docker compose down`.
> Solo se elimina manualmente borrando ese archivo o con `docker compose down -v` para el volumen de n8n.

### 7.5 Reconstruir tras cambios de código

```bash
docker compose up -d --build
```

Si se modificaron dependencias (`requirements.txt`) y el cambio no se refleja:

```bash
docker compose build --no-cache
docker compose up -d
```

---

## 8. Configuración inicial de n8n

Los workflows **no se importan automáticamente**. Pasos:

1. Abrir <http://localhost:5678>.
2. Crear la cuenta de propietario (solo la primera vez).
3. Ir a **Workflows → Import from File** e importar, en este orden:
   - `n8n/workflow_1_prescoring.json`
   - `n8n/workflow_2_enriquecimiento_ia.json`
   - `n8n/workflow_3_notificacion_reporte.json`
4. Activar los tres workflows con el interruptor **Inactive → Active**.
   - El workflow 3 debe estar activo para que el workflow 2 pueda invocarlo.
   - El workflow 2 debe estar activo para que el workflow 1 pueda invocarlo.
5. Para la demostración desde el frontend:
   - **Modo Test:** en n8n, hacer clic en **Test workflow** y luego usar el botón “Disparar n8n (Modo Test)” del frontend (usa `/webhook-test/postulacion`).
   - **Modo Producción:** con el workflow activo, usar “Disparar n8n (Modo Producción Activo)” (usa `/webhook/postulacion`).

> La variable `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` ya está configurada en `compose.yaml` para que el workflow 2 pueda leer `$env.GEMINI_API_KEY`.

---

## 9. Principales funcionalidades

### 9.1 Gestión de estudiantes
- Alta con validación de nombre, email, carrera y al menos una habilidad.
- Normalización de emails y rechazo de duplicados (`HTTP 400`).
- Listado de estudiantes registrados.

### 9.2 Catálogo de ofertas laborales
- Publicación de ofertas con puesto, empresa, descripción y skills requeridas.
- Búsqueda y filtrado parcial por puesto y empresa.

### 9.3 Postulación y matching determinista
- Selección de estudiante y oferta.
- Cálculo matemático reproducible del scoring.
- Visualización de:
  - Puntaje de compatibilidad.
  - Estado de la postulación (Apta / En desarrollo).
  - Habilidades coincidentes.
  - Habilidades faltantes (brecha).
  - Fórmula evaluada.

### 9.4 Plan de formación con IA
- Generación de un plan en Markdown con:
  - Diagnóstico de la brecha.
  - Ruta de aprendizaje acelerada.
  - Proyecto integrador de portfolio.
  - Recursos gratuitos recomendados.
- Uso de Gemini (`GEMINI_MODEL`, por defecto `gemini-3.8-flash`) si hay clave.
- Fallback offline con plantilla pedagógica si no hay clave o falla la red.
- Persistencia del plan en SQLite mediante `POST /postulaciones/{id}/ia-feedback`.

### 9.5 Historial de postulaciones
- Consulta de postulaciones con scoring, estado y plan IA almacenado.

### 9.6 Automatización con n8n
- Pre-scoring automático vía webhook.
- Bifurcación condicional por umbral del 70%.
- Enriquecimiento con IA y notificación simulada.

### 9.7 Modo autónomo (alta disponibilidad)
- Si el backend no responde, el frontend sigue funcionando con datos semilla en memoria (`st.session_state`).
- Permite demostrar la interfaz sin base de datos, aunque los datos se pierden al recargar.

### 9.8 Documentación interactiva de la API
- Swagger UI en `/docs` y ReDoc en `/redoc`.

---

## 10. API REST — Endpoints principales

| Método | Ruta | Código esperado | Descripción |
|---|---|---|---|
| `POST` | `/estudiantes` | `201` / `400` / `422` | Registrar estudiante. |
| `GET` | `/estudiantes` | `200` | Listar estudiantes. |
| `POST` | `/ofertas` | `201` / `422` | Registrar oferta laboral. |
| `GET` | `/ofertas?puesto=&empresa=` | `200` | Listar/filtrar ofertas. |
| `POST` | `/postulaciones/match` | `200` / `404` | Calcular scoring y persistir postulación. |
| `GET` | `/postulaciones` | `200` | Historial de postulaciones. |
| `POST` | `/postulaciones/{id}/ia-feedback` | `200` / `404` | Guardar plan formativo del LLM. |
| `GET` | `/health` | `200` | Healthcheck del servicio. |

### Ejemplo de cálculo de match

```bash
curl -X POST http://localhost:8000/postulaciones/match \
  -H "Content-Type: application/json" \
  -d '{"estudiante_id": 1, "oferta_id": 1}'
```

### Ejemplo de alta de estudiante

```bash
curl -X POST http://localhost:8000/estudiantes \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Camila Navarro",
    "email": "camila.navarro@universidad.edu.ar",
    "carrera": "Ingeniería Informática",
    "skills": ["Python", "SQL", "Git"]
  }'
```

---

## 11. Estructura de carpetas y archivos

```text
Proyecto_A_Vinculacion_Profesional_TP/
│
├── .env.example                  # Plantilla de variables de entorno (sin claves reales)
├── .gitignore                    # Exclusión de .env, bases SQLite, cachés, etc.
├── BitacoraIA.md                 # Bitácora de uso de IA del proyecto
├── compose.yaml                  # Orquestación Docker: n8n + backend + frontend
├── README.md                     # Documentación del proyecto
│
├── backend/                      # Microservicio FastAPI
│   ├── .dockerignore             # Excluye cachés, data local y .env del build
│   ├── Dockerfile                # Imagen Python 3.11 + Uvicorn
│   ├── requirements.txt          # fastapi, uvicorn, pydantic, sqlalchemy, requests...
│   ├── app/
│   │   ├── main.py               # Configuración FastAPI, CORS y routers
│   │   ├── schemas.py            # Esquemas Pydantic v2
│   │   ├── database/
│   │   │   ├── database.py       # Engine, sesión, get_db e init_db
│   │   │   └── models.py         # Modelos ORM SQLAlchemy
│   │   ├── api/
│   │   │   ├── estudiantes.py    # Endpoints de estudiantes
│   │   │   ├── ofertas.py        # Endpoints de ofertas
│   │   │   ├── postulaciones.py  # Matching, historial e ia-feedback
│   │   │   └── health.py         # /health
│   │   └── services/
│   │       └── matcher.py        # Algoritmo determinista puro
│   └── data/                     # Persistencia SQLite montada desde el host
│       └── .gitkeep              # Conserva la carpeta en el repositorio
│
├── frontend/                     # Interfaz Streamlit
│   ├── .dockerignore             # Excluye cachés y .env del build
│   ├── Dockerfile                # Imagen Python 3.11 + Streamlit
│   ├── requirements.txt          # streamlit>=1.36.0, requests, python-dotenv
│   ├── app.py                    # Punto de entrada: configuración, sidebar y navegación
│   ├── common.py                 # Semillas, estado de sesión y helpers compartidos
│   └── pages/
│       ├── main_page.py          # Página de bienvenida
│       ├── postulacion.py        # Vista de matching y plan IA
│       ├── estudiantes.py        # Vista de gestión de estudiantes
│       ├── ofertas.py            # Vista del catálogo de ofertas
│       ├── historial.py          # Vista del historial de postulaciones
│       └── acerca.py             # Vista de arquitectura del sistema
│
└── n8n/                          # Workflows exportados de n8n (importar manualmente)
    ├── readme.md                 # Documentación de los workflows
    ├── workflow_1_prescoring.json
    ├── workflow_2_enriquecimiento_ia.json
    └── workflow_3_notificacion_reporte.json
```

### Descripción de archivos clave

| Archivo | Responsabilidad |
|---|---|
| `compose.yaml` | Define los 3 servicios, la red `app-network`, el volumen `tp_n8n_data`, puertos, variables de entorno y healthcheck del backend. |
| `backend/app/main.py` | Configura FastAPI, CORS, ciclo de vida y registra los routers. |
| `backend/app/database/database.py` | Crea las tablas `estudiantes`, `ofertas` y `postulaciones`, y precarga datos semilla. |
| `backend/app/database/models.py` | Modelos ORM de SQLAlchemy y serialización JSON de skills. |
| `backend/app/schemas.py` | Validación de emails, longitudes y listas de habilidades con Pydantic v2. |
| `backend/app/services/matcher.py` | Función pura de scoring y detección de brechas; no depende de FastAPI ni de la base de datos. |
| `frontend/app.py` | Punto de entrada: configuración global, sidebar y navegación con `st.navigation`. |
| `frontend/pages/` | Una vista por archivo (`main_page`, `postulacion`, `estudiantes`, `ofertas`, `historial`, `acerca`), cada una con `render()`. |
| `frontend/common.py` | Datos semilla, estado de sesión y helpers de API compartidos. |
| `.env.example` | Puertos, URLs, clave opcional de Gemini y modelo (`GEMINI_MODEL`). |

---

## 12. Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `N8N_PORT` | `5678` | Puerto del host para n8n. |
| `BACKEND_PORT` | `8000` | Puerto del host para el backend. |
| `FRONTEND_PORT` | `8501` | Puerto del host para el frontend. |
| `N8N_HOST` | `localhost` | Host público de n8n. |
| `DATABASE_URL` | `sqlite:///./data/vinculacion.db` | Cadena de conexión de SQLAlchemy. |
| `BACKEND_API_URL` | `http://backend:8000` | URL interna del backend usada por el frontend. |
| `GEMINI_API_KEY` | *(vacío)* | Clave opcional de Google Gemini. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Modelo de Gemini usado por el frontend y n8n. |

---

## 13. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| El frontend muestra “Backend Desconectado”. | El backend aún no terminó de arrancar o falló. | `docker compose ps` y `docker compose logs backend`. Esperar el healthcheck. |
| `port is already allocated`. | Otro proceso usa 8000/8501/5678. | Cambiar los puertos en `.env` o liberar el puerto. |
| n8n no ejecuta el workflow 2. | Falta `GEMINI_API_KEY` o el workflow 2 no está activo. | Configurar la clave en `.env`, reiniciar con `docker compose up -d` y activar el workflow. |
| Error 404 al disparar el webhook de producción. | El workflow está inactivo. | Activar el workflow en n8n (Inactive → Active). |
| Los datos desaparecen al recargar. | El backend está caído y se usa memoria RAM. | Levantar el backend y verificar `/health`. |
| El plan IA se genera pero no se guarda. | La postulación no existe en SQLite o el backend está caído. | Verificar que el match se haya calculado con el backend online. |
| Los cambios de código no se reflejan. | Imagen antigua en caché. | `docker compose build --no-cache && docker compose up -d`. |
| Windows no encuentra `curl`. | PowerShell antiguo. | Usar `curl.exe` o `Invoke-RestMethod`. |

### Comandos útiles de diagnóstico

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose exec backend ls -la /app/data
docker compose exec backend curl -s http://localhost:8000/health
docker compose config
```

---

## 14. Notas y limitaciones

- El scoring es **determinista** y no usa IA; el LLM solo redacta el plan formativo.
- El envío de correo del workflow 3 es **simulado** (nodo Set); no se envía un email real.
- El workflow 2 requiere conexión a Internet y una `GEMINI_API_KEY` válida para el enriquecimiento en vivo.
- Los workflows de n8n se importan manualmente; no se auto-importan al iniciar el contenedor.
- La base SQLite es adecuada para docencia y demostración; para producción se recomienda PostgreSQL.
- El frontend incluye un modo autónomo en memoria, útil para demo, pero sin persistencia real.
- La clave de Gemini debe configurarse en `.env` **antes** de levantar los contenedores, porque n8n la lee al iniciar.
