# LO QUE DESTAPÓ LA AUDITORÍA DEL 29-09: las reglas imperativas no se volvían a mirar al entregar,
# y el aviso al guardar se lo llevaba por delante el siguiente mensaje. Esta prueba lo vigila.
import sys; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B, openpyxl, os
T="\t"
MALA=T.join(["11001000000046855268","F","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","CERRADO",
  "","","","CEDULA DE CIUDADANIA","1886999","ANA MARIA GOMEZ","ABC123"])
BUENA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","ANA MARIA GOMEZ","ABC123"])
BLOQUE="2026ER500\t01/09/2026\t03/09/2026\tANA MARIA GOMEZ\n2026ER501\t01/09/2026\t03/09/2026\tOTRA PERSONA"
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE); B.ir_a(pag,"2026ER500")
    B.pegar_tira(pag,MALA)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","ana@gmail.com")
    B.escribir(pag,"#cc_res","1368706"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(800); B.confirmar_nombre(pag)

    print("1) el aviso de regla rota queda FIJO, no se lo lleva otro mensaje")
    pag.wait_for_timeout(2500)
    caja=pag.locator("#avisoImperativas")
    ok(caja.is_visible(), "sigue visible pasados 2,5 s")
    t=caja.inner_text()
    ok("R09" in t and "R10" in t, "y nombra las dos reglas rotas → "+t.replace("\n"," | ")[:120])

    print("2) la revisión previa de la masiva SÍ las ve")
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1300)
    ok(pag.locator("#preflightDialog[open]").count()==1, "la revisión previa se abre")
    lista=pag.locator("#preflightLista").inner_text()
    ok("imperativamente DEVUELTO" in lista, "y dice que es imperativamente DEVUELTO")
    ok("GRAVE" in pag.locator("#preflightResumen").inner_text(), "marcado como GRAVE")
    pag.click("#preflightCancel"); pag.wait_for_timeout(400)

    print("3) al corregirlo, desaparece de los dos sitios")
    B.pegar_tira(pag,BUENA)
    pag.click("#cc_save"); pag.wait_for_timeout(800); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    ok(pag.locator("#avisoImperativas").is_hidden(), "el aviso fijo se va")
    with pag.expect_download(timeout=25000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1300)
        if pag.locator("#preflightDialog[open]").count():
            print("      (la revisión se abrió; resumen:", pag.locator("#preflightResumen").inner_text()[:90], ")")
            pag.click("#preflightProceed")
    ruta=os.path.join(os.path.dirname(__file__),"imperativas.xlsx"); dl.value.save_as(ruta)
    ws=openpyxl.load_workbook(ruta).active
    ok(ws.max_row==2 and ws.cell(row=2,column=11).value=="VIGENTE", "y la fila sale ya corregida")

    print("4) una fecha que no se entiende NO puede salir en blanco sin avisar")
    B.escribir(pag,"#cc_fechaRes","26-07-24x")
    pag.click("#cc_save"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1300)
    abierto = pag.locator("#preflightDialog[open]").count()==1
    txt = pag.locator("#preflightLista").inner_text() if abierto else ""
    ok(abierto and "no se entiende como fecha" in txt, "se avisa de la fecha ilegible → "+txt.replace("\n"," ")[:140])
    if abierto: pag.click("#preflightCancel")
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
