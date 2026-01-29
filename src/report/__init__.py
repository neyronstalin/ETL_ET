"""
Módulo de generación de reportes y artifacts.

Genera:
- OUT.json: Resultado completo serializado
- RUN_REPORT.md: Resumen ejecutivo
- rubros_md/*.md: Reportes individuales por rubro
"""

from src.report.json_generator import (
    generate_out_json,
    load_out_json,
    generate_summary_json
)

from src.report.md_reporter import (
    generate_run_report
)

from src.report.rubro_report import (
    generate_rubro_reports,
    generate_single_rubro_report,
    find_rubro_report,
    get_rubros_by_category
)

__all__ = [
    # JSON
    "generate_out_json",
    "load_out_json",
    "generate_summary_json",

    # MD Reports
    "generate_run_report",
    "generate_rubro_reports",
    "generate_single_rubro_report",

    # Utilities
    "find_rubro_report",
    "get_rubros_by_category",
]
