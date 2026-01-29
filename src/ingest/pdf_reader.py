"""
Módulo de ingesta de PDFs (digitales y escaneados).

Responsabilidades:
- Detectar si un PDF es digital (texto extraíble) o escaneado (imagen)
- Extraer texto de PDFs digitales
- Identificar páginas que requieren OCR
- Generar metadatos de páginas
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pdfplumber
from pypdf import PdfReader

from src.models.schemas import PageMetadata, TipoDocumento, DocumentMetadata
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DETECCIÓN DE TIPO DE PDF
# ═══════════════════════════════════════════════════════════════════════════

def detect_pdf_type(pdf_path: Path, sample_pages: int = 3) -> TipoDocumento:
    """
    Detecta si un PDF es digital, escaneado o mixto.

    Estrategia:
    1. Extrae texto de las primeras N páginas
    2. Si >80% de las páginas tienen texto extraíble → DIGITAL
    3. Si <20% tienen texto → ESCANEADO
    4. Caso contrario → MIXTO

    Args:
        pdf_path: Ruta al archivo PDF
        sample_pages: Número de páginas a samplear para detección

    Returns:
        TipoDocumento: DIGITAL | ESCANEADO | MIXTO

    Raises:
        FileNotFoundError: Si el PDF no existe
        ValueError: Si el PDF está corrupto
    """
    logger.info(f"Detectando tipo de PDF: {pdf_path.name}")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_check = min(sample_pages, total_pages)

            pages_with_text = 0

            for i in range(pages_to_check):
                text = pdf.pages[i].extract_text()
                # Consideramos que tiene texto si tiene más de 50 caracteres
                if text and len(text.strip()) > 50:
                    pages_with_text += 1

            ratio = pages_with_text / pages_to_check

            if ratio >= 0.8:
                tipo = TipoDocumento.DIGITAL
            elif ratio <= 0.2:
                tipo = TipoDocumento.ESCANEADO
            else:
                tipo = TipoDocumento.MIXTO

            logger.info(
                f"PDF detectado como {tipo.value} "
                f"({pages_with_text}/{pages_to_check} páginas con texto)"
            )
            return tipo

    except Exception as e:
        logger.error(f"Error al detectar tipo de PDF: {e}")
        raise ValueError(f"PDF corrupto o ilegible: {e}")


def is_page_digital(page_text: str, min_chars: int = 50) -> bool:
    """
    Determina si una página tiene texto extraíble (es digital).

    Args:
        page_text: Texto extraído de la página
        min_chars: Mínimo de caracteres para considerarla digital

    Returns:
        True si la página es digital, False si requiere OCR
    """
    return bool(page_text and len(page_text.strip()) >= min_chars)


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN DE TEXTO (PDFs Digitales)
# ═══════════════════════════════════════════════════════════════════════════

def extract_text_from_digital_pdf(pdf_path: Path) -> Dict[int, str]:
    """
    Extrae texto de un PDF digital (con texto real).

    Args:
        pdf_path: Ruta al PDF

    Returns:
        Dict[page_number, text]: Diccionario con texto por página (1-indexed)

    Raises:
        FileNotFoundError: Si el PDF no existe
    """
    logger.info(f"Extrayendo texto de PDF digital: {pdf_path.name}")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

    pages_text = {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages_text[i] = text

                logger.debug(
                    f"Página {i}: {len(text)} caracteres extraídos"
                )

        logger.info(f"Texto extraído de {len(pages_text)} páginas")
        return pages_text

    except Exception as e:
        logger.error(f"Error al extraer texto: {e}")
        raise


def extract_pages_metadata(pdf_path: Path) -> Tuple[List[PageMetadata], int]:
    """
    Extrae metadatos de todas las páginas del PDF.

    Args:
        pdf_path: Ruta al PDF

    Returns:
        Tuple[List[PageMetadata], total_pages]:
            - Lista de metadatos por página
            - Total de páginas

    Raises:
        FileNotFoundError: Si el PDF no existe
    """
    logger.info(f"Extrayendo metadatos de páginas: {pdf_path.name}")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

    metadata_list = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                is_digital = is_page_digital(text)

                metadata = PageMetadata(
                    page_number=i,
                    tipo_documento=TipoDocumento.DIGITAL if is_digital else TipoDocumento.ESCANEADO,
                    ocr_applied=False,  # Se actualizará después si se aplica OCR
                    text_length=len(text)
                )

                metadata_list.append(metadata)

        logger.info(f"Metadatos extraídos para {total_pages} páginas")
        return metadata_list, total_pages

    except Exception as e:
        logger.error(f"Error al extraer metadatos: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL DE INGESTA
# ═══════════════════════════════════════════════════════════════════════════

def ingest_pdf(
    pdf_path: Path,
    force_ocr: bool = False
) -> Tuple[Dict[int, str], DocumentMetadata]:
    """
    Función principal de ingesta de PDFs.

    Flujo:
    1. Detecta tipo de PDF (digital/escaneado/mixto)
    2. Extrae texto de páginas digitales
    3. Identifica páginas que requieren OCR
    4. Genera metadatos del documento

    Args:
        pdf_path: Ruta al archivo PDF
        force_ocr: Si True, aplica OCR a todas las páginas (ignora detección)

    Returns:
        Tuple[Dict[int, str], DocumentMetadata]:
            - Diccionario con texto por página (puede estar vacío si requiere OCR)
            - Metadatos del documento

    Raises:
        FileNotFoundError: Si el PDF no existe
        ValueError: Si el PDF está corrupto

    Example:
        >>> from pathlib import Path
        >>> pdf_path = Path("data/input/especificaciones.pdf")
        >>> pages_text, metadata = ingest_pdf(pdf_path)
        >>> print(f"Total páginas: {metadata.total_pages}")
        >>> print(f"Páginas que requieren OCR: {len(metadata.pages_with_ocr)}")
    """
    logger.info(f"Iniciando ingesta de PDF: {pdf_path.name}")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

    # 1. Detectar tipo de PDF
    tipo_pdf = detect_pdf_type(pdf_path)

    # 2. Extraer metadatos de páginas
    pages_metadata, total_pages = extract_pages_metadata(pdf_path)

    # 3. Identificar páginas que requieren OCR
    pages_requiring_ocr = []

    if force_ocr:
        pages_requiring_ocr = list(range(1, total_pages + 1))
    else:
        for meta in pages_metadata:
            if meta.tipo_documento == TipoDocumento.ESCANEADO:
                pages_requiring_ocr.append(meta.page_number)

    # 4. Extraer texto de páginas digitales
    pages_text = {}

    if tipo_pdf in [TipoDocumento.DIGITAL, TipoDocumento.MIXTO] and not force_ocr:
        pages_text = extract_text_from_digital_pdf(pdf_path)
    else:
        # Si es escaneado o force_ocr, dejamos vacío (el módulo OCR lo llenará)
        pages_text = {i: "" for i in range(1, total_pages + 1)}

    # 5. Generar metadatos del documento
    doc_metadata = DocumentMetadata(
        filename=pdf_path.name,
        total_pages=total_pages,
        tipo_documento=tipo_pdf,
        pages_with_ocr=pages_requiring_ocr
    )

    logger.info(
        f"Ingesta completada: {total_pages} páginas, "
        f"{len(pages_requiring_ocr)} requieren OCR"
    )

    return pages_text, doc_metadata


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

def get_pdf_info(pdf_path: Path) -> Dict[str, any]:
    """
    Obtiene información básica del PDF (metadatos PyPDF).

    Args:
        pdf_path: Ruta al PDF

    Returns:
        Dict con información del PDF (autor, título, páginas, etc.)
    """
    try:
        reader = PdfReader(pdf_path)
        info = {
            "num_pages": len(reader.pages),
            "metadata": reader.metadata,
            "is_encrypted": reader.is_encrypted
        }
        return info
    except Exception as e:
        logger.warning(f"No se pudo leer metadata del PDF: {e}")
        return {}
