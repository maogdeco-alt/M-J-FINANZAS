"""Revisión de una plantilla antes de usarla.

El modo de falla más costoso no es que la app se caiga: es que la plantilla
salga con un `XXXX` o una raya `____` que nadie notó, y la resolución se firme
así. Este módulo revisa una plantilla y reporta tres cosas:

    1. Qué etiquetas usa y si todas existen (una etiqueta mal escrita nunca se
       reemplaza y queda impresa tal cual).
    2. Qué espacios en blanco manuales quedan (XXXX, ____, "XX de ___ de 2026"),
       con una sugerencia de qué etiqueta poner en su lugar.
    3. Si tiene las anclas de sección para el armado por bloques.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from docx.document import Document as DocumentoDocx

from .armado import (ANCLA_CIERRE, ANCLA_CONSIDERANDOS, ANCLA_ENCABEZADO,
                     ANCLA_HOJA_DATOS, ANCLA_RESUELVE)
from .plantilla import ETIQUETA, recorrer_parrafos

ANCLAS = (ANCLA_ENCABEZADO, ANCLA_CONSIDERANDOS, ANCLA_RESUELVE, ANCLA_CIERRE,
          ANCLA_HOJA_DATOS)

# Espacios que se llenan a mano en las plantillas de Word.
PATRONES_BLANCO = (
    ("raya", re.compile(r"_{3,}")),
    ("equis", re.compile(r"\bX{2,}\b")),
    ("equis_pegada", re.compile(r"\d+X{2,}|X{2,}\d+")),
    ("anio_incompleto", re.compile(r"\b20[0-9]?X\b")),
)

# Qué etiqueta sugerir según lo que diga el texto justo antes del blanco.
SUGERENCIAS: tuple[tuple[str, str], ...] = (
    ("matrícula inmobiliaria", "matricula"),
    ("matricula inmobiliaria", "matricula"),
    ("m.i.", "matricula"),
    ("ficha catastral", "ficha_catastral"),
    ("cédula catastral", "ficha_catastral"),
    ("matrícula profesional", "proyectista_matricula"),
    ("cédula de ciudadanía", "documentos"),
    ("cedula de ciudadanía", "documentos"),
    ("resolución no", "resolucion_numero"),
    ("resolucion no", "resolucion_numero"),
    ("rad #", "expediente"),
    ("será el arquitecto", "constructor_nombre"),
    ("será la arquitecta", "constructor_nombre"),
    ("a los", "fecha_letras"),
    ("recibido no", "radicado"),
    ("oficio no", "viabilidad_oficio"),
    ("consecutivo no", "reparto_numero"),
    ("radicación no", "radicado"),
    ("radicado", "radicado"),
    ("expediente no", "expediente"),
    ("estrato", "estrato"),
    ("auto no", "auto_numero"),
    ("certificado idu", "idu_certificado"),
    ("factura no", "factura_numero"),
    ("escritura pública no", "escritura_numero"),
    ("anotación no", "folio_anotacion"),
    ("notaría", "escritura_notaria"),
    ("en un lote de terreno de", "area_lote"),
    ("edificación existente en", "area_demoler"),
    ("demolicion total de la edificación existente en", "area_demoler"),
    ("presentados por el arquitecto", "proyectista_nombre"),
    ("presentados por la arquitecta", "proyectista_nombre"),
    ("obras que trata la presente licencia será el arquitecto",
     "constructor_nombre"),
    ("constructor responsable de la obra el arquitecto", "constructor_nombre"),
    ("área de construcción total de", "area_construida"),
    ("área construida", "area_construida"),
    ("en la", "direccion"),
    ("predio ubicado en", "direccion"),
    ("del mes de", "fecha_mes"),
    ("de 20", "fecha_anio"),
    ("cubierta en", "cubierta"),
    ("destinada a", "destinacion"),
    ("pisos", "pisos_cifra"),
    ("señor", "nombres"),
    ("señora", "nombres"),
    ("vigencia de", "vigencia"),
)


# Lo que sigue al blanco a veces lo identifica mejor que lo que lo precede:
# en "en ____ (2) pisos", la palabra que manda está después.
SUGERENCIAS_DESPUES: tuple[tuple[str, str], ...] = (
    (r"^\s*\(\s*[\dX]+\s*\)\s*pisos", "pisos_cifra"),
    (r"^\s*pisos\b", "pisos_cifra"),
    (r"^\s*%", "indice_ocupacion_propuesto"),
    (r"^\s*m[²2]\b", "area_construida"),
)


@dataclass
class Hallazgo:
    """Un espacio en blanco encontrado en la plantilla."""

    tipo: str
    texto: str
    contexto: str
    sugerencia: str = ""
    parrafo: int = 0
    posicion: int = 0


@dataclass
class Informe:
    etiquetas: list[str] = field(default_factory=list)
    etiquetas_desconocidas: list[str] = field(default_factory=list)
    anclas: list[str] = field(default_factory=list)
    anclas_faltantes: list[str] = field(default_factory=list)
    blancos: list[Hallazgo] = field(default_factory=list)
    parrafos: int = 0

    @property
    def sirve(self) -> bool:
        """La plantilla se puede usar: no tiene etiquetas mal escritas."""
        return not self.etiquetas_desconocidas

    @property
    def lista(self) -> bool:
        """Además, no quedan espacios por convertir en etiquetas."""
        return self.sirve and not self.blancos

    def resumen(self) -> str:
        partes = [
            f"{self.parrafos} párrafos",
            f"{len(self.etiquetas)} etiquetas",
            f"{len(self.blancos)} espacios en blanco",
        ]
        if self.etiquetas_desconocidas:
            partes.append(
                f"{len(self.etiquetas_desconocidas)} etiquetas desconocidas")
        return " · ".join(partes)


def etiquetas_conocidas() -> set[str]:
    """Todas las etiquetas que la app sabe reemplazar, más las anclas."""
    from .bloques import Biblioteca
    from .catalogo import Solicitud
    from .gramatica import Titular
    from .profesionales import Profesional
    from .resolucion import Inmueble, Resolucion

    muestra = Resolucion(
        fecha=date.today(),
        solicitud=Solicitud("construccion", ["obra_nueva"]),
        titulares=[Titular("N N", "M", "CC", "1")],
        inmueble=Inmueble(),
        profesionales=[Profesional(rol, "N N") for rol in
                       ("proyectista", "estructural", "constructor")],
    )
    conocidas = set(muestra.etiquetas()) | set(ANCLAS)
    # Las etiquetas que usan los bloques también son válidas en la plantilla.
    try:
        for bloque in Biblioteca().todos(incluir_inactivos=True):
            conocidas.update(bloque.etiquetas())
    except (FileNotFoundError, ValueError):
        pass
    return conocidas


# "XX de ______ de 2026", "el XX de ____": el blanco es parte de una fecha.
RE_FECHA_ALREDEDOR = re.compile(
    r"^\s*(?:de\s*)?_*\s*(?:de\s+(?:20\d\d|_+|20\dX))", re.IGNORECASE)
RE_ANTES_DE_FECHA = re.compile(
    r"\b(?:el|del|calendad[ao]|fijad[ao]|desfijándose|fecha)\s+$",
    re.IGNORECASE)


def _sugerir(antes: str, despues: str = "") -> str:
    """Qué etiqueta poner en lugar del blanco, según el texto que lo rodea."""
    # Primero las fechas: son el blanco más repetido y el más fácil de errar.
    if RE_FECHA_ALREDEDOR.match(despues) or RE_ANTES_DE_FECHA.search(antes):
        return "fecha_larga"

    # Lo que sigue al blanco pesa más que el contexto anterior.
    for patron, etiqueta in SUGERENCIAS_DESPUES:
        if re.match(patron, despues, re.IGNORECASE):
            return etiqueta

    minusculas = antes.lower()
    mejor = ""
    posicion = -1
    for pista, etiqueta in SUGERENCIAS:
        encontrado = minusculas.rfind(pista)
        if encontrado > posicion:
            posicion, mejor = encontrado, etiqueta
    return mejor


def auditar(doc: DocumentoDocx,
            conocidas: set[str] | None = None) -> Informe:
    """Revisa la plantilla y devuelve el informe."""
    if conocidas is None:
        conocidas = etiquetas_conocidas()

    informe = Informe()
    vistas: dict[str, None] = {}

    for indice, parrafo in enumerate(recorrer_parrafos(doc), start=1):
        texto = parrafo.text
        if not texto.strip():
            continue
        informe.parrafos += 1

        for clave in ETIQUETA.findall(texto):
            vistas.setdefault(clave, None)

        # Los blancos se buscan sobre el texto sin etiquetas, para no marcar
        # una etiqueta que ya resuelve ese espacio.
        limpio = ETIQUETA.sub(" ", texto)
        encontrados: dict[tuple[int, int], Hallazgo] = {}
        for tipo, patron in PATRONES_BLANCO:
            for coincidencia in patron.finditer(limpio):
                tramo = coincidencia.span()
                if tramo in encontrados:
                    continue   # dos patrones sobre el mismo texto
                inicio = max(0, coincidencia.start() - 70)
                antes = limpio[inicio:coincidencia.start()]
                despues = limpio[coincidencia.end():coincidencia.end() + 24]
                encontrados[tramo] = Hallazgo(
                    tipo=tipo,
                    texto=coincidencia.group(0),
                    contexto=(antes + coincidencia.group(0)).strip(),
                    sugerencia=_sugerir(antes, despues),
                    parrafo=indice,
                    posicion=coincidencia.start(),
                )
        informe.blancos.extend(
            hallazgo for _, hallazgo in sorted(encontrados.items()))

    informe.etiquetas = list(vistas)
    informe.etiquetas_desconocidas = [c for c in informe.etiquetas
                                      if c not in conocidas]
    informe.anclas = [a for a in ANCLAS if a in informe.etiquetas]
    informe.anclas_faltantes = [a for a in ANCLAS if a not in informe.etiquetas]
    return informe


# --- Conversión automática -------------------------------------------------

# "XX de ______ de 2026" son tres blancos de una sola fecha: hay que tratarlos
# como uno, o la plantilla queda con tres etiquetas en lugar de una.
RE_UNION_FECHA = re.compile(r"^\s*(?:de|del)\s*$", re.IGNORECASE)
RE_CIERRE_FECHA = re.compile(r"^\s*(?:de|del)\s+(?:20\d\d|20\d?X)\b",
                             re.IGNORECASE)

# "73001-2-26-XXXX": el prefijo es parte del número, no texto fijo. Si se deja,
# el documento sale con el prefijo repetido dos veces.
RE_PREFIJO_ACTO = re.compile(r"(\d{3,5}-\d{1,2}-\d{2}-)$")
ETIQUETAS_CON_PREFIJO = {"resolucion_numero", "expediente", "auto_numero"}


@dataclass
class Cambio:
    """Un reemplazo hecho (o por hacer) en la plantilla."""

    parrafo: int
    original: str
    etiqueta: str
    contexto: str = ""

    @property
    def descripcion(self) -> str:
        return f"{self.original} → {{{{{self.etiqueta}}}}}"


def _agrupar_fechas(blancos: list[Hallazgo], texto: str
                    ) -> list[tuple[int, int, str]]:
    """Devuelve los tramos a reemplazar en un párrafo: (inicio, fin, etiqueta).

    Los blancos que forman una sola fecha se unen en un tramo, incluyendo el
    "de" que los separa y el año que los cierra.
    """
    tramos: list[tuple[int, int, str]] = []
    indice = 0
    while indice < len(blancos):
        actual = blancos[indice]
        inicio = actual.posicion
        fin = inicio + len(actual.texto)
        etiqueta = actual.sugerencia

        if etiqueta in ETIQUETAS_CON_PREFIJO:
            prefijo = RE_PREFIJO_ACTO.search(texto[:inicio])
            if prefijo:
                inicio = prefijo.start(1)

        if etiqueta == "fecha_larga":
            # Absorbe los blancos siguientes unidos por "de".
            siguiente = indice + 1
            while siguiente < len(blancos):
                candidato = blancos[siguiente]
                entre = texto[fin:candidato.posicion]
                if not RE_UNION_FECHA.match(entre):
                    break
                fin = candidato.posicion + len(candidato.texto)
                siguiente += 1
            # Y el año que cierra la fecha, si está escrito.
            cierre = RE_CIERRE_FECHA.match(texto[fin:])
            if cierre:
                fin += cierre.end()
            indice = siguiente
        else:
            indice += 1

        if etiqueta:
            tramos.append((inicio, fin, etiqueta))
    return tramos


def convertir(doc: DocumentoDocx, aplicar: bool = True,
              conocidas: set[str] | None = None
              ) -> tuple[list[Cambio], list[Hallazgo]]:
    """Cambia los espacios en blanco por la etiqueta sugerida.

    Devuelve (cambios hechos, blancos que quedaron sin convertir). Con
    `aplicar=False` solo calcula, sin tocar el documento: sirve para mostrar
    qué pasaría antes de decidir.

    Los blancos sin sugerencia no se tocan: inventar una etiqueta equivocada
    es peor que dejar la raya, porque la raya se ve y la etiqueta equivocada
    imprime un dato de otro campo.
    """
    from .plantilla import reemplazar_tramos

    if conocidas is None:
        conocidas = etiquetas_conocidas()

    cambios: list[Cambio] = []
    sin_convertir: list[Hallazgo] = []

    for indice, parrafo in enumerate(recorrer_parrafos(doc), start=1):
        texto = parrafo.text
        if not texto.strip():
            continue
        informe = auditar_parrafo(texto, indice, conocidas)
        if not informe:
            continue

        tramos = _agrupar_fechas(informe, texto)
        aplicables = [(ini, fin, f"{{{{{etiqueta}}}}}")
                      for ini, fin, etiqueta in tramos
                      if etiqueta in conocidas]

        # Pendiente es lo que ningún tramo alcanzó a cubrir.
        for hallazgo in informe:
            inicio = hallazgo.posicion
            fin_hallazgo = inicio + len(hallazgo.texto)
            cubierto = any(ini <= inicio and fin_hallazgo <= fin
                           for ini, fin, _ in aplicables)
            if not cubierto:
                sin_convertir.append(hallazgo)

        for ini, fin, etiqueta in tramos:
            if etiqueta in conocidas:
                cambios.append(Cambio(
                    parrafo=indice, original=texto[ini:fin],
                    etiqueta=etiqueta,
                    contexto=texto[max(0, ini - 50):fin].strip()))
        if aplicar and aplicables:
            reemplazar_tramos(parrafo, aplicables)

    return cambios, sin_convertir


# Un blanco de fecha solo puede estar hecho de rayas, equis, "de" y un año.
# Sirve para no tragarse el número de un oficio que viene antes de la fecha:
# en "Oficio No. 25000XXXX de ___________", el oficio no es parte de la fecha.
RE_FORMA_FECHA = re.compile(r"(?:_+|X{1,2}|20\d{2}|20\d?X{1,2})+")


def parece_fecha(texto: str) -> bool:
    nucleo = re.sub(r"(?i)\bde\b|\s+", "", texto)
    return bool(nucleo) and bool(RE_FORMA_FECHA.fullmatch(nucleo))


def convertir_texto(texto: str, conocidas: set[str] | None = None,
                    solo_fechas: bool = False) -> tuple[str, list[Cambio]]:
    """La misma conversión, sobre un texto suelto.

    Sirve para los bloques de la biblioteca, que se extrajeron textuales de la
    plantilla y por eso traen sus propios espacios en blanco.

    Con `solo_fechas` únicamente se convierten los blancos que son claramente
    una fecha. Los demás (un número de oficio, el número de otra resolución)
    se dejan como están: una etiqueta equivocada imprime el dato de otro campo
    y eso no se nota al revisar, mientras que una raya sí.
    """
    if conocidas is None:
        conocidas = etiquetas_conocidas()

    cambios: list[Cambio] = []
    lineas: list[str] = []
    for numero, linea in enumerate(texto.split("\n"), start=1):
        blancos = auditar_parrafo(linea, numero, conocidas)
        tramos = [(ini, fin, etiqueta)
                  for ini, fin, etiqueta in _agrupar_fechas(blancos, linea)
                  if etiqueta in conocidas
                  and (not solo_fechas
                       or (etiqueta == "fecha_larga"
                           and parece_fecha(linea[ini:fin])))]
        for ini, fin, etiqueta in sorted(tramos, reverse=True):
            cambios.append(Cambio(parrafo=numero, original=linea[ini:fin],
                                  etiqueta=etiqueta,
                                  contexto=linea[max(0, ini - 45):fin].strip()))
            linea = linea[:ini] + f"{{{{{etiqueta}}}}}" + linea[fin:]
        lineas.append(linea)
    return "\n".join(lineas), cambios


def auditar_parrafo(texto: str, indice: int = 1,
                    conocidas: set[str] | None = None) -> list[Hallazgo]:
    """Los blancos de un solo párrafo, en orden de aparición."""
    limpio = ETIQUETA.sub(" ", texto)
    encontrados: dict[tuple[int, int], Hallazgo] = {}
    for tipo, patron in PATRONES_BLANCO:
        for coincidencia in patron.finditer(limpio):
            tramo = coincidencia.span()
            if tramo in encontrados:
                continue
            inicio = max(0, coincidencia.start() - 70)
            antes = limpio[inicio:coincidencia.start()]
            despues = limpio[coincidencia.end():coincidencia.end() + 24]
            encontrados[tramo] = Hallazgo(
                tipo=tipo, texto=coincidencia.group(0),
                contexto=(antes + coincidencia.group(0)).strip(),
                sugerencia=_sugerir(antes, despues),
                parrafo=indice, posicion=coincidencia.start())
    return [hallazgo for _, hallazgo in sorted(encontrados.items())]
