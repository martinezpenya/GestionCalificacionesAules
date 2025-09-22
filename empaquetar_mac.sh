#!/bin/bash

set -euo pipefail

# Empaquetado para macOS: crea .app y .dmg

APP_NAME="GestorCalificacionesAules"
ENTRYPOINT="calificaciones_aules.py"
ICON_PNG="gestor-calificaciones.png"
BUILD_DIR="build-macos"
DIST_DIR="dist"

echo "Limpiando builds anteriores..."
rm -rf "$BUILD_DIR" "$DIST_DIR/${APP_NAME}.app" "$DIST_DIR/${APP_NAME}.dmg" build
mkdir -p "$BUILD_DIR"

echo "Instalando dependencias (pyinstaller y requirements)..."
python3 -m pip install --upgrade pip >/dev/null
python3 -m pip install -r requirements.txt >/dev/null
python3 -m pip install pyinstaller >/dev/null

# Generar icono .icns a partir del PNG si es posible
ICNS_PATH="$BUILD_DIR/${APP_NAME}.icns"
if command -v iconutil >/dev/null 2>&1 && command -v sips >/dev/null 2>&1 && [ -f "$ICON_PNG" ]; then
  echo "Generando icono .icns desde $ICON_PNG..."
  ICONSET_DIR="$BUILD_DIR/${APP_NAME}.iconset"
  rm -rf "$ICONSET_DIR"
  mkdir -p "$ICONSET_DIR"
  # Tamaños requeridos
  for size in 16 32 64 128 256 512; do
    sips -z "$size" "$size" "$ICON_PNG" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null
    sips -z $((size*2)) $((size*2)) "$ICON_PNG" --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" >/dev/null
  done
  iconutil -c icns "$ICONSET_DIR" -o "$ICNS_PATH"
else
  echo "iconutil/sips no disponibles o falta $ICON_PNG. Continuando sin icono personalizado."
  ICNS_PATH=""
fi

echo "Creando bundle .app con PyInstaller..."
PYI_ARGS=(
  --name "$APP_NAME"
  --onefile
  --console
  --osx-bundle-identifier com.aules.$APP_NAME
)

if [ -n "$ICNS_PATH" ] && [ -f "$ICNS_PATH" ]; then
  PYI_ARGS+=(--icon "$ICNS_PATH")
fi

pyinstaller "${PYI_ARGS[@]}" "$ENTRYPOINT"

if [ ! -d "$DIST_DIR/${APP_NAME}.app" ]; then
  echo "Error: No se ha generado ${DIST_DIR}/${APP_NAME}.app" >&2
  exit 1
fi

echo "Creando imagen .dmg..."
hdiutil create -volname "${APP_NAME}" -srcfolder "$DIST_DIR/${APP_NAME}.app" -ov -format UDZO "$DIST_DIR/${APP_NAME}.dmg" >/dev/null

echo "Listo. Artefactos generados:"
echo "- ${DIST_DIR}/${APP_NAME}.app"
echo "- ${DIST_DIR}/${APP_NAME}.dmg"



