"""
dominio/arbol.py
================
Modelo puro de un nodo del árbol de derivación.
No contiene lógica de construcción ni de dibujo; solo la estructura de datos
que tanto la capa lógica (para construir) como la de presentación (para dibujar)
usarán sin acoplarse entre sí.
"""

from __future__ import annotations
from typing import List, Optional


class NodoArbol:
    """
    Nodo de un árbol de derivación N-ario.

    Atributos
    ---------
    simbolo  : str
        El símbolo gramatical representado (terminal, no terminal o '…').
    hijos    : List[NodoArbol]
        Lista ordenada de hijos (izquierda a derecha), vacía si es hoja.
    truncado : bool
        True cuando el nodo se cortó por límite de profundidad o ciclo,
        y se debe mostrar '…' en la visualización.

    Diseño
    ------
    Se eligió una clase mutable (en lugar de dataclass frozen) para poder
    construir el árbol de forma incremental desde la capa lógica sin
    crear objetos intermedios excesivos.
    """

    def __init__(
        self,
        simbolo: str,
        hijos: Optional[List["NodoArbol"]] = None,
        truncado: bool = False,
    ) -> None:
        self.simbolo: str = simbolo
        self.hijos: List["NodoArbol"] = hijos if hijos is not None else []
        self.truncado: bool = truncado

    # ------------------------------------------------------------------
    # Construcción de árbol desde secuencia de derivación
    # ------------------------------------------------------------------

    def agregar_hijo(self, hijo: "NodoArbol") -> None:
        """Añade un nodo hijo a la lista de hijos de este nodo."""
        self.hijos.append(hijo)

    def es_hoja(self) -> bool:
        """Un nodo es hoja si no tiene hijos (terminal o truncado)."""
        return len(self.hijos) == 0

    # ------------------------------------------------------------------
    # Representación textual (útil para depuración y CLI)
    # ------------------------------------------------------------------

    def texto_horizontal(self, prefijo: str = "", es_ultimo: bool = True) -> str:
        """
        Genera una representación textual del árbol en formato horizontal
        (árbol de texto tipo 'tree' de Linux) con el símbolo raíz a la
        izquierda y las hojas a la derecha.

        Parámetros
        ----------
        prefijo   : cadena de prefijo acumulada para la indentación.
        es_ultimo : indica si este nodo es el último hijo de su padre.
        """
        conector = "└── " if es_ultimo else "├── "
        etiqueta = self.simbolo + (" …" if self.truncado else "")
        lineas = [prefijo + conector + etiqueta]

        # Extensión del prefijo para los hijos
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
        for i, hijo in enumerate(self.hijos):
            ultimo = (i == len(self.hijos) - 1)
            lineas.append(hijo.texto_horizontal(nuevo_prefijo, ultimo))

        return "\n".join(lineas)

    def __repr__(self) -> str:
        return f"NodoArbol('{self.simbolo}', hijos={len(self.hijos)}, truncado={self.truncado})"
