"""
api/estudiantes.py - Endpoints de gestión de estudiantes.
"""
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.database import get_db
from backend.app.database.models import EstudianteDB
from app.schemas import EstudianteCreate, EstudianteResponse

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])


@router.post(
    "",
    response_model=EstudianteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="1. Registrar nuevo estudiante"
)
def crear_estudiante(payload: EstudianteCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo perfil de estudiante.
    Valida formato de email, longitud de nombre y al menos una habilidad.
    Retorna HTTP 201 en caso de éxito o HTTP 400 si el email ya existe.
    """
    existente = db.query(EstudianteDB).filter(EstudianteDB.email == payload.email.lower()).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un estudiante registrado con el email {payload.email}"
        )

    nuevo = EstudianteDB(
        nombre=payload.nombre,
        email=payload.email.lower(),
        carrera=payload.carrera,
        skills_json=json.dumps(payload.skills)
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return EstudianteResponse(
        id=nuevo.id,
        nombre=nuevo.nombre,
        email=nuevo.email,
        carrera=nuevo.carrera,
        skills=nuevo.skills,
        fecha_creacion=nuevo.fecha_creacion
    )


@router.get(
    "",
    response_model=List[EstudianteResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar estudiantes registrados"
)
def listar_estudiantes(db: Session = Depends(get_db)):
    """Listado completo de estudiantes registrados."""
    estudiantes = db.query(EstudianteDB).all()
    return [
        EstudianteResponse(
            id=e.id,
            nombre=e.nombre,
            email=e.email,
            carrera=e.carrera,
            skills=e.skills,
            fecha_creacion=e.fecha_creacion
        )
        for e in estudiantes
    ]
