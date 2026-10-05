"""
aplicacion/servicio.py
======================
Capa de aplicación: único punto de entrada para la presentación.
Orquesta el parseo del texto de gramática, la creación del objeto Gramatica,
la invocación del motor de análisis y la construcción de ambos árboles.

La capa de presentación (ventana.py) SOLO llama a 'analizar()' y recibe
un ResultadoAnalisis; nunca toca directamente el parser ni el dominio.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from dominio.gramatica import Gramatica, Produccion, GramaticaError
from dominio.arbol import NodoArbol
from logica.parser import analizar_pertenencia
from logica.constructor_arbol import construir_arbol_particular, construir_arbol_general


@dataclass
class ResultadoAnalisis:
    """
    Contenedor de todos los resultados que la presentación necesita mostrar.

    Campos
    ------
    pertenece        : bool             — True si w ∈ L(G).
    derivacion       : List[str]        — Pasos de derivación leftmost.
    arbol_particular : Optional[NodoArbol] — Árbol de w; None si no pertenece.
    arbol_general    : Optional[NodoArbol] — Árbol general de G.
    error            : Optional[str]    — Mensaje de error si algo falló.
    palabra          : str              — La palabra analizada.
    """
    pertenece: bool = False
    derivacion: List[str] = field(default_factory=list)
    arbol_particular: Optional[NodoArbol] = None
    arbol_general: Optional[NodoArbol] = None
    error: Optional[str] = None
    palabra: str = ""


def analizar(
    gramatica_texto: str,
    palabra: str,
    profundidad_general: int = 3,
) -> ResultadoAnalisis:
    """
    Punto de entrada principal del servicio.

    Parámetros
    ----------
    gramatica_texto   : str  — Texto completo de la gramática (ver formato abajo).
    palabra           : str  — Palabra a verificar.
    profundidad_general: int — Profundidad del árbol general (por defecto 3).

    Formato esperado de gramatica_texto
    ------------------------------------
    Cada línea puede ser una de:
      - "TERMINALES: a,b,c"
      - "NO_TERMINALES: S,A,B"
      - "INICIAL: S"
      - "PRODUCCIONES:"   (lo que sigue hasta el final son producciones)
      - "A -> aA | b"     (producción en línea)
    Las líneas vacías y los comentarios (#) se ignoran.

    Retorna
    -------
    ResultadoAnalisis con todos los campos completados o con 'error' no nulo.
    """
    resultado = ResultadoAnalisis(palabra=palabra)

    try:
        # --- Paso 1: Parsear el texto de gramática ---
        gramatica = _parsear_gramatica(gramatica_texto)

        # --- Paso 2: Generar siempre el árbol general ---
        resultado.arbol_general = construir_arbol_general(
            gramatica, profundidad_max=profundidad_general
        )

        # --- Paso 3: Analizar pertenencia ---
        pertenece, derivacion = analizar_pertenencia(gramatica, palabra)
        resultado.pertenece = pertenece

        if pertenece and derivacion:
            resultado.derivacion = derivacion
            # --- Paso 4: Construir árbol particular ---
            resultado.arbol_particular = construir_arbol_particular(
                gramatica, derivacion
            )

    except GramaticaError as e:
        resultado.error = f"Error en la gramática: {e}"
    except Exception as e:
        resultado.error = f"Error inesperado: {e}"

    return resultado


# =============================================================================
# Parseador de texto de gramática
# =============================================================================

def _parsear_gramatica(texto: str) -> Gramatica:
    """
    Convierte el texto ingresado por el usuario en un objeto Gramatica.

    Formato aceptado (insensible a espacios extras):
    ------------------------------------------------
    TERMINALES: a,b
    NO_TERMINALES: S,A,B
    INICIAL: S
    PRODUCCIONES:
    S -> AB
    A -> aA | a
    B -> bB | b

    Las líneas de PRODUCCIONES pueden venir con o sin la cabecera
    "PRODUCCIONES:"; cualquier línea que contenga "->" se interpreta
    como una producción.

    Lanza GramaticaError si el texto está mal formado.
    """
    terminales: Optional[set] = None
    no_terminales: Optional[set] = None
    inicial: Optional[str] = None
    producciones_raw: List[tuple] = []   # (cabeza, [cuerpos])

    for linea in texto.splitlines():
        linea = linea.strip()

        # Ignorar vacías y comentarios
        if not linea or linea.startswith("#"):
            continue

        linea_upper = linea.upper()

        if linea_upper.startswith("TERMINALES:"):
            parte = linea.split(":", 1)[1].strip()
            terminales = _parsear_conjunto(parte)

        elif linea_upper.startswith("NO_TERMINALES:") or linea_upper.startswith("NOTERMINALES:"):
            parte = linea.split(":", 1)[1].strip()
            no_terminales = _parsear_conjunto(parte)

        elif linea_upper.startswith("INICIAL:"):
            inicial = linea.split(":", 1)[1].strip()

        elif linea_upper.startswith("PRODUCCIONES:"):
            # Cabecera de sección; las producciones vienen en las líneas siguientes
            continue

        elif "->" in linea:
            # Línea de producción
            partes = linea.split("->", 1)
            if len(partes) != 2:
                raise GramaticaError(f"Producción malformada: '{linea}'")
            cabeza = partes[0].strip()
            cuerpos_str = partes[1].strip()
            cuerpos = [c.strip() for c in cuerpos_str.split("|") if c.strip()]
            if not cuerpos:
                raise GramaticaError(f"La producción '{linea}' no tiene cuerpo válido.")
            producciones_raw.append((cabeza, cuerpos))

    # Verificar que se proporcionaron todos los campos obligatorios
    if terminales is None:
        raise GramaticaError("Falta la línea 'TERMINALES: ...'")
    if no_terminales is None:
        raise GramaticaError("Falta la línea 'NO_TERMINALES: ...'")
    if inicial is None:
        raise GramaticaError("Falta la línea 'INICIAL: ...'")
    if not producciones_raw:
        raise GramaticaError("No se encontraron producciones (usa el formato 'A -> cuerpo').")

    # Construir lista de Produccion
    producciones: List[Produccion] = []
    for cabeza, cuerpos in producciones_raw:
        producciones.append(Produccion(cabeza=cabeza, cuerpos=cuerpos))

    # Crear y retornar la gramática (se valida en __init__)
    return Gramatica(
        terminales=terminales,
        no_terminales=no_terminales,
        inicial=inicial,
        producciones=producciones,
    )


def _parsear_conjunto(texto: str) -> set:
    """
    Convierte una cadena separada por comas en un conjunto de símbolos.
    Ejemplo: "a, b, c" -> {'a', 'b', 'c'}
    """
    return {s.strip() for s in texto.split(",") if s.strip()}


# Tipo opcional para la anotación en _parsear_gramatica
from typing import Optional  # noqa: E402 (importación duplicada necesaria aquí)
