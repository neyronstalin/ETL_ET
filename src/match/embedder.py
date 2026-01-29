"""
Módulo de generación de embeddings para matching semántico.

Usa sentence-transformers para generar vectores densos que representan
semánticamente las descripciones de rubros.

Modelo recomendado: paraphrase-multilingual-MiniLM-L12-v2
- Soporta español
- Rápido (12 capas)
- Buena calidad para matching
- ~120MB
"""

from typing import List, Optional
import numpy as np
from pathlib import Path
import logging

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class Embedder:
    """
    Generador de embeddings semánticos.

    Usa sentence-transformers para convertir texto a vectores densos.
    Incluye caché para evitar recalcular embeddings.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        device: str = "cpu"
    ):
        """
        Inicializa el embedder.

        Args:
            model_name: Nombre del modelo sentence-transformers
            cache_dir: Directorio para cachear modelos
            device: 'cpu' o 'cuda'

        Raises:
            RuntimeError: Si sentence-transformers no está instalado
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "sentence-transformers no instalado. "
                "Instalar con: pip install sentence-transformers"
            )

        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.cache_dir = cache_dir or settings.CACHE_DIR / "embeddings"
        self.device = device

        logger.info(f"Cargando modelo de embeddings: {self.model_name}")
        self.model = SentenceTransformer(
            self.model_name,
            cache_folder=str(self.cache_dir),
            device=self.device
        )
        logger.info(f"Modelo cargado. Dimensión: {self.model.get_sentence_embedding_dimension()}")

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Genera embeddings para una lista de textos.

        Args:
            texts: Lista de textos a encodear
            batch_size: Tamaño de batch para procesamiento
            show_progress: Mostrar barra de progreso
            normalize: Normalizar vectores a unit length (mejor para cosine similarity)

        Returns:
            Array numpy de shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )

        return embeddings

    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Genera embedding para un único texto.

        Args:
            text: Texto a encodear
            normalize: Normalizar vector

        Returns:
            Vector embedding de shape (embedding_dim,)
        """
        return self.encode([text], normalize=normalize)[0]

    @property
    def embedding_dimension(self) -> int:
        """Retorna la dimensión de los embeddings."""
        return self.model.get_sentence_embedding_dimension()


class EmbeddingCache:
    """
    Caché de embeddings para evitar recalcular.

    Usa un diccionario en memoria. Para proyectos grandes,
    considerar usar FAISS o bases vectoriales.
    """

    def __init__(self):
        self._cache: dict[str, np.ndarray] = {}

    def get(self, text: str) -> Optional[np.ndarray]:
        """Obtiene embedding del caché."""
        return self._cache.get(text)

    def set(self, text: str, embedding: np.ndarray) -> None:
        """Almacena embedding en caché."""
        self._cache[text] = embedding

    def get_or_compute(
        self,
        text: str,
        embedder: Embedder,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Obtiene del caché o calcula si no existe.

        Args:
            text: Texto a encodear
            embedder: Instancia de Embedder
            normalize: Normalizar embedding

        Returns:
            Vector embedding
        """
        cached = self.get(text)
        if cached is not None:
            return cached

        embedding = embedder.encode_single(text, normalize=normalize)
        self.set(text, embedding)
        return embedding

    def clear(self) -> None:
        """Limpia el caché."""
        self._cache.clear()

    def size(self) -> int:
        """Retorna cantidad de embeddings en caché."""
        return len(self._cache)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calcula similaridad coseno entre dos vectores.

    Si los vectores están normalizados (unit length), esto se simplifica
    a un producto punto.

    Args:
        a: Vector 1
        b: Vector 2

    Returns:
        Similaridad coseno en rango [-1, 1], típicamente [0, 1] para textos
    """
    # Si los vectores están normalizados, cosine similarity = dot product
    return float(np.dot(a, b))


def batch_cosine_similarity(
    query_embedding: np.ndarray,
    corpus_embeddings: np.ndarray
) -> np.ndarray:
    """
    Calcula similaridad coseno entre un query y un corpus.

    Args:
        query_embedding: Vector de shape (embedding_dim,)
        corpus_embeddings: Matriz de shape (n_corpus, embedding_dim)

    Returns:
        Array de similaridades de shape (n_corpus,)
    """
    # Para vectores normalizados: cosine similarity = dot product
    similarities = np.dot(corpus_embeddings, query_embedding)
    return similarities


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════

_global_embedder: Optional[Embedder] = None
_global_cache: Optional[EmbeddingCache] = None


def get_embedder() -> Embedder:
    """
    Obtiene instancia global de Embedder (Singleton).

    Útil para evitar cargar el modelo múltiples veces.
    """
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = Embedder()
    return _global_embedder


def get_cache() -> EmbeddingCache:
    """Obtiene instancia global de EmbeddingCache (Singleton)."""
    global _global_cache
    if _global_cache is None:
        _global_cache = EmbeddingCache()
    return _global_cache
