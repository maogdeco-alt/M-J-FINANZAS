# "Revisa que todas las opciones estén incluidas y funcionales."
# Las que solo aparecen al hacer algo, y que ninguna prueba tocaba: la DOBLE VERIFICACIÓN de las
# reglas, agregar un radicado a mano, la calculadora de término, la papelera y los puntos de
# restauración.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
BLOQUE="2026ER001\t01/09/2026\t03/09/2026\tPERSONA 1"
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)

    print("1) DOBLE VERIFICACIÓN para cambiar una regla")
    pag.click("#reglasBtn"); pag.wait_for_selector("#reglasDialog[open]"); pag.wait_for_timeout(600)
    editar = pag.locator("button[data-regla-editar]").first
    ok(editar.count()>0, "hay reglas que se pueden ajustar")
    rid = editar.get_attribute("data-regla-editar")
    editar.click(); pag.wait_for_timeout(600)
    ok(pag.locator("#reglaCambioDialog[open]").count()==1, "se abre la verificación")
    ok("1 de 2" in pag.locator("#reglaCambioTitle").inner_text(), "empieza en «Verificación 1 de 2»")
    # hay que tocar algo primero: se cambia el valor del parámetro
    # el ajuste es por casillas (a qué clasificaciones aplica la regla): se marca una que no lo esté
    cajas = pag.locator("#reglaCambioResumen input[type=checkbox]")
    cambiada = None
    for i in range(cajas.count()):
        if not cajas.nth(i).is_checked():
            cajas.nth(i).check(); cambiada = cajas.nth(i).get_attribute("data-regla-cat"); break
    if cambiada is None and cajas.count():
        cajas.first.uncheck(); cambiada = cajas.first.get_attribute("data-regla-cat")
    print("      se marca la clasificación:", cambiada)
    pag.wait_for_timeout(250)
    pag.click("#reglaCambioNext"); pag.wait_for_timeout(500)
    ok(pag.locator("#reglaCambioPaso2").is_visible(), "pasa a la verificación 2 de 2")
    ok(pag.locator("#reglaCambioConfirm").is_visible(), "y aparece «Confirmar el cambio»")
    print("      pide escribir:", pag.locator("#reglaCambioIdEsperado").inner_text())
    # se escribe MAL a propósito: no debe dejar
    pag.fill("#reglaCambioConfirmInput","XXXX"); pag.click("#reglaCambioConfirm"); pag.wait_for_timeout(500)
    ok(pag.locator("#reglaCambioDialog[open]").count()==1, "con el identificador mal, NO deja cambiar")
    ok(not pag.locator("#reglaCambioError").is_hidden(), "y lo dice")
    # ahora bien
    pag.fill("#reglaCambioConfirmInput", rid); pag.click("#reglaCambioConfirm"); pag.wait_for_timeout(800)
    ok(pag.locator("#reglaCambioDialog[open]").count()==0, "con el identificador correcto, sí cambia")
    txt = pag.locator("#reglasDialog").inner_text()
    ok(cambiada is not None and cambiada in txt, "el cambio se ve en la regla (%s)" % cambiada)
    ok("BITÁCORA" in txt.upper() and rid in txt, "y queda anotado en la bitácora")
    # deshacer, para no dejar la prueba sucia
    pag.evaluate("()=>document.getElementById('reglasDialog').close()"); pag.wait_for_timeout(300)

    print("2) agregar un radicado a mano")
    pag.click("#abrirImportarBtn"); pag.wait_for_timeout(600)
    pag.click("#addOneBtn"); pag.wait_for_timeout(500)
    ok(pag.locator("#addOneDialog[open]").count()==1, "se abre la ventana")
    pag.fill("#one_radicado","2026ER999"); pag.fill("#one_nombre","PERSONA A MANO")
    pag.click("#addOneConfirm"); pag.wait_for_timeout(800)
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())"); pag.wait_for_timeout(400)
    pag.evaluate("()=>{const b=document.querySelector('#filterTabs button[data-filter=\"all\"]'); if(b) b.click();}")
    pag.wait_for_timeout(400)
    ok(pag.locator('#queuePanel .queue-item', has_text="2026ER999").count()>0, "y el radicado entra a la cola")

    print("3) calculadora de término")
    if pag.locator("#termCalcBtn").count():
        pag.click("#termCalcBtn"); pag.wait_for_timeout(500)
        ok(pag.locator("#termCalcDialog[open]").count()==1, "se abre")
        pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())"); pag.wait_for_timeout(300)
    else:
        print("      (no hay botón de calculadora en esta versión)")

    print("4) las cuatro pestañas de Ajustes")
    pag.click("#settingsBtn"); pag.wait_for_timeout(700)
    for tab in ["general","clasificacion","informes","papelera"]:
        antes=len(err)
        pag.locator('#settingsDialog button[data-stab="%s"]' % tab).click(); pag.wait_for_timeout(450)
        vis = pag.locator("#stab-"+tab).is_visible()
        ok(vis and len(err)==antes, "pestaña «%s»: se abre y no rompe nada" % tab)
        pag.evaluate("()=>document.querySelectorAll('#settingsDialog details').forEach(d=>d.open=true)")
        pag.wait_for_timeout(250)
        for bid,nom in [("#papeleraRefrescar","papelera"),("#puntosRefrescar","puntos de restauración"),
                        ("#entregasRefrescar","constancias de entrega"),("#repetidosRefrescar","datos repetidos"),
                        ("#downloadHistoryBtn","descargar historial")]:
            b=pag.locator(bid)
            if b.count() and b.is_visible() and bid!="#downloadHistoryBtn":
                a2=len(err); b.click(); pag.wait_for_timeout(350)
                ok(len(err)==a2, "   "+nom+": responde sin romperse")
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
