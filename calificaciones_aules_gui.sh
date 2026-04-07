#!/bin/bash
# Activar el entorno virtual local del proyecto
source .venv/bin/activate

# Instalar/Actualizar dependencias de forma eficiente
pip install -r requirements.txt

# Ejecutar la interfaz gráfica (Versión Estable Tkinter)
python gui_aules.py

# Desactivar el entorno virtual
deactivate
