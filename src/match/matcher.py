"""
Matcher semántico multi-stage para rubros ET ↔ WBS.

Implementa un pipeline de matching en varias etapas:
1. Generación de embeddings (si no existen)
2. Búsqueda semántica (cosine similarity)
3. Refinamiento con fuzzy matching
4. Scoring combinado
5. Clasificación (MATCHED/AMBIGUOUS/NO_MATCH)
"""

from typing import List, Optional, Tuple
import numpy as np
import time
import logging
from pathlib import Path

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from src.models.schemas import (
    Rubro, ReferenceRubro, MatchResult, MatchEvidence, MatchStatus
)
from src.match.embedder import Embedder, get_embedder, batch_cosine_similarity
from src.match.scoring import (
    calculate_match_score, rank_candidates, is_ambiguous,
    fuzzy_similarity, normalize_fuzzy_score, ScoringWeights
)
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class SemanticMatcher:
    """
    Matcher semántico para rubros ET ↔ WBS.

    Usa embeddings + FAISS para búsqueda rápida + refinamiento fuzzy.
    """

    def __init__(
        self,
        reference_rubros: List[ReferenceRubro],
        embedder: Optional[Embedder] = None,
        use_faiss: bool = True
    ):
        """
        Inicializa el matcher.

        Args:
            reference_rubros: Lista de rubros WBS de referencia
            embedder: Instancia de Embedder (usa global si None)
            use_faiss: Usar FAISS para búsqueda rápida (requiere faiss-cpu instalado)
        """
        self.reference_rubros = reference_rubros
        self.embedder = embedder or get_embedder()
        self.settings = get_settings()
        self.use_faiss = use_faiss and FAISS_AVAILABLE

        # Generar embeddings de referencia
        logger.info(f"Generando embeddings para {len(reference_rubros)} rubros WBS...")
        self._generate_reference_embeddings()

        # Construir índice FAISS si está disponible
        if self.use_faiss:
            self._build_faiss_index()

    def _generate_reference_embeddings(self) -> None:
        """Genera embeddings para todos los rubros de referencia."""
        descriptions = [r.description for r in self.reference_rubros]

        embeddings = self.embedder.encode(
            descriptions,
            batch_size=32,
            show_progress=True,
            normalize=True
        )

        # Asignar embeddings a cada rubro
        for rubro, embedding in zip(self.reference_rubros, embeddings):
            rubro.embedding = embedding.tolist()

        logger.info(f"✅ Embeddings generados: {len(embeddings)} vectores")

    def _build_faiss_index(self) -> None:
        """Construye índice FAISS para búsqueda rápida."""
        if not FAISS_AVAILABLE:
            logger.warning("FAISS no disponible, usando búsqueda lineal")
            self.use_faiss = False
            return

        # Extraer embeddings como matriz numpy
        embeddings_matrix = np.array([
            r.embedding for r in self.reference_rubros
        ]).astype('float32')

        # Crear índice FAISS (IndexFlatIP para cosine similarity con vectores normalizados)
        dimension = embeddings_matrix.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        self.faiss_index.add(embeddings_matrix)

        logger.info(f"✅ Índice FAISS construido: {self.faiss_index.ntotal} vectores")

    def match_single(
        self,
        rubro: Rubro,
        top_k: int = 5
    ) -> MatchResult:
        """
        Encuentra match para un único rubro ET.

        Args:
            rubro: Rubro ET a matchear
            top_k: Cantidad de candidatos a considerar

        Returns:
            MatchResult con best_match y alternatives
        """
        start_time = time.time()

        # Generar embedding del rubro ET
        et_embedding = self.embedder.encode_single(
            rubro.descripcion,
            normalize=True
        )

        # Búsqueda semántica
        candidates_indices, semantic_scores = self._search_semantic(
            et_embedding,
            top_k=top_k
        )

        # Refinamiento con scoring combinado
        evidences = self._refine_candidates(
            rubro=rubro,
            candidates_indices=candidates_indices,
            semantic_scores=semantic_scores
        )

        # Clasificar resultado
        match_result = self._classify_match(
            rubro=rubro,
            evidences=evidences,
            processing_time_ms=(time.time() - start_time) * 1000
        )

        return match_result

    def match_batch(
        self,
        rubros: List[Rubro],
        top_k: int = 5
    ) -> List[MatchResult]:
        """
        Matchea un batch de rubros ET.

        Args:
            rubros: Lista de rubros ET
            top_k: Candidatos por rubro

        Returns:
            Lista de MatchResult
        """
        logger.info(f"Matching {len(rubros)} rubros...")

        results = []
        for i, rubro in enumerate(rubros, 1):
            if i % 10 == 0:
                logger.info(f"  Progreso: {i}/{len(rubros)}")

            result = self.match_single(rubro, top_k=top_k)
            results.append(result)

        logger.info(f"✅ Matching completado: {len(results)} resultados")
        return results

    def _search_semantic(
        self,
        query_embedding: np.ndarray,
        top_k: int
    ) -> Tuple[List[int], List[float]]:
        """
        Búsqueda semántica usando FAISS o búsqueda lineal.

        Args:
            query_embedding: Vector embedding del query
            top_k: Cantidad de resultados

        Returns:
            Tupla (índices, scores)
        """
        if self.use_faiss:
            # Búsqueda con FAISS
            query_vector = query_embedding.reshape(1, -1).astype('float32')
            scores, indices = self.faiss_index.search(query_vector, top_k)
            return indices[0].tolist(), scores[0].tolist()
        else:
            # Búsqueda lineal (fallback)
            embeddings_matrix = np.array([
                r.embedding for r in self.reference_rubros
            ])
            scores = batch_cosine_similarity(query_embedding, embeddings_matrix)

            # Top k
            top_indices = np.argsort(scores)[::-1][:top_k]
            top_scores = scores[top_indices]

            return top_indices.tolist(), top_scores.tolist()

    def _refine_candidates(
        self,
        rubro: Rubro,
        candidates_indices: List[int],
        semantic_scores: List[float]
    ) -> List[MatchEvidence]:
        """
        Refina candidatos con scoring combinado.

        Args:
            rubro: Rubro ET
            candidates_indices: Índices de candidatos
            semantic_scores: Scores semánticos

        Returns:
            Lista de MatchEvidence ordenada por combined_score
        """
        evidences = []

        for idx, semantic_score in zip(candidates_indices, semantic_scores):
            candidate = self.reference_rubros[idx]

            # Score combinado
            combined, method = calculate_match_score(
                et_description=rubro.descripcion,
                wbs_description=candidate.description,
                et_code=rubro.codigo,
                wbs_code=candidate.wbs_code,
                et_unit=rubro.unidad,
                wbs_unit=candidate.unit,
                semantic_score=semantic_score,
                weights=None  # Usa pesos por defecto
            )

            # Fuzzy score para evidencia
            fuzzy_score = fuzzy_similarity(
                rubro.descripcion,
                candidate.description,
                method="token_set_ratio"
            )

            evidence = MatchEvidence(
                wbs_code=candidate.wbs_code,
                wbs_description=candidate.description,
                similarity_score=semantic_score,
                fuzzy_score=fuzzy_score,
                combined_score=combined,
                match_method=method,
                snippet_et=rubro.descripcion[:200],
                snippet_wbs=candidate.description[:200]
            )

            evidences.append(evidence)

        # Ordenar por combined_score descendente
        evidences.sort(key=lambda e: e.combined_score, reverse=True)

        return evidences

    def _classify_match(
        self,
        rubro: Rubro,
        evidences: List[MatchEvidence],
        processing_time_ms: float
    ) -> MatchResult:
        """
        Clasifica el resultado del matching.

        Args:
            rubro: Rubro ET
            evidences: Lista de evidencias ordenadas
            processing_time_ms: Tiempo de procesamiento

        Returns:
            MatchResult con clasificación apropiada
        """
        if not evidences:
            # No hay candidatos
            return MatchResult(
                et_rubro_id=rubro.rubro_id,
                et_code=rubro.codigo,
                et_description=rubro.descripcion,
                status=MatchStatus.NO_MATCH,
                best_match=None,
                alternative_matches=[],
                confidence=0.0,
                processing_time_ms=processing_time_ms
            )

        best_evidence = evidences[0]
        best_score = best_evidence.combined_score

        # Determinar status
        if best_score >= self.settings.MATCH_THRESHOLD:
            # Verificar ambigüedad
            if len(evidences) > 1:
                second_score = evidences[1].combined_score
                if (best_score - second_score) < self.settings.MATCH_AMBIGUOUS_THRESHOLD:
                    status = MatchStatus.AMBIGUOUS
                else:
                    status = MatchStatus.MATCHED
            else:
                status = MatchStatus.MATCHED

        elif best_score >= self.settings.MATCH_AMBIGUOUS_THRESHOLD:
            # Score intermedio → requiere revisión manual
            status = MatchStatus.MANUAL_REVIEW

        else:
            # Score bajo → no match
            status = MatchStatus.NO_MATCH

        # Seleccionar alternativas (top 3 además del mejor)
        alternatives = evidences[1:4] if len(evidences) > 1 else []

        return MatchResult(
            et_rubro_id=rubro.rubro_id,
            et_code=rubro.codigo,
            et_description=rubro.descripcion,
            status=status,
            best_match=best_evidence if status != MatchStatus.NO_MATCH else None,
            alternative_matches=alternatives,
            confidence=best_score,
            processing_time_ms=processing_time_ms
        )


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════

def load_reference_rubros_from_excel(
    excel_path: Path,
    sheet_name: str = "WBS",
    code_col: str = "Código",
    desc_col: str = "Descripción",
    unit_col: Optional[str] = "Unidad",
    category_col: Optional[str] = "Especialidad"
) -> List[ReferenceRubro]:
    """
    Carga rubros de referencia desde un archivo Excel.

    Args:
        excel_path: Ruta al archivo Excel
        sheet_name: Nombre de la hoja
        code_col: Nombre de columna de código
        desc_col: Nombre de columna de descripción
        unit_col: Nombre de columna de unidad (opcional)
        category_col: Nombre de columna de categoría (opcional)

    Returns:
        Lista de ReferenceRubro
    """
    import pandas as pd

    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    reference_rubros = []
    for _, row in df.iterrows():
        rubro = ReferenceRubro(
            wbs_code=str(row[code_col]),
            description=str(row[desc_col]),
            unit=str(row[unit_col]) if unit_col and unit_col in df.columns else None,
            category=str(row[category_col]) if category_col and category_col in df.columns else None
        )
        reference_rubros.append(rubro)

    logger.info(f"✅ Cargados {len(reference_rubros)} rubros de referencia desde {excel_path}")
    return reference_rubros
