# main.py (corregido para importar RRApp)
import tkinter as tk
from models.scheduler import RoundRobinScheduler
from views.tkinter_view import RRApp # <-- Cambiado a RRApp
from presenters.rr_presenter import RRPresenter

def main():
    """Punto de entrada del programa. Crea y ejecuta la aplicación."""
    # Crear el Modelo
    model = RoundRobinScheduler(quantum=200)

    # Crear la Vista principal (RRApp hereda de tk.Tk)
    view = RRApp(presenter=None)
    
    # Crear el Presentador y vincularlo a la Vista
    presenter = RRPresenter(model=model, view=view)
    view.presenter = presenter

    # Iniciar el bucle principal de Tkinter
    view.mainloop()

if __name__ == "__main__":
    main()