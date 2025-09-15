#!/bin/bash

# Script para empaquetar calificaciones_aules.py como AppImage

# Crear el ejecutable con PyInstaller
#!/bin/bash

# Script para empaquetar calificaciones_aules.py como AppImage
#!/bin/bash

# Script corregido para crear el archivo .desktop correctamente

echo "Limpiando builds anteriores..."
rm -rf dist build AppDir GestorCalificacionesAules*.AppImage

echo "Creando ejecutable con PyInstaller..."
pyinstaller --onefile --name="GestorCalificacionesAules" \
    --hidden-import=requests \
    --hidden-import=bs4 \
    --hidden-import=tqdm \
    --hidden-import=urllib.parse \
    --hidden-import=json \
    --hidden-import=re \
    --hidden-import=os \
    --hidden-import=sys \
    --hidden-import=time \
    calificaciones_aules.py

echo "Creando estructura AppImage..."
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# Copiar el ejecutable
cp dist/GestorCalificacionesAules AppDir/usr/bin/

# Añadir icono
cp gestor-calificaciones.png AppDir/gestor-calificaciones-aules.png

# Crear archivo .desktop CORRECTAMENTE usando echo
echo "[Desktop Entry]" > AppDir/gestor-calificaciones-aules.desktop
echo "Name=Gestor de Calificaciones Aules" >> AppDir/gestor-calificaciones-aules.desktop
echo "Comment=Gestiona estructuras de calificación en Moodle/Aules" >> AppDir/gestor-calificaciones-aules.desktop
echo "Exec=GestorCalificacionesAules" >> AppDir/gestor-calificaciones-aules.desktop
echo "Icon=gestor-calificaciones-aules" >> AppDir/gestor-calificaciones-aules.desktop
echo "Type=Application" >> AppDir/gestor-calificaciones-aules.desktop
echo "Categories=Education;" >> AppDir/gestor-calificaciones-aules.desktop
echo "Terminal=true" >> AppDir/gestor-calificaciones-aules.desktop

# Verificar que el archivo se creó correctamente
echo "Verificando archivo .desktop:"
ls -la AppDir/gestor-calificaciones-aules.desktop
cat AppDir/gestor-calificaciones-aules.desktop

# Crear AppRun
cat > AppDir/AppRun << 'EOF'
#!/bin/bash
HERE=$(dirname $(readlink -f "$0"))
export PATH="$HERE/usr/bin:$PATH"
cd "$HERE"
exec "./usr/bin/GestorCalificacionesAules" "$@"
EOF

chmod +x AppDir/AppRun
chmod +x AppDir/usr/bin/GestorCalificacionesAules

echo "Estructura AppImage creada:"
tree AppDir/

echo "Ejecutando appimagetool..."
./appimagetool-x86_64.AppImage AppDir
