import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import threading
import json
import os
from calificaciones_aules import AulesClient, insertar_categorias_y_items, eliminar_estructura, actualizar_formulas, cargar_datos_json, sincronizar_todo, guardar_datos_json, get_json_path

# Versión de la Aplicación (Control de cambios)
__version__ = "1.8.0"

# Configuración de apariencia
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gestor Automatizado del Cuaderno de Calificaciones de Aules")
        self.geometry("1100x750")

        # Configuración de layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Estado de la aplicación
        self.client = None
        self.is_busy = False

        # --- BARRA LATERAL ---
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AULES TOOL", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.home_button = ctk.CTkButton(self.sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Inicio",
                                         fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                         anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.config_button = ctk.CTkButton(self.sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Ajustes",
                                           fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                           anchor="w", command=self.config_button_event)
        self.config_button.grid(row=2, column=0, sticky="ew")

        self.json_button = ctk.CTkButton(self.sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Editor JSON",
                                         fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                         anchor="w", command=self.json_button_event)
        self.json_button.grid(row=3, column=0, sticky="ew")

        self.logs_button = ctk.CTkButton(self.sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Consola",
                                         fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                         anchor="w", command=self.logs_button_event)
        self.logs_button.grid(row=4, column=0, sticky="ew")

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Modo Visual:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 20))

        # Etiqueta de Versión
        self.version_label = ctk.CTkLabel(self.sidebar_frame, text=f"v{__version__}", text_color="gray50", font=ctk.CTkFont(size=11))
        self.version_label.grid(row=8, column=0, padx=20, pady=(0, 10))

        # --- FRAMES DE CONTENIDO ---
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.config_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.json_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.logs_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        self.init_home_view()
        self.init_config_view()
        self.init_json_view()
        self.init_logs_view()

        # Cargar datos iniciales desde JSON
        self.reload_all_data_event()
        
        # Seleccionar vista por defecto
        self.select_frame_by_name("home")

    def init_home_view(self):
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(self.home_frame, text="Gestión de Cuaderno Aules", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(40, 10), sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(self.home_frame, text="Automatización de criterios y categorías personalizada.", text_color="gray")
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 40), sticky="w")

        # Botones de Acción
        self.actions_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        self.actions_frame.grid(row=2, column=0, padx=20, sticky="w")

        self.btn_crear = ctk.CTkButton(self.actions_frame, text="Crear Estructura", height=45, width=200, command=self.crear_estructura_event)
        self.btn_crear.grid(row=0, column=0, padx=(0, 20))

        self.btn_actualizar = ctk.CTkButton(self.actions_frame, text="Actualizar Fórmulas", height=45, width=200, command=self.actualizar_formulas_event)
        self.btn_actualizar.grid(row=0, column=1, padx=(0, 20))

        self.btn_eliminar = ctk.CTkButton(self.actions_frame, text="Eliminar Estructura", height=45, width=200, fg_color="#ae3333", hover_color="#8b2828", command=self.eliminar_estructura_event)
        self.btn_eliminar.grid(row=0, column=2)

        # Estado
        self.status_card = ctk.CTkFrame(self.home_frame, height=100, width=400)
        self.status_card.grid(row=3, column=0, padx=20, pady=40, sticky="w")
        self.status_card.grid_propagate(False)
        
        self.status_icon = ctk.CTkLabel(self.status_card, text="●", text_color="#ae3333", font=ctk.CTkFont(size=30))
        self.status_icon.grid(row=0, column=0, padx=20, pady=25)
        
        self.status_text = ctk.CTkLabel(self.status_card, text="Desconectado de Aules", font=ctk.CTkFont(size=14))
        self.status_text.grid(row=0, column=1, pady=25)

    def init_config_view(self):
        self.config_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.config_frame, text="Ajustes de Conexión", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(40, 20), sticky="w")
        
        self.url_var = ctk.StringVar(value="https://aules.edu.gva.es/docent")
        ctk.CTkLabel(self.config_frame, text="Sector / Entorno:").grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.url_menu = ctk.CTkOptionMenu(self.config_frame, values=["https://aules.edu.gva.es/docent", "https://aules.edu.gva.es/fp", "https://aules.edu.gva.es/semipresencial"], variable=self.url_var, width=450)
        self.url_menu.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")

        ctk.CTkLabel(self.config_frame, text="Usuario:").grid(row=3, column=0, padx=20, sticky="w")
        self.user_entry = ctk.CTkEntry(self.config_frame, placeholder_text="Tu usuario o DNI", width=450)
        self.user_entry.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="w")

        ctk.CTkLabel(self.config_frame, text="Contraseña:").grid(row=5, column=0, padx=20, sticky="w")
        self.pwd_entry = ctk.CTkEntry(self.config_frame, placeholder_text="Tu contraseña", show="*", width=450)
        self.pwd_entry.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="w")

        # Opción CE as Category
        self.ce_as_category_var = ctk.BooleanVar(value=True)
        self.ce_as_category_switch = ctk.CTkSwitch(self.config_frame, text="Tratar CE como categoría (ce_as_category)", variable=self.ce_as_category_var)
        self.ce_as_category_switch.grid(row=7, column=0, padx=20, pady=(10, 20), sticky="w")

        self.btn_connect = ctk.CTkButton(self.config_frame, text="Guardar y Conectar con Aules", height=45, width=450, command=self.connect_event)
        self.btn_connect.grid(row=8, column=0, padx=20, pady=20, sticky="w")

    def init_json_view(self):
        self.json_frame.grid_columnconfigure(0, weight=1)
        self.json_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.json_frame, text="Configuración del Cuaderno (JSON)", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(40, 10), sticky="w")
        
        self.json_path_label = ctk.CTkLabel(self.json_frame, text="Ruta: (sin datos cargados)", text_color="gray", font=ctk.CTkFont(size=11))
        self.json_path_label.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")
        
        self.json_text = ctk.CTkTextbox(self.json_frame, font=("Courier", 12), fg_color=("white", "gray10"))
        self.json_text.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        self.btn_refresh_json = ctk.CTkButton(self.json_frame, text="Sincronizar Aplicación con Archivo JSON", height=40, command=self.reload_all_data_event)
        self.btn_refresh_json.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="w")

    def init_logs_view(self):
        self.logs_frame.grid_columnconfigure(0, weight=1)
        self.logs_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.logs_frame, text="Consola de Operaciones", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(40, 10), sticky="w")
        self.log_text = ctk.CTkTextbox(self.logs_frame, font=("Courier", 11), fg_color=("white", "gray10"))
        self.log_text.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.progressbar = ctk.CTkProgressBar(self.logs_frame)
        self.progressbar.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.progressbar.set(0)

    # --- LÓGICA DE CONTROL ---

    def log(self, message, level="info"):
        timestamp = time.strftime('%H:%M:%S')
        full_message = f"[{timestamp}] {message}\n"
        self.log_text.insert("end", full_message)
        self.log_text.see("end")

    def select_frame_by_name(self, name):
        # Actualizar colores botones sidebar
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.config_button.configure(fg_color=("gray75", "gray25") if name == "config" else "transparent")
        self.json_button.configure(fg_color=("gray75", "gray25") if name == "json" else "transparent")
        self.logs_button.configure(fg_color=("gray75", "gray25") if name == "logs" else "transparent")

        # Mostrar frames
        if name == "home": self.home_frame.grid(row=0, column=1, sticky="nsew")
        else: self.home_frame.grid_forget()
        
        if name == "config": self.config_frame.grid(row=0, column=1, sticky="nsew")
        else: self.config_frame.grid_forget()
        
        if name == "json":
            self.json_frame.grid(row=0, column=1, sticky="nsew")
            # Actualizar solo la vista previa de texto al entrar si no se ha hecho
        else: self.json_frame.grid_forget()
        
        if name == "logs": self.logs_frame.grid(row=0, column=1, sticky="nsew")
        else: self.logs_frame.grid_forget()

    def home_button_event(self): self.select_frame_by_name("home")
    def config_button_event(self): self.select_frame_by_name("config")
    def json_button_event(self): self.select_frame_by_name("json")
    def logs_button_event(self): self.select_frame_by_name("logs")

    def change_appearance_mode_event(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def reload_all_data_event(self):
        """Recarga TODO desde el JSON: Texto, Ajustes y Credenciales"""
        try:
            data = cargar_datos_json()
            if data:
                # 1. Actualizar Vista Previa de Texto y Ruta
                self.json_text.delete("1.0", "end")
                self.json_text.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
                self.json_path_label.configure(text=f"Ruta: {get_json_path()}")
                
                # 2. Actualizar Campos de Conexión
                if "base_url" in data: self.url_var.set(data["base_url"])
                if "username" in data: 
                    self.user_entry.delete(0, "end")
                    self.user_entry.insert(0, data["username"])
                if "password" in data: 
                    self.pwd_entry.delete(0, "end")
                    self.pwd_entry.insert(0, data["password"])
                
                # 3. Actualizar ce_as_category
                global_cfg = data.get("configuracion_global", {})
                if "ce_as_category" in global_cfg:
                    self.ce_as_category_var.set(global_cfg["ce_as_category"])
                
                self.log("Aplicación sincronizada con los datos de 'datos_aules.json'.", "success")
        except Exception as e:
            self.log(f"Error durante la sincronización: {e}", "error")

    def connect_event(self):
        user = self.user_entry.get()
        pwd = self.pwd_entry.get()
        url = self.url_var.get()
        ce_as_cat = self.ce_as_category_var.get()
        
        if not user or not pwd:
            messagebox.showerror("Error", "Rellena usuario y contraseña")
            return

        # 1. Guardar cambios físicamente en el JSON antes de conectar
        try:
            data = cargar_datos_json()
            if not data:
                # Primer arranque: Crear estructura básica por defecto
                data = {
                    "base_url": url,
                    "username": user,
                    "password": pwd,
                    "course_id": 0,
                    "configuracion_global": {
                        "aggregation": 10,
                        "aggregateonlygraded": False,
                        "grademax": 10,
                        "gradepass": 5,
                        "ce_as_category": ce_as_cat
                    },
                    "categoria_padre": "Nueva Categoría",
                    "categorias_hijas": []
                }
            else:
                # Actualizar datos existentes
                data["username"] = user
                data["password"] = pwd
                data["base_url"] = url
                if "configuracion_global" not in data: data["configuracion_global"] = {}
                data["configuracion_global"]["ce_as_category"] = ce_as_cat
            
            # Guardar físicamente
            guardar_datos_json(data)
            
            # Refrescar la vista previa del JSON si existe el método (corregido a reload_all_data_event)
            self.reload_all_data_event()
        except Exception as e:
            self.log(f"Error al guardar ajustes: {e}", "error")

        # 2. Proceder con el Login
        def task():
            self.btn_connect.configure(state="disabled")
            self.log(f"Conectando a {url}...")
            client = AulesClient(url, log_callback=self.log, progress_callback=lambda v, m: (self.progressbar.set(v/100), self.log(m, "info") if m else None))
            if client.login(user, pwd):
                self.client = client
                self.status_icon.configure(text_color="#44ae44")
                self.status_text.configure(text=f"Conectado como {user}")
                self.log("Ajustes guardados y conexión establecida.", "success")
                self.home_button_event()
            else:
                self.log("Error de conexión/credenciales.", "error")
            self.btn_connect.configure(state="normal")

        threading.Thread(target=task, daemon=True).start()

    def run_safe_action(self, action_fn, *args):
        if not self.client:
            messagebox.showwarning("Atención", "Conecta primero desde Ajustes")
            self.config_button_event()
            return
        
        self.select_frame_by_name("logs")
        def task():
            try:
                action_fn(self.client, *args)
            except Exception as e:
                self.log(f"Error: {e}", "error")
        
        threading.Thread(target=task, daemon=True).start()

    def crear_estructura_event(self):
        data = cargar_datos_json()
        if data:
            data["configuracion_global"]["ce_as_category"] = self.ce_as_category_var.get()
            self.run_safe_action(insertar_categorias_y_items, data["course_id"], data["categoria_padre"], data["categorias_hijas"], data["configuracion_global"])

    def actualizar_formulas_event(self):
        data = cargar_datos_json()
        if data:
            # Sincronización inteligente de estructura y pesos
            data["configuracion_global"]["ce_as_category"] = self.ce_as_category_var.get()
            self.run_safe_action(sincronizar_todo, data["course_id"], data["categoria_padre"], data["categorias_hijas"], data["configuracion_global"])

    def eliminar_estructura_event(self):
        if messagebox.askyesno("Confirmar", "¿Seguro que quieres borrar TODA la estructura de categorías?"):
            data = cargar_datos_json()
            if data:
                self.run_safe_action(eliminar_estructura, data["course_id"], data["categoria_padre"])

if __name__ == "__main__":
    app = App()
    app.mainloop()
