"""Comprueba que la instalación quedó completa y funcionando.

    python verificar.py

Revisa las dependencias, la biblioteca de bloques y las plantillas, y genera
una resolución de prueba de punta a punta. Si todo sale bien, la app está
lista para usarse. Pensado para correr después de instalar y cada vez que algo
se sienta raro.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

OK = "  [ok]   "
MAL = "  [FALLA]"
AVISO = "  [aviso]"

fallas: list[str] = []
avisos: list[str] = []


def ok(mensaje: str) -> None:
    print(f"{OK} {mensaje}")


def falla(mensaje: str, remedio: str = "") -> None:
    print(f"{MAL} {mensaje}")
    if remedio:
        print(f"           → {remedio}")
    fallas.append(mensaje)


def aviso(mensaje: str, remedio: str = "") -> None:
    print(f"{AVISO} {mensaje}")
    if remedio:
        print(f"           → {remedio}")
    avisos.append(mensaje)


def revisar_python() -> None:
    version = sys.version_info
    texto = f"{version.major}.{version.minor}.{version.micro}"
    if version < (3, 10):
        falla(f"Python {texto}: la app necesita 3.10 o superior.",
              "Instale una versión nueva desde python.org.")
    else:
        ok(f"Python {texto}")


def revisar_dependencias() -> None:
    requeridas = {
        "streamlit": "la interfaz web",
        "docx": "la lectura y escritura de Word (paquete python-docx)",
        "pandas": "las tablas del formulario",
    }
    for modulo, para_que in requeridas.items():
        try:
            importado = __import__(modulo)
        except ImportError:
            falla(f"Falta '{modulo}' ({para_que}).",
                  "Ejecute: python -m pip install -r requirements.txt")
        else:
            version = getattr(importado, "__version__", "")
            ok(f"{modulo} {version}".strip())


def revisar_biblioteca() -> None:
    from curaduria.bloques import CATEGORIAS, Biblioteca

    try:
        libreria = Biblioteca()
    except ValueError as error:
        falla(f"La biblioteca de bloques no se pudo leer: {error}",
              "Revise biblioteca/bloques_usuario.json, o bórrelo para volver "
              "al catálogo original.")
        return

    if len(libreria) < 10:
        falla(f"La biblioteca solo tiene {len(libreria)} bloques.",
              "Debería traer el catálogo completo. ¿Falta "
              "biblioteca/bloques_base.json?")
        return
    ok(f"Biblioteca: {len(libreria)} bloques")

    sin_texto = [b.id for b in libreria.todos() if not b.texto.strip()]
    if sin_texto:
        falla(f"Bloques sin texto: {', '.join(sin_texto[:5])}")

    mal_categorizados = [b.id for b in libreria.todos()
                         if b.categoria not in CATEGORIAS]
    if mal_categorizados:
        aviso(f"Bloques con categoría desconocida: "
              f"{', '.join(mal_categorizados[:5])}")

    obligatorios = libreria.obligatorios("construccion")
    if len(obligatorios) < 5:
        aviso(f"Solo {len(obligatorios)} bloques obligatorios para "
              "construcción.")
    else:
        ok(f"Bloques obligatorios para construcción: {len(obligatorios)}")

    if libreria.archivo_usuario.exists():
        propios = [b for b in libreria.todos(incluir_inactivos=True)
                   if b.origen == "usuario"]
        ok(f"Bloques propios guardados: {len(propios)}")


def revisar_plantillas() -> None:
    from curaduria.auditoria import auditar
    from curaduria.plantilla import abrir

    carpeta = RAIZ / "plantillas"
    if not carpeta.exists():
        falla("No existe la carpeta plantillas/.",
              "Ejecute: python crear_plantilla_ejemplo.py")
        return

    viejas = list(carpeta.glob("*.doc"))
    if viejas:
        aviso(f"{len(viejas)} plantilla(s) en formato viejo (.doc): "
              f"{', '.join(p.name for p in viejas)}",
              "Ábralas en Word y guárdelas como .docx; la app no lee .doc.")

    plantillas = [p for p in carpeta.glob("*.docx")
                  if not p.name.startswith("~$")]
    if not plantillas:
        falla("No hay ninguna plantilla .docx en plantillas/.",
              "Ejecute: python crear_plantilla_ejemplo.py")
        return

    for ruta in plantillas:
        try:
            informe = auditar(abrir(ruta))
        except Exception as error:
            falla(f"{ruta.name} no se pudo abrir: {error}",
                  "Ábrala en Word y vuelva a guardarla como .docx.")
            continue
        detalle = f"{ruta.name}: {informe.resumen()}"
        if informe.etiquetas_desconocidas:
            aviso(detalle, "Etiquetas mal escritas: "
                  + ", ".join(f"{{{{{c}}}}}"
                              for c in informe.etiquetas_desconocidas[:5]))
        elif informe.blancos:
            aviso(detalle, f"{len(informe.blancos)} espacios se llenarían a "
                  f"mano. Vea: python revisar_plantilla.py "
                  f"plantillas/{ruta.name}")
        else:
            ok(detalle)


def revisar_generacion() -> None:
    """La prueba de verdad: generar una resolución completa."""
    from curaduria import armado
    from curaduria.bloques import Biblioteca
    from curaduria.catalogo import Solicitud
    from curaduria.gramatica import Titular
    from curaduria.plantilla import recorrer_parrafos
    from curaduria.profesionales import Profesional
    from curaduria.resolucion import Despacho, Inmueble, Resolucion

    resolucion = Resolucion(
        numero="PRUEBA-0001", fecha=date.today(), radicado="2600000",
        fecha_radicado=date.today(), consecutivo_expediente="1",
        solicitud=Solicitud("construccion", ["obra_nueva"],
                            ["vivienda_unifamiliar"]),
        despacho=Despacho(curador="NOMBRE DE PRUEBA",
                          sustanciador="SUSTANCIADORA DE PRUEBA"),
        titulares=[Titular("MARÍA DE PRUEBA", "F", "CC", "41000000"),
                   Titular("JUAN DE PRUEBA", "M", "CC", "79000000")],
        inmueble=Inmueble(direccion="CALLE DE PRUEBA 1",
                          matricula_inmobiliaria="350-000001",
                          ficha_catastral="01-01-0001-0001-000",
                          area_lote=100.0, area_construida=80.0, pisos=2),
        profesionales=[
            Profesional("proyectista", "ARQUITECTA DE PRUEBA", "F", "1", "A-1"),
            Profesional("constructor", "CONSTRUCTOR DE PRUEBA", "M", "2", "C-2"),
        ])

    errores = resolucion.errores()
    if errores:
        falla("La resolución de prueba no pasó las validaciones: "
              + "; ".join(errores))
        return
    ok("Validaciones de la resolución de prueba")

    etiquetas = resolucion.etiquetas()
    # La concordancia de género es la razón de ser de la app: se comprueba.
    if etiquetas["propietario"] != "propietarios":
        falla("La concordancia de número falló: dos titulares deberían dar "
              f"'propietarios', dio '{etiquetas['propietario']}'.")
    elif etiquetas["expediente"] == "":
        falla("El expediente no se armó.")
    else:
        ok(f"Concordancia y expediente: {etiquetas['expediente']}, "
           f"'{etiquetas['articulo']} {etiquetas['propietario']}'")

    libreria = Biblioteca()
    bloques = libreria.obligatorios("construccion")
    filas = armado.filas_hoja_datos(etiquetas, resolucion.secciones_hoja_datos())

    doc, faltantes = armado.armar_desde_bloques(bloques, etiquetas, filas)
    with tempfile.TemporaryDirectory() as carpeta:
        destino = Path(carpeta) / "prueba.docx"
        doc.save(destino)
        tamano = destino.stat().st_size
    texto = "\n".join(p.text for p in recorrer_parrafos(doc))
    if "MARÍA DE PRUEBA" not in texto:
        falla("El documento de prueba salió sin los datos de los titulares.")
    elif not doc.tables:
        falla("El documento de prueba salió sin la hoja de datos.")
    else:
        ok(f"Documento de prueba generado: {len(bloques)} bloques, "
           f"{tamano // 1024} KB")
    if faltantes:
        aviso(f"Etiquetas sin dato en la prueba: "
              f"{', '.join(sorted(faltantes)[:5])}",
              "Es normal: son datos que la prueba no llena.")


def main() -> int:
    print("\n  Comprobación del Automatizador de Resoluciones")
    print("  " + "-" * 50)
    revisar_python()
    revisar_dependencias()
    if fallas:
        print("\n  No puedo seguir hasta que estén las dependencias.\n")
        return 1
    revisar_biblioteca()
    revisar_plantillas()
    revisar_generacion()

    print("  " + "-" * 50)
    if fallas:
        print(f"\n  {len(fallas)} problema(s) por resolver. "
              "Vea el detalle arriba.\n")
        return 1
    if avisos:
        print(f"\n  Todo funciona. {len(avisos)} aviso(s) que conviene "
              "revisar, pero la app ya se puede usar.")
        print("  Arranque con: iniciar.bat  (o ./iniciar.sh)\n")
        return 0
    print("\n  Todo en orden. Arranque con: iniciar.bat  (o ./iniciar.sh)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
