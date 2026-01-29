"""
Módulo de logging estructurado.

Configura structlog para logging con contexto y trazabilidad.
"""

import logging
import sys
from pathlib import Path
import structlog
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE STRUCTLOG
# ═══════════════════════════════════════════════════════════════════════════

def configure_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_logs: bool = False
) -> None:
    """
    Configura el sistema de logging.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta opcional para guardar logs en archivo
        json_logs: Si True, usa formato JSON; si False, usa formato legible

    Example:
        >>> configure_logging(level="DEBUG", log_file=Path("logs/pipeline.log"))
    """
    # Configurar logging estándar
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper())
    )

    # Configurar procesadores de structlog
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        # Formato JSON para producción
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Formato legible para desarrollo/notebooks
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Si se especificó archivo, agregar handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Obtiene un logger estructurado.

    Args:
        name: Nombre del logger (usualmente __name__ del módulo)

    Returns:
        Logger configurado

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Procesando PDF", filename="test.pdf", page=1)
    """
    return structlog.get_logger(name)


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN POR DEFECTO
# ═══════════════════════════════════════════════════════════════════════════

# Configurar logging por defecto al importar el módulo
configure_logging(level="INFO", json_logs=False)
