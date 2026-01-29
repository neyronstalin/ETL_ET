"""
Módulo de matching semántico.

Proporciona funcionalidad para matchear rubros extraídos (ET)
contra una base de referencia (WBS) usando embeddings + fuzzy matching.
"""

from src.match.embedder import (
    Embedder,
    EmbeddingCache,
    get_embedder,
    get_cache,
    cosine_similarity,
    batch_cosine_similarity
)

from src.match.scoring import (
    ScoringWeights,
    fuzzy_similarity,
    code_similarity,
    unit_similarity,
    combined_score,
    calculate_match_score,
    rank_candidates,
    is_ambiguous,
    get_match_method
)

from src.match.matcher import (
    SemanticMatcher,
    load_reference_rubros_from_excel
)

__all__ = [
    # Embedder
    "Embedder",
    "EmbeddingCache",
    "get_embedder",
    "get_cache",
    "cosine_similarity",
    "batch_cosine_similarity",

    # Scoring
    "ScoringWeights",
    "fuzzy_similarity",
    "code_similarity",
    "unit_similarity",
    "combined_score",
    "calculate_match_score",
    "rank_candidates",
    "is_ambiguous",
    "get_match_method",

    # Matcher
    "SemanticMatcher",
    "load_reference_rubros_from_excel",
]
