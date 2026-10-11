# RESTAURAR UN PUNTO NO PUEDE DESHACER LO QUE YA ESTABA CORREGIDO.
#
# La pantalla lo promete: "Restaurar nunca borra nada: añade lo que falte y rellena los datos
# vacíos, y deja intacto lo que ya tengas". El código hacía lo contrario: el dato VIEJO del punto
# pisaba al de ahora (encontrado en la auditoría del 10-10-2026). Si se restauraba un punto para
# recuperar un radicado borrado, todos los demás volvían a como estaban en ese momento.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
RAD = ["202640000000001", "202640000000002"]
BLOQUE = "\n".join("%s\t01/09/2026\t03/09/2026\tPERSONA %d" % (r, i + 1) for i, r in enumerate(RAD))
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag); B.importar(pag, BLOQUE)
    B.ir_a(pag, RAD[0]); B.escribir(pag, "#cc_idNum", "COMENTARIO VIEJO")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    print("1) se crea un punto (con el comentario viejo)")
    pag.click("#settingsBtn"); pag.wait_for_timeout(600)
    pag.locator('#settingsDialog button[data-stab="papelera"]').click(); pag.wait_for_timeout(400)
    pag.click("#puntosCrear"); pag.wait_for_timeout(900)
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    print("2) se corrige el comentario y se borra el otro radicado")
    B.ir_a(pag, RAD[0]); B.escribir(pag, "#cc_idNum", "COMENTARIO CORREGIDO")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    B.ir_a(pag, RAD[1]); pag.click("#cc_delete"); pag.wait_for_timeout(400)
    pag.click("#deleteConfirmOk"); pag.wait_for_timeout(700)
    print("3) se restaura el punto para recuperar el borrado")
    pag.click("#settingsBtn"); pag.wait_for_timeout(600)
    pag.locator('#settingsDialog button[data-stab="papelera"]').click(); pag.wait_for_timeout(400)
    pag.click("#puntosRefrescar"); pag.wait_for_timeout(700)
    # el punto creado a mano en el paso 1 es el más viejo de la lista (el borrado creó otro después)
    pag.locator("#puntosLista button[data-punto-restaurar]").last.click(); pag.wait_for_timeout(900)
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    vuelve = pag.locator('#queuePanel .queue-item', has_text=RAD[1]).count() > 0 or pag.evaluate(
        "(r)=>{const b=document.querySelector('#filterTabs button[data-filter=\"all\"]'); if(b) b.click(); return !!document.querySelector('#queuePanel .queue-item')}", RAD[1])
    B.ir_a(pag, RAD[1])
    ok(RAD[1] in pag.locator("#cc_radicadoLabel").inner_text(), "volvió el radicado borrado")
    B.ir_a(pag, RAD[0])
    ok(pag.input_value("#cc_idNum") == "COMENTARIO CORREGIDO",
       "el comentario corregido NO vuelve al viejo → " + repr(pag.input_value("#cc_idNum")))
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
