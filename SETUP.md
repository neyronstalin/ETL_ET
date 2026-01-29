# 🚀 Setup del Entorno - Pipeline Extracción PDF Técnicos

## Requisitos Previos
- **Python 3.11+** (recomendado: 3.11.8)
- **Visual Studio Code** con extensión Python y Jupyter
- **Git** (opcional, para control de versiones)
- **Tesseract OCR** (para PDFs escaneados)

---

## ✅ CHECKLIST DE INSTALACIÓN (Windows)

### PASO 1: Instalar Python 3.11+
```powershell
# Descargar desde https://www.python.org/downloads/
# Durante instalación, MARCAR "Add Python to PATH"
# Verificar instalación:
python --version
# Debe mostrar: Python 3.11.x
```

### PASO 2: Instalar Tesseract OCR (CRÍTICO para PDFs escaneados)
```powershell
# Descargar instalador desde:
# https://github.com/UB-Mannheim/tesseract/wiki
# Descargar: tesseract-ocr-w64-setup-5.3.3.exe (o versión más reciente)

# Ruta de instalación típica: C:\Program Files\Tesseract-OCR

# Agregar a PATH (Método 1: Durante instalación - marcar checkbox)
# Método 2: Manual
# 1. Abrir "Editar variables de entorno del sistema"
# 2. Variables de entorno → PATH → Nuevo
# 3. Agregar: C:\Program Files\Tesseract-OCR

# Verificar instalación:
tesseract --version
# Debe mostrar: tesseract 5.x.x

# Instalar idioma español (IMPORTANTE para PDFs en español)
# El instalador incluye español, verificar que exista:
# C:\Program Files\Tesseract-OCR\tessdata\spa.traineddata
```

### PASO 3: Crear Entorno Virtual
```powershell
# Navegar al directorio del proyecto
cd ETL_ET

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Si hay error de permisos, ejecutar como administrador:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activar entorno virtual (Windows CMD)
.\.venv\Scripts\activate.bat

# Verificar que el entorno esté activo (debe aparecer (.venv) al inicio del prompt)
```

### PASO 4: Instalar Dependencias
```powershell
# Con el entorno virtual activo:
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalaciones críticas:
python -c "import pytesseract; print('pytesseract OK')"
python -c "import pdfplumber; print('pdfplumber OK')"
python -c "import easyocr; print('easyocr OK')"
python -c "import pandas; print('pandas OK')"
```

### PASO 5: Configurar VSCode
```powershell
# 1. Abrir VSCode
code .

# 2. Instalar extensiones REQUERIDAS:
#    - Python (Microsoft)
#    - Jupyter (Microsoft)
#    - Pylance (Microsoft)

# 3. Seleccionar intérprete Python del entorno virtual:
#    - Ctrl+Shift+P → "Python: Select Interpreter"
#    - Seleccionar: .\.venv\Scripts\python.exe

# 4. Verificar que Jupyter esté configurado:
#    - Abrir notebooks/pipeline_example.ipynb
#    - Debe detectar automáticamente el kernel (.venv)
```

### PASO 6: Configurar Pytesseract (PATH)
```python
# Si Tesseract no está en PATH del sistema, configurar manualmente:
# Editar src/ocr/tesseract_ocr.py:

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### PASO 7: Crear Carpetas de Datos
```powershell
# Ya existen en la estructura, verificar:
mkdir -p data/input
mkdir -p data/output
mkdir -p data/cache

# Colocar PDFs de prueba en data/input/
```

### PASO 8: Ejecutar Test de Smoke
```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Ejecutar tests básicos
pytest tests/test_smoke.py -v

# Debe mostrar: PASSED
```

### PASO 9: Ejecutar Notebook de Ejemplo
```powershell
# Abrir VSCode
code .

# Abrir notebooks/pipeline_example.ipynb
# Ejecutar todas las celdas (Ctrl+Shift+Enter)
# Debe procesar un PDF de ejemplo y generar output en data/output/
```

---

## 📦 Estructura de Carpetas Esperada
```
ETL_ET/
├── .venv/                    # Entorno virtual (ignorado en git)
├── data/
│   ├── input/                # PDFs de entrada
│   ├── output/               # Excel generados
│   └── cache/                # Cache OCR (opcional)
├── src/
│   ├── __init__.py
│   ├── ingest/               # Lectura de PDFs
│   ├── ocr/                  # OCR (Tesseract/EasyOCR)
│   ├── parse/                # Parseo de rubros
│   ├── models/               # Pydantic models
│   ├── export/               # Generación Excel
│   └── utils/                # Logging, validación
├── notebooks/
│   └── pipeline_example.ipynb
├── tests/
│   └── test_*.py
├── requirements.txt
├── SETUP.md                  # Este archivo
├── SPEC.md                   # Especificación técnica
└── README.md
```

---

## 🔧 Troubleshooting Común

### Error: "tesseract is not installed or it's not in your PATH"
**Solución:**
```python
# En src/ocr/tesseract_ocr.py, agregar:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Error: "Jupyter kernel not found"
**Solución:**
```powershell
# Reinstalar ipykernel
pip install --force-reinstall ipykernel
python -m ipykernel install --user --name=.venv
```

### Error: "ModuleNotFoundError: No module named 'src'"
**Solución:**
```powershell
# Asegurarse de ejecutar desde la raíz del proyecto
cd ETL_ET
# O agregar al PYTHONPATH en el notebook:
import sys
sys.path.append('.')
```

### Error: EasyOCR descarga modelos muy lento
**Solución:**
```python
# Primera ejecución descarga modelos (~100MB)
# Usar cache: los modelos se guardan en ~/.EasyOCR/
# Alternativa: usar solo Tesseract para testing inicial
```

---

## 🎯 Verificación Final

Ejecutar este script de verificación:

```powershell
python -c "
import sys
print(f'Python: {sys.version}')

import pytesseract
print('pytesseract: OK')

import pdfplumber
print('pdfplumber: OK')

import pandas
print('pandas: OK')

import easyocr
print('easyocr: OK')

import pydantic
print('pydantic: OK')

print('\n✅ Entorno configurado correctamente!')
"
```

---

## 📚 Próximos Pasos

1. Leer [SPEC.md](SPEC.md) para entender la arquitectura
2. Revisar [notebooks/pipeline_example.ipynb](notebooks/pipeline_example.ipynb)
3. Colocar un PDF de prueba en `data/input/`
4. Ejecutar el notebook y revisar `data/output/resultado.xlsx`
5. Iterar sobre reglas de parseo en `src/parse/rubro_parser.py`

---

## 🆘 Soporte

Si algo falla, verificar:
1. ✅ Python 3.11+ instalado y en PATH
2. ✅ Tesseract instalado y en PATH (o configurado manualmente)
3. ✅ Entorno virtual activado (debe aparecer `(.venv)` en el prompt)
4. ✅ Todas las dependencias instaladas (`pip list | findstr pdfplumber`)
5. ✅ VSCode usando el intérprete correcto (`.venv/Scripts/python.exe`)
