"""
services/matcher.py - Algoritmo determinista puro de scoring y cálculo de brechas
Proyecto A: Plataforma de Vinculación y Desarrollo Profesional
"""
from dataclasses import dataclass
from typing import List, Set


@dataclass
class MatchResult:
    scoring: float
    matching_skills: List[str]
    missing_skills: List[str]
    formula: str


def calculate_match(student_skills: List[str], required_skills: List[str]) -> MatchResult:
    """
    Calcula determinísticamente la compatibilidad entre las habilidades del estudiante
    y las habilidades requeridas por la oferta de empleo.

    Fórmula matemática requerida por la especificación:
        Scoring = ( |Skills Estudiante ∩ Skills Oferta| / |Skills Oferta| ) * 100

    Reglas de negocio:
    1. La comparación es insensible a mayúsculas/minúsculas y elimina espacios circundantes.
    2. Las habilidades coincidentes y faltantes conservan el formato y casing de la oferta.
    3. Si la oferta no tiene habilidades requeridas, el scoring es 0.0 para prevenir división por cero.
    4. El porcentaje se redondea a 2 decimales y se encuentra estrictamente en el intervalo [0.0, 100.0].
    """
    try:
        # Validación de casos borde
        if not required_skills:
            return MatchResult(
                scoring=0.0,
                matching_skills=[],
                missing_skills=[],
                formula="(0 / 0) * 100 = 0.0%"
            )

        # Normalización para búsqueda case-insensitive
        student_set_normalized: Set[str] = {
            s.strip().lower() for s in student_skills if s and s.strip()
        }

        matching: List[str] = []
        missing: List[str] = []

        # Recorremos los requerimientos de la oferta preservando su presentación original
        for req in required_skills:
            clean_req = req.strip()
            if not clean_req:
                continue

            if clean_req.lower() in student_set_normalized:
                matching.append(clean_req)
            else:
                missing.append(clean_req)

        total_req = len(matching) + len(missing)
        if total_req == 0:
            return MatchResult(
                scoring=0.0,
                matching_skills=[],
                missing_skills=[],
                formula="(0 / 0) * 100 = 0.0%"
            )

        # Cálculo explícito de la fórmula determinista
        interseccion_count = len(matching)
        scoring_val = (interseccion_count / total_req) * 100.0
        scoring_rounded = round(scoring_val, 2)

        formula_str = f"({interseccion_count} / {total_req}) * 100 = {scoring_rounded}%"

        return MatchResult(
            scoring=scoring_rounded,
            matching_skills=matching,
            missing_skills=missing,
            formula=formula_str
        )

    except Exception as exc:
        raise ValueError(f"Error al calcular match determinista: {str(exc)}") from exc
