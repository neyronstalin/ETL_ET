"""
Extractor de secciones específicas de Especificaciones Técnicas.

Detecta bloques de rubros y extrae solo las secciones:
- 2. MATERIALES
- 3. EQUIPO MÍNIMO

Ignora todo el resto (Definición, Procedimientos, etc.)
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RubroBlock:
    """Bloque de un rubro completo en el PDF."""
    codigo: str
    nombre: str
    unidad: str
    page_number: int
    full_text: str
    start_line: int
    end_line: int


@dataclass
class ResourceSection:
    """Sección de recursos (MATERIALES o EQUIPO)."""
    section_type: str  # "MATERIALES" o "EQUIPO"
    raw_text: str
    items: List[str]
    is_empty: bool  # True si dice "No aplica" o está vacío
    observations: List[str]  # Texto condicional/reglas


def detect_rubro_blocks(text: str, page_number: int) -> List[RubroBlock]:
    """
    Detecta bloques de rubros en el texto de una página.

    Args:
        text: Texto completo de la página
        page_number: Número de página

    Returns:
        Lista de RubroBlock encontrados
    """
    blocks = []

    # Patrón de código de rubro: XX.XXX.X.XX o XX.XXX
    # Ejemplo: 01.001.4.01, 01.002.4.01
    rubro_pattern = r'\b(\d{2}\.\d{3}(?:\.\d{1,2}\.\d{2})?)\s+([A-ZÑÁÉÍÓÚ\s,]+?)(?:\s+(m\d?|u|kg|gl|ha|km))?$'

    lines = text.split('\n')

    for i, line in enumerate(lines):
        # Buscar inicio de rubro (línea con "Rubro:")
        if line.strip().startswith("Rubro:"):
            # La siguiente línea debería tener el código
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                match = re.match(rubro_pattern, next_line.strip(), re.IGNORECASE)

                if match:
                    codigo = match.group(1)
                    nombre = match.group(2).strip()
                    unidad = match.group(3) if match.group(3) else "u"

                    # Buscar fin del bloque (siguiente rubro o fin de página)
                    end_line = _find_block_end(lines, i + 2)

                    block_text = '\n'.join(lines[i:end_line])

                    block = RubroBlock(
                        codigo=codigo,
                        nombre=nombre,
                        unidad=unidad,
                        page_number=page_number,
                        full_text=block_text,
                        start_line=i,
                        end_line=end_line
                    )

                    blocks.append(block)

    return blocks


def _find_block_end(lines: List[str], start: int) -> int:
    """
    Encuentra el fin de un bloque de rubro.

    El bloque termina cuando:
    - Se encuentra otro "Rubro:"
    - Se encuentra un patrón de nueva sección principal
    - Se llega al fin de la página
    """
    for i in range(start, len(lines)):
        line = lines[i].strip()

        # Siguiente rubro
        if line.startswith("Rubro:"):
            return i

        # Nueva sección principal (otro documento)
        if re.match(r'^\d{2}\.\d{3}\s+[A-Z]', line):
            return i

    return len(lines)


def extract_material_section(block: RubroBlock) -> Optional[ResourceSection]:
    """
    Extrae la sección "2. MATERIALES" de un bloque de rubro.

    Args:
        block: Bloque de rubro completo

    Returns:
        ResourceSection con materiales o None si no se encuentra
    """
    return _extract_numbered_section(block, "2.", "MATERIALES", "3.")


def extract_equipo_section(block: RubroBlock) -> Optional[ResourceSection]:
    """
    Extrae la sección "3. EQUIPO MÍNIMO" de un bloque de rubro.

    Args:
        block: Bloque de rubro completo

    Returns:
        ResourceSection con equipos o None si no se encuentra
    """
    return _extract_numbered_section(block, "3.", "EQUIPO", "4.")


def _extract_numbered_section(
    block: RubroBlock,
    section_number: str,
    section_keyword: str,
    next_section: str
) -> Optional[ResourceSection]:
    """
    Extrae una sección numerada (2. MATERIALES, 3. EQUIPO, etc.)

    Args:
        block: Bloque de rubro
        section_number: Número de sección (ej: "2.")
        section_keyword: Palabra clave de la sección (ej: "MATERIALES")
        next_section: Número de siguiente sección para delimitar (ej: "3.")

    Returns:
        ResourceSection o None si no se encuentra
    """
    lines = block.full_text.split('\n')

    # Buscar inicio de sección
    start_idx = None
    for i, line in enumerate(lines):
        if section_number in line and section_keyword in line.upper():
            start_idx = i
            break

    if start_idx is None:
        return None

    # Buscar fin de sección (siguiente sección numerada)
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        line = lines[i].strip()

        # Siguiente sección numerada
        if re.match(r'^\d+\.', line):
            end_idx = i
            break

    # Extraer texto de la sección (sin el header)
    section_lines = lines[start_idx + 1:end_idx]
    raw_text = '\n'.join(section_lines).strip()

    # Detectar si está vacía o dice "No aplica"
    is_empty = _is_empty_section(raw_text)

    # Parsear items
    items = []
    observations = []

    if not is_empty:
        items, observations = _parse_resource_lines(raw_text)

    section_type = "MATERIALES" if "MATERIALES" in section_keyword else "EQUIPO"

    return ResourceSection(
        section_type=section_type,
        raw_text=raw_text,
        items=items,
        is_empty=is_empty,
        observations=observations
    )


def _is_empty_section(text: str) -> bool:
    """
    Detecta si una sección está vacía o dice "No aplica".

    Args:
        text: Texto de la sección

    Returns:
        True si está vacía
    """
    text_lower = text.lower().strip()
    # Remover puntos finales para comparación
    text_clean = text_lower.rstrip('.')

    # Patrones de sección vacía
    empty_patterns = [
        "no aplica",
        "no requiere",
        "no corresponde",
        "ninguno",
        "ninguna",
        "n/a",
        "na",
        ""
    ]

    # Comparación exacta
    if text_clean in empty_patterns:
        return True

    # Texto muy corto (<10 chars) probablemente vacío
    if len(text_lower) < 10:
        return True

    return False


def _parse_resource_lines(text: str) -> Tuple[List[str], List[str]]:
    """
    Parsea líneas de recursos, separando items reales de observaciones.

    Reglas:
    - Items: nombres concretos de materiales/equipos
    - Observaciones: texto con "según", "de acuerdo", "mínimo", condicionales

    Args:
        text: Texto de la sección de recursos

    Returns:
        Tupla (items, observations)
    """
    items = []
    observations = []

    # Patrones de observación (no son recursos)
    observation_patterns = [
        r'\bsegún\b',
        r'\bde acuerdo\b',
        r'\bconforme\b',
        r'\bmínimo\b',
        r'\bsi\s+\w+',
        r'\bcuando\b',
        r'\bdebe\b',
        r'\bserá\b',
        r'\bestar[áa]\b'
    ]

    # Si es una sola línea con comas, split directo
    if ',' in text and text.count('\n') <= 1:
        raw_items = [item.strip() for item in text.split(',')]
        for item in raw_items:
            if _is_observation_text(item, observation_patterns):
                observations.append(item)
            elif len(item) > 2:  # Ignorar items muy cortos
                items.append(item)
        return items, observations

    # Múltiples líneas: procesar línea por línea
    lines = text.split('\n')
    for line in lines:
        line = line.strip()

        # Ignorar líneas vacías
        if not line:
            continue

        # Detectar viñetas (•, -, *)
        if line.startswith(('•', '-', '*')):
            line = line[1:].strip()

        # Separar por comas si tiene
        if ',' in line:
            sub_items = [s.strip() for s in line.split(',')]
            for item in sub_items:
                if _is_observation_text(item, observation_patterns):
                    observations.append(item)
                elif len(item) > 2:
                    items.append(item)
        else:
            # Línea completa
            if _is_observation_text(line, observation_patterns):
                observations.append(line)
            elif len(line) > 2:
                items.append(line)

    return items, observations


def _is_observation_text(text: str, patterns: List[str]) -> bool:
    """
    Detecta si un texto es una observación/regla en vez de un recurso.

    Args:
        text: Texto a evaluar
        patterns: Lista de patrones regex de observación

    Returns:
        True si es observación
    """
    text_lower = text.lower()

    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True

    # Texto muy largo (>80 chars) probablemente es descripción, no recurso
    if len(text) > 80:
        return True

    return False


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════

def extract_resources_from_rubro(block: RubroBlock) -> Dict[str, ResourceSection]:
    """
    Extrae recursos (materiales y equipo) de un bloque de rubro.

    Args:
        block: Bloque de rubro completo

    Returns:
        Dict con claves "materiales" y "equipo"
    """
    materiales = extract_material_section(block)
    equipo = extract_equipo_section(block)

    return {
        "materiales": materiales,
        "equipo": equipo
    }
