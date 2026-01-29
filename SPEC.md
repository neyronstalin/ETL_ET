# ESPECIFICACIÓN TÉCNICA - Pipeline Extracción PDF Especificaciones Técnicas

**Versión:** 1.1 (Advanced)
**Fecha:** 2026-01-29
**Autor:** Senior Data/ML Engineer

---

## 📋 Tabla de Contenidos

### Secciones v1.0 (Legacy)
1. [Objetivo y Alcance](#1-objetivo-y-alcance)
2. [Entradas Soportadas](#2-entradas-soportadas)
3. [Salidas (Estructura Excel)](#3-salidas-estructura-excel)
4. [Modelos de Datos](#4-modelos-de-datos)
5. [Contratos de Funciones](#5-contratos-de-funciones)
6. [Reglas de Parseo](#6-reglas-de-parseo)
7. [Estrategia de Pruebas](#7-estrategia-de-pruebas)
8. [Performance y Optimización](#8-performance-y-optimización)
9. [Roadmap Futuro](#9-roadmap-futuro)

### Secciones v1.1 (Advanced) 🆕
10. [Conversión Avanzada](#10-conversión-avanzada)
11. [Matching Semántico WBS↔ET](#11-matching-semántico-wbset)
12. [Deduplicación y Conflictos](#12-deduplicación-y-conflictos)
13. [Artifacts v1.1](#13-artifacts-v11)
14. [Excel Template Mode](#14-excel-template-mode)

---

## 1. Objetivo y Alcance

### 1.1 Objetivo

Construir una **pipeline modular y reproducible** para extraer información estructurada desde archivos PDF de especificaciones técnicas (digitales o escaneados) y exportarla a un archivo Excel con múltiples hojas normalizadas.

### 1.2 Alcance

**Incluye:**
- ✅ Lectura de PDFs digitales (con texto extraíble)
- ✅ OCR de PDFs escaneados (imagen)
- ✅ Detección automática de tipo de PDF (digital/escaneado/mixto)
- ✅ Extracción de:
  - Código de rubro (ej: 01.01.01)
  - Descripción del rubro
  - Unidad de medida (m, m², m³, kg, u, etc.)
  - Desglose de materiales y equipos
  - Cantidades (cuando estén disponibles)
- ✅ Clasificación de recursos: MATERIAL vs EQUIPO
- ✅ Generación de warnings para datos incompletos o ambiguos
- ✅ Export a Excel con 5 hojas: Resumen, Rubros, Recursos, Relaciones, Warnings
- ✅ Trazabilidad completa: página de origen, snippets, confidence scores
- ✅ Arquitectura modular (código en `src/`, notebooks separados)
- ✅ Soporte para español (OCR con idioma 'spa')

**No incluye (fuera de alcance v1.0):**
- ❌ Interpretación semántica avanzada (NLP/LLMs)
- ❌ Layout-aware parsing (detección de tablas complejas)
- ❌ Cálculo de precios o totales
- ❌ Integración con bases de datos
- ❌ API web o servicio deployado

---

## 2. Entradas Soportadas

### 2.1 Formatos de Entrada

**Tipo:** Archivos PDF
**Ubicación:** `data/input/`

**Variantes soportadas:**
1. **PDF Digital:** PDF con texto real extraíble (generado desde Word, LibreOffice, etc.)
2. **PDF Escaneado:** PDF que contiene imágenes de páginas escaneadas (requiere OCR)
3. **PDF Mixto:** Algunas páginas digitales, otras escaneadas

### 2.2 Estructura Esperada de los PDFs

Los PDFs de especificaciones técnicas suelen seguir este patrón semi-estructurado:

```
[CÓDIGO] [DESCRIPCIÓN DEL RUBRO]
Unidad: [UNIDAD]

[Método constructivo opcional]

MATERIALES:
- Material 1
- Material 2

EQUIPOS:
- Equipo 1
- Equipo 2
```

**Ejemplo real:**
```
01.01.01 EXCAVACIÓN MANUAL EN TERRENO NATURAL
Unidad: m³

Se realizará excavación manual a la profundidad especificada...

MATERIALES:
- Agua para compactación (lt)
- Arena gruesa (m³)

EQUIPOS:
- Herramientas manuales (%)
- Carretilla (u)
```

### 2.3 Supuestos y Limitaciones

**Supuestos:**
- Los códigos de rubro siguen formato: `XX.XX.XX` (ej: 01.01.01, 2.3.1, 10-05-02)
- Las unidades aparecen cerca del encabezado del rubro
- Los recursos están listados con viñetas (-) o numeración
- El idioma principal es español

**Limitaciones conocidas:**
- Si un PDF está muy corrupto o es ilegible, el OCR puede fallar
- Tablas complejas o layouts multi-columna pueden no parsearse correctamente
- Códigos de rubro no estándar pueden no detectarse
- La clasificación MATERIAL/EQUIPO es heurística (puede requerir ajuste)

---

## 3. Salidas (Estructura Excel)

### 3.1 Ubicación

**Default:** `data/output/[nombre_pdf]_resultado.xlsx`

### 3.2 Estructura del Excel

El archivo Excel contiene **5 hojas**:

#### Hoja 1: **Resumen**

Metadatos del documento procesado.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| Archivo | str | Nombre del PDF procesado |
| Total Páginas | int | Número total de páginas |
| Tipo de Documento | str | DIGITAL / ESCANEADO / MIXTO |
| Páginas con OCR | str | Lista de páginas que requirieron OCR |
| Total Rubros | int | Rubros extraídos |
| Total Recursos | int | Recursos extraídos |
| Total Warnings | int | Warnings generados |
| Fecha de Procesamiento | datetime | Timestamp de ejecución |

#### Hoja 2: **Rubros**

Tabla de rubros extraídos.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| rubro_id | str | ID único (ej: RUB_01_01_01_P1) |
| codigo | str | Código del rubro (ej: 01.01.01) |
| descripcion | str | Descripción completa |
| unidad | str | Unidad normalizada (m, m², m³, kg, u) |
| pages | str | Páginas de origen (separadas por coma) |
| confidence | float | Score de confianza (0.0 - 1.0) |
| metodo_constructivo | str | Método (si existe) |

#### Hoja 3: **Recursos**

Tabla de recursos (materiales/equipos).

| Columna | Tipo | Descripción |
|---------|------|-------------|
| recurso_id | str | ID único (ej: RUB_01_01_01_P1_REC001) |
| rubro_id | str | ID del rubro padre (FK) |
| tipo | enum | MATERIAL / EQUIPO / MANO_DE_OBRA / DESCONOCIDO |
| nombre | str | Descripción del recurso |
| unidad | str | Unidad del recurso (puede diferir del rubro) |
| cantidad | float | Cantidad (si está disponible) |
| confidence | float | Score de confianza (0.0 - 1.0) |

#### Hoja 4: **Relaciones**

Tabla desnormalizada para análisis (JOIN de Rubros + Recursos).

| Columna | Tipo | Descripción |
|---------|------|-------------|
| rubro_codigo | str | Código del rubro |
| rubro_descripcion | str | Descripción del rubro |
| recurso_tipo | enum | Tipo de recurso |
| recurso_nombre | str | Nombre del recurso |
| cantidad | float | Cantidad |
| unidad | str | Unidad |

#### Hoja 5: **Warnings**

Log de warnings y errores durante el parseo.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| warning_id | str | ID único del warning |
| rubro_id | str | Rubro asociado (si aplica) |
| page | int | Número de página |
| kind | enum | Tipo de warning (ver WarningKind) |
| severity | enum | LOW / MEDIUM / HIGH |
| message | str | Mensaje descriptivo |
| snippet | str | Fragmento de texto (máx 100 chars) |

**Colores por severidad:**
- 🔴 **HIGH:** Rojo claro (FFCCCC) - Rubro incompleto, error crítico
- 🟡 **MEDIUM:** Amarillo (FFFFCC) - Unidad desconocida, recurso sin clasificar
- ⚪ **LOW:** Gris (E7E6E6) - Advertencias menores

---

## 4. Modelos de Datos

### 4.1 Modelo Rubro (Pydantic)

```python
class Rubro(BaseModel):
    rubro_id: str                    # ID único
    codigo: str                      # Código (ej: "01.01.01")
    descripcion: str                 # Descripción completa
    unidad: str                      # Unidad normalizada
    source_pages: List[int]          # Páginas de origen
    confidence: float                # 0.0 - 1.0
    metodo_constructivo: Optional[str] = None
    created_at: datetime
```

**Validaciones:**
- `codigo`: No vacío, formato validado
- `unidad`: Normalizada automáticamente (m2 → m²)
- `confidence`: Rango [0.0, 1.0]

**Generación de ID:**
```python
rubro_id = f"RUB_{codigo.replace('.', '_')}_P{page_number}"
# Ejemplo: "RUB_01_01_01_P1"
```

### 4.2 Modelo Recurso (Pydantic)

```python
class TipoRecurso(str, Enum):
    MATERIAL = "MATERIAL"
    EQUIPO = "EQUIPO"
    MANO_DE_OBRA = "MANO_DE_OBRA"
    DESCONOCIDO = "DESCONOCIDO"

class Recurso(BaseModel):
    recurso_id: str                  # ID único
    rubro_id: str                    # FK a Rubro
    tipo: TipoRecurso                # Clasificación
    nombre: str                      # Descripción
    unidad: Optional[str] = None
    cantidad: Optional[float] = None
    confidence: float = 1.0
    source_snippet: Optional[str] = None
    created_at: datetime
```

**Generación de ID:**
```python
recurso_id = f"{rubro_id}_REC{index:03d}"
# Ejemplo: "RUB_01_01_01_P1_REC001"
```

### 4.3 Modelo ParseWarning (Pydantic)

```python
class WarningKind(str, Enum):
    RUBRO_INCOMPLETE = "RUBRO_INCOMPLETE"
    UNIDAD_DESCONOCIDA = "UNIDAD_DESCONOCIDA"
    RECURSO_SIN_TIPO = "RECURSO_SIN_TIPO"
    OCR_BAJA_CONFIANZA = "OCR_BAJA_CONFIANZA"
    FORMATO_INVALIDO = "FORMATO_INVALIDO"
    PARSING_ERROR = "PARSING_ERROR"

class ParseWarning(BaseModel):
    warning_id: str
    rubro_id: Optional[str] = None
    page: Optional[int] = None
    kind: WarningKind
    message: str
    snippet: Optional[str] = None
    severity: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    created_at: datetime
```

### 4.4 Modelo PipelineResult (Output Final)

```python
class PipelineResult(BaseModel):
    metadata: DocumentMetadata
    rubros: List[Rubro]
    recursos: List[Recurso]
    warnings: List[ParseWarning]

    @property
    def success_rate(self) -> float:
        """Tasa de éxito: rubros sin warnings / total rubros"""
        ...
```

---

## 5. Contratos de Funciones

### 5.1 Módulo Ingest

#### `ingest_pdf(pdf_path: Path, force_ocr: bool = False) -> Tuple[Dict[int, str], DocumentMetadata]`

**Propósito:** Leer PDF y extraer texto de páginas digitales.

**Input:**
- `pdf_path`: Ruta al PDF (debe existir)
- `force_ocr`: Si True, fuerza OCR en todas las páginas

**Output:**
- `Dict[int, str]`: Diccionario con texto por página (1-indexed)
- `DocumentMetadata`: Metadatos del documento

**Errores:**
- `FileNotFoundError`: PDF no existe
- `ValueError`: PDF corrupto

**Ejemplo:**
```python
pages_text, metadata = ingest_pdf(Path("data/input/spec.pdf"))
print(f"Tipo: {metadata.tipo_documento}")
print(f"Páginas con OCR: {metadata.pages_with_ocr}")
```

---

### 5.2 Módulo OCR

#### `ocr_pdf_page(pdf_path: Path, page_number: int, lang: str = 'spa') -> Tuple[str, float]`

**Propósito:** Aplicar OCR a una página de PDF.

**Input:**
- `pdf_path`: Ruta al PDF
- `page_number`: Número de página (1-indexed)
- `lang`: Idioma OCR ('spa', 'eng', 'spa+eng')

**Output:**
- `str`: Texto extraído
- `float`: Confidence score (0-100)

**Errores:**
- `RuntimeError`: Tesseract no instalado
- `ValueError`: Número de página inválido

**Ejemplo:**
```python
text, conf = ocr_pdf_page(Path("data/input/scan.pdf"), page_number=1)
print(f"Confianza: {conf:.1f}%")
```

---

### 5.3 Módulo Parse

#### `parsear_texto_completo(texto: str, page_number: int) -> Tuple[List[Rubro], List[Recurso], List[ParseWarning]]`

**Propósito:** Parsear texto completo de una página para extraer rubros y recursos.

**Input:**
- `texto`: Texto de la página (digital o OCR)
- `page_number`: Número de página (para trazabilidad)

**Output:**
- `List[Rubro]`: Rubros encontrados
- `List[Recurso]`: Recursos encontrados
- `List[ParseWarning]`: Warnings generados

**Errores:**
- Nunca lanza excepciones; genera warnings en caso de fallos

**Ejemplo:**
```python
rubros, recursos, warnings = parsear_texto_completo(text, page_number=1)
print(f"Encontrados {len(rubros)} rubros")
```

---

### 5.4 Módulo Export

#### `export_to_excel(result: PipelineResult, output_path: Path, apply_formatting: bool = True) -> None`

**Propósito:** Exportar resultados a Excel con 5 hojas.

**Input:**
- `result`: PipelineResult con datos
- `output_path`: Ruta donde guardar el Excel
- `apply_formatting`: Si True, aplica colores y formato

**Output:**
- None (escribe archivo en disco)

**Errores:**
- `IOError`: No se puede escribir archivo
- `ValueError`: Datos inválidos

**Ejemplo:**
```python
export_to_excel(result, Path("data/output/resultado.xlsx"))
```

---

## 6. Reglas de Parseo

### 6.1 Detección de Código de Rubro

**Patrón regex:**
```python
PATRON_CODIGO = r'(\d{1,3}[\.\-]\d{1,3}[\.\-]\d{1,3})'
```

**Formatos válidos:**
- `01.01.01` ✅
- `1.1.1` ✅
- `10-05-02` ✅
- `001.002.003` ✅

**Formatos inválidos:**
- `1.1` ❌ (solo 2 niveles)
- `A.01.01` ❌ (contiene letra)

### 6.2 Normalización de Unidades

| Variantes detectadas | Unidad normalizada |
|---------------------|-------------------|
| m, mt, mts, metro | **m** |
| m2, m², m^2, metro cuadrado | **m²** |
| m3, m³, m^3, metro cubico | **m³** |
| kg, kilo, kilogramo | **kg** |
| u, un, und, unid, unidad, pza, pieza | **u** |
| lt, l, litro | **lt** |
| ton, t, tonelada | **ton** |

### 6.3 Segmentación de Rubros

**Estrategia:** Buscar patrones de código como delimitadores.

```python
def segmentar_en_rubros(texto_completo: str) -> List[str]:
    # Busca todos los códigos (XX.XX.XX)
    # Segmenta texto entre código N y código N+1
    # Retorna lista de bloques
```

**Ejemplo:**
```
Entrada:
"01.01.01 RUBRO 1\nDetalle...\n02.01.01 RUBRO 2\nDetalle..."

Salida:
[
  "01.01.01 RUBRO 1\nDetalle...",
  "02.01.01 RUBRO 2\nDetalle..."
]
```

### 6.4 Clasificación MATERIAL vs EQUIPO

**Estrategia de clasificación (orden de precedencia):**

1. **Búsqueda de palabras clave exactas:**
   ```python
   MATERIAL_INDICATORS = [
       'cemento', 'arena', 'piedra', 'acero', 'clavo',
       'alambre', 'pintura', 'tubo', 'cable', 'varilla'
   ]

   EQUIPO_INDICATORS = [
       'mezcladora', 'vibrador', 'camion', 'retroexcavadora',
       'compresor', 'martillo', 'andamio', 'encofrado'
   ]
   ```

2. **Fuzzy matching (similitud > 70%):**
   - Usa RapidFuzz para comparar nombre del recurso con keywords

3. **Fallback:**
   - Si no se puede clasificar → `TipoRecurso.DESCONOCIDO`
   - Genera warning con severity=LOW

**Ejemplos:**
```
"Cemento Portland tipo I" → MATERIAL (match exacto "cemento")
"Mezcladora de concreto 1 saco" → EQUIPO (match exacto "mezcladora")
"Herramientas manuales" → EQUIPO (fuzzy match "herramientas")
"Insumo especial XYZ" → DESCONOCIDO (no match)
```

### 6.5 Extracción de Recursos

**Patrones de detección:**
- Líneas que comienzan con: `-`, `*`, `•`, `1)`, `a)`
- Ubicadas después de secciones "MATERIALES:" o "EQUIPOS:"

**Regex para items de lista:**
```python
r'^[\-\*\•\d\)\.]+\s*'
```

**Ejemplo:**
```
MATERIALES:
- Cemento Portland (kg)
- Arena gruesa (m³)
* Agua (lt)

→ 3 recursos detectados
```

### 6.6 Manejo de "Unknowns"

**Casos que generan warnings:**

| Caso | Warning Kind | Severity | Acción |
|------|-------------|----------|--------|
| Código no detectado | RUBRO_INCOMPLETE | HIGH | No crear rubro |
| Descripción vacía | RUBRO_INCOMPLETE | MEDIUM | Usar "SIN DESCRIPCIÓN" |
| Unidad no encontrada | UNIDAD_DESCONOCIDA | MEDIUM | Usar "SIN UNIDAD" |
| Recurso sin clasificar | RECURSO_SIN_TIPO | LOW | Tipo = DESCONOCIDO |
| OCR confidence < 50% | OCR_BAJA_CONFIANZA | MEDIUM | Reducir confidence del rubro |

---

## 7. Estrategia de Pruebas

### 7.1 Tests Unitarios (pytest)

**Ubicación:** `tests/`

#### Test 1: `test_normalizar_unidad`

```python
def test_normalizar_unidad():
    assert normalizar_unidad("m2") == "m²"
    assert normalizar_unidad("metro cuadrado") == "m²"
    assert normalizar_unidad("und") == "u"
    assert normalizar_unidad("kg.") == "kg"
```

#### Test 2: `test_extraer_codigo_rubro`

```python
def test_extraer_codigo_rubro():
    assert extraer_codigo_rubro("01.01.01 EXCAVACIÓN") == "01.01.01"
    assert extraer_codigo_rubro("10-05-02 RUBRO") == "10-05-02"
    assert extraer_codigo_rubro("Sin código") is None
```

#### Test 3: `test_clasificar_tipo_recurso`

```python
def test_clasificar_tipo_recurso():
    assert clasificar_tipo_recurso("Cemento Portland") == TipoRecurso.MATERIAL
    assert clasificar_tipo_recurso("Mezcladora 1 saco") == TipoRecurso.EQUIPO
    assert clasificar_tipo_recurso("Insumo XYZ") == TipoRecurso.DESCONOCIDO
```

#### Test 4: `test_segmentar_en_rubros`

```python
def test_segmentar_en_rubros():
    texto = "01.01 RUBRO 1\nDetalle...\n02.01 RUBRO 2\nDetalle..."
    bloques = segmentar_en_rubros(texto)
    assert len(bloques) == 2
    assert "01.01" in bloques[0]
    assert "02.01" in bloques[1]
```

#### Test 5: `test_pipeline_end_to_end`

```python
def test_pipeline_end_to_end(tmp_path):
    # Crear PDF de prueba
    pdf_path = tmp_path / "test.pdf"
    # ... generar PDF con contenido de prueba ...

    output_path = tmp_path / "resultado.xlsx"
    result = run_pipeline(pdf_path, output_path)

    assert result.metadata.total_pages > 0
    assert len(result.rubros) > 0
    assert output_path.exists()
```

### 7.2 Ejecución de Tests

```bash
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar con coverage
pytest tests/ --cov=src --cov-report=html

# Ejecutar un test específico
pytest tests/test_parse.py::test_normalizar_unidad -v
```

### 7.3 Tests de Integración

**TODO (v1.1):**
- Test con PDFs reales de ejemplo
- Test de performance (procesamiento de 100 páginas)
- Test de resiliencia (PDFs corruptos)

---

## 8. Performance y Optimización

### 8.1 Caching de OCR

**Estrategia:** Usar `joblib` para cachear resultados de OCR por página.

```python
from joblib import Memory

memory = Memory("data/cache", verbose=0)

@memory.cache
def ocr_pdf_page_cached(pdf_path, page_number, lang):
    return ocr_pdf_page(pdf_path, page_number, lang)
```

**Beneficio:** Si se re-procesa el mismo PDF, las páginas OCR ya procesadas se reutilizan.

### 8.2 Paralelización

**TODO (v1.1):** Procesar múltiples páginas en paralelo usando `multiprocessing`.

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_page, pages)
```

**Limitación actual:** El OCR es el cuello de botella (CPU-bound).

### 8.3 Benchmarks Esperados

| Tipo de PDF | Páginas | Tiempo estimado (1 core) |
|-------------|---------|-------------------------|
| Digital | 50 | ~5 segundos |
| Escaneado (300 DPI) | 50 | ~2-3 minutos |
| Escaneado (600 DPI) | 50 | ~5-8 minutos |

**Nota:** OCR es el proceso más lento (2-5 seg/página).

### 8.4 Memoria

**Consumo estimado:**
- PDF digital: ~10 MB por 100 páginas
- OCR: ~50-100 MB por página (durante conversión PDF→Imagen)

**Recomendación:** Procesar PDFs de <200 páginas. Para PDFs grandes, implementar procesamiento por lotes.

---

## 9. Roadmap Futuro

### 9.1 Mejoras Corto Plazo (v1.1)

- [ ] **Tests de integración** con PDFs reales de ejemplo
- [ ] **Cache persistente** para OCR (evitar re-procesar)
- [ ] **Parseo de cantidades** (extraer números con regex)
- [ ] **Detección de tablas** usando `pdfplumber.extract_tables()`
- [ ] **Progress bar** en notebook con `tqdm`
- [ ] **Configuración desde .env** (rutas, thresholds, etc.)

### 9.2 Mejoras Mediano Plazo (v1.2)

- [ ] **Layout-aware parsing** (detectar columnas, headers)
- [ ] **Clasificación con ML** (MATERIAL/EQUIPO usando embeddings)
- [ ] **Named Entity Recognition** para cantidades y unidades
- [ ] **Paralelización** de OCR con `multiprocessing`
- [ ] **Interfaz web** (Streamlit) para upload de PDFs
- [ ] **Export a múltiples formatos** (CSV, JSON, SQL)

### 9.3 Mejoras Largo Plazo (v2.0)

- [ ] **Integración con LLMs** (GPT-4, Claude) para clasificación semántica
- [ ] **Fine-tuning de OCR** con modelos custom (EasyOCR)
- [ ] **Base de datos** (PostgreSQL) para almacenar histórico
- [ ] **API REST** para integración con otros sistemas
- [ ] **Dashboard** de analytics (Tableau, PowerBI)
- [ ] **CI/CD** con GitHub Actions

---

## 10. Conversión Avanzada

### 10.1 Objetivo

Convertir PDFs a formatos estructurados (Markdown + JSON) usando herramientas especializadas antes del parseo tradicional. Esto mejora la precisión de extracción, especialmente en documentos con layouts complejos.

### 10.2 Estrategias Disponibles

**Implementado en:** `src/convert/`

#### 10.2.1 Docling (IBM)
**Módulo:** `docling_converter.py`

**Características:**
- ✅ Convierte PDF → Markdown + JSON estructurado
- ✅ Detecta outline (jerarquía de secciones)
- ✅ Extrae tablas preservando estructura
- ✅ Alta precisión en layouts complejos
- ⚠️ Más lento (~5-10 seg/página)

**Uso:**
```python
from src.convert import DoclingConverter

converter = DoclingConverter()
result = converter.convert(pdf_path)  # ConversionResult

print(result.markdown_content)  # Markdown
print(result.json_content)      # Dict con outline, tablas, etc.
```

**Dependencias:**
```bash
pip install docling==1.16.2
```

#### 10.2.2 Marker
**Módulo:** `marker_converter.py`

**Características:**
- ✅ Conversión rápida (~2-3 seg/página)
- ✅ Buena detección de tablas
- ✅ Soporta OCR integrado
- ⚠️ Menos preciso que Docling en layouts complejos

**Uso:**
```python
from src.convert import MarkerConverter

converter = MarkerConverter()
result = converter.convert(pdf_path)
```

**Dependencias:**
```bash
pip install marker-pdf==0.2.17
```

#### 10.2.3 PyMuPDF4LLM
**Módulo:** `pymupdf_converter.py`

**Características:**
- ✅ Muy rápido (~1 seg/página)
- ✅ Simple, ligero
- ⚠️ No detecta outline ni tablas complejas
- ✅ Bueno como fallback

**Uso:**
```python
from src.convert import PyMuPDFConverter

converter = PyMuPDFConverter()
result = converter.convert(pdf_path)
```

**Dependencias:**
```bash
pip install pymupdf4llm==0.0.10
```

### 10.3 Cascada de Conversión (Auto)

**Módulo:** `converter_router.py`

Si se selecciona `strategy='auto'`, se intenta en orden:

1. **Docling** → Si falla o timeout → 2
2. **Marker** → Si falla o timeout → 3
3. **PyMuPDF4LLM** → Fallback final

**Configuración:**
```python
# settings.py
CONVERSION_STRATEGY = "auto"  # docling | marker | pymupdf | auto
CONVERSION_TIMEOUT_S = 300    # 5 minutos max
```

**Uso:**
```python
from src.convert import ConverterRouter

router = ConverterRouter(strategy="auto")
result = router.convert(pdf_path)

print(f"Estrategia usada: {result.strategy_used}")
print(f"Fallback chain: {result.fallback_chain}")
```

### 10.4 Output: ConversionResult

**Schema:** `src/models/schemas.py`

```python
class ConversionResult(BaseModel):
    success: bool
    strategy_used: ConversionStrategy  # docling | marker | pymupdf
    markdown_content: str              # Contenido en MD
    json_content: dict                 # Outline, tablas, metadata
    metadata: dict                     # Info de conversión
    fallback_chain: List[str]          # Estrategias intentadas
    processing_time_s: float           # Tiempo de procesamiento
    warnings: List[str]                # Warnings generados
```

### 10.5 Artifacts Generados

Cuando se usa conversión avanzada, se generan estos archivos en `data/output/artifacts/`:

- **ET.md**: Markdown completo del PDF
- **ET.json**: JSON estructurado con outline, tablas, metadata

**Ejemplo ET.json:**
```json
{
  "outline": [
    {"level": 1, "title": "01.01 OBRAS PRELIMINARES", "page": 1},
    {"level": 2, "title": "01.01.01 EXCAVACIÓN MANUAL", "page": 1}
  ],
  "tables": [
    {"page": 3, "data": [[...]], "bbox": [x1, y1, x2, y2]}
  ],
  "metadata": {
    "total_pages": 50,
    "processing_time_s": 25.3
  }
}
```

---

## 11. Matching Semántico WBS↔ET

### 11.1 Objetivo

Matchear rubros extraídos del PDF (ET) contra una base de referencia (WBS) usando **embeddings semánticos** + fuzzy matching. Esto permite:
- ✅ Normalizar códigos (mapear códigos locales → WBS estándar)
- ✅ Detectar rubros similares aunque la descripción sea diferente
- ✅ Identificar ambigüedades y conflictos
- ✅ Generar evidencia de matching para auditoría

### 11.2 Arquitectura

**Implementado en:** `src/match/`

#### 11.2.1 Componentes

1. **Embedder** (`embedder.py`)
   - Genera vectores densos usando `sentence-transformers`
   - Modelo: `paraphrase-multilingual-MiniLM-L12-v2` (soporta español)
   - Caché de embeddings para performance

2. **Scoring** (`scoring.py`)
   - Calcula scores combinados: semantic (70%) + fuzzy (20%) + code (5%) + unit (5%)
   - Fuzzy matching con `rapidfuzz`
   - Code/unit similarity con normalización

3. **Matcher** (`matcher.py`)
   - Pipeline multi-stage: embeddings → FAISS search → refinamiento
   - Top-k candidatos con evidencia
   - Clasificación automática: MATCHED/AMBIGUOUS/NO_MATCH/MANUAL_REVIEW

### 11.3 Flujo de Matching

```
┌─────────────────┐
│  Rubros ET      │ (extraídos del PDF)
│  - Código ET    │
│  - Descripción  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. Embeddings   │ sentence-transformers
│    (vectores)   │ → [384 dims]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. FAISS Search │ cosine similarity
│    (top-k)      │ → [(idx, score), ...]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Refinamiento │ scoring combinado
│    (fuzzy+code) │ → MatchEvidence
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Clasificación│ thresholds
│   (status)      │ → MatchResult
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WBS Matched    │
│  - Código WBS   │
│  - Confidence   │
│  - Alternatives │
└─────────────────┘
```

### 11.4 Uso

#### 11.4.1 Cargar WBS de Referencia

```python
from src.match import load_reference_rubros_from_excel

reference_rubros = load_reference_rubros_from_excel(
    excel_path=Path("data/reference/WBS.xlsx"),
    sheet_name="WBS",
    code_col="Código",
    desc_col="Descripción",
    unit_col="Unidad",
    category_col="Especialidad"
)
# → List[ReferenceRubro]
```

#### 11.4.2 Crear Matcher

```python
from src.match import SemanticMatcher

matcher = SemanticMatcher(
    reference_rubros=reference_rubros,
    use_faiss=True  # Requiere faiss-cpu instalado
)
# → Genera embeddings y construye índice FAISS
```

#### 11.4.3 Matchear Rubros

```python
# Match único
match_result = matcher.match_single(rubro)

print(match_result.status)  # MATCHED
print(match_result.best_match.wbs_code)  # "01.01.01"
print(match_result.confidence)  # 0.92

# Match batch
match_results = matcher.match_batch(rubros_list)
```

### 11.5 Output: MatchResult

**Schema:** `src/models/schemas.py`

```python
class MatchResult(BaseModel):
    et_rubro_id: str                    # ID del rubro ET
    et_code: Optional[str]              # Código ET (si existe)
    et_description: str                 # Descripción ET
    status: MatchStatus                 # MATCHED | AMBIGUOUS | NO_MATCH | MANUAL_REVIEW
    best_match: Optional[MatchEvidence] # Mejor candidato
    alternative_matches: List[MatchEvidence]  # Top 3 alternativas
    confidence: float                   # Confidence global (0-1)
    processing_time_ms: float           # Tiempo de matching
```

**MatchEvidence:**
```python
class MatchEvidence(BaseModel):
    wbs_code: str                # Código WBS candidato
    wbs_description: str         # Descripción WBS
    similarity_score: float      # Score semántico (cosine)
    fuzzy_score: float           # Score fuzzy (0-100)
    combined_score: float        # Score final combinado (0-1)
    match_method: str            # semantic | fuzzy | code | hybrid
    snippet_et: Optional[str]    # Snippet ET para auditoría
    snippet_wbs: Optional[str]   # Snippet WBS para auditoría
```

### 11.6 Thresholds

**Configuración en:** `src/config/settings.py`

```python
MATCH_THRESHOLD = 0.75              # Match exitoso si score >= 0.75
MATCH_AMBIGUOUS_THRESHOLD = 0.05    # Ambiguo si top2 diff < 0.05
FUZZY_THRESHOLD = 80                # Fuzzy score mínimo (0-100)
```

### 11.7 Casos de Uso

| Caso | Status | Acción |
|------|--------|--------|
| Score >= 0.75 y único claro | **MATCHED** | Usar best_match automáticamente |
| Score >= 0.75 pero top 2 similares | **AMBIGUOUS** | Mostrar alternatives para revisión manual |
| Score 0.50-0.75 | **MANUAL_REVIEW** | Requiere validación humana |
| Score < 0.50 | **NO_MATCH** | No se encontró candidato válido |

---

## 12. Deduplicación y Conflictos

### 12.1 Objetivo

Detectar y resolver duplicados en los rubros extraídos. Duplicados pueden ocurrir por:
- ✅ Mismo rubro repetido en múltiples páginas (exacto)
- ✅ OCR generó códigos diferentes para el mismo rubro (conflicto)
- ✅ Rubros sin código que son similares

### 12.2 Estrategias

**Implementado en:** `src/dedupe/`

#### 12.2.1 MERGE (Fusionar Duplicados Exactos)

**Condición:** Mismo código + misma descripción + misma unidad

**Acción:**
- Fusionar en un único rubro
- Combinar `source_pages` (ej: [1, 3, 5])
- Promediar `confidence`
- Consolidar recursos asociados

**Ejemplo:**
```
Input:
- RUB_01_01_01_P1: "Excavación manual" (página 1)
- RUB_01_01_01_P3: "Excavación manual" (página 3)

Output:
- RUB_01_01_01: "Excavación manual" (páginas [1, 3])
```

#### 12.2.2 SPLIT (Separar Conflictos)

**Condición:** Mismo código pero diferentes descripciones/unidades

**Acción:**
- Detectar conflicto (DESCRIPTION, UNIT, RESOURCES)
- Separar con sufijos: `#A`, `#B`, `#C`

**Ejemplo:**
```
Input:
- RUB_01_01_01_P1: "Excavación manual" (unidad: m³)
- RUB_01_01_01_P5: "Excavación mecánica" (unidad: m³)

Conflicto: DESCRIPTION

Output:
- 01.01.01#A: "Excavación manual"
- 01.01.01#B: "Excavación mecánica"
```

#### 12.2.3 HASH (Generar Código)

**Condición:** Rubro sin código (código vacío o null)

**Acción:**
- Generar código hash basado en descripción
- Formato: `HASH_XXXXXXXX` (MD5 truncado)

**Ejemplo:**
```
Input:
- RUB_NONE_P2: "Material granular compactado" (código: "")

Output:
- HASH_3F7A2B1C: "Material granular compactado"
```

### 12.3 Uso

```python
from src.dedupe import DedupeEngine

engine = DedupeEngine(
    similarity_threshold=0.95,
    enable_merge=True,
    enable_split=True,
    enable_hash=True
)

deduped_rubros, duplicate_groups, stats = engine.deduplicate(rubros)

print(f"Input: {stats.total_input} rubros")
print(f"Output: {stats.total_output} rubros")
print(f"Merged: {stats.merged_groups}")
print(f"Split: {stats.split_groups}")
print(f"Hashed: {stats.hashed_rubros}")
```

### 12.4 Output: DuplicateGroup

**Schema:** `src/models/schemas.py`

```python
class DuplicateGroup(BaseModel):
    group_id: str                    # ID del grupo (DUP_01_01_01)
    canonical_code: str              # Código canónico normalizado
    rubro_ids: List[str]             # IDs de rubros duplicados
    strategy: DuplicateStrategy      # MERGE | SPLIT | HASH
    conflicts: List[ConflictType]    # [DESCRIPTION, UNIT, ...]
    resolved_rubros: List[Rubro]     # Rubros después de resolver
    merge_count: int                 # Cantidad de merges
    split_count: int                 # Cantidad de splits
```

### 12.5 Configuración

**settings.py:**
```python
DEDUPE_SIMILARITY_THRESHOLD = 0.95  # Para considerar descripciones similares
DEDUPE_ENABLE_MERGE = True
DEDUPE_ENABLE_SPLIT = True
DEDUPE_ENABLE_HASH = True
```

---

## 13. Artifacts v1.1

### 13.1 Objetivo

Generar artifacts adicionales (Markdown, JSON) para:
- ✅ Trazabilidad completa
- ✅ Debugging y auditoría
- ✅ Integración con otros sistemas
- ✅ Documentación automática

### 13.2 Artifacts Generados

**Ubicación:** `data/output/artifacts/[timestamp]/`

#### 13.2.1 ET.md (Markdown del PDF)

**Generado por:** Conversión avanzada (docling/marker/pymupdf)

**Contenido:**
- Markdown completo del PDF
- Preserva estructura (headers, listas, tablas)
- Útil para revisión manual

**Tamaño:** ~50-200 KB por 50 páginas

#### 13.2.2 ET.json (Estructura JSON)

**Generado por:** Conversión avanzada

**Contenido:**
```json
{
  "outline": [
    {"level": 1, "title": "01.00 OBRAS PRELIMINARES", "page": 1},
    {"level": 2, "title": "01.01.01 EXCAVACIÓN", "page": 1}
  ],
  "tables": [
    {
      "page": 3,
      "data": [["Código", "Descripción", "Unidad"], ...],
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "metadata": {
    "total_pages": 50,
    "strategy": "docling",
    "processing_time_s": 25.3
  }
}
```

#### 13.2.3 OUTLINE.md (Índice del Documento)

**Generado por:** `src/outline/outline_builder.py`

**Contenido:**
- Tabla de contenidos del PDF
- Jerarquía de rubros (nivel 1, 2, 3)
- Referencias de página

**Ejemplo:**
```markdown
# OUTLINE - Especificaciones Técnicas

## 01.00 OBRAS PRELIMINARES (Página 1)

### 01.01 Movimiento de Tierras (Página 1)
- 01.01.01 Excavación Manual (Página 1)
- 01.01.02 Excavación Mecánica (Página 2)

### 01.02 Demoliciones (Página 5)
- 01.02.01 Demolición de Muros (Página 5)
```

#### 13.2.4 RUN_REPORT.md (Resumen Ejecutivo)

**Generado por:** `src/report/md_reporter.py`

**Contenido:**
- Metadata del documento
- Estadísticas de conversión
- Estadísticas de extracción
- Matching semántico (success rate, distribución)
- Deduplicación (merges, splits)
- Warnings por severidad
- Lista de artifacts generados

**Ejemplo:** Ver [IMPLEMENTATION_SUMMARY_V1.1.md](IMPLEMENTATION_SUMMARY_V1.1.md)

#### 13.2.5 rubros_md/*.md (Reportes por Rubro)

**Generados por:** `src/report/rubro_report.py`

**Cantidad:** 1 archivo MD por rubro

**Naming:** `{codigo}_{descripcion}.md` (ej: `01_01_01_excavacion_manual.md`)

**Contenido de cada archivo:**
- Header (código + descripción)
- Información del rubro (tabla)
- Matching semántico (best match + alternatives)
- Recursos asociados (por tipo)
- Trazabilidad (páginas, confidence)
- Metadata

**Ejemplo:**
```markdown
# 01.01.01 - EXCAVACIÓN MANUAL EN TERRENO NATURAL

**ID:** `RUB_01_01_01_P1`

---

## 📋 Información del Rubro

| Atributo | Valor |
|----------|-------|
| **Código** | `01.01.01` |
| **Descripción** | EXCAVACIÓN MANUAL EN TERRENO NATURAL |
| **Unidad** | m³ |
| **Confianza** | 🟢 95.0% |
| **Páginas Fuente** | 1 |

## 🎯 Matching Semántico

✅ **Estado:** MATCHED
**Confianza:** 92.5%

### Mejor Candidato

| Atributo | Valor |
|----------|-------|
| **Código WBS** | `01.01.01` |
| **Descripción WBS** | Excavación manual en terreno compacto |
| **Score Semántico** | 88.3% |
| **Score Fuzzy** | 91.2% |
| **Score Combinado** | 92.5% |
| **Método** | hybrid |

...
```

#### 13.2.6 OUT.json (Resultado Completo)

**Generado por:** `src/report/json_generator.py`

**Contenido:**
- Serialización completa de `PipelineResultV1_1`
- Todos los rubros, recursos, warnings
- Resultados de matching
- Grupos de duplicados
- Metadata de artifacts

**Tamaño:** ~500 KB - 5 MB (dependiendo de cantidad de rubros)

**Uso:**
- Integración con otros sistemas (API, DB)
- Re-cargar resultados sin re-procesar
- Análisis programático

```python
from src.report import load_out_json

result = load_out_json(Path("data/output/artifacts/OUT.json"))
print(f"Rubros: {len(result.rubros)}")
print(f"Match success rate: {result.match_success_rate}")
```

### 13.3 ArtifactMetadata

**Schema:** Cada artifact tiene metadata asociada

```python
class ArtifactMetadata(BaseModel):
    artifact_type: Literal["ET.md", "ET.json", "OUTLINE.md", "RUN_REPORT.md", "rubro.md", "OUT.json"]
    file_path: str                    # Ruta absoluta
    size_bytes: int                   # Tamaño del archivo
    generated_at: datetime            # Timestamp
    checksum: Optional[str]           # MD5 hash
```

---

## 14. Excel Template Mode

### 14.1 Objetivo

Generar Excel en dos modos:

1. **Modo Global** (v1.0): 5 hojas con todos los rubros
2. **Modo Per-Rubro** (v1.1): 1 archivo Excel por rubro o 1 sheet por rubro

### 14.2 Modo Global (Default)

**Ya implementado en v1.0:** `src/export/excel_exporter.py`

**Estructura:**
- Hoja 1: Resumen
- Hoja 2: Rubros
- Hoja 3: Recursos
- Hoja 4: Relaciones Rubro-Recurso
- Hoja 5: Warnings

**Uso:**
```python
from src.export import ExcelExporter

exporter = ExcelExporter()
exporter.export_to_excel(
    result=pipeline_result,
    output_path=Path("data/output/resultado.xlsx")
)
```

### 14.3 Modo Per-Rubro (v1.1)

**Implementado en:** `src/export/template_exporter.py` (PENDIENTE)

#### 14.3.1 Opción A: 1 Archivo por Rubro

**Output:** `data/output/per_rubro/01_01_01_excavacion.xlsx`, `01_01_02_relleno.xlsx`, ...

**Estructura de cada archivo:**
- Hoja "Información": Código, descripción, unidad, método constructivo
- Hoja "Recursos": Tabla de materiales + equipos + mano de obra
- Hoja "Matching": Best match WBS + alternatives
- Hoja "Trazabilidad": Páginas, confidence, snippets

**Uso:**
```python
from src.export import TemplateExporter

exporter = TemplateExporter(mode="one_file_per_rubro")
exporter.export(rubros, recursos, match_results, output_dir)
```

#### 14.3.2 Opción B: 1 Sheet por Rubro (Single File)

**Output:** `data/output/resultado_per_rubro.xlsx`

**Estructura:**
- Sheet "Resumen": Índice de todos los rubros
- Sheet "01.01.01": Rubro 01.01.01 con recursos
- Sheet "01.01.02": Rubro 01.01.02 con recursos
- ...

**Limitación Excel:** Máximo 1,048,576 sheets (en práctica: ~100-200 rubros recomendados)

**Uso:**
```python
exporter = TemplateExporter(mode="one_sheet_per_rubro")
exporter.export(rubros, recursos, match_results, output_path)
```

### 14.4 Plantillas

**Ubicación:** `data/templates/rubro_template.xlsx`

**Contenido:**
- Formato predefinido (colores, headers, anchos de columna)
- Fórmulas (ej: total de recursos)
- Validaciones de datos

**Customización:**
- Editar `rubro_template.xlsx` manualmente
- El exporter copia la plantilla y rellena datos

### 14.5 Configuración

**settings.py:**
```python
EXPORT_MODE = "auto"  # global | one_file_per_rubro | one_sheet_per_rubro | auto
EXCEL_MAX_RUBROS = 100  # Límite para one_sheet_per_rubro
```

**Lógica "auto":**
```python
if len(rubros) <= EXCEL_MAX_RUBROS:
    mode = "one_sheet_per_rubro"
else:
    mode = "global"
```

### 14.6 Sheet Name Sanitization

Excel tiene límites en nombres de hojas:
- ✅ Máximo 31 caracteres
- ❌ No permitidos: `\ / : * ? [ ]`

**Utilidad:** `src/utils/text_norm.py`

```python
from src.utils.text_norm import sanitize_excel_sheet_name

safe_name = sanitize_excel_sheet_name("01.01.01 - Excavación Manual en Terreno Natural")
# → "01_01_01_Excavacion_Manual_e"
```

---

## 📊 Diagrama de Flujo

```
┌─────────────────┐
│   PDF Input     │
│  (data/input/)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  1. INGEST      │  pdf_reader.py
│  - Detect type  │  → Dict[page, text]
│  - Extract text │  → DocumentMetadata
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Digital? │ ──No──┐
    └────┬────┘        │
         │Yes          ▼
         │      ┌─────────────────┐
         │      │  2. OCR         │  tesseract_ocr.py
         │      │  - PDF→Image    │  → Dict[page, text]
         │      │  - Tesseract    │  → confidence
         │      └────────┬────────┘
         │               │
         └───────────────┘
                 │
                 ▼
         ┌─────────────────┐
         │  3. PARSE       │  rubro_parser.py
         │  - Segmentar    │  → List[Rubro]
         │  - Extraer      │  → List[Recurso]
         │  - Clasificar   │  → List[ParseWarning]
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  4. VALIDATE    │
         │  - Check FKs    │
         │  - Warnings     │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  5. EXPORT      │  excel_exporter.py
         │  - 5 hojas      │  → .xlsx
         │  - Formato      │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   Excel Output  │
         │ (data/output/)  │
         └─────────────────┘
```

---

## 📝 Notas Finales

### Convenciones de Código

- **Estilo:** PEP 8, formateado con `black`
- **Type hints:** Obligatorios en todas las funciones públicas
- **Docstrings:** Formato Google Style
- **Logging:** Usar `structlog` con contexto
- **Idioma:** Código y comentarios en español

### Contacto y Soporte

Para bugs, features o dudas:
- Crear issue en repositorio
- Revisar logs en `data/output/[nombre]_resultado.xlsx` → Hoja "Warnings"

---

**Fin de especificación técnica**
