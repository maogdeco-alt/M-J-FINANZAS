"""Armado del documento de Word.

Dos caminos, que se pueden combinar:

1. Plantilla maestra con etiquetas: se rellena y listo (módulo `plantilla`).
2. Armado por bloques: se escoge del catálogo qué considerandos aplican y el
   documento se construye párrafo por párrafo. Si la plantilla trae la etiqueta
   {{considerandos}}, los bloques se insertan ahí conservando el formato del
   párrafo que la contenía.

Además produce la hoja de datos: el cuadro con la información general fija que
se diligencia antes de empezar a trabajar el archivo, para que el sustanciador
no tenga que ir a buscar cada dato en el expediente.
"""

from __future__ import annotations

import copy
from typing import Iterable, Mapping, Sequence

from docx import Document
from docx.document import Document as DocumentoDocx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph

from .bloques import Bloque
from .plantilla import ETIQUETA, recorrer_parrafos, rellenar

ANCLA_ENCABEZADO = "encabezado"
ANCLA_CONSIDERANDOS = "considerandos"
ANCLA_RESUELVE = "resuelve"
ANCLA_CIERRE = "cierre"
ANCLA_HOJA_DATOS = "hoja_datos"

# Si la plantilla no trae el ancla de una sección, sus bloques se suman a esta.
ANCLA_ALTERNATIVA = {
    ANCLA_ENCABEZADO: ANCLA_CONSIDERANDOS,
    ANCLA_CIERRE: ANCLA_RESUELVE,
}

SECCIONES = ("encabezado", "considerando", "resuelve", "cierre")
ANCLA_DE_SECCION = {
    "encabezado": ANCLA_ENCABEZADO,
    "considerando": ANCLA_CONSIDERANDOS,
    "resuelve": ANCLA_RESUELVE,
    "cierre": ANCLA_CIERRE,
}


def seccion_de(bloque: Bloque) -> str:
    """En qué parte del acto va el bloque: encabezado, considerando, resuelve
    o cierre. Todo lo que no sea una de las otras tres es un considerando."""
    if bloque.categoria == "encabezado":
        return "encabezado"
    if bloque.categoria == "resuelve":
        return "resuelve"
    if bloque.categoria == "cierre":
        return "cierre"
    return "considerando"


# --- Inserción de párrafos --------------------------------------------------

def _insertar_parrafo_despues(parrafo: Paragraph, texto: str) -> Paragraph:
    """Clona el párrafo (para heredar su formato) y le pone otro texto."""
    nuevo_xml = copy.deepcopy(parrafo._p)
    parrafo._p.addnext(nuevo_xml)
    nuevo = Paragraph(nuevo_xml, parrafo._parent)
    for run in list(nuevo.runs)[1:]:
        run._element.getparent().remove(run._element)
    if nuevo.runs:
        nuevo.runs[0].text = texto
    else:
        nuevo.add_run(texto)
    return nuevo


def _vaciar_parrafo(parrafo: Paragraph) -> None:
    for run in list(parrafo.runs):
        run._element.getparent().remove(run._element)


def _eliminar_parrafo(parrafo: Paragraph) -> None:
    parrafo._p.getparent().remove(parrafo._p)


def insertar_textos(doc: DocumentoDocx, ancla: str,
                    textos: Sequence[str]) -> bool:
    """Reemplaza el párrafo que contiene {{ancla}} por un párrafo por texto.

    Devuelve False si la plantilla no tiene esa etiqueta.
    """
    objetivo = None
    for parrafo in recorrer_parrafos(doc):
        if f"{{{{{ancla}}}}}" in parrafo.text.replace(" ", ""):
            objetivo = parrafo
            break
        if ancla in ETIQUETA.findall(parrafo.text):
            objetivo = parrafo
            break
    if objetivo is None:
        return False

    referencia = objetivo
    for texto in textos:
        referencia = _insertar_parrafo_despues(referencia, texto)
    _eliminar_parrafo(objetivo)
    return True


def agregar_textos_al_final(doc: DocumentoDocx, textos: Iterable[str],
                            justificado: bool = True) -> None:
    for texto in textos:
        parrafo = doc.add_paragraph(texto)
        if justificado:
            parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


# --- Hoja de datos (el cuadro) ---------------------------------------------

def filas_hoja_datos(datos: Mapping[str, str],
                     secciones: Sequence[tuple[str, Sequence[tuple[str, str]]]]
                     ) -> list[tuple[str, str, str]]:
    """Convierte la definición de secciones en filas (seccion, campo, valor)."""
    filas: list[tuple[str, str, str]] = []
    for titulo, campos in secciones:
        for etiqueta, clave in campos:
            valor = datos.get(clave, "")
            filas.append((titulo, etiqueta, "" if valor is None else str(valor)))
    return filas


def _poner_bordes(tabla) -> None:
    """Pone la rejilla sin depender del estilo "Table Grid".

    Una plantilla guardada desde el formato viejo de Word puede no traer ese
    estilo definido, y entonces asignarlo falla. Los bordes se escriben
    directamente para que el cuadro se vea igual en cualquier plantilla.
    """
    try:
        tabla.style = "Table Grid"
        return
    except KeyError:
        pass

    propiedades = tabla._tbl.tblPr
    bordes = propiedades.find(qn("w:tblBorders"))
    if bordes is None:
        bordes = propiedades.makeelement(qn("w:tblBorders"), {})
        propiedades.append(bordes)
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        borde = bordes.makeelement(qn(f"w:{lado}"), {
            qn("w:val"): "single", qn("w:sz"): "4",
            qn("w:space"): "0", qn("w:color"): "999999",
        })
        bordes.append(borde)


def _marcar_pendiente(celda, texto: str) -> None:
    """Las celdas sin dato quedan con una raya diligenciable, no vacías."""
    parrafo = celda.paragraphs[0]
    _vaciar_parrafo(parrafo)
    if texto.strip():
        parrafo.add_run(texto)
    else:
        run = parrafo.add_run("_" * 28)
        run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)


def construir_hoja_datos(doc: DocumentoDocx,
                         filas: Sequence[tuple[str, str, str]],
                         titulo: str = "HOJA DE DATOS DEL EXPEDIENTE",
                         subtitulo: str = "") -> None:
    """Escribe el cuadro de información general fija en el documento."""
    encabezado = doc.add_paragraph()
    encabezado.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = encabezado.add_run(titulo)
    run.bold = True
    run.font.size = Pt(12)

    if subtitulo:
        linea = doc.add_paragraph()
        linea.alignment = WD_ALIGN_PARAGRAPH.CENTER
        detalle = linea.add_run(subtitulo)
        detalle.italic = True
        detalle.font.size = Pt(9)

    tabla = doc.add_table(rows=0, cols=2)
    _poner_bordes(tabla)
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER

    seccion_actual = None
    for seccion, campo, valor in filas:
        if seccion != seccion_actual:
            seccion_actual = seccion
            fila = tabla.add_row()
            fila.cells[0].merge(fila.cells[1])
            celda = fila.cells[0]
            _vaciar_parrafo(celda.paragraphs[0])
            run = celda.paragraphs[0].add_run(seccion.upper())
            run.bold = True
            run.font.size = Pt(9)
        fila = tabla.add_row()
        celda_campo = fila.cells[0]
        _vaciar_parrafo(celda_campo.paragraphs[0])
        run = celda_campo.paragraphs[0].add_run(campo)
        run.bold = True
        run.font.size = Pt(9)
        _marcar_pendiente(fila.cells[1], valor)
        for parrafo in fila.cells[1].paragraphs:
            for run_valor in parrafo.runs:
                run_valor.font.size = Pt(9)


def _parrafo_ancla(doc: DocumentoDocx, ancla: str) -> Paragraph | None:
    for parrafo in recorrer_parrafos(doc):
        if ancla in ETIQUETA.findall(parrafo.text):
            return parrafo
    return None


def insertar_hoja_datos(doc: DocumentoDocx,
                        filas: Sequence[tuple[str, str, str]],
                        titulo: str = "HOJA DE DATOS DEL EXPEDIENTE",
                        subtitulo: str = "",
                        ancla: str = ANCLA_HOJA_DATOS) -> str:
    """Pone el cuadro en el documento y dice dónde quedó.

    Si la plantilla trae {{hoja_datos}}, el cuadro reemplaza esa etiqueta; si
    no, encabeza el documento seguido de un salto de página, para que el acto
    empiece en la hoja siguiente.
    """
    cuerpo = doc.element.body
    previos = list(cuerpo)

    construir_hoja_datos(doc, filas, titulo, subtitulo)
    objetivo = _parrafo_ancla(doc, ancla)

    if objetivo is None:
        salto = doc.add_paragraph()
        salto.add_run().add_break(WD_BREAK.PAGE)

    nuevos = [elemento for elemento in list(cuerpo)
              if not any(elemento is previo for previo in previos)]
    referencia = objetivo._p if objetivo is not None else (
        previos[0] if previos else None)
    if referencia is not None:
        for elemento in nuevos:
            referencia.addprevious(elemento)
    if objetivo is not None:
        _eliminar_parrafo(objetivo)
        return "ancla"
    return "inicio"


def documento_hoja_datos(filas: Sequence[tuple[str, str, str]],
                         titulo: str, subtitulo: str = "") -> DocumentoDocx:
    """Hoja de datos como documento independiente, para imprimir o adjuntar."""
    doc = Document()
    estilo = doc.styles["Normal"]
    estilo.font.name = "Arial"
    estilo.font.size = Pt(10)
    construir_hoja_datos(doc, filas, titulo, subtitulo)
    doc.add_paragraph()
    nota = doc.add_paragraph()
    run = nota.add_run(
        "Las casillas con raya están pendientes de diligenciar. "
        "Este cuadro no hace parte del acto administrativo."
    )
    run.italic = True
    run.font.size = Pt(8)
    return doc


# --- Armado completo --------------------------------------------------------

def armar_desde_bloques(bloques: Sequence[Bloque], datos: Mapping[str, str],
                        hoja_datos: Sequence[tuple[str, str, str]] | None = None,
                        titulo_hoja: str = "HOJA DE DATOS DEL EXPEDIENTE",
                        subtitulo_hoja: str = "") -> tuple[DocumentoDocx, set[str]]:
    """Construye la resolución completa a partir del catálogo de bloques."""
    doc = Document()
    estilo = doc.styles["Normal"]
    estilo.font.name = "Arial"
    estilo.font.size = Pt(11)

    if hoja_datos:
        construir_hoja_datos(doc, hoja_datos, titulo_hoja, subtitulo_hoja)
        doc.add_page_break()

    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run(f"RESOLUCIÓN No. {datos.get('resolucion_numero', '')}")
    run.bold = True
    subtitulo = doc.add_paragraph()
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitulo.add_run(f"({datos.get('fecha_larga', '')})")
    doc.add_paragraph()

    def _titulo_centrado(texto: str) -> None:
        doc.add_paragraph()
        parrafo = doc.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        parrafo.add_run(texto).bold = True
        doc.add_paragraph()

    faltantes: set[str] = set()
    puesto_considerando = False
    puesto_resuelve = False
    for bloque in bloques:
        seccion = seccion_de(bloque)
        if seccion == "considerando" and not puesto_considerando:
            _titulo_centrado("CONSIDERANDO")
            puesto_considerando = True
        elif seccion == "resuelve" and not puesto_resuelve:
            _titulo_centrado("RESUELVE")
            puesto_resuelve = True
        agregar_textos_al_final(doc, bloque.render(datos))
        doc.add_paragraph()
        faltantes.update(bloque.faltantes(datos))

    return doc, faltantes


def armar_sobre_plantilla(doc: DocumentoDocx, bloques: Sequence[Bloque],
                          datos: Mapping[str, str],
                          hoja_datos: Sequence[tuple[str, str, str]] | None = None,
                          titulo_hoja: str = "HOJA DE DATOS DEL EXPEDIENTE",
                          subtitulo_hoja: str = "") -> dict:
    """Rellena la plantilla e inyecta los bloques en el ancla de cada sección.

    La plantilla puede traer {{encabezado}}, {{considerandos}}, {{resuelve}} y
    {{cierre}}. Si le falta alguna, sus bloques se suman al ancla vecina
    ({{encabezado}} a los considerandos, {{cierre}} a la parte resolutiva) para
    que nada se pierda en silencio. El informe dice qué se usó.
    """
    por_seccion: dict[str, list[str]] = {s: [] for s in SECCIONES}
    faltantes_bloques: set[str] = set()
    conteo: dict[str, int] = {s: 0 for s in SECCIONES}

    for bloque in bloques:
        seccion = seccion_de(bloque)
        conteo[seccion] += 1
        faltantes_bloques.update(bloque.faltantes(datos))
        por_seccion[seccion].extend(bloque.render(datos))
        por_seccion[seccion].append("")

    anclas_presentes = {
        ancla: _parrafo_ancla(doc, ancla) is not None
        for ancla in (ANCLA_ENCABEZADO, ANCLA_CONSIDERANDOS, ANCLA_RESUELVE,
                      ANCLA_CIERRE)
    }

    # Las secciones sin ancla propia se acumulan en su ancla alternativa.
    textos_por_ancla: dict[str, list[str]] = {}
    desviadas: list[str] = []
    for seccion in SECCIONES:
        textos = por_seccion[seccion]
        if not textos:
            continue
        ancla = ANCLA_DE_SECCION[seccion]
        if not anclas_presentes.get(ancla):
            alternativa = ANCLA_ALTERNATIVA.get(ancla)
            if alternativa and anclas_presentes.get(alternativa):
                desviadas.append(seccion)
                ancla = alternativa
        destino = textos_por_ancla.setdefault(ancla, [])
        if ancla == ANCLA_CONSIDERANDOS and seccion == "encabezado":
            destino[:0] = textos      # el encabezado siempre va primero
        else:
            destino.extend(textos)

    usadas: dict[str, bool] = {}
    for ancla, textos in textos_por_ancla.items():
        usadas[ancla] = insertar_textos(doc, ancla, textos)

    ubicacion_hoja = ""
    if hoja_datos:
        ubicacion_hoja = insertar_hoja_datos(
            doc, hoja_datos, titulo_hoja, subtitulo_hoja)

    faltantes_plantilla = rellenar(doc, datos)

    return {
        "faltantes": faltantes_plantilla | faltantes_bloques,
        "ancla_encabezado": usadas.get(ANCLA_ENCABEZADO, False),
        "ancla_considerandos": usadas.get(ANCLA_CONSIDERANDOS, False),
        "ancla_resuelve": usadas.get(ANCLA_RESUELVE, False),
        "ancla_cierre": usadas.get(ANCLA_CIERRE, False),
        "anclas_faltantes": sorted(a for a, hay in anclas_presentes.items()
                                   if not hay),
        "secciones_desviadas": desviadas,
        "bloques_por_seccion": conteo,
        "bloques_considerandos": conteo["considerando"] + conteo["encabezado"],
        "bloques_resuelve": conteo["resuelve"] + conteo["cierre"],
        "hoja_datos": ubicacion_hoja,
    }
