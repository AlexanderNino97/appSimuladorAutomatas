"""
dominio/gramatica.py
====================
Modelos puros de la gramática formal G = (ΣT, ΣNT, S, P).
Esta capa NO contiene lógica de algoritmo ni referencias a la GUI.
Solo define estructuras de datos y validaciones básicas de integridad.
"""

from dataclasses import dataclass, field
from typing import List, Set, Tuple


@dataclass
class Produccion:
    """
    Representa una producción gramatical de la forma  A -> α₁ | α₂ | …
    donde 'cabeza' es el no terminal del lado izquierdo y 'cuerpos' es la
    lista de alternativas (cada alternativa es una cadena de símbolos).

    Ejemplo:
        Produccion(cabeza='A', cuerpos=['aA', 'a'])
    """
    cabeza: str                        # No terminal izquierdo (un solo símbolo)
    cuerpos: List[str] = field(default_factory=list)   # Alternativas del lado derecho

    def __repr__(self) -> str:
        alternativas = " | ".join(self.cuerpos)
        return f"{self.cabeza} -> {alternativas}"


class GramaticaError(Exception):
    """
    Excepción específica del dominio para errores de definición de gramática.
    Se lanza cuando la gramática no cumple los requisitos mínimos o tiene
    símbolos inválidos.
    """
    pass


class Gramatica:
    """
    Representa la gramática formal G = (ΣT, ΣNT, S, P).

    Atributos
    ---------
    terminales   : conjunto de símbolos terminales (ΣT)
    no_terminales: conjunto de no terminales (ΣNT)
    inicial      : símbolo inicial S ∈ ΣNT
    producciones : lista de objetos Produccion

    Invariantes que valida __init__
    --------------------------------
    - |ΣT|  >= 2  (requisito mínimo académico)
    - |ΣNT| >= 3  (requisito mínimo académico)
    - |P|   >= 3  (requisito mínimo académico)
    - S ∈ ΣNT
    - Cada cabeza de producción ∈ ΣNT
    - Los terminales y no terminales no se solapan
    """

    def __init__(
        self,
        terminales: Set[str],
        no_terminales: Set[str],
        inicial: str,
        producciones: List[Produccion],
    ) -> None:
        # Guardamos copias inmutables para evitar mutaciones externas
        self.terminales: Set[str] = frozenset(terminales)
        self.no_terminales: Set[str] = frozenset(no_terminales)
        self.inicial: str = inicial
        self.producciones: List[Produccion] = list(producciones)

        # Validar antes de aceptar la gramática
        self._validar()

    # ------------------------------------------------------------------
    # Validación interna
    # ------------------------------------------------------------------

    def _validar(self) -> None:
        """
        Comprueba que la gramática cumpla los requisitos mínimos del enunciado.
        Lanza GramaticaError con un mensaje descriptivo si algo falla.
        """
        # Requisito 1: Mínimo 2 terminales
        if len(self.terminales) < 2:
            raise GramaticaError(
                f"Se requieren al menos 2 terminales; se recibieron {len(self.terminales)}."
            )

        # Requisito 2: Mínimo 3 no terminales
        if len(self.no_terminales) < 3:
            raise GramaticaError(
                f"Se requieren al menos 3 no terminales; se recibieron {len(self.no_terminales)}."
            )

        # Requisito 3: Mínimo 3 producciones (contamos alternativas totales)
        total_alternativas = sum(len(p.cuerpos) for p in self.producciones)
        if total_alternativas < 3:
            raise GramaticaError(
                f"Se requieren al menos 3 alternativas de producción; "
                f"se recibieron {total_alternativas}."
            )

        # El símbolo inicial debe ser un no terminal
        if self.inicial not in self.no_terminales:
            raise GramaticaError(
                f"El símbolo inicial '{self.inicial}' no pertenece a ΣNT."
            )

        # Las cabezas de producción deben ser no terminales conocidos
        for prod in self.producciones:
            if prod.cabeza not in self.no_terminales:
                raise GramaticaError(
                    f"La cabeza '{prod.cabeza}' de la producción no es un no terminal."
                )

        # Los conjuntos de terminales y no terminales no deben solaparse
        solapamiento = self.terminales & self.no_terminales
        if solapamiento:
            raise GramaticaError(
                f"Los símbolos {solapamiento} aparecen en ΣT y en ΣNT a la vez."
            )

    # ------------------------------------------------------------------
    # Consultas de utilidad para las capas superiores
    # ------------------------------------------------------------------

    def producciones_de(self, cabeza: str) -> List[str]:
        """
        Devuelve la lista de cuerpos (alternativas) para el no terminal 'cabeza'.
        Si no existe producción para 'cabeza', retorna lista vacía.
        """
        for prod in self.producciones:
            if prod.cabeza == cabeza:
                return list(prod.cuerpos)
        return []

    def es_terminal(self, simbolo: str) -> bool:
        """Indica si 'simbolo' es un terminal de la gramática."""
        return simbolo in self.terminales

    def es_no_terminal(self, simbolo: str) -> bool:
        """Indica si 'simbolo' es un no terminal de la gramática."""
        return simbolo in self.no_terminales

    def todos_los_cuerpos(self) -> List[Tuple[str, str]]:
        """
        Retorna lista plana de (cabeza, cuerpo) para cada alternativa.
        Útil en el motor de análisis para iterar sobre todas las reglas.
        """
        resultado: List[Tuple[str, str]] = []
        for prod in self.producciones:
            for cuerpo in prod.cuerpos:
                resultado.append((prod.cabeza, cuerpo))
        return resultado

    def __repr__(self) -> str:
        prods_str = "; ".join(str(p) for p in self.producciones)
        return (
            f"Gramatica(ΣT={set(self.terminales)}, "
            f"ΣNT={set(self.no_terminales)}, "
            f"S='{self.inicial}', "
            f"P=[{prods_str}])"
        )
