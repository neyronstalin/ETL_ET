# 🏗️ ARQUITECTURA DEL SISTEMA - ETL_ET v1.1

**Proyecto:** Pipeline Extracción PDF Especificaciones Técnicas
**Versión:** 1.1 (Advanced Mode)
**Fecha:** 2026-01-28

---

## 📊 VISIÓN GENERAL

ETL_ET es un pipeline modular para extraer información estructurada desde PDFs de especificaciones técnicas y matchear contra un archivo de referencia WBS.

**Modos de operación:**
- **Legacy (v1.0):** PDF → OCR → Parse → Excel (5 hojas)
- **Advanced (v1.1):** PDF → Conversión estructurada → Match WBS → Dedupe → Reportes MD + Excel

---

## 🎯 OBJETIVOS ARQUITECTÓNICOS

1. **Modularidad:** Cada fase es independiente y testeable
2. **Extensibilidad:** Fácil agregar nuevos conversores o matchers
3. **Trazabilidad:** Todo dato tiene origen (página + snippet + confidence)
4. **Fallbacks:** Múltiples estrategias para conversión y matching
5. **Performance:** Caching de embeddings y OCR
6. **Usabilidad:** CLI + Notebook, logs estructurados, reportes legibles

---

## 📐 DIAGRAMA DE MÓDULOS

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ETL_ET PIPELINE v1.1                         │
└──────────────────────────────────────────────────────────────────────┘

                              ┌──────────┐
                              │   USER   │
                              └─────┬────┘
                                    │
                      ┌─────────────┴──────────────┐
                      │                            │
                 ┌────▼────┐                 ┌─────▼──────┐
                 │   CLI   │                 │  Notebook  │
                 │pipeline.│                 │  Jupyter   │
                 │   py    │                 │            │
                 └────┬────┘                 └─────┬──────┘
                      │                            │
                      └─────────────┬──────────────┘
                                    │
                        ┌───────────▼────────────┐
                        │  ORCHESTRATOR         │
                        │  src/pipeline.py       │
                        │  - Legacy path         │
                        │  - Advanced path       │
                        └───────────┬────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
   ┌────▼────┐              ┌───────▼────────┐          ┌──────▼──────┐
   │ CONFIG  │              │   CONVERSION   │          │   INGEST    │
   │settings │              │ DoclingMarker   │          │ pdf_reader  │
   │  .py    │              │   PyMuPDF4LLM  │          │   WBS ref   │
   └─────────┘              └───────┬────────┘          └──────┬──────┘
                                    │                           │
                        ┌───────────▼────────────┬──────────────┘
                        │                        │
                   ┌────▼─────┐          ┌──────▼──────┐
                   │ OUTLINE  │          │    MATCH    │
                   │ builder  │          │  WBS ↔ ET   │
                   └──────────┘          │  embedder   │
                                         │  matcher    │
                                         │  scoring    │
                                         └──────┬──────┘
                                                │
                        ┌───────────────────────┼───────────────────┐
                        │                       │                   │
                   ┌────▼─────┐          ┌─────▼──────┐      ┌─────▼──────┐
                   │  PARSE   │          │   DEDUPE   │      │   REPORT   │
                   │ resource │          │   merge    │      │ json, MD   │
                   │extractor │          │   split    │      │  rubro_md  │
                   └──────────┘          └─────┬──────┘      └─────┬──────┘
                                               │                    │
                                               └──────────┬─────────┘
                                                          │
                                                     ┌────▼─────┐
                                                     │  EXPORT  │
                                                     │  Excel   │
                                                     │ template │
                                                     └──────────┘
```

---

## 🔄 DATAFLOW DETALLADO

### Legacy Path (v1.0)

```
 PDF INPUT
     │
     ▼
 ┌───────────────┐
 │   INGEST      │  pdf_reader.py
 │ - Detect type │  → Dict[page, text]
 │ - Extract txt │
 └───────┬───────┘
         │
         ▼
    ┌────────┐
    │Digital?│ ──No──┐
    └───┬────┘       │
        │Yes         ▼
        │        ┌───────────────┐
        │        │      OCR      │  tesseract_ocr.py
        │        │  - Tesseract  │  → text + confidence
        │        └───────┬───────┘
        │                │
        └────────────────┘
                │
                ▼
         ┌──────────────┐
         │    PARSE     │  rubro_parser.py
         │ - Segment    │  → Rubros[]
         │ - Extract    │  → Recursos[]
         │ - Classify   │  → Warnings[]
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │    EXPORT    │  excel_exporter.py
         │ - 5 sheets   │  → resultado.xlsx
         │ - Format     │
         └──────────────┘
```

---

### Advanced Path (v1.1)

```
 PDF INPUT + WBS REFERENCE
     │              │
     ▼              │
 ┌──────────────────────────┐
 │   CONVERSION             │  convert/converter_router.py
 │ 1. Try Docling           │  → ET.md (Markdown fiel)
 │ 2. Fallback Marker       │  → ET.json (estructura)
 │ 3. Fallback PyMuPDF4LLM  │  → ConversionResult
 └──────────┬───────────────┘
            │
            ▼
 ┌──────────────────────────┐
 │   OUTLINE BUILDER        │  outline/outline_builder.py
 │ - Parse ET.json          │  → OUTLINE.md
 │ - Build hierarchy        │  (Página → Sección → Rubro)
 └──────────┬───────────────┘
            │
            ├─────────────────────┐
            │                     │
            ▼                     ▼
    ┌───────────────┐     ┌───────────────┐
    │  WBS INGEST   │     │   ET PARSE    │
    │ - Load XLSX   │     │ - From ET.json│
    │ - Normalize   │     │ - Extract     │
    │ - Validate    │     │   rubros      │
    └───────┬───────┘     └───────┬───────┘
            │                     │
            │   ┌─────────────────┘
            │   │
            ▼   ▼
    ┌───────────────────────────┐
    │   MATCHING SEMÁNTICO      │  match/matcher.py
    │ 1. Exact code match       │  → MatchResult[]
    │ 2. Fuzzy code (rapidfuzz) │  - MATCHED (≥0.75)
    │ 3. Embeddings (cosine)    │  - AMBIGUOUS (0.65-0.75)
    │ 4. Hybrid scoring         │  - UNMATCHED (<0.65)
    └──────────┬────────────────┘
               │
               ▼
    ┌───────────────────────────┐
    │   RESOURCE EXTRACTION     │  parse/resource_extractor.py
    │ - From ET.json tables     │  → Recursos[]
    │ - Classify MATERIAL/EQUIP │  (trazabilidad: page+snippet)
    └──────────┬────────────────┘
               │
               ▼
    ┌───────────────────────────┐
    │   DEDUPLICATION           │  dedupe/dedupe_engine.py
    │ - Detect duplicates       │  → DuplicateGroup[]
    │ - Merge exact             │  - MERGE (exact)
    │ - Split conflicts         │  - SPLIT (conflict: #A, #B)
    │ - Hash code-missing       │  - HASH (no code)
    └──────────┬────────────────┘
               │
               ├──────────────────┬──────────────────┐
               │                  │                  │
               ▼                  ▼                  ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  OUT.json    │   │ RUN_REPORT   │   │  rubros_md/  │
    │  (puente)    │   │    .md       │   │  *.md        │
    └──────────────┘   └──────────────┘   └──────────────┘
               │
               ▼
    ┌───────────────────────────┐
    │   EXPORT EXCEL            │  export/template_exporter.py
    │ Mode: per-rubro | global  │  → resultado.xlsx
    │ - 1 sheet/rubro           │  (con template)
    │ - Sanitize names (≤31ch)  │
    │ - Fallback to global      │
    └───────────────────────────┘
```

---

## 🧩 MÓDULOS Y RESPONSABILIDADES

### 1. **src/config/** (Configuración)

**Archivo:** `settings.py`

**Responsabilidad:** Configuración global con Pydantic Settings.

**Variables clave:**
- Paths (input, output, cache, artifacts, templates)
- OCR (lang, DPI, confidence threshold)
- Conversión (strategy, timeout)
- Matching (embedding model, thresholds, FAISS)
- Export (mode, formato)
- Logging (level, JSON, file)

**Patrón:** Singleton

---

### 2. **src/convert/** (Conversión Estructurada)

**Archivos:**
- `docling_converter.py`: Conversión con Docling (IBM)
- `marker_converter.py`: Conversión con Marker (fallback)
- `pymupdf_converter.py`: Conversión rápida PyMuPDF4LLM (fallback 2)
- `converter_router.py`: Router automático con cascade

**Responsabilidad:** PDF → ET.md + ET.json

**Estrategia:**
1. Intenta Docling (mejor calidad)
2. Si falla → Marker (fallback robusto)
3. Si falla → PyMuPDF4LLM (fallback rápido)

**Output:**
- `ET.md`: Markdown fiel al PDF (inspección humana)
- `ET.json`: JSON estructurado (secciones, tablas, bloques, páginas)

**Patrón:** Strategy + Chain of Responsibility

---

### 3. **src/outline/** (Outline Jerárquico)

**Archivo:** `outline_builder.py`

**Responsabilidad:** Construir jerarquía Página → Sección → Rubro

**Input:** ET.json
**Output:** OUTLINE.md

**Estructura:**
```
# OUTLINE
## Página 1
### Sección 1.1: MOVIMIENTO DE TIERRAS
- 01.01.01 Excavación manual (líneas 10-25)
- 01.01.02 Relleno (líneas 26-45)
## Página 2
...
```

**Utilidad:** Navegación rápida, debugging

---

### 4. **src/ingest/** (Ingesta de Datos)

**Archivos:**
- `pdf_reader.py`: (v1.0) Lector PDF básico
- `reference_reader.py`: (v1.1) Lector WBS reference

**Responsabilidad:**
- Leer PDF y detectar tipo (digital/escaneado/mixto)
- Cargar WBS reference desde XLSX/CSV

**WBS format esperado:**
- Columnas: `codigo`, `descripcion`, `unidad`
- Columnas opcionales: `precio_unitario`, `cantidad` (ignoradas)

**Validación:**
- Detectar duplicados en WBS
- Normalizar códigos
- Generar `WBS_VALIDATION.md`

---

### 5. **src/match/** (Matching Semántico)

**Archivos:**
- `embedder.py`: Generación de embeddings
- `matcher.py`: Matching multi-stage
- `scoring.py`: Cálculo de scores

**Responsabilidad:** Match WBS ↔ ET

**Estrategia multi-stage:**
1. **Exact code:** Si código match exacto → score=1.0
2. **Fuzzy code:** rapidfuzz >80 → score=0.9
3. **Embeddings:** cosine similarity → score variable
4. **Hybrid:** (fuzzy_desc * 0.3) + (embedding_sim * 0.7)

**Modelo embeddings:**
- `paraphrase-multilingual-MiniLM-L12-v2`
- Cache en `data/cache/embeddings/`
- Batch processing (32 rubros/batch)

**FAISS:**
- Solo si >1000 rubros
- k-NN búsqueda rápida

**Categorización:**
- **MATCHED:** score ≥ 0.75
- **AMBIGUOUS:** 0.65 ≤ score < 0.75 (revisar manual)
- **UNMATCHED:** score < 0.65

**Patrón:** Strategy + Template Method

---

### 6. **src/parse/** (Parseo y Extracción)

**Archivos:**
- `rubro_parser.py`: (v1.0) Parser regex básico
- `resource_extractor.py`: (v1.1) Extracción layout-aware

**Responsabilidad:**
- Parsear rubros desde texto (v1.0) o ET.json (v1.1)
- Extraer recursos (materiales/equipos) desde tablas o listas
- Clasificar tipo de recurso (MATERIAL/EQUIPO)

**Layout-aware (v1.1):**
- Parse tablas en ET.json (si existe sección "tables")
- Identificar columnas: nombre, unidad, cantidad
- Fallback a regex si no hay tablas

**Clasificación:**
- Keywords (30+ por tipo)
- Fuzzy matching (rapidfuzz)
- Embeddings (opcional)

**Trazabilidad:**
- Cada recurso tiene: `pages`, `snippet`, `table_id`, `confidence`

---

### 7. **src/dedupe/** (Deduplicación)

**Archivo:** `dedupe_engine.py`

**Responsabilidad:** Detectar y resolver duplicados

**Casos:**
1. **Duplicado exacto:** Mismo código + misma unidad → **MERGE**
   - Unir recursos
   - Combinar páginas
   - Promedio de confidence
   - Provenance: `merged_from: [id1, id2]`

2. **Conflicto:** Mismo código + distinta unidad → **SPLIT**
   - Crear: `codigo#A`, `codigo#B`
   - Marcar: `conflict_flag: True`
   - Incluir ambos en OUT.json

3. **Código ausente:** No se detectó código → **HASH**
   - Generar ID: `HASH_<sha256[:8]>`
   - Marcar: `code_missing: True`
   - Warning en RUN_REPORT

**Patrón:** Strategy

---

### 8. **src/report/** (Reportes)

**Archivos:**
- `json_generator.py`: Genera OUT.json
- `md_reporter.py`: Genera RUN_REPORT.md
- `rubro_report.py`: Genera rubros_md/*.md

**Responsabilidad:** Outputs finales estructurados

**OUT.json:**
```json
{
  "metadata": {...},
  "summary": {
    "total_wbs_rubros": 150,
    "total_et_rubros": 145,
    "matched": 130,
    "ambiguous": 10,
    "unmatched": 10
  },
  "matches": [...],
  "duplicates": [...],
  "conflicts": [...],
  "warnings": [...]
}
```

**RUN_REPORT.md:**
- Resumen numérico
- Tabla de duplicados resueltos
- Tabla de conflictos
- Top warnings por severidad

**rubros_md/*.md:**
- 1 archivo por rubro
- Match WBS → ET (score)
- Páginas origen + snippet
- Tabla de recursos
- Warnings específicos
- Máximo 30 líneas snippet

**Patrón:** Builder + Template

---

### 9. **src/export/** (Export Excel)

**Archivos:**
- `excel_exporter.py`: (v1.0) Export 5 hojas global
- `template_exporter.py`: (v1.1) Export per-rubro con template

**Responsabilidad:** Generar Excel final

**Modo per-rubro:**
- 1 hoja por rubro (usa template `rubro_template.xlsx`)
- Nombre hoja: `{codigo}` (sanitizado, ≤31 chars)
- Fallback si >100 rubros → modo global

**Modo global:**
- 5 hojas: Resumen, Rubros, Recursos, Relaciones, Warnings
- Colores por severidad (warnings)
- Formato automático (anchos, colores)

**Sanitización:**
- Nombres ≤31 chars
- Sin caracteres: `\/:*?[]`
- Deduplicación de nombres (sufijo `_2`, `_3`)

**Patrón:** Strategy + Template

---

### 10. **src/models/** (Modelos de Datos)

**Archivo:** `schemas.py`

**Responsabilidad:** Definir contratos con Pydantic

**Modelos v1.0:**
- `Rubro`, `Recurso`, `ParseWarning`
- `TipoRecurso`, `TipoDocumento`, `WarningKind`
- `PageMetadata`, `DocumentMetadata`, `PipelineResult`

**Modelos v1.1 (nuevos):**
- `ConversionResult`: Output de conversores
- `OutlineStructure`, `OutlineNode`: Jerarquía outline
- `ReferenceRubro`, `ETRubro`: Rubros WBS vs ET
- `MatchResult`, `MatchEvidence`: Resultados de matching
- `DuplicateGroup`, `ConflictRecord`: Deduplicación
- `PipelineArtifacts`: Paths a artefactos generados

**Patrón:** Data Transfer Object (DTO)

---

### 11. **src/utils/** (Utilidades)

**Archivos:**
- `logger.py`: (v1.0) Structlog
- `text_norm.py`: (v1.1) Normalización de texto

**Responsabilidad:**
- Logging estructurado con contexto
- Normalización de códigos, unidades, strings
- Corrección de errores OCR
- Sanitización de nombres de archivo/hoja

**Funciones clave text_norm:**
- `normalize_rubro_code()`: "1.1.1" → "01.01.01"
- `fix_ocr_errors()`: "O1" → "01", "0l" → "01"
- `normalize_unidad()`: "m2" → "m²"
- `sanitize_excel_sheet_name()`: ≤31 chars, sin [\/:*?]

---

### 12. **src/pipeline.py** (Orchestrator)

**Responsabilidad:** Orquestar todo el flujo

**Modos:**
- `legacy`: Pipeline v1.0 (PDF → OCR → Parse → Excel)
- `advanced`: Pipeline v1.1 (Conversión → Match → Dedupe → Reportes)
- `auto`: Detecta automáticamente (si hay WBS reference → advanced)

**CLI:**
```bash
python src/pipeline.py input.pdf \
  --mode advanced \
  --reference wbs.xlsx \
  --export-mode per-rubro \
  --write-artifacts true \
  --match-threshold 0.75
```

**Patrón:** Facade + Strategy

---

## 🎨 PATRONES DE DISEÑO

| Patrón | Módulo | Justificación |
|--------|--------|---------------|
| **Singleton** | config/settings | Una sola instancia de configuración |
| **Strategy** | convert/, export/ | Múltiples estrategias intercambiables |
| **Chain of Responsibility** | convert/router | Fallbacks en cascada |
| **Template Method** | match/matcher | Matching multi-stage con pasos definidos |
| **Builder** | report/ | Construcción de reportes complejos |
| **Factory** | models/schemas | Generación de IDs únicos |
| **Facade** | pipeline.py | Interfaz simple para sistema complejo |

---

## 💾 PERSISTENCIA Y CACHE

### Cache de OCR

**Ubicación:** `data/cache/ocr/`
**Estrategia:** joblib.Memory (hash por página)
**Beneficio:** No re-procesar páginas ya OCRizadas

### Cache de Embeddings

**Ubicación:** `data/cache/embeddings/`
**Estrategia:** Pickle de numpy arrays (hash por texto)
**Beneficio:** Embeddings se calculan 1 vez, reusan en siguientes runs

### Artifacts

**Ubicación:** `data/artifacts/`
**Archivos:**
- `ET.md`, `ET.json` (conversión)
- `OUTLINE.md` (outline)
- `OUT.json` (resultado final)
- `RUN_REPORT.md` (reporte)
- `rubros_md/*.md` (reportes por rubro)
- `WBS_VALIDATION.md` (validación WBS)

**Retención:** Overwrite en cada run (no historial)

---

## 🔒 PRINCIPIOS SOLID

### Single Responsibility
- Cada módulo tiene 1 responsabilidad clara
- `embedder.py` solo genera embeddings
- `matcher.py` solo hace matching
- `dedupe_engine.py` solo deduplica

### Open/Closed
- Fácil agregar nuevos conversores (docling, marker, pymupdf, ...)
- Fácil agregar nuevos matchers (regex, fuzzy, embeddings, ...)
- No modificar código existente

### Liskov Substitution
- Todos los conversores devuelven `ConversionResult`
- Intercambiables sin romper pipeline

### Interface Segregation
- Interfaces pequeñas y enfocadas
- `Embedder` solo tiene `embed()`
- `Matcher` solo tiene `match()`

### Dependency Inversion
- Pipeline depende de abstracciones (interfaces)
- No depende de implementaciones concretas
- Config inyectado vía Settings

---

## 📊 TRADE-OFFS Y DECISIONES

| Decisión | Pro | Contra | Justificación |
|----------|-----|--------|---------------|
| **Pydantic Settings** | Validación automática, type hints | +1 dependencia | Esencial para config robusta |
| **Sentence-transformers** | Matching semántico robusto | ~1GB modelos, lento | Accuracy > speed en v1.1 |
| **FAISS** | Búsqueda k-NN rápida | Solo útil si >1000 rubros | Opcional, threshold configurable |
| **Múltiples conversores** | Fallbacks robustos | Más dependencias | Crítico para robustez |
| **Cache embeddings** | Performance | Disco +500MB | Esencial, embeddings muy lentos |
| **Reportes MD** | Legibilidad humana | +I/O operations | Debugging y auditoría |
| **Excel per-rubro** | Mejor UX (1 hoja/rubro) | Límite 100 rubros | Fallback a global |

---

## 🚀 ESCALABILIDAD

### Limitaciones actuales (v1.1)

| Límite | Valor | Mitigación |
|--------|-------|------------|
| **Rubros por PDF** | ~500 | Paralelizar matching |
| **Páginas por PDF** | ~200 | Batch processing OCR |
| **Embeddings cache** | ~1GB | Configurar limpieza periódica |
| **Excel per-rubro** | 100 rubros | Fallback a global mode |
| **RAM (embeddings)** | 8GB mín | Reducir batch size |

### Mejoras futuras (v2.0)

- **Paralelización:** multiprocessing para OCR y embeddings
- **Base de datos:** PostgreSQL para histórico
- **API REST:** Servicio web para integración
- **GPU:** FAISS-GPU para búsqueda más rápida
- **Streaming:** Procesamiento incremental de PDFs grandes

---

## 🧪 TESTING STRATEGY

### Niveles de testing

1. **Unit tests:** Funciones individuales (normalización, scoring, etc.)
2. **Integration tests:** Módulos completos (converter, matcher, etc.)
3. **End-to-end tests:** Pipeline completo (PDF → Excel)
4. **Smoke tests:** Imports y configuración básica

### Fixtures

- `pdf_synthetic.pdf`: PDF generado con reportlab (20 rubros)
- `wbs_example.xlsx`: WBS reference (15 rubros)
- `et_mock.json`: ET.json simulado
- `et_mock.md`: ET.md simulado

### Coverage target

- Módulos core: >80%
- Módulos utils: >90%
- Global: >75%

---

## 📚 DOCUMENTACIÓN

| Documento | Audiencia | Contenido |
|-----------|-----------|-----------|
| **README.md** | Usuarios | Overview, quick start |
| **QUICKSTART.md** | Usuarios | Comandos esenciales |
| **SETUP.md** | Usuarios | Instalación detallada |
| **SPEC.md** | Desarrolladores | Especificación técnica completa |
| **ARCHITECTURE.md** | Desarrolladores | Este documento |
| **PLAN_V1.1.md** | PM | Plan de 10 fases |
| **RUN_REPORT.md** | Usuarios finales | Reporte por ejecución |

---

## 🔄 FLUJO DE TRABAJO TÍPICO

### Usuario Final

```bash
# 1. Instalar
pip install -r requirements-full.txt

# 2. Preparar inputs
cp especificaciones.pdf data/input/
cp wbs_referencia.xlsx data/input/

# 3. Ejecutar pipeline advanced
python src/pipeline.py data/input/especificaciones.pdf \
  --mode advanced \
  --reference data/input/wbs_referencia.xlsx

# 4. Revisar outputs
cat data/artifacts/RUN_REPORT.md
open data/output/especificaciones_resultado.xlsx
ls data/artifacts/rubros_md/
```

### Desarrollador (agregar nuevo conversor)

```bash
# 1. Crear módulo
touch src/convert/my_converter.py

# 2. Implementar interfaz ConversionResult
# 3. Agregar a converter_router.py
# 4. Tests
pytest tests/test_convert.py::test_my_converter -v

# 5. Documentar en SPEC.md
```

---

## 🎯 CONCLUSIÓN

La arquitectura v1.1 está diseñada para ser:
- **Modular:** Fácil agregar/modificar componentes
- **Robusta:** Múltiples fallbacks y validaciones
- **Trazable:** Todo dato tiene origen y confidence
- **Escalable:** Preparado para paralelización y BD futuro
- **Usable:** CLI + Notebook + Reportes legibles

**Próximo paso:** Implementar Fase 1 (Conversión) según [PLAN_V1.1.md](PLAN_V1.1.md)

---

**Fin ARCHITECTURE.md**
