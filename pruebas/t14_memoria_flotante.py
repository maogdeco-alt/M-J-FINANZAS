# LA MEMORIA DE LA VENTANA FLOTANTE. Tres cosas distintas, que conviene no confundir:
#   (a) lo que se escribe NO se pierde ni cerrando la ventana en seco;
#   (b) al volver a abrirla, vuelve al radicado en el que se estaba (antes empezaba del primero);
#   (c) cada ventana recuerda LO SUYO: mover una no arrastra a la otra.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T="\t"
def tira(i): return T.join(["1100100000004685%04d"%i,"C02","19/04/2025","19/04/2025","No",
  "CAMARAS SALVAVIDAS","VIGENTE","","","","CEDULA DE CIUDADANIA","520000%03d"%i,"PERSONA %d"%i,"ABC%03d"%i])
BLOQUE="\n".join("2026ER%03d\t01/09/2026\t03/09/2026\tPERSONA %d"%(i,i) for i in range(1,6))
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
def abrir_flotante(ctx):
    f=ctx.new_page(); e=[]
    f.on("pageerror", lambda x: e.append(str(x)))
    f.goto(B.URL+"#flotante=1", wait_until="domcontentloaded")
    f.wait_for_selector("#loginEmail", timeout=20000)
    f.fill("#loginEmail","prueba@gmail.com"); f.fill("#loginPassword","123456")
    f.click("#loginBtn"); f.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    f.wait_for_timeout(1600)
    return f,e
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    for i in range(1,6):
        B.ir_a(pag,"2026ER%03d"%i); B.pegar_tira(pag,tira(i))
        B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p%d@gmail.com"%i)
        B.escribir(pag,"#cc_res","13687%02d"%i); B.escribir(pag,"#cc_fechaRes","26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(400); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

    print("(a) cerrar la flotante en seco justo después de escribir")
    flo,ef=abrir_flotante(ctx)
    B.ir_a_compacto(flo,"2026ER004")
    flo.fill("#cc_idNum","ESCRITO Y CERRADO AL INSTANTE"); flo.dispatch_event("#cc_idNum","input")
    flo.wait_for_timeout(150)
    flo.close(); pag.wait_for_timeout(1500)
    B.ir_a(pag,"2026ER004")
    ok(pag.input_value("#cc_idNum")=="ESCRITO Y CERRADO AL INSTANTE",
       "no se pierde lo escrito → "+repr(pag.input_value("#cc_idNum")))

    print("(b) al reabrir la flotante, vuelve donde estaba")
    flo,ef=abrir_flotante(ctx)
    B.ir_a_compacto(flo,"2026ER004")
    estaba=flo.locator("#cc_radicadoLabel").inner_text()
    flo.close(); pag.wait_for_timeout(700)
    flo,ef=abrir_flotante(ctx)
    vuelve=flo.locator("#cc_radicadoLabel").inner_text()
    ok(estaba==vuelve, "estaba en «%s» y vuelve a «%s»" % (estaba, vuelve))

    print("(c) cada ventana recuerda lo suyo")
    B.ir_a(pag,"2026ER001")
    enPrincipal=pag.locator("#cc_radicadoLabel").inner_text()
    flo.wait_for_timeout(600)
    enFlotante=flo.locator("#cc_radicadoLabel").inner_text()
    ok("2026ER001" in enPrincipal and "2026ER004" in enFlotante,
       "la principal en «%s» y la flotante sigue en «%s»" % (enPrincipal, enFlotante))
    print("errores js:", err or "ninguno", "|", ef or "ninguno")
    if err or ef: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
