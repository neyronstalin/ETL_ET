# Pipeline de Extracción de Especificaciones Técnicas desde PDF

**Versión:** 1.0
**Stack:** Python 3.11+ | Jupyter | Tesseract OCR | Pydantic | Pandas

---

## 📖 Descripción

Pipeline modular para extraer información estructurada desde archivos PDF de especificaciones técnicas (digitales o escaneados) y exportarla a Excel con múltiples hojas normalizadas.

**Capacidades:**
- ✅ Extracción de rubros (código, descripción, unidad)
- ✅ Desglose de materiales y equipos
- ✅ OCR automático para PDFs escaneados (Tesseract + EasyOCR)
- ✅ Clasificación de recursos (MATERIAL/EQUIPO)
- ✅ Export a Excel con 5 hojas: Resumen, Rubros, Recursos, Relaciones, Warnings
- ✅ Trazabilidad completa (páginas, snippets, confidence scores)
- ✅ Arquitectura modular (código en `src/`, notebooks separados)

---

## 🚀 Quick Start

### 1. Clonar repositorio (o crear desde cero)

```bash
cd ETL_ET
```

### 2. Crear entorno virtual

```powershell
# Crear venv
python -m venv .venv

# Activar (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activar (Windows CMD)
.\.venv\Scripts\activate.bat
```

### 3. Instalar dependencias

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Instalar Tesseract OCR

**Windows:**
1. Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Ejecutar instalador: `tesseract-ocr-w64-setup-5.3.3.exe`
3. Agregar a PATH: `C:\Program Files\Tesseract-OCR`
4. Verificar: `tesseract --version`

**Ver instrucciones detalladas en:** [SETUP.md](SETUP.md)

### 5. Ejecutar notebook de ejemplo

```powershell
# Abrir VSCode
code .

# Abrir notebooks/pipeline_example.ipynb
# Ejecutar todas las celdas (Ctrl+Shift+Enter)
```

---

## 📂 Estructura del Proyecto

```
ETL_ET/
├── data/
│   ├── input/                # PDFs de entrada
│   ├── output/               # Excel generados
│   └── cache/                # Cache de OCR
├── src/
│   ├── ingest/               # Lectura de PDFs
│   │   └── pdf_reader.py
│   ├── ocr/                  # OCR (Tesseract/EasyOCR)
│   │   └── tesseract_ocr.py
│   ├── parse/                # Parseo de rubros/recursos
│   │   └── rubro_parser.py
│   ├── models/               # Pydantic models
│   │   └── schemas.py
│   ├── export/               # Generación Excel
│   │   └── excel_exporter.py
│   ├── utils/                # Logging, helpers
│   │   └── logger.py
│   └── pipeline.py           # Orchestrator principal
├── notebooks/
│   └── pipeline_example.ipynb
├── tests/
│   └── test_smoke.py
├── requirements.txt
├── SETUP.md                  # Setup detallado
├── SPEC.md                   # Especificación técnica
└── README.md                 # Este archivo
```

---

## 🎯 Uso Básico

### Opción 1: Notebook Jupyter (Recomendado)

```python
from pathlib import Path
from src.pipeline import run_pipeline

# Configuración
pdf_path = Path("data/input/especificaciones.pdf")
output_path = Path("data/output/resultado.xlsx")

# Ejecutar pipeline
result = run_pipeline(pdf_path, output_path)

print(f"Rubros extraídos: {len(result.rubros)}")
print(f"Recursos extraídos: {len(result.recursos)}")
```

### Opción 2: CLI

```powershell
python src/pipeline.py data/input/especificaciones.pdf -o data/output/resultado.xlsx
```

### Opción 3: Batch (múltiples PDFs)

```python
from pathlib import Path
from src.pipeline import process_multiple_pdfs

results = process_multiple_pdfs(
    input_dir=Path("data/input"),
    output_dir=Path("data/output")
)
```

---

## 📊 Output (Excel)

El Excel generado contiene **5 hojas**:

| Hoja | Contenido |
|------|-----------|
| **Resumen** | Metadatos del documento (páginas, tipo, totales) |
| **Rubros** | Tabla de rubros (código, descripción, unidad, confidence) |
| **Recursos** | Tabla de recursos (tipo, nombre, unidad, cantidad) |
| **Relaciones** | Join de Rubros + Recursos (para análisis) |
| **Warnings** | Log de warnings/errores (con severidad y snippets) |

**Formato:**
- Encabezados con colores por hoja
- Warnings coloreados por severidad (🔴 HIGH, 🟡 MEDIUM, ⚪ LOW)
- Columnas auto-ajustadas
- Paneles congelados

---

## 🧪 Testing

```powershell
# Ejecutar todos los tests
pytest tests/ -v

# Solo tests unitarios (rápidos)
pytest tests/ -v -m unit

# Con coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [SETUP.md](SETUP.md) | Instrucciones detalladas de instalación y configuración |
| [SPEC.md](SPEC.md) | Especificación técnica completa (arquitectura, contratos, reglas) |
| [notebooks/pipeline_example.ipynb](notebooks/pipeline_example.ipynb) | Ejemplos de uso interactivos |

---

## 🔧 Configuración

Crear archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

**Variables clave:**

```env
# Ruta a Tesseract (si no está en PATH)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Idioma OCR
OCR_LANG=spa

# DPI para OCR (mayor = mejor calidad pero más lento)
OCR_DPI=300
```

---

## 🐛 Troubleshooting

### Error: "tesseract is not installed or it's not in your PATH"

**Solución:**

```python
# En src/ocr/tesseract_ocr.py, descomentar y ajustar:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Error: "ModuleNotFoundError: No module named 'src'"

**Solución:**

```python
# En el notebook, agregar al inicio:
import sys
sys.path.append('.')
```

### OCR muy lento

**Soluciones:**
- Reducir DPI: `ocr_dpi=200` (default: 300)
- Procesar solo páginas necesarias
- Usar cache (ya habilitado por defecto)

---

## 🛠️ Stack Tecnológico

| Componente | Librería | Justificación |
|------------|----------|---------------|
| **PDF Digital** | `pdfplumber` | Mejor extracción de texto con layout awareness |
| **OCR** | `pytesseract`, `easyocr` | Tesseract (robusto) + EasyOCR (fallback) |
| **Validación** | `pydantic` | Contratos de datos y validación automática |
| **Export** | `pandas`, `openpyxl` | Excel con múltiples hojas y formato |
| **Parsing** | `regex`, `rapidfuzz` | Regex avanzado + fuzzy matching |
| **Logging** | `structlog` | Logging estructurado con contexto |
| **Testing** | `pytest` | Framework de testing estándar |

---

## 📈 Roadmap

### v1.1 (Corto plazo)
- [ ] Tests de integración con PDFs reales
- [ ] Cache persistente para OCR
- [ ] Parseo de cantidades (regex números)
- [ ] Detección de tablas con `pdfplumber`

### v1.2 (Mediano plazo)
- [ ] Layout-aware parsing (columnas, headers)
- [ ] Clasificación con ML (embeddings)
- [ ] Paralelización de OCR
- [ ] Interfaz web (Streamlit)

### v2.0 (Largo plazo)
- [ ] Integración con LLMs (GPT-4, Claude)
- [ ] Base de datos (PostgreSQL)
- [ ] API REST
- [ ] Dashboard de analytics

---

## 👥 Contribuir

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

**Convenciones:**
- Código y comentarios en español
- PEP 8, formateado con `black`
- Type hints obligatorios
- Tests para nuevas funcionalidades

---

## 📝 Licencia

MIT License - Ver [LICENSE](LICENSE) para detalles.

---

## 📧 Contacto

**Autor:** Senior Data/ML Engineer
**Proyecto:** Pipeline Extracción PDF Especificaciones Técnicas
**Fecha:** 2026-01-28

---

## 🙏 Agradecimientos

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF parsing
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

**¿Listo para empezar?** 🚀

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Colocar PDF en data/input/
cp mi_especificacion.pdf data/input/

# 3. Abrir notebook
jupyter notebook notebooks/pipeline_example.ipynb
```
