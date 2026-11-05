"""
api/postulaciones.py - Endpoints de matching y feedback de IA.
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
"""
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.basededatos import get_db
from app.models import EstudianteDB, OfertaDB, PostulacionDB
from app.schemas import (
    MatchRequest,
    MatchResponse,
    IAFeedbackRequest,
    IAFeedbackResponse,
    PostulacionResponse,
)
from app.services.matcher import calculate_match

router = APIRouter(prefix="/postulaciones", tags=["Postulaciones"])


@router.post(
    "/match",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    summary="4. Ejecutar match determinista entre estudiante y oferta"
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


@router.get(
    "",
    response_model=List[PostulacionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar historial de postulaciones"
)
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


@router.post(
    "/{id}/ia-feedback",
    response_model=IAFeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="5. Guardar recomendación formativa del LLM"
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
