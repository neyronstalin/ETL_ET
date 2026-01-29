#!/bin/bash
# Script de instalación automática de Tesseract OCR para WSL2/Linux

set -e  # Exit on error

echo ""
echo "🔧 INSTALADOR DE TESSERACT OCR"
echo "================================"
echo ""
echo "Este script instalará:"
echo "  • Tesseract OCR (motor de OCR)"
echo "  • Paquete de idioma español (spa)"
echo ""
echo "Requiere permisos de sudo (se te pedirá la contraseña)"
echo ""

# Verificar si ya está instalado
if command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract ya está instalado:"
    tesseract --version | head -1
    echo ""
    read -p "¿Reinstalar de todas formas? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Instalación cancelada"
        exit 0
    fi
fi

echo ""
echo "📦 Actualizando repositorios..."
sudo apt-get update -qq

echo ""
echo "📦 Instalando Tesseract OCR..."
sudo apt-get install -y tesseract-ocr

echo ""
echo "📦 Instalando paquete de idioma español..."
sudo apt-get install -y tesseract-ocr-spa

echo ""
echo "✅ INSTALACIÓN COMPLETADA"
echo "========================="
echo ""

# Verificar instalación
echo "📋 Información de la instalación:"
echo ""
tesseract --version | head -1

echo ""
echo "📋 Idiomas disponibles:"
tesseract --list-langs

echo ""
echo "✅ Tesseract instalado correctamente"
echo ""
echo "Próximos pasos:"
echo "  1. En el notebook, ejecutar celda de verificación de nuevo"
echo "  2. Debe mostrar: ✅ Tesseract instalado correctamente"
echo "  3. Debe mostrar: ✅ Idioma español (spa) disponible"
echo ""
