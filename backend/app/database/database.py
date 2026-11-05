"""
database.py - Configuración de SQLite, sesión y creación de tablas.
"""
import os
import json
from sqlalchemy import create_engine
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
            pass #CHEQUEAR, no deberiamos manejar este posible error

# create_engine con connect_args para SQLite multihilo seguro
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Crea las tablas en la base de datos si no existen y precarga datos iniciales."""
    # Import perezoso para evitar el ciclo basededatos <-> models
    from backend.app.database import models

    Base.metadata.create_all(bind=engine)

    # Precarga de datos semilla si la BD está vacía
    db = SessionLocal()
    try:
        if db.query(models.EstudianteDB).count() == 0:
            estudiantes_seed = [
                models.EstudianteDB(
                    nombre="Valeria Gómez",
                    email="valeria.gomez@universidad.edu.ar",
                    carrera="Ingeniería en Sistemas de Información",
                    skills_json=json.dumps(["Python", "SQL", "FastAPI", "Git"])
                ),
                models.EstudianteDB(
                    nombre="Lucas Morales",
                    email="lucas.morales@universidad.edu.ar",
                    carrera="Licenciatura en Ciencias de la Computación",
                    skills_json=json.dumps(["JavaScript", "React", "HTML", "CSS", "Git"])
                ),
                models.EstudianteDB(
                    nombre="Sofía Benítez",
                    email="sofia.benitez@universidad.edu.ar",
                    carrera="Ingeniería Informática",
                    skills_json=json.dumps(["Python", "Docker", "PostgreSQL", "Linux", "FastAPI", "Pandas"])
                )
            ]
            db.add_all(estudiantes_seed)

        if db.query(models.OfertaDB).count() == 0:
            ofertas_seed = [
                models.OfertaDB(
                    puesto="Desarrollador Backend Junior (Python / FastAPI)",
                    empresa="Fintech Innova",
                    descripcion="Desarrollo de microservicios transaccionales con FastAPI y Docker.",
                    skills_requeridas_json=json.dumps(["Python", "FastAPI", "Docker", "PostgreSQL", "Git"])
                ),
                models.OfertaDB(
                    puesto="Data Engineer Trainee",
                    empresa="DataCloud Analytics",
                    descripcion="Construcción de pipelines ETL y consultas analíticas.",
                    skills_requeridas_json=json.dumps(["Python", "SQL", "Pandas", "Docker", "Airflow"])
                ),
                models.OfertaDB(
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
