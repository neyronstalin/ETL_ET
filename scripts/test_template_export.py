"""
Script de prueba para validar el export con template de 4 categorías.

Prueba con los 2 rubros de validación:
- 01.001.4.01: Con materiales y equipo
- 01.002.4.01: Sin materiales (No aplica), solo equipo
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etl_apu.export_template import export_apus_from_template, TemplateMapping

def create_test_data():
    """Crea datos de prueba para los 2 rubros de validación."""

    # Datos de los rubros
    rubros_data = [
        {
            "codigo": "01.001.4.01",
            "descripcion": "REPLANTEO Y TRAZADO",
            "unidad": "m2"
        },
        {
            "codigo": "01.002.4.01",
            "descripcion": "LIMPIEZA Y DESBROCE DE TERRENO",
            "unidad": "m2"
        }
    ]

    # Recursos por rubro
    recursos_por_rubro = {
        "01.001.4.01": [
            # MATERIALES
            {
                "nombre": "ESTACAS",
                "categoria": "MATERIALES",
                "unidad": "u",
                "cantidad": 10.0
            },
            {
                "nombre": "CLAVOS",
                "categoria": "MATERIALES",
                "unidad": "kg",
                "cantidad": 2.0
            },
            {
                "nombre": "PINTURA ESMALTE O SIMILAR",
                "categoria": "MATERIALES",
                "unidad": "gl",
                "cantidad": 1.0
            },
            # EQUIPO
            {
                "nombre": "HERRAMIENTA MENOR",
                "categoria": "EQUIPO",
                "cantidad": 1.0
            },
            {
                "nombre": "EQUIPO DE TOPOGRAFÍA",
                "categoria": "EQUIPO",
                "cantidad": 1.0
            }
        ],
        "01.002.4.01": [
            # Sin materiales (No aplica)
            # EQUIPO
            {
                "nombre": "HERRAMIENTA MENOR",
                "categoria": "EQUIPO",
                "cantidad": 1.0
            }
        ]
    }

    return rubros_data, recursos_por_rubro


def main():
    """Ejecuta la prueba de export con template."""

    print("=" * 70)
    print("TEST: Export APUs con Template de 4 Categorías")
    print("=" * 70)
    print()

    # Rutas
    template_path = Path("data/templates/Template_APUS.xlsx")
    output_path = Path("data/output/TEST_APUS_TEMPLATE.xlsx")

    # Verificar que existe el template
    if not template_path.exists():
        print(f"❌ ERROR: Template no encontrado en {template_path}")
        print("   Ejecuta primero: python scripts/create_template_apu.py")
        return 1

    print(f"✓ Template encontrado: {template_path}")

    # Crear datos de prueba
    rubros_data, recursos_por_rubro = create_test_data()

    print(f"✓ Datos de prueba creados:")
    print(f"  - Rubros: {len(rubros_data)}")
    print(f"  - Rubro 01.001.4.01: {len(recursos_por_rubro['01.001.4.01'])} recursos")
    print(f"  - Rubro 01.002.4.01: {len(recursos_por_rubro['01.002.4.01'])} recursos")
    print()

    # Ejecutar export
    print("Exportando...")
    try:
        stats = export_apus_from_template(
            template_path=template_path,
            output_path=output_path,
            rubros_data=rubros_data,
            recursos_por_rubro=recursos_por_rubro,
            mapping=None  # Usar mapeo por defecto
        )

        print()
        print("=" * 70)
        print("RESULTADOS DEL EXPORT")
        print("=" * 70)
        print(f"✓ Archivo generado: {output_path}")
        print(f"  - Hojas creadas: {stats.hojas_creadas}")
        print(f"  - Recursos exportados: {stats.recursos_exportados}")
        print(f"  - Filas insertadas: {stats.filas_insertadas}")
        print(f"  - Duplicados detectados: {stats.duplicados_detectados}")

        if stats.warnings:
            print()
            print("WARNINGS:")
            for warning in stats.warnings:
                print(f"  ⚠️  {warning}")

        print()
        print("=" * 70)
        print("VALIDACIÓN")
        print("=" * 70)

        # Validar resultados esperados
        validaciones = []

        # Validación 1: Número de hojas
        if stats.hojas_creadas == 2:
            validaciones.append("✓ Número de hojas creadas correcto (2)")
        else:
            validaciones.append(f"❌ Número de hojas incorrecto: {stats.hojas_creadas} (esperado: 2)")

        # Validación 2: Número de recursos
        if stats.recursos_exportados == 6:  # 5 de rubro 1 + 1 de rubro 2
            validaciones.append("✓ Número de recursos exportados correcto (6)")
        else:
            validaciones.append(f"❌ Número de recursos incorrecto: {stats.recursos_exportados} (esperado: 6)")

        # Validación 3: Sin duplicados
        if stats.duplicados_detectados == 0:
            validaciones.append("✓ Sin duplicados detectados")
        else:
            validaciones.append(f"⚠️  Duplicados detectados: {stats.duplicados_detectados}")

        for val in validaciones:
            print(val)

        print()
        print("=" * 70)
        print("TEST COMPLETADO")
        print("=" * 70)
        print(f"Revisa el archivo generado: {output_path}")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR DURANTE EL EXPORT")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
