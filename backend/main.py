"""
main.py - Aplicación FastAPI principal
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
Cumple estrictamente con los 5 endpoints mínimos obligatorios y códigos HTTP estándar.
"""
import os
import json
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import init_db, get_db, EstudianteDB, OfertaDB, PostulacionDB
from models import (
    EstudianteCreate,
    EstudianteResponse,
    OfertaCreate,
    OfertaResponse,
    MatchRequest,
    MatchResponse,
    IAFeedbackRequest,
    IAFeedbackResponse,
    PostulacionResponse
)
from services.matcher import calculate_match

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="Plataforma de Vinculación Profesional - Backend API",
    description="API determinista para cálculo de scoring y gestión de postulaciones con IA.",
    version="1.0.0"
)

# Configuración de CORS para permitir peticiones desde Streamlit y n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Base de Datos SQLite al arrancar
@app.on_event("startup")
def startup_event():
    init_db()


# =========================================================================
# ENDPOINTS OBLIGATORIOS (SECCIÓN 2.1 DE LA ESPECIFICACIÓN)
# =========================================================================

# 1. POST /estudiantes: Alta y validación de perfil
@app.post(
    "/estudiantes",
    response_model=EstudianteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="1. Registrar nuevo estudiante",
    tags=["Estudiantes"]
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


# 2. POST /ofertas: Alta y validación de oferta laboral
@app.post(
    "/ofertas",
    response_model=OfertaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="2. Registrar nueva oferta laboral",
    tags=["Ofertas"]
)
def crear_oferta(payload: OfertaCreate, db: Session = Depends(get_db)):
    """
    Publica una nueva oferta laboral con sus habilidades requeridas.
    Retorna HTTP 201 en caso de éxito.
    """
    nueva = OfertaDB(
        puesto=payload.puesto,
        empresa=payload.empresa,
        descripcion=payload.descripcion or "",
        skills_requeridas_json=json.dumps(payload.skills_requeridas)
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return OfertaResponse(
        id=nueva.id,
        puesto=nueva.puesto,
        empresa=nueva.empresa,
        skills_requeridas=nueva.skills_requeridas,
        descripcion=nueva.descripcion,
        fecha_creacion=nueva.fecha_creacion
    )


# 3. GET /ofertas: Listado de ofertas activas con filtros opcionales
@app.get(
    "/ofertas",
    response_model=List[OfertaResponse],
    status_code=status.HTTP_200_OK,
    summary="3. Listar ofertas laborales activas",
    tags=["Ofertas"]
)
def listar_ofertas(
    puesto: Optional[str] = Query(None, description="Filtro parcial por título del puesto"),
    empresa: Optional[str] = Query(None, description="Filtro parcial por nombre de empresa"),
    db: Session = Depends(get_db)
):
    """
    Retorna el catálogo de ofertas activas con soporte para filtros de búsqueda.
    """
    query = db.query(OfertaDB)
    if puesto:
        query = query.filter(OfertaDB.puesto.ilike(f"%{puesto}%"))
    if empresa:
        query = query.filter(OfertaDB.empresa.ilike(f"%{empresa}%"))

    ofertas = query.all()
    return [
        OfertaResponse(
            id=o.id,
            puesto=o.puesto,
            empresa=o.empresa,
            skills_requeridas=o.skills_requeridas,
            descripcion=o.descripcion,
            fecha_creacion=o.fecha_creacion
        )
        for o in ofertas
    ]


# 4. POST /postulaciones/match: Cálculo determinista de scoring y brechas
@app.post(
    "/postulaciones/match",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    summary="4. Ejecutar match determinista entre estudiante y oferta",
    tags=["Postulaciones"]
)
def calcular_postulacion_match(payload: MatchRequest, db: Session = Depends(get_db)):
    """
    Calcula determinísticamente la compatibilidad:
    Scoring = (|Skills Estudiante ∩ Skills Oferta| / |Skills Oferta|) * 100
    Determina si la postulación está 'Apta para entrevista' (>= 70%) o 'En desarrollo formativo' (< 70%).
    Persiste el resultado en SQLite para trazabilidad.
    """
    estudiante = db.query(EstudianteDB).filter(EstudianteDB.id == payload.estudiante_id).first()
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estudiante con ID {payload.estudiante_id} no encontrado"
        )

    oferta = db.query(OfertaDB).filter(OfertaDB.id == payload.oferta_id).first()
    if not oferta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Oferta con ID {payload.oferta_id} no encontrada"
        )

    # Invocación de la función determinista pura
    match_result = calculate_match(estudiante.skills, oferta.skills_requeridas)

    # Condición de negocio
    estado = "Apta para entrevista" if match_result.scoring >= 70.0 else "En desarrollo formativo"

    # Persistencia del resultado de la postulación
    postulacion = PostulacionDB(
        estudiante_id=estudiante.id,
        oferta_id=oferta.id,
        scoring=match_result.scoring,
        skills_coincidentes_json=json.dumps(match_result.matching_skills),
        skills_faltantes_json=json.dumps(match_result.missing_skills),
        estado=estado
    )
    db.add(postulacion)
    db.commit()
    db.refresh(postulacion)

    return MatchResponse(
        postulacion_id=postulacion.id,
        estudiante_id=estudiante.id,
        estudiante_nombre=estudiante.nombre,
        oferta_id=oferta.id,
        oferta_puesto=oferta.puesto,
        empresa=oferta.empresa,
        scoring=match_result.scoring,
        skills_coincidentes=match_result.matching_skills,
        skills_faltantes=match_result.missing_skills,
        estado=estado,
        formula=match_result.formula
    )


# 5. POST /postulaciones/{id}/ia-feedback: Guarda la recomendación del LLM
@app.post(
    "/postulaciones/{id}/ia-feedback",
    response_model=IAFeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="5. Guardar recomendación formativa del LLM",
    tags=["Postulaciones"]
)
def guardar_ia_feedback(id: int, payload: IAFeedbackRequest, db: Session = Depends(get_db)):
    """
    Almacena el plan de carrera o sugerencia formativa generada por el LLM
    asociada a una postulación específica.
    """
    postulacion = db.query(PostulacionDB).filter(PostulacionDB.id == id).first()
    if not postulacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Postulación con ID {id} no encontrada"
        )

    postulacion.ia_feedback = payload.feedback.strip()
    db.commit()
    db.refresh(postulacion)

    return IAFeedbackResponse(
        mensaje="Recomendación de IA almacenada exitosamente",
        postulacion_id=id,
        ia_feedback=postulacion.ia_feedback
    )


# =========================================================================
# ENDPOINTS COMPLEMENTARIOS DE APOYO (CONSULTA Y DIAGNÓSTICO)
# =========================================================================
@app.get("/estudiantes", response_model=List[EstudianteResponse], tags=["Estudiantes"])
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


@app.get("/postulaciones", response_model=List[PostulacionResponse], tags=["Postulaciones"])
def listar_postulaciones(db: Session = Depends(get_db)):
    """Historial de postulaciones registradas en SQLite."""
    items = db.query(PostulacionDB).order_by(PostulacionDB.id.desc()).all()
    return [
        PostulacionResponse(
            id=p.id,
            estudiante_id=p.estudiante_id,
            oferta_id=p.oferta_id,
            scoring=p.scoring,
            skills_coincidentes=json.loads(p.skills_coincidentes_json),
            skills_faltantes=json.loads(p.skills_faltantes_json),
            estado=p.estado,
            ia_feedback=p.ia_feedback,
            fecha=p.fecha
        )
        for p in items
    ]


@app.get("/health", tags=["Salud"])
def health_check():
    """Verificación de operatividad del microservicio."""
    return {"status": "ok", "service": "FastAPI Backend TP Vinculación"}
