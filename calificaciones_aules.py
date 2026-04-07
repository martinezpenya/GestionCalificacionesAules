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
import getpass

# --- CONSTANTES ---
VERSION = "1.6.1"
FECHA = "07/04/2026"

# --- UTILIDADES ---

def limpiar_id(id_raw):
    """
    Limpia prefijos comunes de Moodle para obtener el ID numérico.
    Ejemplos: 'cg123' -> '123', 'ig456' -> '456', 'grade-item-cg789' -> '789'
    """
    if not id_raw:
        return ""
    id_str = str(id_raw)
    
    # Eliminar prefijos largos primero
    prefixes = ['grade-item-cg', 'grade-item-ig', 'cg', 'ig', 'gc']
    for p in prefixes:
        if id_str.startswith(p):
            return id_str[len(p):]
    return id_str

class AulesClient:
    """Cliente para la interacción con la plataforma Aules."""
    
    def __init__(self, base_url, log_callback=None, progress_callback=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.sesskey = None
        self.username = None
        self.log_callback = log_callback
        self.progress_callback = progress_callback

    def _log(self, message, level="info"):
        """Centraliza los logs enviándolos al callback o a print."""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            prefix = "[INFO]" if level == "info" else "[ERROR]"
            print(f"{prefix} {message}")

    def _update_progress(self, value, message=""):
        """Notifica el progreso a través del callback."""
        if self.progress_callback:
            self.progress_callback(value, message)

    def login(self, username, password):
        """Inicia sesión en Aules y extrae la sesskey."""
        self.username = username
        self._log(f"Iniciando sesión como {username}...")

        # Verificar si ya estamos logueados
        try:
            r = self.session.get(f"{self.base_url}/my/")
            if 'logout' in r.text.lower():
                self._log("Sesión ya activa detectada.")
                self._extraer_sesskey(r.text)
                if self.sesskey:
                    return True
        except Exception as e:
            self._log(f"Error al verificar sesión: {e}", "error")

        # Proceso de login normal
        try:
            r = self.session.get(f"{self.base_url}/login/index.php")
            token_match = re.search(r'name="logintoken" value="(\w{32})"', r.text)
            if not token_match:
                self._log("Error: No se pudo encontrar el token de login", "error")
                return False

            payload = {
                'username': username,
                'password': password,
                'anchor': '',
                'logintoken': token_match.group(1)
            }
            
            r = self.session.post(f"{self.base_url}/login/index.php", data=payload)
            self._extraer_sesskey(r.text)

            if self.sesskey:
                self._log("Sesión iniciada correctamente.")
                return True
            
            self._log("Error: No se pudo obtener la clave de sesión.", "error")
            return False
        except Exception as e:
            self._log(f"Error durante el login: {e}", "error")
            return False

    def _extraer_sesskey(self, html):
        """Busca la sesskey en el contenido HTML."""
        match = re.search(r'sesskey=(\w+)', html)
        if match:
            self.sesskey = match.group(1)

    def post_ajax(self, info, payload_list):
        """Realiza una petición AJAX al servicio de Moodle."""
        url = f"{self.base_url}/lib/ajax/service.php?sesskey={self.sesskey}&info={info}"
        try:
            r = self.session.post(url, json=payload_list)
            return r.json()
        except Exception as e:
            self._log(f"Error en petición AJAX: {e}", "error")
            return None

    def get(self, path, params=None):
        """Petición GET simplificada."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self.session.get(url, params=params)

    def post(self, path, data=None, headers=None):
        """Petición POST simplificada."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self.session.post(url, data=data, headers=headers)

# Detectar si estamos en modo AppImage
def is_appimage():
    """Check if running as AppImage"""
    return hasattr(sys, '_MEIPASS') or 'APPIMAGE' in os.environ

def generar_estructura_basica():
    """Guía al usuario para generar una estructura básica de JSON"""
    if 'APPIMAGE' in os.environ:
        base_dir = os.path.dirname(os.environ.get('APPIMAGE'))

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
    password = getpass.getpass("Contraseña (de AULES): ")
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

def guardar_datos_json(data):
    """Guarda los datos proporcionados en el archivo datos_aules.json"""
    if 'APPIMAGE' in os.environ:
        base_dir = os.path.dirname(os.environ.get('APPIMAGE'))
    elif getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        base_dir = os.getcwd()

    nombre_archivo = "datos_aules.json"
    json_path = os.path.join(base_dir, nombre_archivo)

    try:
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar JSON: {e}")
        return False

def obtener_elementos_curso(client, course_id):
    """Obtiene todos los elementos de calificación del curso con análisis mejorado."""
    client._log("Obteniendo elementos del curso...")
    r = client.get(f"grade/edit/tree/index.php?id={course_id}")
    
    if r.status_code != 200:
        client._log(f"Error al acceder al curso: {r.status_code}", "error")
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

def eliminar_elemento(client, course_id, elemento, verificar_eliminacion):
    """Elimina un elemento (categoría o item) del curso con la URL correcta."""
    try:
        # URL CORRECTA para ambos casos (categorías e items)
        url = f"grade/edit/tree/index.php?id={course_id}&action=delete&confirm=1&eid={elemento['id']}&sesskey={client.sesskey}&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}"
        
        client._log(f"Eliminando: {elemento['nombre']}")
        r = client.get(url)
        
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
        client._log(f"Error al eliminar elemento {elemento['nombre']}: {e}", "error")
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

def get_categoria_payload(client, course_id, name, parent_id=0, config_global=None):
    if config_global is None:
        config_global = {"aggregation": 0, "aggregateonlygraded": 1, "grademax": 100, "gradepass": 50}

    parent_id_num = limpiar_id(parent_id)
    parent_field = f"&parentcategory={parent_id_num}" if parent_id_num else ""

    formdata = (
        f"id=0&courseid={course_id}&category=-1&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}&sesskey={client.sesskey}"
        f"&_qf__core_grades_form_add_category=1&fullname={urllib.parse.quote(name)}&aggregation={config_global.get('aggregation', 0)}"
        f"&aggregateonlygraded={1 if config_global.get('aggregateonlygraded', True) else 0}&droplow=0&grade_item_gradetype=1"
        f"&grade_item_grademax={config_global.get('grademax', 100)}&grade_item_grademin=0&grade_item_gradepass={config_global.get('gradepass', 50)}"
        f"&grade_item_weightoverride=0{parent_field}"
    )

    return json.dumps([{
        "index": 0,
        "methodname": "core_form_dynamic_form",
        "args": {"formdata": formdata, "form": "core_grades\\form\\add_category"}
    }])


def get_item_payload(client, course_id, name, parent_id, config_global=None, idnumber=""):
    if config_global is None:
        config_global = {"grademax": 100, "gradepass": 50}

    parent_id_num = limpiar_id(parent_id)
    id_field = f"&idnumber={urllib.parse.quote(idnumber)}" if idnumber else ""

    formdata = (
        f"id=0&courseid={course_id}&itemid=-1&itemtype=manual&gpr_type=edit&gpr_plugin=tree&gpr_courseid={course_id}"
        f"&sesskey={client.sesskey}&_qf__core_grades_form_add_item=1&itemname={urllib.parse.quote(name)}{id_field}"
        f"&gradetype=1&grademax={config_global.get('grademax', 100)}&grademin=0.00&gradepass={config_global.get('gradepass', 50)}"
        f"&hidden=0&locked=0&parentcategory={parent_id_num}"
    )

    return json.dumps([{
        "index": 0,
        "methodname": "core_form_dynamic_form",
        "args": {"formdata": formdata, "form": "core_grades\\form\\add_item"}
    }])


def obtener_id_categoria(client, course_id, nombre_categoria):
    """Función auxiliar para obtener el ID de una categoría por su nombre"""
    payload = [{
        "index": 0,
        "methodname": "core_form_dynamic_form",
        "args": {
            "formdata": f"category=-1&courseid={course_id}&gpr_plugin=tree",
            "form": "core_grades\\form\\add_category"
        }
    }]
    
    r = client.post_ajax("core_form_dynamic_form", payload)
    if not r: return 0
    
    pattern = r'<option value="(\d+)"[\s\n]*>([^<]+)</option>'
    options = re.findall(pattern, r[0]["data"]["html"])
    
    for o in options:
        if o[1] == nombre_categoria:
            return int(o[0])
    return 0

def obtener_id_item(client, course_id, nombre_item):
    """Función auxiliar para obtener el ID de un item por su nombre"""
    try:
        r = client.get(f"grade/edit/tree/index.php?id={course_id}")
        if r.status_code != 200: return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        trs = soup.find_all("tr", class_="item")
        
        for tr in trs:
            nombre_celda = tr.find("td", class_="cell") or tr.find("td", class_="column-name")
            if nombre_celda:
                gradeitem_span = nombre_celda.find("span", class_="gradeitemheader")
                if gradeitem_span and gradeitem_span.get_text(strip=True) == nombre_item:
                    item_id = tr.get("data-itemid") or tr.get("id", "").replace("grade-item-", "")
                    return item_id
        return None
    except Exception as e:
        print(f"Error en obtener_id_item: {e}")
        return None

def modificar_gradepass_item(client, course_id, item_id, item_nombre, config_global, item_idnumber="", aggregationcoef=1.0):
    """Modifica el campo gradepass, idnumber y aggregationcoef de un item específico"""
    client._log(f"Modificando item: {item_nombre}")
    item_id_num = limpiar_id(item_id)

    formdata = {
        "id": item_id_num,
        "courseid": course_id,
        "itemtype": "manual",
        "gpr_type": "edit",
        "gpr_plugin": "tree",
        "gpr_courseid": course_id,
        "sesskey": client.sesskey,
        "_qf__edit_item_form": "1",
        "mform_isexpanded_id_general": "1",
        "itemname": item_nombre,
        "iteminfo": "",
        "idnumber": item_idnumber,
        "gradetype": "1",
        "grademax": config_global.get("grademax", 10),
        "grademin": "0",
        "gradepass": config_global.get("gradepass", 5),
        "display": "0",
        "decimals": "-1",
        "hidden": "0",
        "locked": "0",
        "aggregationcoef": aggregationcoef,
        "submitbutton": "Guarda+els+canvis"
    }

    r = client.post("grade/edit/tree/item.php", data=formdata)
    if r.status_code == 200:
        client._log(f"Item '{item_nombre}' modificado.")
        return True
    return False

def modificar_formula_item(client, course_id, item_id, item_nombre, formula):
    """Modifica la fórmula de cálculo de un item específico"""
    item_id_num = limpiar_id(item_id)
    formdata = {
        "id": item_id_num,
        "courseid": course_id,
        "section": "calculation",
        "gpr_type": "edit",
        "gpr_plugin": "tree",
        "gpr_courseid": course_id,
        "sesskey": client.sesskey,
        "_qf__edit_calculation_form": "1",
        "calculation": formula,
        "submitbutton": "Guarda+els+canvis"
    }
    client.post("grade/edit/tree/calculation.php", data=formdata)
    client._log(f"Fórmula de '{item_nombre}' actualizada.")
    return True

def modificar_formula_categoria(client, course_id, categoria_id, categoria_nombre, formula):
    """Modifica la fórmula de cálculo de una categoría específica"""
    cat_id_num = limpiar_id(categoria_id)
    formdata = {
        "id": cat_id_num,
        "courseid": course_id,
        "section": "calculation",
        "gpr_type": "edit",
        "gpr_plugin": "tree",
        "gpr_courseid": course_id,
        "sesskey": client.sesskey,
        "_qf__edit_calculation_form": "1",
        "calculation": formula,
        "submitbutton": "Guarda+els+canvis"
    }
    client.post("grade/edit/tree/calculation.php", data=formdata)
    client._log(f"Fórmula de categoría '{categoria_nombre}' actualizada.")
    return True

def modificar_gradepass_categoria(client, course_id, categoria_id, categoria_nombre, config_global, aggregationcoef=0.0, idnumber=""):
    """Modifica el campo gradepass, aggregationcoef e idnumber de una categoría específica"""
    cat_id_num = limpiar_id(categoria_id)
    formdata = {
        "id": cat_id_num,
        "courseid": course_id,
        "gpr_type": "edit",
        "gpr_plugin": "tree",
        "gpr_courseid": course_id,
        "sesskey": client.sesskey,
        "_qf__edit_category_form": "1",
        "fullname": categoria_nombre,
        "aggregation": config_global.get("aggregation", 0),
        "aggregateonlygraded": 1 if config_global.get("aggregateonlygraded", True) else 0,
        "grade_item_grademax": config_global.get("grademax", 100),
        "grade_item_idnumber": idnumber,
        "grade_item_gradepass": config_global.get("gradepass", 50),
        "grade_item_aggregationcoef": aggregationcoef,
        "submitbutton": "Guarda+els+canvis"
    }

    r = client.post("grade/edit/tree/category.php", data=formdata)
    if r.status_code == 200:
        client._log(f"Categoría '{categoria_nombre}' modificada.")
        return True
    return False

def insertar_categorias_y_items(client, course_id, categoria_padre, categorias_hijas, config_global=None):
    # Configuración por defecto
    if config_global is None:
        config_global = {"aggregation": 0, "aggregateonlygraded": 1, "grademax": 100, "gradepass": 50}

    # Primero insertar la categoría padre
    client._log(f"Insertando categoría padre: {categoria_padre}")
    payload = get_categoria_payload(client, course_id, categoria_padre, config_global=config_global)
    client.post_ajax("core_form_dynamic_form", json.loads(payload))

    # Obtener el ID de la categoría padre
    padre_id = obtener_id_categoria_completo(client, course_id, categoria_padre)
    if not padre_id: return

    modificar_gradepass_categoria(client, course_id, padre_id, categoria_padre, config_global)

    # Luego insertar las categorías hijas y sus elementos
    total_hijas = len(categorias_hijas)
    for i, categoria_hija in enumerate(categorias_hijas):
        nombre_hija = categoria_hija["nombre"]
        coef_hija = categoria_hija.get("aggregationcoef", 0.0)
        
        progress = (i / total_hijas) * 100
        client._update_progress(progress, f"Procesando {nombre_hija}...")

        client.post_ajax("core_form_dynamic_form", json.loads(get_categoria_payload(client, course_id, nombre_hija, padre_id, config_global)))
        hija_id = obtener_id_categoria_completo(client, course_id, nombre_hija)
        if not hija_id: continue

        modificar_gradepass_categoria(client, course_id, hija_id, nombre_hija, config_global, coef_hija)

        elementos = categoria_hija["elementos"]
        total_elementos = len(elementos)
        ce_as_category = config_global.get("ce_as_category", False)

        for j, elemento_info in enumerate(elementos):
            if isinstance(elemento_info, dict):
                e_nombre, e_formula, e_idnum, e_coef = elemento_info["nombre"], elemento_info.get("formula"), elemento_info.get("idnumber", ""), elemento_info.get("aggregationcoef", 1.0)
            else:
                e_nombre, e_formula, e_idnum, e_coef = elemento_info, None, "", 1.0

            if ce_as_category:
                client._log(f"Insertando CE como categoría: {e_nombre}")
                client.post_ajax("core_form_dynamic_form", json.loads(get_categoria_payload(client, course_id, e_nombre, hija_id, config_global)))
                time.sleep(1)
                ce_id = obtener_id_categoria_completo(client, course_id, e_nombre)
                if ce_id:
                    modificar_gradepass_categoria(client, course_id, ce_id, e_nombre, config_global, e_coef, e_idnum)
                    if e_formula:
                        modificar_formula_categoria(client, course_id, ce_id, e_nombre, e_formula)
            else:
                client._log(f"Insertando CE como item: {e_nombre}")
                client.post_ajax("core_form_dynamic_form", json.loads(get_item_payload(client, course_id, e_nombre, hija_id, config_global, e_idnum)))
                time.sleep(1)
                item_id = obtener_id_item_completo(client, course_id, e_nombre)
                if item_id:
                    modificar_gradepass_item(client, course_id, item_id, e_nombre, config_global, e_idnum, e_coef)
                    if e_formula:
                        modificar_formula_item(client, course_id, item_id, e_nombre, e_formula)

    
    client._update_progress(100, "Estructura creada correctamente.")

def obtener_id_categoria_completo(client, course_id, nombre_categoria):
    """Obtiene el ID completo (cg######) de una categoría por su nombre"""
    for intento in range(3):
        try:
            client._log(f"Buscando categoría: '{nombre_categoria}' (Intento {intento + 1})")
            time.sleep(2 if intento == 0 else 1)
            
            r = client.get(f"grade/edit/tree/index.php?id={course_id}")
            if r.status_code != 200: continue
            
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.find_all("tr", class_="category") or soup.find_all("tr", attrs={"data-category": True})
            
            for row in rows:
                name_cell = row.find("td", class_="column-name")
                if not name_cell: continue
                
                cat_name = name_cell.get_text(strip=True)
                if nombre_categoria.lower() in cat_name.lower():
                    cat_id = row.get("id", "").replace("grade-item-", "") or row.get("data-category")
                    if cat_id: return cat_id
        except Exception as e:
            client._log(f"Error: {e}", "error")
    return None
    
def obtener_id_item_completo(client, course_id, nombre_item):
    """Obtiene el ID completo (ig######) de un item por su nombre"""
    try:
        r = client.get(f"grade/edit/tree/index.php?id={course_id}")
        if r.status_code != 200: return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("tr", class_="item")
        
        for item in items:
            name_cell = item.find("td", class_="column-name")
            if name_cell:
                span = name_cell.find("span", class_="gradeitemheader")
                if span and span.get_text(strip=True) == nombre_item:
                    return item.get("id", "").replace("grade-item-", "")
        return None
    except Exception as e:
        client._log(f"Error: {e}", "error")
    return None

def actualizar_formulas(client, course_id, categorias_hijas, config_global=None):
    """Actualiza o elimina las fórmulas de cálculo de los elementos existentes"""
    client._log("Iniciando actualización/eliminación de fórmulas...")
    
    if config_global is None:
        config_global = {}
    
    ce_as_category = config_global.get("ce_as_category", False)
    total_hijas = len(categorias_hijas)
    
    for i, categoria_hija in enumerate(categorias_hijas):
        progress = (i / total_hijas) * 100
        client._update_progress(progress, f"Actualizando fórmulas en {categoria_hija['nombre']}...")
        
        for elemento_info in categoria_hija["elementos"]:
            nombre = elemento_info["nombre"] if isinstance(elemento_info, dict) else elemento_info
            formula = elemento_info.get("formula") if isinstance(elemento_info, dict) else None
            
            if formula is not None:
                if ce_as_category:
                    item_id = obtener_id_categoria_completo(client, course_id, nombre)
                    if item_id:
                        modificar_formula_categoria(client, course_id, item_id, nombre, formula)
                else:
                    item_id = obtener_id_item_completo(client, course_id, nombre)
                    if item_id:
                        modificar_formula_item(client, course_id, item_id, nombre, formula)

    
    client._update_progress(100, "Actualización de fórmulas completada.")

def sincronizar_todo(client, course_id, categoria_padre_nombre, categorias_hijas, config_global=None):
    """Sincronización inteligente: Crea elementos faltantes y actualiza fórmulas/pesos de los existentes."""
    client._log("Iniciando sincronización inteligente de estructura y pesos...")
    
    if config_global is None:
        config_global = {"aggregation": 10, "aggregateonlygraded": True, "grademax": 10.0, "gradepass": 5.0}

    ce_as_category = config_global.get("ce_as_category", False)
    
    # 1. Obtener estado actual de Aules
    elementos_actuales = obtener_elementos_curso(client, course_id)
    if not elementos_actuales:
        client._log("No se pudo obtener la estructura actual de Aules.", "error")
        return

    # 2. Verificar/Crear categoría padre
    padre = encontrar_categoria_por_nombre(elementos_actuales, categoria_padre_nombre)
    if not padre:
        client._log(f"Creando categoría padre faltante: {categoria_padre_nombre}")
        client.post_ajax("core_form_dynamic_form", json.loads(get_categoria_payload(client, course_id, categoria_padre_nombre, config_global=config_global)))
        # Esperar un poco a que Moodle procese la creación
        time.sleep(2)
        padre_id = obtener_id_categoria_completo(client, course_id, categoria_padre_nombre)
    else:
        padre_id = padre["id"]
        modificar_gradepass_categoria(client, course_id, padre_id, categoria_padre_nombre, config_global)

    if not padre_id:
        client._log("Error crítico: No se pudo obtener el ID de la categoría padre.", "error")
        return

    # 3. Procesar categorías hijas (RAs)
    total_hijas = len(categorias_hijas)
    for i, cat_json in enumerate(categorias_hijas):
        nombre_hija = cat_json["nombre"]
        coef_hija = cat_json.get("aggregationcoef", 0.0)
        progress = (i / total_hijas) * 100
        client._update_progress(progress, f"Sincronizando {nombre_hija}...")

        # Buscar si el RA existe
        hija = encontrar_categoria_por_nombre(elementos_actuales, nombre_hija)
        if not hija:
            client._log(f"Creando RA faltante: {nombre_hija}")
            client.post_ajax("core_form_dynamic_form", json.loads(get_categoria_payload(client, course_id, nombre_hija, padre_id, config_global)))
            time.sleep(2)
            hija_id = obtener_id_categoria_completo(client, course_id, nombre_hija)
        else:
            hija_id = hija["id"]
        
        if not hija_id: continue

        # Actualizar configuración del RA (coeficientes)
        modificar_gradepass_categoria(client, course_id, hija_id, nombre_hija, config_global, coef_hija)

        # 4. Procesar elementos (CEs) de esta hija
        for elemento_json in cat_json.get("elementos", []):
            if isinstance(elemento_json, dict):
                e_nombre = elemento_json["nombre"]
                e_formula = elemento_json.get("formula")
                e_idnum = elemento_json.get("idnumber", "")
                e_coef = elemento_json.get("aggregationcoef", 1.0)
            else:
                e_nombre, e_formula, e_idnum, e_coef = elemento_json, None, "", 1.0

            # Buscar si el CE existe en cualquier formato (item o categoría)
            item_existente = next((e for e in elementos_actuales if e["tipo"] == "item" and e["nombre"] == e_nombre), None)
            cat_existente = encontrar_categoria_por_nombre(elementos_actuales, e_nombre)

            if ce_as_category:
                # El usuario quiere que los CE sean CATEGORÍAS
                if cat_existente:
                    ce_id = cat_existente["id"]
                    client._log(f"Actualizando CE (Categoría): {e_nombre}")
                    modificar_gradepass_categoria(client, course_id, ce_id, e_nombre, config_global, e_coef, e_idnum)
                    if e_formula: modificar_formula_categoria(client, course_id, ce_id, e_nombre, e_formula)
                elif item_existente:
                    client._log(f"AVISO: {e_nombre} existe como ITEM pero ce_as_category=True. Se creará la CATEGORÍA.", "error")
                    client.post_ajax("core_form_dynamic_form", json.loads(get_categoria_payload(client, course_id, e_nombre, hija_id, config_global)))
                    time.sleep(1)
                    ce_id = obtener_id_categoria_completo(client, course_id, e_nombre)
                    if ce_id:
                        modificar_gradepass_categoria(client, course_id, ce_id, e_nombre, config_global, e_coef, e_idnum)
                        if e_formula: modificar_formula_categoria(client, course_id, ce_id, e_nombre, e_formula)
                else:
                    client._log(f"Creando CE faltante (categoría): {e_nombre}")
                    client.post_ajax("core_form_dynamic_form", json.loads(get_categoria_payload(client, course_id, e_nombre, hija_id, config_global)))
                    time.sleep(1)
                    ce_id = obtener_id_categoria_completo(client, course_id, e_nombre)
                    if ce_id:
                        modificar_gradepass_categoria(client, course_id, ce_id, e_nombre, config_global, e_coef, e_idnum)
                        if e_formula: modificar_formula_categoria(client, course_id, ce_id, e_nombre, e_formula)
            else:
                # El usuario quiere que los CE sean ITEMS INDIVIDUALES
                if item_existente:
                    item_id = item_existente["id"]
                    client._log(f"Actualizando CE (Item): {e_nombre}")
                    modificar_gradepass_item(client, course_id, item_id, e_nombre, config_global, e_idnum, e_coef)
                    if e_formula: modificar_formula_item(client, course_id, item_id, e_nombre, e_formula)
                elif cat_existente:
                    client._log(f"AVISO: {e_nombre} existe como CATEGORÍA pero ce_as_category=False. Se creará el ITEM.", "error")
                    client.post_ajax("core_form_dynamic_form", json.loads(get_item_payload(client, course_id, e_nombre, hija_id, config_global, e_idnum)))
                    time.sleep(1)
                    item_id = obtener_id_item_completo(client, course_id, e_nombre)
                    if item_id:
                        modificar_gradepass_item(client, course_id, item_id, e_nombre, config_global, e_idnum, e_coef)
                        if e_formula: modificar_formula_item(client, course_id, item_id, e_nombre, e_formula)
                else:
                    client._log(f"Creando CE faltante (item): {e_nombre}")
                    client.post_ajax("core_form_dynamic_form", json.loads(get_item_payload(client, course_id, e_nombre, hija_id, config_global, e_idnum)))
                    time.sleep(1)
                    item_id = obtener_id_item_completo(client, course_id, e_nombre)
                    if item_id:
                        modificar_gradepass_item(client, course_id, item_id, e_nombre, config_global, e_idnum, e_coef)
                        if e_formula: modificar_formula_item(client, course_id, item_id, e_nombre, e_formula)

    client._update_progress(100, "Sincronización inteligente completada con éxito.")

def eliminar_estructura(client, course_id, nombre_categoria_padre):
    """Elimina una estructura completa a partir de una categoría padre"""
    elementos = obtener_elementos_curso(client, course_id)
    if not elementos: return

    categoria_padre = encontrar_categoria_por_nombre(elementos, nombre_categoria_padre)
    if not categoria_padre:
        client._log(f"No se encontró la categoría '{nombre_categoria_padre}'", "error")
        return
        
    elementos_relacionados = encontrar_elementos_por_categoria(elementos, categoria_padre["id"])
    a_eliminar = elementos_relacionados + [categoria_padre]
    
    # Eliminar duplicados y ordenar categorías (profundas primero)
    vistos = set()
    unicos = []
    for e in a_eliminar:
        uid = f"{e['tipo']}_{e['id']}"
        if uid not in vistos:
            unicos.append(e)
            vistos.add(uid)

    # Nota: En modo GUI, la confirmación debería venir de la interfaz antes de llamar a esto.
    # Por ahora mantenemos compatibilidad básica si no hay GUI activa.
    if not client.log_callback:
        confirmacion = input(f"\n¿Eliminar {len(unicos)} elementos de '{nombre_categoria_padre}'? (s/n): ")
        if confirmacion.lower() != 's': return
    
    # Items primero, luego categorías de nivel profundo a superficial
    items = [e for e in unicos if e["tipo"] == "item"]
    cats = sorted([e for e in unicos if e["tipo"] == "category"], key=lambda x: x.get("nivel", 0), reverse=True)
    
    total = len(unicos)
    for i, e in enumerate(items + cats):
        progress = (i / total) * 100
        client._update_progress(progress, f"Eliminando {e['nombre']}...")
        eliminar_elemento(client, course_id, e, True)
    
    client._update_progress(100, f"Eliminación de '{nombre_categoria_padre}' completada.")

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
    if is_appimage():
        print("=== GESTOR DE CALIFICACIONES AULES ===")
        print("Ejecutando en modo AppImage")
        input("Presiona Enter para continuar...")

    while True:
        opcion = mostrar_menu()
        if opcion == "0":
            generar_estructura_basica()
            continue
        elif opcion == "4":
            mostrar_ayuda_creditos()
            continue
        elif opcion == "5":
            break

        data = cargar_datos_json()
        if not data:
            input("Presiona Enter para continuar...")
            continue

        client = AulesClient(data["base_url"])
        if not client.login(data["username"], data["password"]):
            input("Error de login. Presiona Enter...")
            continue

        course_id = data["course_id"]
        categoria_padre = data["categoria_padre"]
        categorias_hijas = data["categorias_hijas"]
        config_global = data["configuracion_global"]

        if opcion == "1":
            insertar_categorias_y_items(client, course_id, categoria_padre, categorias_hijas, config_global)
        elif opcion == "2":
            elementos = obtener_elementos_curso(client, course_id)
            padre = encontrar_categoria_por_nombre(elementos, categoria_padre)
            if not padre: continue
            
            relacionados = encontrar_elementos_por_categoria(elementos, padre["id"])
            for e in tqdm(relacionados, desc="Actualizando"):
                if e["tipo"] == "category":
                    conf = next((c for c in categorias_hijas if c["nombre"] == e["nombre"]), {})
                    modificar_gradepass_categoria(client, course_id, e["id"], e["nombre"], config_global, conf.get("aggregationcoef", 0.0))
                    modificar_formula_categoria(client, course_id, e["id"], e["nombre"], conf.get("formula", ""))
                else:
                    conf = None
                    for ch in categorias_hijas:
                        for ec in ch.get("elementos", []):
                            if isinstance(ec, dict) and ec["nombre"] == e["nombre"]:
                                conf = ec; break
                        if conf: break
                    
                    if conf:
                        modificar_gradepass_item(client, course_id, e["id"], e["nombre"], config_global, conf.get("idnumber", ""), conf.get("aggregationcoef", 1.0))
                        modificar_formula_item(client, course_id, e["id"], e["nombre"], conf.get("formula", ""))
        elif opcion == "3":
            nombre_del = input("Introduce la categoría padre a eliminar: ")
            if nombre_del.strip():
                eliminar_estructura(client, course_id, nombre_del)
        
        input("\nProceso finalizado. Presiona Enter para continuar...")

if __name__ == "__main__":
    main()
