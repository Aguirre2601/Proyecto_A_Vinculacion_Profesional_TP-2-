"""
database.py - Configuración de SQLite y Modelos ORM con SQLAlchemy
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
"""
import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vinculacion.db")

# Asegurar que el directorio de la base de datos exista
if "sqlite" in DATABASE_URL:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception:
            pass

# create_engine con connect_args para SQLite multihilo seguro
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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


def init_db():
    """Crea las tablas en la base de datos si no existen y precarga datos iniciales."""
    Base.metadata.create_all(bind=engine)
    
    # Precarga de datos semilla si la BD está vacía
    db = SessionLocal()
    try:
        if db.query(EstudianteDB).count() == 0:
            estudiantes_seed = [
                EstudianteDB(
                    nombre="Valeria Gómez",
                    email="valeria.gomez@universidad.edu.ar",
                    carrera="Ingeniería en Sistemas de Información",
                    skills_json=json.dumps(["Python", "SQL", "FastAPI", "Git"])
                ),
                EstudianteDB(
                    nombre="Lucas Morales",
                    email="lucas.morales@universidad.edu.ar",
                    carrera="Licenciatura en Ciencias de la Computación",
                    skills_json=json.dumps(["JavaScript", "React", "HTML", "CSS", "Git"])
                ),
                EstudianteDB(
                    nombre="Sofía Benítez",
                    email="sofia.benitez@universidad.edu.ar",
                    carrera="Ingeniería Informática",
                    skills_json=json.dumps(["Python", "Docker", "PostgreSQL", "Linux", "FastAPI", "Pandas"])
                )
            ]
            db.add_all(estudiantes_seed)

        if db.query(OfertaDB).count() == 0:
            ofertas_seed = [
                OfertaDB(
                    puesto="Desarrollador Backend Junior (Python / FastAPI)",
                    empresa="Fintech Innova",
                    descripcion="Desarrollo de microservicios transaccionales con FastAPI y Docker.",
                    skills_requeridas_json=json.dumps(["Python", "FastAPI", "Docker", "PostgreSQL", "Git"])
                ),
                OfertaDB(
                    puesto="Data Engineer Trainee",
                    empresa="DataCloud Analytics",
                    descripcion="Construcción de pipelines ETL y consultas analíticas.",
                    skills_requeridas_json=json.dumps(["Python", "SQL", "Pandas", "Docker", "Airflow"])
                ),
                OfertaDB(
                    puesto="Fullstack Developer Jr",
                    empresa="AgileTech Solutions",
                    descripcion="Integración de frontend React con backend FastAPI.",
                    skills_requeridas_json=json.dumps(["Python", "FastAPI", "JavaScript", "React", "Docker"])
                )
            ]
            db.add_all(ofertas_seed)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error precargando datos semilla: {e}")
    finally:
        db.close()


def get_db():
    """Generador de dependencia de sesión de base de datos para FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
