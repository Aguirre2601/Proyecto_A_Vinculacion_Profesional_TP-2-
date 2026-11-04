"""
models.py - Modelos Pydantic para validación estricta de esquemas
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ==========================================
# Modelos para Estudiante
# ==========================================
class EstudianteCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120, description="Nombre y apellido completo")
    email: str = Field(..., description="Correo electrónico válido")
    carrera: str = Field(..., min_length=3, max_length=150, description="Carrera universitaria actual")
    skills: List[str] = Field(..., min_length=1, description="Lista de habilidades del estudiante")

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        clean = str(v).strip().lower()
        if "@" not in clean or len(clean) < 3:
            raise ValueError("Formato de correo electrónico inválido. Debe contener '@'.")
        if "." not in clean.split("@")[-1]:
            clean = clean + ".com"
        return clean

    @field_validator("skills")
    @classmethod
    def validar_y_normalizar_skills(cls, v: List[str]) -> List[str]:
        limpias = [s.strip() for s in v if s and s.strip()]
        if not limpias:
            raise ValueError("Debe incluir al menos una habilidad válida")
        return limpias


class EstudianteResponse(BaseModel):
    id: int
    nombre: str
    email: str
    carrera: str
    skills: List[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ==========================================
# Modelos para Oferta Laboral
# ==========================================
class OfertaCreate(BaseModel):
    puesto: str = Field(..., min_length=2, max_length=150, description="Título del puesto")
    empresa: str = Field(..., min_length=2, max_length=120, description="Nombre de la empresa")
    skills_requeridas: List[str] = Field(..., min_length=1, description="Lista de habilidades requeridas")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Descripción opcional del puesto")

    @field_validator("skills_requeridas")
    @classmethod
    def validar_skills_requeridas(cls, v: List[str]) -> List[str]:
        limpias = [s.strip() for s in v if s and s.strip()]
        if not limpias:
            raise ValueError("Debe incluir al menos una habilidad requerida")
        return limpias


class OfertaResponse(BaseModel):
    id: int
    puesto: str
    empresa: str
    skills_requeridas: List[str]
    descripcion: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ==========================================
# Modelos para Postulación y Matching Determinista
# ==========================================
class MatchRequest(BaseModel):
    estudiante_id: int = Field(..., gt=0, description="ID del estudiante postulado")
    oferta_id: int = Field(..., gt=0, description="ID de la oferta laboral")


class MatchResponse(BaseModel):
    postulacion_id: int
    estudiante_id: int
    estudiante_nombre: str
    oferta_id: int
    oferta_puesto: str
    empresa: str
    scoring: float = Field(..., ge=0.0, le=100.0, description="Porcentaje de compatibilidad determinista")
    skills_coincidentes: List[str]
    skills_faltantes: List[str]
    estado: str = Field(..., description="'Apta para entrevista' o 'En desarrollo formativo'")
    formula: str


# ==========================================
# Modelos para Feedback de IA
# ==========================================
class IAFeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=5, description="Texto de recomendación generado por el LLM")


class IAFeedbackResponse(BaseModel):
    mensaje: str
    postulacion_id: int
    ia_feedback: str


class PostulacionResponse(BaseModel):
    id: int
    estudiante_id: int
    oferta_id: int
    scoring: float
    skills_coincidentes: List[str]
    skills_faltantes: List[str]
    estado: str
    ia_feedback: Optional[str] = None
    fecha: datetime
