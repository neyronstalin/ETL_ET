"""
Utilidades de normalización de texto.

Funciones para normalizar códigos de rubro, unidades, y corregir errores comunes de OCR.
"""

import re
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════
# NORMALIZACIÓN DE CÓDIGOS DE RUBRO
# ═══════════════════════════════════════════════════════════════════════════

def normalize_rubro_code(code: str) -> str:
    """
    Normaliza código de rubro a formato estándar: XX.XX.XX

    Casos manejados:
    - "1.1.1" → "01.01.01"
    - "01-01-01" → "01.01.01"
    - "01 01 01" → "01.01.01"
    - "O1.01.01" → "01.01.01" (OCR: O→0)
    - "01.0l.01" → "01.01.01" (OCR: l→1)

    Args:
        code: Código de rubro raw

    Returns:
        Código normalizado en formato XX.XX.XX

    Example:
        >>> normalize_rubro_code("1.1.1")
        '01.01.01'
        >>> normalize_rubro_code("O1-02-03")
        '01.02.03'
        >>> normalize_rubro_code("1.0l.5")
        '01.01.05'
    """
    # Limpiar espacios
    code = code.strip()

    # Corregir errores comunes de OCR
    code = fix_ocr_errors(code)

    # Reemplazar separadores no estándar por puntos
    code = re.sub(r'[\-\s]+', '.', code)

    # Extraer números
    parts = re.findall(r'\d+', code)

    if len(parts) < 2:
        # Si no tiene al menos 2 niveles, retornar original
        return code

    # Pad con ceros a la izquierda (2 dígitos)
    parts_padded = [part.zfill(2) for part in parts]

    # Tomar primeros 3 niveles (o los que haya)
    parts_final = parts_padded[:3]

    return '.'.join(parts_final)


def fix_ocr_errors(text: str) -> str:
    """
    Corrige errores comunes de OCR en texto.

    Errores típicos:
    - O (letra O) → 0 (cero)
    - l (ele minúscula) → 1 (uno)
    - I (i mayúscula) → 1 (uno)
    - S → 5 (en códigos)

    Args:
        text: Texto con posibles errores OCR

    Returns:
        Texto corregido

    Example:
        >>> fix_ocr_errors("O1.0l.05")
        '01.01.05'
    """
    # Crear copia para trabajar
    fixed = text

    # O mayúscula → 0 (solo si está rodeada de dígitos o al inicio)
    fixed = re.sub(r'\bO(\d)', r'0\1', fixed)  # O5 → 05
    fixed = re.sub(r'(\d)O(\d)', r'\g<1>0\2', fixed)  # 1O5 → 105

    # l minúscula → 1 (en contexto numérico)
    fixed = re.sub(r'(\d)l(\d)', r'\g<1>1\2', fixed)  # 0l1 → 011
    fixed = re.sub(r'(\d)l\b', r'\g<1>1', fixed)  # 0l → 01

    # I mayúscula → 1 (en contexto numérico)
    fixed = re.sub(r'(\d)I(\d)', r'\g<1>1\2', fixed)  # 0I1 → 011

    return fixed


def is_valid_rubro_code(code: str) -> bool:
    """
    Verifica si un código de rubro es válido.

    Formato válido: N.N.N o NN.NN.NN (2-3 niveles, separados por punto)

    Args:
        code: Código a validar

    Returns:
        True si es válido, False en caso contrario

    Example:
        >>> is_valid_rubro_code("01.01.01")
        True
        >>> is_valid_rubro_code("1.1")
        False
        >>> is_valid_rubro_code("ABC")
        False
    """
    # Patron: 1-3 dígitos, punto, 1-3 dígitos, opcionalmente más niveles
    pattern = r'^\d{1,3}(\.\d{1,3}){1,3}$'
    return bool(re.match(pattern, code))


# ═══════════════════════════════════════════════════════════════════════════
# NORMALIZACIÓN DE UNIDADES
# ═══════════════════════════════════════════════════════════════════════════

# Mapeo de unidades (ampliado desde v1.0)
UNIDADES_NORMALIZADAS = {
    # Longitud
    'm': ['m', 'mt', 'mts', 'metro', 'metros', 'mtr'],
    'km': ['km', 'kilometro', 'kilometros', 'kms'],
    'cm': ['cm', 'centimetro', 'centimetros', 'cms'],

    # Área
    'm²': ['m2', 'm²', 'm^2', 'metro cuadrado', 'metros cuadrados', 'm2.', 'm²​'],
    'km²': ['km2', 'km²', 'kilometro cuadrado', 'kilometros cuadrados'],
    'ha': ['ha', 'hectarea', 'hectareas', 'has'],

    # Volumen
    'm³': ['m3', 'm³', 'm^3', 'metro cubico', 'metros cubicos', 'm3.', 'm³​'],
    'lt': ['lt', 'l', 'litro', 'litros', 'lts'],
    'gln': ['gln', 'gl', 'galon', 'galones', 'gal'],

    # Peso
    'kg': ['kg', 'kilo', 'kilogramo', 'kilogramos', 'kgs', 'kg.'],
    'ton': ['ton', 't', 'tonelada', 'toneladas', 'tn'],
    'g': ['g', 'gramo', 'gramos', 'gr', 'grs'],

    # Unidad
    'u': ['u', 'un', 'und', 'unid', 'unidad', 'unidades', 'pza', 'pieza', 'piezas',
          'pzs', 'pz', 'uni'],

    # Otros
    'bls': ['bls', 'bolsa', 'bolsas', 'bol'],
    'gl': ['gl', 'global', 'glb'],
    '%': ['%', 'porcentaje', 'pct', 'percent'],
    'h': ['h', 'hora', 'horas', 'hr', 'hrs', 'hh'],
    'día': ['dia', 'dias', 'día', 'días', 'd'],
    'mes': ['mes', 'meses', 'm'],
}


def normalize_unidad(unidad_raw: str) -> str:
    """
    Normaliza unidad de medida a su forma estándar.

    Args:
        unidad_raw: Unidad raw extraída del texto

    Returns:
        Unidad normalizada

    Example:
        >>> normalize_unidad("m2")
        'm²'
        >>> normalize_unidad("metro cuadrado")
        'm²'
        >>> normalize_unidad("und")
        'u'
        >>> normalize_unidad("kgs")
        'kg'
    """
    unidad_lower = unidad_raw.lower().strip()

    # Remover puntos finales
    unidad_lower = unidad_lower.rstrip('.')

    for unidad_norm, variantes in UNIDADES_NORMALIZADAS.items():
        if unidad_lower in variantes:
            return unidad_norm

    # Si no se encuentra, devolver la original limpia
    return unidad_raw.strip()


# ═══════════════════════════════════════════════════════════════════════════
# LIMPIEZA DE STRINGS
# ═══════════════════════════════════════════════════════════════════════════

def clean_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Limpia string: espacios, saltos de línea múltiples, caracteres raros.

    Args:
        text: Texto a limpiar
        max_length: Longitud máxima (opcional, trunca si excede)

    Returns:
        Texto limpio

    Example:
        >>> clean_string("  Hola\\n\\n\\nmundo  ")
        'Hola\\nmundo'
        >>> clean_string("Texto largo...", max_length=10)
        'Texto l...'
    """
    # Remover espacios al inicio/fin
    text = text.strip()

    # Normalizar espacios múltiples
    text = re.sub(r' +', ' ', text)

    # Normalizar saltos de línea múltiples
    text = re.sub(r'\n\n+', '\n\n', text)

    # Remover caracteres de control (excepto \n, \t)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Truncar si excede longitud
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + '...'

    return text


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitiza nombre de archivo: remueve caracteres inválidos.

    Args:
        filename: Nombre de archivo
        max_length: Longitud máxima

    Returns:
        Nombre sanitizado

    Example:
        >>> sanitize_filename("Rubro 01/01\\01.txt")
        'Rubro_01_01_01.txt'
        >>> sanitize_filename("Archivo*con?chars:inválidos")
        'Archivo_con_chars_inválidos'
    """
    # Reemplazar caracteres inválidos por underscore
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Truncar si excede
    if len(sanitized) > max_length:
        # Preservar extensión si existe
        parts = sanitized.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            max_name_len = max_length - len(ext) - 1
            sanitized = name[:max_name_len] + '.' + ext
        else:
            sanitized = sanitized[:max_length]

    return sanitized


def sanitize_excel_sheet_name(name: str) -> str:
    """
    Sanitiza nombre de hoja de Excel.

    Reglas:
    - Máximo 31 caracteres
    - No puede contener: \\ / ? * [ ]
    - No puede comenzar o terminar con '

    Args:
        name: Nombre de hoja propuesto

    Returns:
        Nombre sanitizado

    Example:
        >>> sanitize_excel_sheet_name("Rubro 01.01.01 - Excavación")
        'Rubro 01.01.01 - Excavación'
        >>> sanitize_excel_sheet_name("Rubro [muy] largo*con?chars/inválidos\\que excede el límite")
        'Rubro _muy_ largo_con_chars'
    """
    # Reemplazar caracteres inválidos
    invalid_chars = r'[\\/:*?\[\]]'
    sanitized = re.sub(invalid_chars, '_', name)

    # Remover comillas al inicio/fin
    sanitized = sanitized.strip("'")

    # Truncar a 31 caracteres
    if len(sanitized) > 31:
        sanitized = sanitized[:31]

    # Si quedó vacío, usar default
    if not sanitized:
        sanitized = "Sheet1"

    return sanitized


# ═══════════════════════════════════════════════════════════════════════════
# DETECCIÓN DE PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

def extract_codigo_from_text(text: str) -> Optional[str]:
    """
    Extrae código de rubro desde texto (wrapper de v1.0).

    Args:
        text: Texto donde buscar código

    Returns:
        Código encontrado (normalizado) o None

    Example:
        >>> extract_codigo_from_text("01.01.01 EXCAVACIÓN MANUAL")
        '01.01.01'
        >>> extract_codigo_from_text("Sin código")
        None
    """
    # Patrón: 1-3 dígitos, separador, repetir 2-3 veces
    pattern = r'(\d{1,3}[\.\-\s]\d{1,3}[\.\-\s]\d{1,3})'
    match = re.search(pattern, text)

    if match:
        code_raw = match.group(1)
        return normalize_rubro_code(code_raw)

    return None


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Trunca texto si excede longitud máxima.

    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar si se trunca

    Returns:
        Texto truncado

    Example:
        >>> truncate_text("Texto muy largo", max_length=10)
        'Texto m...'
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def remove_extra_whitespace(text: str) -> str:
    """
    Remueve espacios en blanco extra (espacios múltiples, tabs, etc).

    Args:
        text: Texto a limpiar

    Returns:
        Texto sin espacios extra

    Example:
        >>> remove_extra_whitespace("Hola    mundo\\t\\n")
        'Hola mundo'
    """
    # Reemplazar cualquier whitespace múltiple por un espacio
    return ' '.join(text.split())


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "normalize_rubro_code",
    "fix_ocr_errors",
    "is_valid_rubro_code",
    "normalize_unidad",
    "clean_string",
    "sanitize_filename",
    "sanitize_excel_sheet_name",
    "extract_codigo_from_text",
    "truncate_text",
    "remove_extra_whitespace",
]
