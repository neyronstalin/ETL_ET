"""
Módulo de deduplicación de rubros.

Implementa estrategias para detectar y resolver duplicados:
- MERGE: Fusionar duplicados exactos
- SPLIT: Separar conflictos con sufijos
- HASH: Generar códigos para rubros sin código
"""

from src.dedupe.dedupe_engine import (
    DedupeEngine,
    DedupeStats,
    find_exact_duplicates,
    deduplicate_simple
)

__all__ = [
    "DedupeEngine",
    "DedupeStats",
    "find_exact_duplicates",
    "deduplicate_simple",
]
