# 🖥️ Simulador de Planificación Round Robin

Una aplicación de escritorio desarrollada en **Python** con **Tkinter** que simula el algoritmo de planificación de procesos **Round Robin**.
Permite configurar el *quantum*, añadir procesos y visualizar la ejecución paso a paso mediante una interfaz gráfica interactiva.

---

## ✨ Características Principales

### 🎯 Algoritmo Implementado

* **Round Robin**: Algoritmo de planificación de CPU con *quantum* configurable.

  * Ejecución preemptiva.
  * Cola circular de procesos.
  * Cálculo automático de métricas de rendimiento.

### 📊 Visualizaciones Interactivas

* **Ejecución Paso a Paso**: Muestra cómo los procesos van ocupando la CPU.
* **Tablas de Resultados**: Métricas detalladas por proceso (AT, BT, CT, TT, WT).
* **📈 Análisis de Rendimiento**: Promedios de espera y turnaround.
* **Indicadores Visuales**: Representación en Tkinter con distinción por proceso.

### 🛠️ Funcionalidades Avanzadas

* **⚙️ Quantum Configurable**: Ajusta el valor del *quantum* según la simulación.
* **🔄 Gestión de Cola**: Inserción y rotación dinámica de procesos.
* **📊 Cálculos Automáticos**: Métricas generadas al finalizar la ejecución.
* **Interfaz Intuitiva**: Fácil de usar para propósitos educativos.

---

## 🚀 Instalación y Configuración

### Prerrequisitos

* **Python 3.10+**

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tuusuario/round_robin.git  
cd round_robin
```

### 2. Ejecutar la Aplicación

```bash
python3 -m round_robin.main
```

---

## 📖 Guía de Uso

### Añadir Procesos

1. **PID**: Identificador del proceso (ej: P1, P2, P3).
2. **Arrival Time (AT)**: Tiempo de llegada al sistema.
3. **Burst Time (BT)**: Tiempo de ejecución requerido.

### Configurar Quantum

* Establece el valor del *quantum* antes de iniciar la simulación.

### Visualización

* Observa cómo los procesos se alternan en la CPU.
* Revisa las métricas generadas al finalizar.

---

## 🧮 Métricas Calculadas

### Tiempos Fundamentales

* **AT (Arrival Time)**: Tiempo de llegada.
* **BT (Burst Time)**: Tiempo de ráfaga requerido.
* **CT (Completion Time)**: Tiempo de finalización.
* **TT (Turnaround Time)**: Tiempo total en el sistema (CT - AT).
* **WT (Waiting Time)**: Tiempo en cola de espera (TT - BT).

### Métricas de Rendimiento

* **Tiempo Promedio de Espera**.
* **Tiempo Promedio de Turnaround**.
* **Análisis de Eficiencia del algoritmo Round Robin**.

---

## 📁 Estructura del Proyecto

```
round_robin/
├── main.py                 # Punto de entrada
├── models/
│   └── scheduler.py        # Lógica del algoritmo Round Robin
├── views/
│   └── tkinter_view.py     # Interfaz gráfica (Tkinter)
└── presenters/
    └── rr_presenter.py     # Conexión entre modelo y vista (MVP)
```

---

## 🔧 Arquitectura Técnica

### Backend (Modelo)

* Implementación del algoritmo Round Robin.
* Gestión de procesos y cálculo de métricas.

### Frontend (Vista)

* Interfaz desarrollada en **Tkinter**.
* Entrada de procesos y parámetros.
* Visualización de resultados.

### Conexión (Presenter)

* Maneja la lógica entre la vista y el modelo.
* Controla la simulación y actualización de la interfaz.

---

## 🎓 Casos de Uso Educativos

* **Simulación Académica**: Ideal para comprender el funcionamiento del algoritmo Round Robin.
* **Pruebas de Quantum**: Observar cómo varía el rendimiento según el quantum elegido.
* **Comparación con Otros Algoritmos**: Puede extenderse para contrastar con **FCFS** o **SJF**.

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Haz un *fork* del repositorio.
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`).
3. Haz *commit* de tus cambios (`git commit -m "Nueva funcionalidad"`).
4. Haz *push* a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un *Pull Request*.

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**.