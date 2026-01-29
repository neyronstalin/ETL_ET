# 🗂️ ESTRUCTURA DE CARPETAS v1.1

**Proyecto:** ETL_ET - Pipeline Extracción PDF Advanced
**Estado:** En desarrollo (Fase 0 completada)

---

## 📂 Árbol Completo del Proyecto

```
ETL_ET/
├── .env.example                       # Template de variables de entorno
├── .gitignore                         # Archivos ignorados por git
├── README.md                          # Documentación principal
├── README_INSTALL.md                  # Guía detallada de instalación
├── QUICKSTART.md                      # Guía rápida 5 minutos
├── SETUP.md                           # Setup paso a paso
├── SPEC.md                            # Especificación técnica completa
├── PLAN_V1.1.md                       # Plan de acción v1.1 (10 fases)
├── ARCHITECTURE.md                    # [TODO Fase 10] Arquitectura + diagramas
├── pytest.ini                         # Configuración pytest
├── requirements.txt                   # Dependencias v1.0 (legacy)
├── requirements-minimal.txt           # Dependencias mínimas (sin embeddings)
├── requirements-full.txt              # Dependencias completas v1.1
│
├── data/                              # Datos y artefactos
│   ├── input/                         # PDFs de entrada
│   │   └── .gitkeep
│   ├── output/                        # Excel generados
│   │   └── .gitkeep
│   ├── cache/                         # Cache OCR + embeddings
│   │   ├── embeddings/                # [TODO Fase 4] Cache sentence-transformers
│   │   └── .gitkeep
│   ├── templates/                     # Templates Excel
│   │   └── rubro_template.xlsx        # [TODO Fase 8] Template por rubro
│   └── artifacts/                     # [NEW v1.1] Artefactos generados
│       ├── ET.md                      # [TODO Fase 1] Markdown del PDF
│       ├── ET.json                    # [TODO Fase 1] JSON estructurado
│       ├── OUTLINE.md                 # [TODO Fase 2] Outline jerárquico
│       ├── OUT.json                   # [TODO Fase 7] JSON puente final
│       ├── RUN_REPORT.md              # [TODO Fase 7] Reporte de ejecución
│       ├── WBS_VALIDATION.md          # [TODO Fase 3] Validación WBS
│       └── rubros_md/                 # [TODO Fase 7] Reportes por rubro
│           ├── RUB_01_01_01.md
│           ├── RUB_01_01_02.md
│           └── ...
│
├── notebooks/                         # Jupyter notebooks
│   ├── pipeline_example.ipynb         # Ejemplos v1.0 + v1.1
│   └── advanced_example.ipynb         # [TODO Fase 10] Solo v1.1
│
├── src/                               # Código fuente
│   ├── __init__.py
│   │
│   ├── config/                        # [NEW v1.1] Configuración
│   │   ├── __init__.py
│   │   └── settings.py                # [TODO Fase 0] Pydantic Settings
│   │
│   ├── convert/                       # [NEW v1.1] Conversión estructurada
│   │   ├── __init__.py
│   │   ├── docling_converter.py       # [TODO Fase 1] Docling
│   │   ├── marker_converter.py        # [TODO Fase 1] Marker
│   │   ├── pymupdf_converter.py       # [TODO Fase 1] PyMuPDF4LLM
│   │   └── converter_router.py        # [TODO Fase 1] Router auto
│   │
│   ├── outline/                       # [NEW v1.1] Outline jerárquico
│   │   ├── __init__.py
│   │   └── outline_builder.py         # [TODO Fase 2] Builder + MD generator
│   │
│   ├── ingest/                        # Ingesta de datos
│   │   ├── __init__.py
│   │   ├── pdf_reader.py              # [v1.0] Lector PDF básico
│   │   └── reference_reader.py        # [TODO Fase 3] Lector WBS reference
│   │
│   ├── ocr/                           # OCR
│   │   ├── __init__.py
│   │   └── tesseract_ocr.py           # [v1.0] Tesseract/EasyOCR
│   │
│   ├── parse/                         # Parseo y extracción
│   │   ├── __init__.py
│   │   ├── rubro_parser.py            # [v1.0] Parser básico regex
│   │   └── resource_extractor.py      # [TODO Fase 5] Extracción layout-aware
│   │
│   ├── match/                         # [NEW v1.1] Matching semántico
│   │   ├── __init__.py
│   │   ├── embedder.py                # [TODO Fase 4] Sentence Transformers
│   │   ├── matcher.py                 # [TODO Fase 4] Matching WBS ↔ ET
│   │   └── scoring.py                 # [TODO Fase 4] Cálculo de scores
│   │
│   ├── dedupe/                        # [NEW v1.1] Deduplicación
│   │   ├── __init__.py
│   │   └── dedupe_engine.py           # [TODO Fase 6] Merge/Split/Hash
│   │
│   ├── report/                        # [NEW v1.1] Reportes MD + JSON
│   │   ├── __init__.py
│   │   ├── json_generator.py          # [TODO Fase 7] OUT.json generator
│   │   ├── md_reporter.py             # [TODO Fase 7] RUN_REPORT.md
│   │   └── rubro_report.py            # [TODO Fase 7] rubros_md/*.md
│   │
│   ├── export/                        # Export a Excel
│   │   ├── __init__.py
│   │   ├── excel_exporter.py          # [v1.0] Export 5 hojas global
│   │   └── template_exporter.py       # [TODO Fase 8] Export per-rubro
│   │
│   ├── models/                        # Modelos Pydantic
│   │   ├── __init__.py
│   │   └── schemas.py                 # [v1.0 + TODO ampliar v1.1]
│   │       # Modelos v1.0:
│   │       #   - Rubro, Recurso, ParseWarning
│   │       #   - TipoRecurso, TipoDocumento, WarningKind
│   │       #   - PageMetadata, DocumentMetadata, PipelineResult
│   │       # Modelos v1.1 (TODO):
│   │       #   - ConversionResult [Fase 1]
│   │       #   - OutlineStructure, OutlineNode [Fase 2]
│   │       #   - ReferenceRubro [Fase 3]
│   │       #   - ETRubro [Fase 3]
│   │       #   - MatchResult, MatchEvidence [Fase 4]
│   │       #   - DuplicateGroup, ConflictRecord [Fase 6]
│   │       #   - PipelineArtifacts [Fase 7]
│   │
│   ├── utils/                         # Utilidades
│   │   ├── __init__.py
│   │   ├── logger.py                  # [v1.0] Structlog
│   │   └── text_norm.py               # [TODO Fase 3] Normalización de texto
│   │
│   └── pipeline.py                    # [v1.0 + TODO extender v1.1] Orchestrator
│       # Legacy mode (v1.0)
│       # Advanced mode (v1.1) [TODO Fase 10]
│
└── tests/                             # Tests
    ├── __init__.py
    │
    ├── fixtures/                      # [TODO Fase 9] Fixtures sintéticos
    │   ├── pdf_synthetic.pdf          # PDF generado con reportlab
    │   ├── wbs_example.xlsx           # WBS de referencia
    │   ├── et_mock.json               # ET.json simulado
    │   └── et_mock.md                 # ET.md simulado
    │
    ├── test_smoke.py                  # [v1.0] Tests básicos
    ├── test_smoke_v1.1.py             # [TODO Fase 9] Tests v1.1
    ├── test_parse.py                  # [v1.0] Tests parseo
    ├── test_convert.py                # [TODO Fase 9] Tests conversión
    ├── test_match.py                  # [TODO Fase 9] Tests matching
    ├── test_dedupe.py                 # [TODO Fase 9] Tests deduplicación
    ├── test_export_template.py        # [TODO Fase 9] Tests export per-rubro
    └── test_report.py                 # [TODO Fase 9] Tests reportes MD

```

---

## 📊 ESTADÍSTICAS

| Categoría | v1.0 (Actual) | v1.1 (Target) |
|-----------|---------------|---------------|
| **Módulos** | 6 | 13 |
| **Archivos .py** | 8 | 23 |
| **Tests** | 2 | 9 |
| **Fixtures** | 0 | 4 |
| **Docs** | 4 | 8 |
| **Total líneas código** | ~3,000 | ~8,000+ |

---

## 🔑 MÓDULOS CLAVE (v1.1)

### 1. **src/convert/** (Conversión Estructurada)

**Responsabilidad:** Convertir PDF → ET.md + ET.json con estructura jerárquica.

**Archivos:**
- `docling_converter.py`: Conversión con Docling (IBM, primario)
- `marker_converter.py`: Conversión con Marker (fallback)
- `pymupdf_converter.py`: Conversión rápida PyMuPDF4LLM (fallback 2)
- `converter_router.py`: Selección automática de conversor

**Output:**
- `ET.md`: Markdown fiel al documento
- `ET.json`: Estructura JSON (secciones, tablas, bloques, páginas)

---

### 2. **src/match/** (Matching Semántico)

**Responsabilidad:** Match rubros WBS ↔ ET usando embeddings + fuzzy.

**Archivos:**
- `embedder.py`: Generación de embeddings (sentence-transformers)
- `matcher.py`: Matching multi-stage (código exacto → fuzzy → semántico)
- `scoring.py`: Cálculo de scores y confidence

**Estrategia:**
1. Regla dura (código exacto) → score=1.0
2. Fuzzy código (rapidfuzz >80) → score=0.9
3. Embeddings (cosine sim) → score variable
4. Hybrid scoring

**Categorías:**
- MATCHED (≥0.75)
- AMBIGUOUS (0.65-0.75)
- UNMATCHED (<0.65)

---

### 3. **src/dedupe/** (Deduplicación)

**Responsabilidad:** Detectar y resolver rubros duplicados/conflictivos.

**Archivo:**
- `dedupe_engine.py`: Detección + resolución

**Casos:**
1. **Duplicado exacto** (mismo código, misma unidad) → MERGE
2. **Conflicto** (mismo código, distinta unidad) → SPLIT (código#A, #B)
3. **Código ausente** → HASH_ID (HASH_sha256[:8])

---

### 4. **src/report/** (Reportes MD + JSON)

**Responsabilidad:** Generar outputs estructurados finales.

**Archivos:**
- `json_generator.py`: OUT.json (matches + recursos + warnings)
- `md_reporter.py`: RUN_REPORT.md (resumen + tablas conflictos)
- `rubro_report.py`: rubros_md/*.md (1 por rubro)

**Formato RUN_REPORT.md:**
- Resumen numérico (matched/ambiguous/unmatched)
- Tabla de duplicados resueltos
- Tabla de conflictos
- Top warnings por severidad

---

### 5. **src/export/template_exporter.py** (Excel per-rubro)

**Responsabilidad:** Generar Excel con 1 hoja por rubro.

**Features:**
- Template `rubro_template.xlsx` (estructura predefinida)
- Nombres de hoja sanitizados (<=31 chars, sin caracteres inválidos)
- Fallback a modo global si >100 rubros

---

## 🔄 DATAFLOW v1.1

```
┌─────────┐
│   PDF   │
└────┬────┘
     │
     ▼
┌──────────────────┐
│ 1. CONVERSIÓN    │  convert/converter_router.py
│ Docling/Marker   │  → ET.md, ET.json
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 2. OUTLINE       │  outline/outline_builder.py
│ Build hierarchy  │  → OUTLINE.md
└────┬─────────────┘
     │
     ├─────────────────┐
     ▼                 ▼
┌──────────┐    ┌────────────┐
│ 3a. WBS  │    │ 3b. ET     │
│ Reference│    │ Rubros     │
└────┬─────┘    └────┬───────┘
     │               │
     └───────┬───────┘
             ▼
     ┌──────────────────┐
     │ 4. MATCHING      │  match/matcher.py
     │ WBS ↔ ET         │  → MatchResult[]
     └────┬─────────────┘
          │
          ▼
     ┌──────────────────┐
     │ 5. RECURSOS      │  parse/resource_extractor.py
     │ Extract          │  → Recurso[]
     └────┬─────────────┘
          │
          ▼
     ┌──────────────────┐
     │ 6. DEDUPE        │  dedupe/dedupe_engine.py
     │ Merge/Split/Hash │  → DuplicateGroup[]
     └────┬─────────────┘
          │
          ├───────────────┬──────────────┐
          ▼               ▼              ▼
     ┌──────────┐  ┌──────────┐  ┌───────────┐
     │ OUT.json │  │ RUN_     │  │ rubros_md/│
     │          │  │ REPORT   │  │ *.md      │
     └──────────┘  └──────────┘  └───────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Excel        │
                  │ (per-rubro   │
                  │  o global)   │
                  └──────────────┘
```

---

## 🎯 PRÓXIMOS PASOS

**Fase 0 (Completada):**
- ✅ Estructura de carpetas creada
- ✅ requirements-full.txt / requirements-minimal.txt
- ✅ README_INSTALL.md con guías

**Fase 1 (Siguiente):**
- [ ] Implementar `src/convert/docling_converter.py`
- [ ] Implementar `src/convert/marker_converter.py`
- [ ] Implementar `src/convert/pymupdf_converter.py`
- [ ] Implementar `src/convert/converter_router.py`
- [ ] Definir modelo `ConversionResult` en schemas.py
- [ ] Tests: `tests/test_convert.py`

Ver [PLAN_V1.1.md](PLAN_V1.1.md) para detalles completos.

---

**Última actualización:** 2026-01-28
**Estado:** Fase 0 completada, listo para Fase 1
