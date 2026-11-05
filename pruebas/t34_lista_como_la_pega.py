# UNA LISTA DE SOLO RADICADOS, PEGADA COMO LLEGA DE VERDAD
#
# La primera lista real (11-10-2026, 136 radicados, nada más) llegó con una comilla y un espacio
# antes del primer número, un espacio antes de cada uno y una comilla al final. Copiada de Excel
# llega con saltos de línea de Windows. Las dos formas tienen que entrar COMPLETAS. Y lo que no
# es un radicado tiene que quedar fuera diciendo POR QUÉ (no "menos de 4 columnas").
# Radicados inventados con la misma forma; ninguno es real.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
R = ["202661203%05d2" % (89000 - i * 37) for i in range(136)]
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def importar(pag, txt):
    pag.click("#abrirImportarBtn"); pag.wait_for_selector("#importDialog[open]", timeout=10000)
    pag.evaluate("""(b)=>{const acc=document.getElementById('paso1Accordion'); if(acc) acc.open=true;
      const t=document.getElementById('bulkPaste'); t.value=b; t.dispatchEvent(new Event('input',{bubbles:true}));}""", txt)
    pag.click("#importBtn"); pag.wait_for_timeout(900)
    rep = pag.locator("#importReportDialog").inner_text() if pag.locator("#importReportDialog[open]").count() else ""
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    return rep
def radicados(pag):
    return sorted(r.get("radicado") for r in pag.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));return JSON.parse(localStorage.getItem(k)||'[]')}"))

with sync_playwright() as pw:
    for nombre, txt in (("como la pegó (comillas y espacios)", '" ' + "\n ".join(R) + ' "'),
                        ("copiada de Excel (saltos de Windows)", "\r\n".join(R) + "\r\n")):
        nav, ctx, pag, err = B.abrir(pw)
        B.entrar(pag)
        importar(pag, txt)
        rs = radicados(pag)
        ok(rs == sorted(R), "%s: entran los 136, con su número exacto → %d" % (nombre, len(rs)))
        if err: fallos.append("errores de JavaScript: %s" % err)
        nav.close()
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    rep = importar(pag, "\n".join([R[0], "2,02661E+14", "2026612038709021", "20266120387090"]))
    ok(radicados(pag) == [R[0]], "solo entra el radicado bueno → %s" % radicados(pag))
    ok("número científico" in rep, "dice que Excel lo volvió número científico")
    ok("tiene 16 dígitos" in rep and "tiene 14 dígitos" in rep, "dice cuántos dígitos traen los que no son de 15")
    if err: fallos.append("errores de JavaScript: %s" % err)
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
