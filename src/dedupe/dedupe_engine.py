"""
Motor de deduplicación de rubros.

Implementa tres estrategias:
1. MERGE: Duplicados exactos (mismo código + descripción) → fusionar
2. SPLIT: Conflictos (mismo código, desc/unidad diferente) → separar con sufijos (#A, #B)
3. HASH: Sin código → generar código hash basado en descripción

"""

from typing import List, Dict, Tuple, Set
from collections import defaultdict
import hashlib
import logging
from dataclasses import dataclass

from src.models.schemas import (
    Rubro, DuplicateGroup, DuplicateStrategy, ConflictType
)
from src.utils.text_norm import normalize_rubro_code

logger = logging.getLogger(__name__)


@dataclass
class DedupeStats:
    """Estadísticas de deduplicación."""
    total_input: int
    total_output: int
    merged_groups: int
    split_groups: int
    hashed_rubros: int
    exact_duplicates_removed: int


class DedupeEngine:
    """
    Motor de deduplicación de rubros.

    Detecta y resuelve duplicados usando estrategias configurables.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        enable_merge: bool = True,
        enable_split: bool = True,
        enable_hash: bool = True
    ):
        """
        Inicializa el motor de deduplicación.

        Args:
            similarity_threshold: Umbral para considerar descripciones similares (0-1)
            enable_merge: Habilitar estrategia MERGE
            enable_split: Habilitar estrategia SPLIT
            enable_hash: Habilitar estrategia HASH para códigos faltantes
        """
        self.similarity_threshold = similarity_threshold
        self.enable_merge = enable_merge
        self.enable_split = enable_split
        self.enable_hash = enable_hash

    def deduplicate(self, rubros: List[Rubro]) -> Tuple[List[Rubro], List[DuplicateGroup], DedupeStats]:
        """
        Deduplica lista de rubros.

        Args:
            rubros: Lista de rubros a deduplicar

        Returns:
            Tupla (rubros_deduplicados, duplicate_groups, stats)
        """
        logger.info(f"Iniciando deduplicación de {len(rubros)} rubros...")

        # Paso 1: Agrupar por código normalizado
        code_groups = self._group_by_code(rubros)

        # Paso 2: Procesar cada grupo
        resolved_rubros: List[Rubro] = []
        duplicate_groups: List[DuplicateGroup] = []
        merged_count = 0
        split_count = 0
        hashed_count = 0

        for canonical_code, group_rubros in code_groups.items():
            if len(group_rubros) == 1:
                # No hay duplicados en este código
                resolved_rubros.extend(group_rubros)
            else:
                # Detectar tipo de duplicado y resolver
                group, resolved = self._resolve_duplicate_group(canonical_code, group_rubros)
                duplicate_groups.append(group)
                resolved_rubros.extend(resolved)
                merged_count += group.merge_count
                split_count += group.split_count

        # Paso 3: Hashear rubros sin código
        if self.enable_hash:
            no_code_rubros = [r for r in rubros if not r.codigo or r.codigo.strip() == ""]
            if no_code_rubros:
                logger.info(f"Aplicando HASH a {len(no_code_rubros)} rubros sin código")
                for rubro in no_code_rubros:
                    rubro.codigo = self._generate_hash_code(rubro.descripcion)
                    hashed_count += 1

        # Stats
        stats = DedupeStats(
            total_input=len(rubros),
            total_output=len(resolved_rubros),
            merged_groups=merged_count,
            split_groups=split_count,
            hashed_rubros=hashed_count,
            exact_duplicates_removed=len(rubros) - len(resolved_rubros)
        )

        logger.info(
            f"✅ Deduplicación completada: {stats.total_input} → {stats.total_output} rubros "
            f"({stats.merged_groups} merged, {stats.split_groups} split, {stats.hashed_rubros} hashed)"
        )

        return resolved_rubros, duplicate_groups, stats

    def _group_by_code(self, rubros: List[Rubro]) -> Dict[str, List[Rubro]]:
        """
        Agrupa rubros por código normalizado.

        Args:
            rubros: Lista de rubros

        Returns:
            Diccionario {codigo_normalizado: [rubros]}
        """
        code_groups: Dict[str, List[Rubro]] = defaultdict(list)

        for rubro in rubros:
            if rubro.codigo and rubro.codigo.strip():
                canonical_code = normalize_rubro_code(rubro.codigo)
            else:
                # Rubros sin código → grupo especial
                canonical_code = f"__NO_CODE_{rubro.rubro_id}"

            code_groups[canonical_code].append(rubro)

        return code_groups

    def _resolve_duplicate_group(
        self,
        canonical_code: str,
        rubros: List[Rubro]
    ) -> Tuple[DuplicateGroup, List[Rubro]]:
        """
        Resuelve un grupo de rubros duplicados.

        Args:
            canonical_code: Código canónico del grupo
            rubros: Lista de rubros con el mismo código

        Returns:
            Tupla (DuplicateGroup, rubros_resueltos)
        """
        # Detectar conflictos
        conflicts = self._detect_conflicts(rubros)

        if not conflicts:
            # No hay conflictos → MERGE (duplicados exactos)
            if self.enable_merge:
                merged_rubro, merge_count = self._merge_exact_duplicates(rubros)
                group = DuplicateGroup(
                    group_id=f"DUP_{canonical_code}",
                    canonical_code=canonical_code,
                    rubro_ids=[r.rubro_id for r in rubros],
                    strategy=DuplicateStrategy.MERGE,
                    conflicts=[],
                    resolved_rubros=[merged_rubro],
                    merge_count=merge_count,
                    split_count=0
                )
                return group, [merged_rubro]
            else:
                # Merge deshabilitado, mantener todos
                return self._create_passthrough_group(canonical_code, rubros), rubros

        else:
            # Hay conflictos → SPLIT
            if self.enable_split:
                split_rubros = self._split_conflicting_duplicates(canonical_code, rubros)
                group = DuplicateGroup(
                    group_id=f"DUP_{canonical_code}",
                    canonical_code=canonical_code,
                    rubro_ids=[r.rubro_id for r in rubros],
                    strategy=DuplicateStrategy.SPLIT,
                    conflicts=conflicts,
                    resolved_rubros=split_rubros,
                    merge_count=0,
                    split_count=len(split_rubros)
                )
                return group, split_rubros
            else:
                # Split deshabilitado, mantener todos
                return self._create_passthrough_group(canonical_code, rubros), rubros

    def _detect_conflicts(self, rubros: List[Rubro]) -> List[ConflictType]:
        """
        Detecta conflictos entre rubros con el mismo código.

        Args:
            rubros: Lista de rubros

        Returns:
            Lista de tipos de conflictos detectados
        """
        conflicts: Set[ConflictType] = set()

        # Extraer valores únicos
        descriptions = {r.descripcion.strip().lower() for r in rubros}
        units = {r.unidad.strip().lower() for r in rubros if r.unidad}

        # Detectar conflictos
        if len(descriptions) > 1:
            conflicts.add(ConflictType.DESCRIPTION)

        if len(units) > 1:
            conflicts.add(ConflictType.UNIT)

        # Conflictos de recursos (si hay recursos asociados)
        # TODO: Implementar cuando se integre con recursos

        return list(conflicts)

    def _merge_exact_duplicates(self, rubros: List[Rubro]) -> Tuple[Rubro, int]:
        """
        Fusiona duplicados exactos en un único rubro.

        Args:
            rubros: Lista de rubros exactamente iguales

        Returns:
            Tupla (rubro_fusionado, cantidad_fusionada)
        """
        # Usar el primer rubro como base
        merged = rubros[0]

        # Combinar source_pages de todos
        all_pages = set()
        for rubro in rubros:
            all_pages.update(rubro.source_pages)

        merged.source_pages = sorted(list(all_pages))

        # Promedio de confidence
        avg_confidence = sum(r.confidence for r in rubros) / len(rubros)
        merged.confidence = avg_confidence

        return merged, len(rubros)

    def _split_conflicting_duplicates(
        self,
        canonical_code: str,
        rubros: List[Rubro]
    ) -> List[Rubro]:
        """
        Separa rubros conflictivos con sufijos.

        Args:
            canonical_code: Código canónico
            rubros: Lista de rubros conflictivos

        Returns:
            Lista de rubros con códigos modificados (#A, #B, etc.)
        """
        split_rubros = []

        for i, rubro in enumerate(rubros):
            # Agregar sufijo al código
            suffix = chr(65 + i)  # A, B, C, ...
            rubro.codigo = f"{canonical_code}#{suffix}"
            split_rubros.append(rubro)

        return split_rubros

    def _generate_hash_code(self, description: str) -> str:
        """
        Genera código hash para rubros sin código.

        Args:
            description: Descripción del rubro

        Returns:
            Código hash en formato "HASH_XXXXXX"
        """
        # MD5 hash de la descripción
        hash_obj = hashlib.md5(description.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:8].upper()

        return f"HASH_{hash_hex}"

    def _create_passthrough_group(
        self,
        canonical_code: str,
        rubros: List[Rubro]
    ) -> DuplicateGroup:
        """
        Crea un grupo de duplicados sin resolver (passthrough).

        Usado cuando las estrategias están deshabilitadas.
        """
        return DuplicateGroup(
            group_id=f"DUP_{canonical_code}",
            canonical_code=canonical_code,
            rubro_ids=[r.rubro_id for r in rubros],
            strategy=DuplicateStrategy.MERGE,  # Default
            conflicts=[],
            resolved_rubros=rubros,
            merge_count=0,
            split_count=0
        )


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════

def find_exact_duplicates(rubros: List[Rubro]) -> List[List[Rubro]]:
    """
    Encuentra grupos de rubros exactamente duplicados.

    Dos rubros son duplicados exactos si tienen:
    - Mismo código (normalizado)
    - Misma descripción (ignorando case/espacios)
    - Misma unidad

    Args:
        rubros: Lista de rubros

    Returns:
        Lista de grupos de duplicados [[rubro1, rubro2], [rubro3, rubro4], ...]
    """
    # Crear signature para cada rubro
    signature_groups: Dict[str, List[Rubro]] = defaultdict(list)

    for rubro in rubros:
        code_norm = normalize_rubro_code(rubro.codigo) if rubro.codigo else ""
        desc_norm = rubro.descripcion.strip().lower()
        unit_norm = rubro.unidad.strip().lower() if rubro.unidad else ""

        signature = f"{code_norm}|{desc_norm}|{unit_norm}"
        signature_groups[signature].append(rubro)

    # Filtrar solo grupos con duplicados
    duplicate_groups = [
        group for group in signature_groups.values()
        if len(group) > 1
    ]

    return duplicate_groups


def deduplicate_simple(rubros: List[Rubro]) -> List[Rubro]:
    """
    Deduplicación simple: solo remueve duplicados exactos.

    Función de conveniencia para uso rápido.

    Args:
        rubros: Lista de rubros

    Returns:
        Lista deduplicada
    """
    engine = DedupeEngine(
        enable_merge=True,
        enable_split=False,
        enable_hash=False
    )

    deduped, _, stats = engine.deduplicate(rubros)
    logger.info(f"Deduplicación simple: {stats.total_input} → {stats.total_output}")
    return deduped
