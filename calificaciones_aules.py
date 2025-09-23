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
import pydoc

VERSION = "0.6"
FECHA = "24/09/2025"

# Detectar si estamos en modo AppImage
def is_appimage():
    """Check if running as AppImage"""
    return hasattr(sys, '_MEIPASS') or 'APPIMAGE' in os.environ

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

    # Guardar en archivo
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


    print(f"\n✓ Estructura básica guardada en '{nombre_archivo}'")
    print("\nRECOMENDACIÓN: Edita manualmente el archivo para:")
    print("1. Completar las descripciones de los RA y CE")
    print("2. Añadir fórmulas de cálculo si es necesario (Solo CE)(usar sintaxis Moodle: =[[NOMBRE_ITEM]])")
    print("   Los identificadores que uses en las formulas deben existir previamente, sino la formula no se aplicara")
    print("3. Añadir idnumber (Solo CE) para identificar elementos de forma única")
    print("4. Añadir más categorías hijas y elementos si es necesario")
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
    nombre_archivo = "datos_aules.json"
    json_path = os.path.join(base_dir, nombre_archivo)

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

def get_categoria_payload(sesskey, course_id, name, parent_id=0, config_global=None):
    if config_global is None:
        config_global = {
            "aggregation": 0,
            "aggregateonlygraded": 1,
            "grademax": 100,
            "gradepass": 50
        }

    aggregation = config_global.get("aggregation", 0)
    aggregateonlygraded = 1 if config_global.get("aggregateonlygraded", True) else 0
    grademax = config_global.get("grademax", 100)
    gradepass = config_global.get("gradepass", 50)

    # limpiar el parent_id
    parent_id_num = ""
    if parent_id:
        parent_id_str = str(parent_id)
        if parent_id_str.startswith('cg'):
            parent_id_str = parent_id_str[2:]
        parent_id_num = parent_id_str

    parent = f"&parentcategory={parent_id_num}" if parent_id_num else ""

    formdata = (
        f"id=0&courseid={course_id}&category=-1&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}&sesskey={sesskey}"
        f"&_qf__core_grades_form_add_category=1&fullname={name}&aggregation={aggregation}"
        f"&aggregateonlygraded={aggregateonlygraded}&droplow=0&grade_item_gradetype=1"
        f"&grade_item_grademax={grademax}&grade_item_grademin=0&grade_item_gradepass={gradepass}"
        f"&grade_item_weightoverride=0{parent}"
    )

    data = [{
        "index": 0,
        "methodname": "core_form_dynamic_form",
        "args": {
            "formdata": formdata,
            "form": "core_grades\\form\\add_category"
        }
    }]
    return json.dumps(data)


def get_item_payload(sesskey, course_id, name, parent_id, config_global=None, idnumber=""):
    if config_global is None:
        config_global = {"grademax": 100, "gradepass": 50}

    grademax = config_global.get("grademax", 100)
    gradepass = config_global.get("gradepass", 50)

    # limpiar el parent_id (cg123456 -> 123456)
    parent_id_str = str(parent_id)
    if parent_id_str.startswith('cg'):
        parent_id_str = parent_id_str[2:]

    idnumber_field = f"&idnumber={urllib.parse.quote(idnumber)}" if idnumber else ""

    formdata = (
        f"id=0&courseid={course_id}&itemid=-1&itemtype=manual&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}"
        f"&sesskey={sesskey}&_qf__core_grades_form_add_item=1&itemname={name}{idnumber_field}"
        f"&gradetype=1&grademax={grademax}&grademin=0.00&gradepass={gradepass}"
        f"&hidden=0&locked=0&parentcategory={parent_id_str}"
    )

    data = [{
        "index": 0,
        "methodname": "core_form_dynamic_form",
        "args": {
            "formdata": formdata,
            "form": "core_grades\\form\\add_item"
        }
    }]
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
    """Modifica el campo gradepass, idnumber y aggregationcoef de un item específico usando ID completo (ig######)"""
    print(f"Modificando item: {item_nombre} (ID: {item_id})")

    # Extraer el ID numérico del ID completo (ig1357691 → 1357691)
    if item_id.startswith('ig'):
        item_id_numerico = item_id[2:]
    else:
        item_id_numerico = item_id

    # Configuración para items
    grademax = config_global.get("grademax", 10)
    gradepass = config_global.get("gradepass", 5)

    # Codificar los valores para URL
    nombre_codificado = urllib.parse.quote(item_nombre)
    idnumber_codificado = urllib.parse.quote(item_idnumber) if item_idnumber else ""

    # Incluir idnumber en el formdata
    idnumber_field = f"&idnumber={idnumber_codificado}" if item_idnumber else ""

    formdata = (
        f"id={item_id_numerico}&"
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
    
    # Extraer ID numérico (ig1357691 → 1357691)
    if isinstance(item_id, str) and item_id.startswith('ig'):
        item_id_numerico = item_id[2:]
    else:
        item_id_numerico = item_id

    # Construir el payload para la solicitud POST
    formdata = (
        f"id={item_id_numerico}&"
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

    url = f"{base_url}/grade/edit/tree/calculation.php"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = session.post(url, cookies=cookie, data=formdata, headers=headers)
    print(f"Fórmula del item '{item_nombre}' {accion} correctamente: {formula}")
    return True

def modificar_formula_categoria(session, cookie, base_url, sesskey, course_id, categoria_id, categoria_nombre, formula):
    """Modifica la fórmula de cálculo de una categoría específica"""
    if formula == "":
        print(f"Eliminando fórmula de la categoría: {categoria_nombre} (ID: {categoria_id})")
        accion = "eliminada"
    else:
        print(f"Modificando fórmula de la categoría: {categoria_nombre} (ID: {categoria_id})")
        accion = "modificada"
    
    # Extraer ID numérico si es necesario (gc1357938 → 1357938)
    if isinstance(categoria_id, str) and categoria_id.startswith('gc'):
        categoria_id_numerico = categoria_id[2:]
    else:
        categoria_id_numerico = categoria_id

    # Construir el payload para la solicitud POST
    formdata = (
        f"id={categoria_id_numerico}&"
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

    url = f"{base_url}/grade/edit/tree/calculation.php"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = session.post(url, cookies=cookie, data=formdata, headers=headers)
    print(f"Fórmula de la categoría '{categoria_nombre}' {accion} correctamente: {formula}")
    return True

def modificar_gradepass_categoria(session, cookie, base_url, sesskey, course_id, categoria_id, categoria_nombre, config_global, aggregationcoef=0.0):
    """Modifica el campo gradepass y aggregationcoef de una categoría específica usando ID completo (cg######)"""
    print(f"Modificando categoría: {categoria_nombre} (ID: {categoria_id})")

    # Extraer el ID numérico del ID completo (cg192460 → 192460)
    if categoria_id.startswith('cg'):
        categoria_id_numerico = categoria_id[2:]
    else:
        categoria_id_numerico = categoria_id

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
        f"id={categoria_id_numerico}&"
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

def insertar_categorias_y_items(session, cookie, base_url, sesskey, course_id, categoria_padre, categorias_hijas, config_global=None):
    # Configuración por defecto
    if config_global is None:
        config_global = {
            "aggregation": 0,
            "aggregateonlygraded": 1,
            "grademax": 100,
            "gradepass": 50
        }

    # Obtener gradepass de la configuración global
    gradepass = config_global.get("gradepass", 50)

    # Primero insertar la categoría padre
    print(f"Insertando categoría padre: {categoria_padre}")

    payload = get_categoria_payload(sesskey, course_id, categoria_padre, config_global=config_global)
    url = f"{base_url}/lib/ajax/service.php?sesskey={sesskey}&info=core_form_dynamic_form"
    r = session.post(url, cookies=cookie, data=payload)

    # Obtener el ID de la categoría padre (cg######)
    padre_id = obtener_id_categoria_completo(session, cookie, base_url, sesskey, course_id, categoria_padre)

    if not padre_id or not padre_id.startswith('cg'):
        print(f"Error: No se pudo obtener el ID completo de la categoría padre '{categoria_padre}'")
        return

    print(f"Categoría padre '{categoria_padre}' insertada con ID: {padre_id}")
    
    # Modificar gradepass de la categoría padre
    modificar_gradepass_categoria(
        session, cookie, base_url, sesskey, course_id,
        padre_id, categoria_padre, config_global
    )

    # Luego insertar las categorías hijas y sus elementos
    for categoria_hija in tqdm(categorias_hijas, desc="Insertando categorías hijas"):
        nombre_categoria_hija = categoria_hija["nombre"]
        elementos = categoria_hija["elementos"]
        aggregationcoef_categoria = categoria_hija.get("aggregationcoef", 0.0)

        print(f"Insertando categoría hija: {nombre_categoria_hija}")

        # Insertar la categoría hija
        payload = get_categoria_payload(sesskey, course_id, nombre_categoria_hija, padre_id, config_global)
        url = f"{base_url}/lib/ajax/service.php?sesskey={sesskey}&info=core_form_dynamic_form"
        r = session.post(url, cookies=cookie, data=payload)

        # Obtener el ID completo de la categoría hija (cg######)
        hija_id = obtener_id_categoria_completo(session, cookie, base_url, sesskey, course_id, nombre_categoria_hija)

        if not hija_id or not hija_id.startswith('cg'):
            print(f"Error: No se pudo obtener el ID completo de la categoría hija '{nombre_categoria_hija}'")
            continue

        print(f"Categoría hija '{nombre_categoria_hija}' insertada con ID: {hija_id}")

        # Modificar gradepass y aggregationcoef de la categoría hija
        modificar_gradepass_categoria(
            session, cookie, base_url, sesskey, course_id,
            hija_id, nombre_categoria_hija, config_global, aggregationcoef_categoria
        )

        # Insertar los elementos de calificación en la categoría hija
        for elemento_info in tqdm(elementos, desc=f"Insertando elementos en {nombre_categoria_hija}"):
            # Determinar si el elemento es un string (nombre simple) o un diccionario (con nombre, fórmula e idnumber)
            if isinstance(elemento_info, dict):
                elemento_nombre = elemento_info["nombre"]
                elemento_formula = elemento_info.get("formula", None)
                elemento_idnumber = elemento_info.get("idnumber", "")
                elemento_aggregationcoef = elemento_info.get("aggregationcoef", 1.0)
            else:
                elemento_nombre = elemento_info
                elemento_formula = None
                elemento_idnumber = ""
                elemento_aggregationcoef = 1.0

            # Pasar el idnumber a get_item_payload
            payload = get_item_payload(sesskey, course_id, elemento_nombre, hija_id, config_global, elemento_idnumber)
            url = f"{base_url}/lib/ajax/service.php?sesskey={sesskey}&info=core_form_dynamic_form"
            r = session.post(url, cookies=cookie, data=payload)

            # Verificar si la inserción fue exitosa
            if r.status_code == 200 and r.json()[0]["error"] == False:
                print(f"Elemento de calificación '{elemento_nombre}' insertado correctamente")

                # Esperar un momento para que el servidor procese la creación
                time.sleep(1)

                # Obtener el ID completo del item recién creado (ig######)
                item_id = obtener_id_item_completo(session, cookie, base_url, sesskey, course_id, elemento_nombre)

                if item_id and item_id.startswith('ig'):
                    # Modificar el gradepass, idnumber y aggregationcoef del item recién creado
                    modificar_gradepass_item(
                        session, cookie, base_url, sesskey, course_id,
                        item_id, elemento_nombre, config_global, 
                        elemento_idnumber, elemento_aggregationcoef
                    )

                    # Si hay una fórmula definida, aplicarla
                    if elemento_formula:
                        modificar_formula_item(
                            session, cookie, base_url, sesskey, course_id,
                            item_id, elemento_nombre, elemento_formula
                        )
                else:
                    print(f"Error: No se pudo obtener el ID completo del item '{elemento_nombre}'")
            else:
                print(f"Error al insertar el elemento de calificación '{elemento_nombre}': {r.text}")

def obtener_id_categoria_completo(session, cookie, base_url, sesskey, course_id, nombre_categoria):
    """Obtiene el ID completo (cg######) de una categoría por su nombre - Versión mejorada con pausas"""
    import time
    
    # Intentar múltiples veces con pausas
    max_intentos = 3
    pausa_inicial = 2  # segundos
    pausa_entre_intentos = 1  # segundos
    
    for intento in range(max_intentos):
        try:
            print(f"Intento {intento + 1}/{max_intentos} - Buscando categoría: '{nombre_categoria}'")
            
            # Pausa inicial para dar tiempo al servidor
            if intento == 0:
                print(f"Esperando {pausa_inicial} segundos para que el servidor procese la creación...")
                time.sleep(pausa_inicial)
            else:
                print(f"Esperando {pausa_entre_intentos} segundos antes del siguiente intento...")
                time.sleep(pausa_entre_intentos)
            
            # Obtener la página de gestión de calificaciones
            url = f"{base_url}/grade/edit/tree/index.php?id={course_id}"
            r = session.get(url, cookies=cookie)
            
            if r.status_code != 200:
                print(f"Error al obtener página de calificaciones: {r.status_code}")
                continue
            
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Estrategia 1: Buscar tr con clase category
            categorias = soup.find_all("tr", class_="category")
            print(f"Estrategia 1 - Encontradas {len(categorias)} categorías con class='category'")
            
            # Estrategia 2: Si no encuentra nada, buscar por data-category
            if not categorias:
                categorias = soup.find_all("tr", attrs={"data-category": True})
                print(f"Estrategia 2 - Encontradas {len(categorias)} categorías con data-category")
            
            # Estrategia 3: Buscar cualquier tr que contenga "grade-item-cg"
            if not categorias:
                categorias = soup.find_all("tr", id=lambda x: x and x.startswith("grade-item-cg"))
                print(f"Estrategia 3 - Encontradas {len(categorias)} categorías con ID grade-item-cg")
            
            # Estrategia 4: Buscar por patrón en el HTML
            if not categorias:
                # Buscar todas las filas que contengan "RA CE" o el nombre de la categoría
                todas_las_filas = soup.find_all("tr")
                categorias = []
                for fila in todas_las_filas:
                    if fila.get_text() and nombre_categoria in fila.get_text():
                        categorias.append(fila)
                print(f"Estrategia 4 - Encontradas {len(categorias)} filas que contienen '{nombre_categoria}'")
            
            print(f"Total de categorías encontradas: {len(categorias)}")
            
            for categoria in categorias:
                # Extraer el nombre de la categoría con múltiples estrategias
                nombre_celda = categoria.find("td", class_="column-name")
                if not nombre_celda:
                    continue
                    
                categoria_name = None
                
                # Estrategia 1: Buscar div con clase rowtitle
                rowtitle = nombre_celda.find("div", class_="rowtitle")
                if rowtitle:
                    categoria_name = rowtitle.get_text(strip=True)
                    print(f"Estrategia nombre 1 - Encontrado: '{categoria_name}'")
                
                # Estrategia 2: Si no se encuentra con rowtitle, buscar directamente en la celda
                if not categoria_name:
                    # Buscar cualquier elemento que contenga el texto
                    texto_completo = nombre_celda.get_text(strip=True)
                    if texto_completo:
                        categoria_name = texto_completo
                        print(f"Estrategia nombre 2 - Encontrado: '{categoria_name}'")
                
                # Estrategia 3: Buscar en spans con clase gradeitemheader
                if not categoria_name:
                    gradeitem_span = nombre_celda.find("span", class_="gradeitemheader")
                    if gradeitem_span:
                        categoria_name = gradeitem_span.get_text(strip=True)
                        print(f"Estrategia nombre 3 - Encontrado: '{categoria_name}'")
                
                # Estrategia 4: Buscar cualquier texto que contenga el nombre
                if not categoria_name:
                    # Buscar en todos los elementos de texto
                    for elemento in nombre_celda.find_all(text=True):
                        texto = elemento.strip()
                        if texto and nombre_categoria.lower() in texto.lower():
                            categoria_name = texto
                            print(f"Estrategia nombre 4 - Encontrado: '{categoria_name}'")
                            break
                
                if categoria_name:
                    # Comparar con el nombre que buscamos (comparación flexible)
                    if (categoria_name == nombre_categoria or 
                        categoria_name.strip() == nombre_categoria.strip() or
                        nombre_categoria.lower() in categoria_name.lower()):
                        
                        # El ID completo está en el atributo id del TR (grade-item-cg######)
                        if "id" in categoria.attrs:
                            categoria_id = categoria.attrs["id"].replace("grade-item-", "")
                            print(f"✓ ID completo de la categoría '{categoria_name}': {categoria_id}")
                            return categoria_id
                        else:
                            print(f"✗ Categoría encontrada pero sin ID: '{categoria_name}'")
            
            # Si llegamos aquí, no se encontró la categoría en este intento
            if intento < max_intentos - 1:
                print(f"✗ Categoría no encontrada en intento {intento + 1}, reintentando...")
            else:
                print(f"✗ Error: No se pudo obtener el ID completo de la categoría '{nombre_categoria}' después de {max_intentos} intentos")
                print("Categorías disponibles:")
                for categoria in categorias:
                    nombre_celda = categoria.find("td", class_="column-name")
                    if nombre_celda:
                        texto = nombre_celda.get_text(strip=True)
                        if texto:
                            print(f"  - '{texto}'")
                return None
                
        except Exception as e:
            print(f"Error en obtener_id_categoria_completo (intento {intento + 1}): {e}")
            if intento == max_intentos - 1:
                return None
            continue
    
    return None
    
def obtener_id_item_completo(session, cookie, base_url, sesskey, course_id, nombre_item):
    """Obtiene el ID completo (ig######) de un item por su nombre"""
    try:
        # Obtener la página de gestión de calificaciones
        url = f"{base_url}/grade/edit/tree/index.php?id={course_id}"
        r = session.get(url, cookies=cookie)
        
        if r.status_code != 200:
            print(f"Error al obtener página de calificaciones: {r.status_code}")
            return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Buscar todos los items (elementos de calificación)
        items = soup.find_all("tr", class_="item")
        
        for item in items:
            # Extraer el nombre del item
            nombre_celda = item.find("td", class_="column-name")
            if nombre_celda:
                # Buscar el span con la clase gradeitemheader que contiene el nombre real
                gradeitem_span = nombre_celda.find("span", class_="gradeitemheader")
                if gradeitem_span:
                    item_name = gradeitem_span.get_text(strip=True)
                    
                    # Comparar con el nombre que buscamos
                    if item_name == nombre_item:
                        # El ID completo está en el atributo id del TR (grade-item-ig######)
                        if "id" in item.attrs:
                            item_id = item.attrs["id"].replace("grade-item-", "")
                            print(f"ID completo del item '{item_name}': {item_id}")
                            return item_id
        
        print(f"Error: No se pudo obtener el ID completo del item '{nombre_item}'")
        return None
        
    except Exception as e:
        print(f"Error en obtener_id_item_completo: {e}")
        return None
def actualizar_formulas(session, cookie, base_url, sesskey, course_id, categorias_hijas):
    """Actualiza o elimina las fórmulas de cálculo de los elementos existentes"""
    print("Iniciando actualización/eliminación de fórmulas...")
    
    # Contadores para estadísticas
    total_elementos = 0
    elementos_con_formula = 0
    elementos_actualizados = 0
    elementos_eliminados = 0
    elementos_no_encontrados = 0
    
    # Recorrer todas las categorías hijas y sus elementos
    for categoria_hija in tqdm(categorias_hijas, desc="Procesando categorías"):
        nombre_categoria = categoria_hija["nombre"]
        elementos = categoria_hija["elementos"]
        
        print(f"\nProcesando categoría: {nombre_categoria}")
        
        # Procesar cada elemento de la categoría
        for elemento_info in elementos:
            # Determinar si el elemento es un string (nombre simple) o un diccionario (con nombre y fórmula)
            if isinstance(elemento_info, dict):
                elemento_nombre = elemento_info["nombre"]
                elemento_formula = elemento_info.get("formula", None)
            else:
                elemento_nombre = elemento_info
                elemento_formula = None
            
            total_elementos += 1
            
            # Si el elemento tiene fórmula definida (puede ser cadena vacía para eliminar), procesarlo
            if elemento_formula is not None:
                elementos_con_formula += 1
                print(f"Buscando elemento: {elemento_nombre}")
                
                # Obtener el ID del item
                item_id = obtener_id_item(session, cookie, base_url, sesskey, course_id, elemento_nombre)
                
                if item_id:
                    # Modificar o eliminar la fórmula del item
                    if modificar_formula_item(session, cookie, base_url, sesskey, course_id, item_id, elemento_nombre, elemento_formula):
                        if elemento_formula == "":
                            elementos_eliminados += 1
                        else:
                            elementos_actualizados += 1
                    # Pequeña pausa para no saturar el servidor
                    time.sleep(0.5)
                else:
                    elementos_no_encontrados += 1
                    print(f"Elemento no encontrado: {elemento_nombre}")
    
    # Mostrar resumen de la operación
    print("\n" + "="*50)
    print("RESUMEN DE LA ACTUALIZACIÓN/ELIMINACIÓN")
    print("="*50)
    print(f"Total de elementos procesados: {total_elementos}")
    print(f"Elementos con fórmula definida: {elementos_con_formula}")
    print(f"Elementos actualizados correctamente: {elementos_actualizados}")
    print(f"Elementos con fórmula eliminada: {elementos_eliminados}")
    print(f"Elementos no encontrados: {elementos_no_encontrados}")
    print("="*50)

def eliminar_estructura(session, cookie, base_url, sesskey, course_id, nombre_categoria_padre):
    """Elimina una estructura completa a partir de una categoría padre"""
    print(f"Buscando categoría padre: {nombre_categoria_padre}")
    
    # Obtener todos los elementos del curso
    elementos = obtener_elementos_curso(session, cookie, base_url, course_id)
    
    if not elementos:
        print("No se encontraron elementos en el curso o no se pudo acceder a él.")
        return
    
    print(f"Se encontraron {len(elementos)} elementos en el curso")
    
    # Encontrar la categoría padre
    categoria_padre = encontrar_categoria_por_nombre(elementos, nombre_categoria_padre)
    if not categoria_padre:
        print(f"Advertencia: No se encontró la categoría '{nombre_categoria_padre}'")
        # Mostrar categorías disponibles para ayudar con la depuración
        categorias_disponibles = [e["nombre"] for e in elementos if e["tipo"] == "category"]
        print("Categorías disponibles:")
        for cat in categorias_disponibles:
            print(f"  - {cat}")
        return
        
    print(f"Encontrada categoría: {categoria_padre['nombre']} (ID: {categoria_padre['id']}, Nivel: {categoria_padre['nivel']})")
    
    # Encontrar todos los elementos relacionados con esta categoría
    elementos_relacionados = encontrar_elementos_por_categoria(elementos, categoria_padre["id"])
    print(f"Encontrados {len(elementos_relacionados)} elementos relacionados con {categoria_padre['nombre']}")
    
    elementos_a_eliminar = elementos_relacionados
    elementos_a_eliminar.append(categoria_padre)
    
    # Eliminar duplicados
    elementos_unicos = []
    ids_vistos = set()
    for elemento in elementos_a_eliminar:
        elemento_id = f"{elemento['tipo']}_{elemento['id']}"
        if elemento_id not in ids_vistos:
            elementos_unicos.append(elemento)
            ids_vistos.add(elemento_id)
    
    elementos_a_eliminar = elementos_unicos
    
    print(f"Elementos encontrados para eliminar: {len(elementos_a_eliminar)}")
    
    # Separar items y categorías
    items = [e for e in elementos_a_eliminar if e["tipo"] == "item"]
    categorias = [e for e in elementos_a_eliminar if e["tipo"] == "category"]
    
    print(f"  - Items: {len(items)}")
    print(f"  - Categorías: {len(categorias)}")
    
    # Mostrar lo que se va a eliminar para confirmación
    print("\nElementos a eliminar:")
    for categoria in categorias:
        print(f"  - Categoría: {categoria['nombre']} (nivel: {categoria['nivel']}, ID: {categoria['id']})")
    for item in items:
        print(f"  - Item: {item['nombre']} (ID: {item['id']})")
    
    # Confirmar antes de eliminar
    confirmacion = input("\n¿Estás seguro de que quieres eliminar estos elementos? (s/n): ")
    if confirmacion.lower() != 's':
        print("Operación cancelada.")
        return
    
    # Configuración de verificación (por defecto True)
    verificar_eliminacion = True
    
    # Progreso general - primero items, luego categorías (de más específicas a más generales)
    # Ordenar categorías por nivel descendente (las más profundas primero)
    categorias_ordenadas = sorted(categorias, key=lambda x: x.get("nivel", 0), reverse=True)
    
    print("\nIniciando eliminación...")
    
    with tqdm(total=len(elementos_a_eliminar), desc="Eliminando elementos") as pbar:
        # Primero eliminar todos los items
        for item in items:
            if eliminar_elemento(session, cookie, base_url, sesskey, course_id, item, verificar_eliminacion):
                print(f"✓ Eliminado elemento: {item['nombre']}")
            else:
                print(f"✗ Error al eliminar elemento: {item['nombre']}")
            pbar.update(1)
        
        # Luego eliminar categorías (de más profundas a más superficiales)
        for categoria in categorias_ordenadas:
            if eliminar_elemento(session, cookie, base_url, sesskey, course_id, categoria, verificar_eliminacion):
                print(f"✓ Eliminada categoría: {categoria['nombre']}")
            else:
                print(f"✗ Error al eliminar categoría: {categoria['nombre']}")
            pbar.update(1)
    
    print("Proceso de eliminación completado.")

def mostrar_menu(args=None):
    """Muestra el menú principal y obtiene la selección del usuario"""
    if args and args.mode:
        # Usar modo desde argumentos de línea de comandos
        mode_mapping = {
            'generate': '0',
            'create': '1',
            'update': '2',
            'delete': '3'
        }
        return mode_mapping.get(args.mode, '4')

    print("\n" + "="*70)
    print(f"GESTIÓN DE ESTRUCTURAS DE CALIFICACIÓN EN MOODLE  v{VERSION}  ({FECHA})")
    print("="*70)
    print("0. Generar estructura básica JSON local")
    print("1. Crear nueva estructura online con el json datos_aules.json")
    print("2. Actualizar cálculos y pesos en estructura existente online")
    print("3. Eliminar estructura")
    print("4. Ayuda/Creditos")
    print("5. Salir")
    print("="*70)

    while True:
        opcion = input("Selecciona una opción (0-5): ")
        if opcion in ["0", "1", "2", "3", "4", "5"]:
            return opcion
        print("Opción no válida. Por favor, selecciona 0, 1, 2, 3, 4 o 5.")

def mostrar_ayuda_creditos():
    """Muestra la información de ayuda y créditos del script con paginador"""
    texto = """
================================================================================
Script de Gestión de Calificaciones para Aules (Moodle)
================================================================================

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
================================================================================
"""
    # Mostrar texto con paginador
    pydoc.pager(texto)
    input("\nPresiona Enter para volver al menú principal...")

def main():
    """Función principal del script."""
    session = requests.session()

    if is_appimage():
        print("=== GESTOR DE CALIFICACIONES AULES ===")
        print("Ejecutando en modo AppImage")
        input("Presiona Enter para continuar...")

    while True:
        # Mostrar menú siempre
        opcion = mostrar_menu()

        if opcion == "0":
            # Generar estructura básica JSON
            generar_estructura_basica()
            continue

        elif opcion == "4":
            # Ayuda / Créditos
            mostrar_ayuda_creditos()
            continue

        elif opcion == "5":
            # Salir
            print("Saliendo del programa...")
            break

        # Para opciones 1, 2 y 3 necesitamos datos_aules.json
        try:
            data = cargar_datos_json()
            if not data:
                input("Presiona Enter para continuar...")
                continue
        except Exception as e:
            print(f"Error al cargar datos_aules.json: {e}")
            input("Presiona Enter para continuar...")
            continue

        base_url = data["base_url"]
        username = data["username"]
        password = data["password"]
        course_id = data["course_id"]
        categoria_padre = data["categoria_padre"]
        categorias_hijas = data["categorias_hijas"]
        config_global = data["configuracion_global"]

        if opcion == "1":
            # Crear nueva estructura online
            cookie, sesskey = login(session, base_url, username, password)
            if not sesskey:
                print("Error en el login. Reintentando...")
                session = requests.session()  # Reiniciamos la sesión
                cookie, sesskey = login(session, base_url, username, password)
                if not sesskey:
                    print("Error crítico en el login. Abortando.")
                    break

            print(f"Usando curso con ID: {course_id}")
            print(f"Categoría padre: {categoria_padre}")
            print(f"Categorías hijas a crear: {len(categorias_hijas)}")

            total_elementos = sum(len(categoria["elementos"]) for categoria in categorias_hijas)
            print(f"Elementos de calificación a crear: {total_elementos}")

            insertar_categorias_y_items(session, cookie, base_url, sesskey, course_id, categoria_padre, categorias_hijas, config_global)
            print("Proceso de creación completado.")
            input("Presiona Enter para continuar...")

        elif opcion == "2":
            # Actualizar cálculos y pesos en estructura existente online
            print("\nCargando configuración desde JSON...")
            print("✓ Configuración cargada correctamente")

            # Iniciar sesión
            session = requests.Session()
            cookie, sesskey = login(session, base_url, username, password)

            if not cookie or not sesskey:
                print("Error: No se pudo iniciar sesión")
                input("Presiona Enter para continuar...")
                continue

            # Obtener elementos del curso
            elementos = obtener_elementos_curso(session, cookie, base_url, course_id)

            if not elementos:
                print("No se encontraron elementos en el curso")
                input("Presiona Enter para continuar...")
                continue

            # Encontrar la categoría padre
            categoria_padre_elem = encontrar_categoria_por_nombre(elementos, categoria_padre)

            if not categoria_padre_elem:
                print(f"No se encontró la categoría padre: {categoria_padre}")
                input("Presiona Enter para continuar...")
                continue

            # Encontrar todos los elementos relacionados
            elementos_a_modificar = encontrar_elementos_por_categoria(elementos, categoria_padre_elem["id"])

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
                    # Buscar en el JSON la configuración específica de esta categoría
                    config_categoria = None
                    
                    # Primero verificar si es la categoría padre
                    if elemento["nombre"] == categoria_padre:
                        config_categoria = {
                            "aggregationcoef": data['aggregationcoef']
                        }
                    else:
                        # Buscar en las categorías hijas
                        for categoria_hija in categorias_hijas:
                            if categoria_hija["nombre"] == elemento["nombre"]:
                                config_categoria = categoria_hija
                                break
                    
                    aggregationcoef = config_categoria.get("aggregationcoef", 0.0) if config_categoria else 0.0
                    formula = config_categoria.get("formula", "") if config_categoria else ""
                    #print(f"Formula de la categoria: {elemento["nombre"]}: {formula}")
                    if modificar_gradepass_categoria(session, cookie, base_url, sesskey, course_id,
                                                elemento["id"], elemento["nombre"], config_global, aggregationcoef):
                        elementos_modificados += 1
                    if modificar_formula_categoria(session, cookie, base_url, sesskey, course_id,
                                        elemento["id"], elemento["nombre"], formula):
                        print(f"✓ Fórmula actualizada para: {elemento['nombre']}")
                    else:
                        print(f"✗ Error al actualizar fórmula para: {elemento['nombre']}")
                else:  # item
                    # Obtener configuración para items
                    config_item = None
                    for categoria_hija in categorias_hijas:
                        for item_config in categoria_hija.get("elementos", []):
                            if isinstance(item_config, dict) and item_config["nombre"] == elemento["nombre"]:
                                config_item = item_config
                                break
                        if config_item:
                            break

                    idnumber = config_item.get("idnumber", "") if config_item else ""
                    aggregationcoef = config_item.get("aggregationcoef", 1.0) if config_item else 1.0
                    formula = config_item.get("formula", "") if config_item else ""

                    #print(f"Formula del item: {elemento["nombre"]}: {formula}")


                    # Modificar gradepass, idnumber y aggregationcoef
                    if modificar_gradepass_item(session, cookie, base_url, sesskey, course_id,
                                            elemento["id"], elemento["nombre"], config_global,
                                            idnumber, aggregationcoef):
                        elementos_modificados += 1
                    
                    if modificar_formula_item(session, cookie, base_url, sesskey, course_id,
                                        elemento["id"], elemento["nombre"], formula):
                        print(f"✓ Fórmula actualizada para: {elemento['nombre']}")
                    else:
                        print(f"✗ Error al actualizar fórmula para: {elemento['nombre']}")

            print(f"\nSe modificaron {elementos_modificados} de {len(elementos_a_modificar)} elementos")
            input("Presiona Enter para continuar...")

        elif opcion == "3":
            # Eliminar estructura
            cookie, sesskey = login(session, base_url, username, password)
            if not sesskey:
                print("Error en el login. Reintentando...")
                session = requests.session()  # Reiniciamos la sesión
                cookie, sesskey = login(session, base_url, username, password)
                if not sesskey:
                    print("Error crítico en el login. Abortando.")
                    break

            print(f"Usando curso con ID: {course_id}")

            nombre_categoria_padre = input("Introduce el nombre de la categoría padre a eliminar: ")
            if not nombre_categoria_padre.strip():
                print("No se ha introducido ningún nombre. Operación cancelada.")
                continue

            eliminar_estructura(session, cookie, base_url, sesskey, course_id, nombre_categoria_padre)
            input("Presiona Enter para continuar...")

if __name__ == "__main__":
    main()
