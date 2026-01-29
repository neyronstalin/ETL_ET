"""
Configuración global del pipeline usando Pydantic Settings.

Variables cargadas desde .env con defaults sensatos.
"""

from pathlib import Path
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Configuración global del pipeline ETL_ET v1.1.

    Variables se cargan desde:
    1. Variables de entorno
    2. Archivo .env (si existe)
    3. Valores por defecto (definidos aquí)

    Example:
        >>> from src.config.settings import get_settings
        >>> settings = get_settings()
        >>> print(settings.OCR_LANG)
        'spa'
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # PATHS
    # ═══════════════════════════════════════════════════════════════════════

    DATA_INPUT_DIR: Path = Field(
        default=Path("data/input"),
        description="Directorio de PDFs de entrada"
    )

    DATA_OUTPUT_DIR: Path = Field(
        default=Path("data/output"),
        description="Directorio de Excel de salida"
    )

    DATA_CACHE_DIR: Path = Field(
        default=Path("data/cache"),
        description="Directorio de cache (OCR, embeddings)"
    )

    DATA_ARTIFACTS_DIR: Path = Field(
        default=Path("data/artifacts"),
        description="Directorio de artefactos (ET.md, OUT.json, etc.)"
    )

    TEMPLATES_DIR: Path = Field(
        default=Path("data/templates"),
        description="Directorio de templates Excel"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # TESSERACT OCR
    # ═══════════════════════════════════════════════════════════════════════

    TESSERACT_CMD: Optional[str] = Field(
        default=None,
        description="Ruta al ejecutable de Tesseract (solo si no está en PATH)"
    )

    OCR_LANG: str = Field(
        default="spa",
        description="Idioma para OCR (spa, eng, spa+eng)"
    )

    OCR_DPI: int = Field(
        default=300,
        ge=100,
        le=600,
        description="DPI para conversión PDF→Imagen en OCR"
    )

    OCR_CONFIDENCE_THRESHOLD: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Threshold de confidence para warning OCR"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CONVERSIÓN (v1.1)
    # ═══════════════════════════════════════════════════════════════════════

    CONVERSION_STRATEGY: Literal["auto", "docling", "marker", "pymupdf"] = Field(
        default="auto",
        description="Estrategia de conversión PDF→MD/JSON"
    )

    CONVERSION_TIMEOUT_SECONDS: int = Field(
        default=300,
        ge=60,
        description="Timeout por página en conversión (segundos)"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # MATCHING SEMÁNTICO (v1.1)
    # ═══════════════════════════════════════════════════════════════════════

    EMBEDDING_MODEL: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2",
        description="Modelo de sentence-transformers"
    )

    EMBEDDING_BATCH_SIZE: int = Field(
        default=32,
        ge=1,
        le=128,
        description="Batch size para generación de embeddings"
    )

    EMBEDDING_CACHE_ENABLED: bool = Field(
        default=True,
        description="Habilitar cache de embeddings"
    )

    MATCH_THRESHOLD: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Threshold para match aceptado (≥0.75 = MATCHED)"
    )

    MATCH_AMBIGUOUS_THRESHOLD: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Threshold para match ambiguo (0.65-0.75 = AMBIGUOUS)"
    )

    FUZZY_MATCH_THRESHOLD: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Threshold para fuzzy matching (rapidfuzz)"
    )

    USE_FAISS: bool = Field(
        default=True,
        description="Usar FAISS para búsqueda vectorial (solo si >1000 rubros)"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # PARSING Y EXTRACCIÓN
    # ═══════════════════════════════════════════════════════════════════════

    MIN_RUBRO_LENGTH: int = Field(
        default=10,
        ge=5,
        description="Longitud mínima de descripción de rubro (caracteres)"
    )

    MAX_SNIPPET_LENGTH: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Longitud máxima de snippet en evidencias (caracteres)"
    )

    MAX_RESOURCES_PER_RUBRO: int = Field(
        default=50,
        ge=10,
        description="Máximo de recursos por rubro (truncar si excede)"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # EXPORT
    # ═══════════════════════════════════════════════════════════════════════

    EXPORT_MODE: Literal["auto", "per-rubro", "global"] = Field(
        default="auto",
        description="Modo de export Excel (per-rubro=1 hoja por rubro, global=5 hojas)"
    )

    EXCEL_APPLY_FORMATTING: bool = Field(
        default=True,
        description="Aplicar formato a Excel (colores, anchos)"
    )

    EXCEL_MAX_RUBROS_PER_SHEET: int = Field(
        default=100,
        ge=10,
        description="Máximo rubros para modo per-rubro (si >100 → global)"
    )

    OUTPUT_SUFFIX: str = Field(
        default="_resultado",
        description="Sufijo para archivos de salida"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # REPORTES (v1.1)
    # ═══════════════════════════════════════════════════════════════════════

    WRITE_ARTIFACTS: bool = Field(
        default=True,
        description="Escribir artefactos (ET.md, OUT.json, RUN_REPORT.md, etc.)"
    )

    MAX_RUBRO_REPORT_LINES: int = Field(
        default=30,
        ge=10,
        description="Máximo de líneas de snippet en rubro report"
    )

    GENERATE_RUBRO_MD: bool = Field(
        default=True,
        description="Generar rubros_md/*.md (1 por rubro)"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # LOGGING
    # ═══════════════════════════════════════════════════════════════════════

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Nivel de logging"
    )

    LOG_JSON: bool = Field(
        default=False,
        description="Usar formato JSON en logs (producción)"
    )

    LOG_FILE: Optional[Path] = Field(
        default=None,
        description="Ruta al archivo de log (opcional)"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # PERFORMANCE
    # ═══════════════════════════════════════════════════════════════════════

    NUM_WORKERS: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Número de workers para procesamiento paralelo (futuro)"
    )

    ENABLE_CACHE: bool = Field(
        default=True,
        description="Habilitar cache general (OCR + embeddings)"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # VALIDATORS
    # ═══════════════════════════════════════════════════════════════════════

    @field_validator('MATCH_AMBIGUOUS_THRESHOLD')
    @classmethod
    def validate_ambiguous_threshold(cls, v, info):
        """Ambiguous threshold debe ser menor que match threshold."""
        match_threshold = info.data.get('MATCH_THRESHOLD', 0.75)
        if v >= match_threshold:
            raise ValueError(
                f"MATCH_AMBIGUOUS_THRESHOLD ({v}) debe ser < MATCH_THRESHOLD ({match_threshold})"
            )
        return v

    @field_validator('DATA_INPUT_DIR', 'DATA_OUTPUT_DIR', 'DATA_CACHE_DIR',
                     'DATA_ARTIFACTS_DIR', 'TEMPLATES_DIR')
    @classmethod
    def ensure_path_exists(cls, v):
        """Crear directorios si no existen."""
        if v and not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON PATTERN
# ═══════════════════════════════════════════════════════════════════════════

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Obtiene la instancia global de Settings (singleton).

    Returns:
        Settings: Configuración global

    Example:
        >>> settings = get_settings()
        >>> print(settings.OCR_LANG)
        'spa'
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Recarga settings desde .env (útil para tests).

    Returns:
        Settings: Nueva instancia de configuración
    """
    global _settings
    _settings = Settings()
    return _settings


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = ["Settings", "get_settings", "reload_settings"]
