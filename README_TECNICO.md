# 🛠️ Documentación Técnica - Gestión de Calificaciones Aules

Este documento contiene información técnica detallada sobre la estructura, configuración y funcionamiento interno del script, destinada a desarrolladores o usuarios avanzados.

---

## 📂 Estructura del Proyecto

A continuación se detallan los archivos que componen este repositorio y su función:

| Fichero | Descripción |
| :--- | :--- |
| `calificaciones_aules.py` | Script principal en Python para la gestión del libro de calificaciones. |
| `calificaciones_aules.sh` | Script para Linux que crea el entorno virtual y ejecuta el script automáticamente. |
| `calificaciones_aules.bat` | Script equivalente para Windows (.bat). |
| `requirements.txt` | Lista de dependencias de Python necesarias (`requests`, `beautifulsoup4`, `tqdm`). |
| `empaquetar_appimage.sh` | Script para generar el AppImage en Linux (requiere `build.sh`). |
| `empaquetar_mac.sh` | Script para generar el binario en macOS. |
| `empaquetar_windows.bat` | Archivo de lotes para generar el ejecutable (.EXE) en Windows. |
| `build.sh` | Lógica de construcción para AppImage. |
| `gestor-calificaciones.ico/png` | Recursos visuales para los binarios. |

---

## ⚙️ Detalles de Configuración Avanzada

### Tipos de Agregación (Moodle/Aules)
Al configurar la clave `aggregation` en el archivo JSON, puedes usar los siguientes valores numéricos:

*   **0**: Media de las calificaciones.
*   **10**: Media ponderada de las calificaciones.
*   **11**: Media ponderada simple de las calificaciones.
*   **12**: Media de las calificaciones (con créditos extra).
*   **2**: Mediana de las calificaciones.
*   **4**: Calificación más baja.
*   **6**: Calificación más alta.
*   **8**: Moda de las calificaciones.
*   **13**: Natural (Suma de puntos).

### Notas sobre los Campos JSON
*   **`aggregationcoef`**: Es opcional. Por defecto es `0.0` para categorías y `1.0` para ítems. Define el peso del elemento en la media ponderada.
*   **`idnumber`**: Campo crucial para las fórmulas. Debe ser único dentro del curso.
*   **`formula`**: Utiliza la sintaxis de Moodle: `=[[ID_ITEM_1]]*0.5 + [[ID_ITEM_2]]*0.5`. Los ítems referenciados deben existir previamente.
*   **`ce_as_category`**: (Booleano) Si es `true`, los Criterios de Evaluación se crearán como **Categorías de Calificación** (nivel 3) en lugar de ítems simples. Esto permite anidar sub-tareas individuales dentro de cada criterio directamente en Aules. 

---


## 🖥️ Ejemplo Real de Ejecución (Logs)

A continuación se muestra una traza típica de la **Opción 0 (Generador de JSON)**:

```text
==================================================
GENERADOR DE ESTRUCTURA BÁSICA JSON
==================================================

--- DATOS DE CONEXIÓN ---
Selecciona la URL base de Aules:
  1: https://aules.edu.gva.es/docent (entorno de pruebas)
  2: https://aules.edu.gva.es/fp (FP Presencial)
  Opción (1-4): 1
Nombre de usuario (Tu DNI): 11111111H
ID del curso: 112233

--- CONFIGURACIÓN GLOBAL ---
Selecciona el tipo de agregación: 10
¿Considerar solo elementos calificados? (s/n): n
Calificación máxima: 10
Calificación mínima para aprobar: 5

--- CATEGORÍA PADRE ---
Nombre de la categoría padre: RA CE FEE

✓ Estructura básica guardada en 'datos_aules_generado.json'
```

---

## 🤖 Prompt completo para IA Generativa

Si deseas que una IA genere el JSON completo a partir de un PDF de tu programación, utiliza este esquema exacto:

> "Necesito generar un archivo JSON para configurar la estructura de calificaciones en Moodle/Aules. El documento adjunto contiene los Resultados de Aprendizaje (RA) y Criterios de Evaluación (CE) de mi módulo. 
> 
> Por favor, genera un JSON con esta estructura básica:
> - Base URL: [TU_URL]
> - Usuario: [TU_DNI]
> - Categoría padre: [NOMBRE]
> 
> Estructura: Cada RA debe ser una categoría hija y cada CE debe ser un elemento dentro de su RA. Incluye 'aggregationcoef' si el documento especifica pesos."

---

## 🔒 Detalles Técnicos de macOS (Avanzado)

Para usuarios que necesiten depurar o firmar manualmente el binario:
*   El binario se construye con `PyInstaller` usando el modo `--onefile`.
*   La firma ad-hoc se puede verificar con: `codesign -dvv Gestor_Calificaciones_Aules`.
*   El paquete `.dmg` se genera mediante `hdiutil` con el formato `UDZO`.
