# El bloque de la mañana: que GUARDE sin fallas y que se pueda trabajar en la ventana flotante.
import sys, os, json, urllib.request; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B
SHEET = os.path.join(os.path.dirname(__file__), "sheet_donina.xlsx")
# El sheet de Donina lleva datos de ciudadanos reales: NO va en el repositorio (ver .gitignore).
# Para correr esta prueba, deja una copia del archivo del día aquí con ese nombre.
if not os.path.exists(SHEET):
    print("  SALTADA: falta pruebas/sheet_donina.xlsx (el sheet real no se guarda en el repositorio).")
    print("  Copia aquí el archivo de un día cualquiera con ese nombre y vuelve a correrla.")
    sys.exit(0)
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
def nube():
    d=json.loads(urllib.request.urlopen("http://127.0.0.1:9870/rest/v1/radicados_datos?x",timeout=5).read())
    if not d or not d[0]: return None
    m=d[0].get("manana")
    if isinstance(m,str): m=json.loads(m)
    return m
def entrar_flotante(ctx):
    f=ctx.new_page(); e=[]
    f.on("pageerror", lambda x: e.append(str(x)))
    f.goto(B.URL+"#flotante=1", wait_until="domcontentloaded")
    f.wait_for_selector("#loginEmail", timeout=20000)
    f.fill("#loginEmail","prueba@gmail.com"); f.fill("#loginPassword","123456")
    f.click("#loginBtn"); f.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    f.wait_for_timeout(1800)
    return f,e
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag)
    pag.click("#selBloqueManana"); pag.wait_for_timeout(500)
    pag.set_input_files("#manFile", SHEET); pag.wait_for_timeout(2500)
    pag.fill("#manNombre","ALEJANDRA"); pag.keyboard.press("Tab"); pag.wait_for_timeout(900)

    print("1) sube a la nube en su propia columna, sin tocar la de la masiva")
    n = nube()
    ok(n is not None, "la columna «manana» llegó al servidor")
    if n:
        ok(len(n.get("sin",[]))==65 and len(n.get("ia",[]))==167, "con las 65 + 167 filas → %d + %d" % (len(n.get("sin",[])), len(n.get("ia",[]))))
        ok(n.get("nombre")=="ALEJANDRA", "y con el nombre → "+repr(n.get("nombre")))

    print("2) «solo los míos» usa ese nombre")
    pag.click('#manTabs button[data-mantab="sin"]'); pag.wait_for_timeout(400)
    pag.uncheck("#manSoloPendientes"); pag.wait_for_timeout(500)
    todas = pag.locator("#manPanel .man-fila").count()
    pag.check("#manSoloMios"); pag.wait_for_timeout(600)
    mias = pag.locator("#manPanel .man-fila").count()
    print("      de %d filas, %d quedan al filtrar por ALEJANDRA" % (todas, mias))
    ok(0 < mias < todas, "filtra de verdad (reconoce «MARIA  ALEJANDRA» como tuya)")
    pag.uncheck("#manSoloMios"); pag.wait_for_timeout(400)

    print("3) al recargar, todo sigue ahí")
    pag.reload(wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(2000)
    ok(pag.locator("#bloqueManana").is_visible(), "abre directo en el bloque de la mañana (lo recuerda)")
    ok(pag.locator("#manCuentaSin").inner_text().endswith("/ 65"), "las 65 siguen → "+pag.locator("#manCuentaSin").inner_text())
    ok(pag.input_value("#manNombre")=="ALEJANDRA", "y el nombre también")

    print("4) la ventana flotante")
    flo,ef = entrar_flotante(ctx)
    flo.click("#selBloqueManana"); flo.wait_for_timeout(900)
    ok(flo.locator("#bloqueManana").is_visible(), "el bloque de la mañana se ve en la flotante")
    ok(flo.locator("#manPanel .man-fila").count() > 0, "con sus filas (%d)" % flo.locator("#manPanel .man-fila").count())
    ok(flo.locator("#manCargaAccordion").is_hidden(), "sin el bloque de cargar, que ahí no hace falta")
    flo.click('#manTabs button[data-mantab="ia"]'); flo.wait_for_timeout(700)
    fila = flo.locator("#manPanel .man-fila").first
    rad = fila.locator(".man-rad").inner_text()
    inp = fila.locator("input[data-manclas]")
    inp.click(); flo.wait_for_timeout(500)
    ok(flo.locator("#manSugerenciasVivas .fd-item").count() > 20, "el desplegable de clasificaciones funciona ahí dentro")
    inp.fill("MASIVO TIPO 7"); flo.wait_for_timeout(300); flo.keyboard.press("Enter"); flo.wait_for_timeout(1200)

    print("5) lo que se hace en la flotante llega a la principal")
    pag.reload(wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(2200)
    pag.click('#manTabs button[data-mantab="ia"]'); pag.wait_for_timeout(500)
    pag.uncheck("#manSoloPendientes"); pag.wait_for_timeout(600)
    pag.fill("#manBuscar", rad); pag.wait_for_timeout(700)
    txt = pag.locator("#manPanel").inner_text()
    ok("MASIVO TIPO 7" in txt, "la corrección hecha en la flotante está en la principal → " + txt.replace("\n"," ")[:150])
    print("errores js:", err or "ninguno", "|", ef or "ninguno")
    if err or ef: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
