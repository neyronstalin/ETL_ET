"""
Módulo ETL para extracción tipo APU desde Especificaciones Técnicas.

Extrae SOLO secciones específicas:
- 2. MATERIALES
- 3. EQUIPO MÍNIMO

Ignora: Definición, Procedimientos, Medición, Forma de pago, etc.
"""

from .extract_sections import (
    RubroBlock,
    ResourceSection,
    detect_rubro_blocks,
    extract_material_section,
    extract_equipo_section,
    extract_resources_from_rubro
)

__all__ = [
    "RubroBlock",
    "ResourceSection",
    "detect_rubro_blocks",
    "extract_material_section",
    "extract_equipo_section",
    "extract_resources_from_rubro",
]
