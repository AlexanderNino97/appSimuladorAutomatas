"""
main.py
=======
Punto de entrada de la aplicación gráfica.
Instancia la ventana principal y arranca el loop de eventos de Tkinter.

Ejecución:
    python main.py
"""

import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path de Python,
# de modo que los paquetes (dominio, logica, aplicacion, presentacion)
# sean importables sin instalar.
_RAIZ = os.path.dirname(os.path.abspath(__file__))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from presentacion.ventana import VentanaPrincipal


def main() -> None:
    """Función principal: crea y ejecuta la ventana."""
    app = VentanaPrincipal()
    app.ejecutar()


if __name__ == "__main__":
    main()
