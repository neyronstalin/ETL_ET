"""
Generador de reportes individuales por rubro (rubros_md/*.md).

Cada rubro obtiene un archivo MD con:
- Información completa del rubro
- Recursos asociados
- Evidencia de matching (si aplica)
- Trazabilidad (páginas, snippets, confidence)
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
import logging

from src.models.schemas import (
    Rubro, Recurso, MatchResult, MatchStatus, ArtifactMetadata
)
from src.utils.text_norm import sanitize_excel_sheet_name

logger = logging.getLogger(__name__)


def generate_rubro_reports(
    rubros: List[Rubro],
    recursos: List[Recurso],
    match_results: Optional[List[MatchResult]],
    output_dir: Path
) -> List[ArtifactMetadata]:
    """
    Genera reportes MD individuales para cada rubro.

    Args:
        rubros: Lista de rubros
        recursos: Lista de recursos
        match_results: Resultados de matching (opcional)
        output_dir: Directorio donde guardar (rubros_md/)

    Returns:
        Lista de ArtifactMetadata de archivos generados
    """
    logger.info(f"Generando reportes individuales para {len(rubros)} rubros...")

    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)

    # Mapear recursos por rubro_id
    recursos_by_rubro = {}
    for recurso in recursos:
        if recurso.rubro_id not in recursos_by_rubro:
            recursos_by_rubro[recurso.rubro_id] = []
        recursos_by_rubro[recurso.rubro_id].append(recurso)

    # Mapear match results por rubro_id
    matches_by_rubro = {}
    if match_results:
        for match in match_results:
            matches_by_rubro[match.et_rubro_id] = match

    # Generar reporte para cada rubro
    artifacts = []
    for i, rubro in enumerate(rubros, 1):
        if i % 50 == 0:
            logger.info(f"  Progreso: {i}/{len(rubros)}")

        rubro_recursos = recursos_by_rubro.get(rubro.rubro_id, [])
        rubro_match = matches_by_rubro.get(rubro.rubro_id)

        artifact = generate_single_rubro_report(
            rubro=rubro,
            recursos=rubro_recursos,
            match_result=rubro_match,
            output_dir=output_dir
        )

        artifacts.append(artifact)

    logger.info(f"✅ Reportes generados: {len(artifacts)} archivos")

    return artifacts


def generate_single_rubro_report(
    rubro: Rubro,
    recursos: List[Recurso],
    match_result: Optional[MatchResult],
    output_dir: Path
) -> ArtifactMetadata:
    """
    Genera reporte MD para un único rubro.

    Args:
        rubro: Rubro a reportar
        recursos: Recursos del rubro
        match_result: Resultado de matching (opcional)
        output_dir: Directorio de salida

    Returns:
        ArtifactMetadata del archivo generado
    """
    # Generar nombre de archivo seguro
    filename = _generate_safe_filename(rubro)
    output_path = output_dir / filename

    # Construir contenido
    sections = [
        _generate_rubro_header(rubro),
        _generate_rubro_info(rubro),
        _generate_matching_info(match_result),
        _generate_recursos_section(recursos),
        _generate_traceability_section(rubro),
        _generate_metadata_section(rubro)
    ]

    content = "\n\n".join([s for s in sections if s])  # Filtrar secciones vacías

    # Escribir archivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Crear metadata
    artifact = ArtifactMetadata(
        artifact_type="rubro.md",
        file_path=str(output_path),
        size_bytes=output_path.stat().st_size,
        generated_at=datetime.now()
    )

    return artifact


def _generate_safe_filename(rubro: Rubro) -> str:
    """
    Genera nombre de archivo seguro para el rubro.

    Args:
        rubro: Rubro

    Returns:
        Nombre de archivo tipo "01_01_01_descripcion.md"
    """
    # Normalizar código
    code_safe = rubro.codigo.replace(".", "_").replace(" ", "_")
    code_safe = sanitize_excel_sheet_name(code_safe)

    # Truncar descripción
    desc_safe = rubro.descripcion[:30].strip()
    desc_safe = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in desc_safe)
    desc_safe = desc_safe.replace(" ", "_")

    return f"{code_safe}_{desc_safe}.md"


def _generate_rubro_header(rubro: Rubro) -> str:
    """Genera encabezado del reporte."""
    return f"""# {rubro.codigo} - {rubro.descripcion}

**ID:** `{rubro.rubro_id}`

---"""


def _generate_rubro_info(rubro: Rubro) -> str:
    """Genera información básica del rubro."""
    confidence_bar = "🟢" if rubro.confidence >= 0.8 else "🟡" if rubro.confidence >= 0.6 else "🔴"

    metodo_section = ""
    if rubro.metodo_constructivo:
        metodo_section = f"""
### Método Constructivo
{rubro.metodo_constructivo}"""

    return f"""## 📋 Información del Rubro

| Atributo | Valor |
|----------|-------|
| **Código** | `{rubro.codigo}` |
| **Descripción** | {rubro.descripcion} |
| **Unidad** | {rubro.unidad} |
| **Confianza** | {confidence_bar} {rubro.confidence * 100:.1f}% |
| **Páginas Fuente** | {', '.join(map(str, rubro.source_pages))} |{metodo_section}"""


def _generate_matching_info(match_result: Optional[MatchResult]) -> str:
    """Genera sección de matching (si aplica)."""
    if not match_result:
        return ""

    status_icon = {
        MatchStatus.MATCHED: "✅",
        MatchStatus.AMBIGUOUS: "⚠️",
        MatchStatus.NO_MATCH: "❌",
        MatchStatus.MANUAL_REVIEW: "⏳"
    }

    icon = status_icon.get(match_result.status, "❓")

    best_match_section = ""
    if match_result.best_match:
        bm = match_result.best_match
        best_match_section = f"""
### Mejor Candidato

| Atributo | Valor |
|----------|-------|
| **Código WBS** | `{bm.wbs_code}` |
| **Descripción WBS** | {bm.wbs_description} |
| **Score Semántico** | {bm.similarity_score * 100:.1f}% |
| **Score Fuzzy** | {bm.fuzzy_score:.1f}% |
| **Score Combinado** | {bm.combined_score * 100:.1f}% |
| **Método** | {bm.match_method} |"""

    alternatives_section = ""
    if match_result.alternative_matches:
        alternatives_section = "\n### Candidatos Alternativos\n\n"
        alternatives_section += "| Código WBS | Descripción | Score |\n"
        alternatives_section += "|------------|-------------|-------|\n"
        for alt in match_result.alternative_matches[:3]:  # Top 3
            alternatives_section += f"| `{alt.wbs_code}` | {alt.wbs_description[:50]}... | {alt.combined_score * 100:.1f}% |\n"

    return f"""## 🎯 Matching Semántico

{icon} **Estado:** {match_result.status.value}
**Confianza:** {match_result.confidence * 100:.1f}%
**Tiempo de Procesamiento:** {match_result.processing_time_ms:.2f} ms{best_match_section}{alternatives_section}"""


def _generate_recursos_section(recursos: List[Recurso]) -> str:
    """Genera sección de recursos."""
    if not recursos:
        return "## 📦 Recursos\n\n_No se extrajeron recursos para este rubro_"

    recursos_by_tipo = {}
    for recurso in recursos:
        tipo = recurso.tipo.value
        if tipo not in recursos_by_tipo:
            recursos_by_tipo[tipo] = []
        recursos_by_tipo[tipo].append(recurso)

    tipo_sections = []
    for tipo, tipo_recursos in recursos_by_tipo.items():
        tipo_icon = {
            "MATERIAL": "🧱",
            "EQUIPO": "🔧",
            "MANO_DE_OBRA": "👷",
            "DESCONOCIDO": "❓"
        }
        icon = tipo_icon.get(tipo, "📦")

        table = "| Nombre | Unidad | Cantidad | Confianza |\n"
        table += "|--------|--------|----------|------------|\n"

        for r in tipo_recursos:
            cantidad_str = f"{r.cantidad:.2f}" if r.cantidad else "N/A"
            unidad_str = r.unidad or "N/A"
            table += f"| {r.nombre} | {unidad_str} | {cantidad_str} | {r.confidence * 100:.0f}% |\n"

        tipo_sections.append(f"### {icon} {tipo}\n\n{table}")

    return f"""## 📦 Recursos Asociados

**Total:** {len(recursos)}

{chr(10).join(tipo_sections)}"""


def _generate_traceability_section(rubro: Rubro) -> str:
    """Genera sección de trazabilidad."""
    pages_list = ', '.join([f"p. {p}" for p in rubro.source_pages])

    return f"""## 🔍 Trazabilidad

### Páginas Fuente
- **Páginas:** {pages_list}
- **Confidence:** {rubro.confidence * 100:.1f}%

### Información Técnica
- **Rubro ID:** `{rubro.rubro_id}`
- **Timestamp:** {rubro.created_at.strftime('%Y-%m-%d %H:%M:%S')}"""


def _generate_metadata_section(rubro: Rubro) -> str:
    """Genera sección de metadatos."""
    return f"""---

_Reporte generado automáticamente por ETL Pipeline v1.1_
_Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"""


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE BÚSQUEDA Y FILTRADO
# ═══════════════════════════════════════════════════════════════════════════

def find_rubro_report(codigo: str, rubros_dir: Path) -> Optional[Path]:
    """
    Busca el archivo MD de un rubro por código.

    Args:
        codigo: Código del rubro (ej: "01.01.01")
        rubros_dir: Directorio rubros_md/

    Returns:
        Path al archivo MD o None si no existe
    """
    code_pattern = codigo.replace(".", "_")

    for md_file in rubros_dir.glob(f"{code_pattern}_*.md"):
        return md_file

    return None


def get_rubros_by_category(rubros_dir: Path, category_prefix: str) -> List[Path]:
    """
    Obtiene reportes de rubros por categoría (prefijo de código).

    Args:
        rubros_dir: Directorio rubros_md/
        category_prefix: Prefijo (ej: "01_01" para todos los 01.01.XX)

    Returns:
        Lista de Paths a archivos MD
    """
    pattern = f"{category_prefix}_*.md"
    return sorted(rubros_dir.glob(pattern))
