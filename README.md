# 🎓 Gestor automatizado del cuaderno de calificación de Aules

> **Gestión eficiente, rápida y automatizada de estructuras de calificación en Aules (Moodle).**

[![Aules](https://img.shields.io/badge/Plataforma-Aules%20(Moodle)-orange.svg)](https://aules.edu.gva.es)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📺 Videotutorial: Funcionamiento Básico
Haz clic en la imagen inferior para ver cómo empezar a utilizar la herramienta:

[![Funcionamiento básico](https://img.youtube.com/vi/wSBCkJVSGhM/0.jpg)](https://www.youtube.com/watch?v=wSBCkJVSGhM)

---

## 🚀 ¿Qué es el Gestor automatizado del cuaderno de calificación de Aules?

Es una herramienta unificada con menú interactivo diseñada para docentes que necesitan gestionar estructuras complejas de calificación en la plataforma **Aules**. Olvídate de crear manualmente decenas de categorías y criterios de evaluación.

### ✨ Características Principales
- 🎨 **Nueva Interfaz Visual**: Aplicación moderna integrada (GUI) para una gestión sin comandos.
- 🛠️ **Gestión Integral**: Crea, actualiza fórmulas/pesos y elimina estructuras completas en segundos.
- 📝 **Configuración JSON**: Define toda tu programación en un simple archivo `datos_aules.json`.
- 🤖 **IA Friendly**: Incluye prompts optimizados para que ChatGPT/Claude generen tu configuración a partir de tu programación docente.
- 💻 **Multiplataforma**: Binarios listos para Windows, Linux (AppImage) y macOS (Apple Silicon/Intel).

> [!NOTE]
> Para detalles técnicos, estructura de archivos y opciones avanzadas, consulta la [**Guía Técnica para Desarrolladores**](file:///media/DADES/OneDriveGVA/DOCENCIA/25-26/AULES/GestionCalificacionesAules/README_TECNICO.md).

---

## 📥 Descargas (Releases)

| Asset | Sistema Operativo | Descripción |
| :--- | :--- | :--- |
| 🪟 `Gestor_Calificaciones_Aules.exe` | **Windows** | Ejecutable directo para Windows 10/11. |
| 🐧 `Gestor_de_Calificaciones_Aules.AppImage` | **GNU/Linux** | Formato universal. Ejecutar con `chmod +x` y `./fichero`. |
| 🍎 `AulesGradeManager.dmg` | **macOS** | Instalador para sistemas Mac (ver guía de seguridad abajo). |

---

## ⚙️ Configuración y Persistencia de Datos (`datos_aules.json`)

La aplicación utiliza un sistema de **Ruta Inteligente** para buscar y guardar tus configuraciones de forma segura:

1.  **Modo Portable**: El sistema busca primero en la **misma carpeta** donde se encuentra el ejecutable. Esto es ideal para llevar la App y tus datos en un pendrive.
2.  **Modo Instalado (Recomendado)**: Si no existe un archivo local, la aplicación guardará y buscará tus datos automáticamente en tu carpeta personal de **Documentos**, dentro de la subcarpeta `GestionCalificacionesAules`.

> [!TIP]
> **Usuarios de macOS**: Si ejecutas la App desde Aplicaciones o desde un disco virtual (.dmg), tus configuraciones se guardarán automáticamente en tu carpeta de Documentos para evitar errores de permisos.

```json
{
  "base_url": "https://aules.edu.gva.es/docent",
  "username": "12345678H",
  "password": "tu_contraseña",
  "course_id": 112233,
  "configuracion_global": {
    "aggregation": 10,
    "aggregateonlygraded": false,
    "grademax": 10,
    "gradepass": 5,
    "ce_as_category": false
  },
  "categoria_padre": "Nombre categoría principal",

  "categorias_hijas": [
    {
      "nombre": "RA1: Resultado de Aprendizaje 1",
      "aggregationcoef": 2,
      "elementos": [
        "CE 1.1 Examen Teórico",
        {
          "nombre": "CE 1.2 Práctica Final",
          "aggregationcoef": 2,
          "formula": "=[[EXAM]]*0.4+[[PRAC]]*0.6",
          "idnumber": "ID_CE12"
        }
      ]
    }
  ]
}
```

> [!TIP]
> **Opciones de Agregación más comunes**: 
> - `0`: Media aritmética.
> - `10`: Media ponderada.
> - `13`: Natural (Suma).

---

## 🌐 Información de Referencia

### 🔗 URLs Base Soportadas
- **Entorno de Pruebas**: `https://aules.edu.gva.es/docent`
- **FP Presencial**: `https://aules.edu.gva.es/fp`
- **FP Semipresencial**: `https://aules.edu.gva.es/semipresencial`

### 📊 Opciones de Agregación
| Código | Tipo de Agregación | Descripción |
| :--- | :--- | :--- |
| **0** | Media | Media de todas las calificaciones. |
| **10** | Media ponderada | Media basada en pesos (`aggregationcoef`). |
| **13** | Natural | Suma de puntos de todos los elementos. |
| **2** | Mediana | Valor central de las calificaciones. |
| **11** | Media ponderada simple | Media ponderada automática. |

> [!TIP]
> Para ver el listado técnico completo de agregaciones, consulta el [README_TECNICO.md](file:///media/DADES/OneDriveGVA/DOCENCIA/25-26/AULES/GestionCalificacionesAules/README_TECNICO.md).

---

## 🛠️ Modo de Empleo

### 🔄 Flujo de Trabajo Recomendado
1. **Paso 0**: Generar la plantilla inicial con la **Opción 0** del menú.
2. **Paso 1**: Editar `datos_aules_generado.json` (puedes usar el prompt de IA de abajo).
3. **Paso 2**: Renombrar el archivo final a `datos_aules.json`.
4. **Paso 3**: Ejecutar la **Opción 1** para subir la estructura a Aules.

### 💻 Ejemplo de Ejecución (Opción 0)
```text
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
5. Añadir `ce_as_category: true` si prefieres que los Criterios de Evaluación se creen como categorías en lugar de ítems simples.
6. Añadir más categorías hijas y elementos si es necesario


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

[<img align="left" height="18px" alt="martinezpenya | Sponsor" src="https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86" />](https://github.com/sponsors/martinezpenya)
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/martinezpenya)

---

## 🎨 Nueva Interfaz Gráfica (GUI)

La versión actual incluye una interfaz moderna basada en **CustomTkinter** que permite gestionar todo de forma visual:

1. **Dashboard de Inicio**: Estado de conexión y acciones rápidas.
2. **Ajustes Avanzados**: Configura tu usuario, contraseña, entorno y la nueva opción de **CE como categorías**.
3. **Editor JSON**: Vista previa de tu configuración.
4. **Consola en vivo**: Sigue el progreso de las operaciones en tiempo real.


Para ejecutar la versión visual, simplemente abre el ejecutable (`.exe`, `.AppImage` o `.dmg`) descargado de las Release.

---

## 🛠️ Desarrollo y Ejecución Local

Si prefieres ejecutar el código fuente:

```bash
git clone https://github.com/martinezpenya/GestionCalificacionesAules.git
cd GestionCalificacionesAules
pip install -r requirements.txt
# Para la versión visual:
python gui_aules.py
# Para la versión de terminal:
python calificaciones_aules.py
```
