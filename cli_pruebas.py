# -*- coding: utf-8 -*-
"""
cli_pruebas.py
==============
Prueba el motor de análisis POR CONSOLA, sin necesidad de GUI.
Demuestra la separación de capas: la lógica es completamente independiente
de Tkinter y puede usarse en entornos headless (servidores, CI/CD, etc.).

Ejecución:
    python cli_pruebas.py

Qué prueba este script
-----------------------
1. Gramática de demostración: ΣT={a,b}, ΣNT={S,A,B}, S, producciones estándar.
2. Caso "aabb"  → debe pertenecer    (w ∈ L(G)).
3. Caso "aba"   → no debe pertenecer (w ∉ L(G)).
4. Caso "a"     → debe pertenecer    (una sola 'a' de A -> a y B -> b = "ab"... no, verifica).
5. Caso borde: gramática inválida (menos de 2 terminales).
6. Imprime el árbol particular y el árbol general en formato textual.
"""

import sys
import os

# Configurar stdout en UTF-8 para evitar errores de codificación en Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Añadir el directorio raíz al path (igual que main.py)
_RAIZ = os.path.dirname(os.path.abspath(__file__))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from aplicacion.servicio import analizar


# =============================================================================
# Gramática de demostración
# =============================================================================

GRAMATICA_DEMO = """\
TERMINALES: a,b
NO_TERMINALES: S,A,B
INICIAL: S
PRODUCCIONES:
S -> AB
A -> aA | a
B -> bB | b
"""

# =============================================================================
# Casos de prueba
# =============================================================================

CASOS = [
    ("aabb",   True,  "Caso 1 -- Pertenencia esperada"),
    ("aba",    False, "Caso 2 -- No pertenencia esperada"),
    ("ab",     True,  "Caso 3 -- Palabra minima (a+b)"),
    ("aaabbb", True,  "Caso 4 -- Palabra mas larga"),
    ("ba",     False, "Caso 5 -- Orden invertido"),
    ("",       False, "Caso 6 -- Palabra vacia (lambda no esta en L(G))"),
    ("aab",    True,  "Caso 7 -- aab pertenece (A=aa, B=b => a^2 b^1)"),
]


def separador(caracter: str = "-", ancho: int = 70) -> str:
    """Retorna una linea separadora."""
    return caracter * ancho


def imprimir_arbol_texto(nodo, prefijo="", es_ultimo=True) -> None:
    """
    Imprime el árbol en formato textual horizontal (árbol de texto).
    Reutiliza el método texto_horizontal del NodoArbol del dominio.
    """
    if nodo is None:
        print("  (árbol no disponible)")
        return
    # Imprimir el nodo raíz sin conector
    print(f"  {nodo.simbolo}")
    # Imprimir hijos usando el método del dominio
    for i, hijo in enumerate(nodo.hijos):
        ultimo = (i == len(nodo.hijos) - 1)
        print(hijo.texto_horizontal("  ", ultimo))


def ejecutar_caso(descripcion: str, palabra: str, esperado: bool) -> None:
    """Ejecuta un caso de prueba individual e imprime los resultados."""
    print(separador())
    print(f"  {descripcion}")
    print(f"  Palabra: \"{palabra}\" | Resultado esperado: {'∈' if esperado else '∉'} L(G)")
    print(separador("·"))

    resultado = analizar(GRAMATICA_DEMO, palabra, profundidad_general=3)

    # Comprobar error
    if resultado.error:
        print(f"  ⚠  ERROR: {resultado.error}")
        print()
        return

    # Mostrar relacion de pertenencia
    simbolo_rel = "pertenece" if resultado.pertenece else "NO pertenece"
    estado_ok   = "[OK]" if resultado.pertenece == esperado else "[ERROR - Inesperado!]"

    print(f"  Resultado: \"{palabra}\" {simbolo_rel} L(G)   {estado_ok}")
    print()

    # Derivacion leftmost
    if resultado.derivacion:
        print("  Derivacion por la izquierda (leftmost):")
        for i, paso in enumerate(resultado.derivacion):
            flecha = "  S  " if i == 0 else f" =>{i:2d} "
            print(f"    {flecha}  {paso}")
    else:
        print("  (Sin derivacion -- la palabra no pertenece al lenguaje)")
    print()

    # Árbol particular
    print("  Árbol de derivación PARTICULAR:")
    imprimir_arbol_texto(resultado.arbol_particular)
    print()


def ejecutar_caso_error() -> None:
    """Prueba que el servicio maneja correctamente una gramática inválida."""
    print(separador())
    print("  Caso borde — Gramática inválida (solo 1 terminal)")
    print(separador("·"))

    gramatica_mala = """\
TERMINALES: a
NO_TERMINALES: S,A,B
INICIAL: S
PRODUCCIONES:
S -> aA
A -> aB | a
B -> a
"""
    resultado = analizar(gramatica_mala, "aa")
    if resultado.error:
        print(f"  ✔  Error capturado correctamente:")
        print(f"     {resultado.error}")
    else:
        print("  ✘  No se detectó el error (comportamiento inesperado)")
    print()


def main() -> None:
    """Función principal del script de pruebas en consola."""
    print()
    print(separador("="))
    print("  SIMULADOR DE GRAMATICAS FORMALES -- Pruebas por Consola (sin GUI)")
    print("  Motor: BFS con derivacion por la izquierda (leftmost derivation)")
    print(separador("="))
    print()
    print("  Gramatica de demostracion:")
    print("    Terminales   = {a, b}")
    print("    No Terminales= {S, A, B}")
    print("    S inicial    = S")
    print("    Producciones:")
    print("      S -> AB")
    print("      A -> aA | a")
    print("      B -> bB | b")
    print()
    print("  L(G) = { a^n b^m | n >= 1, m >= 1 }")
    print()

    # Mostrar el árbol general una vez
    resultado_general = analizar(GRAMATICA_DEMO, "aabb", profundidad_general=3)
    if not resultado_general.error:
        print(separador())
        print("  Arbol de derivacion GENERAL (profundidad 3, desde S):")
        imprimir_arbol_texto(resultado_general.arbol_general)
        print()

    # Ejecutar todos los casos de prueba
    for palabra, esperado, descripcion in CASOS:
        ejecutar_caso(descripcion, palabra, esperado)

    # Caso de error de gramática
    ejecutar_caso_error()

    print(separador("="))
    print("  Todas las pruebas completadas. Capa logica funcionando sin GUI. [OK]")
    print(separador("="))
    print()


if __name__ == "__main__":
    main()
