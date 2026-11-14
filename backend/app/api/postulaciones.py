"""
api/postulaciones.py - Endpoints de matching y feedback de IA.
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
"""
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import EstudianteDB, OfertaDB, PostulacionDB
from app.schemas import (
    MatchResponse,
    MatchRegistroRequest,
    IAFeedbackRequest,
    IAFeedbackResponse,
    PostulacionResponse,
)


router = APIRouter(prefix="/postulaciones", tags=["Postulaciones"])


@router.post(
    "/registrar",
    response_model=MatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Persistir un match ya calculado por n8n (Workflow 1)"
)
def registrar_postulacion(payload: MatchRegistroRequest, db: Session = Depends(get_db)):
    """
    Guarda en SQLite un match calculado externamente por n8n.
    No recalcula el scoring: confía en los valores deterministas enviados por el Workflow 1.
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

    postulacion = PostulacionDB(
        estudiante_id=estudiante.id,
        oferta_id=oferta.id,
        scoring=payload.scoring,
        skills_coincidentes_json=json.dumps(payload.skills_coincidentes),
        skills_faltantes_json=json.dumps(payload.skills_faltantes),
        estado=payload.estado
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
        scoring=payload.scoring,
        skills_coincidentes=payload.skills_coincidentes,
        skills_faltantes=payload.skills_faltantes,
        estado=payload.estado,
        formula=payload.formula
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
