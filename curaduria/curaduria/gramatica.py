"""Concordancia de género y número para resoluciones de curaduría.

El operador solo informa el sexo de cada titular; de ahí se derivan artículos,
tratamientos, sustantivos y participios. Si hay varios titulares, el número
pasa a plural y el género mixto se resuelve en masculino (regla del español).
"""

from __future__ import annotations

from dataclasses import dataclass, field

MASCULINO = "M"
FEMENINO = "F"
SINGULAR = "S"
PLURAL = "P"

# Sustantivos y participios de uso frecuente, en sus cuatro formas.
# Orden de cada tupla: (M sing, F sing, M plur, F plur)
_LEXICO: dict[str, tuple[str, str, str, str]] = {
    "articulo": ("el", "la", "los", "las"),
    "articulo_indefinido": ("un", "una", "unos", "unas"),
    "contraccion_de": ("del", "de la", "de los", "de las"),
    "contraccion_a": ("al", "a la", "a los", "a las"),
    "tratamiento": ("señor", "señora", "señores", "señoras"),
    "tratamiento_abrev": ("Sr.", "Sra.", "Sres.", "Sras."),
    "propietario": ("propietario", "propietaria", "propietarios", "propietarias"),
    "solicitante": ("solicitante", "solicitante", "solicitantes", "solicitantes"),
    "titular": ("titular", "titular", "titulares", "titulares"),
    "interesado": ("interesado", "interesada", "interesados", "interesadas"),
    "apoderado": ("apoderado", "apoderada", "apoderados", "apoderadas"),
    "poseedor": ("poseedor", "poseedora", "poseedores", "poseedoras"),
    "identificado": ("identificado", "identificada", "identificados", "identificadas"),
    "representado": ("representado", "representada", "representados", "representadas"),
    "notificado": ("notificado", "notificada", "notificados", "notificadas"),
    "obligado": ("obligado", "obligada", "obligados", "obligadas"),
    "citado": ("citado", "citada", "citados", "citadas"),
    "mismo": ("mismo", "misma", "mismos", "mismas"),
    "pronombre": ("él", "ella", "ellos", "ellas"),
    "quien": ("quien", "quien", "quienes", "quienes"),
    "este": ("este", "esta", "estos", "estas"),
    "aquel": ("aquel", "aquella", "aquellos", "aquellas"),
    "cuyo": ("cuyo", "cuya", "cuyos", "cuyas"),
    "posesivo": ("su", "su", "sus", "sus"),
    "verbo_ser": ("es", "es", "son", "son"),
    "verbo_obrar": ("obra", "obra", "obran", "obran"),
    "verbo_solicitar": ("solicita", "solicita", "solicitan", "solicitan"),
    "verbo_presentar": ("presenta", "presenta", "presentan", "presentan"),
    "verbo_deber": ("deberá", "deberá", "deberán", "deberán"),
    "verbo_podra": ("podrá", "podrá", "podrán", "podrán"),
    "verbo_acreditar": ("acredita", "acredita", "acreditan", "acreditan"),
    "verbo_actuar": ("actúa", "actúa", "actúan", "actúan"),
    "verbo_aportar": ("aportó", "aportó", "aportaron", "aportaron"),
    "documento": ("documento de identidad", "documento de identidad",
                  "documentos de identidad", "documentos de identidad"),
}


def _indice(genero: str, numero: str) -> int:
    base = 0 if numero == SINGULAR else 2
    return base + (0 if genero == MASCULINO else 1)


def flexionar(clave: str, genero: str, numero: str) -> str:
    """Devuelve la forma de `clave` concordada en género y número."""
    formas = _LEXICO.get(clave)
    if formas is None:
        raise KeyError(f"'{clave}' no está en el léxico de concordancia")
    return formas[_indice(genero, numero)]


def flexionar_libre(palabra: str, genero: str, numero: str) -> str:
    """Flexiona una palabra cualquiera terminada en -o/-a (p. ej. un oficio).

    Sirve para términos no previstos en el léxico: "arquitecto" -> "arquitecta".
    """
    raiz = palabra
    if genero == FEMENINO and palabra.endswith("o"):
        raiz = palabra[:-1] + "a"
    elif genero == MASCULINO and palabra.endswith("a") and palabra[-2:] != "ia":
        raiz = palabra[:-1] + "o"
    if numero == PLURAL:
        raiz = pluralizar(raiz)
    return raiz


def pluralizar(palabra: str) -> str:
    vocales = "aeiouáéíóú"
    if not palabra:
        return palabra
    ultima = palabra[-1].lower()
    if ultima in "aeio":
        return palabra + "s"
    if ultima in "uú":
        return palabra + "es"
    if ultima == "z":
        return palabra[:-1] + "ces"
    if ultima in vocales:
        return palabra + "s"
    return palabra + "es"


# --- Titulares -------------------------------------------------------------

TIPOS_DOCUMENTO = {
    "CC": "cédula de ciudadanía",
    "CE": "cédula de extranjería",
    "NIT": "Número de Identificación Tributaria",
    "PAS": "pasaporte",
    "PEP": "permiso especial de permanencia",
    "TI": "tarjeta de identidad",
}


@dataclass
class Titular:
    """Una persona (o persona jurídica) que figura en la resolución."""

    nombre: str
    genero: str = MASCULINO          # M / F
    tipo_documento: str = "CC"
    numero_documento: str = ""
    calidad: str = "propietario"     # propietario, apoderado, poseedor...

    @property
    def es_juridica(self) -> bool:
        return self.tipo_documento == "NIT"

    def documento_largo(self) -> str:
        tipo = TIPOS_DOCUMENTO.get(self.tipo_documento, self.tipo_documento)
        if not self.numero_documento:
            return tipo
        return f"{tipo} No. {self.numero_documento}"

    def documento_corto(self) -> str:
        if not self.numero_documento:
            return self.tipo_documento
        return f"{self.tipo_documento} {self.numero_documento}"

    def frase_identificacion(self) -> str:
        """"JUAN PÉREZ, identificado con cédula de ciudadanía No. 79.000.000"."""
        participio = flexionar("identificado", self.genero, SINGULAR)
        if self.es_juridica:
            participio = "identificada"
        return f"{self.nombre}, {participio} con {self.documento_largo()}"


def unir_con_y(partes: list[str]) -> str:
    """Une una lista en lenguaje natural: "A", "A y B", "A, B y C"."""
    partes = [p for p in partes if p]
    if not partes:
        return ""
    if len(partes) == 1:
        return partes[0]
    return ", ".join(partes[:-1]) + " y " + partes[-1]


@dataclass
class Concordancia:
    """Resuelve el género y número del grupo de titulares."""

    titulares: list[Titular] = field(default_factory=list)

    @property
    def numero(self) -> str:
        return SINGULAR if len(self.titulares) <= 1 else PLURAL

    @property
    def genero(self) -> str:
        if not self.titulares:
            return MASCULINO
        generos = {t.genero for t in self.titulares}
        if generos == {FEMENINO}:
            return FEMENINO
        return MASCULINO  # masculino genérico para grupo mixto o masculino

    @property
    def mixto(self) -> bool:
        return len({t.genero for t in self.titulares}) > 1

    def palabra(self, clave: str) -> str:
        return flexionar(clave, self.genero, self.numero)

    def etiquetas(self) -> dict[str, str]:
        """Todas las variantes gramaticales, listas para la plantilla."""
        datos = {clave: self.palabra(clave) for clave in _LEXICO}
        # Variantes capitalizadas, para inicios de párrafo: {{Articulo}}
        datos.update({clave.capitalize(): valor[0].upper() + valor[1:]
                      for clave, valor in datos.items() if valor})
        return datos

    # --- Textos compuestos ------------------------------------------------

    def nombres(self) -> str:
        return unir_con_y([t.nombre for t in self.titulares])

    def documentos(self) -> str:
        return unir_con_y([t.documento_corto() for t in self.titulares])

    def identificacion_completa(self) -> str:
        """Bloque "NOMBRE, identificado con ... y NOMBRE, identificada con ..."."""
        return unir_con_y([t.frase_identificacion() for t in self.titulares])

    def frase_calidad(self) -> str:
        """"en calidad de propietario" / "en calidad de propietarios"."""
        calidades = {t.calidad for t in self.titulares}
        clave = calidades.pop() if len(calidades) == 1 else "titular"
        if clave not in _LEXICO:
            return "en calidad de " + flexionar_libre(clave, self.genero, self.numero)
        return "en calidad de " + flexionar(clave, self.genero, self.numero)
