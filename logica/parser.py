"""
logica/parser.py
================
Motor de análisis de pertenencia al lenguaje.
Determina si una palabra w ∈ L(G) usando BFS sobre formas sentenciales
con derivación por la izquierda (leftmost derivation).

Esta capa NO importa Tkinter ni realiza E/S de consola; recibe objetos
del dominio y retorna resultados puros.

Algoritmo
---------
Estado = forma sentencial actual (cadena de símbolos).
Cola BFS: cada elemento es (forma_sentencial, lista_de_pasos).
  - Se expande siempre el NO TERMINAL MÁS A LA IZQUIERDA (derivación canónica
    izquierda), garantizando que cada camino de la BFS corresponde a una
    derivación leftmost única.
  - Poda 1: si los terminales ya fijados al inicio no coinciden con el prefijo
    de la palabra objetivo, se descarta la rama.
  - Poda 2: si la longitud de la forma excede len(palabra) (asumiendo que no
    hay producciones λ), se descarta.
  - Poda 3: si la forma ya es completamente terminal y no es igual a w, descartada.
  - Límite de iteraciones para evitar bucles infinitos en gramáticas recursivas.
"""

from collections import deque
from typing import List, Optional, Tuple, Set

from dominio.gramatica import Gramatica


# Número máximo de estados explorados antes de declarar "no pertenece / límite"
_MAX_ITERACIONES = 50_000


def analizar_pertenencia(
    gramatica: Gramatica,
    palabra: str,
) -> Tuple[bool, Optional[List[str]]]:
    """
    Determina si 'palabra' ∈ L(G) y retorna la derivación por la izquierda.

    Parámetros
    ----------
    gramatica : Gramatica
        La gramática formal ya validada.
    palabra : str
        La cadena a verificar (puede ser cadena vacía para λ).

    Retorna
    -------
    (True,  lista_de_formas_sentenciales) si palabra ∈ L(G).
    (False, None)                         si palabra ∉ L(G) o se alcanzó el límite.

    La lista de formas sentenciales incluye S al inicio y la palabra al final,
    representando cada paso de la derivación.
    """
    # Caso especial: palabra vacía (cadena λ)
    # Solo pertenece si S ->* λ. Con nuestras restricciones simplificadas
    # (sin producciones λ explícitas), lo manejamos aquí.
    if palabra == "":
        # Verificar si el símbolo inicial puede derivar λ directamente
        for cuerpo in gramatica.producciones_de(gramatica.inicial):
            if cuerpo in ("", "λ", "ε"):
                return True, [gramatica.inicial, ""]
        return False, None

    objetivo = list(palabra)           # Palabra como lista de caracteres
    longitud_max = len(objetivo)       # Límite de longitud de forma sentencial

    # Cola BFS: (forma_sentencial_como_lista, pasos_de_derivación)
    # La forma sentencial se representa como lista de símbolos para facilitar
    # la búsqueda del primer no terminal.
    estado_inicial = [gramatica.inicial]
    cola: deque = deque()
    cola.append((estado_inicial, [_lista_a_cadena(estado_inicial)]))

    # Conjunto de formas visitadas para no repetir estados (evita ciclos)
    visitados: Set[str] = {gramatica.inicial}

    iteraciones = 0

    while cola:
        iteraciones += 1
        if iteraciones > _MAX_ITERACIONES:
            # Se alcanzó el límite de exploración; no se puede decidir
            break

        forma, pasos = cola.popleft()

        # Buscar el primer no terminal (derivación por la izquierda)
        indice_nt = _primer_no_terminal(forma, gramatica)

        if indice_nt == -1:
            # No hay no terminales: la forma es completamente terminal
            if forma == objetivo:
                return True, pasos
            # Si no coincide, este camino no lleva a la palabra
            continue

        nt = forma[indice_nt]  # No terminal a expandir

        # Obtener todas las alternativas de producción para este NT
        alternativas = gramatica.producciones_de(nt)

        for cuerpo in alternativas:
            # Construir la nueva forma sentencial reemplazando el NT
            # por los símbolos del cuerpo de la producción
            if cuerpo in ("", "λ", "ε"):
                # Producción vacía: eliminar el NT
                nueva_forma = forma[:indice_nt] + forma[indice_nt + 1:]
            else:
                # Descomponer el cuerpo en símbolos individuales
                simbolos_cuerpo = _descomponer_cuerpo(cuerpo, gramatica)
                nueva_forma = (
                    forma[:indice_nt] + simbolos_cuerpo + forma[indice_nt + 1:]
                )

            # --- Poda 1: prefijo terminal no coincide ---
            if not _prefijo_compatible(nueva_forma, objetivo, gramatica):
                continue

            # --- Poda 2: longitud excede la palabra objetivo ---
            if len(nueva_forma) > longitud_max:
                continue

            # Convertir a cadena para chequear visitados
            clave = _lista_a_cadena(nueva_forma)
            if clave in visitados:
                continue
            visitados.add(clave)

            nuevos_pasos = pasos + [clave]

            # Si la nueva forma es completamente terminal, comprobar match
            if _es_terminal_completa(nueva_forma, gramatica):
                if nueva_forma == objetivo:
                    return True, nuevos_pasos
                # Si no coincide, no encolar
                continue

            cola.append((nueva_forma, nuevos_pasos))

    return False, None


# ------------------------------------------------------------------
# Funciones auxiliares privadas
# ------------------------------------------------------------------

def _lista_a_cadena(forma: List[str]) -> str:
    """Convierte lista de símbolos a cadena concatenada para hashing."""
    return "".join(forma)


def _primer_no_terminal(forma: List[str], gramatica: Gramatica) -> int:
    """
    Retorna el índice del primer no terminal en 'forma'.
    Retorna -1 si no hay no terminales (forma completamente terminal).
    """
    for i, simbolo in enumerate(forma):
        if gramatica.es_no_terminal(simbolo):
            return i
    return -1


def _es_terminal_completa(forma: List[str], gramatica: Gramatica) -> bool:
    """Retorna True si todos los símbolos en 'forma' son terminales."""
    return all(gramatica.es_terminal(s) for s in forma)


def _descomponer_cuerpo(cuerpo: str, gramatica: Gramatica) -> List[str]:
    """
    Descompone el lado derecho de una producción en lista de símbolos.

    Estrategia: itera carácter a carácter. Si un carácter es un no terminal
    conocido, lo toma como símbolo individual. Los terminales también son
    caracteres individuales. Esto funciona para gramáticas donde los símbolos
    son de un solo carácter, que es el caso estándar en ejercicios académicos.

    Para gramáticas con símbolos de múltiples caracteres se necesitaría un
    lexer más sofisticado (fuera del alcance de este simulador simplificado).
    """
    resultado = []
    i = 0
    while i < len(cuerpo):
        # Intentar reconocer no terminales de múltiples caracteres
        # (por ejemplo, si el usuario define no terminales como "AB", "NT1")
        # Estrategia greedy: buscar el no terminal más largo que coincida
        encontrado = False
        for longitud in range(min(4, len(cuerpo) - i), 0, -1):
            candidato = cuerpo[i:i + longitud]
            if gramatica.es_no_terminal(candidato):
                resultado.append(candidato)
                i += longitud
                encontrado = True
                break
        if not encontrado:
            # Tomar como terminal el carácter actual
            resultado.append(cuerpo[i])
            i += 1
    return resultado


def _prefijo_compatible(
    forma: List[str],
    objetivo: List[str],
    gramatica: Gramatica,
) -> bool:
    """
    Verifica que los terminales fijados al inicio de 'forma' sean compatibles
    con el prefijo de 'objetivo'.

    Recorre la forma desde la izquierda mientras encuentre terminales.
    Si en algún punto el terminal no coincide con el carácter del objetivo,
    retorna False (poda). Retorna True en cuanto encuentre un no terminal
    (el resto aún puede expandirse) o se agoten los terminales.
    """
    for i, simbolo in enumerate(forma):
        if gramatica.es_no_terminal(simbolo):
            # A partir de aquí la forma puede cambiar; no podamos
            return True
        # Es terminal: comparar con el carácter correspondiente del objetivo
        if i >= len(objetivo):
            return False
        if simbolo != objetivo[i]:
            return False
    return True
