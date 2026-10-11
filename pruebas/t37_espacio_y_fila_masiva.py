# MEJOR USO DEL ESPACIO (11-10-2026) SIN PERDER NADA
#
# La casilla Comentario salió de la pantalla a pedido de la usuaria. Aquí se exige:
#   1. que ya no se vea, en la principal ni en la flotante;
#   2. que un comentario YA guardado no se borre al seguir trabajando el radicado;
#   3. que la flotante muestre la fila de la masiva del radicado y que coincida, columna por
#      columna, con la que sale en el archivo descargado;
#   4. que la flotante quepa en mucho menos alto que antes (antes ~1180 px para un radicado).
# Datos inventados.
import sys, os, json, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
RAD = "202670000000001"
TIRA = T.join(["11001000000046850001", "C29", "19/04/2025", "21/04/2025", "No", "CAMARAS SALVAVIDAS", "VIGENTE", "", "", "",
               "CEDULA DE CIUDADANIA", "52000001", "PERSONA DE PRUEBA", "ABC123"])
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
CLAVE = "radicados_semanales_v2::prueba@gmail.com"
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, RAD + "\t01/10/2026\t05/10/2026\tPERSONA DE PRUEBA")
    # un comentario escrito con la versión anterior (cuando la casilla existía)
    pag.evaluate("""(k)=>{const a=JSON.parse(localStorage.getItem(k)); a[0].comentario='NOTA DE ANTES'; localStorage.setItem(k, JSON.stringify(a));}""", CLAVE)
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail", "prueba@gmail.com"); pag.fill("#loginPassword", "123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000); pag.wait_for_timeout(1000)
    B.ir_a(pag, RAD)
    ok(not pag.locator("#cc_comentario").is_visible(), "la casilla Comentario ya no está en la principal")
    B.pegar_tira(pag, TIRA); B.escribir(pag, "#cc_formato", "T11"); B.escribir(pag, "#cc_direccion", "prueba@gmail.com")
    B.escribir(pag, "#cc_res", "1234567"); B.escribir(pag, "#cc_fechaRes", "26/07/2025")
    pag.click("#cc_save"); pag.wait_for_timeout(600); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    rec = json.loads(pag.evaluate("(k)=>localStorage.getItem(k)", CLAVE))[0]
    ok(rec.get("comentario") == "NOTA DE ANTES", "el comentario ya guardado no se borra al trabajar el radicado → %r" % rec.get("comentario"))

    flo = ctx.new_page(); flo.set_viewport_size({"width": 620, "height": 540}); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded"); flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail", "prueba@gmail.com"); flo.fill("#loginPassword", "123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000); flo.wait_for_timeout(1500)
    if flo.locator("#captureEmptyVerTodos").is_visible(): flo.click("#captureEmptyVerTodos"); flo.wait_for_timeout(500)
    ok(RAD in flo.locator("#cc_radicadoLabel").inner_text(), "la flotante abre el radicado")
    ok(not flo.locator("#cc_comentario").is_visible(), "la casilla Comentario ya no está en la flotante")
    alto = flo.evaluate("()=>document.documentElement.scrollHeight")
    ok(alto < 950, "la flotante ocupa mucho menos alto (antes ~1180 px) → %d px" % alto)
    auto = flo.locator("#filaMasivaAuto").inner_text()
    ok("FOTO EXTEMPO CON RES Y ANEXOS" in auto and "46850001" in auto and "Res. 1234567 de 2025" in auto,
       "la flotante muestra lo que la app pone sola en la masiva → %r" % auto.replace("\n", " "))
    flo.click("#filaMasivaDetails > summary"); flo.wait_for_timeout(400)
    vista = flo.evaluate("()=>[...document.querySelectorAll('#filaMasivaTabla tr')].map(tr=>tr.children[2].textContent)")
    flo.close()

    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    salida = os.path.join(os.environ.get("TMPDIR", "/tmp"), "t37_masiva.xlsx")
    with pag.expect_download(timeout=30000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightProceed")
    dl.value.save_as(salida)
    fila = [("" if c is None else str(c)) for c in list(openpyxl.load_workbook(salida).active.iter_rows(min_row=2, values_only=True))[0]]
    ok(len(vista) == 27 and vista == fila, "la fila que muestra la flotante es IGUAL a la del archivo, las 27 columnas" +
       ("" if vista == fila else " → " + str([(i, a, b) for i, (a, b) in enumerate(zip(vista, fila)) if a != b][:5])))
    print("errores js:", err or "ninguno", "|", err2 or "ninguno")
    if err or err2: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
