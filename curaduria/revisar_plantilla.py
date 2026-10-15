"""Revisa una plantilla de Word antes de usarla con la app.

    python revisar_plantilla.py plantillas/mi_plantilla.docx

Reporta las etiquetas que usa, las que están mal escritas (nunca se
reemplazarían), las anclas de sección y los espacios en blanco que todavía se
llenan a mano, con una sugerencia de qué etiqueta poner en cada uno.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from curaduria.auditoria import auditar
from curaduria.plantilla import abrir


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    ruta = Path(sys.argv[1])
    if not ruta.exists():
        print(f"No encontré el archivo: {ruta}")
        return 2
    if ruta.suffix.lower() == ".doc":
        print(f"'{ruta.name}' está en el formato viejo de Word (.doc).")
        print("Ábralo en Word y use Archivo → Guardar como → "
              "Documento de Word (*.docx).")
        return 2
    if ruta.suffix.lower() != ".docx":
        print(f"Esperaba un archivo .docx, no '{ruta.suffix}'.")
        return 2

    informe = auditar(abrir(ruta))

    print(f"\n  {ruta.name}")
    print(f"  {informe.resumen()}\n")

    if informe.etiquetas_desconocidas:
        print("  ETIQUETAS QUE LA APP NO CONOCE (revise si están mal escritas;")
        print("  tal como están quedarían impresas en la resolución):")
        for clave in informe.etiquetas_desconocidas:
            print(f"    - {{{{{clave}}}}}")
        print()

    print("  ANCLAS DE SECCIÓN")
    for ancla in ("encabezado", "considerandos", "resuelve", "cierre",
                  "hoja_datos"):
        marca = "sí" if ancla in informe.anclas else "no"
        print(f"    {{{{{ancla}}}}}  {marca}")
    if not informe.anclas:
        print("    (sin anclas la plantilla solo rellena etiquetas: los "
              "bloques no se insertan)")
    print()

    if informe.blancos:
        por_tipo = Counter(h.tipo for h in informe.blancos)
        print(f"  ESPACIOS EN BLANCO: {len(informe.blancos)} "
              f"({dict(por_tipo)})")
        print("  Cámbielos por la etiqueta sugerida para que se llenen solos:\n")
        for hallazgo in informe.blancos[:60]:
            sugerido = (f"  ->  {{{{{hallazgo.sugerencia}}}}}"
                        if hallazgo.sugerencia else "  ->  (sin sugerencia)")
            contexto = hallazgo.contexto.replace("\n", " ")
            print(f"    párrafo {hallazgo.parrafo:>3}: …{contexto}{sugerido}")
        if len(informe.blancos) > 60:
            print(f"    … y {len(informe.blancos) - 60} más.")
        print()

    if informe.lista:
        print("  La plantilla está lista: sin etiquetas desconocidas y sin "
              "espacios por convertir.\n")
    elif informe.sirve:
        print("  La plantilla se puede usar, pero esos espacios en blanco "
              "habrá que llenarlos a mano.\n")
    else:
        print("  Corrija las etiquetas desconocidas antes de usarla.\n")

    return 0 if informe.sirve else 1


if __name__ == "__main__":
    sys.exit(main())
