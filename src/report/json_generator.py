"""
Generador de OUT.json con resultado completo del pipeline.

Este módulo exporta el PipelineResultV1_1 a JSON con formato legible
y validado contra los schemas de Pydantic.
"""

import json
from pathlib import Path
from typing import Optional
import hashlib
from datetime import datetime
import logging

from src.models.schemas import PipelineResultV1_1, ArtifactMetadata

logger = logging.getLogger(__name__)


def generate_out_json(
    result: PipelineResultV1_1,
    output_path: Path,
    indent: int = 2,
    ensure_ascii: bool = False
) -> ArtifactMetadata:
    """
    Genera archivo OUT.json con el resultado completo.

    Args:
        result: Resultado del pipeline v1.1
        output_path: Ruta donde guardar OUT.json
        indent: Indentación para formato legible
        ensure_ascii: Si False, permite caracteres Unicode (español)

    Returns:
        ArtifactMetadata del archivo generado
    """
    logger.info(f"Generando OUT.json en {output_path}")

    # Convertir a dict usando Pydantic
    result_dict = result.model_dump(mode='json')

    # Agregar metadatos adicionales
    result_dict['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'version': '1.1',
        'schema': 'PipelineResultV1_1'
    }

    # Escribir JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=indent, ensure_ascii=ensure_ascii)

    # Calcular checksum
    checksum = _calculate_file_checksum(output_path)

    # Crear metadata del artifact
    artifact = ArtifactMetadata(
        artifact_type="OUT.json",
        file_path=str(output_path),
        size_bytes=output_path.stat().st_size,
        generated_at=datetime.now(),
        checksum=checksum
    )

    logger.info(f"✅ OUT.json generado: {output_path.stat().st_size / 1024:.2f} KB")

    return artifact


def load_out_json(json_path: Path) -> PipelineResultV1_1:
    """
    Carga y valida OUT.json.

    Args:
        json_path: Ruta al archivo OUT.json

    Returns:
        PipelineResultV1_1 validado

    Raises:
        ValidationError: Si el JSON no es válido
        FileNotFoundError: Si el archivo no existe
    """
    logger.info(f"Cargando OUT.json desde {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Eliminar metadatos internos
    data.pop('_metadata', None)

    # Validar con Pydantic
    result = PipelineResultV1_1(**data)

    logger.info(f"✅ OUT.json cargado: {len(result.rubros)} rubros")

    return result


def _calculate_file_checksum(file_path: Path) -> str:
    """
    Calcula checksum MD5 de un archivo.

    Args:
        file_path: Ruta al archivo

    Returns:
        Checksum MD5 en hexadecimal
    """
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


def generate_summary_json(
    result: PipelineResultV1_1,
    output_path: Path
) -> ArtifactMetadata:
    """
    Genera JSON resumido (solo estadísticas, sin datos completos).

    Útil para dashboards o reportes rápidos.

    Args:
        result: Resultado del pipeline
        output_path: Ruta de salida

    Returns:
        ArtifactMetadata del archivo generado
    """
    summary = {
        'metadata': {
            'filename': result.metadata.filename,
            'total_pages': result.metadata.total_pages,
            'processing_date': result.metadata.processing_date.isoformat(),
        },
        'counts': {
            'rubros': len(result.rubros),
            'recursos': len(result.recursos),
            'warnings': len(result.warnings),
        },
        'conversion': {
            'success': result.conversion_result.success if result.conversion_result else False,
            'strategy': result.conversion_result.strategy_used if result.conversion_result else None,
        },
        'matching': {
            'total_matches': len(result.match_results),
            'success_rate': result.match_success_rate,
            'matched': len([m for m in result.match_results if m.status.value == 'MATCHED']),
            'ambiguous': len([m for m in result.match_results if m.status.value == 'AMBIGUOUS']),
            'no_match': len([m for m in result.match_results if m.status.value == 'NO_MATCH']),
        },
        'deduplication': result.dedup_stats,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    checksum = _calculate_file_checksum(output_path)

    artifact = ArtifactMetadata(
        artifact_type="OUT.json",
        file_path=str(output_path),
        size_bytes=output_path.stat().st_size,
        generated_at=datetime.now(),
        checksum=checksum
    )

    logger.info(f"✅ Summary JSON generado: {output_path}")

    return artifact
