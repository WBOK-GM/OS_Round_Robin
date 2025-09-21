# 🖥️ Simulador de Planificación Round Robin

Una aplicación de escritorio desarrollada en **Python** con **Tkinter** que simula el algoritmo de planificación de procesos **Round Robin**. Permite configurar el *quantum*, añadir procesos y visualizar la ejecución paso a paso mediante una interfaz gráfica interactiva.

---

## ✨ Características Principales

### 🎯 Algoritmo Implementado

* **Round Robin**: Algoritmo de planificación de CPU con *quantum* configurable.

  * Ejecución preemptiva.
  * Cola circular de procesos.
  * Cálculo automático de métricas de rendimiento.

### 📊 Visualizaciones Interactivas

* **Ejecución Paso a Paso**: Muestra cómo los procesos van ocupando la CPU.
* **Tablas de Resultados**: Métricas detalladas por proceso (AT, BT, CT, TT, WT, NTAT).
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

* **Python 3.10 o superior**
* **Git** (para clonar el repositorio)

---

### 1. Clonar el Repositorio

```bash
git clone https://github.com/WBOK-GM/OS_Round_Robin.git
cd OS_Round_Robin
```

---

### 2. Ejecutar la Aplicación

**Windows:**

```bash
python main.py
```

**Linux / macOS:**

```bash
python3 main.py
```

---

## 📖 Guía de Uso

### 🚀 Comenzando Rápidamente

1. **Cargar Procesos de Ejemplo**: Haz clic en el botón **"Load Sample Processes"** para cargar un conjunto predeterminado de procesos.
2. **Configurar Quantum**: Ajusta el valor del quantum según sea necesario (por defecto es 200).
3. **Iniciar Simulación**:
   - **Opción 1**: Haz clic en **"Start"** para ejecutar automáticamente.
   - **Opción 2**: Usa **"Step"** para avanzar paso a paso y observar el comportamiento detallado.

---

### ⚙️ Panel de Control

| Elemento | Descripción |
|--------|-----------|
| **Quantum** | Valor del quantum para el algoritmo Round Robin. |
| **Start** | Inicia la simulación automática. |
| **Pause** | Pausa la ejecución en curso. |
| **Step** | Avanza un solo paso de tiempo (quantum). |
| **Clear All** | Elimina todos los procesos y reinicia todo. |
| **Reset** | Reinicia la simulación manteniendo los procesos. |
| **Speed** | Control deslizante para ajustar la velocidad de ejecución (1-1000%). |
| **Set Speed** | Aplica la velocidad seleccionada en el control deslizante. |

> 💡 **Nota**: El tamaño del paso de ejecución está determinado por el valor del **quantum**, mientras que la **velocidad** solo afecta la rapidez con que se muestran los pasos en la interfaz.

---

### 📋 Tabla de Procesos

Muestra todos los procesos con sus métricas en tiempo real:

| Columna | Significado |
|--------|-----------|
| **Pid** | Identificador del proceso (P1, P2, etc.) |
| **Arrival** | Tiempo de llegada (AT) |
| **Burst** | Tiempo de ráfaga requerido (BT) |
| **Start** | Tiempo en que comenzó a ejecutarse |
| **Remaining** | Tiempo restante para completar |
| **Completion** | Tiempo de finalización (CT) |
| **Turnaround** | Tiempo total en el sistema (TT = CT - AT) |
| **Waiting** | Tiempo en cola de espera (WT = TT - BT) |
| **Ntat** | Turnaround normalizado (TT/BT) |
| **Status** | Estado actual: `Running`, `Ready`, `Completed` |

---

### ➕ Gestión Manual de Procesos

Puedes agregar procesos manualmente:

1. Ingresa el **Arrival Time (AT)** (tiempo de llegada)
2. Ingresa el **Burst Time (BT)** (tiempo de ejecución)
3. Haz clic en **"Add"** para incluirlo en la tabla
4. Usa **"Delete"** para eliminar procesos seleccionados

---

### 📊 Diagrama de Gantt

Visualización gráfica de la ejecución de procesos:

- Muestra la secuencia temporal de ejecución
- Cada barra representa un proceso en la CPU
- Doble clic para hacer zoom
- Ajusta el zoom con el control **"Zoom Gantt (%)"**

---

### 📋 Estado del Sistema

Panel que muestra información en tiempo real:

- **Tiempo Actual**: Tiempo transcurrido en la simulación
- **Proceso Ejecutando**: Proceso actual en la CPU
- **Procesos en Ready**: Cola de procesos esperando

---

### 📈 Métricas Finales

Al finalizar la simulación, se muestran:

- **Tiempo Promedio de Espera (WT)**
- **Tiempo Promedio de Turnaround (TT)**
- **Eficiencia del sistema**

---

### 📝 Log de Eventos

Registro de eventos importantes durante la ejecución:

- Inicio y finalización de procesos
- Cambios de contexto
- Mensajes de advertencia o error

---

## 🧮 Métricas Calculadas

### Tiempos Fundamentales

* **AT (Arrival Time)**: Tiempo de llegada al sistema
* **BT (Burst Time)**: Tiempo de ráfaga requerido
* **CT (Completion Time)**: Tiempo de finalización
* **TT (Turnaround Time)**: Tiempo total en el sistema (CT - AT)
* **WT (Waiting Time)**: Tiempo en cola de espera (TT - BT)
* **NTAT (Normalized TAT)**: TT / BT (turnaround normalizado)

---

## 📁 Estructura del Proyecto

```
OS_Round_Robin/
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

* Implementación del algoritmo Round Robin
* Gestión de procesos y cálculo de métricas

### Frontend (Vista)

* Interfaz desarrollada en **Tkinter**
* Entrada de procesos y parámetros
* Visualización de resultados

### Conexión (Presenter)

* Maneja la lógica entre la vista y el modelo
* Controla la simulación y actualización de la interfaz

---

## 🎓 Casos de Uso Educativos

* **Simulación Académica**: Ideal para entender el algoritmo Round Robin
* **Pruebas de Quantum**: Observar cómo afecta el rendimiento
* **Comparación con Otros Algoritmos**: Base para extender a FCFS o SJF

