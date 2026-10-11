# SONDA: en la ventana flotante, cuando ya no quedan PENDIENTES, ¿qué se ve y qué se puede hacer?
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T="\t"
def tira(i): return T.join(["1100100000004685%04d"%i,"C02","19/04/2025","19/04/2025","No",
  "CAMARAS SALVAVIDAS","VIGENTE","","","","CEDULA DE CIUDADANIA","520000%03d"%i,"PERSONA %d"%i,"ABC%03d"%i])
BLOQUE="\n".join("2026ER%03d\t01/09/2026\t03/09/2026\tPERSONA %d"%(i,i) for i in (1,2))
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    for i in (1,2):
        B.ir_a(pag,"2026ER%03d"%i); B.pegar_tira(pag,tira(i))
        B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p%d@gmail.com"%i)
        B.escribir(pag,"#cc_res","13687%02d"%i); B.escribir(pag,"#cc_fechaRes","26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    flo=ctx.new_page()
    flo.goto(B.URL+"#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail","prueba@gmail.com"); flo.fill("#loginPassword","123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    flo.wait_for_timeout(1800)
    print("¿se ve el formulario?", flo.locator("#captureForm").is_visible())
    print("¿se ve el cartel de vacío?", flo.locator("#captureEmpty").is_visible())
    if flo.locator("#captureEmpty").is_visible():
        print("dice:", flo.locator("#captureEmpty").inner_text().replace("\n"," "))
    print("controles disponibles en la flotante para cambiar de filtro o buscar:")
    for sel,nom in [("#filterTabs","pestañas Pendientes/Completos/Todos"),("#search","buscador"),
                    ("#queuePanel","lista de la cola"),("#cc_next","botón Siguiente"),
                    ("#cc_prev","botón Anterior"),("#toggleQueueBtn","botón mostrar cola")]:
        c=flo.locator(sel)
        print("   ", nom, "->", ("VISIBLE" if (c.count() and c.first.is_visible()) else "no se ve"))
    print("--- se pulsa 'Ver todos los radicados' ---")
    flo.click("#captureEmptyVerTodos"); flo.wait_for_timeout(800)
    ok(flo.locator("#captureForm").is_visible(), "vuelve el formulario")
    print("radicado a la vista:", flo.locator("#cc_radicadoLabel").inner_text() if flo.locator("#captureForm").is_visible() else "-")
    ok(flo.locator("#cc_next").is_visible(), "y se puede navegar con Siguiente")
    nav.close()

# Antes terminaba siempre con éxito: era una sonda que solo imprimía. Ahora exige la salida.
import sys as _s
_s.exit(1 if fallos else 0)
