"""
Tests unitarios para el módulo de parseo.
"""

import pytest
from src.parse.rubro_parser import (
    normalizar_unidad,
    extraer_codigo_rubro,
    extraer_unidad,
    clasificar_tipo_recurso,
    segmentar_en_rubros
)
from src.models.schemas import TipoRecurso


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE NORMALIZACIÓN DE UNIDADES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_normalizar_unidad_m2():
    """Normaliza variantes de m²"""
    assert normalizar_unidad("m2") == "m²"
    assert normalizar_unidad("m^2") == "m²"
    assert normalizar_unidad("metro cuadrado") == "m²"


@pytest.mark.unit
def test_normalizar_unidad_m3():
    """Normaliza variantes de m³"""
    assert normalizar_unidad("m3") == "m³"
    assert normalizar_unidad("m^3") == "m³"
    assert normalizar_unidad("metro cubico") == "m³"


@pytest.mark.unit
def test_normalizar_unidad_kg():
    """Normaliza variantes de kg"""
    assert normalizar_unidad("kg") == "kg"
    assert normalizar_unidad("kg.") == "kg"
    assert normalizar_unidad("kilo") == "kg"
    assert normalizar_unidad("kilogramo") == "kg"


@pytest.mark.unit
def test_normalizar_unidad_u():
    """Normaliza variantes de unidad"""
    assert normalizar_unidad("u") == "u"
    assert normalizar_unidad("un") == "u"
    assert normalizar_unidad("und") == "u"
    assert normalizar_unidad("unidad") == "u"
    assert normalizar_unidad("pza") == "u"
    assert normalizar_unidad("pieza") == "u"


@pytest.mark.unit
def test_normalizar_unidad_desconocida():
    """Mantiene unidades desconocidas"""
    assert normalizar_unidad("xyz") == "xyz"
    assert normalizar_unidad("unidad_custom") == "unidad_custom"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE EXTRACCIÓN DE CÓDIGO
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_extraer_codigo_rubro_puntos():
    """Extrae códigos con formato XX.XX.XX"""
    assert extraer_codigo_rubro("01.01.01 EXCAVACIÓN MANUAL") == "01.01.01"
    assert extraer_codigo_rubro("10.05.02 RUBRO") == "10.05.02"
    assert extraer_codigo_rubro("1.1.1 RUBRO") == "1.1.1"


@pytest.mark.unit
def test_extraer_codigo_rubro_guiones():
    """Extrae códigos con formato XX-XX-XX"""
    assert extraer_codigo_rubro("01-01-01 EXCAVACIÓN") == "01-01-01"
    assert extraer_codigo_rubro("10-05-02 RUBRO") == "10-05-02"


@pytest.mark.unit
def test_extraer_codigo_rubro_sin_codigo():
    """Retorna None si no hay código"""
    assert extraer_codigo_rubro("Sin código de rubro") is None
    assert extraer_codigo_rubro("EXCAVACIÓN MANUAL") is None
    assert extraer_codigo_rubro("01.01 SOLO DOS NIVELES") is None  # Formato inválido


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE EXTRACCIÓN DE UNIDAD
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_extraer_unidad_texto():
    """Extrae unidad de texto"""
    assert extraer_unidad("Precio por m2") == "m²"
    assert extraer_unidad("Unidad: m³") == "m³"
    assert extraer_unidad("Se mide en kg") == "kg"
    assert extraer_unidad("Total u") == "u"


@pytest.mark.unit
def test_extraer_unidad_no_encontrada():
    """Retorna None si no hay unidad"""
    assert extraer_unidad("Sin unidad de medida") is None
    assert extraer_unidad("Descripción genérica") is None


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE CLASIFICACIÓN DE RECURSOS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_clasificar_material():
    """Clasifica correctamente materiales"""
    assert clasificar_tipo_recurso("Cemento Portland tipo I") == TipoRecurso.MATERIAL
    assert clasificar_tipo_recurso("Arena gruesa") == TipoRecurso.MATERIAL
    assert clasificar_tipo_recurso("Acero corrugado") == TipoRecurso.MATERIAL
    assert clasificar_tipo_recurso("Pintura látex") == TipoRecurso.MATERIAL


@pytest.mark.unit
def test_clasificar_equipo():
    """Clasifica correctamente equipos"""
    assert clasificar_tipo_recurso("Mezcladora de concreto") == TipoRecurso.EQUIPO
    assert clasificar_tipo_recurso("Vibrador de inmersión") == TipoRecurso.EQUIPO
    assert clasificar_tipo_recurso("Camión volquete") == TipoRecurso.EQUIPO
    assert clasificar_tipo_recurso("Andamio metálico") == TipoRecurso.EQUIPO


@pytest.mark.unit
def test_clasificar_desconocido():
    """Clasifica como DESCONOCIDO si no puede determinar"""
    assert clasificar_tipo_recurso("Insumo especial XYZ") == TipoRecurso.DESCONOCIDO
    assert clasificar_tipo_recurso("Recurso genérico") == TipoRecurso.DESCONOCIDO


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE SEGMENTACIÓN
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_segmentar_en_rubros():
    """Segmenta texto en bloques de rubros"""
    texto = """
    01.01.01 RUBRO 1
    Detalle del rubro 1
    Material A

    02.01.01 RUBRO 2
    Detalle del rubro 2
    Material B

    03.01.01 RUBRO 3
    Detalle del rubro 3
    """

    bloques = segmentar_en_rubros(texto)

    assert len(bloques) == 3
    assert "01.01.01" in bloques[0]
    assert "02.01.01" in bloques[1]
    assert "03.01.01" in bloques[2]


@pytest.mark.unit
def test_segmentar_en_rubros_sin_codigos():
    """Retorna lista vacía si no hay códigos"""
    texto = "Texto sin códigos de rubro"
    bloques = segmentar_en_rubros(texto)
    assert bloques == []


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_normalizar_unidad_case_insensitive():
    """Normalización es case-insensitive"""
    assert normalizar_unidad("M2") == "m²"
    assert normalizar_unidad("KG") == "kg"
    assert normalizar_unidad("UNIDAD") == "u"


@pytest.mark.unit
def test_extraer_codigo_multiple_codigos():
    """Extrae primer código si hay múltiples"""
    texto = "01.01.01 RUBRO 1 y 02.01.01 RUBRO 2"
    codigo = extraer_codigo_rubro(texto)
    assert codigo == "01.01.01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
