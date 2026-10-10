# UNA SEMANA CERRADA NO PUEDE VOLVER A LA LISTA.
#
# Pedido de la usuaria (10-10-2026): "cada semana es vital que la información se borre PERO que se
# guarde en el historial, NO se puede cruzar la información. ESO HA OCURRIDO". Reproducido así con
# la versión publicada (424c34a): principal y flotante abiertas; la flotante guarda; se cierra la
# semana desde la principal; la nube RECHAZA ese cierre (la marca de la principal quedó vieja) y
# sigue con la semana vieja; al entrar otra vez, la app junta nube y navegador y la semana cerrada
# vuelve entera a la lista, aunque ya está en el historial, y entra en la masiva siguiente.
import sys, os, json, hashlib, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
URL = B.URL
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
T = "\t"
def tira(i): return T.join(["1100100000004685%04d" % i, "C02", "19/04/2025", "19/04/2025", "No",
  "CAMARAS SALVAVIDAS", "VIGENTE", "", "", "", "CEDULA DE CIUDADANIA", "520000%03d" % i, "PERSONA %d" % i, "ABC%03d" % i])
VIEJA = ["2026500000000%02d" % i for i in (1, 2, 3)]
def bloque(rads, f): return "\n".join("%s\t01/09/2026\t%s\tPERSONA %d" % (r, f, i + 1) for i, r in enumerate(rads))
def login(p):
    p.goto(URL + ("#flotante=1" if p is not pag else ""), wait_until="domcontentloaded")
    p.wait_for_selector("#loginEmail", timeout=20000)
    p.fill("#loginEmail", "prueba@gmail.com"); p.fill("#loginPassword", "123456")
    p.click("#loginBtn"); p.wait_for_selector("#authDialog", state="hidden", timeout=20000); p.wait_for_timeout(1500)
def lista(p):
    p.evaluate("()=>{const b=document.querySelector('#filterTabs button[data-filter=\"all\"]'); if(b) b.click();}")
    p.wait_for_timeout(300)
    return sorted(set(t.split()[0] for t in p.locator("#queuePanel .queue-item .qi-rad, #queuePanel .queue-item").all_inner_texts() if t.strip()))
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.reiniciar(); login(pag)
    B.importar(pag, bloque(VIEJA, "21/09/2026"))
    for i, r in enumerate(VIEJA, 1):
        B.ir_a(pag, r); B.pegar_tira(pag, tira(i)); B.escribir(pag, "#cc_formato", "T14")
        B.escribir(pag, "#cc_res", "1%d" % i); B.escribir(pag, "#cc_fechaRes", "26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(400); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(2000)
    flo = ctx.new_page(); login(flo)
    if flo.locator("#captureEmptyVerTodos").is_visible(): flo.click("#captureEmptyVerTodos"); flo.wait_for_timeout(500)
    flo.fill("#cc_comentario", "algo en la flotante"); flo.dispatch_event("#cc_comentario", "input")
    flo.click("#cc_save"); flo.wait_for_timeout(500); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    flo.wait_for_timeout(2500)
    print("estado principal antes de cerrar:", pag.locator("#saveStatus").inner_text())
    pag.click("#cerrarSemanaNavBtn"); pag.wait_for_timeout(600); pag.click("#confirmOk"); pag.wait_for_timeout(3500)
    ok("otro lugar" not in pag.locator("#saveStatus").inner_text(), "el cierre llega a la nube → " + pag.locator("#saveStatus").inner_text())
    print("historial semanas (principal):", pag.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_historial_v1::'));return (JSON.parse(localStorage.getItem(k)||'[]')).length}"))
    pag.close(); flo.close()
    print("--- al día siguiente, MISMO computador: se entra de nuevo")
    pag = ctx.new_page(); pag.on("pageerror", lambda e: err.append(str(e)))
    login(pag)
    l = lista(pag); print("lista al entrar:", l)
    viejos = [r for r in VIEJA if any(r in x for x in l)]
    ok(not viejos, "la semana cerrada NO vuelve a la lista al entrar otra vez → %d de vuelta" % len(viejos))
    hist = pag.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_historial_v1::'));return (JSON.parse(localStorage.getItem(k)||'[]')).reduce((n,h)=>n+(h.records||[]).length,0)}")
    ok(hist == 3, "y sus 3 radicados siguen en el historial → %d" % hist)
    print("errores:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()

    print("--- (b) se cierra la semana SIN CONEXIÓN (la nube no se entera) y se entra otra vez con conexión")
    nav, ctx, pag, err = B.abrir(pw)
    B.reiniciar(); login(pag)
    B.importar(pag, bloque(VIEJA, "21/09/2026"))
    for i, r in enumerate(VIEJA, 1):
        B.ir_a(pag, r); B.pegar_tira(pag, tira(i)); B.escribir(pag, "#cc_formato", "T14")
        B.escribir(pag, "#cc_res", "1%d" % i); B.escribir(pag, "#cc_fechaRes", "26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(400); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(2000)
    ctx.route("http://127.0.0.1:9870/rest/**", lambda route: route.abort())   # se cae la conexión
    pag.click("#cerrarSemanaNavBtn"); pag.wait_for_timeout(600); pag.click("#confirmOk"); pag.wait_for_timeout(3000)
    pag.close()
    ctx.unroute("http://127.0.0.1:9870/rest/**")                              # vuelve
    pag = ctx.new_page(); pag.on("pageerror", lambda e: err.append(str(e)))
    login(pag)
    l = lista(pag); print("lista al entrar:", l)
    viejos = [r for r in VIEJA if any(r in x for x in l)]
    ok(not viejos, "(b) la semana cerrada sin conexión NO vuelve a la lista → %d de vuelta" % len(viejos))
    hist = pag.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_historial_v1::'));return (JSON.parse(localStorage.getItem(k)||'[]')).reduce((n,h)=>n+(h.records||[]).length,0)}")
    ok(hist == 3, "(b) y sus 3 radicados siguen en el historial → %d" % hist)
    err[:] = [e for e in err if "ERR_FAILED" not in e]  # la caída de red es a propósito en (b)
    print("errores:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
