# ⚡ QUICKSTART - Pipeline Extracción PDF

**Guía rápida de 5 minutos para empezar a usar el pipeline.**

---

## 🚀 Comandos Esenciales (Windows)

### 1. Setup Inicial (solo primera vez)

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

**IMPORTANTE:** Instalar Tesseract OCR antes:
- Descargar: https://github.com/UB-Mannheim/tesseract/wiki
- Instalar: `tesseract-ocr-w64-setup-5.3.3.exe`
- Verificar: `tesseract --version`

---

### 2. Uso Diario

```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Abrir VSCode
code .

# Abrir notebook: notebooks/pipeline_example.ipynb
# Ejecutar todas las celdas
```

---

## 📝 Código Mínimo (Copy-Paste)

### En Notebook:

```python
# Celda 1: Imports
from pathlib import Path
from src.pipeline import run_pipeline

# Celda 2: Configurar rutas
pdf_path = Path("data/input/mi_archivo.pdf")
output_path = Path("data/output/resultado.xlsx")

# Celda 3: Ejecutar pipeline
result = run_pipeline(pdf_path, output_path)

# Celda 4: Ver resultados
print(f"✅ Rubros: {len(result.rubros)}")
print(f"✅ Recursos: {len(result.recursos)}")
print(f"⚠️ Warnings: {len(result.warnings)}")
```

---

## 📂 Dónde Colocar los Archivos

```
ETL_ET/
├── data/
│   ├── input/     ← COLOCA AQUÍ TUS PDFs
│   └── output/    ← AQUÍ APARECERÁN LOS EXCEL
```

**Pasos:**
1. Copiar tu PDF a `data/input/`
2. Ejecutar el notebook
3. Revisar resultado en `data/output/[nombre]_resultado.xlsx`

---

## ✅ Verificar Instalación

```powershell
# Test rápido (debe pasar todos los checks)
pytest tests/test_smoke.py -v

# Verificar Tesseract
tesseract --version

# Verificar Python
python --version  # Debe ser 3.11+
```

---

## 🐛 Problemas Comunes

### Error: "tesseract is not installed"

**Solución:**
```python
# Editar: src/ocr/tesseract_ocr.py (línea 36)
# Descomentar y ajustar:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Error: "ModuleNotFoundError: No module named 'src'"

**Solución:**
```python
# Agregar al inicio del notebook:
import sys
sys.path.append('.')
```

### Jupyter kernel no aparece

**Solución:**
```powershell
pip install --force-reinstall ipykernel
python -m ipykernel install --user --name=.venv
```

---

## 📚 Documentación Completa

| Documento | Para qué sirve |
|-----------|----------------|
| [README.md](README.md) | Visión general del proyecto |
| [SETUP.md](SETUP.md) | Instalación detallada paso a paso |
| [SPEC.md](SPEC.md) | Especificación técnica completa |
| **QUICKSTART.md** | Esta guía rápida |

---

## 🎯 Flujo Típico de Uso

```
1. Colocar PDF en data/input/
   ↓
2. Abrir notebook (notebooks/pipeline_example.ipynb)
   ↓
3. Ejecutar todas las celdas (Ctrl+Shift+Enter)
   ↓
4. Revisar Excel en data/output/
   ↓
5. Analizar warnings (hoja "Warnings" del Excel)
   ↓
6. Iterar: ajustar reglas de parseo si es necesario
```

---

## 🔧 Personalización Rápida

### Cambiar idioma de OCR:

```python
result = run_pipeline(
    pdf_path,
    output_path,
    ocr_lang='eng'  # o 'spa+eng' para español+inglés
)
```

### Forzar OCR en todas las páginas:

```python
result = run_pipeline(
    pdf_path,
    output_path,
    force_ocr=True
)
```

### Procesar múltiples PDFs:

```python
from src.pipeline import process_multiple_pdfs

results = process_multiple_pdfs(
    input_dir=Path("data/input"),
    output_dir=Path("data/output")
)
```

---

## 📊 Interpretar Resultados

### Excel generado contiene 5 hojas:

| Hoja | Qué contiene |
|------|--------------|
| **Resumen** | Metadatos (páginas, tipo, totales) |
| **Rubros** | Tabla de rubros (código, descripción, unidad) |
| **Recursos** | Tabla de materiales/equipos |
| **Relaciones** | Join Rubros + Recursos (para análisis) |
| **Warnings** | Errores/advertencias (🔴 HIGH, 🟡 MEDIUM, ⚪ LOW) |

### Interpretar Warnings:

- **🔴 HIGH (Rojo):** Rubro incompleto, error crítico → Revisar manualmente
- **🟡 MEDIUM (Amarillo):** Unidad desconocida, recurso sin clasificar → Verificar
- **⚪ LOW (Gris):** Advertencias menores → Opcional revisar

---

## 💡 Tips

1. **PDFs de mala calidad:** Aumentar DPI del OCR:
   ```python
   result = run_pipeline(pdf_path, output_path, ocr_dpi=600)
   ```

2. **Agregar keywords personalizados:**
   - Editar: `src/parse/rubro_parser.py`
   - Agregar a `MATERIAL_INDICATORS` o `EQUIPO_INDICATORS`

3. **Ver logs detallados:**
   ```python
   from src.utils.logger import configure_logging
   configure_logging(level="DEBUG")
   ```

---

## 🆘 ¿Necesitas Ayuda?

1. Ver [SETUP.md](SETUP.md) para troubleshooting detallado
2. Ver [SPEC.md](SPEC.md) para documentación técnica
3. Revisar warnings en la hoja "Warnings" del Excel generado

---

**¡Listo para procesar tu primer PDF!** 🚀

```powershell
.\.venv\Scripts\Activate.ps1
code .
# Abrir notebooks/pipeline_example.ipynb
```
