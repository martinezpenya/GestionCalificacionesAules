# Autores
- Idea inicial: Manuel Sanchez (Nelo) me.sanchezgomis@edu.gva.es
- Ampliación de funcionalidades, comentarios y reusabilidad: David Martinez (www.martinezpenya.es)

# Contenido

## Código

| Fichero                     | Descripción                                                  |
| --------------------------- | ------------------------------------------------------------ |
| `calificaciones_aules.py`   | Script en python para la gestión de libro de calificaciones en AULES (Moodle) |
| `calificaciones_aules.sh`   | Script para la creación de un entorno virtual y ejecución del script `calificaciones_aules.py` (teniendo instalado previamente Python) en distribuciones GNU/linux. |
| `calificaciones_aules.bat`  | Script para la creación de un entorno virtual y ejecución del script `calificaciones_aules.py` (teniendo instalado previamente Python) en sistemas operativos Windows. |
| `requirements.txt`          | Fichero de requisitos/dependencias, usado por `calificaciones_aules.sh` y `calificaciones_aules.bat` para lanzar `calificaciones_aules.py` |
| `empaquetar_appimage.sh`    | Script python para empaquetar el script `calificaciones_aules.py` en un AppImage en sistemas GNU/Linux. Requiere `build.sh`. |
| `build.sh`                  | Script python para generrar el AppImage. Usado por `empaquetar_appimage.sh` |
| `empaquetar_windows.bat`    | Archivo de proceso por lotes para empaquetar el script `calificaciones_aules.py` en un ejecutable (EXE) en sistemas Windows. |
| `gestor-calificaciones.ico` | Logo de la aplicación para Windows.                          |
| `gestor-calificaciones.png` | Logo de la aplicación para GNU/Linux.                        |

## Releases

En el apartado releases hay disponibles dos assets:

| Asset                                            | Descripción                                                  |
| ------------------------------------------------ | ------------------------------------------------------------ |
| `Gestor_Calificaciones_Aules.exe`                | Binario ejecutable para sistemas Windows.                    |
| `Gestor_de_Calificaciones_Aules-x86_64.AppImage` | Binario ejecutable para sistemas GNU/Linux, ejecutar con `./Gestor_de_Calificaciones_Aules-x86_64.AppImage` desde la consola |

# Ayuda

## DESCRIPCIÓN:
Script unificado con menú interactivo para gestionar estructuras de calificación en Moodle/Aules.
Permite crear, actualizar fórmulas, eliminar estructuras completas y generar plantillas de configuración.

## CARACTERÍSTICAS PRINCIPALES:
- Menú interactivo con 5 opciones principales
- Gestión completa de categorías y elementos de calificación
- Soporte para fórmulas de cálculo personalizadas
- Configuración mediante archivo JSON (datos_aules.json)
- Detección automática del entorno de ejecución (AppImage vs desarrollo)

## OPCIONES DEL MENÚ:
0. Generar estructura básica JSON local
   - Guía interactiva para crear datos_aules_generado.json
   - Incluye sugerencias para IA generativa

1. Crear nueva estructura online
   - Crea estructura completa basada en datos_aules.json

2. Actualizar cálculos y pesos
   - Modifica fórmulas, pesos y configuraciones en estructura existente

3. Eliminar estructura online
   - Elimina completamente una estructura por categoría padre

4. Salir
   - Finaliza la ejecución

El script detecta automáticamente si se ejecuta como AppImage y busca datos_aules.json

## ESTRUCTURA DEL ARCHIVO JSON (datos_aules.json):
```json
{
  "base_url": "https://aules.edu.gva.es/docent",
  "username": "tu_usuario",
  "password": "tu_contraseña",
  "course_id": 12345,
  "configuracion_global": {
    "aggregation": 10,
    "aggregateonlygraded": false,
    "grademax": 10,
    "gradepass": 5
  },
  "categoria_padre": "Nombre categoría padre",
  "categorias_hijas": [
    {
      "nombre": "Nombre RA1",
      "aggregationcoef": 2,
      "elementos": [
        "Elemento simple",
        {
          "nombre": "Elemento con configuración",
          "aggregationcoef": 2,
          "formula": "=[[1AVA]]",
          "idnumber": "ID_UNICO_001"
        }
      ]
    }
  ]
}
```

## URLs BASE SOPORTADAS:
- https://aules.edu.gva.es/docent (entorno de pruebas)
- https://aules.edu.gva.es/fp (FP Presencial)
- https://aules.edu.gva.es/semipresencial (FP Semipresencial)

## OPCIONES DE AGREGACIÓN:
-  0: Media de las calificaciones
- 10: Media ponderada de las calificaciones
- 11: Media ponderada simple de las calificaciones
- 12: Media de las calificaciones (con créditos extra)
-  2: Mediana de las calificaciones
-  4: Calificación más baja
-  6: Calificación más alta
-  8: Moda de las calificaciones
- 13: Natural

## NOTAS IMPORTANTES:
- Opciones 1, 2 y 3 requieren datos_aules.json
- aggregationcoef es opcional (0.0 categorías, 1.0 items por defecto)
- Fórmulas usan sintaxis Moodle: =[[NOMBRE_ITEM]]
- idnumber identifica elementos únicamente
- Se recomienda ejecutar como AppImage para mejor portabilidad

## FLUJO DE TRABAJO RECOMENDADO:
1. Ejecutar opción 0 para generar plantilla básica
2. Editar manualmente el JSON generado
3. Usar IA generativa (ChatGPT, Claude, etc.) para completar RA y CE
4. Renombrar archivo a datos_aules.json
5. Ejecutar opción 1 para crear estructura online

## SOPORTE PARA IA GENERATIVA:
Incluye prompt específico para crear JSON completos a partir de documentos con RA y CE.
