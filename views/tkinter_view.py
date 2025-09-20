# views/tkinter_view.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Optional, Tuple, Any, Dict
import math

# Asumiendo que los modelos se importan correctamente desde el directorio padre
# Si ejecutas este archivo directamente, es posible que necesites ajustes
from models.scheduler import Process # <-- Añadido esta importación

class RRViewInterface:
    """Interfaz que define los métodos que el Presentador puede llamar en la Vista."""
    def get_quantum(self) -> int: raise NotImplementedError
    def get_ticks_per_second(self) -> int: raise NotImplementedError
    def get_arrival_burst(self) -> Tuple[int, int]: raise NotImplementedError # Or handle errors differently
    def get_selected_pid(self) -> Optional[int]: raise NotImplementedError
    def get_new_arrival_burst(self, pid: int, old_arrival: int, old_burst: int) -> Optional[Tuple[int, int]]: raise NotImplementedError
    def get_gantt_zoom(self) -> int: raise NotImplementedError
    def get_canvas_time_scale_base(self) -> float: raise NotImplementedError

    def set_running_state(self, running: bool): raise NotImplementedError
    def set_initial_state(self, initial: bool): raise NotImplementedError
    def set_canvas_time_scale(self, scale: float): raise NotImplementedError
    def set_next_pid(self, next_pid: int): raise NotImplementedError

    def show_message(self, title: str, message: str, type: str = "info"): raise NotImplementedError # type: info, warning, error
    def confirm_action(self, title: str, message: str) -> bool: raise NotImplementedError
    def ask_string(self, title: str, prompt: str, initialvalue: str = "") -> Optional[str]: raise NotImplementedError

    def refresh_process_table(self, processes: Dict[int, Process], scheduler_state: Any): raise NotImplementedError # Pass necessary state
    def update_queues_display(self, time: int, current_pid: Optional[int], ready_pids: List[int]): raise NotImplementedError
    def update_metrics_display(self, metrics: Dict[str, Any]): raise NotImplementedError
    def log_message(self, message: str): raise NotImplementedError

    def draw_static_gantt(self, time: int, scale: float): raise NotImplementedError
    def draw_execution_burst(self, pid: Optional[int], start_time: int, duration: int, scale: float): raise NotImplementedError
    def update_gantt_time_line(self, time: int, scale: float): raise NotImplementedError
    def clear_gantt(self): raise NotImplementedError
    def redraw_gantt_bursts(self, history: List[Tuple[Optional[int], int, int]], scale: float): raise NotImplementedError

    def toggle_full_gantt_view(self, gantt_only: bool): raise NotImplementedError # Logic moved to Presenter

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>  Cambio de nombre de clase: RRAppTk -> RRApp  >>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class RRApp(tk.Tk, RRViewInterface):
    """
    Implementación de la interfaz gráfica usando tkinter.
    Esta clase se enfoca solo en la presentación y captura de eventos del usuario.
    La lógica se delega al Presentador.
    """
    def __init__(self, presenter):
        """Inicializa la ventana principal y todos los componentes de la UI."""
        super().__init__()
        self.presenter = presenter # Referencia al Presentador
        self.title("SIMULADOR OPERATIVOS ROUND ROBIN - MVP")
        self.geometry("1500x750")
        self.minsize(1300, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Manejar cierre de ventana

        # Estado de la aplicación (gestionado por el Presentador, pero la vista lo necesita)
        self.running = False
        self.initial_state = True
        self.gantt_only = False
        self.canvas_time_scale = 5.0 # Valor inicial, se actualizará
        self.canvas_time_scale_base = 5.0 # Valor base para zoom

        # Variables de control de UI
        self.quantum_var = tk.IntVar(value=200)
        self.ticks_per_second_var = tk.IntVar(value=100)
        self.arrival_var = tk.IntVar(value=0)
        self.burst_var = tk.IntVar(value=5)
        self.gantt_zoom_var = tk.IntVar(value=10) # 10% inicial

        # Configurar estilos visuales
        self.setup_styles()

        # Crear todos los widgets de la interfaz
        self.create_widgets()

        # Configurar zoom del Gantt
        self.canvas_time_scale = self.canvas_time_scale_base * (self.gantt_zoom_var.get() / 100.0)

        # Dibujar el Gantt inicial
        self.draw_static_gantt(0, self.canvas_time_scale)

        # Mensajes iniciales en el log
        self.log_message("Bienvenido al Simulador Round Robin (MVP).")
        self.log_message("Agrega procesos manualmente o carga un conjunto de ejemplo.")

    def setup_styles(self):
        """Configura los estilos visuales de la aplicación usando ttk.Style."""
        style = ttk.Style(self)
        style.theme_use("clam")
        # Definir colores
        self.bg_color = "#f0f2f5"
        self.panel_bg = "#ffffff"
        self.accent_color = "#4CAF50"
        self.danger_color = "#f44336"
        self.text_color = "#333333"
        self.header_color = "#424242"
        self.border_color = "#e0e0e0"
        self.scrollbar_color = "#c1c1c1"
        self.scrollbar_active_color = "#a0a0a0"
        self.configure(bg=self.bg_color)
        # Configurar estilos para diferentes widgets
        style.configure("TFrame", background=self.bg_color)
        style.configure("Panel.TFrame", background=self.panel_bg, borderwidth=1, relief="flat", bordercolor=self.border_color)
        style.configure("TLabelframe", background=self.panel_bg, borderwidth=1, relief="solid", bordercolor=self.border_color)
        style.configure("TLabelframe.Label", background=self.panel_bg, foreground=self.header_color, font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 9))
        style.configure("Header.TLabel", foreground=self.header_color, font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=5,
                        background=self.accent_color, foreground="white", borderwidth=0)
        style.map("TButton",
                  background=[("active", self.accent_color), ("!disabled", self.accent_color)],
                  foreground=[("active", "white"), ("!disabled", "white")])
        style.configure("Danger.TButton", background=self.danger_color, foreground="white")
        style.map("Danger.TButton",
                  background=[("active", self.danger_color), ("!disabled", self.danger_color)])
        style.configure("TEntry", fieldbackground=self.panel_bg, bordercolor=self.border_color, relief="solid", borderwidth=1)
        style.configure("TSpinbox", fieldbackground=self.panel_bg, bordercolor=self.border_color, relief="solid", borderwidth=1)
        style.configure("Treeview",
                        background=self.panel_bg,
                        foreground=self.text_color,
                        rowheight=25,
                        fieldbackground=self.panel_bg,
                        borderwidth=1,
                        relief="solid")
        style.map("Treeview",
                  background=[('selected', '#a3c2e6')],
                  foreground=[('selected', self.text_color)])
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 7, "bold"),
                        background=self.header_color,
                        foreground="white",
                        padding=5,
                        relief="flat")
        style.map("Treeview.Heading", background=[('active', self.header_color)])
        style.configure("Vertical.TScrollbar",
                        gripcount=0,
                        arrowsize=12,
                        background=self.scrollbar_color,
                        troughcolor=self.panel_bg,
                        bordercolor=self.panel_bg,
                        relief="flat")
        style.map("Vertical.TScrollbar",
                  background=[("active", self.scrollbar_active_color),
                             ("pressed", self.scrollbar_active_color)])
        style.configure("Horizontal.TScrollbar",
                        gripcount=0,
                        arrowsize=12,
                        background=self.scrollbar_color,
                        troughcolor=self.panel_bg,
                        bordercolor=self.panel_bg,
                        relief="flat")
        style.map("Horizontal.TScrollbar",
                  background=[("active", self.scrollbar_active_color),
                             ("pressed", self.scrollbar_active_color)])
        # Configurar opciones globales para widgets de texto
        self.option_add('*text.background', self.panel_bg)
        self.option_add('*text.foreground', self.text_color)
        self.option_add('*text.font', ("Consolas", 9))

    def create_widgets(self):
        """Crea y organiza todos los widgets de la interfaz gráfica."""
        # Marco principal
        main_frame = ttk.Frame(self, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # --- PANEL IZQUIERDO ---
        left = ttk.Frame(main_frame, style="Panel.TFrame")
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=0, ipadx=12, ipady=5)
        self.left_panel = left
        # Control del Quantum
        qf = ttk.Frame(left, style="TFrame")
        qf.pack(fill=tk.X, pady=(10,5), padx=5)
        ttk.Label(qf, text="Quantum:", style="TLabel").pack(side=tk.LEFT)
        qspin = ttk.Spinbox(qf, from_=1, to=50, textvariable=self.quantum_var, width=5, command=self.on_set_quantum, style="TSpinbox")
        qspin.pack(side=tk.LEFT, padx=10)
        # Botones de control
        ctrlf = ttk.Frame(left, style="TFrame")
        ctrlf.pack(fill=tk.X, pady=10, padx=5)
        self.btn_start = ttk.Button(ctrlf, text="Start", command=self.on_start, style="TButton")
        self.btn_start.pack(side=tk.LEFT, padx=3)
        self.btn_pause = ttk.Button(ctrlf, text="Pause", command=self.on_pause, state=tk.DISABLED, style="TButton")
        self.btn_pause.pack(side=tk.LEFT, padx=3)
        self.btn_step = ttk.Button(ctrlf, text="Step", command=self.on_step, style="TButton")
        self.btn_step.pack(side=tk.LEFT, padx=3)
        self.btn_clear_all = ttk.Button(ctrlf, text="Clear All", command=self.on_clear_all, style="Danger.TButton")
        self.btn_clear_all.pack(side=tk.LEFT, padx=3)
        self.btn_reset = ttk.Button(ctrlf, text="Reset", command=self.on_reset, style="Danger.TButton")
        self.btn_reset.pack(side=tk.LEFT, padx=3)
        # Control de Velocidad
        vf = ttk.Frame(left, style="TFrame")
        vf.pack(fill=tk.X, pady=(5, 5), padx=5)
        ttk.Label(vf, text="Ticks/Segundo:", style="TLabel").pack(side=tk.LEFT)
        self.ticks_per_second_spinbox = ttk.Spinbox(
            vf, from_=1, to=1000, textvariable=self.ticks_per_second_var,
            width=6, style="TSpinbox"
        )
        self.ticks_per_second_spinbox.pack(side=tk.LEFT, padx=10)
        ttk.Button(vf, text="Aplicar Velocidad", command=self.on_set_speed, style="TButton").pack(side=tk.LEFT, padx=5)
        # Tabla de Procesos
        table_frame = ttk.LabelFrame(left, text="Procesos", style="TLabelframe")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        cols = ("pid", "arrival", "burst", "start", "remaining", "completion", "turnaround", "waiting", "ntat", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse", height=10, style="Treeview")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            if c == "status":
                self.tree.column(c, width=100, anchor=tk.CENTER)
            elif c == "pid":
                self.tree.column(c, width=40, anchor=tk.CENTER)
            elif c in ["turnaround", "waiting", "ntat"]:
                self.tree.column(c, width=80, anchor=tk.CENTER)
            else:
                self.tree.column(c, width=70, anchor=tk.CENTER)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)
        self.setup_treeview_grid()
        self.tree.bind("<Double-1>", self.on_edit_row) # Permitir edición al doble clic
        # Texto de ayuda de iniciales
        initials_frame = ttk.Frame(left, style="TFrame")
        initials_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(initials_frame, text="Iniciales:", font=("Segoe UI", 9, "bold"), background=self.panel_bg).pack(anchor=tk.W)
        initials_text = ("AT: Arrival Time  |  BT: Burst Time  |  CT: Completion Time  |  "
                        "TAT: Turnaround Time  |  WT: Waiting Time  |  NTAT: Normalized TAT")
        ttk.Label(initials_frame, text=initials_text, font=("Segoe UI", 8),
                 background=self.panel_bg, foreground="#666666").pack(anchor=tk.W)
        # Gestión de Procesos (Formulario)
        process_mgmt_frame = ttk.LabelFrame(left, text="Gestión de Procesos", style="TLabelframe")
        process_mgmt_frame.pack(fill=tk.X, pady=10, padx=5)
        input_frame = ttk.Frame(process_mgmt_frame, style="TFrame")
        input_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        arrival_row = ttk.Frame(input_frame, style="TFrame")
        arrival_row.pack(fill=tk.X, pady=2)
        ttk.Label(arrival_row, text="Arrival Time (AT):", style="TLabel", width=18, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(arrival_row, textvariable=self.arrival_var, width=8, style="TEntry").pack(side=tk.LEFT)
        burst_row = ttk.Frame(input_frame, style="TFrame")
        burst_row.pack(fill=tk.X, pady=2)
        ttk.Label(burst_row, text="Burst Time (BT):", style="TLabel", width=18, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(burst_row, textvariable=self.burst_var, width=8, style="TEntry").pack(side=tk.LEFT)
        btn_row = ttk.Frame(process_mgmt_frame, style="TFrame")
        btn_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        add_btn = ttk.Button(btn_row, text="Añadir", command=self.on_add_process, style="TButton")
        add_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        del_btn = ttk.Button(btn_row, text="Eliminar", command=self.on_delete_selected, style="Danger.TButton")
        del_btn.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        # Botón de ejemplo
        load_btn = ttk.Button(left, text="Cargar Procesos de Ejemplo", command=self.on_load_sample, style="TButton")
        load_btn.pack(fill=tk.X, pady=(0, 10), padx=5)
        # --- PANEL DERECHO ---
        right = ttk.Frame(main_frame, style="Panel.TFrame")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0, ipadx=5, ipady=5)
        self.right_panel = right
        # Diagrama de Gantt
        gantt_frame = ttk.LabelFrame(right, text="Diagrama de Gantt:        Doble Click para Zoom", style="TLabelframe")
        gantt_frame.pack(fill=tk.BOTH, expand=True, pady=(10,5), padx=5)
        self.gantt_frame = gantt_frame
        gantt_container = ttk.Frame(gantt_frame, style="TFrame")
        gantt_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        zoom_frame = ttk.Frame(gantt_container, style="TFrame")
        zoom_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(zoom_frame, text="Zoom Gantt (%):", style="TLabel").pack(side=tk.LEFT)
        self.gantt_zoom_spinbox = ttk.Spinbox(
            zoom_frame, from_=10, to=500, textvariable=self.gantt_zoom_var,
            width=6, style="TSpinbox", increment=10
        )
        self.gantt_zoom_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_frame, text="Aplicar", command=self.on_set_gantt_zoom, style="TButton").pack(side=tk.LEFT, padx=5)
        self.canvas = tk.Canvas(gantt_container, bg=self.panel_bg, height=200, highlightthickness=0)
        gantt_h_scroll = ttk.Scrollbar(gantt_container, orient=tk.HORIZONTAL, command=self.canvas.xview, style="Horizontal.TScrollbar")
        self.canvas.configure(xscrollcommand=gantt_h_scroll.set)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        gantt_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.bind('<Double-1>', self.toggle_gantt_view) # Toggle vista solo Gantt
        # Estado Actual
        queues_frame = ttk.LabelFrame(right, text="Estado Actual", style="TLabelframe")
        queues_frame.pack(fill=tk.X, pady=5, padx=5)
        self.queues_label = ttk.Label(queues_frame, text="Tiempo: -\nEjecutando: -\nReady: -",
                                      font=("Consolas", 9), background=self.panel_bg, foreground=self.text_color, justify=tk.LEFT)
        self.queues_label.pack(anchor=tk.W, padx=10, pady=5)
        # Métricas
        metrics_frame = ttk.Frame(right, style="TFrame")
        metrics_frame.pack(fill=tk.X, pady=(5,5), padx=5)
        self.metrics_label = ttk.Label(metrics_frame, text="Métricas: -", style="Header.TLabel")
        self.metrics_label.pack(anchor=tk.W)
        # Log de Eventos
        log_frame = ttk.LabelFrame(right, text="Log de Eventos", style="TLabelframe")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        self.log = tk.Text(log_frame, height=7, wrap=tk.WORD, borderwidth=0, highlightthickness=0)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        log_vsb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview, style="Vertical.TScrollbar")
        log_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=log_vsb.set)

    # --- Métodos de configuración de UI ---
    def setup_treeview_grid(self):
        """Configura estilos específicos para el Treeview."""
        style = ttk.Style()
        style.configure("Treeview",
                        background=self.panel_bg,
                        foreground=self.text_color,
                        rowheight=25,
                        fieldbackground=self.panel_bg,
                        borderwidth=1,
                        relief="solid")
        style.map("Treeview",
                  background=[('selected', '#a3c2e6')],
                  foreground=[('selected', self.text_color)])
        self.tree.tag_configure('oddrow', background='#f9f9f9')
        self.tree.tag_configure('evenrow', background='white')
        self.tree.configure(style="Treeview")

    def update_row_tags(self, event=None):
        """Alterna colores de fondo de las filas de la tabla para mejor legibilidad."""
        children = self.tree.get_children('')
        for index, child in enumerate(children):
            if index % 2 == 0:
                self.tree.item(child, tags=('evenrow',))
            else:
                self.tree.item(child, tags=('oddrow',))

    def toggle_gantt_view(self, event=None):
        """
        Alterna entre la vista completa (panel izquierdo + Gantt + métricas + log)
        y una vista solo con el Gantt.
        """
        self.gantt_only = not self.gantt_only
        self.toggle_full_gantt_view(self.gantt_only) # Delegar al Presentador

    # --- Métodos de manejo de eventos de la UI (llaman al Presentador) ---
    def on_set_speed(self):
        """Maneja el evento de cambio de velocidad de simulación."""
        # La validación se puede hacer aquí o en el Presentador
        self.presenter.handle_set_speed()

    def on_set_gantt_zoom(self):
        """Maneja el evento de cambio de zoom del Gantt."""
        self.presenter.handle_set_gantt_zoom()

    def on_add_process(self):
        """Maneja el evento de agregar un nuevo proceso."""
        self.presenter.handle_add_process()

    def on_edit_row(self, event=None):
        """Maneja el evento de edición de un proceso al hacer doble clic en la tabla."""
        selected_pid = self.get_selected_pid()
        if selected_pid is not None:
            self.presenter.handle_edit_process(selected_pid)

    def on_delete_selected(self):
        """Maneja el evento de eliminar un proceso seleccionado."""
        selected_pid = self.get_selected_pid()
        if selected_pid is not None:
            self.presenter.handle_delete_process(selected_pid)

    def on_set_quantum(self):
        """Maneja el evento de cambio de quantum."""
        self.presenter.handle_set_quantum()

    def on_load_sample(self):
        """Maneja el evento de cargar procesos de ejemplo."""
        self.presenter.handle_load_sample()

    def on_start(self):
        """Inicia la simulación en modo automático."""
        self.presenter.handle_start()

    def on_pause(self):
        """Pausa la simulación en modo automático."""
        self.presenter.handle_pause()

    def on_step(self):
        """Ejecuta un paso de la simulación en modo manual."""
        self.presenter.handle_step()

    def on_reset(self):
        """Reinicia la simulación."""
        self.presenter.handle_reset()

    def on_clear_all(self):
        """Limpia todos los datos de la aplicación."""
        self.presenter.handle_clear_all()

    def on_closing(self):
        """Maneja el evento de cierre de la ventana principal."""
        if self.running and messagebox.askokcancel("Salir", "La simulación está en curso. ¿Deseas salir?"):
            self.destroy()
        elif not self.running:
            self.destroy()

    # --- Implementación de RRViewInterface ---
    def get_quantum(self) -> int:
        return self.quantum_var.get()

    def get_ticks_per_second(self) -> int:
        return self.ticks_per_second_var.get()

    def get_arrival_burst(self) -> Tuple[int, int]:
        # Puede lanzar ValueError si no son enteros válidos
        arrival = self.arrival_var.get()
        burst = self.burst_var.get()
        return arrival, burst

    def get_selected_pid(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        item = sel[0]
        return int(self.tree.set(item, "pid"))

    def get_new_arrival_burst(self, pid: int, old_arrival: int, old_burst: int) -> Optional[Tuple[int, int]]:
         # Solicitar nuevo Arrival Time
        while True:
            new_arr_str = simpledialog.askstring("Editar Arrival Time", f"Nuevo Arrival Time para P{pid}:", initialvalue=str(old_arrival), parent=self)
            if new_arr_str is None: return None # Cancelado
            try:
                new_arr = int(new_arr_str)
                if new_arr < 0: raise ValueError
                break
            except ValueError:
                messagebox.showerror("Error de Entrada", "Por favor, introduce un número entero no negativo para Arrival Time.")
        # Solicitar nuevo Burst Time
        while True:
            new_burst_str = simpledialog.askstring("Editar Burst Time", f"Nuevo Burst Time para P{pid}:", initialvalue=str(old_burst), parent=self)
            if new_burst_str is None: return None # Cancelado
            try:
                new_burst = int(new_burst_str)
                if new_burst <= 0: raise ValueError
                break
            except ValueError:
                messagebox.showerror("Error de Entrada", "Por favor, introduce un número entero positivo para Burst Time.")
        return new_arr, new_burst

    def get_gantt_zoom(self) -> int:
        return self.gantt_zoom_var.get()

    def get_canvas_time_scale_base(self) -> float:
        return self.canvas_time_scale_base

    def set_running_state(self, running: bool):
        self.running = running
        state = tk.NORMAL if running else tk.DISABLED
        pause_state = tk.NORMAL if running else tk.DISABLED
        self.btn_start.config(state=tk.DISABLED if running else tk.NORMAL)
        self.btn_pause.config(state=pause_state)
        self.btn_step.config(state=tk.DISABLED if running else tk.NORMAL)

    def set_initial_state(self, initial: bool):
        self.initial_state = initial

    def set_canvas_time_scale(self, scale: float):
        self.canvas_time_scale = scale

    def set_next_pid(self, next_pid: int):
        # Este método no es necesario si el PID se maneja completamente en el modelo/presenter
        pass

    def show_message(self, title: str, message: str, type: str = "info"):
        if type == "info":
            messagebox.showinfo(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        elif type == "error":
            messagebox.showerror(title, message)

    def confirm_action(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)

    def ask_string(self, title: str, prompt: str, initialvalue: str = "") -> Optional[str]:
        return simpledialog.askstring(title, prompt, initialvalue=initialvalue, parent=self)

    def refresh_process_table(self, processes: Dict[int, Process], scheduler_state: Any):
        """Actualiza la tabla de procesos con la información más reciente."""
        # Limpiar tabla
        for r in self.tree.get_children():
            self.tree.delete(r)
        row_count = 0
        # Obtener estado del scheduler (necesario para calcular el status)
        # Este paso es un poco incómodo, quizás el Presenter debería pasar el status calculado
        # Por ahora, asumimos que scheduler_state tiene current, ready, future, finished
        current_pid = scheduler_state.current.pid if scheduler_state.current else None
        ready_pids = [p.pid for p in scheduler_state.ready]
        future_pids = [p.pid for p in scheduler_state.future]
        finished_pids = [p.pid for p in scheduler_state.finished]

        def _status_of(p: Process) -> str:
            if current_pid is not None and current_pid == p.pid:
                return "Running"
            if p.pid in ready_pids:
                return "Ready"
            if p.pid in future_pids:
                return "Ready"
            if p.pid in finished_pids:
                return "Finished"
            return "Idle"

        # Ordenar procesos por PID
        for pid in sorted(processes.keys()):
            p = processes[pid]
            status = _status_of(p)
            start = "" if p.start_time is None else str(p.start_time)
            comp = "" if p.completion_time is None else str(p.completion_time)
            turnaround_time = ""
            waiting_time = ""
            ntat = ""
            current_time = scheduler_state.time # Asumimos que se pasa el tiempo actual
            if p.completion_time is not None:
                tat_value = p.completion_time - p.arrival
                turnaround_time = str(tat_value)
                waiting_time = str(tat_value - p.burst)
                if p.burst > 0:
                    ntat = f"{tat_value / p.burst:.2f}"
                else:
                    ntat = "∞"
            elif p.start_time is not None:
                # Mostrar valores parciales mientras se ejecuta
                current_turnaround = current_time - p.arrival
                current_waiting = current_turnaround - (p.burst - p.remaining)
                turnaround_time = f"{current_turnaround}+"
                waiting_time = f"{current_waiting}+"
                if p.burst > 0:
                    ntat = f"{current_turnaround / p.burst:.2f}+"
                else:
                    ntat = "∞"
            # Aplicar colores alternados a las filas
            tags = ('evenrow',) if row_count % 2 == 0 else ('oddrow',)
            self.tree.insert("", tk.END, values=(p.pid, p.arrival, p.burst, start, p.remaining, comp, turnaround_time, waiting_time, ntat, status), tags=tags)
            row_count += 1
        self.update_row_tags()
        # Seleccionar y resaltar el proceso en ejecución
        if current_pid:
            for iid in self.tree.get_children():
                if int(self.tree.set(iid, "pid")) == current_pid:
                    self.tree.selection_set(iid)
                    self.tree.focus(iid)
                    self.tree.see(iid)

    def update_queues_display(self, time: int, current_pid: Optional[int], ready_pids: List[int]):
        """Actualiza el marco que muestra el estado actual de las colas."""
        ready_pids_str = ", ".join(f"P{p}" for p in ready_pids) or "Ninguno"
        current_pid_str = f"P{current_pid}" if current_pid else "Ninguno"
        queues_text = (f"Tiempo Actual: {time}\n"
                       f"Ejecutando: {current_pid_str}\n"
                       f"Cola Ready: [{ready_pids_str}]")
        self.queues_label.config(text=queues_text)

    def update_metrics_display(self, metrics: Dict[str, Any]):
        """Calcula y muestra las métricas de rendimiento."""
        if not metrics:
            self.metrics_label.config(text="Métricas: No hay procesos finalizados.")
            return
        avg_ntat_str = f"{metrics['avg_ntat']:.2f}"
        cv_ntat_str = f"{metrics['cv_ntat']:.2f}" if metrics['cv_ntat'] is not None else "N/A"
        txt = (f"Turnaround Promedio={metrics['avg_turnaround']:.2f} | Espera Promedio={metrics['avg_waiting']:.2f}\n"
             f"Cambios de Contexto={metrics['context_switches']}             | Makespan={metrics['makespan']}\n"
               f"NTAT Promedio={avg_ntat_str}                    | Coef. Var. NTAT={cv_ntat_str} %")
        self.metrics_label.config(text=f"Métricas:\n{txt}")

    def log_message(self, message: str):
        """Añade un mensaje al log de eventos."""
        self.log.insert(tk.END, f"{message}\n")
        self.log.see(tk.END) # Desplazar al final

    def draw_static_gantt(self, time: int, scale: float):
        """Dibuja los elementos estáticos del diagrama de Gantt (eje de tiempo, etiquetas)."""
        self.canvas.delete("gantt_static")
        self.canvas.create_text(5, 6, anchor=tk.NW, text=f"Tiempo: {time}",
                               tag="gantt_static", font=("Segoe UI", 8, "bold"), fill=self.text_color)
        self.canvas.create_text(100, 6, anchor=tk.NW, text="CPU",
                               tag="gantt_static", font=("Segoe UI", 9, "bold"), fill=self.text_color)
        self.canvas.create_line(0, 30, self.canvas.winfo_width(), 30,
                               fill=self.border_color, tag="gantt_static")
        canvas_width = max(self.canvas.winfo_width(), 800)
        if scale <= 0:
            time_step = 1
        else:
            time_step = max(1, round(50 / scale))
            if time_step < 5:
                time_step = 1
            elif time_step < 10:
                time_step = 5
            else:
                time_step = max(10, round(time_step / 10) * 10)
        max_time_to_draw = max(time + 50, int((canvas_width + 100) / scale))
        for t in range(0, max_time_to_draw + 1, time_step):
            x = t * scale
            self.canvas.create_line(x, 30, x, 35, fill=self.border_color, tag="gantt_static")
            self.canvas.create_text(x, 38, anchor=tk.N, text=str(t), font=("Segoe UI", 7), fill=self.text_color, tag="gantt_static")
        needed_width = max_time_to_draw * scale + 100
        current_canvas_width = self.canvas.winfo_width()
        if needed_width > current_canvas_width:
            self.canvas.config(scrollregion=(0, 0, needed_width, self.canvas.winfo_height()))
        else:
            self.canvas.config(scrollregion=(0, 0, max(current_canvas_width, needed_width), self.canvas.winfo_height()))

    def draw_execution_burst(self, pid: Optional[int], start_time: int, duration: int, scale: float):
        """
        Dibuja una barra representando una ráfaga de ejecución en el diagrama de Gantt.
        """
        if duration <= 0:
            return
        height = 28
        row_y = 38
        x0 = start_time * scale
        x1 = (start_time + duration) * scale
        tags = ("burst",)
        if pid is not None:
            color = self._color_for_pid(pid)
            self.canvas.create_rectangle(x0, row_y, x1, row_y + height, fill=color, outline=self.border_color, tags=tags)
            if x1 - x0 > 20: # Solo mostrar texto si hay espacio
                self.canvas.create_text((x0 + x1)/2, row_y + height/2, text=f"P{pid}", fill="white", font=("Segoe UI", 8, "bold"), tags=tags)
            self.canvas.create_text(x0, row_y + height + 10, text=str(start_time), font=("Segoe UI", 7), fill=self.text_color, tags=tags)
            if duration > 1:
                self.canvas.create_text(x1, row_y + height + 10, text=str(start_time + duration), font=("Segoe UI", 7), fill=self.text_color, tags=tags)
        else: # Ráfaga de IDLE
            self.canvas.create_rectangle(x0, row_y, x1, row_y + height, fill="#e0e0e0", outline=self.border_color, tags=tags)
            if x1 - x0 > 30: # Solo mostrar texto si hay espacio
                self.canvas.create_text((x0 + x1)/2, row_y + height/2, text="IDLE", fill="#666666", font=("Segoe UI", 8), tags=tags)
            self.canvas.create_text(x0, row_y + height + 10, text=str(start_time), font=("Segoe UI", 7), fill=self.text_color, tags=tags)
            if duration > 1:
                self.canvas.create_text(x1, row_y + height + 10, text=str(start_time + duration), font=("Segoe UI", 7), fill=self.text_color, tags=tags)

    def update_gantt_time_line(self, time: int, scale: float):
        """Actualiza la línea de tiempo actual en el Gantt."""
        self.canvas.delete("tline")
        x_current = time * scale
        self.canvas.create_line(x_current, 0, x_current, self.canvas.winfo_height(), dash=(2,2), fill=self.header_color, tag="tline")
        needed_width = (time + 5) * scale
        current_canvas_width = self.canvas.winfo_width()
        if needed_width > current_canvas_width:
             self.canvas.config(scrollregion=(0, 0, needed_width, self.canvas.winfo_height()))
        self.canvas.xview_moveto(max(0, (x_current - self.canvas.winfo_width()) / needed_width))

    def clear_gantt(self):
        """Limpia el contenido del Gantt."""
        self.canvas.delete("all")

    def redraw_gantt_bursts(self, history: List[Tuple[Optional[int], int, int]], scale: float):
        """Redibuja todas las ráfagas almacenadas en el historial del Gantt."""
        for entry in history:
             if len(entry) >= 3:
                 pid, start_time, duration = entry[0], entry[1], entry[2]
                 self.draw_execution_burst(pid, start_time, duration, scale)

    def toggle_full_gantt_view(self, gantt_only: bool):
        """
        Alterna entre la vista completa (panel izquierdo + Gantt + métricas + log)
        y una vista solo con el Gantt. (Lógica movida de RRApp.toggle_gantt_view)
        """
        if gantt_only:
            if self.left_panel:
                self.left_panel.pack_forget()
            for child in self.right_panel.winfo_children():
                if child != self.gantt_frame:
                    child.pack_forget()
            self.gantt_frame.pack(fill=tk.BOTH, expand=True, pady=(10,10), padx=5)
        else:
            if self.left_panel:
                self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=0, ipadx=12, ipady=5)
            self.gantt_frame.pack(fill=tk.BOTH, expand=True, pady=(10,5), padx=5)
            self.queues_label.master.pack(fill=tk.X, pady=5, padx=5)
            self.metrics_label.master.pack(fill=tk.X, pady=(5,5), padx=5)
            # Re-find log frame if needed or pass reference
            # Assuming it's the last child added
            self.log_frame = self.right_panel.winfo_children()[-1]
            self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        self.update_idletasks()

    # --- Métodos auxiliares ---
    def _color_for_pid(self, pid: int) -> str:
        """
        Genera un color único basado en el PID para usar en el Gantt.
        Returns:
            str: Un color en formato hexadecimal (e.g., "#a1b2c3").
        """
        # Algoritmo para generar colores distintos basados en el PID
        hue = (pid * 137.5) % 360 # 137.5 es el ángulo áureo, ayuda a distribuir colores
        saturation = 0.7
        lightness = 0.5
        c = (1 - abs(2 * lightness - 1)) * saturation
        x = c * (1 - abs((hue / 60) % 2 - 1))
        m = lightness - c / 2
        r, g, b = 0, 0, 0
        if 0 <= hue < 60: r, g, b = c, x, 0
        elif 60 <= hue < 120: r, g, b = x, c, 0
        elif 120 <= hue < 180: r, g, b = 0, c, x
        elif 180 <= hue < 240: r, g, b = 0, x, c
        elif 240 <= hue < 300: r, g, b = x, 0, c
        elif 300 <= hue < 360: r, g, b = c, 0, x
        r = int((r + m) * 255)
        g = int((g + m) * 255)
        b = int((b + m) * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
