# 🔧 INSTALAR TESSERACT OCR EN WSL2/LINUX

**Sistema detectado:** Linux (WSL2)
**Estado actual:** Tesseract NO instalado

---

## ⚡ INSTALACIÓN RÁPIDA (COPY-PASTE)

### Opción 1: Instalación completa (Tesseract + Español)

Abre una **terminal WSL** y ejecuta:

```bash
# Actualizar repositorios
sudo apt-get update

# Instalar Tesseract + idioma español
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa

# Verificar instalación
tesseract --version

# Verificar idiomas disponibles
tesseract --list-langs
```

**Tiempo estimado:** 2-3 minutos

---

## 📋 PASO A PASO DETALLADO

### 1. Actualizar paquetes del sistema

```bash
sudo apt-get update
```

**Output esperado:**
```
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
Get:2 http://archive.ubuntu.com/ubuntu jammy-updates InRelease
...
Reading package lists... Done
```

---

### 2. Instalar Tesseract OCR

```bash
sudo apt-get install -y tesseract-ocr
```

**Output esperado:**
```
Reading package lists... Done
Building dependency tree... Done
...
Setting up tesseract-ocr (4.1.1-2.1build1) ...
```

**Tamaño:** ~5 MB

---

### 3. Instalar paquete de idioma español

```bash
sudo apt-get install -y tesseract-ocr-spa
```

**Output esperado:**
```
Reading package lists... Done
...
Setting up tesseract-ocr-spa (1:4.00~git30-7274cfa-1.1) ...
```

**Tamaño:** ~5 MB

---

### 4. Verificar instalación

```bash
# Ver versión instalada
tesseract --version
```

**Output esperado:**
```
tesseract 4.1.1
 leptonica-1.82.0
  libgif 5.1.9 : libjpeg 8d (libjpeg-turbo 2.1.1) : libpng 1.6.37 : libtiff 4.3.0 : zlib 1.2.11 : libwebp 1.2.2 : libopenjp2 2.4.0
 Found AVX2
 Found AVX
 Found FMA
 Found SSE
 Found libarchive 3.6.0 zlib/1.2.11 liblzma/5.2.5 bz2lib/1.0.8 liblz4/1.9.3 libzstd/1.4.8
```

---

### 5. Verificar idiomas disponibles

```bash
tesseract --list-langs
```

**Output esperado:**
```
List of available languages (3):
eng
osd
spa  ← ESPAÑOL INSTALADO ✅
```

---

## ✅ VERIFICACIÓN EN PYTHON

Después de instalar, ejecuta esto en el notebook:

```python
from src.ocr.tesseract_ocr import test_tesseract_installation, get_available_languages

if test_tesseract_installation():
    print("✅ Tesseract instalado correctamente")
    langs = get_available_languages()
    print(f"Idiomas disponibles: {langs}")

    if 'spa' in langs:
        print("✅ Idioma español (spa) disponible")
    else:
        print("⚠️ Español no instalado")
else:
    print("❌ Tesseract NO detectado")
```

**Output esperado:**
```
✅ Tesseract instalado correctamente
Idiomas disponibles: ['eng', 'osd', 'spa']
✅ Idioma español (spa) disponible
```

---

## 🔍 TROUBLESHOOTING

### Error: "tesseract: command not found"

**Causa:** Tesseract no está en el PATH

**Solución:**
```bash
# Ver dónde se instaló
which tesseract

# Debería mostrar: /usr/bin/tesseract

# Si no aparece, reinstalar:
sudo apt-get install --reinstall tesseract-ocr
```

---

### Error: "Language 'spa' is not installed"

**Causa:** Paquete de idioma español no instalado

**Solución:**
```bash
# Instalar paquete español
sudo apt-get install tesseract-ocr-spa

# Verificar que se instaló
tesseract --list-langs | grep spa
```

---

### Error: "Unable to load unicharset file"

**Causa:** Archivos de datos corruptos

**Solución:**
```bash
# Reinstalar completamente
sudo apt-get remove tesseract-ocr tesseract-ocr-spa
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

---

## 📦 IDIOMAS ADICIONALES (OPCIONAL)

Si necesitas más idiomas además de español:

```bash
# Inglés (ya viene por defecto)
sudo apt-get install tesseract-ocr-eng

# Francés
sudo apt-get install tesseract-ocr-fra

# Portugués
sudo apt-get install tesseract-ocr-por

# Ver todos los idiomas disponibles
apt-cache search tesseract-ocr | grep "^tesseract-ocr-"
```

---

## 🚀 DESPUÉS DE INSTALAR

Una vez instalado Tesseract:

1. **Recargar el kernel del notebook:**
   - `Ctrl+Shift+P` → "Jupyter: Restart Kernel"

2. **Ejecutar celda de verificación:**
   ```python
   from src.ocr.tesseract_ocr import test_tesseract_installation
   test_tesseract_installation()
   ```

3. **Continuar con el notebook:**
   - Todas las celdas que usan OCR deberían funcionar ahora

---

## 📊 INFORMACIÓN DE VERSIONES

| Componente | Versión típica (Ubuntu 22.04) |
|------------|-------------------------------|
| Tesseract | 4.1.1 |
| Leptonica | 1.82.0 |
| Idioma español (spa) | 4.00 |

---

## 💡 NOTAS IMPORTANTES

1. **Tesseract es un binario del sistema**, NO un paquete de Python
   - Se instala con `apt-get`, no con `pip`
   - Python solo tiene el wrapper `pytesseract`

2. **Los archivos de datos de idiomas** se instalan en:
   - `/usr/share/tesseract-ocr/4.00/tessdata/`
   - Archivo español: `spa.traineddata`

3. **pytesseract (Python)** ya está instalado en el venv
   - Solo necesitas instalar el binario Tesseract del sistema

4. **No requiere configuración adicional** si está en PATH
   - Linux: `/usr/bin/tesseract`
   - WSL2: Funciona exactamente igual que Linux nativo

---

## ✅ CHECKLIST POST-INSTALACIÓN

- [ ] `tesseract --version` funciona
- [ ] `tesseract --list-langs` muestra 'spa'
- [ ] `test_tesseract_installation()` retorna True en Python
- [ ] `get_available_languages()` incluye 'spa'
- [ ] Celda 3 del notebook ejecuta sin errores

---

## 🎯 COMANDO TODO-EN-UNO

Si quieres instalar todo de una vez:

```bash
sudo apt-get update && \
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa && \
tesseract --version && \
tesseract --list-langs && \
echo "" && \
echo "✅ Tesseract instalado correctamente"
```

---

**Última actualización:** 2026-01-28
**Sistema:** Linux (WSL2)
