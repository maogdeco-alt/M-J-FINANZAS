# "NECESITO LOS RADICADOS QUE TRABAJÉ DESDE EL 28 DE SEPTIEMBRE HASTA AHORA, NO LOS ANTERIORES,
#  NO LOS VIEJOS, NO REPETIR LOS RADICADOS" (5-10-2026).
#
# Antes había una salida por rango de fechas para sacar solo una parte de una lista con semanas
# viejas sin cerrar. El 04-11-2026 se quitó (lo aprobó ella): esa salida se saltaba la revisión, y
# una lista con varias semanas ya no descarga la masiva. Esta prueba vigila ahora que:
#   · la salida por rango ya no se ve, y aunque se dispare a la fuerza NO entrega nada;
#   · con radicados de varias semanas la masiva no sale, y la franja de arriba dice cuáles son;
#   · nada se descarta solo: cada radicado sigue en la lista hasta que ella decida.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
VIEJO   ="202642110700001"   # 10 de septiembre
BORDE   ="202642110700002"   # 28 de septiembre
RECIENTE="202642110700003"   # 2 de octubre (misma semana que el borde)
BLOQUE="\n".join([
 VIEJO   +"\t01/09/2026\t10/09/2026\tPERSONA VIEJA",
 BORDE   +"\t01/09/2026\t28/09/2026\tPERSONA DEL BORDE",
 RECIENTE+"\t01/09/2026\t02/10/2026\tPERSONA RECIENTE",
])
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

def clasificar(pag, rad, suf):
    B.ir_a(pag,rad); B.pegar_tira(pag,TIRA.replace("46855268","4685526"+suf))
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p"+suf+"@gmail.com")
    B.escribir(pag,"#cc_res","13687"+suf); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    for i,rad in enumerate((VIEJO,BORDE,RECIENTE)): clasificar(pag,rad,str(i+1))
    pag.wait_for_timeout(600)

    print("1) los tres quedan LISTOS: lo que frena no es un dato, es la mezcla de semanas")
    ok(pag.locator("#masivaListaBadge").inner_text()=="3", "el botón cuenta 3 → "+pag.locator("#masivaListaBadge").inner_text())
    franja=pag.locator("#avisoSemanas")
    ok(franja.is_visible(), "la franja de semanas mezcladas se ve sin tocar nada")
    t=franja.inner_text()
    ok(VIEJO in t and BORDE in t and RECIENTE in t, "y nombra los radicados de cada semana → "+t[-200:])

    print("2) la masiva no sale así")
    ok(B.descargar(pag) is None, "no se descarga")
    ok(pag.locator("#queuePanel .queue-item").count()==3, "y no se descartó ninguno")

    print("3) la salida por rango ya no está, y forzada tampoco entrega")
    pag.click("#abrirDocumentosBtn"); pag.wait_for_timeout(500)
    ok(pag.locator("#cuadreRangoDescargar:visible").count()==0, "no se ve en Documentos")
    try:
        with pag.expect_download(timeout=4000):
            pag.evaluate("()=>document.getElementById('cuadreRangoDescargar').click()")
        ok(False, "disparada a la fuerza, NO descarga")
    except Exception:
        ok(True, "disparada a la fuerza, NO descarga")
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())"); pag.wait_for_timeout(300)

    print("4) al quitar el viejo (por ejemplo, cerrando su semana), la masiva sale")
    B.ir_a(pag,VIEJO); pag.click("#cc_delete"); pag.wait_for_timeout(300)
    pag.click("#deleteConfirmOk"); pag.wait_for_timeout(600)
    ok(not pag.locator("#avisoSemanas").is_visible(), "la franja se va sola")
    ok(B.descargar(pag, espera=20000) is not None, "y la masiva sale")

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
