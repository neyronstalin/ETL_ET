"""
Tests para extract_sections.py - Extracción de secciones específicas.

Valida que:
1. Rubro 01.001.4.01 extrae: MATERIALES ["ESTACAS", "CLAVOS", "PINTURA..."]
2. Rubro 01.002.4.01 tiene MATERIALES vacío y EQUIPO ["HERRAMIENTA MENOR"]
"""

import pytest
from pathlib import Path
import pdfplumber

from src.etl_apu import (
    detect_rubro_blocks,
    extract_resources_from_rubro,
    RubroBlock
)


@pytest.fixture
def pdf_path():
    """Path al PDF de prueba."""
    return Path("data/input/9. CP.OB.0008 ET BELLAVISTA ampliacion PG 448 2025 08 06.pdf")


@pytest.fixture
def rubro_01_001_text(pdf_path):
    """Texto del rubro 01.001.4.01."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[4]  # Página 5 (índice 4)
        return page.extract_text()


@pytest.fixture
def rubro_01_002_text(pdf_path):
    """Texto del rubro 01.002.4.01."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[7]  # Página 8 (índice 7)
        return page.extract_text()


def test_detect_rubro_01_001(rubro_01_001_text):
    """Test: Detectar rubro 01.001.4.01."""
    blocks = detect_rubro_blocks(rubro_01_001_text, page_number=5)

    assert len(blocks) >= 1, "Debe detectar al menos 1 rubro"

    # Buscar el rubro específico
    block_01_001 = None
    for block in blocks:
        if "01.001.4.01" in block.codigo:
            block_01_001 = block
            break

    assert block_01_001 is not None, "Debe encontrar rubro 01.001.4.01"
    assert "REPLANTEO" in block_01_001.nombre.upper()
    assert block_01_001.unidad in ["m2", "m²", "m", "u"]


def test_extract_materiales_01_001(rubro_01_001_text):
    """Test: Extraer materiales de rubro 01.001.4.01."""
    blocks = detect_rubro_blocks(rubro_01_001_text, page_number=5)
    block_01_001 = next((b for b in blocks if "01.001.4.01" in b.codigo), None)

    assert block_01_001 is not None

    resources = extract_resources_from_rubro(block_01_001)
    materiales = resources["materiales"]

    assert materiales is not None, "Debe encontrar sección MATERIALES"
    assert not materiales.is_empty, "MATERIALES no debe estar vacío"

    # Validar items esperados
    expected_items = ["ESTACAS", "CLAVOS", "PINTURA"]

    materiales_upper = [item.upper() for item in materiales.items]

    for expected in expected_items:
        assert any(expected in item for item in materiales_upper), \
            f"Debe contener '{expected}' en materiales"

    print(f"\n✓ Materiales extraídos: {materiales.items}")


def test_extract_equipo_01_001(rubro_01_001_text):
    """Test: Extraer equipo de rubro 01.001.4.01."""
    blocks = detect_rubro_blocks(rubro_01_001_text, page_number=5)
    block_01_001 = next((b for b in blocks if "01.001.4.01" in b.codigo), None)

    assert block_01_001 is not None

    resources = extract_resources_from_rubro(block_01_001)
    equipo = resources["equipo"]

    assert equipo is not None, "Debe encontrar sección EQUIPO MÍNIMO"
    assert not equipo.is_empty, "EQUIPO no debe estar vacío"

    # Validar items esperados
    expected_items = ["HERRAMIENTA MENOR", "TOPOGRAFÍA"]

    equipo_upper = [item.upper() for item in equipo.items]

    for expected in expected_items:
        assert any(expected in item for item in equipo_upper), \
            f"Debe contener '{expected}' en equipo"

    print(f"\n✓ Equipo extraído: {equipo.items}")


def test_detect_rubro_01_002(rubro_01_002_text):
    """Test: Detectar rubro 01.002.4.01."""
    blocks = detect_rubro_blocks(rubro_01_002_text, page_number=8)

    assert len(blocks) >= 1, "Debe detectar al menos 1 rubro"

    block_01_002 = next((b for b in blocks if "01.002.4.01" in b.codigo), None)

    assert block_01_002 is not None, "Debe encontrar rubro 01.002.4.01"
    assert "DESBROCE" in block_01_002.nombre.upper() or "LIMPIEZA" in block_01_002.nombre.upper()


def test_extract_materiales_01_002_empty(rubro_01_002_text):
    """Test: Materiales de rubro 01.002.4.01 debe estar vacío (No aplica)."""
    blocks = detect_rubro_blocks(rubro_01_002_text, page_number=8)
    block_01_002 = next((b for b in blocks if "01.002.4.01" in b.codigo), None)

    assert block_01_002 is not None

    resources = extract_resources_from_rubro(block_01_002)
    materiales = resources["materiales"]

    assert materiales is not None, "Debe encontrar sección MATERIALES"
    assert materiales.is_empty, "MATERIALES debe estar vacío (No aplica)"
    assert len(materiales.items) == 0, "No debe tener items"

    print(f"\n✓ Materiales vacío (esperado): {materiales.raw_text}")


def test_extract_equipo_01_002(rubro_01_002_text):
    """Test: Equipo de rubro 01.002.4.01 debe tener HERRAMIENTA MENOR."""
    blocks = detect_rubro_blocks(rubro_01_002_text, page_number=8)
    block_01_002 = next((b for b in blocks if "01.002.4.01" in b.codigo), None)

    assert block_01_002 is not None

    resources = extract_resources_from_rubro(block_01_002)
    equipo = resources["equipo"]

    assert equipo is not None, "Debe encontrar sección EQUIPO MÍNIMO"
    assert not equipo.is_empty, "EQUIPO no debe estar vacío"

    # Debe contener "HERRAMIENTA MENOR"
    equipo_upper = [item.upper() for item in equipo.items]

    assert any("HERRAMIENTA" in item and "MENOR" in item for item in equipo_upper), \
        "Debe contener 'HERRAMIENTA MENOR'"

    print(f"\n✓ Equipo extraído: {equipo.items}")


def test_no_observations_in_items(rubro_01_001_text):
    """Test: Observaciones/reglas NO deben estar en items."""
    import re

    blocks = detect_rubro_blocks(rubro_01_001_text, page_number=5)
    block_01_001 = next((b for b in blocks if "01.001.4.01" in b.codigo), None)

    assert block_01_001 is not None

    resources = extract_resources_from_rubro(block_01_001)
    materiales = resources["materiales"]

    # No debe haber items con FRASES de observación (usar word boundaries)
    observation_patterns = [
        r'\bsegún\b',
        r'\bde acuerdo\b',
        r'\bconforme\b',
        r'\bmínimo de\b',
        r'\bsi\s+\w+',  # "si" seguido de espacio y palabra (condicional)
        r'\bdebe\b',
        r'\bserá\b'
    ]

    for item in materiales.items:
        item_lower = item.lower()
        for pattern in observation_patterns:
            match = re.search(pattern, item_lower)
            if match:
                pytest.fail(f"Item '{item}' contiene patrón de observación '{pattern}' (match: '{match.group()}')")


# ═══════════════════════════════════════════════════════════════════════════
# TEST DE INTEGRACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def test_full_extraction_two_rubros(pdf_path):
    """Test de integración: Extraer ambos rubros completos."""
    extracted = {}

    with pdfplumber.open(pdf_path) as pdf:
        # Página 5: Rubro 01.001.4.01
        page5_text = pdf.pages[4].extract_text()
        blocks_page5 = detect_rubro_blocks(page5_text, page_number=5)

        for block in blocks_page5:
            if "01.001.4.01" in block.codigo:
                extracted["01.001.4.01"] = extract_resources_from_rubro(block)

        # Página 8: Rubro 01.002.4.01
        page8_text = pdf.pages[7].extract_text()
        blocks_page8 = detect_rubro_blocks(page8_text, page_number=8)

        for block in blocks_page8:
            if "01.002.4.01" in block.codigo:
                extracted["01.002.4.01"] = extract_resources_from_rubro(block)

    # Validaciones finales
    assert "01.001.4.01" in extracted
    assert "01.002.4.01" in extracted

    # Rubro 01.001.4.01
    r1_mat = extracted["01.001.4.01"]["materiales"]
    r1_eq = extracted["01.001.4.01"]["equipo"]

    assert not r1_mat.is_empty
    assert len(r1_mat.items) >= 3  # Al menos 3 materiales
    assert not r1_eq.is_empty
    assert len(r1_eq.items) >= 2  # Al menos 2 equipos

    # Rubro 01.002.4.01
    r2_mat = extracted["01.002.4.01"]["materiales"]
    r2_eq = extracted["01.002.4.01"]["equipo"]

    assert r2_mat.is_empty  # Materiales = "No aplica"
    assert not r2_eq.is_empty
    assert len(r2_eq.items) >= 1  # Al menos 1 equipo

    print("\n" + "=" * 80)
    print("RESUMEN DE EXTRACCIÓN")
    print("=" * 80)
    print(f"\n01.001.4.01 REPLANTEO:")
    print(f"  Materiales: {r1_mat.items}")
    print(f"  Equipo: {r1_eq.items}")
    print(f"\n01.002.4.01 DESBROCE:")
    print(f"  Materiales: {r2_mat.items if not r2_mat.is_empty else '[No aplica]'}")
    print(f"  Equipo: {r2_eq.items}")
    print("=" * 80)
