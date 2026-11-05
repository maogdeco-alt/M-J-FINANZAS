# LO QUE DESTAPÓ LA AUDITORÍA DEL 29-09: las reglas imperativas no se volvían a mirar al entregar,
# y el aviso al guardar se lo llevaba por delante el siguiente mensaje. Esta prueba lo vigila.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B, openpyxl, os
T="\t"
MALA=T.join(["11001000000046855268","F","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","CERRADO",
  "","","","CEDULA DE CIUDADANIA","1886999","ANA MARIA GOMEZ","ABC123"])
BUENA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","ANA MARIA GOMEZ","ABC123"])
BLOQUE="202670000000500\t01/09/2026\t03/09/2026\tANA MARIA GOMEZ\n202670000000501\t01/09/2026\t03/09/2026\tOTRA PERSONA"
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE); B.ir_a(pag,"202670000000500")
    B.pegar_tira(pag,MALA)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","ana@gmail.com")
    B.escribir(pag,"#cc_res","1368706"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(800); B.confirmar_nombre(pag)

    print("1) el aviso de regla rota queda FIJO, no se lo lleva otro mensaje")
    pag.wait_for_timeout(2500)
    caja=pag.locator("#avisoImperativas")
    ok(caja.is_visible(), "sigue visible pasados 2,5 s")
    t=caja.inner_text()
    ok("Código de infracción F" in t and "Estado" in t and "DEVUELTO" in t,
       "y nombra las dos reglas rotas (R09 código F, R10 estado no VIGENTE) → "+t.replace("\n"," | ")[:160])

    print("2) la masiva NO sale con eso así (04-11-2026: antes la revisión previa avisaba y dejaba seguir)")
    ok(B.descargar(pag) is None, "no se descarga")
    ok("Faltan" in B.toast(pag), "y dice que faltan radicados por dejar LISTOS → "+B.toast(pag)[:90])

    print("3) al corregirlo, el radicado queda LISTO y la masiva sale")
    B.ir_a(pag,"202670000000500")
    B.pegar_tira(pag,BUENA)
    pag.click("#cc_save"); pag.wait_for_timeout(800); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    ok(B.esta_listo(pag), "la caja pasa a LISTO → "+pag.locator("#avisoImperativas").inner_text()[:80])
    B.ir_a(pag,"202670000000501"); B.escribir(pag,"#cc_formato","DEVUELTO")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag)
    ruta=B.descargar(pag, ruta=os.path.join(os.path.dirname(__file__),"imperativas.xlsx"), espera=20000)
    ok(ruta is not None, "se descarga sin ventanas en medio")
    if ruta:
        ws=openpyxl.load_workbook(ruta).active
        ok(ws.max_row==2 and ws.cell(row=2,column=11).value=="VIGENTE", "y la fila sale ya corregida")

    print("4) una fecha que no se entiende NO puede salir en blanco")
    B.ir_a(pag,"202670000000500")
    B.escribir(pag,"#cc_fechaRes","26-07-24x")
    pag.click("#cc_save"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    txt=" | ".join(B.faltas(pag))
    ok("fecha" in txt.lower(), "el radicado vuelve a PENDIENTE y dice que la fecha no sirve → "+txt[:160])
    ok(B.descargar(pag) is None, "y la masiva no sale")
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
