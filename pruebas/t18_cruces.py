# LOS CRUCES QUE FALTABAN POR PROBAR. Tres formas de que la información se mezcle o se pierda que
# ninguna prueba anterior tocaba:
#   (a) dos personas usando el MISMO computador, una detrás de otra;
#   (b) dos ventanas trabajando la mañana a la vez;
#   (c) que lo que llega de la nube borre lo que se está trabajando aquí.
import sys, os, json, urllib.request; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B
SHEET = os.path.join(os.path.dirname(__file__), "sheet_donina.xlsx")
if not os.path.exists(SHEET):
    print("  SALTADA: falta pruebas/sheet_donina.xlsx"); sys.exit(0)
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
UID_ALE = "2b7fb249-8d97-1766-e730-4fd6e90ef330"
def nube_manana():
    d=json.loads(urllib.request.urlopen("http://127.0.0.1:9870/rest/v1/radicados_datos?usuario_id=eq."+UID_ALE,timeout=5).read())
    if not d or not d[0]: return None
    m=d[0].get("manana")
    return json.loads(m) if isinstance(m,str) else m
def entrar_como(pag, correo, limpio=False):
    pag.goto(B.URL, wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail", correo); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1800)

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag, "alejandra@gmail.com")
    pag.click("#selBloqueManana"); pag.wait_for_timeout(500)
    B.cargar_sheet_manana(pag, SHEET)
    pag.fill("#manNombre","ALEJANDRA"); pag.keyboard.press("Tab"); pag.wait_for_timeout(900)
    pag.click('#manTabs button[data-mantab="ia"]'); pag.wait_for_timeout(500)
    f = pag.locator("#manPanel .man-fila").first
    radA = f.locator(".man-rad").inner_text()
    f.locator("button[data-manok]").click(); pag.wait_for_timeout(900)
    ok(pag.locator("#manCuentaIa").inner_text().startswith("119"), "ALEJANDRA dejó 1 revisado → "+pag.locator("#manCuentaIa").inner_text())

    print("(a) entra OTRA persona en el mismo computador")
    pag.click("#userBadge"); pag.wait_for_timeout(700)
    pag.click("#authLogout"); pag.wait_for_timeout(1500)
    # la memoria tiene que quedar en blanco ANTES de que entre nadie
    quedo = pag.evaluate("()=>document.querySelectorAll('#manPanel .man-fila').length")
    ok(quedo == 0, "al cerrar sesión no queda ni una fila en pantalla (%d)" % quedo)
    entrar_como(pag, "sebastian@gmail.com")
    pag.click("#selBloqueManana"); pag.wait_for_timeout(900)
    txt = pag.locator("#manPanel").inner_text()
    ok(pag.locator("#manCuentaSin").inner_text()=="0 / 0", "la cuenta nueva abre VACÍA → "+pag.locator("#manCuentaSin").inner_text())
    ok(radA not in txt, "y no ve ni un radicado de la anterior")
    ok(pag.input_value("#manNombre")=="", "ni su nombre → "+repr(pag.input_value("#manNombre")))

    print("(b) vuelve la primera: su trabajo sigue intacto")
    pag.click("#userBadge"); pag.wait_for_timeout(700)
    pag.click("#authLogout"); pag.wait_for_timeout(1500)
    entrar_como(pag, "alejandra@gmail.com")
    pag.click("#selBloqueManana"); pag.wait_for_timeout(1200)
    ok(pag.locator("#manCuentaSin").inner_text().endswith("/ 65"), "sus 65 filas volvieron → "+pag.locator("#manCuentaSin").inner_text())
    ok(pag.locator("#manCuentaIa").inner_text().startswith("119"), "y su revisión también → "+pag.locator("#manCuentaIa").inner_text())
    ok(pag.input_value("#manNombre")=="ALEJANDRA", "y su nombre")

    print("(c) dos ventanas trabajando la mañana a la vez")
    flo=ctx.new_page(); ef=[]
    flo.on("pageerror", lambda x: ef.append(str(x)))
    flo.goto(B.URL+"#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail","alejandra@gmail.com"); flo.fill("#loginPassword","123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    flo.wait_for_timeout(2000)
    flo.click("#selBloqueManana"); flo.wait_for_timeout(900)
    flo.click('#manTabs button[data-mantab="ia"]'); flo.wait_for_timeout(600)
    # cada ventana trabaja un radicado DISTINTO
    fFlo = flo.locator("#manPanel .man-fila").first
    radFlo = fFlo.locator(".man-rad").inner_text()
    iFlo = fFlo.locator("input[data-manclas]")
    iFlo.click(); iFlo.fill("MASIVO TIPO 3"); flo.wait_for_timeout(300)
    flo.keyboard.press("Enter"); flo.wait_for_timeout(1200)
    pag.click('#manTabs button[data-mantab="ia"]'); pag.wait_for_timeout(500)
    filas = pag.locator("#manPanel .man-fila")
    radPri = None
    for i in range(filas.count()):
        r = filas.nth(i).locator(".man-rad").inner_text()
        if r != radFlo: radPri = r; break
    iPri = filas.nth(1 if radPri != filas.nth(0).locator(".man-rad").inner_text() else 0).locator("input[data-manclas]")
    iPri.click(); iPri.fill("MASIVO TIPO 8"); pag.wait_for_timeout(300)
    pag.keyboard.press("Enter"); pag.wait_for_timeout(1500)

    print("      flotante trabajó %s · principal trabajó %s" % (radFlo, radPri))
    n = nube_manana()
    hechas = {str(r["radicado"]): (r.get("correccion") or ("OK" if r.get("ok") else ""))
              for r in (n or {}).get("ia", []) if r.get("ok") or r.get("correccion")}
    ok(hechas.get(radFlo)=="MASIVO TIPO 3", "en la nube está lo de la flotante → "+str(hechas.get(radFlo)))
    ok(hechas.get(radPri)=="MASIVO TIPO 8", "y lo de la principal → "+str(hechas.get(radPri)))
    ok(hechas.get(radA)=="OK", "y lo de antes no se perdió → "+str(hechas.get(radA)))

    print("(d) la nube NO puede borrar lo que se está trabajando aquí")
    # se simula una nube "vieja y vacía" del día y se recarga: lo local debe sobrevivir
    antes = pag.locator("#manCuentaIa").inner_text()
    urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:9870/rest/v1/radicados_datos?usuario_id=eq.2b7fb249-8d97-1766-e730-4fd6e90ef330",
        data=json.dumps({"manana":{"sin":[], "ia":[], "historial":[], "actualizadoEn":1}}).encode(),
        headers={"Content-Type":"application/json"}, method="PATCH"), timeout=5).read()
    pag.reload(wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail","alejandra@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(2200)
    pag.click("#selBloqueManana"); pag.wait_for_timeout(900)
    ok(pag.locator("#manCuentaSin").inner_text().endswith("/ 65"),
       "una nube vacía NO borró el día abierto → "+pag.locator("#manCuentaSin").inner_text())
    print("errores js:", err or "ninguno", "|", ef or "ninguno")
    if err or ef: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
