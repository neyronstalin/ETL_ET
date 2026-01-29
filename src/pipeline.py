"""
Pipeline principal de extracción de especificaciones técnicas.

Este módulo orquesta todo el flujo: Ingest → OCR → Parse → Export
"""

from pathlib import Path
from typing import Optional, Dict
from tqdm import tqdm

from src.models.schemas import (
    PipelineResult, DocumentMetadata,
    Rubro, Recurso, ParseWarning
)
from src.ingest.pdf_reader import ingest_pdf
from src.ocr.tesseract_ocr import ocr_multiple_pages
from src.parse.rubro_parser import parsear_texto_completo
from src.export.excel_exporter import export_to_excel, validar_antes_de_exportar
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def run_pipeline(
    pdf_path: Path,
    output_path: Path,
    force_ocr: bool = False,
    ocr_lang: str = 'spa',
    ocr_dpi: int = 300,
    apply_excel_formatting: bool = True
) -> PipelineResult:
    """
    Ejecuta el pipeline completo de extracción.

    Flujo:
    1. Ingest: Lee PDF y detecta páginas digitales vs escaneadas
    2. OCR: Aplica OCR a páginas escaneadas
    3. Parse: Extrae rubros y recursos de texto
    4. Export: Genera archivo Excel con resultados

    Args:
        pdf_path: Ruta al PDF de entrada
        output_path: Ruta donde guardar el Excel de salida
        force_ocr: Si True, aplica OCR a todas las páginas (ignora detección)
        ocr_lang: Idioma para OCR ('spa', 'eng', 'spa+eng')
        ocr_dpi: DPI para conversión PDF→Imagen en OCR
        apply_excel_formatting: Si True, aplica formato al Excel

    Returns:
        PipelineResult con rubros, recursos, warnings y metadata

    Raises:
        FileNotFoundError: Si el PDF no existe
        RuntimeError: Si el pipeline falla

    Example:
        >>> pdf_path = Path("data/input/especificaciones.pdf")
        >>> output_path = Path("data/output/resultado.xlsx")
        >>> result = run_pipeline(pdf_path, output_path)
        >>> print(f"Extraídos {len(result.rubros)} rubros")
    """
    logger.info("=" * 80)
    logger.info(f"INICIANDO PIPELINE: {pdf_path.name}")
    logger.info("=" * 80)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

    # ───────────────────────────────────────────────────────────────────────
    # FASE 1: INGEST
    # ───────────────────────────────────────────────────────────────────────
    logger.info("FASE 1: Ingesta de PDF")

    pages_text, doc_metadata = ingest_pdf(pdf_path, force_ocr=force_ocr)

    logger.info(
        f"Ingesta completada: {doc_metadata.total_pages} páginas, "
        f"tipo: {doc_metadata.tipo_documento}"
    )

    # ───────────────────────────────────────────────────────────────────────
    # FASE 2: OCR (si es necesario)
    # ───────────────────────────────────────────────────────────────────────
    if doc_metadata.pages_with_ocr:
        logger.info(
            f"FASE 2: OCR - Procesando {len(doc_metadata.pages_with_ocr)} páginas"
        )

        ocr_results = ocr_multiple_pages(
            pdf_path,
            page_numbers=doc_metadata.pages_with_ocr,
            lang=ocr_lang,
            dpi=ocr_dpi
        )

        # Actualizar pages_text con resultados de OCR
        for page_num, (text, confidence) in ocr_results.items():
            pages_text[page_num] = text
            logger.debug(
                f"Página {page_num}: OCR confidence={confidence:.1f}%"
            )

        logger.info("OCR completado")
    else:
        logger.info("FASE 2: OCR no necesario (PDF digital)")

    # ───────────────────────────────────────────────────────────────────────
    # FASE 3: PARSING
    # ───────────────────────────────────────────────────────────────────────
    logger.info("FASE 3: Parsing de rubros y recursos")

    all_rubros = []
    all_recursos = []
    all_warnings = []

    # Parsear cada página con barra de progreso
    for page_num in tqdm(
        sorted(pages_text.keys()),
        desc="Parseando páginas",
        unit="página"
    ):
        text = pages_text[page_num]

        if not text or len(text.strip()) < 50:
            logger.debug(f"Página {page_num}: Sin contenido relevante, omitiendo")
            continue

        rubros, recursos, warnings = parsear_texto_completo(text, page_num)

        all_rubros.extend(rubros)
        all_recursos.extend(recursos)
        all_warnings.extend(warnings)

    logger.info(
        f"Parsing completado: {len(all_rubros)} rubros, "
        f"{len(all_recursos)} recursos, {len(all_warnings)} warnings"
    )

    # ───────────────────────────────────────────────────────────────────────
    # FASE 4: CONSOLIDACIÓN Y VALIDACIÓN
    # ───────────────────────────────────────────────────────────────────────
    logger.info("FASE 4: Consolidación y validación")

    # Actualizar metadata con totales
    doc_metadata.total_rubros = len(all_rubros)
    doc_metadata.total_recursos = len(all_recursos)
    doc_metadata.total_warnings = len(all_warnings)

    # Crear resultado
    result = PipelineResult(
        metadata=doc_metadata,
        rubros=all_rubros,
        recursos=all_recursos,
        warnings=all_warnings
    )

    # Validar antes de exportar
    errores = validar_antes_de_exportar(result)
    if errores:
        logger.warning(f"Se encontraron {len(errores)} errores de validación:")
        for error in errores:
            logger.warning(f"  - {error}")

    # Estadísticas
    logger.info(f"Success rate: {result.success_rate * 100:.1f}%")
    logger.info(f"Warnings HIGH: {len(result.get_warnings_by_severity('HIGH'))}")
    logger.info(f"Warnings MEDIUM: {len(result.get_warnings_by_severity('MEDIUM'))}")
    logger.info(f"Warnings LOW: {len(result.get_warnings_by_severity('LOW'))}")

    # ───────────────────────────────────────────────────────────────────────
    # FASE 5: EXPORT A EXCEL
    # ───────────────────────────────────────────────────────────────────────
    logger.info("FASE 5: Exportando a Excel")

    # Crear directorio de salida si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export_to_excel(
        result,
        output_path,
        apply_formatting=apply_excel_formatting
    )

    logger.info(f"Excel generado: {output_path}")

    # ───────────────────────────────────────────────────────────────────────
    # RESUMEN FINAL
    # ───────────────────────────────────────────────────────────────────────
    logger.info("=" * 80)
    logger.info("PIPELINE COMPLETADO EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info(f"Input:  {pdf_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Rubros extraídos: {len(all_rubros)}")
    logger.info(f"Recursos extraídos: {len(all_recursos)}")
    logger.info(f"Warnings generados: {len(all_warnings)}")
    logger.info("=" * 80)

    return result


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN HELPER PARA BATCH PROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def process_multiple_pdfs(
    input_dir: Path,
    output_dir: Path,
    pattern: str = "*.pdf",
    **pipeline_kwargs
) -> Dict[str, PipelineResult]:
    """
    Procesa múltiples PDFs en batch.

    Args:
        input_dir: Directorio con PDFs de entrada
        output_dir: Directorio donde guardar Excels
        pattern: Patrón glob para filtrar archivos (ej: "*.pdf", "spec_*.pdf")
        **pipeline_kwargs: Argumentos adicionales para run_pipeline

    Returns:
        Dict[filename, PipelineResult]: Resultados por archivo

    Example:
        >>> results = process_multiple_pdfs(
        ...     input_dir=Path("data/input"),
        ...     output_dir=Path("data/output")
        ... )
        >>> print(f"Procesados {len(results)} archivos")
    """
    logger.info(f"Procesando PDFs en batch desde: {input_dir}")

    if not input_dir.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {input_dir}")

    pdf_files = list(input_dir.glob(pattern))

    if not pdf_files:
        logger.warning(f"No se encontraron PDFs con patrón '{pattern}' en {input_dir}")
        return {}

    logger.info(f"Encontrados {len(pdf_files)} PDFs para procesar")

    results = {}

    for pdf_path in tqdm(pdf_files, desc="Procesando PDFs", unit="archivo"):
        try:
            # Generar nombre de salida
            output_filename = pdf_path.stem + "_resultado.xlsx"
            output_path = output_dir / output_filename

            # Ejecutar pipeline
            result = run_pipeline(pdf_path, output_path, **pipeline_kwargs)
            results[pdf_path.name] = result

        except Exception as e:
            logger.error(f"Error procesando {pdf_path.name}: {e}")
            results[pdf_path.name] = None

    # Resumen final
    exitosos = sum(1 for r in results.values() if r is not None)
    logger.info(f"Batch completado: {exitosos}/{len(pdf_files)} exitosos")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# CLI (Opcional)
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline de extracción de especificaciones técnicas desde PDF"
    )
    parser.add_argument("pdf_path", type=Path, help="Ruta al PDF de entrada")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Ruta al Excel de salida (default: data/output/resultado.xlsx)"
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Forzar OCR en todas las páginas"
    )
    parser.add_argument(
        "--ocr-lang",
        default="spa",
        help="Idioma para OCR (default: spa)"
    )
    parser.add_argument(
        "--no-format",
        action="store_true",
        help="No aplicar formato al Excel"
    )

    args = parser.parse_args()

    # Determinar output path
    if args.output:
        output_path = args.output
    else:
        output_path = Path("data/output") / (args.pdf_path.stem + "_resultado.xlsx")

    # Ejecutar pipeline
    result = run_pipeline(
        pdf_path=args.pdf_path,
        output_path=output_path,
        force_ocr=args.force_ocr,
        ocr_lang=args.ocr_lang,
        apply_excel_formatting=not args.no_format
    )

    print(f"\n✅ Pipeline completado: {output_path}")
