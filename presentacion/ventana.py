"""
presentacion/ventana.py
========================
Interfaz gráfica principal del simulador de autómatas/gramáticas.
Construida con Tkinter (librería estándar de Python).

Esta capa SOLO se comunica con aplicacion/servicio.py.
Nunca importa logica.parser ni dominio directamente.

Layout de la ventana
--------------------
┌─────────────────────────────────────────────────────────────────┐
│  TÍTULO                                                         │
├──────────────────────────────────────────────────────────────── │
│  Panel izquierdo (entrada)    │  Panel derecho (resultados)     │
│  ─ Gramática (Text)           │  ─ Resultado de pertenencia     │
│  ─ Palabra (Entry)            │  ─ Derivación leftmost          │
│  ─ Profundidad árbol general  │  ─ Canvas árbol particular      │
│  ─ Botón Analizar             │  ─ Canvas árbol general         │
│  ─ Botones de ejemplo         │                                 │
└─────────────────────────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont

from aplicacion.servicio import analizar, ResultadoAnalisis
from presentacion.dibujante import Dibujante


# =============================================================================
# Gramática de ejemplo precargada (requisito del enunciado)
# =============================================================================

_GRAMATICA_EJEMPLO = """\
TERMINALES: a,b
NO_TERMINALES: S,A,B
INICIAL: S
PRODUCCIONES:
S -> AB
A -> aA | a
B -> bB | b
"""

_PALABRA_PERTENECE     = "aabb"
_PALABRA_NO_PERTENECE  = "aba"

# Colores del tema CLARO
_BG_DARK    = "#FFFFFF"   # Fondo principal (blanco)
_BG_PANEL   = "#F4F6F9"   # Fondo de paneles (gris muy suave)
_BG_ENTRADA = "#FFFFFF"   # Fondo de campos de texto (blanco)
_FG_BLANCO  = "#1A1A2E"   # Texto principal (casi negro)
_FG_GRIS    = "#555577"   # Texto secundario (gris medio)
_ACENTO     = "#1A6FC4"   # Azul corporativo
_VERDE      = "#1E8449"   # Verde oscuro legible
_ROJO       = "#C0392B"   # Rojo oscuro legible
_NARANJA    = "#D35400"   # Naranja oscuro legible
_AZUL       = "#1A6FC4"   # Azul (igual al acento)


class VentanaPrincipal:
    """
    Ventana principal de la aplicación.
    Se instancia y ejecuta desde main.py con:
        app = VentanaPrincipal()
        app.ejecutar()
    """

    def __init__(self) -> None:
        # Raíz de la aplicación Tkinter
        self._raiz = tk.Tk()
        self._raiz.title("Simulador de Gramáticas Formales — LF Taller 1")
        self._raiz.configure(bg=_BG_DARK)
        self._raiz.geometry("1280x780")
        self._raiz.minsize(900, 600)
        # Icono y cursor por defecto del sistema (tema claro)

        # Fuentes personalizadas
        self._fuente_titulo  = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self._fuente_normal  = tkfont.Font(family="Helvetica", size=10)
        self._fuente_mono    = tkfont.Font(family="Courier",   size=10)
        self._fuente_etiqueta= tkfont.Font(family="Helvetica", size=11, weight="bold")

        # Construir la interfaz
        self._construir_ui()
        self._precargar_ejemplo()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _construir_ui(self) -> None:
        """Crea todos los widgets de la ventana."""

        # === Barra de título superior ===
        self._construir_barra_titulo()

        # === Contenedor principal (PanedWindow horizontal) ===
        contenedor = tk.PanedWindow(
            self._raiz,
            orient=tk.HORIZONTAL,
            bg="#CCCCCC",   # Divisor gris claro visible en tema blanco
            sashwidth=5,
            sashrelief=tk.RAISED,
        )
        contenedor.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Panel izquierdo de entrada
        panel_izq = self._construir_panel_entrada(contenedor)
        contenedor.add(panel_izq, minsize=340)

        # Panel derecho de resultados
        panel_der = self._construir_panel_resultados(contenedor)
        contenedor.add(panel_der, minsize=560)

    def _construir_barra_titulo(self) -> None:
        """Barra superior con el título de la herramienta."""
        barra = tk.Frame(self._raiz, bg=_ACENTO, height=52)
        barra.pack(fill=tk.X)
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text="⚙  Simulador de Gramáticas Formales",
            font=self._fuente_titulo,
            bg=_ACENTO,
            fg="#FFFFFF",
        ).pack(side=tk.LEFT, padx=16, pady=10)

        tk.Label(
            barra,
            text="Lenguajes Formales · UPTC",
            font=self._fuente_normal,
            bg=_ACENTO,
            fg="#D0E8FF",
        ).pack(side=tk.RIGHT, padx=16, pady=10)

    def _construir_panel_entrada(self, padre: tk.Widget) -> tk.Frame:
        """Construye el panel izquierdo con los campos de entrada."""
        frame = tk.Frame(padre, bg=_BG_PANEL, padx=12, pady=12)

        # Encabezado del panel
        self._etiqueta_seccion(frame, "📝 Definición de Gramática").pack(
            anchor=tk.W, pady=(0, 8)
        )

        # Campo de texto para la gramática
        lbl_gram = tk.Label(
            frame,
            text="Gramática (formato: A -> α | β):",
            bg=_BG_PANEL,
            fg=_FG_GRIS,
            font=self._fuente_normal,
        )
        lbl_gram.pack(anchor=tk.W)

        marco_gram = tk.Frame(frame, bg=_ACENTO, padx=1, pady=1)
        marco_gram.pack(fill=tk.BOTH, pady=(2, 8))

        self._txt_gramatica = tk.Text(
            marco_gram,
            height=12,
            font=self._fuente_mono,
            bg=_BG_ENTRADA,
            fg="#1A1A2E",
            insertbackground="#1A1A2E",
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=8,
            pady=6,
        )
        scroll_gram = ttk.Scrollbar(marco_gram, orient=tk.VERTICAL, command=self._txt_gramatica.yview)
        self._txt_gramatica.configure(yscrollcommand=scroll_gram.set)
        self._txt_gramatica.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_gram.pack(side=tk.RIGHT, fill=tk.Y)

        # Campo de la palabra
        lbl_palabra = tk.Label(
            frame,
            text="Palabra a verificar:",
            bg=_BG_PANEL,
            fg=_FG_GRIS,
            font=self._fuente_normal,
        )
        lbl_palabra.pack(anchor=tk.W, pady=(4, 2))

        marco_pal = tk.Frame(frame, bg=_ACENTO, padx=1, pady=1)
        marco_pal.pack(fill=tk.X, pady=(0, 10))

        self._var_palabra = tk.StringVar()
        self._ent_palabra = tk.Entry(
            marco_pal,
            textvariable=self._var_palabra,
            font=self._fuente_mono,
            bg=_BG_ENTRADA,
            fg="#1A1A2E",
            insertbackground="#1A1A2E",
            relief=tk.SUNKEN,
        )
        self._ent_palabra.pack(fill=tk.X, ipady=6, padx=4, pady=4)

        # Control de profundidad del árbol general
        lbl_prof = tk.Label(
            frame,
            text="Profundidad árbol general:",
            bg=_BG_PANEL,
            fg=_FG_GRIS,
            font=self._fuente_normal,
        )
        lbl_prof.pack(anchor=tk.W, pady=(0, 2))

        self._var_profundidad = tk.IntVar(value=3)
        marco_prof = tk.Frame(frame, bg=_BG_PANEL)
        marco_prof.pack(fill=tk.X, pady=(0, 12))

        tk.Scale(
            marco_prof,
            from_=1,
            to=6,
            orient=tk.HORIZONTAL,
            variable=self._var_profundidad,
            bg=_BG_PANEL,
            fg="#1A1A2E",
            highlightthickness=0,
            troughcolor="#DDEEFF",
            activebackground=_ACENTO,
            length=200,
            resolution=1,
        ).pack(side=tk.LEFT)

        tk.Label(
            marco_prof,
            textvariable=self._var_profundidad,
            bg=_BG_PANEL,
            fg=_ACENTO,
            font=self._fuente_etiqueta,
        ).pack(side=tk.LEFT, padx=8)

        # Botón principal Analizar
        self._btn_analizar = tk.Button(
            frame,
            text="▶  ANALIZAR",
            command=self._on_analizar,
            bg=_ACENTO,
            fg="#FFFFFF",
            font=self._fuente_etiqueta,
            relief=tk.RAISED,
            cursor="hand2",
            pady=8,
            activebackground="#155A9E",
            activeforeground="#FFFFFF",
        )
        self._btn_analizar.pack(fill=tk.X, pady=(0, 8))
        self._btn_analizar.bind("<Enter>", lambda e: self._btn_analizar.config(bg="#155A9E"))
        self._btn_analizar.bind("<Leave>", lambda e: self._btn_analizar.config(bg=_ACENTO))

        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Botones de ejemplos predefinidos
        self._etiqueta_seccion(frame, "🔬 Ejemplos Precargados").pack(anchor=tk.W, pady=(0, 6))

        self._btn_ejemplo_si = tk.Button(
            frame,
            text=f"Cargar \"{_PALABRA_PERTENECE}\" (debe pertenecer)",
            command=lambda: self._cargar_ejemplo(_PALABRA_PERTENECE),
            bg=_VERDE,
            fg="#FFFFFF",
            font=self._fuente_normal,
            relief=tk.RAISED,
            cursor="hand2",
            pady=5,
            activebackground="#145A32",
            activeforeground="#FFFFFF",
        )
        self._btn_ejemplo_si.pack(fill=tk.X, pady=(0, 4))

        self._btn_ejemplo_no = tk.Button(
            frame,
            text=f"Cargar \"{_PALABRA_NO_PERTENECE}\" (no debe pertenecer)",
            command=lambda: self._cargar_ejemplo(_PALABRA_NO_PERTENECE),
            bg=_ROJO,
            fg="#FFFFFF",
            font=self._fuente_normal,
            relief=tk.RAISED,
            cursor="hand2",
            pady=5,
            activebackground="#922B21",
            activeforeground="#FFFFFF",
        )
        self._btn_ejemplo_no.pack(fill=tk.X, pady=(0, 4))

        tk.Button(
            frame,
            text="↺  Limpiar resultados",
            command=self._limpiar_resultados,
            bg="#E8EAF0",
            fg=_FG_GRIS,
            font=self._fuente_normal,
            relief=tk.RAISED,
            cursor="hand2",
            pady=4,
            activebackground="#D0D3DC",
            activeforeground="#1A1A2E",
        ).pack(fill=tk.X)

        return frame

    def _construir_panel_resultados(self, padre: tk.Widget) -> tk.Frame:
        """Construye el panel derecho con los resultados del análisis."""
        frame = tk.Frame(padre, bg=_BG_PANEL, padx=12, pady=12)

        # Encabezado
        self._etiqueta_seccion(frame, "📊 Resultados del Análisis").pack(
            anchor=tk.W, pady=(0, 8)
        )

        # --- Área de resultado de pertenencia ---
        self._lbl_resultado = tk.Label(
            frame,
            text="Ingrese una gramática y una palabra, luego presione ANALIZAR.",
            font=self._fuente_etiqueta,
            bg=_BG_PANEL,
            fg="#333355",
            wraplength=700,
            justify=tk.LEFT,
        )
        self._lbl_resultado.pack(anchor=tk.W, pady=(0, 4))

        # --- Área de derivación ---
        lbl_deriv = tk.Label(
            frame,
            text="Derivación por la izquierda:",
            bg=_BG_PANEL,
            fg=_FG_GRIS,
            font=self._fuente_normal,
        )
        lbl_deriv.pack(anchor=tk.W)

        marco_deriv = tk.Frame(frame, bg=_ACENTO, padx=1, pady=1)
        marco_deriv.pack(fill=tk.X, pady=(2, 10))

        self._txt_derivacion = tk.Text(
            marco_deriv,
            height=3,
            font=self._fuente_mono,
            bg="#F0F8FF",
            fg="#1A5276",
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=6,
            pady=4,
        )
        self._txt_derivacion.pack(fill=tk.X)

        # --- Notebooks de árboles ---
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Estilo del notebook (tema claro)
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "TNotebook",
            background=_BG_PANEL,
            borderwidth=1,
        )
        estilo.configure(
            "TNotebook.Tab",
            background="#E0E4EC",
            foreground="#333355",
            padding=[12, 6],
            font=("Helvetica", 10, "bold"),
        )
        estilo.map(
            "TNotebook.Tab",
            background=[("selected", _ACENTO)],
            foreground=[("selected", "#FFFFFF")],
        )

        # Tab: Árbol Particular
        tab_particular = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(tab_particular, text="🌳 Árbol Particular")
        self._canvas_particular, _ = self._crear_canvas_scrollable(tab_particular)

        # Tab: Árbol General
        tab_general = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(tab_general, text="🌐 Árbol General")
        self._canvas_general, _ = self._crear_canvas_scrollable(tab_general)

        # Instancias del dibujante para cada canvas
        self._dibujante_particular = Dibujante(self._canvas_particular)
        self._dibujante_general    = Dibujante(self._canvas_general)

        # Leyenda de colores
        self._construir_leyenda(frame)

        return frame

    def _crear_canvas_scrollable(
        self,
        padre: tk.Frame,
    ) -> tuple:
        """
        Crea un Canvas con scrollbars horizontal y vertical dentro de 'padre'.
        Retorna (canvas, frame_contenedor).
        """
        # Frame que contiene canvas + scrollbars
        contenedor = tk.Frame(padre, bg=_BG_DARK)
        contenedor.pack(fill=tk.BOTH, expand=True)

        # Scrollbar vertical
        scroll_v = ttk.Scrollbar(contenedor, orient=tk.VERTICAL)
        scroll_v.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollbar horizontal
        scroll_h = ttk.Scrollbar(contenedor, orient=tk.HORIZONTAL)
        scroll_h.pack(side=tk.BOTTOM, fill=tk.X)

        # Canvas
        canvas = tk.Canvas(
            contenedor,
            bg="#FFFFFF",
            relief=tk.FLAT,
            highlightthickness=0,
            yscrollcommand=scroll_v.set,
            xscrollcommand=scroll_h.set,
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_v.configure(command=canvas.yview)
        scroll_h.configure(command=canvas.xview)

        # Soporte de rueda del ratón para scroll
        canvas.bind(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )
        canvas.bind(
            "<Shift-MouseWheel>",
            lambda e: canvas.xview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        return canvas, contenedor

    def _construir_leyenda(self, padre: tk.Frame) -> None:
        """Pequeña leyenda de colores de los nodos."""
        frame = tk.Frame(padre, bg=_BG_PANEL)
        frame.pack(anchor=tk.W, pady=(4, 0))

        items = [
            (_AZUL,    "No terminal"),
            (_VERDE,   "Terminal"),
            (_NARANJA, "Truncado (…)"),
        ]
        for color, texto in items:
            tk.Canvas(frame, width=14, height=14, bg=color, highlightthickness=0).pack(
                side=tk.LEFT, padx=(0, 4)
            )
            tk.Label(frame, text=texto, bg=_BG_PANEL, fg="#333355", font=self._fuente_normal).pack(
                side=tk.LEFT, padx=(0, 14)
            )

    def _etiqueta_seccion(self, padre: tk.Widget, texto: str) -> tk.Label:
        """Crea una etiqueta de encabezado de sección."""
        return tk.Label(
            padre,
            text=texto,
            font=self._fuente_etiqueta,
            bg=_BG_PANEL if isinstance(padre, tk.Frame) else _BG_DARK,
            fg=_ACENTO,
        )

    # ------------------------------------------------------------------
    # Lógica de eventos
    # ------------------------------------------------------------------

    def _on_analizar(self) -> None:
        """Manejador del botón ANALIZAR: invoca el servicio y muestra resultados."""
        gramatica_texto = self._txt_gramatica.get("1.0", tk.END).strip()
        palabra         = self._var_palabra.get().strip()
        profundidad     = self._var_profundidad.get()

        if not gramatica_texto:
            messagebox.showwarning(
                "Entrada vacía",
                "Por favor, ingrese la definición de la gramática.",
                parent=self._raiz,
            )
            return

        # Cambiar cursor a espera durante el análisis
        self._raiz.configure(cursor="wait")
        self._raiz.update()

        try:
            resultado = analizar(gramatica_texto, palabra, profundidad_general=profundidad)
            self._mostrar_resultado(resultado)
        finally:
            self._raiz.configure(cursor="")

    def _mostrar_resultado(self, resultado: ResultadoAnalisis) -> None:
        """Actualiza todos los widgets de resultados con el ResultadoAnalisis recibido."""

        # --- Error crítico ---
        if resultado.error:
            self._lbl_resultado.config(
                text=f"⚠ {resultado.error}",
                fg=_NARANJA,
            )
            self._actualizar_derivacion("")
            self._dibujante_particular.limpiar()
            self._dibujante_general.limpiar()
            return

        # --- Resultado de pertenencia ---
        if resultado.pertenece:
            simbolo = "∈"
            color_r = _VERDE
            texto_r = f"✔  \"{resultado.palabra}\" {simbolo} L(G)   — la palabra PERTENECE al lenguaje."
        else:
            simbolo = "∉"
            color_r = _ROJO
            texto_r = f"✘  \"{resultado.palabra}\" {simbolo} L(G)   — la palabra NO pertenece al lenguaje."

        self._lbl_resultado.config(text=texto_r, fg=color_r)

        # --- Derivación leftmost ---
        if resultado.derivacion:
            derivacion_str = "  ⇒  ".join(resultado.derivacion)
        else:
            derivacion_str = "(no hay derivación — la palabra no pertenece al lenguaje)"

        self._actualizar_derivacion(derivacion_str)

        # --- Árbol particular ---
        self._dibujante_particular.limpiar()
        if resultado.arbol_particular:
            self._dibujante_particular.dibujar(resultado.arbol_particular, es_particular=True)
        else:
            # Mostrar mensaje sobre canvas vacío
            self._canvas_particular.create_text(
                200, 100,
                text="No hay árbol particular (la palabra no pertenece)",
                fill="#888899",
                font=self._fuente_normal,
            )

        # --- Árbol general ---
        self._dibujante_general.limpiar()
        if resultado.arbol_general:
            self._dibujante_general.dibujar(resultado.arbol_general, es_particular=False)

    def _actualizar_derivacion(self, texto: str) -> None:
        """Actualiza el widget de texto de derivación."""
        self._txt_derivacion.configure(state=tk.NORMAL)
        self._txt_derivacion.delete("1.0", tk.END)
        self._txt_derivacion.insert(tk.END, texto)
        self._txt_derivacion.configure(state=tk.DISABLED)

    def _precargar_ejemplo(self) -> None:
        """Carga la gramática de ejemplo en el campo de texto al inicio."""
        self._txt_gramatica.delete("1.0", tk.END)
        self._txt_gramatica.insert(tk.END, _GRAMATICA_EJEMPLO)
        self._var_palabra.set(_PALABRA_PERTENECE)

    def _cargar_ejemplo(self, palabra: str) -> None:
        """Carga la gramática de ejemplo y la palabra dada, luego analiza."""
        self._precargar_ejemplo()
        self._var_palabra.set(palabra)
        self._on_analizar()

    def _limpiar_resultados(self) -> None:
        """Limpia los campos de resultado sin borrar la gramática."""
        self._lbl_resultado.config(
            text="Ingrese una gramática y una palabra, luego presione ANALIZAR.",
            fg="#333355",
        )
        self._actualizar_derivacion("")
        self._dibujante_particular.limpiar()
        self._dibujante_general.limpiar()

    # ------------------------------------------------------------------
    # Ciclo principal
    # ------------------------------------------------------------------

    def ejecutar(self) -> None:
        """Inicia el loop principal de Tkinter."""
        self._raiz.mainloop()
