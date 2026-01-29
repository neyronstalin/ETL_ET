# 🚀 PLAN DE ACCIÓN v1.1 - Advanced Document AI Pipeline

**Proyecto:** ETL_ET
**Objetivo:** Conversión estructurada + Matching WBS + Deduplicación + Reportes MD
**Stack:** Docling/Marker + sentence-transformers + faiss + Template Excel

---

## 📊 RESUMEN EJECUTIVO

**Estado Actual (v1.0):**
- ✅ Pipeline básico: PDF → OCR → Parse → Excel (5 hojas)
- ✅ Arquitectura modular (src/ organizado)
- ✅ Pydantic models + structlog
- ✅ Tests básicos (smoke + parse)

**Estado Objetivo (v1.1):**
- ✅ Conversión estructurada (Docling/Marker) → ET.md + ET.json
- ✅ Matching semántico WBS ↔ ET (embeddings + fuzzy)
- ✅ Extracción de recursos layout-aware
- ✅ Resolución de duplicados automática
- ✅ Outputs: OUT.json + RUN_REPORT.md + rubros_md/*.md
- ✅ Excel por rubro con template
- ✅ CLI extendido (--mode advanced, --reference wbs.xlsx)

---

## 🎯 FASES DE IMPLEMENTACIÓN

### FASE 0: AUDITORÍA Y SETUP INICIAL

**Objetivo:** Verificar estado actual, preparar estructura, configurar dependencias.

**Tareas:**

- [ ] **0.1** Auditar módulos existentes
  - Verificar contratos de `src/pipeline.py` (inputs/outputs)
  - Revisar modelos Pydantic en `src/models/schemas.py`
  - Identificar puntos de extensión (legacy vs advanced path)

- [ ] **0.2** Crear estructura de carpetas v1.1
  ```
  src/convert/           # Docling, Marker, PyMuPDF4LLM
  src/outline/           # OUTLINE.md builder
  src/ingest/reference_reader.py  # WBS reference loader
  src/match/             # Embedder, matcher, scoring
  src/dedupe/            # Deduplicación y conflictos
  src/report/            # MD reporters (RUN_REPORT + rubros_md)
  src/export/template_exporter.py
  src/config/settings.py
  data/templates/
  data/artifacts/        # ET.md, ET.json, OUT.json, etc.
  tests/test_convert.py
  tests/test_match.py
  tests/test_dedupe.py
  tests/fixtures/        # PDFs sintéticos, WBS mock
  ```

- [ ] **0.3** Actualizar requirements.txt
  - Agregar: docling, marker-pdf, pymupdf4llm
  - Agregar: sentence-transformers, faiss-cpu
  - Agregar: openpyxl (ya existe, verificar versión)
  - Marcar opcionales: easyocr (ya opcional), torch (para embeddings)
  - Crear requirements-full.txt vs requirements-minimal.txt

- [ ] **0.4** Configurar Settings (Pydantic)
  - Crear `src/config/settings.py`
  - Variables: OCR_LANG, MATCH_THRESHOLD, EXPORT_MODE, ARTIFACT_DIR
  - Cargar desde .env con defaults

**Definition of Done:**
- ✅ Estructura de carpetas creada
- ✅ requirements-full.txt instalable sin errores
- ✅ Settings.py funcional con defaults
- ✅ Documentación actualizada (árbol de carpetas en README)

**Artefactos:**
- `PLAN_V1.1.md` (este archivo)
- `requirements-full.txt`
- `src/config/settings.py`
- Carpetas creadas

---

### FASE 1: INTEGRACIÓN CONVERSIÓN DOC → (ET.md + ET.json)

**Objetivo:** Integrar Docling/Marker/PyMuPDF4LLM para conversión estructurada.

**Tareas:**

- [ ] **1.1** Implementar `src/convert/docling_converter.py`
  - Función: `convert_with_docling(pdf_path: Path) -> ConversionResult`
  - Output: ET.md + ET.json (estructura: secciones, tablas, bloques)
  - Manejar excepciones (PDF corrupto, timeout)
  - Confidence score por página

- [ ] **1.2** Implementar `src/convert/marker_converter.py`
  - Función: `convert_with_marker(pdf_path: Path) -> ConversionResult`
  - Fallback si Docling falla
  - Output: ET.md + ET.json (formato normalizado)

- [ ] **1.3** Implementar `src/convert/pymupdf_converter.py`
  - Función: `convert_with_pymupdf(pdf_path: Path) -> ConversionResult`
  - Fallback rápido (solo MD, JSON mínimo)
  - Para debugging

- [ ] **1.4** Implementar `src/convert/converter_router.py`
  - Función: `convert_pdf(pdf_path: Path, strategy: str = "auto") -> ConversionResult`
  - Strategy: "docling" | "marker" | "pymupdf" | "auto"
  - Auto: intenta Docling → Marker → PyMuPDF
  - Log de cuál conversor se usó y por qué

- [ ] **1.5** Definir modelo `ConversionResult` (Pydantic)
  ```python
  class ConversionResult(BaseModel):
      md_path: Path
      json_path: Path
      converter_used: Literal["docling", "marker", "pymupdf"]
      pages_processed: int
      confidence: float
      processing_time_ms: float
      warnings: List[str]
  ```

- [ ] **1.6** Integrar en pipeline.py
  - Agregar parámetro `conversion_strategy: str = "auto"`
  - Si mode="advanced", usar converter_router
  - Guardar artefactos en `data/artifacts/`

**Definition of Done:**
- ✅ 3 conversores implementados con fallbacks
- ✅ Router funcional (auto mode selecciona mejor)
- ✅ ET.md y ET.json generados correctamente
- ✅ Tests unitarios (mock PDFs, verificar outputs)
- ✅ Documentado en SPEC.md sección "Advanced Conversion"

**Artefactos:**
- `src/convert/*.py` (4 módulos)
- `ConversionResult` en `src/models/schemas.py`
- `tests/test_convert.py`
- ET.md, ET.json en `data/artifacts/`

---

### FASE 2: GENERACIÓN DE OUTLINE JERÁRQUICO (OUTLINE.md)

**Objetivo:** Crear OUTLINE.md con estructura: Página → Sección → Rubro.

**Tareas:**

- [ ] **2.1** Implementar `src/outline/outline_builder.py`
  - Función: `build_outline(et_json: Path) -> OutlineStructure`
  - Parse ET.json para identificar jerarquía
  - Detectar códigos de rubro (XX.XX.XX)
  - Generar árbol: Página → Sección → Subsección → Rubro

- [ ] **2.2** Implementar `generate_outline_md(outline: OutlineStructure) -> Path`
  - Genera OUTLINE.md con formato:
    ```markdown
    # OUTLINE - Especificaciones Técnicas

    ## Página 1
    ### Sección 1.1: MOVIMIENTO DE TIERRAS
    - 01.01.01 Excavación manual (líneas 10-25)
    - 01.01.02 Relleno compactado (líneas 26-45)

    ## Página 2
    ...
    ```
  - Indicar número de línea o char_offset para trazabilidad

- [ ] **2.3** Definir modelo `OutlineStructure` (Pydantic)
  ```python
  class OutlineNode(BaseModel):
      level: int  # 1=página, 2=sección, 3=rubro
      title: str
      code: Optional[str]  # Si es rubro
      page: int
      line_start: Optional[int]
      line_end: Optional[int]
      children: List['OutlineNode'] = []
  ```

- [ ] **2.4** Integrar en pipeline avanzado
  - Generar OUTLINE.md después de conversión
  - Usar para navegación rápida (debugging)

**Definition of Done:**
- ✅ OUTLINE.md generado con jerarquía clara
- ✅ Códigos de rubro detectados y ubicados
- ✅ Tests: verificar jerarquía con ET.json mock
- ✅ Documentado en SPEC.md

**Artefactos:**
- `src/outline/outline_builder.py`
- `OutlineStructure` en `src/models/schemas.py`
- OUTLINE.md en `data/artifacts/`
- `tests/test_outline.py`

---

### FASE 3: INGEST WBS REFERENCE + MODELOS

**Objetivo:** Cargar archivo WBS de referencia (XLSX/CSV) y modelar.

**Tareas:**

- [ ] **3.1** Implementar `src/ingest/reference_reader.py`
  - Función: `load_wbs_reference(file_path: Path) -> List[ReferenceRubro]`
  - Soportar XLSX y CSV
  - Columnas esperadas: codigo, descripcion, unidad
  - Columnas opcionales: precio_unitario, cantidad (ignorar)
  - Validar con Pydantic

- [ ] **3.2** Definir modelo `ReferenceRubro` (Pydantic)
  ```python
  class ReferenceRubro(BaseModel):
      wbs_id: str  # Generado: hash o index
      codigo: str
      descripcion: str
      unidad: str
      metadata: Dict[str, Any] = {}  # Campos extra

      @field_validator('codigo')
      def normalize_codigo(cls, v):
          # Normalizar: 01.01.01 vs 1.1.1 → 01.01.01
          return normalize_rubro_code(v)
  ```

- [ ] **3.3** Implementar normalización de código
  - Función: `normalize_rubro_code(code: str) -> str`
  - Casos:
    - "1.1.1" → "01.01.01"
    - "01-01-01" → "01.01.01"
    - "01 01 01" → "01.01.01"
    - OCR errors: "O1.01.01" → "01.01.01" (O→0)
  - Usar regex + heurísticas

- [ ] **3.4** Implementar validación WBS
  - Verificar duplicados en WBS (mismo código)
  - Warning si hay códigos inválidos
  - Generar reporte: `WBS_VALIDATION.md`

**Definition of Done:**
- ✅ WBS cargado desde XLSX/CSV
- ✅ Normalización de códigos funcional
- ✅ Validación de duplicados WBS
- ✅ Tests: cargar fixtures WBS con casos edge
- ✅ Documentado en SPEC.md

**Artefactos:**
- `src/ingest/reference_reader.py`
- `src/utils/text_norm.py` (normalize_rubro_code)
- `ReferenceRubro` en `src/models/schemas.py`
- `tests/test_reference.py`
- `tests/fixtures/wbs_example.xlsx`

---

### FASE 4: MATCHING WBS ↔ ET (SEMÁNTICO + FUZZY)

**Objetivo:** Match rubros WBS con rubros detectados en ET usando embeddings + fuzzy.

**Tareas:**

- [ ] **4.1** Implementar `src/match/embedder.py`
  - Modelo: sentence-transformers ("paraphrase-multilingual-MiniLM-L12-v2")
  - Función: `embed_rubros(rubros: List[str]) -> np.ndarray`
  - Cache de embeddings (joblib)
  - Batch processing (para performance)

- [ ] **4.2** Implementar `src/match/matcher.py`
  - Función: `match_wbs_to_et(wbs_rubros, et_rubros, threshold=0.75) -> List[MatchResult]`
  - Estrategia multi-stage:
    1. **Regla dura (código exacto):** Si codigo match → score=1.0
    2. **Fuzzy código:** rapidfuzz (threshold 80) → score=0.9
    3. **Embeddings:** cosine similarity → score variable
    4. **Hybrid:** (fuzzy_desc * 0.3) + (embedding_sim * 0.7)
  - Threshold configurable (default 0.75)

- [ ] **4.3** Implementar FAISS index (opcional, si >1000 rubros)
  - Función: `build_faiss_index(embeddings: np.ndarray) -> faiss.Index`
  - Búsqueda k-NN rápida
  - Solo si len(et_rubros) > 1000

- [ ] **4.4** Definir modelo `MatchResult` (Pydantic)
  ```python
  class MatchResult(BaseModel):
      wbs_rubro_id: str
      et_rubro_id: Optional[str]
      score: float  # 0.0-1.0
      match_type: Literal["exact_code", "fuzzy_code", "semantic", "hybrid", "unmatched"]
      evidence: MatchEvidence

  class MatchEvidence(BaseModel):
      pages: List[int]
      snippet: str  # Max 500 chars
      code_similarity: Optional[float]
      desc_similarity: Optional[float]
      unit_match: bool
  ```

- [ ] **4.5** Implementar `src/match/scoring.py`
  - Función: `calculate_match_confidence(match: MatchResult) -> float`
  - Penalizar si unidad no coincide
  - Boost si código exacto
  - Threshold para ambiguous (0.65-0.75)

- [ ] **4.6** Categorizar resultados
  - **MATCHED (score >= 0.75):** Aceptado
  - **AMBIGUOUS (0.65-0.75):** Revisar manual
  - **UNMATCHED (< 0.65):** No match encontrado

**Definition of Done:**
- ✅ Embeddings generados y cacheados
- ✅ Matching multi-stage implementado
- ✅ FAISS opcional funcional
- ✅ MatchResult con evidencia completa
- ✅ Tests: casos matched/ambiguous/unmatched
- ✅ Documentado en SPEC.md (sección "Matching Semántico")

**Artefactos:**
- `src/match/embedder.py`
- `src/match/matcher.py`
- `src/match/scoring.py`
- `MatchResult` en `src/models/schemas.py`
- `tests/test_match.py`
- Cache embeddings en `data/cache/embeddings/`

---

### FASE 5: EXTRACCIÓN DE RECURSOS LAYOUT-AWARE

**Objetivo:** Extraer materiales/equipos desde ET.json usando estructura de tablas/listas.

**Tareas:**

- [ ] **5.1** Implementar `src/parse/resource_extractor.py`
  - Función: `extract_resources_from_json(et_json: Path, rubro_id: str) -> List[Recurso]`
  - Parse tablas en ET.json (si existe sección "tables")
  - Parse listas con viñetas/numeración
  - Identificar columnas: nombre, unidad, cantidad
  - Fallback: regex en texto plano (método v1.0)

- [ ] **5.2** Clasificación MATERIAL/EQUIPO mejorada
  - Usar embeddings (opcional) para clasificación
  - Keywords ampliados (30+ por categoría)
  - Fuzzy matching (rapidfuzz)
  - Confidence score por recurso

- [ ] **5.3** Trazabilidad de recursos
  - Cada recurso debe tener:
    - `pages: List[int]`
    - `snippet: str` (contexto)
    - `table_id: Optional[str]` (si viene de tabla)
    - `confidence: float`

- [ ] **5.4** Integrar con MatchResult
  - Recursos asociados a rubro matched
  - Si rubro no matcheó, recursos quedan "orphan"

**Definition of Done:**
- ✅ Extracción desde tablas funcional
- ✅ Clasificación mejorada con embeddings (opcional)
- ✅ Trazabilidad completa (page + snippet + table_id)
- ✅ Tests: verificar extracción desde ET.json mock
- ✅ Documentado en SPEC.md

**Artefactos:**
- `src/parse/resource_extractor.py`
- Tests actualizados en `tests/test_parse.py`
- Fixtures: ET.json con tablas

---

### FASE 6: RESOLUCIÓN DE DUPLICADOS Y CONFLICTOS

**Objetivo:** Detectar y resolver rubros duplicados/conflictivos.

**Tareas:**

- [ ] **6.1** Implementar `src/dedupe/dedupe_engine.py`
  - Función: `detect_duplicates(et_rubros: List[ETRubro]) -> List[DuplicateGroup]`
  - Casos:
    1. **Duplicado exacto:** Mismo código, misma unidad → MERGE
    2. **Conflicto:** Mismo código, distinta unidad → SPLIT
    3. **Código ausente:** Sin código detectado → HASH_ID

- [ ] **6.2** Estrategia de merge
  - Función: `merge_exact_duplicates(group: DuplicateGroup) -> ETRubro`
  - Unir recursos de ambos rubros
  - Combinar páginas (union)
  - Promedio de confidence
  - Generar provenance: `merged_from: List[str]`

- [ ] **6.3** Estrategia de split
  - Función: `split_conflicts(group: DuplicateGroup) -> List[ETRubro]`
  - Crear códigos: "01.01.01#A", "01.01.01#B"
  - Marcar con `conflict_flag: True`
  - Incluir ambos en OUT.json

- [ ] **6.4** Código ausente (fallback)
  - Generar ID: `HASH_<sha256[:8]>` basado en descripción
  - Marcar con `code_missing: True`
  - Incluir en warnings

- [ ] **6.5** Definir modelos
  ```python
  class DuplicateGroup(BaseModel):
      group_id: str
      rubros: List[str]  # IDs de rubros duplicados
      duplicate_type: Literal["exact", "conflict", "code_missing"]
      resolution: Literal["merged", "split", "manual"]

  class ConflictRecord(BaseModel):
      original_code: str
      rubros_conflictivos: List[str]
      reason: str  # "unidad_diferente", "descripcion_diferente"
      resolution: str  # "split_as_A_B"
  ```

**Definition of Done:**
- ✅ Duplicados exactos mergeados automáticamente
- ✅ Conflictos splitados con código#A, #B
- ✅ Códigos ausentes con HASH_ID
- ✅ Tests: casos merge/split/hash
- ✅ Documentado en SPEC.md (sección "Dedup & Conflicts")

**Artefactos:**
- `src/dedupe/dedupe_engine.py`
- `DuplicateGroup`, `ConflictRecord` en `src/models/schemas.py`
- `tests/test_dedupe.py`

---

### FASE 7: OUT.json + REPORTES MD (RUN_REPORT + rubros_md)

**Objetivo:** Generar outputs finales estructurados.

**Tareas:**

- [ ] **7.1** Definir esquema `OUT.json`
  ```json
  {
    "metadata": {
      "pdf_filename": "ET_ejemplo.pdf",
      "wbs_filename": "WBS_referencia.xlsx",
      "processing_date": "2026-01-28T10:30:00",
      "conversion_strategy": "docling",
      "match_threshold": 0.75
    },
    "summary": {
      "total_wbs_rubros": 150,
      "total_et_rubros": 145,
      "matched": 130,
      "ambiguous": 10,
      "unmatched": 10,
      "duplicates_merged": 5,
      "conflicts_split": 2
    },
    "matches": [
      {
        "wbs_rubro_id": "WBS_001",
        "et_rubro_id": "RUB_01_01_01_P1",
        "score": 0.95,
        "match_type": "exact_code",
        "evidence": {...},
        "recursos": [...]
      }
    ],
    "duplicates": [...],
    "conflicts": [...],
    "warnings": [...]
  }
  ```

- [ ] **7.2** Implementar `src/report/json_generator.py`
  - Función: `generate_out_json(results: PipelineResults) -> Path`
  - Validar con Pydantic antes de guardar
  - Pretty print (indent=2)

- [ ] **7.3** Implementar `src/report/md_reporter.py`
  - Función: `generate_run_report(results: PipelineResults) -> Path`
  - Contenido RUN_REPORT.md:
    ```markdown
    # RUN REPORT - Pipeline v1.1

    **PDF:** ET_ejemplo.pdf
    **WBS:** WBS_referencia.xlsx
    **Fecha:** 2026-01-28 10:30:00

    ## 📊 Resumen Numérico
    | Métrica | Valor |
    |---------|-------|
    | Rubros WBS | 150 |
    | Rubros ET | 145 |
    | Matched (✅) | 130 |
    | Ambiguous (⚠️) | 10 |
    | Unmatched (❌) | 10 |

    ## 🔄 Duplicados Resueltos
    | Código | Tipo | Resolución |
    |--------|------|------------|
    | 01.01.01 | Exacto | Merged |
    | 02.03.05 | Conflicto | Split (A/B) |

    ## ⚠️ Conflictos Detectados
    | Código | Rubro A | Rubro B | Razón |
    |--------|---------|---------|-------|
    | 03.02.01 | Unidad: m² | Unidad: m³ | Unidad diferente |

    ## 🔴 Top Warnings
    1. [HIGH] Rubro 05.01.02: Código no detectado (Página 15)
    2. [MEDIUM] Rubro 06.03.01: Unidad desconocida "pzs"
    ...
    ```

- [ ] **7.4** Implementar `src/report/rubro_report.py`
  - Función: `generate_rubro_reports(results: PipelineResults) -> Path`
  - Crear `rubros_md/` con un archivo por rubro:
    ```markdown
    # Rubro: 01.01.01 - EXCAVACIÓN MANUAL

    ## 🎯 Match WBS → ET
    - **WBS ID:** WBS_001
    - **ET ID:** RUB_01_01_01_P1
    - **Score:** 0.95 (Exact Code Match)
    - **Unidad:** m³ ✅

    ## 📄 Evidencia
    **Páginas:** 5, 6
    **Snippet:**
    ```
    01.01.01 EXCAVACIÓN MANUAL EN TERRENO NATURAL
    Unidad: m³

    Se realizará excavación manual...
    (líneas 1-30)
    ```

    ## 🔧 Recursos Extraídos
    | Tipo | Nombre | Unidad | Cantidad |
    |------|--------|--------|----------|
    | MATERIAL | Arena gruesa | m³ | 0.5 |
    | EQUIPO | Herramientas manuales | % | 3.0 |

    ## ⚠️ Warnings
    - [LOW] Recurso "Agua" sin unidad especificada
    ```

- [ ] **7.5** Limitar tamaño de reportes
  - Snippet máximo: 30 líneas (truncar si excede)
  - Recursos: máximo 50 por rubro (truncar + warning)
  - RUN_REPORT: máximo 2 pantallas (resumir si excede)

**Definition of Done:**
- ✅ OUT.json generado y validado
- ✅ RUN_REPORT.md con resumen + tablas
- ✅ rubros_md/*.md (1 por rubro)
- ✅ Tamaños limitados (legible)
- ✅ Tests: verificar formato y contenido
- ✅ Documentado en SPEC.md

**Artefactos:**
- `src/report/json_generator.py`
- `src/report/md_reporter.py`
- `src/report/rubro_report.py`
- OUT.json, RUN_REPORT.md, rubros_md/ en `data/artifacts/`
- `tests/test_report.py`

---

### FASE 8: EXPORT EXCEL POR RUBRO CON TEMPLATE

**Objetivo:** Generar Excel con 1 hoja por rubro (modo per-rubro) o hojas globales (fallback).

**Tareas:**

- [ ] **8.1** Crear template default
  - Archivo: `data/templates/rubro_template.xlsx`
  - Estructura de hoja:
    ```
    [Header]
    Código: {codigo}
    Descripción: {descripcion}
    Unidad: {unidad}
    Match Score: {score}

    [Recursos]
    | Tipo | Nombre | Unidad | Cantidad | Confidence |
    |------|--------|--------|----------|------------|
    | ...  | ...    | ...    | ...      | ...        |

    [Warnings]
    | Severity | Message |
    |----------|---------|
    | ...      | ...     |
    ```

- [ ] **8.2** Implementar `src/export/template_exporter.py`
  - Función: `export_per_rubro(results: PipelineResults, template: Path, output: Path)`
  - Crear 1 hoja por rubro
  - Nombre de hoja: `{codigo}` (truncar a 31 chars si excede)
  - Manejo de nombres duplicados: agregar sufijo `_2`, `_3`
  - Usar openpyxl para copiar template y llenar datos

- [ ] **8.3** Implementar fallback mode (global sheets)
  - Si demasiados rubros (>100) o error en per-rubro
  - Usar lógica v1.0: 5 hojas (Resumen, Rubros, Recursos, Relaciones, Warnings)

- [ ] **8.4** Validación de nombres de hoja
  - Excel limita nombres a 31 caracteres
  - Caracteres inválidos: \ / ? * [ ]
  - Función: `sanitize_sheet_name(name: str) -> str`
  - Truncar + sanitizar + deduplicar

- [ ] **8.5** Configurar export mode
  - CLI flag: `--export-mode per-rubro|global|auto`
  - Auto: per-rubro si <=100 rubros, global si >100
  - Guardar en settings

**Definition of Done:**
- ✅ Template rubro_template.xlsx creado
- ✅ Export per-rubro funcional
- ✅ Fallback global funcional
- ✅ Nombres de hoja sanitizados (<=31 chars)
- ✅ Tests: verificar ambos modos
- ✅ Documentado en SPEC.md

**Artefactos:**
- `data/templates/rubro_template.xlsx`
- `src/export/template_exporter.py`
- `tests/test_export_template.py`
- Excel generado en `data/output/`

---

### FASE 9: TESTS NUEVOS + FIXTURES + VERIFICACIÓN

**Objetivo:** Asegurar calidad con tests completos y fixtures.

**Tareas:**

- [ ] **9.1** Crear fixtures
  - `tests/fixtures/pdf_synthetic.pdf` (generado con reportlab)
  - `tests/fixtures/wbs_example.xlsx` (15 rubros de ejemplo)
  - `tests/fixtures/et_mock.json` (estructura simulada)
  - `tests/fixtures/et_mock.md` (markdown de ejemplo)

- [ ] **9.2** Tests de conversión
  - `test_docling_converter()` (mock, verificar output)
  - `test_marker_fallback()` (simular fallo Docling)
  - `test_converter_router_auto()` (verificar cascade)

- [ ] **9.3** Tests de normalización
  - `test_normalize_codigo_variants()` (1.1.1 → 01.01.01)
  - `test_normalize_codigo_ocr_errors()` (O1 → 01, l → 1)
  - `test_normalize_unidad()` (ampliar casos v1.0)

- [ ] **9.4** Tests de matching
  - `test_exact_code_match()` (score=1.0)
  - `test_fuzzy_match()` (score ~0.9)
  - `test_semantic_match()` (embeddings)
  - `test_ambiguous_match()` (score 0.65-0.75)
  - `test_unmatched()` (score <0.65)

- [ ] **9.5** Tests de deduplicación
  - `test_merge_exact_duplicates()` (merge automático)
  - `test_split_conflicts()` (código#A, código#B)
  - `test_code_missing_hash()` (HASH_ID generado)

- [ ] **9.6** Tests de export per-rubro
  - `test_sanitize_sheet_name()` (31 chars, caracteres inválidos)
  - `test_export_per_rubro_mode()` (verificar hojas creadas)
  - `test_export_global_fallback()` (>100 rubros)

- [ ] **9.7** Tests de reportes MD
  - `test_run_report_generation()` (estructura correcta)
  - `test_rubro_report_generation()` (snippet truncado)
  - `test_out_json_schema()` (validar con Pydantic)

- [ ] **9.8** Comandos de verificación
  ```bash
  # Tests completos
  pytest tests/ -v --cov=src --cov-report=html

  # Tests rápidos (sin embeddings/OCR)
  pytest tests/ -v -m "not slow"

  # Tests de integración
  pytest tests/ -v -m integration

  # Smoke test v1.1
  pytest tests/test_smoke_v1.1.py -v
  ```

**Definition of Done:**
- ✅ Fixtures creados (PDF, WBS, ET.json mock)
- ✅ 30+ tests nuevos implementados
- ✅ Coverage >80% en módulos nuevos
- ✅ Comandos de verificación documentados
- ✅ CI/CD compatible (GitHub Actions opcional)

**Artefactos:**
- `tests/fixtures/*.{pdf,xlsx,json,md}`
- `tests/test_convert.py`
- `tests/test_match.py`
- `tests/test_dedupe.py`
- `tests/test_export_template.py`
- `tests/test_report.py`
- `tests/test_smoke_v1.1.py`

---

### FASE 10: CLI/NOTEBOOK + DOCS (README/SPEC)

**Objetivo:** Actualizar interfaces de usuario y documentación completa.

**Tareas:**

- [ ] **10.1** Actualizar CLI en `src/pipeline.py`
  - Agregar argumentos:
    ```bash
    python src/pipeline.py input.pdf \
      --mode advanced \
      --reference wbs.xlsx \
      --export-mode per-rubro \
      --write-artifacts true \
      --match-threshold 0.75 \
      --conversion-strategy auto
    ```
  - Mantener compatibilidad v1.0 (--mode legacy)

- [ ] **10.2** Actualizar notebook `notebooks/pipeline_example.ipynb`
  - Agregar sección "Advanced Path (v1.1)"
  - Ejemplos:
    - Conversión con Docling
    - Matching WBS ↔ ET
    - Visualización de matches (tabla con Rich)
    - Inspección de conflictos
    - Abrir rubros_md para debugging
  - Gráficos (opcional): distribución de scores, recursos por tipo

- [ ] **10.3** Crear nuevo notebook `notebooks/advanced_example.ipynb`
  - Foco en features v1.1
  - Ejemplo completo: PDF + WBS → OUT.json
  - Análisis de RUN_REPORT.md
  - Comparación legacy vs advanced

- [ ] **10.4** Actualizar SPEC.md
  - Sección nueva: "Advanced Conversion Path"
    - Docling/Marker/PyMuPDF4LLM (features, pros/cons)
    - ConversionResult schema
    - Estrategia auto
  - Sección nueva: "Matching Semántico WBS↔ET"
    - Multi-stage matching
    - Embeddings (modelo, caching)
    - Scoring (thresholds, penalizaciones)
    - MatchResult schema
  - Sección nueva: "Dedup & Conflicts"
    - 3 casos: exact, conflict, code_missing
    - Estrategias merge/split/hash
  - Sección nueva: "Artifacts v1.1"
    - ET.md, ET.json, OUTLINE.md, OUT.json
    - RUN_REPORT.md, rubros_md/
  - Sección nueva: "Excel Template Mode"
    - Per-rubro vs global
    - Sanitización de nombres de hoja

- [ ] **10.5** Crear ARCHITECTURE.md
  - Diagrama de módulos (ASCII art)
  - Dataflow: PDF → Conversión → Outline → Match → Dedupe → Reportes → Excel
  - Legacy vs Advanced path (comparación)
  - Modelos Pydantic (lista completa)

- [ ] **10.6** Actualizar README.md
  - Agregar "Quick Start v1.1"
  - Features nuevas destacadas
  - Ejemplos de uso advanced mode
  - Árbol de carpetas actualizado

- [ ] **10.7** Actualizar QUICKSTART.md
  - Comando rápido v1.1:
    ```bash
    python src/pipeline.py input.pdf \
      --mode advanced \
      --reference wbs.xlsx
    ```

**Definition of Done:**
- ✅ CLI con flags v1.1 funcional
- ✅ Notebook actualizado con ejemplos advanced
- ✅ SPEC.md con 5 secciones nuevas
- ✅ ARCHITECTURE.md creado con diagramas
- ✅ README/QUICKSTART actualizados
- ✅ Documentación revisada y consistente

**Artefactos:**
- `src/pipeline.py` (CLI actualizado)
- `notebooks/pipeline_example.ipynb` (actualizado)
- `notebooks/advanced_example.ipynb` (nuevo)
- `ARCHITECTURE.md` (nuevo)
- `SPEC.md` (actualizado)
- `README.md` (actualizado)
- `QUICKSTART.md` (actualizado)

---

## 📊 RESUMEN DE ENTREGABLES FINALES

| Artefacto | Ubicación | Descripción |
|-----------|-----------|-------------|
| **ET.md** | `data/artifacts/` | Markdown fiel al PDF (inspección humana) |
| **ET.json** | `data/artifacts/` | Estructura del documento (secciones, tablas, bloques) |
| **OUTLINE.md** | `data/artifacts/` | Jerarquía Página → Sección → Rubro |
| **OUT.json** | `data/artifacts/` | JSON puente final (matches + recursos + warnings) |
| **RUN_REPORT.md** | `data/artifacts/` | Reporte de ejecución (resumen + conflictos) |
| **rubros_md/** | `data/artifacts/rubros_md/` | 1 archivo MD por rubro (evidencia + recursos) |
| **resultado.xlsx** | `data/output/` | Excel (per-rubro o global) |

---

## 🎯 MÉTRICAS DE ÉXITO

| Métrica | Target | Validación |
|---------|--------|------------|
| **Conversión exitosa** | >95% PDFs | Test con 20 PDFs reales |
| **Match accuracy** | >90% rubros | Comparación manual 50 rubros |
| **Dedup precision** | 100% merge exactos | Test unitario |
| **Conflict detection** | >95% conflictos reales | Revisión manual |
| **Test coverage** | >80% módulos nuevos | pytest-cov |
| **Performance** | <5min por PDF (50 páginas) | Benchmark |
| **Usabilidad** | CLI + Notebook ejecutable sin errores | Smoke test |

---

## 🚨 RIESGOS Y MITIGACIONES

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Docling no instala en Windows | Alto | Fallback a Marker + PyMuPDF4LLM |
| Embeddings muy lentos | Medio | Cache + FAISS + batch processing |
| OCR con bajo confidence | Alto | Múltiples conversores + threshold ajustable |
| Nombres de hoja Excel >31 chars | Bajo | Sanitización automática + truncado |
| Conflictos no detectados | Medio | Tests exhaustivos + revisión manual |
| Template Excel corrupto | Bajo | Validación + fallback a global mode |

---

## 📅 ESTIMACIÓN DE TIEMPO

| Fase | Complejidad | Tiempo estimado | Dependencias |
|------|-------------|-----------------|--------------|
| Fase 0 | Baja | 2h | - |
| Fase 1 | Alta | 8h | Fase 0 |
| Fase 2 | Media | 4h | Fase 1 |
| Fase 3 | Baja | 3h | Fase 0 |
| Fase 4 | Alta | 10h | Fase 3 |
| Fase 5 | Media | 6h | Fase 1, 4 |
| Fase 6 | Media | 5h | Fase 4 |
| Fase 7 | Media | 6h | Fase 6 |
| Fase 8 | Media | 5h | Fase 7 |
| Fase 9 | Media | 8h | Todas |
| Fase 10 | Baja | 4h | Fase 9 |
| **TOTAL** | - | **~60h** | - |

---

## ✅ CHECKLIST DE ACEPTACIÓN

### Funcionalidades Core v1.1

- [ ] Conversión estructurada con Docling/Marker/PyMuPDF4LLM
- [ ] Generación de ET.md + ET.json + OUTLINE.md
- [ ] Carga de WBS reference (XLSX/CSV)
- [ ] Matching semántico WBS ↔ ET (embeddings + fuzzy)
- [ ] Extracción de recursos layout-aware desde tablas
- [ ] Resolución de duplicados (merge/split/hash)
- [ ] Generación de OUT.json + RUN_REPORT.md + rubros_md/
- [ ] Export Excel per-rubro con template
- [ ] Export Excel global (fallback)
- [ ] CLI con flags v1.1
- [ ] Notebook con ejemplos advanced

### Calidad

- [ ] Tests >30 nuevos (conversión, match, dedupe, export)
- [ ] Coverage >80% en módulos nuevos
- [ ] Smoke test v1.1 passing
- [ ] Fixtures creados (PDF, WBS, ET.json)
- [ ] Documentación completa (SPEC, ARCHITECTURE, README)

### Performance

- [ ] Procesamiento <5min por PDF de 50 páginas
- [ ] Cache de embeddings funcional
- [ ] No memory leaks en batch processing

### Usabilidad

- [ ] CLI ejecutable sin errores
- [ ] Notebook ejecutable sin errores
- [ ] Reportes MD legibles (<=2 pantallas)
- [ ] Excel abre sin warnings

---

**FIN DEL PLAN DE ACCIÓN v1.1**

---

## 🚀 PRÓXIMO PASO

**Ejecutar Fase 0:** Auditoría + Setup inicial

```bash
# 1. Crear estructura de carpetas
mkdir -p src/{convert,outline,match,dedupe,report,config}
mkdir -p data/{templates,artifacts/rubros_md}
mkdir -p tests/fixtures

# 2. Instalar dependencias
pip install -r requirements-full.txt

# 3. Verificar estado
pytest tests/test_smoke.py -v
```
