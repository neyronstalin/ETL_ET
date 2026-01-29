"""
Generador de RUN_REPORT.md - Resumen ejecutivo del pipeline.

Genera un reporte Markdown legible con estadísticas, métricas y
visualización de resultados del pipeline de extracción.
"""

from pathlib import Path
from datetime import datetime
from typing import List
import logging

from src.models.schemas import (
    PipelineResultV1_1, ArtifactMetadata, MatchStatus, WarningKind
)

logger = logging.getLogger(__name__)


def generate_run_report(
    result: PipelineResultV1_1,
    output_path: Path
) -> ArtifactMetadata:
    """
    Genera RUN_REPORT.md con resumen ejecutivo.

    Args:
        result: Resultado del pipeline
        output_path: Ruta donde guardar RUN_REPORT.md

    Returns:
        ArtifactMetadata del artifact generado
    """
    logger.info(f"Generando RUN_REPORT.md en {output_path}")

    # Construir contenido del reporte
    sections = [
        _generate_header(result),
        _generate_document_info(result),
        _generate_conversion_section(result),
        _generate_extraction_stats(result),
        _generate_matching_section(result),
        _generate_deduplication_section(result),
        _generate_warnings_section(result),
        _generate_artifacts_section(result),
        _generate_footer()
    ]

    content = "\n\n".join(sections)

    # Escribir archivo
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Crear metadata
    artifact = ArtifactMetadata(
        artifact_type="RUN_REPORT.md",
        file_path=str(output_path),
        size_bytes=output_path.stat().st_size,
        generated_at=datetime.now()
    )

    logger.info(f"✅ RUN_REPORT.md generado: {output_path}")

    return artifact


def _generate_header(result: PipelineResultV1_1) -> str:
    """Genera encabezado del reporte."""
    return f"""# 📄 Reporte de Ejecución - Pipeline v1.1

**Documento:** `{result.metadata.filename}`
**Fecha de Procesamiento:** {result.metadata.processing_date.strftime('%Y-%m-%d %H:%M:%S')}
**Páginas Procesadas:** {result.metadata.total_pages}

---"""


def _generate_document_info(result: PipelineResultV1_1) -> str:
    """Genera sección de información del documento."""
    return f"""## 📊 Información del Documento

| Atributo | Valor |
|----------|-------|
| **Tipo de Documento** | {result.metadata.tipo_documento.value} |
| **Páginas con OCR** | {len(result.metadata.pages_with_ocr)} de {result.metadata.total_pages} |
| **Total Rubros Extraídos** | {result.metadata.total_rubros} |
| **Total Recursos Extraídos** | {result.metadata.total_recursos} |
| **Total Warnings** | {result.metadata.total_warnings} |"""


def _generate_conversion_section(result: PipelineResultV1_1) -> str:
    """Genera sección de conversión."""
    if not result.conversion_result:
        return "## 🔄 Conversión\n\n_No se aplicó conversión avanzada (modo legacy)_"

    conv = result.conversion_result
    success_icon = "✅" if conv.success else "❌"

    fallback_info = ""
    if conv.fallback_chain:
        fallback_info = f"\n- **Estrategias Intentadas:** {' → '.join(conv.fallback_chain)}"

    warnings_info = ""
    if conv.warnings:
        warnings_info = f"\n- **Warnings:** {len(conv.warnings)} generados"

    return f"""## 🔄 Conversión a Formato Estructurado

{success_icon} **Estado:** {'Exitosa' if conv.success else 'Fallida'}
- **Estrategia Usada:** `{conv.strategy_used.value}`{fallback_info}
- **Tiempo de Procesamiento:** {conv.processing_time_s:.2f}s
- **Contenido MD Generado:** {len(conv.markdown_content)} caracteres{warnings_info}"""


def _generate_extraction_stats(result: PipelineResultV1_1) -> str:
    """Genera estadísticas de extracción."""
    rubros_con_recursos = len(set(r.rubro_id for r in result.recursos))
    avg_recursos_per_rubro = len(result.recursos) / len(result.rubros) if result.rubros else 0
    success_rate = result.success_rate * 100

    return f"""## 🔍 Estadísticas de Extracción

### Rubros
- **Total Extraídos:** {len(result.rubros)}
- **Con Recursos Asociados:** {rubros_con_recursos}
- **Tasa de Éxito:** {success_rate:.1f}%

### Recursos
- **Total Extraídos:** {len(result.recursos)}
- **Promedio por Rubro:** {avg_recursos_per_rubro:.2f}

### Confianza
- **Promedio Rubros:** {sum(r.confidence for r in result.rubros) / len(result.rubros) * 100 if result.rubros else 0:.1f}%
- **Promedio Recursos:** {sum(r.confidence for r in result.recursos) / len(result.recursos) * 100 if result.recursos else 0:.1f}%"""


def _generate_matching_section(result: PipelineResultV1_1) -> str:
    """Genera sección de matching semántico."""
    if not result.match_results:
        return "## 🎯 Matching Semántico\n\n_No se aplicó matching (modo sin referencia WBS)_"

    matched = len([m for m in result.match_results if m.status == MatchStatus.MATCHED])
    ambiguous = len([m for m in result.match_results if m.status == MatchStatus.AMBIGUOUS])
    no_match = len([m for m in result.match_results if m.status == MatchStatus.NO_MATCH])
    manual = len([m for m in result.match_results if m.status == MatchStatus.MANUAL_REVIEW])

    success_rate = result.match_success_rate * 100
    avg_confidence = sum(m.confidence for m in result.match_results) / len(result.match_results) if result.match_results else 0

    return f"""## 🎯 Matching Semántico WBS ↔ ET

### Resumen
- **Total Procesados:** {len(result.match_results)}
- **Tasa de Éxito:** {success_rate:.1f}%
- **Confianza Promedio:** {avg_confidence * 100:.1f}%

### Distribución por Estado

| Estado | Cantidad | % |
|--------|----------|---|
| ✅ **MATCHED** | {matched} | {matched/len(result.match_results)*100:.1f}% |
| ⚠️ **AMBIGUOUS** | {ambiguous} | {ambiguous/len(result.match_results)*100:.1f}% |
| ⏳ **MANUAL_REVIEW** | {manual} | {manual/len(result.match_results)*100:.1f}% |
| ❌ **NO_MATCH** | {no_match} | {no_match/len(result.match_results)*100:.1f}% |"""


def _generate_deduplication_section(result: PipelineResultV1_1) -> str:
    """Genera sección de deduplicación."""
    if not result.duplicate_groups:
        return "## 🔀 Deduplicación\n\n_No se detectaron duplicados_"

    stats = result.dedup_stats

    return f"""## 🔀 Deduplicación y Resolución de Conflictos

### Resumen
- **Grupos de Duplicados:** {stats['duplicate_groups']}
- **Rubros Fusionados (MERGE):** {stats['total_merged']}
- **Rubros Separados (SPLIT):** {stats['total_split']}

### Estrategias Aplicadas

| Estrategia | Descripción | Aplicaciones |
|------------|-------------|--------------|
| **MERGE** | Duplicados exactos fusionados | {len([g for g in result.duplicate_groups if g.strategy.value == 'MERGE'])} |
| **SPLIT** | Conflictos separados con sufijos | {len([g for g in result.duplicate_groups if g.strategy.value == 'SPLIT'])} |
| **HASH** | Códigos generados para rubros sin código | {len([g for g in result.duplicate_groups if g.strategy.value == 'HASH'])} |"""


def _generate_warnings_section(result: PipelineResultV1_1) -> str:
    """Genera sección de warnings."""
    if not result.warnings:
        return "## ⚠️ Warnings\n\n_No se generaron warnings_"

    by_severity = {
        'HIGH': result.get_warnings_by_severity('HIGH'),
        'MEDIUM': result.get_warnings_by_severity('MEDIUM'),
        'LOW': result.get_warnings_by_severity('LOW')
    }

    by_kind = {}
    for w in result.warnings:
        kind = w.kind.value
        by_kind[kind] = by_kind.get(kind, 0) + 1

    kind_table = "\n".join([
        f"| {kind} | {count} |"
        for kind, count in sorted(by_kind.items(), key=lambda x: -x[1])
    ])

    return f"""## ⚠️ Warnings y Observaciones

### Por Severidad
- 🔴 **HIGH:** {len(by_severity['HIGH'])}
- 🟡 **MEDIUM:** {len(by_severity['MEDIUM'])}
- 🟢 **LOW:** {len(by_severity['LOW'])}

### Por Tipo

| Tipo | Cantidad |
|------|----------|
{kind_table}"""


def _generate_artifacts_section(result: PipelineResultV1_1) -> str:
    """Genera sección de artifacts generados."""
    if not result.artifacts:
        return ""

    artifacts_list = "\n".join([
        f"- **{a.artifact_type}**: `{a.file_path}` ({a.size_bytes / 1024:.2f} KB)"
        for a in result.artifacts
    ])

    return f"""## 📦 Artifacts Generados

{artifacts_list}"""


def _generate_footer() -> str:
    """Genera footer del reporte."""
    return f"""---

_Generado automáticamente por ETL Pipeline v1.1_
_Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"""
