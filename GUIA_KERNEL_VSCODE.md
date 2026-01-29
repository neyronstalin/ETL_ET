# 🎯 GUÍA VISUAL: Cambiar Kernel en VSCode Jupyter

**Problema:** Notebook usa el kernel incorrecto (otro proyecto)
**Solución:** Seleccionar kernel del venv de ETL_ET

---

## 📍 UBICACIÓN DEL SELECTOR DE KERNEL

Cuando abres el notebook en VSCode, verás esto:

```
┌────────────────────────────────────────────────────────────────┐
│  📄 pipeline_example.ipynb                                     │
├────────────────────────────────────────────────────────────────┤
│  [Celda 1]                                                     │
│                                                                │
│  # Agregar src/ al path                                       │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                    👆 AQUÍ                     │
│                     [Python 3.12.3 (/ETL_APU_v3_2/.venv) ▼]   │ ← HACER CLICK
└────────────────────────────────────────────────────────────────┘
```

---

## 🖱️ PASO A PASO (CON IMÁGENES ASCII)

### 1. Hacer CLICK en el selector de kernel

Está en la **esquina superior derecha** del notebook:

```
┌─────────────────────────────────────────────────┐
│ Muestra algo como:                              │
│   Python 3.12.3 (/.../.../ETL_APU_v3_2/.venv) ▼│  ← CLICK AQUÍ
└─────────────────────────────────────────────────┘
```

---

### 2. Aparecerá un dropdown con opciones

```
┌───────────────────────────────────────────────┐
│ Select Kernel                                 │
├───────────────────────────────────────────────┤
│ 🔍 Type to filter...                          │
├───────────────────────────────────────────────┤
│                                               │
│ Python Environments                           │
│ ────────────────────────────────────────────  │
│                                               │
│ ○ Python 3.12.3 (/...ETL_APU_v3_2/.venv)     │ ← ACTUAL (incorrecto)
│                                               │
│ ● ETL_ET (.venv)                              │ ← SELECCIONAR ESTE ✅
│   /home/codevars/ETL_ET/.venv/bin/python     │
│                                               │
│ ○ Python 3.12.3 (/usr/bin/python3)           │
│                                               │
└───────────────────────────────────────────────┘
```

**SELECCIONA:** `ETL_ET (.venv)`

---

### 3. Verificar que cambió

Después de seleccionar, el selector debe mostrar:

```
[ETL_ET (.venv) ▼]  ← ✅ CORRECTO
```

O:

```
[Python 3.12.3 (/home/codevars/ETL_ET/.venv/bin/python) ▼]  ← ✅ CORRECTO
```

---

### 4. Reiniciar el kernel

Una vez seleccionado el kernel correcto:

**Opción A:** Usar el icono de refresh
```
┌─────────────────────────────────────────────────┐
│ [ETL_ET (.venv) ▼]    [↻]  [⬜]  [▶]           │
│                         ^                       │
│                         └─ CLICK para reiniciar │
└─────────────────────────────────────────────────┘
```

**Opción B:** Usar el menú
- Click derecho en el notebook → "Restart Kernel"
- O: `Ctrl+Shift+P` → "Jupyter: Restart Kernel"

---

### 5. Ejecutar la celda de imports

```python
from src.pipeline import run_pipeline
print("✅ Imports OK!")
```

Debe funcionar sin errores.

---

## 🚨 SI "ETL_ET (.venv)" NO APARECE

### Solución 1: Registrar el kernel manualmente

```bash
cd /home/codevars/ETL_ET
bash fix_kernel.sh
```

Luego **RECARGAR VSCODE:**
- `Ctrl+Shift+P` → "Developer: Reload Window"

---

### Solución 2: Seleccionar manualmente la ruta

Si no aparece "ETL_ET (.venv)" en la lista:

1. En el selector, busca la opción: **"Select Another Kernel..."**
2. Luego: **"Python Environments"**
3. Luego: **"Enter the path to a Python interpreter"**
4. Pega: `/home/codevars/ETL_ET/.venv/bin/python`

---

## ✅ VERIFICACIÓN FINAL

Ejecuta esta celda para confirmar que estás en el entorno correcto:

```python
import sys
print("Python:", sys.executable)

# Debe mostrar:
# Python: /home/codevars/ETL_ET/.venv/bin/python

if '/ETL_ET/.venv/' in sys.executable:
    print("✅ Kernel CORRECTO")
else:
    print("❌ Kernel INCORRECTO - cambiar kernel")
```

---

## 🆘 TROUBLESHOOTING

### Error: "Kernel not found"

```bash
# Reinstalar ipykernel
source .venv/bin/activate
pip install --force-reinstall ipykernel
python -m ipykernel install --user --name etl_et_venv
```

### Error: "Cannot start kernel"

```bash
# Verificar que el venv está completo
source .venv/bin/activate
pip install jupyter ipykernel ipywidgets
```

### Error: Sigue sin aparecer

```bash
# Listar kernels disponibles
jupyter kernelspec list

# Debería mostrar:
#   etl_et_venv    /home/codevars/.local/share/jupyter/kernels/etl_et_venv

# Si no aparece, registrar:
python -m ipykernel install --user --name etl_et_venv --display-name "ETL_ET (.venv)"
```

---

## 📞 COMANDOS ÚTILES

```bash
# Ver qué python está usando el notebook actualmente
which python

# Ver kernels disponibles
jupyter kernelspec list

# Eliminar kernel viejo (si hay conflictos)
jupyter kernelspec remove etl_et_venv

# Registrar de nuevo
source .venv/bin/activate
python -m ipykernel install --user --name etl_et_venv --display-name "ETL_ET (.venv)"

# Recargar VSCode
# Ctrl+Shift+P → "Developer: Reload Window"
```

---

## 🎯 RESUMEN RÁPIDO

1. ✅ **Click** en selector kernel (arriba a la derecha)
2. ✅ **Seleccionar** "ETL_ET (.venv)"
3. ✅ **Reiniciar** kernel (icono ↻)
4. ✅ **Ejecutar** celda de imports
5. ✅ **Verificar** que `sys.executable` muestra `/ETL_ET/.venv/`

**¿Ya funciona? Si sigue fallando, ejecuta:** `bash fix_kernel.sh` **y recarga VSCode.**

---

**Última actualización:** 2026-01-28
