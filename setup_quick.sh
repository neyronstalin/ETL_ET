#!/bin/bash
# Setup rápido para ETL_ET v1.0 (minimal)

set -e  # Exit on error

echo "🚀 ETL_ET - Setup Rápido"
echo "================================"
echo ""

# 1. Verificar Python
echo "✓ Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Instalar Python 3.11+"
    exit 1
fi
python3 --version

# 2. Crear entorno virtual
echo ""
echo "✓ Creando entorno virtual..."
if [ -d ".venv" ]; then
    echo "  → .venv ya existe, usando existente"
else
    python3 -m venv .venv
    echo "  → .venv creado"
fi

# 3. Activar entorno virtual
echo ""
echo "✓ Activando entorno virtual..."
source .venv/bin/activate

# 4. Actualizar pip
echo ""
echo "✓ Actualizando pip..."
pip install --upgrade pip setuptools wheel -q

# 5. Instalar dependencias (MINIMAL para empezar)
echo ""
echo "✓ Instalando dependencias (modo MINIMAL)..."
pip install -r requirements-minimal.txt -q

# 6. Verificar instalación
echo ""
echo "✓ Verificando instalación..."
python -c "import pydantic; print(f'  → Pydantic {pydantic.__version__} instalado')"
python -c "import pandas; print(f'  → Pandas instalado')"
python -c "import pdfplumber; print(f'  → PDFPlumber instalado')"

# 7. Verificar imports del proyecto
echo ""
echo "✓ Verificando imports del proyecto..."
python -c "from src.config.settings import get_settings; print('  → Settings OK')"
python -c "from src.utils.text_norm import normalize_rubro_code; print('  → Text normalization OK')"
python -c "from src.models.schemas import Rubro; print('  → Models OK')"

echo ""
echo "✅ Setup completado exitosamente!"
echo ""
echo "Próximos pasos:"
echo "  1. Activar entorno: source .venv/bin/activate"
echo "  2. En VSCode: Ctrl+Shift+P → 'Python: Select Interpreter'"
echo "  3. Seleccionar: .venv/bin/python"
echo "  4. Recargar notebook: Kernel → Restart Kernel"
echo ""
echo "Para modo ADVANCED (embeddings, FAISS):"
echo "  pip install -r requirements-full.txt"
echo ""
