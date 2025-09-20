# models/scheduler.py
import math
from collections import deque
from typing import Optional, List, Tuple, Deque

# --- CLASES DEL MODELO ---
class Process:
    """
    Representa un proceso individual en el sistema.
    Almacena sus atributos estáticos (PID, tiempo de llegada, ráfaga de CPU)
    y su estado dinámico durante la simulación.
    """
    def __init__(self, pid: int, arrival: int, burst: int):
        """
        Inicializa un nuevo proceso.
        Args:
            pid (int): Identificador único del proceso.
            arrival (int): Tiempo en el que el proceso llega al sistema.
            burst (int): Tiempo total de CPU requerido por el proceso.
        """
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst  # Tiempo de CPU restante por ejecutar
        self.start_time: Optional[int] = None  # Tiempo en que comienza su primera ejecución
        self.completion_time: Optional[int] = None  # Tiempo en que termina completamente

class SchedulerObserver:
    """
    Clase base abstracta para objetos que desean recibir notificaciones
    sobre eventos del planificador Round Robin.
    Define la interfaz que deben implementar los observadores.
    """
    def on_tick(self, time: int): pass
    def on_context_switch(self, pid: Optional[int], time: int): pass
    def on_process_finished(self, proc: Process, time: int): pass
    def on_execution_burst(self, pid: Optional[int], start_time: int, duration: int): pass

class RoundRobinScheduler:
    """
    Implementa la lógica del algoritmo de planificación Round Robin.
    Gestiona las colas de procesos, el reloj del sistema y notifica eventos
    a los observadores registrados.
    """
    def __init__(self, quantum: int = 200):
        """
        Inicializa el planificador.
        Args:
            quantum (int): Cantidad de tiempo asignada a cada proceso en turno.
        """
        self.quantum = quantum
        self.time = 0  # Reloj del sistema
        self.future = []  # Lista de procesos que aún no han llegado (ordenada por arrival)
        self.ready: Deque[Process] = deque()  # Cola de procesos listos para ejecutar
        self.finished = []  # Lista de procesos terminados
        self.current: Optional[Process] = None  # Proceso en ejecución actual
        self.current_consumed = 0  # Tiempo consumido del quantum del proceso actual
        self.context_switches = 0  # Contador de cambios de contexto
        self.observers = []  # Lista de observadores registrados
        self.history = []  # Historial de ráfagas de ejecución [(pid, start_time, duration), ...]
        # Para rastrear la ráfaga en ejecución actual
        self.current_burst_start = 0
        self.current_burst_pid = None

    def subscribe(self, obs: SchedulerObserver):
        """Agrega un observador a la lista."""
        self.observers.append(obs)

    def set_quantum(self, q: int):
        """Cambia el valor del quantum."""
        self.quantum = q

    def add_process(self, proc: Process):
        """
        Añade un proceso al planificador.
        Lo coloca en la cola 'ready' si ya ha llegado, o en 'future' si no.
        """
        if proc.arrival <= self.time:
            self.ready.append(proc)
        else:
            self.future.append(proc)
            self.future.sort(key=lambda p: p.arrival) # Mantiene 'future' ordenada

    def _move_arrivals(self):
        """
        Mueve procesos de la lista 'future' a la cola 'ready'
        si su tiempo de llegada es menor o igual al tiempo actual del sistema.
        """
        moved = [p for p in self.future if p.arrival <= self.time]
        self.future = [p for p in self.future if p.arrival > self.time]
        for p in moved:
            self.ready.append(p)

    # --- Métodos de notificación a observadores ---
    def _notify_tick(self):
        """Notifica a los observadores que ha avanzado una unidad de tiempo."""
        for o in self.observers:
            o.on_tick(self.time)

    def _notify_context_switch(self, pid: Optional[int]):
        """Notifica a los observadores que ha ocurrido un cambio de contexto."""
        for o in self.observers:
            o.on_context_switch(pid, self.time)

    def _notify_finished(self, proc: Process):
        """Notifica a los observadores que un proceso ha terminado."""
        for o in self.observers:
            o.on_process_finished(proc, self.time)

    def _notify_execution_burst(self, pid: Optional[int], start_time: int, duration: int):
        """
        Notifica a los observadores sobre una ráfaga de ejecución.
        También almacena la ráfaga en el historial.
        """
        if duration > 0:
            self.history.append((pid, start_time, duration))
        for obs in self.observers:
            obs.on_execution_burst(pid, start_time, duration)

    # --- Gestión de ráfagas de ejecución ---
    def _end_current_burst(self):
        """Finaliza la ráfaga de ejecución actual y notifica."""
        if self.current_burst_pid is not None:
            duration = self.time - self.current_burst_start
            if duration > 0:
                self._notify_execution_burst(self.current_burst_pid, self.current_burst_start, duration)
        self.current_burst_pid = None
        self.current_burst_start = self.time

    def _start_new_burst(self, pid: Optional[int]):
        """Inicia una nueva ráfaga de ejecución."""
        self.current_burst_pid = pid
        self.current_burst_start = self.time

    def step(self) -> bool:
        """
        Ejecuta un paso de la simulación (avanza una unidad de tiempo).
        Implementa la lógica principal del algoritmo Round Robin.
        Returns:
            bool: True si la simulación puede continuar, False si ha terminado.
        """
        self._move_arrivals()
        # Caso 1: No hay proceso en ejecución ni en la cola ready
        if self.current is None and not self.ready:
            # Si hay procesos futuros, avanzar el tiempo hasta su llegada
            if self.future:
                # Si estábamos en IDLE, notificar esa ráfaga
                if self.current_burst_pid is None and self.time > self.current_burst_start:
                    self._notify_execution_burst(None, self.current_burst_start, self.time - self.current_burst_start)
                self.time = self.future[0].arrival
                self._move_arrivals()
                self._notify_tick()
                self._start_new_burst(None) # Iniciar ráfaga de IDLE
                return True
            else:
                # No hay más procesos, finalizar simulación
                self._end_current_burst()
                return False
        # Caso 2: Seleccionar un nuevo proceso para ejecutar
        if self.current is None:
            self._end_current_burst() # Finalizar ráfaga anterior (de IDLE o de otro proceso)
            self.current = self.ready.popleft()
            self.current_consumed = 0
            self.context_switches += 1
            if self.current.start_time is None:
                self.current.start_time = self.time
            self._notify_context_switch(self.current.pid)
            self._start_new_burst(self.current.pid) # Iniciar ráfaga del nuevo proceso
        # Caso 3: El proceso en ejecución ha cambiado (por preemption o finalización)
        elif self.current_burst_pid != self.current.pid:
            self._end_current_burst()
            self._start_new_burst(self.current.pid)
        # Ejecutar el proceso actual por una unidad de tiempo
        self.current.remaining -= 1
        self.current_consumed += 1
        self.time += 1
        self._notify_tick()
        self._move_arrivals() # Verificar si llegan nuevos procesos
        # Caso 4: El proceso actual ha terminado
        if self.current.remaining == 0:
            self.current.completion_time = self.time
            finished = self.current
            self.finished.append(finished)
            self._notify_finished(finished)
            self._end_current_burst() # Finalizar su ráfaga
            self.current = None
            self.current_consumed = 0
            return True
        # Caso 5: El quantum del proceso actual se ha agotado (preemption)
        if self.current_consumed >= self.quantum:
            self._end_current_burst() # Finalizar su ráfaga
            self.ready.append(self.current) # Moverlo al final de la cola ready
            self.current = None
            self.current_consumed = 0
            return True
        # Caso 6: El proceso sigue ejecutando
        return True

    def reset(self):
        """Reinicia el estado del planificador, manteniendo los procesos."""
        self.time = 0
        self.future = []
        self.ready = deque()
        self.finished = []
        self.current = None
        self.current_consumed = 0
        self.context_switches = 0
        self.history = []
        self.current_burst_start = 0
        self.current_burst_pid = None

    def is_done(self) -> bool:
        """
        Verifica si la simulación ha terminado.
        Returns:
            bool: True si no quedan procesos en future, ready o current.
        """
        return not (self.future or self.ready or self.current)

    def metrics(self):
        """
        Calcula y devuelve métricas de rendimiento de la simulación.
        Returns:
            dict: Diccionario con las métricas calculadas.
        """
        n = len(self.finished)
        if n == 0:
            return {}
        # Calcular sumas para métricas promedio
        total_turnaround = sum((p.completion_time - p.arrival) for p in self.finished if p.completion_time is not None)
        total_waiting = sum(((p.completion_time - p.arrival) - p.burst) for p in self.finished if p.completion_time is not None)
        total_response = sum(((p.start_time - p.arrival) if p.start_time is not None else 0) for p in self.finished)
        # Makespan (tiempo total de la simulación)
        makespan = max((p.completion_time for p in self.finished if p.completion_time is not None), default=0)
        # Calcular NTAT y sus estadísticas
        ntat_values = []
        for p in self.finished:
            if p.completion_time is not None and p.burst > 0:
                 tat = p.completion_time - p.arrival
                 ntat = tat / p.burst
                 ntat_values.append(ntat)
        avg_ntat = sum(ntat_values) / len(ntat_values) if ntat_values else 0
        stdev_ntat = 0
        cv_ntat = 0
        if len(ntat_values) > 1:
            variance_ntat = sum((ntat - avg_ntat) ** 2 for ntat in ntat_values) / (len(ntat_values) - 1)
            stdev_ntat = math.sqrt(variance_ntat)
            if avg_ntat > 0:
                cv_ntat = stdev_ntat / avg_ntat * 100
        return {
            "avg_turnaround": total_turnaround / n,
            "avg_waiting": total_waiting / n,
            "avg_response": total_response / n,
            "context_switches": self.context_switches,
            "throughput": n / makespan if makespan > 0 else float('inf'),
            "makespan": makespan,
            "avg_ntat": avg_ntat,
            "stdev_ntat": stdev_ntat,
            "cv_ntat": cv_ntat
        }

# --- PUNTO DE ENTRADA PARA PRUEBAS DEL MODELO (Opcional) ---
# def main():
#     # Puedes probar el modelo aquí sin la interfaz gráfica
#     pass

# if __name__ == "__main__":
#     main()