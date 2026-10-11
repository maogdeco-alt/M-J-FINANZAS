# TODO A MANO: SOLO EL RADICADO Y NINGUNA LÍNEA DE FÉNIX
#
# Pedido el 11-10-2026: copiar solo los radicados y que la app habilite las demás casillas de la
# masiva para llenarlas a mano, con la masiva del 02-10-2026 como modelo. Aquí se llena cada
# casilla escribiendo (sin pegar ninguna línea de Fénix), en la principal y en la flotante, y se
# exige que la masiva salga con cada valor en su columna y con el formato de la del 02-10:
# fechas dd-mmm-aaaa, comparendo de 8 dígitos repetido en C y N, TIPO y PLANTILLA con su texto,
# ANEXO "Res. <número> de <año>". Datos inventados.
import sys, os, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
RAD = ["202650000000001", "202650000000002"]
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def guardar(p):
    p.click("#cc_save"); p.wait_for_timeout(500); B.confirmar_nombre(p); B.cerrar_alerta(p)
def a_mano(p, i, medio):
    B.escribir(p, "#cc_fechaRadicacion", "01/10/2026"); B.escribir(p, "#cc_fechaAsignacion", "05/10/2026")
    B.escribir(p, "#cc_nombre", "PERSONA MANO %d" % i)
    B.escribir(p, "#cc_formato", "T1"); B.escribir(p, "#cc_direccion", "mano%d@gmail.com" % i)
    ok(p.locator("#m_comparendoCompleto").is_visible(), "%02d: las casillas del comparendo están abiertas, sin buscarlas" % i)
    B.escribir(p, "#m_comparendoCompleto", "1100100000000123%04d" % i)
    B.escribir(p, "#m_cod", "C2%d" % i); B.escribir(p, "#m_imposicion", "10/01/2025")
    B.escribir(p, "#m_notificacion", "15/01/2025"); B.escribir(p, "#m_medio", medio); B.escribir(p, "#m_estado", "VIGENTE")
    B.escribir(p, "#cc_tipoId", "CEDULA DE CIUDADANIA"); B.escribir(p, "#cc_idNum", "51000%03d" % i)
    B.escribir(p, "#cc_res", "88%04d" % i); B.escribir(p, "#cc_fechaRes", "20/02/2025")
    guardar(p)

with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, "\n".join(RAD))
    B.ir_a(pag, RAD[0]); a_mano(pag, 1, "COMPARENDERA")
    print("(flotante) el 02 se llena entero desde la ventana flotante")
    flo = ctx.new_page(); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail", "prueba@gmail.com"); flo.fill("#loginPassword", "123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000); flo.wait_for_timeout(1500)
    if flo.locator("#captureEmptyVerTodos").is_visible(): flo.click("#captureEmptyVerTodos"); flo.wait_for_timeout(400)
    for _ in range(3):
        if RAD[1] in flo.locator("#cc_radicadoLabel").inner_text(): break
        flo.click("#cc_next"); flo.wait_for_timeout(300); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    ok(RAD[1] in flo.locator("#cc_radicadoLabel").inner_text(), "la flotante está en el 02")
    a_mano(flo, 2, "COMPARENDERA"); flo.wait_for_timeout(1500); flo.close()

    pag.reload(wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail", "prueba@gmail.com"); pag.fill("#loginPassword", "123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000); pag.wait_for_timeout(1200)
    B.ir_a(pag, RAD[1])
    ok(pag.input_value("#m_cod") == "C22" and pag.input_value("#m_medio") == "COMPARENDERA",
       "tras recargar, la principal muestra lo que llenó la flotante → %r / %r" % (pag.input_value("#m_cod"), pag.input_value("#m_medio")))
    # corregir UNA casilla no borra las demás
    B.escribir(pag, "#m_estado", "VIGENTE"); B.escribir(pag, "#m_cod", "C24"); guardar(pag)
    ok(pag.input_value("#cc_idNum") == "51000002", "corregir la infracción no borra el número de documento → %r" % pag.input_value("#cc_idNum"))

    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    salida = os.path.join(os.environ.get("TMPDIR", "/tmp"), "t35_masiva.xlsx")
    rp = ""
    with pag.expect_download(timeout=30000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count():
            rp = pag.locator("#preflightDialog").inner_text()
            pag.click("#preflightProceed")
    dl.value.save_as(salida)
    ok("CORTADA" not in rp and "solo el número" not in rp and "corrieron" not in rp,
       "la revisión previa no confunde lo llenado a mano con una línea de Fénix mal pegada" + ("" if not rp else " → " + rp[:300].replace("\n", " | ")))
    ws = openpyxl.load_workbook(salida).active
    filas = [[("" if c is None else str(c)) for c in f] for f in ws.iter_rows(values_only=True)]
    cuerpo = {f[0]: f for f in filas[1:]}
    for i, cod in ((1, "C21"), (2, "C24")):
        f = cuerpo.get(RAD[i - 1])
        ok(f is not None, "%02d está en la masiva" % i)
        if not f: continue
        esperado = [RAD[i - 1], "01-oct-2026", "0123%04d" % i, "MANUAL FUERA DE TÉRMINO CON RES", "PERSONA MANO %d" % i,
                    "mano%d@gmail.com" % i, None, None, "05-oct-2026", None, "VIGENTE", "COMPARENDERA", "10-ene-2025",
                    "0123%04d" % i, cod, "15-ene-2025", "88%04d" % i, "20-feb-2025", "Res. 88%04d de 2025" % i,
                    "MANUAL FUERA DE TÉRMINO CON RES", None, "CEDULA DE CIUDADANIA", "51000%03d" % i, "", "", "", ""]
        malas = ["%s=%r (esperaba %r)" % (filas[0][j], f[j], e) for j, e in enumerate(esperado) if e is not None and f[j] != e]
        ok(not malas, "%02d: cada casilla llenada a mano sale en su columna, con el formato de la masiva del 02-10" % i + ("" if not malas else " → " + "; ".join(malas)))
    print("errores js:", err or "ninguno", "|", err2 or "ninguno")
    if err or err2: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
