rem Crear entorno
python3 -m venv %userprofile%/virtual-envs/AULES
source %userprofile%/virtual-envs/AULES/bin/activate

rem Instalar dependencias
python3 install -r requirements.txt

rem Ejecutar el script Python pasando el primer argumento ($1)
python3 calificaciones_aules.py

rem Desactivar el entorno virtual
deactivate
