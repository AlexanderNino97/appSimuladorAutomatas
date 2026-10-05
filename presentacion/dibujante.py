"""
presentacion/dibujante.py
=========================
Responsable de dibujar un NodoArbol sobre un Canvas de Tkinter en layout
HORIZONTAL (raíz a la izquierda, hojas a la derecha).

Diseño del algoritmo de layout
--------------------------------
Se usa un algoritmo de asignación de posiciones Y de abajo hacia arriba
(Reingold-Tilford simplificado para árboles N-arios):

1. Fase de medición: calcular cuántas 'unidades de ranura' ocupa cada subárbol
   (el número de hojas del subárbol, ya que cada hoja ocupa 1 ranura).
2. Fase de posicionamiento: asignar coordenadas (x, y) a cada nodo.
   - x aumenta hacia la derecha por cada nivel de profundidad.
   - y se centra en el rango de ranuras que ocupa el subárbol.
3. Fase de dibujo: renderizar nodos y aristas sobre el Canvas.

Esta capa solo importa tkinter (Canvas) y el dominio (NodoArbol).
No toca la capa lógica ni el servicio.
"""

import tkinter as tk
from typing import Dict, Tuple

from dominio.arbol import NodoArbol


# Constantes de estilo del dibujo
_ANCHO_PASO    = 110   # Separación horizontal entre niveles (px)
_ALTO_RANURA   = 40    # Altura de cada ranura de nodo (px)
_RADIO_NODO    = 18    # Radio del círculo del nodo (px)
_MARGEN_X      = 50    # Margen izquierdo inicial (px)
_MARGEN_Y      = 30    # Margen superior inicial (px)

# Paleta de colores — TEMA CLARO (fondo blanco)
_COLOR_NT           = "#1A6FC4"   # Azul corporativo para no terminales
_COLOR_T            = "#1E8449"   # Verde oscuro para terminales
_COLOR_TRUNCADO     = "#D35400"   # Naranja oscuro para nodos truncados ('…')
_COLOR_TEXTO        = "#FFFFFF"   # Blanco para el texto dentro del nodo
_COLOR_ARISTA       = "#999999"   # Gris medio para las líneas de conexión
_COLOR_FONDO        = "#FFFFFF"   # Fondo blanco del canvas
_COLOR_TEXTO_TRUNC  = "#FFFFFF"   # Texto en nodo truncado



class Dibujante:
    """
    Dibuja un NodoArbol en un Canvas de Tkinter con layout horizontal.

    Uso típico
    ----------
    dibujante = Dibujante(canvas)
    dibujante.dibujar(nodo_raiz, es_particular=True)
    """

    def __init__(self, canvas: tk.Canvas) -> None:
        """
        Parámetros
        ----------
        canvas : tk.Canvas — el canvas donde se dibujará el árbol.
        """
        self._canvas = canvas
        # Diccionario nodo_id -> (cx, cy) para dibujar aristas después
        self._posiciones: Dict[int, Tuple[float, float]] = {}

    def limpiar(self) -> None:
        """Borra todo el contenido del canvas antes de redibujar."""
        self._canvas.delete("all")
        self._posiciones.clear()

    def dibujar(self, raiz: NodoArbol, es_particular: bool = True) -> None:
        """
        Dibuja el árbol completo en el canvas.

        Parámetros
        ----------
        raiz          : NodoArbol — nodo raíz del árbol.
        es_particular : bool      — True para árbol particular (estilo primario),
                                    False para árbol general (estilo secundario).
        """
        self.limpiar()

        # Fase 1: calcular ranuras (cuántas hojas tiene cada subárbol)
        ranuras = _calcular_ranuras(raiz)

        # Fase 2: asignar posiciones (x, y) a cada nodo
        posiciones: Dict[int, Tuple[float, float]] = {}
        _asignar_posiciones(
            nodo=raiz,
            ranuras=ranuras,
            posiciones=posiciones,
            nivel=0,
            ranura_inicio=0,
        )

        # Calcular dimensiones totales para ajustar el scrollregion del canvas
        total_ranuras = ranuras[id(raiz)]
        max_nivel     = _profundidad_max(raiz)
        ancho_total   = _MARGEN_X * 2 + max_nivel * _ANCHO_PASO + _RADIO_NODO * 2
        alto_total    = _MARGEN_Y * 2 + total_ranuras * _ALTO_RANURA

        self._canvas.configure(scrollregion=(0, 0, ancho_total, alto_total))

        # Fase 3: dibujar aristas primero (quedan detrás de los nodos)
        self._dibujar_aristas(raiz, posiciones)

        # Fase 4: dibujar nodos encima
        self._dibujar_nodos(raiz, posiciones)

    # ------------------------------------------------------------------
    # Métodos privados de dibujo
    # ------------------------------------------------------------------

    def _dibujar_aristas(
        self,
        nodo: NodoArbol,
        posiciones: Dict[int, Tuple[float, float]],
    ) -> None:
        """Dibuja recursivamente las líneas de conexión entre padre e hijos."""
        cx, cy = posiciones[id(nodo)]
        for hijo in nodo.hijos:
            hx, hy = posiciones[id(hijo)]
            # Dibujar línea desde el borde derecho del padre al borde izquierdo del hijo
            self._canvas.create_line(
                cx + _RADIO_NODO, cy,
                hx - _RADIO_NODO, hy,
                fill=_COLOR_ARISTA,
                width=1,
                smooth=True,
            )
            self._dibujar_aristas(hijo, posiciones)

    def _dibujar_nodos(
        self,
        nodo: NodoArbol,
        posiciones: Dict[int, Tuple[float, float]],
    ) -> None:
        """Dibuja recursivamente los círculos y etiquetas de cada nodo."""
        cx, cy = posiciones[id(nodo)]

        # Elegir color según tipo de nodo
        if nodo.truncado:
            color_relleno = _COLOR_TRUNCADO
        elif len(nodo.hijos) == 0:
            # Nodo hoja: terminal
            color_relleno = _COLOR_T
        else:
            color_relleno = _COLOR_NT

        # Dibujar círculo
        self._canvas.create_oval(
            cx - _RADIO_NODO, cy - _RADIO_NODO,
            cx + _RADIO_NODO, cy + _RADIO_NODO,
            fill=color_relleno,
            outline="#FFFFFF",
            width=2,
        )

        # Etiqueta del nodo
        etiqueta = ("…" if nodo.truncado else nodo.simbolo)
        # Truncar etiqueta larga para que no se salga del círculo
        if len(etiqueta) > 4:
            etiqueta = etiqueta[:3] + "…"

        self._canvas.create_text(
            cx, cy,
            text=etiqueta,
            fill=_COLOR_TEXTO,
            font=("Helvetica", 9, "bold"),
        )

        # Recursión sobre hijos
        for hijo in nodo.hijos:
            self._dibujar_nodos(hijo, posiciones)


# =============================================================================
# Funciones de cálculo de layout (fuera de la clase, puramente funcionales)
# =============================================================================

def _calcular_ranuras(nodo: NodoArbol) -> Dict[int, int]:
    """
    Calcula el número de ranuras (slots verticales) que ocupa cada subárbol.
    Un nodo hoja ocupa 1 ranura; un nodo interno ocupa la suma de sus hijos.

    Retorna un diccionario {id(nodo): ranuras}.
    """
    resultado: Dict[int, int] = {}
    _calcular_ranuras_rec(nodo, resultado)
    return resultado


def _calcular_ranuras_rec(nodo: NodoArbol, resultado: Dict[int, int]) -> int:
    """Auxiliar recursiva de _calcular_ranuras."""
    if not nodo.hijos:
        resultado[id(nodo)] = 1
        return 1
    total = sum(_calcular_ranuras_rec(h, resultado) for h in nodo.hijos)
    resultado[id(nodo)] = total
    return total


def _asignar_posiciones(
    nodo: NodoArbol,
    ranuras: Dict[int, int],
    posiciones: Dict[int, Tuple[float, float]],
    nivel: int,
    ranura_inicio: int,
) -> None:
    """
    Asigna coordenadas (x, y) a cada nodo en el canvas.

    El eje X crece con el nivel (de izquierda a derecha).
    El eje Y se centra dentro del rango de ranuras asignado al nodo.

    Parámetros
    ----------
    nodo          : NodoArbol — nodo actual.
    ranuras       : dict      — mapa id->ranuras pre-calculado.
    posiciones    : dict      — mapa id->(x,y) que se está llenando.
    nivel         : int       — profundidad actual (0 = raíz).
    ranura_inicio : int       — primera ranura disponible para este subárbol.
    """
    mis_ranuras = ranuras[id(nodo)]

    # Centro vertical dentro del bloque de ranuras
    cy = _MARGEN_Y + (ranura_inicio + mis_ranuras / 2.0) * _ALTO_RANURA
    cx = _MARGEN_X + nivel * _ANCHO_PASO

    posiciones[id(nodo)] = (cx, cy)

    # Asignar posiciones a los hijos de forma consecutiva
    ranura_actual = ranura_inicio
    for hijo in nodo.hijos:
        _asignar_posiciones(
            nodo=hijo,
            ranuras=ranuras,
            posiciones=posiciones,
            nivel=nivel + 1,
            ranura_inicio=ranura_actual,
        )
        ranura_actual += ranuras[id(hijo)]


def _profundidad_max(nodo: NodoArbol) -> int:
    """Calcula la profundidad máxima (número de niveles) del árbol."""
    if not nodo.hijos:
        return 0
    return 1 + max(_profundidad_max(h) for h in nodo.hijos)
