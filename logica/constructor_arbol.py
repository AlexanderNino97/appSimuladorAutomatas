"""
logica/constructor_arbol.py
============================
Construye dos tipos de árboles de derivación a partir de los resultados del
motor de análisis:

1. Árbol PARTICULAR: representación del árbol de derivación de una palabra
   específica, construido a partir de la secuencia de formas sentenciales
   que produjo el parser (derivación leftmost).

2. Árbol GENERAL: exploración desde S de TODAS las alternativas de producción
   hasta una profundidad configurable, marcando con '…' los nodos que se
   cortan por límite de profundidad o por recursión detectada.

Esta capa solo importa el dominio; nunca importa Tkinter ni servicio.
"""

from typing import List, Optional, Set

from dominio.gramatica import Gramatica
from dominio.arbol import NodoArbol
from logica.parser import _descomponer_cuerpo   # reutilizamos la función privada


# =============================================================================
# 1. Árbol Particular
# =============================================================================

def construir_arbol_particular(
    gramatica: Gramatica,
    derivacion: List[str],
) -> Optional[NodoArbol]:
    """
    Convierte la secuencia de formas sentenciales producida por el parser
    en un NodoArbol que representa el árbol de derivación particular de la
    palabra encontrada.

    Algoritmo (simulación de derivación leftmost):
    -----------------------------------------------
    Partimos del árbol con un único nodo raíz (el símbolo inicial).
    Por cada paso de derivación, identificamos el primer no terminal en la
    forma actual, lo 'expandimos' añadiendo hijos al nodo correspondiente,
    y actualizamos la forma sentencial actual.

    Parámetros
    ----------
    gramatica  : Gramatica  — gramática validada.
    derivacion : List[str]  — lista de formas sentenciales (cadenas),
                              de la forma [S, α₁, α₂, …, palabra].

    Retorna
    -------
    Nodo raíz del árbol construido, o None si la derivación está vacía.
    """
    if not derivacion:
        return None

    # Construir el árbol raíz con el símbolo inicial
    raiz = NodoArbol(gramatica.inicial)

    if len(derivacion) <= 1:
        # Caso trivial: la derivación no avanzó
        return raiz

    # Lista de nodos hoja activos (en orden de aparición) que aún pueden
    # expandirse. Empezamos con la raíz como único nodo activo.
    hojas_activas: List[NodoArbol] = [raiz]

    # Procesamos cada par de pasos consecutivos (forma_i -> forma_i+1)
    for paso_idx in range(1, len(derivacion)):
        forma_anterior_str = derivacion[paso_idx - 1]
        forma_actual_str   = derivacion[paso_idx]

        forma_anterior = _descomponer_forma(forma_anterior_str, gramatica)
        forma_actual   = _descomponer_forma(forma_actual_str,   gramatica)

        # Detectar qué no terminal se expandió: es el primer NT en la forma anterior
        pos_nt = _primer_nt_en_lista(forma_anterior, gramatica)
        if pos_nt == -1:
            break   # No hay más no terminales; derivación completa

        nt_expandido = forma_anterior[pos_nt]

        # Los terminales antes del NT no cambian; la diferencia está
        # en la posición pos_nt: el NT se reemplaza por los símbolos de forma_actual
        # desde pos_nt hasta len(forma_actual) - (len(forma_anterior) - pos_nt - 1)
        longitud_sufijo = len(forma_anterior) - pos_nt - 1
        if longitud_sufijo > 0:
            cuerpo_expandido = forma_actual[pos_nt: len(forma_actual) - longitud_sufijo]
        else:
            cuerpo_expandido = forma_actual[pos_nt:]

        # Encontrar el nodo hoja que corresponde al NT expandido.
        # Buscamos entre las hojas activas el que tiene el símbolo NT correcto.
        nodo_a_expandir = _buscar_nodo_nt(hojas_activas, nt_expandido)
        if nodo_a_expandir is None:
            break

        # Crear nodos hijo y añadirlos al nodo expandido
        nuevas_hojas: List[NodoArbol] = []
        for simbolo in cuerpo_expandido:
            hijo = NodoArbol(simbolo)
            nodo_a_expandir.agregar_hijo(hijo)
            nuevas_hojas.append(hijo)

        # Actualizar hojas activas: reemplazar el nodo expandido por sus hijos
        idx = hojas_activas.index(nodo_a_expandir)
        hojas_activas = (
            hojas_activas[:idx] + nuevas_hojas + hojas_activas[idx + 1:]
        )

    return raiz


# =============================================================================
# 2. Árbol General
# =============================================================================

def construir_arbol_general(
    gramatica: Gramatica,
    profundidad_max: int = 3,
) -> NodoArbol:
    """
    Genera el árbol de derivación GENERAL de la gramática, partiendo del
    símbolo inicial S y expandiendo TODAS las alternativas de producción
    hasta 'profundidad_max' niveles.

    Nodos marcados como truncados ('…'):
    - Cuando se alcanza la profundidad máxima y el símbolo aún es un NT.
    - Cuando se detecta un símbolo NT que ya apareció en la ruta desde la raíz
      hasta el nodo actual (ciclo de recursión).

    Parámetros
    ----------
    gramatica       : Gramatica — gramática validada.
    profundidad_max : int       — profundidad máxima de expansión (por defecto 3).

    Retorna
    -------
    Nodo raíz del árbol general.
    """
    raiz = NodoArbol(gramatica.inicial)
    _expandir_nodo_general(
        nodo=raiz,
        gramatica=gramatica,
        profundidad_actual=0,
        profundidad_max=profundidad_max,
        ancestros=frozenset([gramatica.inicial]),
    )
    return raiz


def _expandir_nodo_general(
    nodo: NodoArbol,
    gramatica: Gramatica,
    profundidad_actual: int,
    profundidad_max: int,
    ancestros: frozenset,
) -> None:
    """
    Expande recursivamente el nodo en el árbol general.

    Parámetros
    ----------
    nodo             : NodoArbol — nodo a expandir.
    gramatica        : Gramatica — gramática de referencia.
    profundidad_actual: int      — profundidad actual en el árbol.
    profundidad_max  : int       — profundidad máxima permitida.
    ancestros        : frozenset — conjunto de NT ya en la ruta (para detectar ciclos).
    """
    simbolo = nodo.simbolo

    # Si es terminal, es hoja; no hay nada que expandir
    if gramatica.es_terminal(simbolo):
        return

    # Si no es NT conocido (símbolo desconocido o especial), tampoco expandir
    if not gramatica.es_no_terminal(simbolo):
        return

    # Obtener alternativas de producción
    alternativas = gramatica.producciones_de(simbolo)

    if not alternativas:
        # No tiene producciones: hoja sin expandir
        return

    # Por cada alternativa, crear un grupo de hijos
    for cuerpo in alternativas:
        simbolos_cuerpo = _descomponer_cuerpo(cuerpo, gramatica)

        for sim in simbolos_cuerpo:
            # Decidir si el hijo se trunca
            if profundidad_actual + 1 >= profundidad_max:
                if gramatica.es_no_terminal(sim):
                    # Límite de profundidad alcanzado: marcar como truncado
                    hijo = NodoArbol(sim, truncado=True)
                    nodo.agregar_hijo(hijo)
                else:
                    # Terminal: añadir normalmente aunque estemos en el límite
                    hijo = NodoArbol(sim)
                    nodo.agregar_hijo(hijo)
            elif sim in ancestros and gramatica.es_no_terminal(sim):
                # Ciclo detectado: el símbolo ya aparece como ancestro
                hijo = NodoArbol(sim, truncado=True)
                nodo.agregar_hijo(hijo)
            else:
                hijo = NodoArbol(sim)
                nodo.agregar_hijo(hijo)
                # Expandir recursivamente solo si es NT y no truncado
                if gramatica.es_no_terminal(sim):
                    _expandir_nodo_general(
                        nodo=hijo,
                        gramatica=gramatica,
                        profundidad_actual=profundidad_actual + 1,
                        profundidad_max=profundidad_max,
                        ancestros=ancestros | {sim},
                    )


# =============================================================================
# Funciones auxiliares internas
# =============================================================================

def _descomponer_forma(forma_str: str, gramatica: Gramatica) -> List[str]:
    """
    Descompone una forma sentencial (cadena) en lista de símbolos,
    reconociendo no terminales de múltiples caracteres con estrategia greedy.
    Reutiliza la misma lógica que el parser.
    """
    return _descomponer_cuerpo(forma_str, gramatica)


def _primer_nt_en_lista(forma: List[str], gramatica: Gramatica) -> int:
    """Retorna el índice del primer no terminal en la lista; -1 si no hay."""
    for i, s in enumerate(forma):
        if gramatica.es_no_terminal(s):
            return i
    return -1


def _buscar_nodo_nt(hojas: List[NodoArbol], simbolo: str) -> Optional[NodoArbol]:
    """
    Busca el primer nodo hoja cuyo símbolo coincida con 'simbolo'.
    Retorna None si no se encuentra.
    """
    for nodo in hojas:
        if nodo.simbolo == simbolo and nodo.es_hoja():
            return nodo
    return None
