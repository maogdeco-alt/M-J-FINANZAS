# LA RESOLUCIÓN ESCRITA COMO FECHA O CON TEXTO PEGADO (R29, 11-10-2026)
#
# En la masiva entregada el 02-10-2026 salieron dos resoluciones mal puestas, sin que ninguna regla
# avisara: una quedó como FECHA ("12/8/2025") y otra con texto pegado ("<número> del 11 de marzo de
# 2026"). El ANEXO salió "Res. 12/8/2025 de 2025" y "… de 2026 de 2026". Aquí se exige que la app
# lo avise en la revisión previa, sin impedir descargar (avisa, no bloquea, como las demás), y que
# una resolución bien escrita no dispare nada. Datos inventados; la forma del defecto es la real.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
def tira(i): return T.join(["1100100000004685%04d" % i, "C29", "19/04/2025", "21/04/2025", "No", "CAMARAS SALVAVIDAS", "VIGENTE",
                            "", "", "", "CEDULA DE CIUDADANIA", "5200000%d" % i, "PERSONA %d" % i, "ABC12%d" % i])
CASOS = [("202670000000011", "12/8/2025",                          "fecha"),
         ("202670000000012", "2103738236 del 11 de marzo de 2026", "texto"),
         ("202670000000013", "202542116795856",                    "bien"),
         ("202670000000014", "1368701",                            "bien")]
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, "\n".join("%s\t01/10/2026\t05/10/2026\tPERSONA %d" % (r, i) for i, (r, _, _) in enumerate(CASOS, 1)))
    for i, (rad, res, _) in enumerate(CASOS, 1):
        B.ir_a(pag, rad); B.pegar_tira(pag, tira(i))
        B.escribir(pag, "#cc_formato", "T11"); B.escribir(pag, "#cc_direccion", "persona%d@gmail.com" % i)
        B.escribir(pag, "#cc_res", res); B.escribir(pag, "#cc_fechaRes", "12/08/2025")
        pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

    print("1) la revisión previa lo avisa, radicado por radicado")
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    pre = ""
    with pag.expect_download(timeout=30000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count():
            pre = pag.locator("#preflightDialog").inner_text()
            pag.click("#preflightProceed")
    bloques = {rad: "" for rad, _, _ in CASOS}
    # cada aviso de la revisión previa va bajo su radicado; se mira el trozo de texto de cada uno
    for rad in bloques:
        k = pre.find(rad)
        bloques[rad] = pre[k:k + 900] if k >= 0 else ""
    ok("parece una FECHA" in bloques[CASOS[0][0]], "avisa que la resolución «12/8/2025» parece una fecha")
    ok("texto pegado" in bloques[CASOS[1][0]], "avisa que la resolución trae texto pegado")
    n29 = pre.count("parece una FECHA") + pre.count("trae texto pegado")
    ok(n29 == 2, "y solo esas dos: las resoluciones bien escritas no disparan nada → %d aviso(s)" % n29)
    print("2) avisa, no bloquea: el archivo se descarga igual")
    ruta = os.path.join(os.environ.get("TMPDIR", "/tmp"), "t39_masiva.xlsx"); dl.value.save_as(ruta)
    import openpyxl
    filas = list(openpyxl.load_workbook(ruta).active.iter_rows(min_row=2, values_only=True))
    ok(len(filas) == 4, "salen las 4 filas → %d" % len(filas))
    print("3) la regla está en el catálogo de Ajustes")
    pag.click("#reglasBtn"); pag.wait_for_timeout(1200)
    ok("R29" in pag.locator("body").inner_text(), "R29 aparece en el catálogo de reglas")
    ok(not err, "sin errores de JavaScript → %r" % err)
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
