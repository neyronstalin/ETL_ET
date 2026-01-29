"""
Fix para ipywidgets FileUpload - Compatible con todas las versiones

Este código es compatible con:
- ipywidgets >= 8.0 (formato moderno)
- ipywidgets <= 7.x (formato legacy con metadata)
- Formato tuple y dict
"""

def extract_file_data(upload_value):
    """
    Extrae filename y content de forma robusta desde upload_value.

    Args:
        upload_value: Valor de FileUpload.value (puede ser tuple o dict)

    Returns:
        tuple: (filename, content) o (None, None) si falla
    """
    # Paso 1: Obtener el uploaded_file dict
    uploaded_file = None

    if isinstance(upload_value, tuple):
        # Formato nuevo: tuple con un elemento
        if len(upload_value) > 0:
            uploaded_file = upload_value[0]
    elif isinstance(upload_value, dict):
        # Formato legacy: dict con keys como filenames
        if upload_value:
            uploaded_file = list(upload_value.values())[0]

    if not uploaded_file or not isinstance(uploaded_file, dict):
        print("❌ Formato de upload inesperado")
        return None, None

    # Paso 2: Extraer filename (múltiples estrategias con fallback)
    filename = None

    # Estrategia 1: Formato moderno (directo)
    if "name" in uploaded_file:
        filename = uploaded_file["name"]

    # Estrategia 2: Formato legacy (metadata.name)
    elif "metadata" in uploaded_file and isinstance(uploaded_file["metadata"], dict):
        filename = uploaded_file["metadata"].get("name")

    # Estrategia 3: Buscar en todas las claves (defensivo)
    else:
        # Debug: mostrar estructura disponible
        print(f"⚠️  Formato no reconocido. Keys disponibles: {list(uploaded_file.keys())}")

        # Intentar encontrar filename en cualquier nested dict
        for key, value in uploaded_file.items():
            if isinstance(value, dict) and "name" in value:
                filename = value["name"]
                print(f"✓ Filename encontrado en '{key}.name'")
                break

    # Paso 3: Extraer content
    content = uploaded_file.get("content")

    # Validación final
    if not filename:
        print("❌ No se pudo extraer el nombre del archivo")
        print(f"   Estructura recibida: {uploaded_file.keys()}")
        return None, None

    if not content:
        print("❌ No se pudo extraer el contenido del archivo")
        return None, None

    return filename, content


def on_upload_change_robust(change, input_dir, output_area, listar_callback):
    """
    Callback robusto para FileUpload - Compatible con todas las versiones.

    Args:
        change: Change event de ipywidgets
        input_dir: Path del directorio de input
        output_area: Widget Output para mensajes
        listar_callback: Función para listar PDFs después del upload

    Returns:
        Path del archivo guardado o None si falla
    """
    upload_widget = change['owner']

    with output_area:
        from IPython.display import clear_output
        clear_output()

        if not upload_widget.value:
            print("❌ No se seleccionó archivo")
            return None

        # Extraer filename y content de forma robusta
        filename, content = extract_file_data(upload_widget.value)

        if not filename or not content:
            return None

        print(f"📄 Archivo seleccionado: {filename}")
        print(f"   Tamaño: {len(content) / (1024*1024):.2f} MB")

        # Validar PDF
        if not filename.lower().endswith('.pdf'):
            print("❌ Error: Solo archivos PDF")
            return None

        # Guardar
        from pathlib import Path
        file_path = Path(input_dir) / filename

        if file_path.exists():
            print(f"⚠️  '{filename}' ya existe, sobrescribiendo...")

        try:
            with open(file_path, 'wb') as f:
                f.write(content)

            print(f"✅ Guardado en: {file_path}")
            print()

            # Actualizar lista
            if listar_callback:
                listar_callback()

            return file_path

        except Exception as e:
            print(f"❌ Error al guardar archivo: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════
# CÓDIGO PARA COPIAR AL NOTEBOOK
# ═══════════════════════════════════════════════════════════════════════════

NOTEBOOK_CODE = """
# ═══════════════════════════════════════════════════════════════════════════
# UPLOAD DE PDF - Widget Interactivo (VERSIÓN ROBUSTA)
# ═══════════════════════════════════════════════════════════════════════════

from ipywidgets import FileUpload, Button, Output, VBox, HBox, HTML
from IPython.display import display, clear_output

# Widget de upload
upload_widget = FileUpload(
    accept='.pdf',
    multiple=False,
    description='📤 Seleccionar PDF:',
    button_style='primary',
    style={'description_width': 'initial'}
)

# Output para mensajes
output_area = Output()

# Variable global para almacenar el path del archivo
uploaded_file_path = None

def extract_file_data(upload_value):
    '''
    Extrae filename y content de forma robusta desde upload_value.
    Compatible con ipywidgets >= 8.0 (moderno) y <= 7.x (legacy).
    '''
    # Paso 1: Obtener el uploaded_file dict
    uploaded_file = None

    if isinstance(upload_value, tuple):
        # Formato nuevo: tuple con un elemento
        if len(upload_value) > 0:
            uploaded_file = upload_value[0]
    elif isinstance(upload_value, dict):
        # Formato legacy: dict con keys como filenames
        if upload_value:
            uploaded_file = list(upload_value.values())[0]

    if not uploaded_file or not isinstance(uploaded_file, dict):
        print("❌ Formato de upload inesperado")
        return None, None

    # Paso 2: Extraer filename (múltiples estrategias con fallback)
    filename = None

    # Estrategia 1: Formato moderno (directo)
    if "name" in uploaded_file:
        filename = uploaded_file["name"]

    # Estrategia 2: Formato legacy (metadata.name)
    elif "metadata" in uploaded_file and isinstance(uploaded_file["metadata"], dict):
        filename = uploaded_file["metadata"].get("name")

    # Estrategia 3: Buscar en todas las claves (defensivo)
    else:
        print(f"⚠️  Formato no reconocido. Keys disponibles: {list(uploaded_file.keys())}")

        for key, value in uploaded_file.items():
            if isinstance(value, dict) and "name" in value:
                filename = value["name"]
                print(f"✓ Filename encontrado en '{key}.name'")
                break

    # Paso 3: Extraer content
    content = uploaded_file.get("content")

    # Validación final
    if not filename:
        print("❌ No se pudo extraer el nombre del archivo")
        print(f"   Keys disponibles: {list(uploaded_file.keys())}")
        return None, None

    if not content:
        print("❌ No se pudo extraer el contenido del archivo")
        return None, None

    return filename, content

def on_upload_change(change):
    '''Callback cuando se sube un archivo - VERSIÓN ROBUSTA'''
    global uploaded_file_path

    with output_area:
        clear_output()

        if not upload_widget.value:
            print("❌ No se seleccionó archivo")
            return

        # Extraer filename y content de forma robusta
        filename, content = extract_file_data(upload_widget.value)

        if not filename or not content:
            return

        print(f"📄 Archivo seleccionado: {filename}")
        print(f"   Tamaño: {len(content) / (1024*1024):.2f} MB")

        # Validar PDF
        if not filename.lower().endswith('.pdf'):
            print("❌ Error: Solo archivos PDF")
            return

        # Guardar
        file_path = INPUT_DIR / filename

        if file_path.exists():
            print(f"⚠️  '{filename}' ya existe, sobrescribiendo...")

        try:
            with open(file_path, 'wb') as f:
                f.write(content)

            uploaded_file_path = file_path

            print(f"✅ Guardado en: {file_path}")
            print()
            listar_pdfs_input()

        except Exception as e:
            print(f"❌ Error al guardar: {e}")

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

# UI
print("📤 UPLOAD DE PDF")
print("=" * 70)
display(HTML("<div style='background: #f0f8ff; padding: 10px; border-left: 4px solid #2196F3;'>"
             "<b>📌 Instrucciones:</b><br>"
             "1️⃣ Click en <b>'Seleccionar PDF'</b> y elige tu archivo<br>"
             "2️⃣ El archivo se guarda automáticamente en <code>data/input/</code><br>"
             "3️⃣ Usa <b>'🗑️ Limpiar Input'</b> si quieres empezar de cero"
             "</div>"))
print()
display(VBox([
    HBox([upload_widget, btn_limpiar]),
    output_area
]))
"""

if __name__ == "__main__":
    print("=" * 70)
    print("CÓDIGO LISTO PARA COPIAR AL NOTEBOOK")
    print("=" * 70)
    print()
    print(NOTEBOOK_CODE)
