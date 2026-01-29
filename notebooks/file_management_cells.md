# 📁 CELDAS DE GESTIÓN DE ARCHIVOS PARA NOTEBOOK

**Para agregar a:** `notebooks/pipeline_example.ipynb`
**Ubicación:** Después de imports, antes de "Ejemplo Básico"

---

## 🎯 CELDA 1: GESTIÓN DE DIRECTORIO INPUT

```python
# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ARCHIVOS - PASO 1: Limpiar y preparar directorio
# ═══════════════════════════════════════════════════════════════════════════

import os
from pathlib import Path
import shutil
from IPython.display import display, HTML

# Directorio de trabajo
INPUT_DIR = Path("data/input")
OUTPUT_DIR = Path("data/output")

# Crear directorios si no existen
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def listar_pdfs_input():
    """Lista PDFs en data/input/"""
    pdfs = list(INPUT_DIR.glob("*.pdf"))
    if pdfs:
        print(f"📂 PDFs en {INPUT_DIR}:")
        for idx, pdf in enumerate(pdfs, 1):
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  {idx}. {pdf.name} ({size_mb:.2f} MB)")
        return pdfs
    else:
        print(f"📂 {INPUT_DIR} está vacío (no hay PDFs)")
        return []

def limpiar_input_dir(confirmar=True):
    """Limpia todos los PDFs de data/input/"""
    pdfs = list(INPUT_DIR.glob("*.pdf"))

    if not pdfs:
        print("✓ Directorio ya está vacío")
        return

    if confirmar:
        print(f"⚠️  Se eliminarán {len(pdfs)} archivo(s):")
        for pdf in pdfs:
            print(f"   - {pdf.name}")

        respuesta = input("\n¿Continuar? (s/N): ").strip().lower()
        if respuesta not in ['s', 'si', 'sí', 'yes', 'y']:
            print("❌ Cancelado")
            return

    # Eliminar archivos
    for pdf in pdfs:
        pdf.unlink()
        print(f"   🗑️  Eliminado: {pdf.name}")

    print(f"✅ Directorio {INPUT_DIR} limpiado")

def limpiar_output_dir(confirmar=True):
    """Limpia archivos de data/output/"""
    archivos = list(OUTPUT_DIR.glob("*.xlsx")) + list(OUTPUT_DIR.glob("*.csv"))

    if not archivos:
        print("✓ Directorio output ya está vacío")
        return

    if confirmar:
        print(f"⚠️  Se eliminarán {len(archivos)} archivo(s) de output:")
        for archivo in archivos:
            print(f"   - {archivo.name}")

        respuesta = input("\n¿Continuar? (s/N): ").strip().lower()
        if respuesta not in ['s', 'si', 'sí', 'yes', 'y']:
            print("❌ Cancelado")
            return

    for archivo in archivos:
        archivo.unlink()
        print(f"   🗑️  Eliminado: {archivo.name}")

    print(f"✅ Directorio {OUTPUT_DIR} limpiado")

# Mostrar estado actual
print("📊 ESTADO ACTUAL")
print("=" * 60)
listar_pdfs_input()
print()

# Opciones de limpieza (descomentarlas si necesitas limpiar)
# limpiar_input_dir(confirmar=True)
# limpiar_output_dir(confirmar=True)
```

---

## 🎯 CELDA 2A: UPLOAD DE PDF (CON WIDGET - RECOMENDADO)

```python
# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ARCHIVOS - PASO 2A: Upload PDF con Widget
# ═══════════════════════════════════════════════════════════════════════════

from ipywidgets import FileUpload, Button, Output, VBox, HBox, Label
from IPython.display import display, clear_output
import ipywidgets as widgets

# Widget de upload
upload_widget = FileUpload(
    accept='.pdf',
    multiple=False,
    description='Seleccionar PDF:',
    button_style='primary'
)

# Output para mensajes
output_area = Output()

# Estado
uploaded_file_path = None

def on_upload_change(change):
    """Callback cuando se sube un archivo"""
    global uploaded_file_path

    with output_area:
        clear_output()

        # Verificar que se subió algo
        if not upload_widget.value:
            print("❌ No se seleccionó archivo")
            return

        # Obtener archivo subido
        uploaded_file = list(upload_widget.value.values())[0]
        filename = uploaded_file['metadata']['name']
        content = uploaded_file['content']

        print(f"📄 Archivo seleccionado: {filename}")
        print(f"   Tamaño: {len(content) / (1024*1024):.2f} MB")

        # Validar extensión
        if not filename.lower().endswith('.pdf'):
            print("❌ Error: Solo se permiten archivos PDF")
            return

        # Guardar en data/input/
        file_path = INPUT_DIR / filename

        # Si ya existe, preguntar
        if file_path.exists():
            print(f"⚠️  Archivo '{filename}' ya existe en {INPUT_DIR}")
            print("   Se sobrescribirá...")

        # Escribir archivo
        with open(file_path, 'wb') as f:
            f.write(content)

        uploaded_file_path = file_path

        print(f"✅ Guardado en: {file_path}")
        print(f"✅ Listo para procesar")

        # Mostrar PDFs actuales
        print()
        listar_pdfs_input()

# Conectar callback
upload_widget.observe(on_upload_change, names='value')

# Botón de limpiar
btn_limpiar = Button(
    description='🗑️ Limpiar Input',
    button_style='warning',
    tooltip='Eliminar todos los PDFs de data/input/'
)

def on_limpiar_click(b):
    with output_area:
        clear_output()
        limpiar_input_dir(confirmar=False)
        print()
        listar_pdfs_input()

btn_limpiar.on_click(on_limpiar_click)

# Mostrar UI
print("📤 UPLOAD DE PDF")
print("=" * 60)
print()
display(VBox([
    HBox([upload_widget, btn_limpiar]),
    output_area
]))

print()
print("💡 Instrucciones:")
print("   1. Click en 'Seleccionar PDF' y elige tu archivo")
print("   2. El archivo se guardará automáticamente en data/input/")
print("   3. Usa '🗑️ Limpiar Input' para eliminar archivos previos")
```

---

## 🎯 CELDA 2B: UPLOAD MANUAL (SIN WIDGET - ALTERNATIVA)

```python
# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ARCHIVOS - PASO 2B: Upload manual (alternativa sin widget)
# ═══════════════════════════════════════════════════════════════════════════

# OPCIÓN 1: Copiar archivo existente desde otra ubicación
def copiar_pdf_desde(source_path: str, nuevo_nombre: str = None):
    """
    Copia un PDF desde otra ubicación a data/input/

    Args:
        source_path: Ruta al PDF original
        nuevo_nombre: Nombre opcional para el archivo (si None, usa nombre original)
    """
    source = Path(source_path)

    if not source.exists():
        print(f"❌ Archivo no encontrado: {source_path}")
        return None

    if not source.suffix.lower() == '.pdf':
        print(f"❌ No es un PDF: {source_path}")
        return None

    # Determinar nombre destino
    dest_name = nuevo_nombre if nuevo_nombre else source.name
    dest_path = INPUT_DIR / dest_name

    # Copiar
    shutil.copy2(source, dest_path)
    size_mb = dest_path.stat().st_size / (1024 * 1024)

    print(f"✅ Copiado: {source.name}")
    print(f"   → Destino: {dest_path}")
    print(f"   → Tamaño: {size_mb:.2f} MB")

    return dest_path

# OPCIÓN 2: Renombrar PDF existente en input/
def renombrar_pdf_input(nombre_actual: str, nombre_nuevo: str):
    """Renombra un PDF en data/input/"""
    actual = INPUT_DIR / nombre_actual
    nuevo = INPUT_DIR / nombre_nuevo

    if not actual.exists():
        print(f"❌ Archivo no encontrado: {nombre_actual}")
        listar_pdfs_input()
        return None

    if nuevo.exists():
        print(f"⚠️  '{nombre_nuevo}' ya existe. ¿Sobrescribir?")
        respuesta = input("(s/N): ").strip().lower()
        if respuesta not in ['s', 'si', 'sí', 'yes', 'y']:
            print("❌ Cancelado")
            return None
        nuevo.unlink()

    actual.rename(nuevo)
    print(f"✅ Renombrado: {nombre_actual} → {nombre_nuevo}")
    return nuevo

# EJEMPLO DE USO:
print("📁 GESTIÓN MANUAL DE ARCHIVOS")
print("=" * 60)
print()

# Ejemplo 1: Copiar desde otra ubicación
# copiar_pdf_desde("/ruta/a/mi_pdf.pdf", nuevo_nombre="especificaciones.pdf")

# Ejemplo 2: Renombrar archivo existente
# renombrar_pdf_input("archivo_viejo.pdf", "especificaciones.pdf")

# Mostrar estado
listar_pdfs_input()

print()
print("💡 Funciones disponibles:")
print("   • copiar_pdf_desde(ruta, nuevo_nombre=None)")
print("   • renombrar_pdf_input(nombre_actual, nombre_nuevo)")
print("   • limpiar_input_dir(confirmar=True)")
```

---

## 🎯 CELDA 3: SELECCIÓN DE PDF PARA PROCESAR

```python
# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ARCHIVOS - PASO 3: Seleccionar PDF a procesar
# ═══════════════════════════════════════════════════════════════════════════

def seleccionar_pdf_input():
    """
    Permite seleccionar interactivamente un PDF de data/input/

    Returns:
        Path al PDF seleccionado o None
    """
    pdfs = listar_pdfs_input()

    if not pdfs:
        print()
        print("❌ No hay PDFs disponibles")
        print("   → Usa la celda anterior para subir un PDF")
        return None

    if len(pdfs) == 1:
        print()
        print(f"✅ Único PDF disponible: {pdfs[0].name}")
        return pdfs[0]

    # Múltiples PDFs: pedir selección
    print()
    print("Selecciona un PDF (ingresa el número):")

    while True:
        try:
            seleccion = input("Número [1]: ").strip()

            if not seleccion:
                seleccion = "1"

            idx = int(seleccion) - 1

            if 0 <= idx < len(pdfs):
                pdf_seleccionado = pdfs[idx]
                print(f"✅ Seleccionado: {pdf_seleccionado.name}")
                return pdf_seleccionado
            else:
                print(f"❌ Número inválido. Debe estar entre 1 y {len(pdfs)}")

        except ValueError:
            print("❌ Ingresa un número válido")
        except KeyboardInterrupt:
            print("\n❌ Cancelado")
            return None

# Seleccionar PDF
PDF_INPUT = seleccionar_pdf_input()

if PDF_INPUT:
    print()
    print("📄 PDF SELECCIONADO PARA PROCESAR:")
    print("=" * 60)
    print(f"   Archivo: {PDF_INPUT.name}")
    print(f"   Ruta:    {PDF_INPUT}")
    print(f"   Tamaño:  {PDF_INPUT.stat().st_size / (1024*1024):.2f} MB")
    print()
    print("✅ Listo para ejecutar pipeline")
else:
    print()
    print("⚠️  No se seleccionó PDF. Ejecuta las celdas anteriores para cargar uno.")
```

---

## 🎯 CELDA 4: CONFIGURAR OUTPUT (OPCIONAL)

```python
# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ARCHIVOS - PASO 4: Configurar nombre de salida
# ═══════════════════════════════════════════════════════════════════════════

# Generar nombre de salida automático
if PDF_INPUT:
    # Opción 1: Mismo nombre + "_resultado"
    OUTPUT_NOMBRE = PDF_INPUT.stem + "_resultado.xlsx"

    # Opción 2: Nombre personalizado
    # OUTPUT_NOMBRE = "mi_resultado_personalizado.xlsx"

    OUTPUT_PATH = OUTPUT_DIR / OUTPUT_NOMBRE

    print("📊 CONFIGURACIÓN DE SALIDA")
    print("=" * 60)
    print(f"   Input:  {PDF_INPUT.name}")
    print(f"   Output: {OUTPUT_NOMBRE}")
    print(f"   Ruta:   {OUTPUT_PATH}")
    print()

    if OUTPUT_PATH.exists():
        print(f"⚠️  El archivo '{OUTPUT_NOMBRE}' ya existe y será sobrescrito")
    else:
        print("✅ Archivo de salida nuevo")
else:
    print("❌ Primero selecciona un PDF en la celda anterior")
```

---

## 🎯 CELDA 5: RESUMEN PRE-EJECUCIÓN

```python
# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ARCHIVOS - RESUMEN PRE-EJECUCIÓN
# ═══════════════════════════════════════════════════════════════════════════

from datetime import datetime

print()
print("🚀 RESUMEN DE CONFIGURACIÓN")
print("=" * 70)
print()

if PDF_INPUT and OUTPUT_PATH:
    print(f"📥 INPUT:")
    print(f"   • Archivo:  {PDF_INPUT.name}")
    print(f"   • Tamaño:   {PDF_INPUT.stat().st_size / (1024*1024):.2f} MB")
    print(f"   • Ruta:     {PDF_INPUT}")
    print()

    print(f"📤 OUTPUT:")
    print(f"   • Archivo:  {OUTPUT_PATH.name}")
    print(f"   • Ruta:     {OUTPUT_PATH}")
    print(f"   • Existe:   {'Sí (se sobrescribirá)' if OUTPUT_PATH.exists() else 'No (nuevo)'}")
    print()

    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("=" * 70)
    print()
    print("✅ LISTO PARA EJECUTAR PIPELINE")
    print()
    print("Próxima celda: Ejecutar run_pipeline()")

else:
    print("❌ CONFIGURACIÓN INCOMPLETA")
    print()
    if not PDF_INPUT:
        print("   → Falta: Seleccionar PDF de entrada")
    if not OUTPUT_PATH:
        print("   → Falta: Configurar ruta de salida")
    print()
    print("Ejecuta las celdas anteriores primero")
```

---

## 📋 ORDEN SUGERIDO DE CELDAS EN EL NOTEBOOK

```
1. [Existente] Setup y configuración
2. [Existente] Imports principales
3. [Existente] Verificar Tesseract
4. [NUEVA] CELDA 1: Gestión de directorio input
5. [NUEVA] CELDA 2A: Upload PDF con widget (O 2B si sin widget)
6. [NUEVA] CELDA 3: Seleccionar PDF a procesar
7. [NUEVA] CELDA 4: Configurar output
8. [NUEVA] CELDA 5: Resumen pre-ejecución
9. [Existente] Ejecutar pipeline (modificar para usar PDF_INPUT y OUTPUT_PATH)
10. [Existente] Análisis de resultados
```

---

## 🎨 MEJORAS VISUALES (OPCIONAL)

```python
# Agregar al inicio del notebook para mejor visualización
from IPython.display import HTML, display

# Estilos CSS personalizados
display(HTML("""
<style>
    .pdf-status {
        background: #e8f4f8;
        border-left: 4px solid #2196F3;
        padding: 10px;
        margin: 10px 0;
        font-family: monospace;
    }
    .pdf-success {
        background: #e8f5e9;
        border-left: 4px solid #4CAF50;
        padding: 10px;
        margin: 10px 0;
    }
    .pdf-warning {
        background: #fff3e0;
        border-left: 4px solid #FF9800;
        padding: 10px;
        margin: 10px 0;
    }
    .pdf-error {
        background: #ffebee;
        border-left: 4px solid #f44336;
        padding: 10px;
        margin: 10px 0;
    }
</style>
"""))
```

---

## ✅ VENTAJAS DE ESTE ENFOQUE

1. **✅ Limpieza automática** - Evita archivos antiguos interfiriendo
2. **✅ Upload desde notebook** - No necesitas terminal
3. **✅ Selección interactiva** - Si hay múltiples PDFs
4. **✅ Validación** - Verifica que sea PDF y que exista
5. **✅ Feedback visual** - Mensajes claros en cada paso
6. **✅ Flexible** - Soporta widget O manual
7. **✅ Nombres automáticos** - Output se nombra según input

---

**FIN DEL DOCUMENTO**
