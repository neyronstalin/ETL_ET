"""
Módulo de scoring para matching semántico.

Combina múltiples señales para calcular scores de matching:
- Similaridad semántica (embeddings + cosine)
- Similaridad fuzzy (string matching)
- Signals híbridas (código, unidad, etc.)
"""

from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

from src.config.settings import get_settings


@dataclass
class ScoringWeights:
    """Pesos para combinar diferentes scores."""
    semantic: float = 0.7      # Peso del score semántico
    fuzzy: float = 0.2         # Peso del fuzzy string matching
    code_match: float = 0.05   # Peso de match de código exacto
    unit_match: float = 0.05   # Peso de match de unidad

    def __post_init__(self):
        """Valida que los pesos sumen 1.0."""
        total = self.semantic + self.fuzzy + self.code_match + self.unit_match
        if not 0.99 <= total <= 1.01:  # Tolerancia por floating point
            raise ValueError(f"Los pesos deben sumar 1.0, suma actual: {total}")


def fuzzy_similarity(text1: str, text2: str, method: str = "token_set_ratio") -> float:
    """
    Calcula similaridad fuzzy entre dos textos.

    Args:
        text1: Primer texto
        text2: Segundo texto
        method: Método de rapidfuzz ('ratio', 'token_set_ratio', 'partial_ratio')

    Returns:
        Score en rango [0, 100]

    Raises:
        RuntimeError: Si rapidfuzz no está instalado
    """
    if not RAPIDFUZZ_AVAILABLE:
        raise RuntimeError(
            "rapidfuzz no instalado. "
            "Instalar con: pip install rapidfuzz"
        )

    if method == "ratio":
        return fuzz.ratio(text1, text2)
    elif method == "token_set_ratio":
        return fuzz.token_set_ratio(text1, text2)
    elif method == "partial_ratio":
        return fuzz.partial_ratio(text1, text2)
    else:
        raise ValueError(f"Método fuzzy desconocido: {method}")


def normalize_fuzzy_score(fuzzy_score: float) -> float:
    """
    Normaliza fuzzy score de [0, 100] a [0, 1].

    Args:
        fuzzy_score: Score fuzzy en rango [0, 100]

    Returns:
        Score normalizado en rango [0, 1]
    """
    return fuzzy_score / 100.0


def code_similarity(code1: Optional[str], code2: Optional[str]) -> float:
    """
    Calcula similaridad entre códigos de rubros.

    Args:
        code1: Código 1 (puede ser None si no existe)
        code2: Código 2

    Returns:
        1.0 si son exactamente iguales (ignorando case/espacios),
        0.0 en caso contrario
    """
    if code1 is None or code2 is None:
        return 0.0

    # Normalizar y comparar
    c1 = code1.strip().lower().replace(" ", "")
    c2 = code2.strip().lower().replace(" ", "")

    return 1.0 if c1 == c2 else 0.0


def unit_similarity(unit1: Optional[str], unit2: Optional[str]) -> float:
    """
    Calcula similaridad entre unidades.

    Args:
        unit1: Unidad 1
        unit2: Unidad 2

    Returns:
        1.0 si son exactamente iguales (ignorando case),
        0.5 si son compatibles (ej: 'm2' vs 'm²'),
        0.0 en caso contrario
    """
    if unit1 is None or unit2 is None:
        return 0.0

    u1 = unit1.strip().lower()
    u2 = unit2.strip().lower()

    # Exacto
    if u1 == u2:
        return 1.0

    # Compatibles (mapeo común)
    compatible_pairs = [
        ("m2", "m²"), ("m^2", "m²"),
        ("m3", "m³"), ("m^3", "m³"),
        ("kg", "kilogramo"), ("kgs", "kg"),
        ("u", "und"), ("u", "unidad"), ("und", "unidad")
    ]

    for p1, p2 in compatible_pairs:
        if (u1 == p1 and u2 == p2) or (u1 == p2 and u2 == p1):
            return 0.5

    return 0.0


def combined_score(
    semantic_score: float,
    fuzzy_score: float,
    code_match: float,
    unit_match: float,
    weights: Optional[ScoringWeights] = None
) -> float:
    """
    Calcula score combinado ponderado.

    Args:
        semantic_score: Score semántico (cosine similarity) en [0, 1]
        fuzzy_score: Score fuzzy en [0, 100]
        code_match: Score de código en [0, 1]
        unit_match: Score de unidad en [0, 1]
        weights: Pesos para combinación

    Returns:
        Score combinado en [0, 1]
    """
    if weights is None:
        weights = ScoringWeights()

    # Normalizar fuzzy score a [0, 1]
    fuzzy_normalized = normalize_fuzzy_score(fuzzy_score)

    # Combinar ponderadamente
    score = (
        weights.semantic * semantic_score +
        weights.fuzzy * fuzzy_normalized +
        weights.code_match * code_match +
        weights.unit_match * unit_match
    )

    return score


def rank_candidates(
    scores: List[float],
    top_k: int = 5
) -> List[Tuple[int, float]]:
    """
    Rankea candidatos por score.

    Args:
        scores: Lista de scores
        top_k: Cantidad de top candidatos a retornar

    Returns:
        Lista de tuplas (índice, score) ordenadas descendentemente
    """
    # Crear lista de (índice, score)
    indexed_scores = [(i, score) for i, score in enumerate(scores)]

    # Ordenar por score descendente
    ranked = sorted(indexed_scores, key=lambda x: x[1], reverse=True)

    # Retornar top k
    return ranked[:top_k]


def is_ambiguous(
    top_scores: List[float],
    threshold_diff: float = 0.05
) -> bool:
    """
    Determina si hay ambigüedad entre candidatos.

    Considera ambiguo si los top 2 candidatos tienen scores muy similares.

    Args:
        top_scores: Lista de scores ordenados descendentemente
        threshold_diff: Diferencia mínima para considerar no ambiguo

    Returns:
        True si es ambiguo (top 2 muy similares), False en caso contrario
    """
    if len(top_scores) < 2:
        return False

    best_score = top_scores[0]
    second_score = top_scores[1]

    # Si la diferencia es pequeña, es ambiguo
    return (best_score - second_score) < threshold_diff


def get_match_method(
    semantic_score: float,
    fuzzy_score: float,
    code_match: float
) -> str:
    """
    Determina el método de match predominante.

    Args:
        semantic_score: Score semántico
        fuzzy_score: Score fuzzy (normalizado a [0, 1])
        code_match: Score de código

    Returns:
        'semantic', 'fuzzy', 'code', o 'hybrid'
    """
    fuzzy_normalized = normalize_fuzzy_score(fuzzy_score)

    # Si hay match de código exacto, priorizar
    if code_match >= 0.9:
        return "code"

    # Si semantic es dominante
    if semantic_score > fuzzy_normalized + 0.1:
        return "semantic"

    # Si fuzzy es dominante
    if fuzzy_normalized > semantic_score + 0.1:
        return "fuzzy"

    # En caso contrario, híbrido
    return "hybrid"


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════

def calculate_match_score(
    et_description: str,
    wbs_description: str,
    et_code: Optional[str] = None,
    wbs_code: Optional[str] = None,
    et_unit: Optional[str] = None,
    wbs_unit: Optional[str] = None,
    semantic_score: Optional[float] = None,
    weights: Optional[ScoringWeights] = None
) -> Tuple[float, str]:
    """
    Calcula score combinado para un par ET-WBS.

    Args:
        et_description: Descripción del rubro ET
        wbs_description: Descripción del rubro WBS
        et_code: Código ET (opcional)
        wbs_code: Código WBS
        et_unit: Unidad ET (opcional)
        wbs_unit: Unidad WBS (opcional)
        semantic_score: Score semántico precalculado (si existe)
        weights: Pesos de scoring

    Returns:
        Tupla (score_combinado, método_match)
    """
    # Si no hay semantic score precalculado, usar fuzzy como proxy
    if semantic_score is None:
        semantic_score = normalize_fuzzy_score(
            fuzzy_similarity(et_description, wbs_description)
        )

    # Calcular componentes
    fuzzy_score = fuzzy_similarity(et_description, wbs_description)
    code_match = code_similarity(et_code, wbs_code)
    unit_match = unit_similarity(et_unit, wbs_unit)

    # Score combinado
    score = combined_score(
        semantic_score=semantic_score,
        fuzzy_score=fuzzy_score,
        code_match=code_match,
        unit_match=unit_match,
        weights=weights
    )

    # Método predominante
    method = get_match_method(semantic_score, fuzzy_score, code_match)

    return score, method
