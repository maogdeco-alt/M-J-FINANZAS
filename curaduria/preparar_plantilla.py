"""Convierte una plantilla real de la curaduría en plantilla de la app.

    python preparar_plantilla.py plantillas/mi_plantilla.docx

Por defecto solo muestra qué haría. Para escribir el archivo nuevo:

    python preparar_plantilla.py plantillas/mi_plantilla.docx --aplicar

La plantilla original nunca se modifica: se escribe una copia con el sufijo
`_lista`. Lo que el convertidor no pueda resolver se queda como está y se
reporta, porque una etiqueta equivocada imprime el dato de otro campo sin que
se note, mientras que una raya se ve.
"""

from __future__ import annotations

import sys
from pathlib import Path

from curaduria.configuracion import Configuracion
from curaduria.plantilla import abrir
from curaduria.preparacion import preparar


def valores_del_despacho(config: Configuracion) -> dict[str, str]:
    """Los datos que estén escritos literalmente en la plantilla."""
    valores = {
        "curador": config.curador,
        "sustanciador": config.sustanciador,
        "municipio": config.municipio,
    }
    return {clave: valor for clave, valor in valores.items() if valor.strip()}


def main() -> int:
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    banderas = {a for a in sys.argv[1:] if a.startswith("--")}

    if not argumentos:
        print(__doc__)
        return 2

    ruta = Path(argumentos[0])
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

    aplicar = "--aplicar" in banderas
    con_anclas = "--sin-anclas" not in banderas
    config = Configuracion.cargar()

    doc = abrir(ruta)
    informe = preparar(doc, valores_del_despacho(config), con_anclas)

    print(f"\n  {ruta.name}")
    print(f"  {informe.resumen()}\n")

    if informe.etiquetas_puestas:
        print(f"  ESPACIOS CONVERTIDOS ({len(informe.etiquetas_puestas)})")
        for cambio in informe.etiquetas_puestas[:40]:
            print(f"    párrafo {cambio.parrafo:>3}: {cambio.descripcion}")
        if len(informe.etiquetas_puestas) > 40:
            print(f"    … y {len(informe.etiquetas_puestas) - 40} más.")
        print()

    if informe.literales:
        print(f"  DATOS DEL DESPACHO ({len(informe.literales)})")
        vistos = set()
        for cambio in informe.literales:
            if cambio.original in vistos:
                continue
            vistos.add(cambio.original)
            cuantos = sum(1 for c in informe.literales
                          if c.original == cambio.original)
            print(f"    {cambio.descripcion}  ({cuantos} veces)")
        print("    Ahora salen de la configuración: si cambia la curadora, se "
              "corrige en un solo lugar.\n")

    if informe.anclas:
        print("  ANCLAS PUESTAS")
        for ancla in informe.anclas:
            print(f"    {{{{{ancla}}}}}")
        print(f"    Se recortaron {informe.parrafos_recortados} párrafos del "
              "catálogo. No se pierden: están en la biblioteca de bloques, y "
              "ahí\n    se escogen según el caso en vez de borrarlos a mano "
              "cada vez.\n")
    elif informe.nota_estructura:
        print(f"  ESTRUCTURA\n    {informe.nota_estructura}\n")

    if informe.pendientes:
        print(f"  SE QUEDAN CON LA RAYA ({len(informe.pendientes)})")
        print("    No encontré una etiqueta segura. Se llenan en Word, o "
              "cámbielos usted:")
        for hallazgo in informe.pendientes[:20]:
            print(f"    párrafo {hallazgo.parrafo:>3}: "
                  f"…{hallazgo.contexto[-55:]}")
        print()

    if not aplicar:
        print("  Esto es solo una vista previa; no se escribió nada.")
        print(f"  Para generar el archivo:\n"
              f"      python preparar_plantilla.py {ruta} --aplicar\n")
        return 0

    destino = ruta.with_name(f"{ruta.stem}_lista{ruta.suffix}")
    doc.save(destino)
    print(f"  Plantilla lista: {destino}")
    print(f"  La original ({ruta.name}) no se tocó.")
    print("\n  Ábrala en Word y revísela antes de usarla. Luego elíjala en la "
          "barra lateral de la app.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
