"""
api/ofertas.py - Endpoints de gestión de ofertas laborales.
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.basededatos import get_db
from app.models import OfertaDB
from app.schemas import OfertaCreate, OfertaResponse

router = APIRouter(prefix="/ofertas", tags=["Ofertas"])


@router.post(
    "",
    response_model=OfertaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="2. Registrar nueva oferta laboral"
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


@router.get(
    "",
    response_model=List[OfertaResponse],
    status_code=status.HTTP_200_OK,
    summary="3. Listar ofertas laborales activas"
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
