# EL CASO DE LA DEVOLUCIÓN (3-10-2026). Un radicado asignado, nunca clasificado: la masiva se
# generó sin él, la revisión previa NI SE ABRIÓ, y la semana se cerró sin decir una palabra.
# La entidad lo devolvió semanas después preguntando por qué no se le había respondido.
# Esta prueba vigila que eso no pueda volver a pasar en silencio.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B, openpyxl
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
OLVIDADO="202642110702441"
BLOQUE="\n".join([
 "202670000000001\t01/09/2026\t03/09/2026\tPERSONA 1",
 OLVIDADO+"\t23/08/2026\t03/09/2026\tJOSE AUGUSTO LOAIZA",  # misma semana que los otros: aquí no se prueba la mezcla (t25)
 "202670000000003\t01/09/2026\t03/09/2026\tPERSONA 3",
])
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    for rad in ("202670000000001","202670000000003"):
        B.ir_a(pag,rad); B.pegar_tira(pag,TIRA.replace("46855268","4685526"+rad[-1]))
        B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p@gmail.com")
        B.escribir(pag,"#cc_res","13687"+rad[-1]); B.escribir(pag,"#cc_fechaRes","26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(700)

    print("1) al generar la masiva NO sale, y lo dice (04-11-2026: antes avisaba y dejaba seguir)")
    ok("faltan 1" in pag.locator("#masivaListaBadge").inner_text().lower(),
       "el botón ya lo anunciaba antes de tocarlo")
    ok(B.descargar(pag) is None, "no se descarga una masiva a la que le falta un radicado")
    ok("Faltan 1" in B.toast(pag), "dice cuántos faltan → "+B.toast(pag)[:90])

    print("2) y lleva directo al radicado olvidado")
    ok(OLVIDADO in pag.locator("#cc_radicadoLabel").inner_text(),
       "abre el radicado olvidado en el Paso 2 → "+pag.locator("#cc_radicadoLabel").inner_text())
    ok("FORMATO" in " ".join(B.faltas(pag)), "con la caja diciendo que le falta la clasificación → "+" | ".join(B.faltas(pag))[:90])

    print("3) al cerrar la semana también avisa")
    pag.click("#cerrarSemanaNavBtn"); pag.wait_for_timeout(800)
    nota = pag.locator("#confirmKeptNote").inner_text()
    ok("PENDIENTES" in nota, "el aviso de cierre lo dice → "+nota[:120])
    ok("1" in nota, "con la cantidad")
    ok("confirm-grave" in (pag.locator("#confirmKeptNote").get_attribute("class") or ""), "y marcado como grave")
    pag.click("#confirmCancel"); pag.wait_for_timeout(400)
    ok(pag.locator("#queuePanel .queue-item").count()==3, "al cancelar no se borró nada")

    print("4) si se clasifica, las dos alarmas desaparecen")
    B.ir_a(pag,OLVIDADO); B.pegar_tira(pag,TIRA.replace("46855268","46855299"))
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","jose@gmail.com")
    B.escribir(pag,"#cc_res","1368799"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(600); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    ruta=B.descargar(pag, ruta=os.path.join(os.path.dirname(__file__),"masiva_sinclas.xlsx"), espera=20000)
    ok(ruta is not None, "ya no frena: la masiva sale")
    ws=openpyxl.load_workbook(ruta).active
    rads=[str(ws.cell(row=i,column=1).value) for i in range(2,ws.max_row+1)]
    ok(OLVIDADO in rads, "y ahora SÍ sale en la masiva → "+str(rads))
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
