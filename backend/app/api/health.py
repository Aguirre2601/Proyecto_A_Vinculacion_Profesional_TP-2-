"""
api/health.py - Endpoint de verificación de operatividad.
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
"""
from fastapi import APIRouter

router = APIRouter(tags=["Salud"])


@router.get("/health")
def health_check():
    """Verificación de operatividad del microservicio."""
    return {"status": "ok", "service": "FastAPI Backend TP Vinculación"}
