# presenters/rr_presenter.py
import tkinter as tk
from typing import Optional, List, Dict, Any, Tuple
from models.scheduler import RoundRobinScheduler, Process, SchedulerObserver
from views.tkinter_view import RRViewInterface

class RRPresenter(SchedulerObserver):
    """
    Presentador que coordina la lógica de la aplicación.
    Se suscribe al modelo (RoundRobinScheduler) y actualiza la vista (RRViewInterface).
    """
    def __init__(self, model: RoundRobinScheduler, view: RRViewInterface):
        self.model = model
        self.view = view
        self.model.subscribe(self) # Suscribirse a eventos del modelo

        # Estado de la aplicación
        self.running = False
        self.tick_delay_ms = 350  # Retraso entre pasos en modo automático
        self.after_id = None # Para cancelar after en Tkinter
        self.processes: Dict[int, Process] = {} # Diccionario {pid: Process}
        self.next_pid = 1  # Siguiente PID disponible

        # Inicializar la vista con el estado
        self.view.set_initial_state(True)
        self.view.set_running_state(False)
        # self.view.refresh_process_table(self.processes, self.model) # Inicialmente vacío

    # --- Métodos para manejar eventos de la Vista ---
    def handle_set_speed(self):
        try:
            ticks_per_second = self.view.get_ticks_per_second()
            if ticks_per_second <= 0:
                raise ValueError("Ticks por segundo debe ser positivo.")
            self.tick_delay_ms = int(1000 / ticks_per_second)
            self.view.log_message(f"Velocidad establecida a {ticks_per_second} ticks/segundo (Retraso: {self.tick_delay_ms} ms/tick).")
        except (tk.TclError, ValueError) as e:
            self.view.show_message("Error", f"Valor inválido para Ticks/Segundo: {e}", "error")
            # Revertir valor en la vista si es necesario
            # self.view.set_ticks_per_second(...) # Omitido por simplicidad

    def handle_set_gantt_zoom(self):
        try:
            zoom_percent = self.view.get_gantt_zoom()
            if zoom_percent <= 0:
                raise ValueError("El zoom debe ser positivo.")
            canvas_time_scale_base = self.view.get_canvas_time_scale_base()
            new_scale = canvas_time_scale_base * (zoom_percent / 100.0)
            self.view.set_canvas_time_scale(new_scale) # Actualizar en la vista
            self.view.log_message(f"Zoom del Gantt establecido a {zoom_percent}% (Escala: {new_scale:.2f} px/unidad).")
            # Redibujar Gantt
            self.view.clear_gantt()
            self.view.draw_static_gantt(self.model.time, new_scale)
            self.view.redraw_gantt_bursts(self.model.history, new_scale)
            # Re-dibujar la línea de tiempo actual si no es el estado inicial
            if not self.view.initial_state and self.model.time > 0:
                self.view.update_gantt_time_line(self.model.time, new_scale)
        except (tk.TclError, ValueError) as e:
            self.view.show_message("Error", f"Valor inválido para Zoom: {e}", "error")
            # Revertir valor en la vista si es necesario

    def handle_add_process(self):
        try:
            arrival, burst = self.view.get_arrival_burst()
            if burst <= 0:
                self.view.show_message("Error de Entrada", "El Burst Time debe ser mayor a 0.", "error")
                return
            pid = self.next_pid
            self.next_pid += 1
            p = Process(pid=pid, arrival=arrival, burst=burst)
            self.processes[pid] = p
            self.model.add_process(p)
            self.view.log_message(f"Proceso P{pid} añadido (Arrival={arrival}, Burst={burst})")
            self.view.refresh_process_table(self.processes, self.model)
            # Habilitar botones si es el primer proceso
            if len(self.processes) == 1:
                 self.view.set_running_state(self.running) # Actualiza estado de botones
        except tk.TclError:
            self.view.show_message("Error de Entrada", "Arrival y Burst deben ser números enteros válidos.", "error")

    def handle_edit_process(self, pid: int):
        proc = self.processes.get(pid)
        if proc is None:
            return
        if proc.start_time is not None:
            self.view.show_message("Editar Proceso", "No se puede editar un proceso que ya ha iniciado.", "warning")
            return
        if self.running:
             self.view.show_message("Editar Proceso", "Pausa la simulación para editar procesos.", "warning")
             return

        new_values = self.view.get_new_arrival_burst(pid, proc.arrival, proc.burst)
        if new_values is None: # Cancelado
            return
        new_arr, new_burst = new_values

        # Actualizar proceso
        proc.arrival = new_arr
        proc.burst = new_burst
        proc.remaining = proc.burst # Reiniciar tiempo restante
        # Eliminar del planificador y volver a añadir
        self._remove_proc_from_scheduler(proc.pid)
        self.model.add_process(proc)
        self.view.log_message(f"Proceso P{pid} editado: Arrival={proc.arrival}, Burst={proc.burst}")
        self.view.refresh_process_table(self.processes, self.model)
        self.handle_reset() # Reiniciar simulación para reflejar cambios

    def handle_delete_process(self, pid: int):
        proc = self.processes.get(pid)
        if proc is None: return
        if self.running and self.model.current and self.model.current.pid == pid:
            self.view.show_message("Eliminar Proceso", "No se puede eliminar un proceso que está en ejecución.", "warning")
            return
        if self.running:
             self.view.show_message("Eliminar Proceso", "Pausa la simulación para eliminar procesos.", "warning")
             return

        confirm = self.view.confirm_action("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar el proceso P{pid}?")
        if not confirm: return

        # Eliminar del planificador y del diccionario
        self._remove_proc_from_scheduler(pid)
        del self.processes[pid]
        self.view.log_message(f"Proceso P{pid} eliminado.")
        self.view.refresh_process_table(self.processes, self.model)
        self.handle_reset() # Reiniciar simulación

    def handle_set_quantum(self):
        q = self.view.get_quantum()
        self.model.set_quantum(q)
        self.view.log_message(f"Quantum establecido a {q}.")

    def handle_load_sample(self):
        if self.processes or self.running:
            self.view.show_message(
                "Acción no permitida",
                "Para cargar procesos de ejemplo, primero debes usar 'Clear All' para limpiar el estado actual.",
                "warning"
            )
            return
        sample = [(100, 200), (300, 500), (600, 200), (800, 600), (1000, 700), (1100, 300)]
        self.next_pid = 1
        for arr, b in sample:
            pid = self.next_pid
            self.next_pid += 1
            p = Process(pid=pid, arrival=arr, burst=b)
            self.processes[pid] = p
            self.model.add_process(p)
        self.view.refresh_process_table(self.processes, self.model)
        self.view.log_message("Procesos de ejemplo cargados.")
        self.view.set_running_state(self.running) # Actualiza estado de botones

    def handle_start(self):
        if self.running: return
        if not self.processes:
            self.view.show_message("Sin Procesos", "Agrega procesos antes de iniciar la simulación.", "warning")
            return
        self._ensure_scheduler_has_procs()
        self.model.set_quantum(self.view.get_quantum())
        self.running = True
        self.view.set_running_state(True)
        self.view.set_initial_state(False)
        self.view.log_message("Simulación iniciada.")
        self._schedule_tick() # Iniciar bucle de simulación

    def handle_pause(self):
        if not self.running: return
        self.running = False
        # Cancelar el bucle de simulación si está usando after
        if self.after_id:
            # Se necesita acceso a la vista para `after_cancel`
            # Una forma es pasar `after_cancel` como callback o usar un método en la vista
            # Por simplicidad, asumiremos que `view` tiene acceso a `after_cancel`
            # Esto puede requerir ajustes si `view` es solo una interfaz
            # Alternativa: pasar `after_cancel` al presenter o usar una cola de eventos
            # Aquí asumimos que `view` es `RRAppTk` que tiene `after_cancel`
            if hasattr(self.view, 'after_cancel'):
                 self.view.after_cancel(self.after_id)
            self.after_id = None
        self.view.set_running_state(False)
        self.view.log_message("Simulación pausada.")

    def handle_step(self):
        if self.running:
            self.handle_pause()
        if not self.processes and self.model.is_done():
            self.view.show_message("Fin de Simulación", "No hay más procesos para ejecutar.", "info")
            return
        self._ensure_scheduler_has_procs()
        self.model.set_quantum(self.view.get_quantum())
        steps_to_execute = self.view.get_ticks_per_second()
        steps_executed = 0
        active = True
        # Ejecutar varios pasos para hacer 'Step' más perceptible
        while steps_executed < steps_to_execute and active:
            active = self.model.step()
            steps_executed += 1
        # Actualizar vistas (ya se hará por notificaciones Observer, pero podemos forzarlo)
        self._update_views()
        # self.view.update_queues_display(self.model.time, self.model.current.pid if self.model.current else None, [p.pid for p in self.model.ready])
        if not active:
            self.view.log_message("Simulación finalizada.")
            self._show_metrics()
            self.view.set_running_state(False) # Deshabilitar botones
            self.view.set_initial_state(True)
            # self.view.clear_gantt_time_line() # O borrar "tline" directamente
            self.view.clear_gantt() # Limpiar todo el Gantt?
            self.view.draw_static_gantt(self.model.time, self.view.canvas_time_scale) # Redibujar estático
            self.view.redraw_gantt_bursts(self.model.history, self.view.canvas_time_scale) # Redibujar ráfagas

    def handle_reset(self):
        """Reinicia la simulación, manteniendo los procesos definidos."""
        if self.running: self.handle_pause()
        self.model.reset()
        for p in self.processes.values():
            p.remaining = p.burst
            p.start_time = None
            p.completion_time = None
            self.model.add_process(p) # Volver a añadir al planificador

        # Limpiar y redibujar Gantt
        self.view.clear_gantt()
        self.view.draw_static_gantt(0, self.view.canvas_time_scale) # Dibujar con tiempo 0
        # self.view.set_canvas_scroll(...) # Reset scroll si es necesario

        self.view.refresh_process_table(self.processes, self.model)
        self.view.update_queues_display(0, None, []) # Resetear estado
        self.view.update_metrics_display({}) # Limpiar métricas
        self.view.set_running_state(False) # Resetear botones
        self.view.log_message("Simulación reiniciada. Los procesos han sido preservados.")
        self.view.set_initial_state(True)

    def handle_clear_all(self):
        """Limpia todos los datos de la aplicación, volviendo al estado inicial."""
        if self.running:
            self.handle_pause()
        self.processes.clear()
        self.next_pid = 1
        self.model.reset()

        # Limpiar y redibujar Gantt
        self.view.clear_gantt()
        self.view.draw_static_gantt(0, self.view.canvas_time_scale)

        self.view.refresh_process_table(self.processes, self.model)
        self.view.update_queues_display(0, None, [])
        self.view.update_metrics_display({})
        self.view.set_running_state(False)
        self.view.log_message("All data cleared. Application reset to initial state.")
        self.view.set_initial_state(True)
        self.view.log_message("Application fully cleared.")

    # --- Métodos auxiliares para gestión de procesos ---
    def _remove_proc_from_scheduler(self, pid: int):
        """Elimina un proceso de todas las estructuras internas del planificador."""
        self.model.future = [p for p in self.model.future if p.pid != pid]
        self.model.ready = [p for p in self.model.ready if p.pid != pid] # Deque a lista para filtrar
        self.model.ready = type(self.model.ready)(self.model.ready) # Convertir de nuevo a deque si es necesario
        self.model.finished = [p for p in self.model.finished if p.pid != pid]
        if self.model.current and self.model.current.pid == pid:
            self.model.current = None

    def _proc_in_scheduler(self, pid: int) -> bool:
        """Verifica si un proceso está en alguna de las colas del planificador."""
        if self.model.current and self.model.current.pid == pid: return True
        if any(p.pid == pid for p in self.model.ready): return True
        if any(p.pid == pid for p in self.model.future): return True
        if any(p.pid == pid for p in self.model.finished): return True
        return False

    def _ensure_scheduler_has_procs(self):
        """
        Asegura que todos los procesos definidos por el usuario estén en el planificador.
        Útil al reiniciar o avanzar paso a paso.
        """
        for p in self.processes.values():
            if p.completion_time is None and not self._proc_in_scheduler(p.pid):
                if p.start_time is None:
                    p.remaining = p.burst # Reiniciar si no ha comenzado
                self.model.add_process(p)

    # --- Métodos de control de simulación (auxiliares) ---
    def _schedule_tick(self):
        """Ejecuta pasos de simulación en bucle automático y actualiza la UI."""
        if not self.running:
            return
        steps_per_ui_update = self.view.get_ticks_per_second()
        steps_executed = 0
        active = True
        # Ejecutar varios pasos antes de actualizar la UI para mejorar rendimiento
        while steps_executed < steps_per_ui_update and active:
            active = self.model.step()
            steps_executed += 1
        # self._update_views() # Ya se hará por notificaciones Observer
        # self.view.update_queues_display(self.model.time, self.model.current.pid if self.model.current else None, [p.pid for p in self.model.ready])
        if not active:
            self.view.log_message("Simulación finalizada.")
            self.running = False
            self.view.set_running_state(False)
            self._show_metrics()
            self.view.set_initial_state(True)
            # self.view.clear_gantt_time_line()
            return
        # Programar el siguiente tick usando `after` de la vista
        # Se necesita acceso al método `after` de Tkinter, asumimos `view` es `RRAppTk`
        if hasattr(self.view, 'after'):
            self.after_id = self.view.after(self.tick_delay_ms, self._schedule_tick)
        else:
            # Manejo alternativo si la vista no tiene acceso directo a `after`
            # Por ejemplo, usando una cola de eventos o callbacks
            pass

    def _update_views(self):
        """Actualiza las vistas de la tabla y otras partes de la UI."""
        self.view.refresh_process_table(self.processes, self.model)
        self.view.update_queues_display(self.model.time, self.model.current.pid if self.model.current else None, [p.pid for p in self.model.ready])

    def _show_metrics(self):
        """Calcula y muestra las métricas de rendimiento."""
        m = self.model.metrics()
        self.view.update_metrics_display(m)
        self.view.log_message("Métricas actualizadas.")

    # --- Implementación de SchedulerObserver ---
    # Estos métodos son llamados por el modelo cuando ocurren eventos
    def on_tick(self, time: int):
        """
        Recibe notificación de que ha avanzado un tick del reloj del sistema.
        Actualiza el encabezado del Gantt y mueve la línea de tiempo.
        """
        # self.view.refresh_gantt_header(time) # Ya se hace draw_static_gantt
        self.view.draw_static_gantt(time, self.view.canvas_time_scale)
        self.view.update_gantt_time_line(time, self.view.canvas_time_scale)
        self.view.update_queues_display(time, self.model.current.pid if self.model.current else None, [p.pid for p in self.model.ready])

    def on_context_switch(self, pid: Optional[int], time: int):
        """
        Recibe notificación de un cambio de contexto.
        Añade mensaje al log y actualiza la UI.
        """
        self.view.log_message(f"[t={time}] Cambio de contexto -> {'CPU IDLE' if pid is None else f'P{pid}'}")
        self.view.refresh_process_table(self.processes, self.model)
        # self.view.update_queues_display(self.model.time, self.model.current.pid if self.model.current else None, [p.pid for p in self.model.ready])

    def on_process_finished(self, proc: Process, time: int):
        """
        Recibe notificación de que un proceso ha terminado.
        Añade mensaje al log y actualiza la UI.
        """
        tat = proc.completion_time - proc.arrival if proc.completion_time is not None else "N/A"
        self.view.log_message(f"[t={time}] P{proc.pid} finalizado. Turnaround={tat}.")
        self.view.refresh_process_table(self.processes, self.model)
        # self.view.update_queues_display(self.model.time, self.model.current.pid if self.model.current else None, [p.pid for p in self.model.ready])

    def on_execution_burst(self, pid: Optional[int], start_time: int, duration: int):
        """
        Recibe notificación de una ráfaga de ejecución.
        Dibuja la barra en el Gantt.
        """
        self.view.draw_execution_burst(pid, start_time, duration, self.view.canvas_time_scale)
