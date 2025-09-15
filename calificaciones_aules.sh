#!/bin/bash
# Crear y activar el entorno virtual
python3 -m venv ~/virtual-envs/AULES
source ~/virtual-envs/AULES/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el script Python pasando el primer argumento ($1)
python3 calificaciones_aules.py

# Desactivar el entorno virtual
deactivate
