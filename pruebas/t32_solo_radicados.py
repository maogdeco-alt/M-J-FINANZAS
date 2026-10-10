# SOLO LOS RADICADOS, NADA MÁS
#
# Hay semanas en que la usuaria no tiene extracto: solo la lista de números de radicado, y todo
# lo demás (fechas, nombre, dirección, comparendo, resolución) lo llena a mano. Esta prueba hace
# eso mismo por la interfaz y exige que:
#   1. el bloque de solo números entra completo, sin líneas rechazadas;
#   2. lo escrito a mano queda guardado en SU radicado (ni se pierde ni cae en otro);
#   3. la masiva sale con esas filas y con lo escrito a mano en sus columnas;
#   4. el AGENDAMIENTO no va en la masiva (va en su plantilla).
# Datos inventados; ningún dato real de ciudadanos.
import sys, os, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
RAD = ["2026300000000%02d" % i for i in range(1, 5)]
def tira(i): return T.join(["1100100000004685%04d" % i, "C02", "19/04/2025", "19/04/2025", "No",
  "CAMARAS SALVAVIDAS", "VIGENTE", "", "", "", "CEDULA DE CIUDADANIA", "520000%03d" % i, "PERSONA %d" % i, "ABC%03d" % i])
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)

def a_mano(pag, i, formato, con_comparendo=True):
    B.ir_a(pag, RAD[i - 1])
    ok(pag.locator("#cc_fechaAsignacion").is_visible(), "%02d: las casillas de fechas y nombre aparecen abiertas, sin buscarlas" % i)
    if not pag.locator("#cc_fechaAsignacion").is_visible(): pag.click("#baseEditToggle")
    B.escribir(pag, "#cc_fechaRadicacion", "0%d/10/2026" % i)
    B.escribir(pag, "#cc_fechaAsignacion", "05/10/2026")
    B.escribir(pag, "#cc_nombre", "PERSONA A MANO %d" % i)
    if con_comparendo: B.pegar_tira(pag, tira(i))
    B.escribir(pag, "#cc_formato", formato)
    B.escribir(pag, "#cc_direccion", "mano%d@gmail.com" % i)
    if formato in ("T14", "T1"):
        B.escribir(pag, "#cc_res", "77%04d" % i); B.escribir(pag, "#cc_fechaRes", "26/07/2024")
    B.escribir(pag, "#cc_comentario", "ESCRITO A MANO %d" % i)
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, "\n".join(RAD))
    ok(pag.locator("#statTotal").inner_text().strip() == "4", "entran los 4 radicados de solo números → " + pag.locator("#statTotal").inner_text())
    guardado = pag.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));return JSON.parse(localStorage.getItem(k)||'[]')}")
    ok(sorted(r.get("radicado") for r in guardado) == RAD, "y quedan guardados con su número exacto")
    ok(all(not r.get("nombre") and not r.get("fechaAsignacion") for r in guardado), "sin inventar nombre ni fechas")
    if len(guardado) != 4:
        nav.close(); print("\nRESULTADO:", len(fallos), "FALLA(S)"); sys.exit(1)

    a_mano(pag, 1, "T14"); a_mano(pag, 2, "T10", con_comparendo=False)
    a_mano(pag, 3, "T14"); a_mano(pag, 4, "AGENDAMIENTO")
    pag.wait_for_timeout(1500)

    # se recarga la página: lo escrito a mano tiene que seguir ahí, en su radicado
    pag.reload(wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail", "prueba@gmail.com"); pag.fill("#loginPassword", "123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000); pag.wait_for_timeout(1200)
    guardado = {r.get("radicado"): r for r in pag.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));return JSON.parse(localStorage.getItem(k)||'[]')}")}
    for i, r in enumerate(RAD, 1):
        g = guardado.get(r, {})
        ok(g.get("nombre") == "PERSONA A MANO %d" % i and g.get("comentario") == "ESCRITO A MANO %d" % i
           and g.get("fechaAsignacion") == "05/10/2026" and g.get("fechaRadicacion") == "0%d/10/2026" % i,
           "%s conserva lo escrito a mano tras recargar → %r / %r / %r" % (r[-2:], g.get("nombre"), g.get("comentario"), g.get("fechaRadicacion")))

    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    salida = os.path.join(os.environ.get("TMPDIR", "/tmp"), "t32_masiva.xlsx")
    with pag.expect_download(timeout=30000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count():
            print("   aviso antes de descargar:", pag.locator("#preflightDialog").inner_text()[:400].replace("\n", " | "))
            pag.click("#preflightProceed")
    dl.value.save_as(salida)
    ws = openpyxl.load_workbook(salida).active
    filas = [[("" if c is None else str(c)) for c in f] for f in ws.iter_rows(values_only=True)]
    cab, cuerpo = filas[0], {f[0]: f for f in filas[1:]}
    ok(sorted(cuerpo) == RAD[:3], "la masiva trae el 01, 02 y 03, y NO el agendamiento → " + str(sorted(k[-2:] for k in cuerpo)))
    for i in (1, 2, 3):
        f = cuerpo.get(RAD[i - 1])
        if not f: continue
        d = dict(zip(cab, f))
        # Con comparendo, el destinatario de la masiva es el infractor de Fénix (así salió la
        # masiva buena del 02-10-2026); sin comparendo (T10), el nombre escrito a mano.
        quien = "PERSONA A MANO %d" % i if i == 2 else "PERSONA %d" % i
        ok(f[4] == quien, "%02d destinatario en la masiva → %r" % (i, f[4]))
        ok(f[5] == "mano%d@gmail.com" % i, "%02d dirección en la masiva → %r" % (i, f[5]))
        ok(f[1] == "0%d-oct-2026" % i, "%02d fecha de radicación en la masiva → %r" % (i, f[1]))
        ok(f[8] == "05-oct-2026", "%02d fecha de asignación en la masiva → %r" % (i, f[8]))
        if i != 2: ok(f[2] == "4685%04d" % i, "%02d comparendo (últimos 8) → %r" % (i, f[2]))
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
