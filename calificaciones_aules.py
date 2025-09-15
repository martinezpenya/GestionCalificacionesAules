"""
Script de Gestión de Calificaciones para Aules (Moodle)
=======================================================

Autores:
- Idea inicial: Manuel Sanchez (Nelo) me.sanchezgomis@edu.gva.es
- Ampliación de funcionalidades, comentarios y reusabilidad: David Martinez (www.martinezpenya.es)

DESCRIPCIÓN:
Script unificado con menú interactivo para gestionar estructuras de calificación en Moodle/Aules.
Permite crear, actualizar fórmulas, eliminar estructuras completas y generar plantillas de configuración.

CARACTERÍSTICAS PRINCIPALES:
- Menú interactivo con 5 opciones principales
- Gestión completa de categorías y elementos de calificación
- Soporte para fórmulas de cálculo personalizadas
- Configuración mediante archivo JSON (datos_aules.json)
- Detección automática del entorno de ejecución (AppImage vs desarrollo)

OPCIONES DEL MENÚ:
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

ESTRUCTURA DEL ARCHIVO JSON (datos_aules.json):
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

URLs BASE SOPORTADAS:
- https://aules.edu.gva.es/docent (entorno de pruebas)
- https://aules.edu.gva.es/fp (FP Presencial)
- https://aules.edu.gva.es/semipresencial (FP Semipresencial)

OPCIONES DE AGREGACIÓN:
-  0: Media de las calificaciones
- 10: Media ponderada de las calificaciones
- 11: Media ponderada simple de las calificaciones
- 12: Media de las calificaciones (con créditos extra)
-  2: Mediana de las calificaciones
-  4: Calificación más baja
-  6: Calificación más alta
-  8: Moda de las calificaciones
- 13: Natural

NOTAS IMPORTANTES:
- Opciones 1, 2 y 3 requieren datos_aules.json
- aggregationcoef es opcional (0.0 categorías, 1.0 items por defecto)
- Fórmulas usan sintaxis Moodle: =[[NOMBRE_ITEM]]
- idnumber identifica elementos únicamente
- Se recomienda ejecutar como AppImage para mejor portabilidad

FLUJO DE TRABAJO RECOMENDADO:
1. Ejecutar opción 0 para generar plantilla básica
2. Editar manualmente el JSON generado
3. Usar IA generativa (ChatGPT, Claude, etc.) para completar RA y CE
4. Renombrar archivo a datos_aules.json
5. Ejecutar opción 1 para crear estructura online

SOPORTE PARA IA GENERATIVA:
Incluye prompt específico para crear JSON completos a partir de documentos con RA y CE.
"""

import requests
import re
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
import urllib.parse
import time
import os
import argparse
import sys

# Detectar si estamos en modo AppImage (esta línea ya debería estar)
def is_appimage():
    """Check if running as AppImage"""
    return hasattr(sys, '_MEIPASS') or 'APPIMAGE' in os.environ

def get_appimage_path():
    """Obtiene la ruta base cuando se ejecuta como AppImage"""
    if is_appimage():
        # Cuando es AppImage, la ruta base es donde está el ejecutable
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # Cuando se ejecuta normalmente, usar el directorio del script
        return os.path.dirname(os.path.abspath(__file__))

def login(session, base_url, username, password):
    """Inicia sesión en Aules y devuelve las cookies y la clave de sesión."""
    print("Iniciando sesión...")

    # Primero intentamos obtener la página principal para ver si ya estamos logueados
    r = session.get(f"{base_url}/my/")

    # Verificamos si ya estamos logueados buscando el enlace de logout
    if 'logout' in r.text.lower():
        print("Sesión ya activa detectada.")
        # Extraemos el sesskey de la página
        sesskey_match = re.search(r'sesskey=(\w+)', r.text)
        if sesskey_match:
            sesskey = sesskey_match.group(1)
            print("Sesión recuperada correctamente.")
            return session.cookies.get_dict(), sesskey

    # Si no estamos logueados, procedemos con el login normal
    r = session.get(f"{base_url}/login/index.php")
    cookie = r.cookies.get_dict()

    # Buscamos el token de login
    pattern = r'<input type="hidden" name="logintoken" value="\w{32}">'
    token_matches = re.findall(pattern, r.text)

    if not token_matches:
        print("Error: No se pudo encontrar el token de login")
        return None, None

    token = re.findall(r"\w{32}", token_matches[0])
    if not token:
        print("Error: No se pudo extraer el token de login")
        return None, None

    payload = {'username': username, 'password': password, 'anchor': '', 'logintoken': token[0]}
    r = session.post(f"{base_url}/login/index.php", cookies=cookie, data=payload)

    # Buscamos la clave de sesión
    sesskey_matches = re.findall(r'sesskey=(\w+)', r.text)
    if not sesskey_matches:
        print("Error: No se pudo encontrar la clave de sesión")
        return None, None

    sesskey = sesskey_matches[0]
    print("Sesión iniciada correctamente.")
    return session.cookies.get_dict(), sesskey

def generar_estructura_basica():
    """Guía al usuario para generar una estructura básica de JSON"""
    if 'APPIMAGE' in os.environ:
        base_dir = os.path.dirname(os.environ.get('APPIMAGE'))

    # Determinar el directorio de escritura
        #DAVID
        #base_dir = os.path.expanduser("~")
        #base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        #base_dir = os.path.dirname(os.path.abspath(__file__))
    # Determinar el directorio de escritura
    elif getattr(sys, 'frozen', False):
        # En modo AppImage, usar el directorio del ejecutable
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        print(f"Modo AppImage: guardando en {base_dir}")
    else:
        # En modo normal, usar el directorio actual
        base_dir = os.getcwd()

    print(f"{base_dir}")
    nombre_archivo = "datos_aules_generado.json"
    json_path = os.path.join(base_dir, nombre_archivo)



    print("\n" + "="*50)
    print("GENERADOR DE ESTRUCTURA BÁSICA JSON")
    print("="*50)

    # Datos básicos de conexión
    print("\n--- DATOS DE CONEXIÓN ---")

    # Opciones de URL base
    opciones_url = {
        "1": "https://aules.edu.gva.es/docent (entorno de pruebas)",
        "2": "https://aules.edu.gva.es/fp (FP Presencial)",
        "3": "https://aules.edu.gva.es/semipresencial (FP Semipresencial)",
        "4": "Otra URL (escribir manualmente)"
    }

    print("Selecciona la URL base de Aules:")
    for key, value in opciones_url.items():
        print(f"  {key}: {value}")

    while True:
        opcion_url = input("Opción (1-4): ")
        if opcion_url in opciones_url:
            break
        print("Opción no válida. Por favor, selecciona 1, 2, 3 o 4.")

    if opcion_url == "1":
        base_url = "https://aules.edu.gva.es/docent"
    elif opcion_url == "2":
        base_url = "https://aules.edu.gva.es/fp"
    elif opcion_url == "3":
        base_url = "https://aules.edu.gva.es/semipresencial"
    else:
        base_url = input("Introduce la URL base personalizada: ")

    username = input("Nombre de usuario (Tu DNI): ")
    password = input("Contraseña (de AULES): ")
    course_id = input("ID del curso (cuando entres al curso el ultimo numero de 6 digitos que aparece detras del view.php?id=XXXXXX): ")

    # Configuración global
    print("\n--- CONFIGURACIÓN GLOBAL ---")

    # Opciones de agregación
    opciones_agregacion = {
        "0": "Media de las calificaciones",
        "10": "Media ponderada de las calificaciones",
        "11": "Media ponderada simple de las calificaciones",
        "12": "Media de las calificaciones (con créditos extra)",
        "2": "Mediana de las calificaciones",
        "4": "Calificación más baja",
        "6": "Calificación más alta",
        "8": "Moda de las calificaciones",
        "13": "Natural"
    }

    print("Opciones de agregación:")
    for key, value in opciones_agregacion.items():
        print(f"  {key}: {value}")

    aggregation = input("Selecciona el tipo de agregación: ") or "10"

    aggregateonlygraded = input("¿Considerar solo elementos calificados? (s/n): ").lower() or "s"
    aggregateonlygraded = True if aggregateonlygraded == "s" else False

    grademax = float(input("Calificación máxima (por ejemplo 10): ") or "10")
    gradepass = float(input("Calificación mínima para aprobar (por ejemplo 5): ") or "5")

    # Categoría padre
    print("\n--- CATEGORÍA PADRE ---")
    categoria_padre = input("Nombre de la categoría padre (por ejemplo: 'RA CE FEE'): ")

    # Categorías hijas básicas
    print("\n--- CATEGORÍAS HIJAS BÁSICAS ---")
    print("Se generarán 2 categorías hijas básicas (RA1 y RA2) con algunos criterios de evaluación.")

    categorias_hijas = [
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

    # Construir el JSON
    estructura = {
        "base_url": base_url,
        "username": username,
        "password": password,
        "course_id": int(course_id),
        "configuracion_global": {
            "aggregation": int(aggregation),
            "aggregateonlygraded": aggregateonlygraded,
            "grademax": grademax,
            "gradepass": gradepass
        },
        "categoria_padre": categoria_padre,
        "categorias_hijas": categorias_hijas
    }



    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(estructura, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Estructura básica guardada en '{json_path}'")

    except PermissionError:
        print(f"Error: No se puede escribir en {json_path}")
        print("Intenta ejecutar con permisos de administrador o elige otra ubicación.")
        return
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")
        return

    print("\nRECOMENDACIÓN: Edita manualmente el archivo para:")
    print("1. Completar las descripciones de los RA y CE")
    print("2. Añadir fórmulas de cálculo si es necesario (Solo CE)(usar sintaxis Moodle: =[[NOMBRE_ITEM]])")
    print("   Los identificadores que uses en las formulas deben existir previamente, sino la formula no se aplicara")
    print("3. Añadir idnumber (Solo CE) para identificar elementos de forma única")
    print("4. Añadir aggregationcoef (Solo Categorias hijas (RA) y CE) para indicar el peso del elemento en la ponderacion")
    print("5. Añadir más categorías hijas y elementos si es necesario")
    print("\n  EJEMPLOS:")
    print('  - "formula": "=[[1AVA]]"')
    print('  - "formula": "=([[1AVA]]*0.5)+([[FEE]]*0.5)"')
    print('  - "idnumber": "ID_UNICO_001"')
    print("5. Recuerda que el json se debe llamar exactamente datos_aules.json (renombralo)")

    # Sugerencia para IA generativa
    print("\n" + "="*50)
    print("SUGERENCIA PARA IA GENERATIVA")
    print("="*50)
    print("Para generar automáticamente un JSON completo a partir de un documento con los RA y CE:")
    print("\nPuedes usar el siguiente prompt con una IA como ChatGPT, Claude, Gemini o DeepSeek, adjuntando el json y un pdf o documento de texto donde tengas los RA's y CE's de tu modulo:")
    print("\n" + "*"*80)

    prompt = f"""
Necesito generar un archivo JSON para configurar la estructura de calificaciones en Moodle/Aules.
El documento adjunto contiene los Resultados de Aprendizaje (RA) y Criterios de Evaluación (CE) de mi módulo.

Por favor, genera un JSON con la siguiente estructura basándote en la información del documento:

Base URL: {base_url}
Usuario: {username}
ID del curso: {course_id}
Configuración global: agregación {opciones_agregacion[aggregation]}, calificación máxima {grademax}, calificación para aprobar {gradepass}
Categoría padre: {categoria_padre}

Estructura deseada para categorías hijas:
- Cada Resultado de Aprendizaje (RA) debe ser una categoría hija
- Cada Criterio de Evaluación (CE) debe ser un elemento dentro de la categoría del RA correspondiente
- Para cada elemento, incluye comentarios sobre cómo añadir fórmulas e idnumber si es necesario
- Las fórmulas deben usar la sintaxis de Moodle con referencias como [[1AVA]], [[2AVA]], [[3AVA]], [[FEE]], etc.

Por favor, genera el JSON completo con todos los RA y CE encontrados en el documento, tomando como ejemplo la estructura proporcionada en el json adjunto y extrayendo la informacion de RA y CE del documento pdf o de texto.
"""

    print(prompt)
    print("\n" + "*"*80)
    input("\nCopia este prompt y guardalo para usarlo mas tarde. Presiona Enter para continuar...")

def get_json_path():
    """Obtiene la ruta correcta del archivo JSON para AppImage y modo normal"""
    posibles_rutas = []

    # 1. Directorio del AppImage/ejecutable (prioridad máxima)
    if getattr(sys, 'frozen', False):
        appimage_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        posibles_rutas.append(os.path.join(appimage_dir, 'datos_aules.json'))
        print(f"Buscando en directorio AppImage: {appimage_dir}")

    # 2. Directorio home del usuario
    home_dir = os.path.expanduser("~")
    posibles_rutas.append(os.path.join(home_dir, 'datos_aules.json'))

    # 3. Directorio actual de trabajo
    posibles_rutas.append(os.path.join(os.getcwd(), 'datos_aules.json'))

    # 4. Directorio del script (modo desarrollo)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    posibles_rutas.append(os.path.join(script_dir, 'datos_aules.json'))

    # Buscar en todas las rutas posibles
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            print(f"JSON encontrado en: {ruta}")
            return ruta

    # Si no se encuentra, devolver la ruta del directorio AppImage para creación
    if getattr(sys, 'frozen', False):
        return os.path.join(appimage_dir, 'datos_aules.json')
    else:
        return os.path.join(os.getcwd(), 'datos_aules.json')

def cargar_datos_json():
    """Carga los datos del archivo JSON y devuelve los parámetros necesarios"""
    try:
        # Usar la función mejorada para encontrar el JSON
        json_path = get_json_path()
        print(f"Buscando JSON en: {json_path}")

        if not os.path.exists(json_path):
            print("ERROR: No se encontró datos_aules.json")
            print("Por favor, coloca el archivo datos_aules.json en la misma carpeta que el ejecutable.")
            print(f"Directorio actual: {os.getcwd()}")
            if is_appimage():
                # Mostrar información de depuración
                print(f"Directorio del ejecutable: {os.path.dirname(os.path.abspath(sys.argv[0]))}")
                print(f"Archivos en directorio actual: {os.listdir('.')}")
            return None

        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Verificar que existen las claves necesarias
        required_keys = ["base_url", "username", "password", "course_id", "categoria_padre", "categorias_hijas", "configuracion_global"]
        for key in required_keys:
            if key not in data:
                print(f"Error: La clave '{key}' no existe en el archivo JSON")
                return None

        return data

    except FileNotFoundError:
        print("Error: No se encontró el archivo datos_aules.json")
        return None
    except KeyError as e:
        print(f"Error: Falta la clave {e} en el archivo JSON")
        return None
    except Exception as e:
        print(f"Error inesperado al cargar JSON: {e}")
        return None

def obtener_elementos_curso(session, cookie, base_url, course_id):
    """Obtiene todos los elementos de calificación del curso con análisis mejorado."""
    print("Obteniendo elementos del curso...")
    r = session.get(f"{base_url}/grade/edit/tree/index.php?id={course_id}")

    if r.status_code != 200:
        print(f"Error al acceder al curso: {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    elementos = []

    # Encontrar todas las filas de la tabla de calificaciones
    rows = soup.find_all('tr', {'class': ['category', 'item']})

    for row in rows:
        try:
            # Determinar el tipo de elemento
            if 'category' in row.get('class', []):
                # Es una categoría
                category_id = row.get('data-category', '')
                parent_category_id = row.get('data-parent-category', '')

                if not category_id:
                    continue

                # Obtener el nombre de la categoría
                name_cell = row.find('td', class_='column-name')
                if not name_cell:
                    continue

                # Buscar el nombre en el elemento con clase rowtitle
                rowtitle = name_cell.find('div', class_='rowtitle')
                if rowtitle:
                    name = rowtitle.get_text(strip=True)
                else:
                    # Fallback: obtener texto de la celda
                    name = name_cell.get_text(strip=True)

                if not name:
                    continue

                # Obtener nivel de indentación desde la clase
                nivel = 0
                class_list = name_cell.get('class', [])
                for cls in class_list:
                    if cls.startswith('level'):
                        try:
                            nivel = int(cls.replace('level', ''))
                            break
                        except ValueError:
                            continue

                elementos.append({
                    "tipo": "category",
                    "id": category_id,  # Mantener ID completo (cg183428)
                    "nombre": name,
                    "nivel": nivel,
                    "categoria_padre_id": parent_category_id if parent_category_id else ''
                })

            elif 'item' in row.get('class', []):
                # Es un elemento de calificación - CORREGIDO
                # Extraer el ID completo del item (ig1281062) del atributo id del tr
                item_id_full = row.get('id', '')
                if not item_id_full or not item_id_full.startswith('grade-item-ig'):
                    continue

                # Extraer solo la parte numérica para data-itemid
                item_id_numeric = row.get('data-itemid', '')
                parent_category_id = row.get('data-parent-category', '')

                # Obtener el nombre del item
                name_cell = row.find('td', class_='column-name')
                if not name_cell:
                    continue

                # Buscar el nombre en el elemento con clase rowtitle o gradeitemheader
                rowtitle = name_cell.find('div', class_='rowtitle')
                gradeitemheader = name_cell.find('span', class_='gradeitemheader')

                if rowtitle:
                    name = rowtitle.get_text(strip=True)
                elif gradeitemheader:
                    name = gradeitemheader.get_text(strip=True)
                else:
                    # Fallback: obtener texto de la celda
                    name = name_cell.get_text(strip=True)

                if not name:
                    continue

                # Usar el ID completo del item (ig1281062)
                item_id = item_id_full.replace('grade-item-', '')

                elementos.append({
                    "tipo": "item",
                    "id": item_id,  # ID completo (ig1281062)
                    "id_numerico": item_id_numeric,  # ID numérico por si acaso
                    "nombre": name,
                    "categoria_id": parent_category_id if parent_category_id else ''
                })

        except Exception as e:
            print(f"Advertencia: Error al procesar fila: {e}")
            continue

    return elementos

def eliminar_elemento(session, cookie, base_url, sesskey, course_id, elemento, verificar_eliminacion):
    """Elimina un elemento (categoría o item) del curso con la URL correcta."""
    try:
        # URL CORRECTA para ambos casos (categorías e items)
        if elemento["tipo"] == "category":
            url = f"{base_url}/grade/edit/tree/index.php?id={course_id}&action=delete&confirm=1&eid={elemento['id']}&sesskey={sesskey}&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}"
        else:  # item
            # Usar el ID completo del item (ig1281062)
            url = f"{base_url}/grade/edit/tree/index.php?id={course_id}&action=delete&confirm=1&eid={elemento['id']}&sesskey={sesskey}&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}"

        print(f"Eliminando: {elemento['nombre']}")
        r = session.get(url, cookies=cookie)

        # Si no se requiere verificación, asumimos éxito sin comprobaciones
        if not verificar_eliminacion:
            return True

        # Verificación opcional de eliminación (solo si está activada)
        if r.status_code == 200:
            # Verificación más robusta: buscar indicadores de éxito
            if ("itemdeleted" in r.text.lower() or
                "categorydeleted" in r.text.lower() or
                "success" in r.text.lower() or
                "redirect" in r.text.lower() or
                "location.replace" in r.text.lower()):
                return True
            else:
                # Verificar si realmente hay un error
                error_patterns = [
                    "cannot delete", "no se puede eliminar", "error", "exception",
                    "problema", "no tiene permisos", "permission denied"
                ]
                for pattern in error_patterns:
                    if pattern in r.text.lower():
                        print(f"✗ Error real detectado al eliminar {elemento['nombre']}")
                        return False

                # Si no encontramos errores específicos, asumimos que fue exitoso
                return True
        else:
            print(f"✗ Error HTTP {r.status_code} al eliminar {elemento['nombre']}")
            return False

    except Exception as e:
        print(f"Error al eliminar elemento {elemento['nombre']}: {e}")
        return False

def encontrar_categoria_por_nombre(elementos, nombre):
    """Encuentra una categoría por su nombre con búsqueda flexible."""
    for elemento in elementos:
        if elemento["tipo"] == "category":
            elem_nombre = elemento["nombre"]
            # Buscar coincidencia exacta o que comience con el nombre
            if elem_nombre == nombre or elem_nombre.startswith(nombre):
                return elemento
    return None

def encontrar_elementos_por_categoria(elementos, categoria_id):
    """Encuentra todos los elementos que pertenecen a una categoría."""
    elementos_relacionados = []

    # Encontrar categorías hijas (directas)
    for elemento in elementos:
        if (elemento["tipo"] == "category" and
            elemento.get("categoria_padre_id") == categoria_id):
            elementos_relacionados.append(elemento)
            # Buscar recursivamente elementos de esta categoría hija
            elementos_relacionados.extend(encontrar_elementos_por_categoria(elementos, elemento["id"]))

    # Encontrar items dentro de la categoría
    for elemento in elementos:
        if elemento["tipo"] == "item" and elemento["categoria_id"] == categoria_id:
            elementos_relacionados.append(elemento)

    return elementos_relacionados

def get_categoria_payload(sesskey, course_id, name, parent_id=0, config_global=None, aggregationcoef=0.0):
    # Configuración por defecto
    if config_global is None:
        config_global = {
            "aggregation": 0,  # Natural por defecto
            "aggregateonlygraded": 1,  # True por defecto
            "grademax": 100,  # 100 por defecto
            "gradepass": 50   # 50 por defecto
        }

    # Asegurar que los valores sean los correctos
    aggregation = config_global.get("aggregation", 0)
    aggregateonlygraded = 1 if config_global.get("aggregateonlygraded", True) else 0
    grademax = config_global.get("grademax", 100)
    gradepass = config_global.get("gradepass", 50)

    parent = ""
    if parent_id > 0:
        parent = f"&parentcategory={parent_id}"

    formdata = f"id=0&courseid={course_id}&category=-1&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}&sesskey={sesskey}&_qf__core_grades_form_add_category=1&fullname={name}&aggregation={aggregation}&aggregateonlygraded={aggregateonlygraded}&droplow=0&grade_item_gradetype=1&grade_item_grademax={grademax}&grade_item_grademin=0&grade_item_gradepass={gradepass}&grade_item_weightoverride=0&grade_item_aggregationcoef={aggregationcoef}{parent}"

    data = [
        {
            "index": 0,
            "methodname": "core_form_dynamic_form",
            "args": {
                "formdata": formdata,
                "form": "core_grades\\form\\add_category"
            }
        }
    ]

    return json.dumps(data)

def get_item_payload(sesskey, course_id, name, parent_id, config_global=None, idnumber="", aggregationcoef=1.0):
    # Configuración por defecto para items
    if config_global is None:
        config_global = {
            "grademax": 100,
            "gradepass": 50
        }

    grademax = config_global.get("grademax", 100)
    gradepass = config_global.get("gradepass", 50)

    # Incluir idnumber y aggregationcoef en el formdata si se proporciona
    idnumber_field = f"&idnumber={urllib.parse.quote(idnumber)}" if idnumber else ""
    aggregationcoef_field = f"&aggregationcoef={aggregationcoef}"

    formdata = f"id=0&courseid={course_id}&itemid=-1&itemtype=manual&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}&sesskey={sesskey}&_qf__core_grades_form_add_item=1&itemname={name}{idnumber_field}&gradetype=1&grademax={grademax}&grademin=0.00&gradepass={gradepass}&hidden=0&locked=0&aggregationcoef={aggregationcoef}&parentcategory={parent_id}"

    data = [
        {
            "index": 0,
            "methodname": "core_form_dynamic_form",
            "args": {
                "formdata": formdata,
                "form": "core_grades\\form\\add_item"
            }
        }
    ]

    return json.dumps(data)

def obtener_id_categoria(session, cookie, base_url, sesskey, course_id, nombre_categoria):
    """Función auxiliar para obtener el ID de una categoría por su nombre"""
    payload = [
        {
            "index": 0,
            "methodname": "core_form_dynamic_form",
            "args": {
                "formdata": f"category=-1&courseid={course_id}&gpr_plugin=tree",
                "form": "core_grades\\form\\add_category"
            }
        }
    ]

    url = f"{base_url}/lib/ajax/service.php?sesskey={sesskey}&info=core_form_dynamic_form"
    r = session.post(url, cookies=cookie, data=json.dumps(payload))

    pattern = r'<option value="(\d+)"[\s\n]*>([^<]+)</option>'
    options = re.findall(pattern, r.json()[0]["data"]["html"])

    for o in options:
        if o[1] == nombre_categoria:
            return int(o[0])

    return 0

def obtener_id_item(session, cookie, base_url, sesskey, course_id, nombre_item):
    """Función auxiliar para obtener el ID de un item por su nombre"""
    try:
        # Obtener la página de gestión de calificaciones
        url = f"{base_url}/grade/edit/tree/index.php?id={course_id}"
        r = session.get(url, cookies=cookie)

        if r.status_code != 200:
            print(f"Error al obtener página de calificaciones: {r.status_code}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        trs = soup.find_all("tr")

        for tr in trs:
            # Buscar items (elementos de calificación)
            if "class" in tr.attrs and "item" in tr.attrs["class"]:
                # Extraer el nombre del item
                nombre_celda = tr.find("td", class_="cell")
                if nombre_celda:
                    # Buscar el span con la clase gradeitemheader que contiene el nombre real
                    gradeitem_span = nombre_celda.find("span", class_="gradeitemheader")
                    if gradeitem_span:
                        item_name = gradeitem_span.get_text(strip=True)

                        # Comparar con el nombre que buscamos
                        if item_name == nombre_item:
                            # El ID está en el atributo data-itemid del TR
                            if "data-itemid" in tr.attrs:
                                item_id = tr.attrs["data-itemid"]
                                print(f"ID del item '{item_name}': {item_id}")
                                return item_id

        print(f"Error: No se pudo obtener el ID del item '{nombre_item}'")
        return None

    except Exception as e:
        print(f"Error en obtener_id_item: {e}")
        return None

def modificar_gradepass_item(session, cookie, base_url, sesskey, course_id, item_id, item_nombre, config_global, item_idnumber="", aggregationcoef=1.0):
    """Modifica el campo gradepass, idnumber y aggregationcoef de un item específico"""
    print(f"Modificando item: {item_nombre} (ID: {item_id})")

    # Configuración para items
    grademax = config_global.get("grademax", 10)
    gradepass = config_global.get("gradepass", 5)

    # Codificar los valores para URL
    nombre_codificado = urllib.parse.quote(item_nombre)
    idnumber_codificado = urllib.parse.quote(item_idnumber) if item_idnumber else ""

    # Incluir idnumber en el formdata
    idnumber_field = f"&idnumber={idnumber_codificado}" if item_idnumber else ""

    formdata = (
        f"id={item_id}&"
        f"courseid={course_id}&"
        f"itemtype=manual&"
        f"gpr_type=edit&"
        f"gpr_plugin=tree&"
        f"gpr_courseid={course_id}&"
        f"sesskey={sesskey}&"
        f"_qf__edit_item_form=1&"
        f"mform_isexpanded_id_general=1&"
        f"itemname={nombre_codificado}&"
        f"iteminfo=&"
        f"{idnumber_field}&"  # ← Campo idnumber añadido
        f"gradetype=1&"
        f"grademax={grademax}&"
        f"grademin=0&"
        f"gradepass={gradepass}&"
        f"display=0&"
        f"decimals=-1&"
        f"hidden=0&"
        f"locked=0&"
        f"aggregationcoef={aggregationcoef}&"  # ← Campo aggregationcoef añadido
        f"submitbutton=Guarda+els+canvis"
    )

    # Enviar la solicitud POST al formulario de edición del item
    url = f"{base_url}/grade/edit/tree/item.php"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = session.post(url, cookies=cookie, data=formdata, headers=headers)

    if r.status_code == 200:
        print(f"Item '{item_nombre}' modificado correctamente (gradepass: {gradepass}, idnumber: {item_idnumber}, aggregationcoef: {aggregationcoef})")
        return True
    else:
        print(f"Error al modificar el item '{item_nombre}': {r.status_code}")
        return False

def modificar_formula_item(session, cookie, base_url, sesskey, course_id, item_id, item_nombre, formula):
    """Modifica la fórmula de cálculo de un item específico"""
    if formula == "":
        print(f"Eliminando fórmula del item: {item_nombre} (ID: {item_id})")
        accion = "eliminada"
    else:
        print(f"Modificando fórmula del item: {item_nombre} (ID: {item_id})")
        accion = "modificada"

    # Construir el payload para la solicitud POST
    formdata = (
        f"id={item_id}&"
        f"courseid={course_id}&"
        f"section=calculation&"
        f"gpr_type=edit&"
        f"gpr_plugin=tree&"
        f"gpr_courseid={course_id}&"
        f"sesskey={sesskey}&"
        f"_qf__edit_calculation_form=1&"
        f"mform_isexpanded_id_general=1&"
        f"calculation={urllib.parse.quote(formula)}&"
        f"submitbutton=Guarda+els+canvis"
    )

    # Enviar la solicitud POST al formulario de cálculo
    url = f"{base_url}/grade/edit/tree/calculation.php"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = session.post(url, cookies=cookie, data=formdata, headers=headers)

    if r.status_code == 200:
        if formula == "":
            print(f"Fórmula del item '{item_nombre}' eliminada correctamente")
        else:
            print(f"Fórmula del item '{item_nombre}' {accion} correctamente: {formula}")
        return True
    else:
        print(f"Error al {accion} la fórmula del item '{item_nombre}': {r.status_code}")
        return False

def modificar_gradepass_categoria(session, cookie, base_url, sesskey, course_id, categoria_id, categoria_nombre, config_global, aggregationcoef=0.0):
    """Modifica el campo gradepass y aggregationcoef de una categoría específica"""
    print(f"Modificando categoría: {categoria_nombre} (ID: {categoria_id})")

    # Construir el payload basado en el formulario de edición
    aggregation = config_global.get("aggregation", 0)
    aggregateonlygraded = 1 if config_global.get("aggregateonlygraded", True) else 0
    grademax = config_global.get("grademax", 100)
    gradepass = config_global.get("gradepass", 50)

    # Codificar el nombre para URL
    nombre_codificado = urllib.parse.quote(categoria_nombre)

    formdata = (
        f"mform_isexpanded_id_general=1&"
        f"mform_isexpanded_id_headerparent=1&"
        f"id={categoria_id}&"
        f"courseid={course_id}&"
        f"gpr_type=edit&"
        f"gpr_plugin=tree&"
        f"gpr_courseid={course_id}&"
        f"sesskey={sesskey}&"
        f"_qf__edit_category_form=1&"
        f"mform_isexpanded_id_headercategory=1&"
        f"fullname={nombre_codificado}&"
        f"aggregation={aggregation}&"
        f"aggregateonlygraded={aggregateonlygraded}&"
        f"droplow=0&"
        f"grade_item_itemname=&"
        f"grade_item_iteminfo=&"
        f"grade_item_idnumber=&"
        f"grade_item_gradetype=1&"
        f"grade_item_grademax={grademax}&"
        f"grade_item_grademin=0&"
        f"grade_item_gradepass={gradepass}&"
        f"grade_item_display=0&"
        f"grade_item_decimals=-1&"
        f"grade_item_aggregationcoef={aggregationcoef}&"  # ← Campo aggregationcoef añadido
        f"grade_item_weightoverride=0&"
        f"submitbutton=Guarda+els+canvis"
    )

    # Enviar la solicitud POST al formulario de edición de la categoría
    url = f"{base_url}/grade/edit/tree/category.php"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = session.post(url, cookies=cookie, data=formdata, headers=headers)

    if r.status_code == 200:
        print(f"Categoría '{categoria_nombre}' modificada correctamente (gradepass: {gradepass}, aggregationcoef: {aggregationcoef})")
        return True
    else:
        print(f"Error al modificar la categoría '{categoria_nombre}': {r.status_code}")
        return False

def crear_categoria(session, cookie, base_url, sesskey, course_id, nombre, parent_id=0, config_global=None, aggregationcoef=0.0):
    """Crea una categoría en el libro de calificaciones."""
    print(f"Creando categoría: {nombre}")

    # Configuración por defecto
    if config_global is None:
        config_global = {
            "aggregation": 0,  # Natural por defecto
            "aggregateonlygraded": 1,  # True por defecto
            "grademax": 100,  # 100 por defecto
            "gradepass": 50   # 50 por defecto
        }

    # Asegurar que los valores sean los correctos
    aggregation = config_global.get("aggregation", 0)
    aggregateonlygraded = 1 if config_global.get("aggregateonlygraded", True) else 0
    grademax = config_global.get("grademax", 100)
    gradepass = config_global.get("gradepass", 50)

    # Construir el payload para la solicitud POST
    formdata = (
        f"id=0&"
        f"courseid={course_id}&"
        f"category=-1&"
        f"gpr_type=edit&"
        f"gpr_plugin=tree&"
        f"gpr_courseid={course_id}&"
        f"sesskey={sesskey}&"
        f"_qf__core_grades_form_add_category=1&"
        f"fullname={urllib.parse.quote(nombre)}&"
        f"aggregation={aggregation}&"
        f"aggregateonlygraded={aggregateonlygraded}&"
        f"droplow=0&"
        f"grade_item_gradetype=1&"
        f"grade_item_grademax={grademax}&"
        f"grade_item_grademin=0&"
        f"grade_item_gradepass={gradepass}&"
        f"grade_item_weightoverride=0&"
        f"grade_item_aggregationcoef={aggregationcoef}&"  # ← Campo aggregationcoef añadido
        f"submitbutton=Guarda+els+canvis"
    )

    # Incluir parent_id si es diferente de 0 (categoría raíz)
    if parent_id > 0:
        formdata += f"&parentcategory={parent_id}"

    # Enviar la solicitud POST al formulario de creación de categoría
    url = f"{base_url}/grade/edit/tree/category.php"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = session.post(url, cookies=cookie, data=formdata, headers=headers)

    if r.status_code == 200:
        print(f"Categoría '{nombre}' creada correctamente")
        return True
    else:
        print(f"Error al crear la categoría '{nombre}': {r.status_code}")
        return False

def crear_item(session, cookie, base_url, sesskey, course_id, nombre, parent_id, config_global=None, idnumber="", aggregationcoef=1.0):
    """Crea un item en el libro de calificaciones."""
    print(f"Creando item: {nombre}")

    # Configuración por defecto para items
    if config_global is None:
        config_global = {
            "grademax": 100,
            "gradepass": 50
        }

    grademax = config_global.get("grademax", 100)
    gradepass = config_global.get("gradepass", 50)

    # Construir el payload para la solicitud POST
    formdata = (
        f"id=0&"
        f"courseid={course_id}&"
        f"itemid=-1&"
        f"itemtype=manual&"
        f"gpr_type=edit&"
        f"gpr_plugin=tree&"
        f"gpr_courseid={course_id}&"
        f"sesskey={sesskey}&"
        f"_qf__core_grades_form_add_item=1&"
        f"itemname={urllib.parse.quote(nombre)}&"
        f"gradetype=1&"
        f"grademax={grademax}&"
        f"grademin=0.00&"
        f"gradepass={gradepass}&"
        f"hidden=0&"
        f"locked=0&"
        f"aggregationcoef={aggregationcoef}&"  # ← Campo aggregationcoef añadido
        f"submitbutton=Guarda+els+canvis"
    )

    # Incluir idnumber si se proporciona
    if idnumber:
        formdata += f"&idnumber={urllib.parse.quote(idnumber)}"

    # Incluir parent_id (obligatorio para items)
    formdata += f"&parentcategory={parent_id}"

    # Enviar la solicitud POST al formulario de creación de item
    url = f"{base_url}/grade/edit/tree/item.php"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = session.post(url, cookies=cookie, data=formdata, headers=headers)

    if r.status_code == 200:
        print(f"Item '{nombre}' creado correctamente")
        return True
    else:
        print(f"Error al crear el item '{nombre}': {r.status_code}")
        return False

def crear_estructura_calificaciones(session, cookie, base_url, sesskey, course_id, categoria_padre, categorias_hijas, config_global):
    """Crea la estructura completa de calificaciones basada en el JSON."""
    print("Creando estructura de calificaciones...")

    # Primero crear la categoría padre
    if not crear_categoria(session, cookie, base_url, sesskey, course_id, categoria_padre, 0, config_global):
        print("Error: No se pudo crear la categoría padre")
        return False

    # Obtener el ID de la categoría padre recién creada
    parent_id = obtener_id_categoria(session, cookie, base_url, sesskey, course_id, categoria_padre)
    if parent_id == 0:
        print("Error: No se pudo obtener el ID de la categoría padre")
        return False

    # Crear cada categoría hija y sus elementos
    for categoria_hija in categorias_hijas:
        nombre_categoria = categoria_hija["nombre"]

        # Crear la categoría hija
        if not crear_categoria(session, cookie, base_url, sesskey, course_id, nombre_categoria, parent_id, config_global):
            print(f"Error: No se pudo crear la categoría hija '{nombre_categoria}'")
            continue

        # Obtener el ID de la categoría hija recién creada
        categoria_id = obtener_id_categoria(session, cookie, base_url, sesskey, course_id, nombre_categoria)
        if categoria_id == 0:
            print(f"Error: No se pudo obtener el ID de la categoría hija '{nombre_categoria}'")
            continue

        # Crear los elementos dentro de esta categoría
        for elemento in categoria_hija.get("elementos", []):
            nombre_elemento = elemento["nombre"]
            idnumber = elemento.get("idnumber", "")
            formula = elemento.get("formula", "")
            aggregationcoef = elemento.get("aggregationcoef", 1.0)

            # Crear el item
            if not crear_item(session, cookie, base_url, sesskey, course_id, nombre_elemento, categoria_id, config_global, idnumber, aggregationcoef):
                print(f"Error: No se pudo crear el item '{nombre_elemento}'")
                continue

            # Si hay una fórmula, aplicarla al item
            if formula:
                # Obtener el ID del item recién creado
                item_id = obtener_id_item(session, cookie, base_url, sesskey, course_id, nombre_elemento)
                if item_id:
                    if not modificar_formula_item(session, cookie, base_url, sesskey, course_id, item_id, nombre_elemento, formula):
                        print(f"Error: No se pudo aplicar la fórmula al item '{nombre_elemento}'")
                else:
                    print(f"Error: No se pudo obtener el ID del item '{nombre_elemento}' para aplicar la fórmula")

    print("Estructura de calificaciones creada correctamente")
    return True

def mostrar_ayuda_creditos():
    """Muestra la información de ayuda y créditos del script"""
    print("\n" + "="*80)
    print("Script de Gestión de Calificaciones para Aules (Moodle)")
    print("="*80)
    print("""
Autores:
- Idea inicial: Manuel Sanchez (Nelo) me.sanchezgomis@edu.gva.es
- Ampliación de funcionalidades, comentarios y reusabilidad: David Martinez (www.martinezpenya.es)

DESCRIPCIÓN:
Script unificado con menú interactivo para gestionar estructuras de calificación en Moodle/Aules.
Permite crear, actualizar fórmulas, eliminar estructuras completas y generar plantillas de configuración.

CARACTERÍSTICAS PRINCIPALES:
- Menú interactivo con 5 opciones principales
- Gestión completa de categorías y elementos de calificación
- Soporte para fórmulas de cálculo personalizadas
- Configuración mediante archivo JSON (datos_aules.json)
- Detección automática del entorno de ejecución (AppImage vs desarrollo)

OPCIONES DEL MENÚ:
0. Generar estructura básica JSON local
   - Guía interactiva para crear datos_aules_generado.json
   - Incluye sugerencias para IA generativa

1. Crear nueva estructura online
   - Crea estructura completa basada en datos_aules.json

2. Actualizar cálculos y pesos
   - Modifica fórmulas, pesos y configuraciones en estructura existente

3. Eliminar estructura online
   - Elimina completamente una estructura por categoría padre

4. Ayuda/Créditos
   - Muestra esta información de ayuda

5. Salir
   - Finaliza la ejecución

El script detecta automáticamente si se ejecuta como AppImage y busca datos_aules.json

ESTRUCTURA DEL ARCHIVO JSON (datos_aules.json):
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

URLs BASE SOPORTADAS:
- https://aules.edu.gva.es/docent (entorno de pruebas)
- https://aules.edu.gva.es/fp (FP Presencial)
- https://aules.edu.gva.es/semipresencial (FP Semipresencial)

OPCIONES DE AGREGACIÓN:
-  0: Media de las calificaciones
- 10: Media ponderada de las calificaciones
- 11: Media ponderada simple de las calificaciones
- 12: Media de las calificaciones (con créditos extra)
-  2: Mediana de las calificaciones
-  4: Calificación más baja
-  6: Calificación más alta
-  8: Moda de las calificaciones
- 13: Natural

NOTAS IMPORTANTES:
- Opciones 1, 2 y 3 requieren datos_aules.json
- aggregationcoef es opcional (0.0 categorías, 1.0 items por defecto)
- Fórmulas usan sintaxis Moodle: =[[NOMBRE_ITEM]]
- idnumber identifica elementos únicamente
- Se recomienda ejecutar como AppImage para mejor portabilidad

FLUJO DE TRABAJO RECOMENDADO:
1. Ejecutar opción 0 para generar plantilla básica
2. Editar manualmente el JSON generado
3. Usar IA generativa (ChatGPT, Claude, etc.) para completar RA y CE
4. Renombrar archivo a datos_aules.json
5. Ejecutar opción 1 para crear estructura online

SOPORTE PARA IA GENERATIVA:
Incluye prompt específico para crear JSON completos a partir de documentos con RA y CE.
""")
    input("\nPresiona Enter para volver al menú principal...")

def main():
    parser = argparse.ArgumentParser(description='Herramienta para gestionar calificaciones en Aules')
    parser.add_argument('--debug', action='store_true', help='Mostrar información de depuración')
    args = parser.parse_args()

    if args.debug:
        print("=== MODO DEBUG ===")
        print(f"Directorio actual: {os.getcwd()}")
        print(f"Directorio del script: {os.path.dirname(os.path.abspath(__file__))}")
        print(f"Es AppImage: {is_appimage()}")
        print(f"Archivos en directorio actual: {os.listdir('.')}")
        print("==================")

    while True:
        print("\n" + "="*55)
        print("GESTOR DE ESTRUCTURA DE CALIFICACIONES AULES v.0.4")
        print("="*55)
        print("0. Generar estructura básica JSON local")
        print("1. Crear nueva estructura online con el json datos_aules.json")
        print("2. Actualizar cálculos y pesos en estructura existente online")
        print("3. Eliminar estructura online")
        print("4. Ayuda / Creditos")
        print("5. Salir")
        print("="*55)

        opcion = input("Selecciona una opción: ")

        if opcion == "0":
            generar_estructura_basica()

        elif opcion == "1":
            print("\nCargando configuración desde JSON...")
            data = cargar_datos_json()
            if not data:
                input("Presiona Enter para continuar...")
                continue

            print("✓ Configuración cargada correctamente")

            # Iniciar sesión
            session = requests.Session()
            cookie, sesskey = login(session, data["base_url"], data["username"], data["password"])

            if not cookie or not sesskey:
                print("Error: No se pudo iniciar sesión")
                input("Presiona Enter para continuar...")
                continue

            # Crear estructura
            crear_estructura_calificaciones(
                session, cookie, data["base_url"], sesskey,
                data["course_id"], data["categoria_padre"],
                data["categorias_hijas"], data["configuracion_global"]
            )

            input("Presiona Enter para continuar...")

        elif opcion == "2":
            print("\nCargando configuración desde JSON...")
            data = cargar_datos_json()
            if not data:
                input("Presiona Enter para continuar...")
                continue

            print("✓ Configuración cargada correctamente")

            # Iniciar sesión
            session = requests.Session()
            cookie, sesskey = login(session, data["base_url"], data["username"], data["password"])

            if not cookie or not sesskey:
                print("Error: No se pudo iniciar sesión")
                input("Presiona Enter para continuar...")
                continue

            # Obtener elementos del curso
            elementos = obtener_elementos_curso(session, cookie, data["base_url"], data["course_id"])

            if not elementos:
                print("No se encontraron elementos en el curso")
                input("Presiona Enter para continuar...")
                continue

            # Encontrar la categoría padre
            categoria_padre = encontrar_categoria_por_nombre(elementos, data["categoria_padre"])

            if not categoria_padre:
                print(f"No se encontró la categoría padre: {data['categoria_padre']}")
                input("Presiona Enter para continuar...")
                continue

            # Encontrar todos los elementos relacionados
            elementos_a_eliminar = encontrar_elementos_por_categoria(elementos, categoria_padre["id"])

            if not elementos_a_eliminar:
                print("No se encontraron elementos relacionados con la categoría padre")
                input("Presiona Enter para continuar...")
                continue

            print(f"\nSe van a eliminar {len(elementos_a_eliminar)} elementos:")
            for elemento in elementos_a_eliminar:
                print(f"  - {elemento['nombre']} ({elemento['tipo']})")

            confirmacion = input("\n¿Estás seguro de que quieres eliminar estos elementos? (s/n): ")
            if confirmacion.lower() != 's':
                print("Operación cancelada")
                input("Presiona Enter para continuar...")
                continue

            # Preguntar si se desea verificación de eliminación
            verificar_eliminacion = input("¿Verificar eliminación de cada elemento? (s/n, n=recomendado): ").lower() != 's'

            # Eliminar elementos (primero los items, luego las categorías)
            elementos_eliminados = 0

            # Primero eliminar items
            for elemento in elementos_a_eliminar:
                if elemento["tipo"] == "item":
                    if eliminar_elemento(session, cookie, data["base_url"], sesskey, data["course_id"], elemento, verificar_eliminacion):
                        elementos_eliminados += 1

            # Luego eliminar categorías (en orden inverso para evitar problemas de dependencia)
            categorias_a_eliminar = [e for e in elementos_a_eliminar if e["tipo"] == "category"]
            # Ordenar por nivel descendente (eliminar primero las más profundas)
            categorias_a_eliminar.sort(key=lambda x: x.get("nivel", 0), reverse=True)

            for categoria in categorias_a_eliminar:
                if eliminar_elemento(session, cookie, data["base_url"], sesskey, data["course_id"], categoria, verificar_eliminacion):
                    elementos_eliminados += 1

            print(f"\nSe eliminaron {elementos_eliminados} de {len(elementos_a_eliminar)} elementos")
            input("Presiona Enter para continuar...")

        elif opcion == "3":
            print("\nCargando configuración desde JSON...")
            data = cargar_datos_json()
            if not data:
                input("Presiona Enter para continuar...")
                continue

            print("✓ Configuración cargada correctamente")

            # Iniciar sesión
            session = requests.Session()
            cookie, sesskey = login(session, data["base_url"], data["username"], data["password"])

            if not cookie or not sesskey:
                print("Error: No se pudo iniciar sesión")
                input("Presiona Enter para continuar...")
                continue

            # Obtener elementos del curso
            elementos = obtener_elementos_curso(session, cookie, data["base_url"], data["course_id"])

            if not elementos:
                print("No se encontraron elementos en el curso")
                input("Presiona Enter para continuar...")
                continue

            # Encontrar la categoría padre
            categoria_padre = encontrar_categoria_por_nombre(elementos, data["categoria_padre"])

            if not categoria_padre:
                print(f"No se encontró la categoría padre: {data['categoria_padre']}")
                input("Presiona Enter para continuar...")
                continue

            # Encontrar todos los elementos relacionados
            elementos_a_modificar = encontrar_elementos_por_categoria(elementos, categoria_padre["id"])

            if not elementos_a_modificar:
                print("No se encontraron elementos relacionados con la categoría padre")
                input("Presiona Enter para continuar...")
                continue

            print(f"\nSe van a modificar {len(elementos_a_modificar)} elementos:")
            for elemento in elementos_a_modificar:
                print(f"  - {elemento['nombre']} ({elemento['tipo']})")

            confirmacion = input("\n¿Estás seguro de que quieres modificar estos elementos? (s/n): ")
            if confirmacion.lower() != 's':
                print("Operación cancelada")
                input("Presiona Enter para continuar...")
                continue

            # Modificar elementos
            elementos_modificados = 0

            for elemento in elementos_a_modificar:
                if elemento["tipo"] == "category":
                    if modificar_gradepass_categoria(session, cookie, data["base_url"], sesskey, data["course_id"],
                                                   elemento["id"], elemento["nombre"], data["configuracion_global"]):
                        elementos_modificados += 1
                else:  # item
                    # Buscar en el JSON la configuración específica de este item
                    config_item = None
                    for categoria_hija in data["categorias_hijas"]:
                        for item_config in categoria_hija.get("elementos", []):
                            if item_config["nombre"] == elemento["nombre"]:
                                config_item = item_config
                                break
                        if config_item:
                            break

                    idnumber = config_item.get("idnumber", "") if config_item else ""
                    aggregationcoef = config_item.get("aggregationcoef", 1.0) if config_item else 1.0

                    if modificar_gradepass_item(session, cookie, data["base_url"], sesskey, data["course_id"],
                                              elemento["id"], elemento["nombre"], data["configuracion_global"],
                                              idnumber, aggregationcoef):
                        elementos_modificados += 1

            print(f"\nSe modificaron {elementos_modificados} de {len(elementos_a_modificar)} elementos")
            input("Presiona Enter para continuar...")

        elif opcion == "4":
            mostrar_ayuda_creditos()

        elif opcion == "5":
            print("¡Hasta luego!")
            break

        else:
            print("Opción no válida. Por favor, selecciona una opción del 0 al 4.")

if __name__ == "__main__":
    main()
