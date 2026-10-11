# SONDA (rehecha): concurrencia de verdad. Primero se clasifican los radicados para que
# "Siguiente" funcione también en la flotante; después se prueba que no se pisen.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T="\t"
def tira(i): return T.join(["1100100000004685%04d"%i,"C02","19/04/2025","19/04/2025","No",
  "CAMARAS SALVAVIDAS","VIGENTE","","","","CEDULA DE CIUDADANIA","520000%03d"%i,"PERSONA %d"%i,"ABC%03d"%i])
BLOQUE="\n".join("2026ER%03d\t01/09/2026\t03/09/2026\tPERSONA %d"%(i,i) for i in (1,2,3))
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    for i in (1,2,3):
        B.ir_a(pag,"2026ER%03d"%i); B.pegar_tira(pag,tira(i))
        B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p%d@gmail.com"%i)
        B.escribir(pag,"#cc_res","13687%02d"%i); B.escribir(pag,"#cc_fechaRes","26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    flo=ctx.new_page(); err2=[]
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL+"#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail","prueba@gmail.com"); flo.fill("#loginPassword","123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    flo.wait_for_timeout(1500)
    lleg=B.ir_a_compacto(flo,"2026ER003")
    print("  flotante en:", flo.locator("#cc_radicadoLabel").inner_text(), "| principal en:", pag.locator("#cc_radicadoLabel").inner_text())
    ok(lleg, "la flotante puede moverse hasta el 003 con Siguiente")

    print("(b) radicados DISTINTOS a la vez")
    B.ir_a(pag,"2026ER001")
    flo.fill("#cc_idNum","DEL 003 EN LA FLOTANTE"); flo.dispatch_event("#cc_idNum","input")
    flo.click("#cc_save"); flo.wait_for_timeout(900); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    pag.fill("#cc_idNum","DEL 001 EN LA PRINCIPAL"); pag.dispatch_event("#cc_idNum","input")
    pag.click("#cc_save"); pag.wait_for_timeout(1000); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(1500)
    B.ir_a(pag,"2026ER003"); v3=pag.input_value("#cc_idNum")
    B.ir_a(pag,"2026ER001"); v1=pag.input_value("#cc_idNum")
    ok(v1=="DEL 001 EN LA PRINCIPAL", "sobrevive lo de la principal → "+repr(v1))
    ok(v3=="DEL 003 EN LA FLOTANTE", "sobrevive lo de la flotante → "+repr(v3))

    print("(c) el MISMO radicado, casillas distintas")
    B.ir_a_compacto(flo,"2026ER002"); B.ir_a(pag,"2026ER002")
    print("  flotante en:", flo.locator("#cc_radicadoLabel").inner_text(), "| principal en:", pag.locator("#cc_radicadoLabel").inner_text())
    flo.fill("#cc_direccion","flotante@gmail.com"); flo.dispatch_event("#cc_direccion","input")
    pag.fill("#cc_idNum","NOTA DE LA PRINCIPAL"); pag.dispatch_event("#cc_idNum","input")
    flo.click("#cc_save"); flo.wait_for_timeout(1000); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    pag.click("#cc_save"); pag.wait_for_timeout(1300); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(900)
    B.ir_a(pag,"2026ER001"); B.ir_a(pag,"2026ER002")
    d=pag.input_value("#cc_direccion"); c=pag.input_value("#cc_idNum")
    ok(d=="flotante@gmail.com", "se conserva la casilla escrita en la flotante → "+repr(d))
    ok(c=="NOTA DE LA PRINCIPAL", "y la escrita en la principal → "+repr(c))
    print("errores js:", (err or "ninguno"), "|", (err2 or "ninguno"))
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")

# Hasta el 10-10-2026 esta prueba terminaba SIEMPRE con éxito (exit 0), fallara lo que fallara:
# la batería no se enteraba nunca de un choque entre ventanas. Ahora cuenta.
import sys as _s
_s.exit(1 if fallos else 0)
