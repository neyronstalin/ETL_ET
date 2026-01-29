"""
Tests de smoke básicos para verificar que el entorno está configurado.

Estos tests deben pasar inmediatamente después del setup.
"""

import pytest
from pathlib import Path


def test_python_version():
    """Verifica que Python es 3.11+"""
    import sys
    assert sys.version_info >= (3, 11), "Python 3.11+ requerido"


def test_imports_core():
    """Verifica que los módulos core se pueden importar"""
    from src.models import schemas
    from src.utils import logger
    assert schemas is not None
    assert logger is not None


def test_imports_ingest():
    """Verifica imports del módulo ingest"""
    from src.ingest.pdf_reader import ingest_pdf, detect_pdf_type
    assert callable(ingest_pdf)
    assert callable(detect_pdf_type)


def test_imports_ocr():
    """Verifica imports del módulo OCR"""
    from src.ocr.tesseract_ocr import ocr_pdf_page, test_tesseract_installation
    assert callable(ocr_pdf_page)
    assert callable(test_tesseract_installation)


def test_imports_parse():
    """Verifica imports del módulo parse"""
    from src.parse.rubro_parser import parsear_texto_completo, clasificar_tipo_recurso
    assert callable(parsear_texto_completo)
    assert callable(clasificar_tipo_recurso)


def test_imports_export():
    """Verifica imports del módulo export"""
    from src.export.excel_exporter import export_to_excel
    assert callable(export_to_excel)


def test_data_directories_exist():
    """Verifica que las carpetas de datos existen"""
    data_dir = Path("data")
    assert data_dir.exists(), "Carpeta data/ no existe"

    input_dir = data_dir / "input"
    output_dir = data_dir / "output"
    cache_dir = data_dir / "cache"

    assert input_dir.exists(), "Carpeta data/input/ no existe"
    assert output_dir.exists(), "Carpeta data/output/ no existe"
    assert cache_dir.exists(), "Carpeta data/cache/ no existe"


def test_pydantic_models():
    """Verifica que los modelos Pydantic se pueden instanciar"""
    from src.models.schemas import Rubro, Recurso, TipoRecurso
    from datetime import datetime

    # Crear un Rubro de prueba
    rubro = Rubro(
        rubro_id="TEST_001",
        codigo="01.01.01",
        descripcion="Test rubro",
        unidad="m",
        source_pages=[1],
        confidence=1.0
    )

    assert rubro.rubro_id == "TEST_001"
    assert rubro.unidad == "m"

    # Crear un Recurso de prueba
    recurso = Recurso(
        recurso_id="TEST_REC_001",
        rubro_id="TEST_001",
        tipo=TipoRecurso.MATERIAL,
        nombre="Cemento"
    )

    assert recurso.tipo == TipoRecurso.MATERIAL
    assert recurso.nombre == "Cemento"


def test_logger_configuration():
    """Verifica que el logger se puede configurar"""
    from src.utils.logger import get_logger, configure_logging

    configure_logging(level="INFO")
    logger = get_logger(__name__)

    assert logger is not None
    logger.info("Test log message")


@pytest.mark.slow
def test_tesseract_available():
    """Verifica que Tesseract está instalado (test lento, requiere Tesseract)"""
    from src.ocr.tesseract_ocr import test_tesseract_installation

    # Nota: Este test puede fallar si Tesseract no está instalado
    # Marcar como xfail si es un entorno de CI sin Tesseract
    is_installed = test_tesseract_installation()

    if not is_installed:
        pytest.skip("Tesseract no está instalado")

    assert is_installed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
