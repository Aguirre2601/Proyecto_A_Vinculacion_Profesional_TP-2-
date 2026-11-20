# Plataforma de Vinculación y Desarrollo Profesional — Proyecto A

## 1. Título del software

**Plataforma de Vinculación y Desarrollo Profesional (Proyecto A)**
Sistema de matching determinista entre estudiantes universitarios y ofertas laborales, con enriquecimiento mediante Inteligencia Artificial y automatización Low-Code.

---

## 2. ¿Qué hace?

La plataforma permite que estudiantes universitarios se postulen a ofertas laborales y obtengan un **porcentaje de compatibilidad técnica calculado de forma determinista**, junto con un listado exacto de las habilidades que dominan y las que les faltan.

A partir de esa brecha, el sistema puede generar un **plan de formación personalizado** con Google Gemini desde el Workflow 2 de n8n y almacenarlo en la base de datos. Adicionalmente, un conjunto de workflows de **n8n** automatiza el flujo completo: recepción de la postulación, cálculo del match, enriquecimiento con IA y notificación final.

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
6. Ofrecer una interfaz web amigable que muestre una página de error clara si el backend no está disponible.

---

## 4. Componentes

| Componente | Tecnología | Puerto por defecto | Función |
|---|---|---|---|
| **Frontend** | Streamlit (Python) | `8501` | Interfaz de usuario: postulaciones, alta de estudiantes/ofertas, historial y planes IA. |
| **Backend** | FastAPI + SQLAlchemy (Python) | `8000` | API REST, validación de datos y persistencia SQLite; el scoring lo calcula n8n. |
| **Base de datos** | SQLite | — | Persistencia en `backend/data/vinculacion.db` (volumen del host). |
| **Automatización** | n8n | `5678` | Orquestación Low-Code: el Workflow 1 calcula el match, el Workflow 2 genera el plan IA y el Workflow 3 envía la notificación por correo. |
| **Motor de IA** | Google Gemini (credencial Header Auth en n8n) | — | Generación del plan formativo con el modelo fijo `gemini-3.1-flash-lite`. Si la credencial falta o falla la red, el plan no se genera y se informa el error. |

### Flujo funcional

```text
Usuario (Streamlit)
        │
        ├── POST /estudiantes ──────────────► SQLite
        ├── POST /ofertas ──────────────────► SQLite
        └── POST /webhook/postulacion ──────► n8n Workflow 1
                                                │
                                    Code node: match determinista
                                                │
                                    POST /postulaciones/registrar ──► SQLite
                                                │
                                    (skills faltantes) ──► Workflow 2 (Gemini)
                                                │              │
                                                │              └── POST /postulaciones/{id}/ia-feedback
                                                │              └── Workflow 3 (envío de email SMTP)
                                                │
                                    Respuesta: match + ia_feedback ──► Streamlit
```

El cálculo determinista se ejecuta en el Code node del Workflow 1 de n8n. El backend solo persiste el resultado que n8n envía a `/postulaciones/registrar`; no recalcula el scoring.

### Workflows de n8n incluidos

| Archivo | Webhook | Función |
|---|---|---|
| `n8n/workflow_1_prescoring.json` | `POST /webhook/postulacion` | Recibe el estudiante y la oferta completos, calcula el match en un Code node, persiste vía `/postulaciones/registrar` y llama al Workflow 2 si hay skills faltantes. |
| `n8n/workflow_2_enriquecimiento_ia.json` | `POST /webhook/ia-enrichment` | Construye el prompt con las skills faltantes, llama a Gemini, guarda el feedback y lo devuelve al Workflow 1. |
| `n8n/workflow_3_notificacion_reporte.json` | `POST /webhook/notificacion-reporte` | Envía por correo electrónico (SMTP) el informe y plan de mejora en formato HTML al estudiante si existe feedback de IA. |

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
  Sin clave, el match se calcula igual y el plan IA se informa como no disponible.
- **Cuenta SMTP (ej. Gmail con Contraseña de aplicación)** para el envío real de correos desde el Workflow 3.
- **Python 3.11+** solo si se desea ejecutar los servicios sin Docker.

> Con Docker **no es necesario instalar Python ni las dependencias** de `requirements.txt` en la máquina anfitriona.

---

## 6. Instrucciones de instalación

### 6.1 Obtener el proyecto

```bash
git clone <https://github.com/Aguirre2601/Proyecto_A_Vinculacion_Profesional_TP-2-.git>
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

No hace falta configurar Gemini ni SMTP en `.env`. Las credenciales se cargan en n8n:

1. Ir a **Credentials → Create New → Header Auth**.
2. Nombre: `Header Auth account`; **Header Name:** `x-goog-api-key`; **Value:** tu clave de Google Gemini.
3. El Workflow 2 usa esa credencial y el modelo fijo `gemini-3.1-flash-lite`.

> Si la credencial falta o es inválida, el plan IA no se genera y el match se muestra igual con un aviso. El modelo está fijado en el nodo HTTP Request del Workflow 2; para cambiarlo hay que editar ese nodo.

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
4. Configurar las credenciales en n8n (**Credentials → Create New**):
   - **Google Gemini (`Header Auth`):** Nombre `Header Auth account`, **Header Name:** `x-goog-api-key`, **Value:** tu API key de Google Gemini (usada en el Workflow 2).
   - **Correo saliente (`SMTP`):** Crear una credencial **SMTP** (por ejemplo con Gmail usando `smtp.gmail.com`, puerto `465`, SSL/TLS activo y una *Contraseña de aplicación*) y vincularla en el nodo **Send an Email** del **Workflow 3**.
5. Activar los tres workflows con el interruptor **Inactive → Active**.
   - El workflow 3 debe estar activo para que el workflow 2 pueda invocarlo.
   - El workflow 2 debe estar activo para que el workflow 1 pueda invocarlo.
6. Para la demostración desde el frontend: en la vista **Postulación**, seleccionar estudiante y oferta y pulsar **🚀 Calcular Compatibilidad Determinista**. La app llama a `/webhook/postulacion` (Workflow 1 en producción), muestra el match y el plan IA, y envía el correo al estudiante.

> El Workflow 2 usa la credencial `Header Auth account` (`x-goog-api-key`) y la URL fija de Gemini; no necesita variables de entorno ni `N8N_BLOCK_ENV_ACCESS_IN_NODE`.

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
- Cálculo matemático reproducible del scoring en el Code node del Workflow 1 de n8n.
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
- Uso de Gemini (`gemini-3.1-flash-lite`) desde el Workflow 2 de n8n con la credencial `Header Auth account`.
- Si la credencial falta o falla la red, el match se muestra igual y el plan se informa como no disponible.
- Persistencia del plan en SQLite mediante `POST /postulaciones/{id}/ia-feedback`.

### 9.5 Historial de postulaciones
- Consulta de postulaciones con scoring, estado y plan IA almacenado.

### 9.6 Automatización con n8n
- El frontend dispara el Workflow 1 con los datos completos del estudiante y la oferta.
- El Workflow 1 calcula el match, lo persiste y, si hay skills faltantes, llama al Workflow 2.
- Enriquecimiento con IA y notificación real por correo electrónico vía SMTP (Workflow 3) con el plan de mejora en formato HTML.

### 9.7 Manejo de errores sin fallback offline
- Si el backend o n8n no responden, el frontend muestra `frontend/pages/error.py` y permite volver al inicio.
- No se usan datos semilla ni se calcula el scoring localmente en el frontend.
- El plan IA puede faltar sin perder el match: el Workflow 1 devuelve `ia_error` y el frontend lo muestra como aviso.

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
| `POST` | `/postulaciones/registrar` | `201` / `404` / `422` | Persistir un match ya calculado por n8n Workflow 1. |
| `GET` | `/postulaciones` | `200` | Historial de postulaciones. |
| `POST` | `/postulaciones/{id}/ia-feedback` | `200` / `404` | Guardar plan formativo del LLM. |
| `GET` | `/health` | `200` | Healthcheck del servicio. |

### Ejemplo de persistencia de un match calculado por n8n

```bash
curl -X POST http://localhost:8000/postulaciones/registrar \
  -H "Content-Type: application/json" \
  -d '{
    "estudiante_id": 1,
    "oferta_id": 1,
    "scoring": 60.0,
    "skills_coincidentes": ["Python", "FastAPI", "Git"],
    "skills_faltantes": ["Docker", "PostgreSQL"],
    "estado": "En desarrollo formativo",
    "formula": "(3 / 5) * 100 = 60.0%"
  }'
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
│   │   │   ├── postulaciones.py  # Persistencia, historial e ia-feedback
│   │   │   └── health.py         # /health
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
│       ├── acerca.py             # Vista de arquitectura del sistema
│       └── error.py              # Página global de error y retorno al inicio
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
| `frontend/app.py` | Punto de entrada: configuración global, sidebar y navegación con `st.navigation`. |
| `frontend/pages/` | Una vista por archivo (`main_page`, `postulacion`, `estudiantes`, `ofertas`, `historial`, `acerca`, `error`), cada una con `render()`. |
| `frontend/common.py` | Estado de sesión y helpers de API compartidos. |
| `.env.example` | Puertos y URLs. Las credenciales de Gemini y SMTP se configuran en n8n, no en `.env`. |

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

> La clave y el modelo de Gemini, así como la cuenta SMTP, no son variables de entorno: se configuran directamente en las credenciales de n8n.

---

## 13. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| El frontend muestra la página de error o “Backend desconectado”. | El backend aún no terminó de arrancar o falló. | `docker compose ps` y `docker compose logs backend`. Esperar el healthcheck. |
| `port is already allocated`. | Otro proceso usa 8000/8501/5678. | Cambiar los puertos en `.env` o liberar el puerto. |
| n8n no ejecuta el workflow 2. | Falta la credencial `Header Auth account` o el workflow 2 no está activo. | Crear/verificar la credencial en n8n (header `x-goog-api-key`) y activar el workflow. |
| El workflow 3 falla al enviar el correo. | Falta configurar la credencial SMTP o el workflow 3 está inactivo. | Configurar la credencial SMTP en n8n, vincularla en el nodo `Send an Email` y activar el workflow. |
| Error 404 al disparar el webhook de producción. | El workflow está inactivo. | Activar el workflow en n8n (Inactive → Active). |
| Los datos no se guardan y aparece la página de error. | El backend está caído; no hay fallback en memoria. | Levantar el backend y verificar `/health`. |
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
- El envío de correo del workflow 3 utiliza **SMTP** (nodo *Send an Email*) y requiere configurar una credencial SMTP válida en n8n para despachar los correos reales.
- El workflow 2 requiere conexión a Internet y la credencial `Header Auth account` con una clave válida de Gemini para el enriquecimiento en vivo.
- Los workflows de n8n se importan manualmente; no se auto-importan al iniciar el contenedor.
- La base SQLite es adecuada para docencia y demostración; para producción se recomienda PostgreSQL.
- El frontend requiere el backend: no calcula el scoring ni guarda datos en memoria como fallback.
- Las credenciales de Gemini y SMTP se configuran en n8n (**Credentials**) y no se guardan en `.env` ni en `compose.yaml`.