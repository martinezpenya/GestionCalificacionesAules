#!/bin/bash
# Crear y activar el entorno virtual
python3 -m venv ~/virtual-envs/AULES
source ~/virtual-envs/AULES/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install pyinstaller

# Instalar appimage-builder
./build.sh

# Desactivar el entorno virtual
deactivate

# Descargar appimagetool (si no lo tienes)
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Crear el AppImage final
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir

# Limpiar
rm -rf dist build AppDir
rm appimagetool-x86_64.AppImage GestorCalificacionesAules.spec

