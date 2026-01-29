"""
Modelos Pydantic para el pipeline de extracción de especificaciones técnicas.

Estos modelos definen los contratos de datos entre los módulos y garantizan
validación de tipos en runtime.
"""

from typing import Optional, List, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class TipoRecurso(str, Enum):
    """Tipos de recursos en un rubro."""
    MATERIAL = "MATERIAL"
    EQUIPO = "EQUIPO"
    MANO_DE_OBRA = "MANO_DE_OBRA"
    DESCONOCIDO = "DESCONOCIDO"


class TipoDocumento(str, Enum):
    """Tipo de PDF según contenido."""
    DIGITAL = "DIGITAL"        # Tiene texto extraíble
    ESCANEADO = "ESCANEADO"    # Requiere OCR
    MIXTO = "MIXTO"            # Algunas páginas digitales, otras escaneadas


class WarningKind(str, Enum):
    """Categorías de warnings durante el parseo."""
    RUBRO_INCOMPLETE = "RUBRO_INCOMPLETE"           # Falta codigo/descripcion/unidad
    UNIDAD_DESCONOCIDA = "UNIDAD_DESCONOCIDA"       # Unidad no reconocida
    RECURSO_SIN_TIPO = "RECURSO_SIN_TIPO"           # No se pudo clasificar MATERIAL/EQUIPO
    OCR_BAJA_CONFIANZA = "OCR_BAJA_CONFIANZA"       # Confidence < threshold
    FORMATO_INVALIDO = "FORMATO_INVALIDO"           # Estructura no esperada
    PARSING_ERROR = "PARSING_ERROR"                 # Error general de parseo


# ═══════════════════════════════════════════════════════════════════════════
# MODELOS PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════

class Rubro(BaseModel):
    """
    Representa un rubro de especificaciones técnicas.

    Attributes:
        rubro_id: Identificador único generado (UUID o secuencial)
        codigo: Código del rubro en el documento (ej: "01.01.01")
        descripcion: Descripción completa del rubro
        unidad: Unidad de medida (m, m2, m3, kg, u, etc.)
        source_pages: Lista de páginas donde aparece el rubro
        confidence: Score de confianza del parseo (0.0 - 1.0)
        metodo_constructivo: Opcional, descripción del método (si existe)
        created_at: Timestamp de creación
    """

    model_config = ConfigDict(use_enum_values=True)

    rubro_id: str = Field(..., description="ID único del rubro")
    codigo: str = Field(..., min_length=1, description="Código del rubro (ej: 01.01.01)")
    descripcion: str = Field(..., min_length=1, description="Descripción del rubro")
    unidad: str = Field(..., description="Unidad de medida")
    source_pages: List[int] = Field(default_factory=list, description="Páginas de origen")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confianza del parseo (0-1)"
    )
    metodo_constructivo: Optional[str] = Field(
        default=None,
        description="Descripción del método constructivo"
    )
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        """Valida formato de código (básico)."""
        v = v.strip()
        if not v:
            raise ValueError("Código no puede estar vacío")
        return v

    @field_validator('unidad')
    @classmethod
    def normalizar_unidad(cls, v: str) -> str:
        """Normaliza unidad de medida."""
        # Mapeo de variaciones comunes
        UNIDADES_MAP = {
            'm2': 'm²', 'm3': 'm³', 'mt': 'm', 'mts': 'm',
            'kg.': 'kg', 'und': 'u', 'unid': 'u', 'unidad': 'u'
        }
        v_lower = v.lower().strip()
        return UNIDADES_MAP.get(v_lower, v.strip())


class Recurso(BaseModel):
    """
    Representa un recurso (material/equipo) dentro de un rubro.

    Attributes:
        recurso_id: ID único del recurso
        rubro_id: ID del rubro padre
        tipo: MATERIAL | EQUIPO | MANO_DE_OBRA | DESCONOCIDO
        nombre: Descripción del recurso
        unidad: Unidad de medida del recurso (puede diferir del rubro)
        cantidad: Cantidad requerida (opcional, puede no estar especificada)
        confidence: Score de confianza (0-1)
        source_snippet: Fragmento de texto original
    """

    model_config = ConfigDict(use_enum_values=True)

    recurso_id: str = Field(..., description="ID único del recurso")
    rubro_id: str = Field(..., description="ID del rubro padre")
    tipo: TipoRecurso = Field(default=TipoRecurso.DESCONOCIDO)
    nombre: str = Field(..., min_length=1, description="Nombre/descripción del recurso")
    unidad: Optional[str] = Field(default=None, description="Unidad del recurso")
    cantidad: Optional[float] = Field(default=None, ge=0, description="Cantidad")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_snippet: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Fragmento de texto original"
    )
    created_at: datetime = Field(default_factory=datetime.now)


class ParseWarning(BaseModel):
    """
    Representa un warning/error durante el parseo.

    Se usa para trazabilidad: registrar qué no se pudo parsear correctamente.
    """

    model_config = ConfigDict(use_enum_values=True)

    warning_id: str = Field(..., description="ID único del warning")
    rubro_id: Optional[str] = Field(default=None, description="Rubro asociado (si existe)")
    page: Optional[int] = Field(default=None, description="Número de página")
    kind: WarningKind = Field(..., description="Tipo de warning")
    message: str = Field(..., description="Mensaje descriptivo")
    snippet: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Fragmento de texto problemático"
    )
    severity: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        default="MEDIUM",
        description="Severidad del warning"
    )
    created_at: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════
# MODELOS AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

class PageMetadata(BaseModel):
    """Metadatos de una página procesada."""

    page_number: int = Field(..., ge=1)
    tipo_documento: TipoDocumento
    ocr_applied: bool = Field(default=False)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    processing_time_ms: Optional[float] = Field(default=None)
    text_length: int = Field(default=0, ge=0)


class DocumentMetadata(BaseModel):
    """Metadatos del documento completo."""

    filename: str
    total_pages: int = Field(..., ge=1)
    tipo_documento: TipoDocumento
    pages_with_ocr: List[int] = Field(default_factory=list)
    processing_date: datetime = Field(default_factory=datetime.now)
    total_rubros: int = Field(default=0, ge=0)
    total_recursos: int = Field(default=0, ge=0)
    total_warnings: int = Field(default=0, ge=0)


class PipelineResult(BaseModel):
    """
    Resultado completo del pipeline de extracción.

    Este es el output final que se exporta a Excel.
    """

    metadata: DocumentMetadata
    rubros: List[Rubro] = Field(default_factory=list)
    recursos: List[Recurso] = Field(default_factory=list)
    warnings: List[ParseWarning] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calcula tasa de éxito (rubros sin warnings / total rubros)."""
        if not self.rubros:
            return 0.0
        rubros_con_warnings = len({w.rubro_id for w in self.warnings if w.rubro_id})
        rubros_ok = len(self.rubros) - rubros_con_warnings
        return rubros_ok / len(self.rubros)

    def get_warnings_by_severity(self, severity: str) -> List[ParseWarning]:
        """Filtra warnings por severidad."""
        return [w for w in self.warnings if w.severity == severity]


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES HELPER
# ═══════════════════════════════════════════════════════════════════════════

def generar_rubro_id(codigo: str, page: int) -> str:
    """
    Genera ID único para un rubro basado en código y página.

    Args:
        codigo: Código del rubro (ej: "01.01.01")
        page: Número de página

    Returns:
        ID en formato: "RUB_{codigo}_{page}"
    """
    codigo_clean = codigo.replace(".", "_")
    return f"RUB_{codigo_clean}_P{page}"


def generar_recurso_id(rubro_id: str, index: int) -> str:
    """
    Genera ID único para un recurso.

    Args:
        rubro_id: ID del rubro padre
        index: Índice del recurso dentro del rubro (0-based)

    Returns:
        ID en formato: "{rubro_id}_REC{index}"
    """
    return f"{rubro_id}_REC{index:03d}"


def generar_warning_id(page: int, kind: WarningKind) -> str:
    """Genera ID para un warning."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"WARN_P{page}_{kind.value}_{timestamp}"


# ═══════════════════════════════════════════════════════════════════════════
# MODELOS v1.1 - CONVERSION
# ═══════════════════════════════════════════════════════════════════════════

class ConversionStrategy(str, Enum):
    """Estrategias de conversión disponibles."""
    DOCLING = "docling"      # IBM Docling (más preciso, más lento)
    MARKER = "marker"        # Marker (rápido, bueno con tablas)
    PYMUPDF = "pymupdf"      # PyMuPDF4LLM (más rápido, simple)
    AUTO = "auto"            # Selección automática con cascada


class ConversionResult(BaseModel):
    """
    Resultado de la conversión de PDF a formato estructurado.

    Attributes:
        success: Si la conversión fue exitosa
        strategy_used: Estrategia que funcionó
        markdown_content: Contenido en formato Markdown
        json_content: Contenido estructurado (outline, secciones, tablas)
        metadata: Metadatos de la conversión (tiempo, páginas, etc.)
        fallback_chain: Lista de estrategias intentadas antes del éxito
    """

    success: bool = Field(..., description="Conversión exitosa")
    strategy_used: ConversionStrategy = Field(..., description="Estrategia utilizada")
    markdown_content: str = Field(..., description="Contenido en Markdown")
    json_content: dict = Field(default_factory=dict, description="Contenido estructurado")
    metadata: dict = Field(default_factory=dict, description="Metadatos de conversión")
    fallback_chain: List[str] = Field(
        default_factory=list,
        description="Estrategias intentadas"
    )
    processing_time_s: float = Field(..., ge=0, description="Tiempo de procesamiento")
    warnings: List[str] = Field(default_factory=list, description="Warnings generados")


# ═══════════════════════════════════════════════════════════════════════════
# MODELOS v1.1 - MATCHING SEMÁNTICO
# ═══════════════════════════════════════════════════════════════════════════

class MatchStatus(str, Enum):
    """Estado del matching entre ET y WBS."""
    MATCHED = "MATCHED"              # Match exitoso con alta confianza
    AMBIGUOUS = "AMBIGUOUS"          # Múltiples candidatos con scores similares
    NO_MATCH = "NO_MATCH"            # No se encontró match
    MANUAL_REVIEW = "MANUAL_REVIEW"  # Requiere revisión manual


class MatchEvidence(BaseModel):
    """Evidencia de un match entre rubro ET y referencia WBS."""

    wbs_code: str = Field(..., description="Código WBS candidato")
    wbs_description: str = Field(..., description="Descripción WBS")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Score semántico")
    fuzzy_score: float = Field(..., ge=0.0, le=100.0, description="Score fuzzy (string)")
    combined_score: float = Field(..., ge=0.0, le=1.0, description="Score combinado")
    match_method: str = Field(..., description="Método usado (semantic/fuzzy/hybrid)")
    snippet_et: Optional[str] = Field(default=None, description="Snippet del ET")
    snippet_wbs: Optional[str] = Field(default=None, description="Snippet del WBS")


class MatchResult(BaseModel):
    """
    Resultado del matching de un rubro ET contra la base WBS.

    Attributes:
        et_rubro_id: ID del rubro en ET
        et_code: Código del rubro en ET (puede estar ausente)
        et_description: Descripción del rubro en ET
        status: Estado del match (MATCHED/AMBIGUOUS/NO_MATCH/MANUAL_REVIEW)
        best_match: Mejor candidato (si existe)
        alternative_matches: Candidatos alternativos (para ambiguos)
        confidence: Confianza global del match (0-1)
    """

    et_rubro_id: str = Field(..., description="ID del rubro ET")
    et_code: Optional[str] = Field(default=None, description="Código ET (si existe)")
    et_description: str = Field(..., description="Descripción ET")
    status: MatchStatus = Field(..., description="Estado del matching")
    best_match: Optional[MatchEvidence] = Field(
        default=None,
        description="Mejor candidato"
    )
    alternative_matches: List[MatchEvidence] = Field(
        default_factory=list,
        description="Candidatos alternativos"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza global")
    processing_time_ms: float = Field(..., ge=0, description="Tiempo de matching")


class ReferenceRubro(BaseModel):
    """Rubro de referencia desde archivo WBS (Excel/CSV)."""

    wbs_code: str = Field(..., description="Código WBS normalizado")
    description: str = Field(..., min_length=1, description="Descripción")
    unit: Optional[str] = Field(default=None, description="Unidad")
    category: Optional[str] = Field(default=None, description="Categoría/Especialidad")
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Vector de embedding (generado en runtime)"
    )

    @field_validator('wbs_code')
    @classmethod
    def normalize_wbs_code(cls, v: str) -> str:
        """Normaliza código WBS."""
        from src.utils.text_norm import normalize_rubro_code
        return normalize_rubro_code(v)


# ═══════════════════════════════════════════════════════════════════════════
# MODELOS v1.1 - DEDUPLICACIÓN
# ═══════════════════════════════════════════════════════════════════════════

class DuplicateStrategy(str, Enum):
    """Estrategias de resolución de duplicados."""
    MERGE = "MERGE"      # Duplicados exactos → merge
    SPLIT = "SPLIT"      # Conflictos → split con sufijos (#A, #B)
    HASH = "HASH"        # Sin código → generar código hash


class ConflictType(str, Enum):
    """Tipos de conflictos entre duplicados."""
    DESCRIPTION = "DESCRIPTION"  # Mismo código, descripciones diferentes
    UNIT = "UNIT"                # Mismo código, unidades diferentes
    RESOURCES = "RESOURCES"      # Mismo código, recursos diferentes


class DuplicateGroup(BaseModel):
    """
    Grupo de rubros duplicados detectados.

    Attributes:
        group_id: ID único del grupo
        canonical_code: Código canónico (normalizado)
        rubro_ids: Lista de IDs de rubros duplicados
        strategy: Estrategia de resolución aplicada
        conflicts: Lista de conflictos detectados
        resolved_rubros: Rubros después de resolver
    """

    group_id: str = Field(..., description="ID del grupo")
    canonical_code: str = Field(..., description="Código canónico")
    rubro_ids: List[str] = Field(..., min_length=2, description="IDs de duplicados")
    strategy: DuplicateStrategy = Field(..., description="Estrategia aplicada")
    conflicts: List[ConflictType] = Field(
        default_factory=list,
        description="Tipos de conflictos"
    )
    resolved_rubros: List[Rubro] = Field(
        default_factory=list,
        description="Rubros resueltos"
    )
    merge_count: int = Field(default=0, ge=0, description="Cantidad de merges")
    split_count: int = Field(default=0, ge=0, description="Cantidad de splits")


# ═══════════════════════════════════════════════════════════════════════════
# MODELOS v1.1 - REPORTES
# ═══════════════════════════════════════════════════════════════════════════

class ArtifactMetadata(BaseModel):
    """Metadatos de artefactos generados (MD, JSON)."""

    artifact_type: Literal["ET.md", "ET.json", "OUTLINE.md", "RUN_REPORT.md", "rubro.md", "OUT.json"]
    file_path: str = Field(..., description="Ruta del archivo generado")
    size_bytes: int = Field(..., ge=0)
    generated_at: datetime = Field(default_factory=datetime.now)
    checksum: Optional[str] = Field(default=None, description="Hash MD5 del archivo")


class PipelineResultV1_1(BaseModel):
    """
    Resultado extendido del pipeline v1.1.

    Incluye todo de v1.0 + conversión + matching + dedup + artifacts.
    """

    # Heredado de v1.0
    metadata: DocumentMetadata
    rubros: List[Rubro] = Field(default_factory=list)
    recursos: List[Recurso] = Field(default_factory=list)
    warnings: List[ParseWarning] = Field(default_factory=list)

    # Nuevo en v1.1
    conversion_result: Optional[ConversionResult] = Field(
        default=None,
        description="Resultado de conversión a MD/JSON"
    )
    match_results: List[MatchResult] = Field(
        default_factory=list,
        description="Resultados de matching WBS"
    )
    duplicate_groups: List[DuplicateGroup] = Field(
        default_factory=list,
        description="Grupos de duplicados resueltos"
    )
    artifacts: List[ArtifactMetadata] = Field(
        default_factory=list,
        description="Artefactos generados (MD, JSON)"
    )

    @property
    def match_success_rate(self) -> float:
        """% de rubros con match exitoso."""
        if not self.match_results:
            return 0.0
        matched = len([m for m in self.match_results if m.status == MatchStatus.MATCHED])
        return matched / len(self.match_results)

    @property
    def dedup_stats(self) -> dict:
        """Estadísticas de deduplicación."""
        total_merged = sum(g.merge_count for g in self.duplicate_groups)
        total_split = sum(g.split_count for g in self.duplicate_groups)
        return {
            "duplicate_groups": len(self.duplicate_groups),
            "total_merged": total_merged,
            "total_split": total_split
        }
