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
