"""
main.py - Configuración de la aplicación FastAPI.
Solo se encarga de crear la app, CORS, ciclo de vida y registrar los routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import estudiantes, ofertas, postulaciones, health
from app.database.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar la aplicación."""
    init_db()
    yield


app = FastAPI(
    title="Plataforma de Vinculación Profesional - Backend API",
    description="API determinista para cálculo de scoring y gestión de postulaciones con IA.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuración de CORS para permitir peticiones desde Streamlit y n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(estudiantes.router)
app.include_router(ofertas.router)
app.include_router(postulaciones.router)
app.include_router(health.router)
