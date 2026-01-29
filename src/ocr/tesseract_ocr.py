"""
Módulo OCR usando Tesseract.

Responsabilidades:
- Aplicar OCR a páginas escaneadas de PDFs
- Convertir PDF → Imagen → Texto
- Calcular confidence scores
- Optimizar imágenes pre-OCR (contraste, deskew, etc.)
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import tempfile

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance
except ImportError as e:
    raise ImportError(
        "Dependencias OCR no instaladas. "
        "Ejecuta: pip install pytesseract pdf2image Pillow"
    ) from e

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

# Descomentar y ajustar si Tesseract no está en PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuración Tesseract
TESSERACT_CONFIG = '--psm 6 --oem 3'  # PSM 6: Assume uniform block of text
# PSM modes:
#  6 = Assume a single uniform block of text
#  3 = Fully automatic page segmentation (default)
# OEM modes:
#  3 = Default (Legacy + LSTM)


# ═══════════════════════════════════════════════════════════════════════════
# PRE-PROCESAMIENTO DE IMÁGENES
# ═══════════════════════════════════════════════════════════════════════════

def preprocess_image(image: Image.Image, enhance: bool = True) -> Image.Image:
    """
    Pre-procesa imagen antes de OCR para mejorar accuracy.

    Mejoras aplicadas:
    - Conversión a escala de grises
    - Aumento de contraste
    - Redimensionamiento si la imagen es muy pequeña

    Args:
        image: Imagen PIL
        enhance: Si True, aplica mejoras de contraste y brillo

    Returns:
        Imagen procesada
    """
    # Convertir a escala de grises
    if image.mode != 'L':
        image = image.convert('L')

    # Aumentar contraste
    if enhance:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)  # Factor 1.5 aumenta contraste

        # Aumentar nitidez
        sharpness = ImageEnhance.Sharpness(image)
        image = sharpness.enhance(1.3)

    # Redimensionar si es muy pequeña (Tesseract funciona mejor con DPI alto)
    min_width = 1500
    if image.width < min_width:
        scale_factor = min_width / image.width
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        logger.debug(f"Imagen redimensionada a {new_size} para mejor OCR")

    return image


# ═══════════════════════════════════════════════════════════════════════════
# CONVERSIÓN PDF → IMAGEN
# ═══════════════════════════════════════════════════════════════════════════

def pdf_page_to_image(
    pdf_path: Path,
    page_number: int,
    dpi: int = 300
) -> Image.Image:
    """
    Convierte una página de PDF a imagen PIL.

    Args:
        pdf_path: Ruta al PDF
        page_number: Número de página (1-indexed)
        dpi: DPI para la conversión (mayor DPI = mejor calidad pero más lento)

    Returns:
        Imagen PIL de la página

    Raises:
        ValueError: Si el número de página es inválido
    """
    logger.debug(f"Convirtiendo página {page_number} a imagen (DPI={dpi})")

    try:
        # convert_from_path usa páginas 1-indexed internamente
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=page_number,
            last_page=page_number
        )

        if not images:
            raise ValueError(f"No se pudo convertir página {page_number}")

        return images[0]

    except Exception as e:
        logger.error(f"Error al convertir PDF a imagen: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# OCR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def ocr_image(
    image: Image.Image,
    lang: str = 'spa',
    config: str = TESSERACT_CONFIG,
    preprocess: bool = True
) -> Tuple[str, float]:
    """
    Aplica OCR a una imagen usando Tesseract.

    Args:
        image: Imagen PIL
        lang: Idioma(s) separados por '+' (ej: 'spa', 'spa+eng')
        config: Configuración de Tesseract
        preprocess: Si True, pre-procesa la imagen antes de OCR

    Returns:
        Tuple[text, confidence]:
            - text: Texto extraído
            - confidence: Score de confianza promedio (0-100)

    Raises:
        RuntimeError: Si Tesseract no está instalado o falla
    """
    try:
        # Pre-procesar imagen
        if preprocess:
            image = preprocess_image(image)

        # Ejecutar OCR
        text = pytesseract.image_to_string(image, lang=lang, config=config)

        # Obtener confidence score
        try:
            data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
            confidences = [float(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        except Exception as e:
            logger.warning(f"No se pudo calcular confidence: {e}")
            avg_confidence = 0.0

        return text.strip(), avg_confidence

    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract no está instalado o no está en PATH. "
            "Ver SETUP.md para instrucciones de instalación."
        )
    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        raise


def ocr_pdf_page(
    pdf_path: Path,
    page_number: int,
    lang: str = 'spa',
    dpi: int = 300
) -> Tuple[str, float]:
    """
    Aplica OCR a una página específica de un PDF.

    Esta es la función principal para procesar páginas escaneadas.

    Args:
        pdf_path: Ruta al PDF
        page_number: Número de página (1-indexed)
        lang: Idioma para OCR
        dpi: DPI para conversión PDF→Imagen

    Returns:
        Tuple[text, confidence]:
            - text: Texto extraído
            - confidence: Score de confianza (0-100)

    Example:
        >>> from pathlib import Path
        >>> pdf_path = Path("data/input/escaneado.pdf")
        >>> text, conf = ocr_pdf_page(pdf_path, page_number=1)
        >>> print(f"Confianza: {conf:.1f}%")
        >>> print(f"Texto: {text[:100]}...")
    """
    logger.info(f"Aplicando OCR a {pdf_path.name}, página {page_number}")

    # Convertir página a imagen
    image = pdf_page_to_image(pdf_path, page_number, dpi=dpi)

    # Aplicar OCR
    text, confidence = ocr_image(image, lang=lang)

    logger.info(
        f"OCR completado: {len(text)} caracteres, "
        f"confidence={confidence:.1f}%"
    )

    return text, confidence


# ═══════════════════════════════════════════════════════════════════════════
# BATCH OCR (Múltiples páginas)
# ═══════════════════════════════════════════════════════════════════════════

def ocr_multiple_pages(
    pdf_path: Path,
    page_numbers: list[int],
    lang: str = 'spa',
    dpi: int = 300
) -> Dict[int, Tuple[str, float]]:
    """
    Aplica OCR a múltiples páginas de un PDF.

    Args:
        pdf_path: Ruta al PDF
        page_numbers: Lista de números de página (1-indexed)
        lang: Idioma para OCR
        dpi: DPI para conversión

    Returns:
        Dict[page_number, (text, confidence)]:
            Diccionario con texto y confidence por página

    Example:
        >>> results = ocr_multiple_pages(pdf_path, [1, 3, 5])
        >>> for page, (text, conf) in results.items():
        ...     print(f"Página {page}: {conf:.1f}% confianza")
    """
    logger.info(
        f"Aplicando OCR a {len(page_numbers)} páginas de {pdf_path.name}"
    )

    results = {}

    for page_num in page_numbers:
        try:
            text, conf = ocr_pdf_page(pdf_path, page_num, lang=lang, dpi=dpi)
            results[page_num] = (text, conf)
        except Exception as e:
            logger.error(f"Error en OCR de página {page_num}: {e}")
            results[page_num] = ("", 0.0)

    logger.info(f"OCR batch completado: {len(results)} páginas procesadas")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════

def test_tesseract_installation() -> bool:
    """
    Verifica que Tesseract esté instalado y funcional.

    Returns:
        True si Tesseract está disponible, False en caso contrario
    """
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract versión {version} detectado")
        return True
    except pytesseract.TesseractNotFoundError:
        logger.error(
            "Tesseract NO detectado. "
            "Instalar según instrucciones en SETUP.md"
        )
        return False
    except Exception as e:
        logger.error(f"Error al verificar Tesseract: {e}")
        return False


def get_available_languages() -> list[str]:
    """
    Lista idiomas disponibles en Tesseract.

    Returns:
        Lista de códigos de idioma (ej: ['eng', 'spa', 'fra'])
    """
    try:
        langs = pytesseract.get_languages()
        logger.info(f"Idiomas disponibles en Tesseract: {langs}")
        return langs
    except Exception as e:
        logger.error(f"Error al obtener idiomas: {e}")
        return []
