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
| `empaquetar_mac.sh`    | Script python para empaquetar el script `calificaciones_aules.py` en un AppImage en sistemas macOS.|
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
Permite crear, actualizar fórmulas y pesos, eliminar estructuras completas y generar plantillas de configuración.

## CARACTERÍSTICAS PRINCIPALES:
- Menú interactivo con 5 opciones principales
- Gestión completa de categorías y elementos de calificación
- Soporte para fórmulas de cálculo personalizadas y pesos de los elementos en sus categorias.
- Configuración mediante archivo JSON (`datos_aules.json`)
- Detección automática del entorno de ejecución (AppImage vs desarrollo)

## OPCIONES DEL MENÚ:
0. Generar estructura básica JSON local
   - Guía interactiva para crear `datos_aules_generado.json`
   - Incluye sugerencias para IA generativa

1. Crear nueva estructura online
   - Crea estructura completa basada en `datos_aules.json`

2. Actualizar cálculos y pesos
   - Modifica fórmulas, pesos y configuraciones en estructura existente

3. Eliminar estructura online
   - Elimina completamente una estructura por categoría padre

4. Salir
   - Finaliza la ejecución

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
- `aggregationcoef` es opcional (0.0 categorías, 1.0 items por defecto)
- Fórmulas usan sintaxis Moodle: =[[NOMBRE_ITEM]]
- `idnumber` identifica elementos únicamente
- Se recomienda ejecutar como AppImage para mejor portabilidad

## FLUJO DE TRABAJO RECOMENDADO:
1. Ejecutar opción 0 para generar plantilla básica
2. Editar manualmente el JSON generado
3. Usar IA generativa (ChatGPT, Claude, etc.) para completar RA y CE
4. Renombrar archivo a `datos_aules.json`
5. Ejecutar opción 1 para crear estructura online

## SOPORTE PARA IA GENERATIVA:
Incluye prompt específico para crear JSON completos a partir de documentos con RA y CE.

# Ejemplo de ejecución

Aquí puedes ver un ejemplo de ejecución para la opción 0 (Generar estructura básica):

```sh
==================================================
GENERADOR DE ESTRUCTURA BÁSICA JSON
==================================================

--- DATOS DE CONEXIÓN ---
Selecciona la URL base de Aules:
  1: https://aules.edu.gva.es/docent (entorno de pruebas)
  2: https://aules.edu.gva.es/fp (FP Presencial)
  3: https://aules.edu.gva.es/semipresencial (FP Semipresencial)
  4: Otra URL (escribir manualmente)
Opción (1-4): 1
Nombre de usuario (Tu DNI): 11111111H
Contraseña (de AULES): contraseña
ID del curso (cuando entres al curso el ultimo numero de 6 digitos que aparece detras del view.php?id=XXXXXX): 112233

--- CONFIGURACIÓN GLOBAL ---
Opciones de agregación:
  0: Media de las calificaciones
  10: Media ponderada de las calificaciones
  11: Media ponderada simple de las calificaciones
  12: Media de las calificaciones (con créditos extra)
  2: Mediana de las calificaciones
  4: Calificación más baja
  6: Calificación más alta
  8: Moda de las calificaciones
  13: Natural
Selecciona el tipo de agregación: 10
¿Considerar solo elementos calificados? (s/n): n
Calificación máxima (por ejemplo 10): 10
Calificación mínima para aprobar (por ejemplo 5): 5

--- CATEGORÍA PADRE ---
Nombre de la categoría padre (por ejemplo: 'RA CE FEE'): RA CE FEE

--- CATEGORÍAS HIJAS BÁSICAS ---
Se generarán 2 categorías hijas básicas (RA1 y RA2) con algunos criterios de evaluación.

✓ Estructura básica guardada en '/home/david/datos_aules_generado.json'

RECOMENDACIÓN: Edita manualmente el archivo para:
1. Completar las descripciones de los RA y CE
2. Añadir fórmulas de cálculo si es necesario (Solo CE)(usar sintaxis Moodle: =[[NOMBRE_ITEM]])
   Los identificadores que uses en las formulas deben existir previamente, sino la formula no se aplicara
3. Añadir idnumber (Solo CE) para identificar elementos de forma única
4. Añadir aggregationcoef (Solo Categorias hijas (RA) y CE) para indicar el peso del elemento en la ponderacion
5. Añadir más categorías hijas y elementos si es necesario

  EJEMPLOS:
  - "formula": "=[[1AVA]]"
  - "formula": "=([[1AVA]]*0.5)+([[FEE]]*0.5)"
  - "idnumber": "ID_UNICO_001"
5. Recuerda que el json se debe llamar exactamente datos_aules.json (renombralo)

==================================================
SUGERENCIA PARA IA GENERATIVA
==================================================
Para generar automáticamente un JSON completo a partir de un documento con los RA y CE:

Puedes usar el siguiente prompt con una IA como ChatGPT, Claude, Gemini o DeepSeek, adjuntando el json y un pdf o documento de texto donde tengas los RA's y CE's de tu modulo:

********************************************************************************

Necesito generar un archivo JSON para configurar la estructura de calificaciones en Moodle/Aules.
El documento adjunto contiene los Resultados de Aprendizaje (RA) y Criterios de Evaluación (CE) de mi módulo.

Por favor, genera un JSON con la siguiente estructura basándote en la información del documento:

Base URL: https://aules.edu.gva.es/docent
Usuario: 11111111H
ID del curso: 112233
Configuración global: agregación Media ponderada de las calificaciones, calificación máxima 10.0, calificación para aprobar 5.0
Categoría padre: RA CE FEE

Estructura deseada para categorías hijas:
- Cada Resultado de Aprendizaje (RA) debe ser una categoría hija
- Cada Criterio de Evaluación (CE) debe ser un elemento dentro de la categoría del RA correspondiente

Por favor, genera el JSON completo con todos los RA y CE encontrados en el documento, tomando como ejemplo la estructura proporcionada en el json adjunto y extrayendo la informacion de RA y CE del documento pdf o de texto.


********************************************************************************

Copia este prompt y guardalo para usarlo mas tarde. Presiona Enter para continuar...

```

Y este es el json creado: `datos_aules_generado.json`:

```json
{
  "base_url": "https://aules.edu.gva.es/docent",
  "username": "11111111H",
  "password": "contraseña",
  "course_id": 112233,
  "configuracion_global": {
    "aggregation": 10,
    "aggregateonlygraded": false,
    "grademax": 10.0,
    "gradepass": 5.0
  },
  "categoria_padre": "RA CE FEE",
  "categorias_hijas": [
    {
      "nombre": "RA1: [Descripción del primer resultado de aprendizaje]",
      "elementos": [
        {
          "nombre": "CE1.1: [Primer criterio de evaluación]"
        },
        {
          "nombre": "CE1.2: [Segundo criterio de evaluación]"
        }
      ]
    },
    {
      "nombre": "RA2: [Descripción del segundo resultado de aprendizaje]",
      "elementos": [
        {
          "nombre": "CE2.1: [Primer criterio de evaluación]"
        },
        {
          "nombre": "CE2.2: [Segundo criterio de evaluación]"
        }
      ]
    }
  ]
}
```

