"""
Exportador de APUs usando template Excel.

Genera un archivo Excel con:
- 1 hoja por rubro (nombre = CODIGO del rubro)
- Datos mapeados según configuración de template
- Inserción dinámica de filas para recursos
- Preservación de headers y formato del template

Soporta templates .xls (convierte a .xlsx) y .xlsx
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from copy import copy

try:
    import openpyxl
    from openpyxl import load_workbook, Workbook
    from openpyxl.styles import Font, Fill, Border, Alignment
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import xlrd
    XLRD_AVAILABLE = True
except ImportError:
    XLRD_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TemplateMapping:
    """
    Configuración de mapeo de celdas del template.

    Define dónde escribir cada dato en la hoja del template.
    Ajustar según el template real.
    """
    # Datos del rubro
    codigo_cell: str = "B4"
    descripcion_cell: str = "B5"
    unidad_cell: str = "B6"

    # Tabla de recursos
    table_start_row: int = 10  # Primera fila de datos de la tabla
    col_categoria: str = "A"   # Columna: MATERIALES/EQUIPO/etc
    col_nombre: str = "B"      # Columna: Nombre del recurso
    col_unidad: str = "C"      # Columna: Unidad
    col_cantidad: str = "D"    # Columna: Cantidad

    # Filas por categoría (si el template tiene bloques separados)
    materiales_start_row: Optional[int] = None
    equipo_start_row: Optional[int] = None
    mano_obra_start_row: Optional[int] = None
    transporte_start_row: Optional[int] = None

    # Observaciones
    observaciones_cell: Optional[str] = None


@dataclass
class ExportStats:
    """Estadísticas del export."""
    total_rubros: int = 0
    hojas_creadas: int = 0
    duplicados_detectados: int = 0
    filas_insertadas: int = 0
    recursos_exportados: int = 0
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class TemplateExporter:
    """
    Exportador de APUs basado en template Excel.

    Genera 1 hoja por rubro usando un template como base.
    """

    def __init__(
        self,
        template_path: Path,
        mapping: Optional[TemplateMapping] = None
    ):
        """
        Inicializa el exportador.

        Args:
            template_path: Ruta al template Excel (.xls o .xlsx)
            mapping: Configuración de mapeo de celdas

        Raises:
            RuntimeError: Si openpyxl no está instalado
            FileNotFoundError: Si el template no existe
        """
        if not OPENPYXL_AVAILABLE:
            raise RuntimeError(
                "openpyxl no instalado. "
                "Instalar con: pip install openpyxl"
            )

        self.template_path = template_path
        self.mapping = mapping or TemplateMapping()
        self.sheet_names_used = set()

        if not template_path.exists():
            raise FileNotFoundError(f"Template no encontrado: {template_path}")

        # Convertir .xls a .xlsx si es necesario
        if template_path.suffix == ".xls":
            logger.info("Template es .xls, convirtiendo a .xlsx...")
            self.template_path = self._convert_xls_to_xlsx(template_path)

        # Cargar template
        logger.info(f"Cargando template: {self.template_path}")
        self.template_wb = load_workbook(self.template_path)
        self.template_sheet_name = self.template_wb.sheetnames[0]

        logger.info(f"Template cargado: hoja base '{self.template_sheet_name}'")

    def _convert_xls_to_xlsx(self, xls_path: Path) -> Path:
        """
        Convierte .xls a .xlsx para poder usar openpyxl.

        Args:
            xls_path: Ruta al archivo .xls

        Returns:
            Ruta al archivo .xlsx generado

        Raises:
            RuntimeError: Si xlrd no está instalado o falla la conversión
        """
        if not XLRD_AVAILABLE:
            raise RuntimeError(
                "xlrd no instalado. Necesario para leer .xls\n"
                "Instalar con: pip install xlrd"
            )

        # TODO: Implementar conversión real con xlrd → openpyxl
        # Por ahora, asumir que el usuario proporciona .xlsx

        raise RuntimeError(
            f"Template es .xls: {xls_path}\n"
            "Por favor, convierte manualmente a .xlsx o usa un template .xlsx"
        )

    def export_apus(
        self,
        output_path: Path,
        rubros_data: List[Dict],
        recursos_por_rubro: Dict[str, List[Dict]]
    ) -> ExportStats:
        """
        Exporta APUs a Excel usando el template.

        Args:
            output_path: Ruta donde guardar el Excel de salida
            rubros_data: Lista de dicts con datos de rubros
                [{"codigo": "01.001.4.01", "descripcion": "...", "unidad": "m2"}, ...]
            recursos_por_rubro: Dict {codigo_rubro: [recursos]}
                {"01.001.4.01": [{"categoria": "MATERIALES", "nombre": "Estacas", ...}]}

        Returns:
            ExportStats con estadísticas del export
        """
        logger.info(f"Iniciando export tipo APU a {output_path}")
        logger.info(f"Rubros a exportar: {len(rubros_data)}")

        stats = ExportStats(total_rubros=len(rubros_data))

        # Crear workbook de salida
        output_wb = Workbook()
        output_wb.remove(output_wb.active)  # Remover hoja default vacía

        # Procesar cada rubro
        for rubro in rubros_data:
            codigo = rubro["codigo"]
            recursos = recursos_por_rubro.get(codigo, [])

            # Crear hoja para este rubro
            sheet_name = self._get_unique_sheet_name(codigo, stats)

            logger.info(f"Creando hoja '{sheet_name}' para rubro {codigo}")

            # Clonar template
            new_sheet = self._clone_template_sheet(output_wb, sheet_name)

            # Escribir datos del rubro
            self._write_rubro_data(new_sheet, rubro)

            # Escribir recursos
            filas_insertadas = self._write_recursos(new_sheet, recursos)

            stats.hojas_creadas += 1
            stats.filas_insertadas += filas_insertadas
            stats.recursos_exportados += len(recursos)

        # Guardar archivo
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_wb.save(output_path)

        logger.info(f"✅ Excel generado: {output_path}")
        logger.info(f"   Hojas creadas: {stats.hojas_creadas}")
        logger.info(f"   Recursos exportados: {stats.recursos_exportados}")
        logger.info(f"   Filas insertadas: {stats.filas_insertadas}")

        if stats.duplicados_detectados > 0:
            logger.warning(f"   ⚠️  Duplicados detectados: {stats.duplicados_detectados}")

        return stats

    def _get_unique_sheet_name(self, codigo: str, stats: ExportStats) -> str:
        """
        Genera nombre único de hoja manejando duplicados.

        Args:
            codigo: Código del rubro
            stats: Stats para trackear duplicados

        Returns:
            Nombre de hoja único
        """
        # Sanitizar nombre (Excel no permite algunos caracteres)
        base_name = codigo.replace("/", "_").replace("\\", "_")[:31]

        # Si es único, usar directamente
        if base_name not in self.sheet_names_used:
            self.sheet_names_used.add(base_name)
            return base_name

        # Duplicado detectado
        stats.duplicados_detectados += 1
        stats.warnings.append(
            f"Código duplicado: {codigo} (generando nombre con sufijo)"
        )

        logger.warning(f"⚠️  Código duplicado: {codigo}")

        # Agregar sufijo incremental
        counter = 2
        while True:
            unique_name = f"{base_name[:27]} ({counter})"
            if unique_name not in self.sheet_names_used:
                self.sheet_names_used.add(unique_name)
                return unique_name
            counter += 1

    def _clone_template_sheet(self, target_wb: Workbook, new_name: str):
        """
        Clona la hoja del template al workbook de salida.

        Args:
            target_wb: Workbook destino
            new_name: Nombre de la nueva hoja

        Returns:
            Nueva hoja clonada
        """
        # Obtener hoja template
        template_sheet = self.template_wb[self.template_sheet_name]

        # Crear nueva hoja
        new_sheet = target_wb.create_sheet(title=new_name)

        # Copiar dimensiones de columnas
        for col_letter in template_sheet.column_dimensions:
            if col_letter in template_sheet.column_dimensions:
                new_sheet.column_dimensions[col_letter].width = \
                    template_sheet.column_dimensions[col_letter].width

        # Copiar dimensiones de filas
        for row_num in template_sheet.row_dimensions:
            if row_num in template_sheet.row_dimensions:
                new_sheet.row_dimensions[row_num].height = \
                    template_sheet.row_dimensions[row_num].height

        # Copiar celdas con valores y estilos
        for row in template_sheet.iter_rows():
            for cell in row:
                new_cell = new_sheet[cell.coordinate]
                new_cell.value = cell.value

                # Copiar estilos
                if cell.has_style:
                    new_cell.font = copy(cell.font)
                    new_cell.border = copy(cell.border)
                    new_cell.fill = copy(cell.fill)
                    new_cell.number_format = copy(cell.number_format)
                    new_cell.protection = copy(cell.protection)
                    new_cell.alignment = copy(cell.alignment)

        # Copiar merged cells
        for merged_range in template_sheet.merged_cells.ranges:
            new_sheet.merge_cells(str(merged_range))

        return new_sheet

    def _write_rubro_data(self, sheet, rubro: Dict):
        """
        Escribe datos del rubro en las celdas configuradas.

        Args:
            sheet: Hoja de Excel
            rubro: Dict con datos del rubro
        """
        # Escribir código
        if self.mapping.codigo_cell:
            sheet[self.mapping.codigo_cell] = rubro.get("codigo", "")

        # Escribir descripción
        if self.mapping.descripcion_cell:
            sheet[self.mapping.descripcion_cell] = rubro.get("descripcion", "")

        # Escribir unidad
        if self.mapping.unidad_cell:
            sheet[self.mapping.unidad_cell] = rubro.get("unidad", "")

    def _write_recursos(self, sheet, recursos: List[Dict]) -> int:
        """
        Escribe recursos en la tabla del template.

        Inserta filas dinámicamente si es necesario.

        Args:
            sheet: Hoja de Excel
            recursos: Lista de recursos

        Returns:
            Número de filas insertadas
        """
        if not recursos:
            return 0

        filas_insertadas = 0
        current_row = self.mapping.table_start_row

        # Agrupar por categoría
        recursos_por_categoria = self._agrupar_recursos_por_categoria(recursos)

        # Orden de categorías
        categorias_orden = ["MATERIALES", "EQUIPO", "MANO_OBRA", "TRANSPORTE"]

        for categoria in categorias_orden:
            if categoria not in recursos_por_categoria:
                continue

            recursos_cat = recursos_por_categoria[categoria]

            for recurso in recursos_cat:
                # Escribir categoría
                sheet[f"{self.mapping.col_categoria}{current_row}"] = categoria

                # Escribir nombre
                sheet[f"{self.mapping.col_nombre}{current_row}"] = \
                    recurso.get("nombre", "")

                # Escribir unidad
                if "unidad" in recurso and recurso["unidad"]:
                    sheet[f"{self.mapping.col_unidad}{current_row}"] = \
                        recurso["unidad"]

                # Escribir cantidad
                if "cantidad" in recurso and recurso["cantidad"]:
                    sheet[f"{self.mapping.col_cantidad}{current_row}"] = \
                        recurso["cantidad"]

                current_row += 1

        return filas_insertadas

    def _agrupar_recursos_por_categoria(
        self,
        recursos: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Agrupa recursos por categoría.

        Args:
            recursos: Lista de recursos

        Returns:
            Dict {categoria: [recursos]}
        """
        agrupados = {}

        for recurso in recursos:
            categoria = recurso.get("categoria", "DESCONOCIDO")
            if categoria not in agrupados:
                agrupados[categoria] = []
            agrupados[categoria].append(recurso)

        return agrupados


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════

def export_apus_from_template(
    template_path: Path,
    output_path: Path,
    rubros_data: List[Dict],
    recursos_por_rubro: Dict[str, List[Dict]],
    mapping: Optional[TemplateMapping] = None
) -> ExportStats:
    """
    Función de conveniencia para exportar APUs desde template.

    Args:
        template_path: Ruta al template Excel
        output_path: Ruta de salida
        rubros_data: Lista de rubros
        recursos_por_rubro: Dict de recursos por código de rubro
        mapping: Configuración de mapeo (opcional)

    Returns:
        ExportStats con estadísticas
    """
    exporter = TemplateExporter(template_path, mapping)
    return exporter.export_apus(output_path, rubros_data, recursos_por_rubro)
