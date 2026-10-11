# FLECHA PARA EL CONTEO POR FORMATO EN LA FLOTANTE (11-10-2026)
#
# A pedido de la usuaria: en la flotante, la franja de conteo por formato y el enlace a informes
# van ocultos, con una flecha para desplegarlos cuando quiera consultarlos. En la principal todo
# sigue igual (franja a la vista, sin flecha). Datos inventados.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
RAD = "202670000000002"
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, RAD + "\t01/10/2026\t05/10/2026\tPERSONA DE PRUEBA")
    ok(pag.locator("#openInformesLink").is_visible(), "en la principal el enlace a informes sigue a la vista")
    ok(not pag.locator("#navsubToggle").is_visible(), "en la principal no aparece la flecha")

    flo = ctx.new_page(); flo.set_viewport_size({"width": 620, "height": 540}); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded"); flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail", "prueba@gmail.com"); flo.fill("#loginPassword", "123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000); flo.wait_for_timeout(1500)
    ok(not flo.locator("#openInformesLink").is_visible(), "en la flotante la franja arranca oculta")
    ok(flo.locator("#navsubToggle").is_visible(), "en la flotante hay una flecha para desplegarla")
    if flo.locator("#navsubToggle").is_visible():
        flo.click("#navsubToggle"); flo.wait_for_timeout(300)
        ok(flo.locator("#openInformesLink").is_visible() and flo.locator("#formatoChips").is_visible(),
           "al tocar la flecha se ven el conteo por formato y el enlace a informes")
        ok(flo.get_attribute("#navsubToggle", "aria-expanded") == "true", "la flecha indica que está abierta")
        flo.click("#navsubToggle"); flo.wait_for_timeout(300)
        ok(not flo.locator("#openInformesLink").is_visible(), "al tocarla otra vez se vuelve a ocultar")
    ok(not err2 and not err, "sin errores de JavaScript → %r %r" % (err, err2))
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
