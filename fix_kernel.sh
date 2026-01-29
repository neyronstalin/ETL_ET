#!/bin/bash
# Fix: Registrar kernel de Jupyter para VSCode

echo "🔧 Registrando kernel de Jupyter..."
source .venv/bin/activate

# Asegurar que ipykernel está instalado
pip install ipykernel -q

# Registrar el kernel
python -m ipykernel install --user --name etl_et_venv --display-name "ETL_ET (.venv)"

echo ""
echo "✅ Kernel registrado: ETL_ET (.venv)"
echo ""
echo "Ahora en VSCode:"
echo "  1. Recargar VSCode: Ctrl+Shift+P → 'Developer: Reload Window'"
echo "  2. Abrir notebook"
echo "  3. Click en selector de kernel (arriba a la derecha)"
echo "  4. Seleccionar: 'ETL_ET (.venv)'"
echo ""
