# 📦 GUÍA DE INSTALACIÓN v1.1

**Proyecto:** ETL_ET - Pipeline Extracción PDF
**Versiones:** Legacy (v1.0) | Advanced (v1.1)

---

## 🎯 Elige tu Instalación

### Opción 1: MINIMAL (Legacy v1.0)

**Para:** Usuarios que solo necesitan el pipeline básico sin matching semántico.

**Incluye:**
- ✅ PDF reader (pdfplumber + pypdf)
- ✅ OCR (Tesseract)
- ✅ Parser básico (regex + fuzzy)
- ✅ Export Excel (5 hojas)

**Tamaño:** ~500 MB (con venv)

**Instalación:**
```bash
pip install -r requirements-minimal.txt
```

---

### Opción 2: FULL (Advanced v1.1)

**Para:** Usuarios que quieren conversión estructurada + matching semántico.

**Incluye:**
- ✅ Todo de Minimal +
- ✅ Docling/Marker (conversión estructurada)
- ✅ Sentence Transformers (embeddings)
- ✅ FAISS (búsqueda vectorial)
- ✅ Matching WBS ↔ ET
- ✅ Reportes MD avanzados

**Tamaño:** ~3-4 GB (con venv + modelos)

**Instalación:**
```bash
# Paso 1: Instalar PyTorch CPU primero (Windows)
pip install torch==2.1.2+cpu --extra-index-url https://download.pytorch.org/whl/cpu

# Paso 2: Instalar resto de dependencias
pip install -r requirements-full.txt
```

---

## 🪟 INSTALACIÓN WINDOWS (PASO A PASO)

### Requisitos Previos

1. **Python 3.11+**
   - Descargar: https://www.python.org/downloads/
   - Durante instalación: ✅ Marcar "Add Python to PATH"
   - Verificar: `python --version`

2. **Tesseract OCR**
   - Descargar: https://github.com/UB-Mannheim/tesseract/wiki
   - Instalar: `tesseract-ocr-w64-setup-5.3.3.exe`
   - Agregar a PATH: `C:\Program Files\Tesseract-OCR`
   - Verificar: `tesseract --version`

3. **Visual Studio Build Tools** (solo para FULL mode)
   - Descargar: https://visualstudio.microsoft.com/downloads/
   - Instalar: "Build Tools for Visual Studio 2022"
   - Componentes: "Desktop development with C++"
   - **NOTA:** Solo necesario si vas a instalar Docling
   - Si no quieres instalar Build Tools, usa Marker en lugar de Docling

---

### Instalación MINIMAL (Windows)

```powershell
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 3. Actualizar pip
pip install --upgrade pip setuptools wheel

# 4. Instalar dependencias
pip install -r requirements-minimal.txt

# 5. Verificar instalación
pytest tests/test_smoke.py -v
```

**Tiempo estimado:** 5-10 minutos

---

### Instalación FULL (Windows)

```powershell
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 3. Actualizar pip
pip install --upgrade pip setuptools wheel

# 4. Instalar PyTorch CPU (PRIMERO)
pip install torch==2.1.2+cpu --extra-index-url https://download.pytorch.org/whl/cpu

# 5. Instalar dependencias restantes
pip install -r requirements-full.txt

# 6. Verificar instalación
pytest tests/test_smoke.py -v
```

**Tiempo estimado:** 15-30 minutos (primera vez descarga modelos)

---

## 🐧 INSTALACIÓN LINUX

### Minimal

```bash
# Instalar dependencias del sistema
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# Crear y activar venv
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependencias Python
pip install -r requirements-minimal.txt
```

### Full

```bash
# Instalar dependencias del sistema
sudo apt-get install tesseract-ocr tesseract-ocr-spa build-essential

# Crear y activar venv
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar PyTorch
pip install torch==2.1.2+cpu --extra-index-url https://download.pytorch.org/whl/cpu

# Instalar dependencias Python
pip install -r requirements-full.txt
```

---

## 🍎 INSTALACIÓN macOS

### Minimal

```bash
# Instalar Tesseract con Homebrew
brew install tesseract tesseract-lang

# Crear y activar venv
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependencias Python
pip install -r requirements-minimal.txt
```

### Full

```bash
# Instalar Tesseract
brew install tesseract tesseract-lang

# Crear y activar venv
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar PyTorch
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu

# Instalar dependencias Python
pip install -r requirements-full.txt
```

---

## 🔧 TROUBLESHOOTING

### Error: "Docling no se puede instalar"

**Solución 1:** Instalar Visual Studio Build Tools (Windows)
**Solución 2:** Comentar docling en requirements-full.txt y usar solo Marker:

```bash
# Editar requirements-full.txt, comentar:
# docling==1.16.2
# docling-core==1.8.0
# docling-ibm-models==1.2.0

# Reinstalar
pip install -r requirements-full.txt
```

El pipeline usará automáticamente Marker como fallback.

---

### Error: "torch no se instala correctamente"

**Problema:** torch intenta descargar versión CUDA por defecto (muy pesada)

**Solución:**
```bash
# Desinstalar torch existente
pip uninstall torch

# Instalar versión CPU explícitamente
pip install torch==2.1.2+cpu --extra-index-url https://download.pytorch.org/whl/cpu
```

---

### Error: "python-magic no funciona en Windows"

**Solución:**
```bash
# Desinstalar python-magic
pip uninstall python-magic

# Instalar versión Windows
pip install python-magic-bin==0.4.14
```

O simplemente comentar `python-magic` en requirements si no es crítico.

---

### Error: "sentence-transformers descarga muy lento"

**Problema:** Modelos se descargan desde Hugging Face (~500MB)

**Soluciones:**
1. Esperar (primera vez solo)
2. Descargar modelo manualmente:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
   # Se guarda en ~/.cache/torch/sentence_transformers/
   ```
3. Usar cache compartido (si tienes múltiples proyectos):
   ```bash
   export SENTENCE_TRANSFORMERS_HOME=/ruta/compartida
   ```

---

### Error: "Out of memory" al generar embeddings

**Problema:** Embeddings consumen mucha RAM

**Soluciones:**
1. Procesar por lotes más pequeños:
   ```python
   # En src/match/embedder.py
   BATCH_SIZE = 16  # Reducir de 32 a 16 o 8
   ```

2. Usar modelo más pequeño:
   ```python
   # Cambiar a modelo más ligero
   model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Solo inglés
   ```

3. Cerrar otros programas que consuman RAM

---

## ✅ VERIFICACIÓN POST-INSTALACIÓN

### Test Smoke (Minimal)

```bash
# Activar venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/macOS

# Ejecutar tests
pytest tests/test_smoke.py -v

# Debe mostrar:
# ✅ test_python_version PASSED
# ✅ test_imports_core PASSED
# ✅ test_imports_ingest PASSED
# ✅ test_imports_ocr PASSED
# ✅ test_imports_parse PASSED
# ✅ test_imports_export PASSED
```

### Test Smoke (Full)

```bash
# Además de los tests minimal:
pytest tests/test_smoke_v1.1.py -v

# Verifica:
# ✅ torch importable
# ✅ sentence-transformers importable
# ✅ faiss importable
# ✅ docling/marker importables (con fallback)
```

### Test Completo

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 TAMAÑOS DE INSTALACIÓN

| Componente | Minimal | Full |
|------------|---------|------|
| Python venv | ~200 MB | ~200 MB |
| Dependencias | ~300 MB | ~1.5 GB |
| Modelos (cache) | 0 | ~1-2 GB |
| **TOTAL** | **~500 MB** | **~3-4 GB** |

**Nota:** Modelos se descargan en primera ejecución y se cachean.

---

## 🚀 SIGUIENTE PASO

Después de instalar:

**Minimal:**
```bash
# Leer: QUICKSTART.md
# Ejecutar: notebooks/pipeline_example.ipynb (sección Legacy)
```

**Full:**
```bash
# Leer: PLAN_V1.1.md
# Ejecutar: notebooks/advanced_example.ipynb
```

---

## 💡 RECOMENDACIONES

1. **Primera vez:** Instalar Minimal, probar que funciona, luego upgrade a Full
2. **Desarrollo:** Usar Full en máquina local potente, Minimal en laptops
3. **Producción:** Minimal si solo necesitas OCR + Excel, Full si necesitas matching
4. **CI/CD:** Minimal (tests rápidos), Full (tests completos en server)

---

## 📞 SOPORTE

Si algo falla:
1. ✅ Leer TROUBLESHOOTING arriba
2. ✅ Verificar versión de Python: `python --version` (debe ser 3.11+)
3. ✅ Verificar Tesseract: `tesseract --version`
4. ✅ Revisar logs de instalación: `pip install -r requirements-full.txt -v`
5. ✅ Crear issue en GitHub con logs completos
