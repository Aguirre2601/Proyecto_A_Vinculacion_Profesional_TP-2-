"""
models.py - Modelos ORM de SQLAlchemy.
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from app.basededatos import Base


class EstudianteDB(Base):
    """Tabla de perfiles de estudiantes."""
    __tablename__ = "estudiantes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    carrera = Column(String(150), nullable=False)
    skills_json = Column(Text, nullable=False)  # Serializado en JSON: '["Python", "FastAPI"]'
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    @property
    def skills(self) -> list[str]:
        try:
            return json.loads(self.skills_json)
        except Exception:
            return []

    @skills.setter
    def skills(self, val: list[str]):
        self.skills_json = json.dumps(val)


class OfertaDB(Base):
    """Tabla de ofertas laborales publicadas."""
    __tablename__ = "ofertas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    puesto = Column(String(150), nullable=False, index=True)
    empresa = Column(String(120), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    skills_requeridas_json = Column(Text, nullable=False)  # Serializado JSON
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    @property
    def skills_requeridas(self) -> list[str]:
        try:
            return json.loads(self.skills_requeridas_json)
        except Exception:
            return []

    @skills_requeridas.setter
    def skills_requeridas(self, val: list[str]):
        self.skills_requeridas_json = json.dumps(val)


class PostulacionDB(Base):
    """Tabla de postulaciones y resultados de matching."""
    __tablename__ = "postulaciones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    estudiante_id = Column(Integer, nullable=False, index=True)
    oferta_id = Column(Integer, nullable=False, index=True)
    scoring = Column(Float, nullable=False)
    skills_coincidentes_json = Column(Text, nullable=False)
    skills_faltantes_json = Column(Text, nullable=False)
    estado = Column(String(50), nullable=False)  # "Apta para entrevista" | "En desarrollo formativo"
    ia_feedback = Column(Text, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)
