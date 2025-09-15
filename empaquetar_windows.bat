@echo off
REM =======================================================
REM EMPAQUETADOR PARA CALIFICACIONES_AULES - WINDOWS EXE
REM =======================================================
echo.
echo Creando ejecutable para Calificaciones Aules...
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Instala Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar si existe el icono
if not exist "%~dp0gestor-calificaciones.ico" (
    echo ADVERTENCIA: No se encontró el icono "gestor-calificaciones.ico"
    echo Continuando sin icono...
    set ICON_OPTION=
) else (
    echo Icono encontrado: gestor-calificaciones.ico
    set ICON_OPTION=--icon "%~dp0gestor-calificaciones.ico"
    copy "%~dp0gestor-calificaciones.ico" . >nul
)

REM Crear directorio de trabajo
set WORKDIR=%~dp0empaquetado_windows
echo [DEBUG] Directorio de trabajo: %WORKDIR%
if not exist "%WORKDIR%" mkdir "%WORKDIR%"
cd /d "%WORKDIR%"
echo [DEBUG] Directorio actual: %CD%
echo.

echo Creando entorno virtual...
python -m venv venv
call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install --upgrade pip
pip install requests beautifulsoup4 tqdm pyinstaller

echo Copiando script principal...
copy "%~dp0calificaciones_aules.py" . >nul

echo Compilando ejecutable con PyInstaller...
pyinstaller --onefile --console ^
  --name Gestor_Calificaciones_Aules ^
  %ICON_OPTION% ^
  --hidden-import=bs4 ^
  --hidden-import=tqdm ^
  --hidden-import=requests ^
  calificaciones_aules.py



REM IMPORTANTE: Regresar al directorio original antes de continuar
cd /d "%~dp0"

echo.
echo =======================================================
echo ¡EMPAQUETADO COMPLETADO!
echo =======================================================
echo.
echo El ejecutable se encuentra en: %WORKDIR%\dist\
echo.
echo Archivo generado: Gestor_Calificaciones_Aules.exe
if exist "%~dp0gestor-calificaciones.ico" (
    echo Icono personalizado incluido: ✓
) else (
    echo Icono personalizado: No encontrado
)
echo.
echo Para usar el programa:
echo   1. Coloca el archivo "datos_aules.json" en la misma carpeta
echo   2. Ejecuta "Gestor_Calificaciones_Aules.exe"
echo.
echo NOTA: Los usuarios NO necesitan tener Python instalado.
echo.

REM Copiar el ejecutable al directorio original
if exist "%WORKDIR%\dist\Gestor_Calificaciones_Aules.exe" (
    copy "%WORKDIR%\dist\Gestor_Calificaciones_Aules.exe" . >nul
    echo Ejecutable copiado a: %CD%\Gestor_Calificaciones_Aules.exe
) else (
    echo ERROR: No se pudo encontrar el ejecutable
)

echo.
set /p ELIMINAR="¿Quieres eliminar la carpeta de TRABAJO? (s/n): "
if /i "%ELIMINAR%"=="s" (
	rmdir /s /q "%WORKDIR%"
)

echo.
echo Proceso finalizado. Presiona cualquier tecla para salir...
pause >nul

echo Desactivando entorno virtual...
deactivate