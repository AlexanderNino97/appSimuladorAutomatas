# Simulador de Gramáticas Formales

Este proyecto es un simulador académico que permite verificar si una palabra pertenece o no al lenguaje generado por una gramática libre de contexto, utilizando una interfaz gráfica moderna desarrollada en Python y Tkinter.

## Características

- **Validación de Gramática:** Exige un mínimo de 2 terminales, 3 no terminales y 3 producciones.
- **Árbol Particular:** Genera y dibuja el árbol de derivación específico para una palabra dada si pertenece al lenguaje.
- **Árbol General:** Expande el árbol de la gramática desde el símbolo inicial hasta una profundidad configurable, útil para visualizar la estructura del lenguaje.
- **Arquitectura en Capas:** El código está estrictamente dividido en Dominio, Lógica, Aplicación y Presentación.
- **Tema Claro:** Interfaz limpia con alto contraste para facilitar la visualización de los árboles.

## Requisitos

- Python 3.8 o superior.
- Tkinter (incluido por defecto en la mayoría de las instalaciones de Python).

No se requieren librerías externas (`pip install`). Todo se ejecuta con la librería estándar.

## Cómo ejecutar

Para iniciar la interfaz gráfica (GUI):

```bash
python main.py
```

Para correr las pruebas automáticas en consola (sin GUI):

```bash
python cli_pruebas.py
```

## Estructura del proyecto

- `dominio/`: Modelos de datos (Gramática, Árbol).
- `logica/`: Motor de análisis BFS y constructor de árboles.
- `aplicacion/`: Servicios que conectan lógica y presentación.
- `presentacion/`: Interfaz Tkinter y dibujante en Canvas.
- `documentacion_entrega.pdf`: Guion e instrucciones para el taller.
