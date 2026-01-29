"""
Módulo de parseo de rubros desde texto extraído.

Responsabilidades:
- Detectar bloques de rubros en texto
- Extraer código, descripción, unidad
- Parsear desglose de materiales/equipos
- Clasificar recursos (MATERIAL vs EQUIPO)
- Generar warnings para datos incompletos
"""

import re
from typing import List, Tuple, Optional, Dict
from rapidfuzz import fuzz

from src.models.schemas import (
    Rubro, Recurso, ParseWarning,
    TipoRecurso, WarningKind,
    generar_rubro_id, generar_recurso_id, generar_warning_id
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# PATRONES DE REGEX
# ═══════════════════════════════════════════════════════════════════════════

# Patrón para código de rubro: 01.01.01 o 1.1.1 o 01-01-01
PATRON_CODIGO = r'(\d{1,3}[\.\-]\d{1,3}[\.\-]\d{1,3})'

# Patrón para unidades de medida comunes
PATRON_UNIDAD = r'\b(m³?²?|m2|m3|kg|u|und|unidad|gl|gln|pza|pieza|lt|ton|ha|km)\b'

# Palabras clave para detectar inicio de materiales/equipos
KEYWORDS_MATERIALES = [
    'materiales', 'material', 'insumos', 'recursos',
    'componentes', 'elementos'
]

KEYWORDS_EQUIPOS = [
    'equipos', 'equipo', 'maquinaria', 'herramientas',
    'maquinas', 'herramienta'
]

# Palabras clave para clasificar tipo de recurso
MATERIAL_INDICATORS = [
    'cemento', 'arena', 'piedra', 'grava', 'acero', 'hierro',
    'alambre', 'clavo', 'madera', 'ladrillo', 'bloque',
    'pintura', 'barniz', 'pegamento', 'adhesivo', 'tubo',
    'tuberia', 'cable', 'conductor', 'varilla', 'perfil'
]

EQUIPO_INDICATORS = [
    'mezcladora', 'vibrador', 'cortadora', 'trompo',
    'camion', 'volquete', 'retroexcavadora', 'cargador',
    'compresor', 'martillo', 'taladro', 'soldadora',
    'andamio', 'encofrado', 'puntales'
]


# ═══════════════════════════════════════════════════════════════════════════
# NORMALIZACIÓN DE UNIDADES
# ═══════════════════════════════════════════════════════════════════════════

UNIDADES_NORMALIZADAS = {
    # Longitud
    'm': ['m', 'mt', 'mts', 'metro', 'metros'],
    'km': ['km', 'kilometro', 'kilometros'],

    # Área
    'm²': ['m2', 'm²', 'm^2', 'metro cuadrado', 'metros cuadrados'],
    'ha': ['ha', 'hectarea', 'hectareas'],

    # Volumen
    'm³': ['m3', 'm³', 'm^3', 'metro cubico', 'metros cubicos'],
    'lt': ['lt', 'l', 'litro', 'litros'],
    'gln': ['gln', 'gl', 'galon', 'galones'],

    # Peso
    'kg': ['kg', 'kilo', 'kilogramo', 'kilogramos'],
    'ton': ['ton', 't', 'tonelada', 'toneladas'],

    # Unidad
    'u': ['u', 'un', 'und', 'unid', 'unidad', 'unidades', 'pza', 'pieza', 'piezas']
}


def normalizar_unidad(unidad_raw: str) -> str:
    """
    Normaliza una unidad a su forma estándar.

    Args:
        unidad_raw: Unidad extraída del texto (puede tener typos)

    Returns:
        Unidad normalizada (ej: "m2" → "m²")

    Example:
        >>> normalizar_unidad("m2")
        'm²'
        >>> normalizar_unidad("metro cuadrado")
        'm²'
        >>> normalizar_unidad("und")
        'u'
    """
    unidad_lower = unidad_raw.lower().strip()

    for unidad_norm, variantes in UNIDADES_NORMALIZADAS.items():
        if unidad_lower in variantes:
            return unidad_norm

    # Si no se encuentra, devolver la original limpia
    return unidad_raw.strip()


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN DE RUBROS
# ═══════════════════════════════════════════════════════════════════════════

def extraer_codigo_rubro(texto: str) -> Optional[str]:
    """
    Extrae código de rubro del texto (ej: "01.01.01").

    Args:
        texto: Texto donde buscar el código

    Returns:
        Código encontrado o None

    Example:
        >>> extraer_codigo_rubro("01.01.01 EXCAVACIÓN MANUAL")
        '01.01.01'
    """
    match = re.search(PATRON_CODIGO, texto)
    return match.group(1) if match else None


def extraer_unidad(texto: str) -> Optional[str]:
    """
    Extrae unidad de medida del texto.

    Args:
        texto: Texto donde buscar la unidad

    Returns:
        Unidad encontrada y normalizada, o None

    Example:
        >>> extraer_unidad("Precio por m2")
        'm²'
    """
    match = re.search(PATRON_UNIDAD, texto, re.IGNORECASE)
    if match:
        return normalizar_unidad(match.group(1))
    return None


def segmentar_en_rubros(texto_completo: str) -> List[str]:
    """
    Segmenta texto completo en bloques de rubros.

    Estrategia: busca patrones de código (XX.XX.XX) como delimitadores.

    Args:
        texto_completo: Texto de una o varias páginas

    Returns:
        Lista de bloques de texto, uno por rubro

    Example:
        >>> texto = "01.01 RUBRO 1\\nDetalle...\\n02.01 RUBRO 2\\nDetalle..."
        >>> bloques = segmentar_en_rubros(texto)
        >>> len(bloques)
        2
    """
    # Buscar todas las posiciones donde aparecen códigos de rubro
    matches = list(re.finditer(PATRON_CODIGO, texto_completo))

    if not matches:
        logger.warning("No se encontraron códigos de rubro en el texto")
        return []

    bloques = []

    for i, match in enumerate(matches):
        start = match.start()

        # Fin del bloque: inicio del siguiente rubro o fin del texto
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(texto_completo)

        bloque = texto_completo[start:end].strip()
        bloques.append(bloque)

    logger.info(f"Se encontraron {len(bloques)} bloques de rubros")
    return bloques


# ═══════════════════════════════════════════════════════════════════════════
# PARSEO DE RUBRO INDIVIDUAL
# ═══════════════════════════════════════════════════════════════════════════

def parsear_rubro(
    bloque_texto: str,
    page_number: int
) -> Tuple[Optional[Rubro], List[ParseWarning]]:
    """
    Parsea un bloque de texto para extraer un Rubro.

    Args:
        bloque_texto: Texto del rubro
        page_number: Número de página de origen

    Returns:
        Tuple[Rubro | None, List[ParseWarning]]:
            - Rubro parseado (None si falla)
            - Lista de warnings generados

    Example:
        >>> bloque = "01.01.01 EXCAVACIÓN MANUAL\\nUnidad: m³\\nDescripción..."
        >>> rubro, warnings = parsear_rubro(bloque, page_number=1)
        >>> print(rubro.codigo)
        '01.01.01'
    """
    warnings = []

    # Extraer código
    codigo = extraer_codigo_rubro(bloque_texto)
    if not codigo:
        warning = ParseWarning(
            warning_id=generar_warning_id(page_number, WarningKind.RUBRO_INCOMPLETE),
            page=page_number,
            kind=WarningKind.RUBRO_INCOMPLETE,
            message="No se pudo extraer código de rubro",
            snippet=bloque_texto[:200],
            severity="HIGH"
        )
        warnings.append(warning)
        return None, warnings

    # Generar ID
    rubro_id = generar_rubro_id(codigo, page_number)

    # Extraer primera línea como descripción (heurística)
    lineas = bloque_texto.split('\n')
    descripcion = lineas[0].replace(codigo, '').strip() if lineas else ""

    if not descripcion:
        warning = ParseWarning(
            warning_id=generar_warning_id(page_number, WarningKind.RUBRO_INCOMPLETE),
            rubro_id=rubro_id,
            page=page_number,
            kind=WarningKind.RUBRO_INCOMPLETE,
            message="Descripción de rubro vacía",
            snippet=bloque_texto[:200],
            severity="MEDIUM"
        )
        warnings.append(warning)
        descripcion = "SIN DESCRIPCIÓN"

    # Extraer unidad
    unidad = extraer_unidad(bloque_texto)
    if not unidad:
        warning = ParseWarning(
            warning_id=generar_warning_id(page_number, WarningKind.UNIDAD_DESCONOCIDA),
            rubro_id=rubro_id,
            page=page_number,
            kind=WarningKind.UNIDAD_DESCONOCIDA,
            message="No se pudo extraer unidad de medida",
            snippet=bloque_texto[:200],
            severity="MEDIUM"
        )
        warnings.append(warning)
        unidad = "SIN UNIDAD"

    # Crear objeto Rubro
    rubro = Rubro(
        rubro_id=rubro_id,
        codigo=codigo,
        descripcion=descripcion,
        unidad=unidad,
        source_pages=[page_number],
        confidence=1.0 if not warnings else 0.7  # Reducir confidence si hay warnings
    )

    return rubro, warnings


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN DE RECURSOS (Materiales/Equipos)
# ═══════════════════════════════════════════════════════════════════════════

def clasificar_tipo_recurso(nombre_recurso: str) -> TipoRecurso:
    """
    Clasifica un recurso como MATERIAL o EQUIPO usando heurísticas.

    Estrategia:
    1. Buscar palabras clave en el nombre
    2. Si no se encuentra, usar fuzzy matching
    3. Fallback: DESCONOCIDO

    Args:
        nombre_recurso: Nombre/descripción del recurso

    Returns:
        TipoRecurso: MATERIAL | EQUIPO | DESCONOCIDO

    Example:
        >>> clasificar_tipo_recurso("Cemento Portland tipo I")
        TipoRecurso.MATERIAL
        >>> clasificar_tipo_recurso("Mezcladora de concreto")
        TipoRecurso.EQUIPO
    """
    nombre_lower = nombre_recurso.lower()

    # 1. Búsqueda exacta de palabras clave
    for keyword in MATERIAL_INDICATORS:
        if keyword in nombre_lower:
            return TipoRecurso.MATERIAL

    for keyword in EQUIPO_INDICATORS:
        if keyword in nombre_lower:
            return TipoRecurso.EQUIPO

    # 2. Fuzzy matching (si el nombre es similar a algún indicador)
    max_similarity_material = max(
        (fuzz.partial_ratio(nombre_lower, keyword) for keyword in MATERIAL_INDICATORS),
        default=0
    )
    max_similarity_equipo = max(
        (fuzz.partial_ratio(nombre_lower, keyword) for keyword in EQUIPO_INDICATORS),
        default=0
    )

    threshold = 70  # Umbral de similitud

    if max_similarity_material > threshold and max_similarity_material > max_similarity_equipo:
        return TipoRecurso.MATERIAL
    elif max_similarity_equipo > threshold:
        return TipoRecurso.EQUIPO

    # 3. Fallback
    return TipoRecurso.DESCONOCIDO


def extraer_recursos(
    bloque_texto: str,
    rubro: Rubro
) -> Tuple[List[Recurso], List[ParseWarning]]:
    """
    Extrae lista de recursos (materiales/equipos) de un bloque de rubro.

    Args:
        bloque_texto: Texto del bloque completo
        rubro: Objeto Rubro padre

    Returns:
        Tuple[List[Recurso], List[ParseWarning]]:
            - Lista de recursos parseados
            - Lista de warnings

    Example:
        >>> bloque = "...\\nMATERIALES:\\n- Cemento 50kg\\n- Arena m³"
        >>> recursos, warns = extraer_recursos(bloque, rubro)
        >>> len(recursos)
        2
    """
    recursos = []
    warnings = []

    # Buscar secciones de materiales/equipos
    lineas = bloque_texto.split('\n')

    recursos_candidatos = []
    en_seccion_recursos = False

    for linea in lineas:
        linea_lower = linea.lower()

        # Detectar inicio de sección de recursos
        if any(kw in linea_lower for kw in KEYWORDS_MATERIALES + KEYWORDS_EQUIPOS):
            en_seccion_recursos = True
            continue

        # Si estamos en sección de recursos y la línea parece un item
        if en_seccion_recursos:
            # Detectar líneas que parecen items (comienzan con - o * o número)
            if re.match(r'^[\-\*\•\d\)]', linea.strip()):
                recursos_candidatos.append(linea.strip())

    # Parsear cada recurso candidato
    for idx, recurso_texto in enumerate(recursos_candidatos):
        # Limpiar marcadores de lista
        recurso_texto = re.sub(r'^[\-\*\•\d\)\.]+\s*', '', recurso_texto).strip()

        if not recurso_texto or len(recurso_texto) < 3:
            continue

        # Clasificar tipo
        tipo = clasificar_tipo_recurso(recurso_texto)

        # Generar warning si no se pudo clasificar
        if tipo == TipoRecurso.DESCONOCIDO:
            warning = ParseWarning(
                warning_id=generar_warning_id(rubro.source_pages[0], WarningKind.RECURSO_SIN_TIPO),
                rubro_id=rubro.rubro_id,
                page=rubro.source_pages[0],
                kind=WarningKind.RECURSO_SIN_TIPO,
                message=f"No se pudo clasificar recurso: {recurso_texto}",
                snippet=recurso_texto,
                severity="LOW"
            )
            warnings.append(warning)

        # Extraer unidad (si existe en el texto del recurso)
        unidad_recurso = extraer_unidad(recurso_texto)

        # Crear objeto Recurso
        recurso = Recurso(
            recurso_id=generar_recurso_id(rubro.rubro_id, idx),
            rubro_id=rubro.rubro_id,
            tipo=tipo,
            nombre=recurso_texto,
            unidad=unidad_recurso,
            cantidad=None,  # TODO: parsear cantidades (regex para números)
            source_snippet=recurso_texto
        )

        recursos.append(recurso)

    logger.info(
        f"Extraídos {len(recursos)} recursos del rubro {rubro.codigo}"
    )

    return recursos, warnings


# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE COMPLETO DE PARSEO
# ═══════════════════════════════════════════════════════════════════════════

def parsear_texto_completo(
    texto: str,
    page_number: int
) -> Tuple[List[Rubro], List[Recurso], List[ParseWarning]]:
    """
    Parsea texto completo de una página para extraer rubros y recursos.

    Esta es la función principal del módulo de parseo.

    Args:
        texto: Texto extraído de la página (digital o OCR)
        page_number: Número de página

    Returns:
        Tuple[List[Rubro], List[Recurso], List[ParseWarning]]:
            - Lista de rubros encontrados
            - Lista de recursos encontrados
            - Lista de warnings

    Example:
        >>> texto = open("page1.txt").read()
        >>> rubros, recursos, warnings = parsear_texto_completo(texto, page_number=1)
        >>> print(f"Encontrados {len(rubros)} rubros y {len(recursos)} recursos")
    """
    logger.info(f"Parseando texto de página {page_number}")

    rubros = []
    recursos = []
    warnings = []

    # 1. Segmentar en bloques de rubros
    bloques = segmentar_en_rubros(texto)

    # 2. Parsear cada bloque
    for bloque in bloques:
        # Parsear rubro
        rubro, rubro_warnings = parsear_rubro(bloque, page_number)
        warnings.extend(rubro_warnings)

        if rubro:
            rubros.append(rubro)

            # Extraer recursos del rubro
            recursos_rubro, recursos_warnings = extraer_recursos(bloque, rubro)
            recursos.extend(recursos_rubro)
            warnings.extend(recursos_warnings)

    logger.info(
        f"Parseo completado: {len(rubros)} rubros, "
        f"{len(recursos)} recursos, {len(warnings)} warnings"
    )

    return rubros, recursos, warnings
