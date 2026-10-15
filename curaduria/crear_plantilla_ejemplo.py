"""Genera una plantilla maestra de ejemplo con todas las etiquetas disponibles.

    python crear_plantilla_ejemplo.py [ruta_salida]

Sirve como punto de partida: ábrala en Word, pegue el texto real de sus
resoluciones y conserve las etiquetas {{...}} donde van los datos variables.
"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

DESTINO_POR_DEFECTO = Path(__file__).parent / "plantillas" / "plantilla_maestra.docx"


def _p(doc, texto, *, negrita=False, centrado=False, tamano=11):
    parrafo = doc.add_paragraph()
    if centrado:
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = parrafo.add_run(texto)
    run.bold = negrita
    run.font.size = Pt(tamano)
    return parrafo


def construir() -> Document:
    """Plantilla con anclas: el cuerpo variable lo aportan los bloques."""
    doc = Document()
    estilo = doc.styles["Normal"]
    estilo.font.name = "Arial"
    estilo.font.size = Pt(11)

    encabezado = doc.sections[0].header.paragraphs[0]
    encabezado.alignment = WD_ALIGN_PARAGRAPH.CENTER
    encabezado.add_run("{{curaduria}}").bold = True

    _p(doc, "RESOLUCIÓN No. {{resolucion_numero}}", negrita=True, centrado=True)
    _p(doc, "({{fecha_larga}})", centrado=True)
    _p(doc, "")
    _p(doc, "“Por medio de la cual se resuelve la solicitud de "
            "{{tramite_completo}} radicada bajo el número {{radicado}} del "
            "{{fecha_radicado_larga}}, Expediente No. {{expediente}}”",
       negrita=True, centrado=True)
    _p(doc, "")
    # Ancla: el preámbulo lo aporta el bloque "preambulo".
    _p(doc, "{{encabezado}}")
    _p(doc, "")
    _p(doc, "CONSIDERANDO", negrita=True, centrado=True)
    _p(doc, "")
    # Ancla: aquí se insertan los considerandos elegidos en la app.
    _p(doc, "{{considerandos}}")
    _p(doc, "")
    _p(doc, "En virtud de lo anterior, {{curador_tratamiento_largo}},")
    _p(doc, "")
    _p(doc, "RESUELVE", negrita=True, centrado=True)
    _p(doc, "")
    # Ancla: aquí se insertan los artículos y parágrafos elegidos.
    _p(doc, "{{resuelve}}")
    _p(doc, "")
    # Ancla: cierre, firma, notificación y pie de archivo.
    _p(doc, "{{cierre}}")

    pie = doc.sections[0].footer.paragraphs[0]
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pie.add_run("Resolución {{resolucion_numero}} del {{fecha}} — "
                "Expediente {{expediente}}")

    return doc


def main() -> None:
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else DESTINO_POR_DEFECTO
    destino.parent.mkdir(parents=True, exist_ok=True)
    construir().save(destino)
    print(f"Plantilla de ejemplo creada en: {destino}")


if __name__ == "__main__":
    main()
