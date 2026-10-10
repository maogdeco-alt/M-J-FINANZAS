# 1c. "hay espacios al copiar y pegar informacion y en la masiva final aparecen espacios"
# 1b. "al generar la masiva NO hay cuadricula de fondo"
from playwright.sync_api import sync_playwright
import base as B, sys, os, openpyxl
T="\t"; NBSP=" "; ZWSP="​"
# Una tira con toda la basura invisible que deja copiar y pegar de verdad.
TIRA = T.join(["  11001000000046855268 ","D01 "," 19/04/2025","19/04/2025","No",
  "CAMARAS SALVAVIDAS"+NBSP,"VIGENTE","","","","CEDULA DE"+NBSP+"CIUDADANIA","  1886999  ",
  "JOSE"+ZWSP+"  PÉREZ   CASTAÑEDA ","ABC123 "])
BLOQUE = "2026ER200\t01/09/2026\t03/09/2026\tJOSE PEREZ CASTANEDA\n2026ER201\t01/09/2026\t03/09/2026\tSEGUNDA PERSONA"
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav,ctx,pag,errores=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    B.ir_a(pag,"2026ER200")
    B.pegar_tira(pag, TIRA)
    B.escribir(pag,"#cc_formato","T14")
    B.escribir(pag,"#cc_direccion","  persona"+NBSP+"@gmail.com  ")
    # el correo con un espacio adentro SÍ se avisa (no se corrige solo: cambiar un correo es cambiar un dato)

    B.escribir(pag,"#cc_res","1368706"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag)
    pag.click("#cc_saveNext"); pag.wait_for_timeout(600); B.confirmar_nombre(pag)
    av = " | ".join(B.avisos_alerta(pag))
    ok("ESPACIO adentro" in av, "avisa del espacio dentro del correo → "+av[:120])
    B.cerrar_alerta(pag)
    # ahora se corrige y se sigue
    B.ir_a(pag,"2026ER200")
    B.escribir(pag,"#cc_direccion","persona@gmail.com")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    # el segundo radicado se queda sin clasificar a propósito: no entra en la masiva

    with pag.expect_download(timeout=25000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(900)
        if pag.locator("#preflightDialog[open]").count():
            pag.click("#preflightProceed")
    ruta = os.path.join(os.path.dirname(__file__), "masiva.xlsx")
    dl.value.save_as(ruta)
    wb = openpyxl.load_workbook(ruta); ws = wb.active
    cab = [c.value for c in ws[1]]; fila=[c.value for c in ws[2]]
    print("      fila:", [repr(v) for v in fila])
    malos = [(cab[i], repr(v)) for i,v in enumerate(fila)
             if isinstance(v,str) and (v!=v.strip() or "  " in v or NBSP in v or ZWSP in v or "\n" in v)]
    ok(not malos, "ni una casilla con espacios de más o caracteres invisibles → " + str(malos))
    ok(fila[cab.index("REMITENTE_DESTINATARIO")]=="JOSE PÉREZ CASTAÑEDA", "el nombre queda limpio → "+repr(fila[cab.index("REMITENTE_DESTINATARIO")]))
    ok(fila[cab.index("TIPO DE DOCUMENTO")]=="CEDULA DE CIUDADANIA", "el tipo de documento queda limpio → "+repr(fila[cab.index("TIPO DE DOCUMENTO")]))
    ok(fila[cab.index("NUMERO DE DOCUMENTO")]=="1886999", "el documento queda limpio")
    b=ws["A2"].border
    ok(all(x and x.style for x in (b.left,b.right,b.top,b.bottom)), "la masiva sale CON cuadrícula")
    ok(ws["A1"].font.bold and ws.freeze_panes=="A2", "con la fila de títulos en negrita y congelada")
    ok(len(cab)==27, "siguen siendo las 27 columnas de siempre → "+str(len(cab)))
    print("\nerrores de JavaScript:", errores or "ninguno")
    if errores: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
