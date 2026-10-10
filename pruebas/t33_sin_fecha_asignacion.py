# SOLO EL RADICADO, Y SIN FECHA DE ASIGNACIÓN
#
# Hay excepciones en que la usuaria solo tiene el número de radicado y NO puede dar la fecha de
# asignación ni lo demás. La app tiene que dejarla trabajarlo igual, sin inventar nada:
#   1. el radicado entra, se clasifica y se guarda sin fechas ni nombre (nada lo bloquea);
#   2. en la cola y en el formulario se ve que NO tiene fecha de asignación, y el término dice
#      "sin dato" (no se calcula con una fecha inventada);
#   3. lo trabajado sigue ahí al recargar, y también desde la ventana flotante;
#   4. la masiva lo trae, con las casillas de fecha VACÍAS (ninguna fecha inventada);
#   5. cerrar la semana lo cierra con los demás y queda en el historial.
# Datos inventados; ningún dato real de ciudadanos.
import sys, os, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
RAD = ["2026400000000%02d" % i for i in range(1, 3)]
TIRA2 = T.join(["11001000000046850002", "C02", "19/04/2025", "19/04/2025", "No",
  "CAMARAS SALVAVIDAS", "VIGENTE", "", "", "", "CEDULA DE CIUDADANIA", "520000002", "PERSONA DOS", "ABC002"])
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def guardados(p):
    return {r.get("radicado"): r for r in p.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));return JSON.parse(localStorage.getItem(k)||'[]')}")}
def guardar(p):
    p.click("#cc_save"); p.wait_for_timeout(500); B.confirmar_nombre(p); B.cerrar_alerta(p)

with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, "\n".join(RAD))
    # 01: petición oscura, sin nada más que el radicado
    B.ir_a(pag, RAD[0])
    B.escribir(pag, "#cc_formato", "T10"); B.escribir(pag, "#cc_comentario", "SOLO EL NUMERO")
    guardar(pag)
    # 02: con comparendo y resolución, pero sin fechas base ni nombre del solicitante
    B.ir_a(pag, RAD[1])
    B.pegar_tira(pag, TIRA2); B.escribir(pag, "#cc_formato", "T14")
    B.escribir(pag, "#cc_direccion", "dos@gmail.com"); B.escribir(pag, "#cc_res", "770002"); B.escribir(pag, "#cc_fechaRes", "26/07/2024")
    guardar(pag)
    g = guardados(pag)
    ok(g.get(RAD[0], {}).get("formato") == "T10" and g.get(RAD[0], {}).get("comentario") == "SOLO EL NUMERO",
       "01 se guarda clasificado sin fechas ni nombre → %r" % g.get(RAD[0], {}).get("formato"))
    ok(g.get(RAD[1], {}).get("formato") == "T14" and g.get(RAD[1], {}).get("res") == "770002",
       "02 se guarda clasificado sin fechas base → %r" % g.get(RAD[1], {}).get("formato"))
    ok(all(not g[r].get("fechaAsignacion") and not g[r].get("fechaRadicacion") for r in RAD), "ninguna fecha inventada en lo guardado")

    B.ir_a(pag, RAD[0])
    fila = pag.locator('#queuePanel .queue-item', has_text=RAD[0]).first.inner_text()
    ok("SIN FECHA DE ASIGNACIÓN" in fila.upper(), "la cola marca que no tiene fecha de asignación → %r" % fila.replace("\n", " | "))
    base = pag.locator("#baseFieldsView").inner_text()
    ok("sin fecha" in base.lower() and "sin dato" in base.lower(), "el formulario dice sin fecha y término sin dato → %r" % base.replace("\n", " | "))
    ok(pag.locator("#cc_priorityBadge").is_hidden(), "no se marca PRIORITARIO con una fecha que no existe")

    print("(flotante) se le añade algo desde la ventana flotante")
    flo = ctx.new_page(); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail", "prueba@gmail.com"); flo.fill("#loginPassword", "123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000); flo.wait_for_timeout(1500)
    if flo.locator("#captureEmptyVerTodos").is_visible(): flo.click("#captureEmptyVerTodos"); flo.wait_for_timeout(400)
    for _ in range(4):
        if RAD[0] in flo.locator("#cc_radicadoLabel").inner_text(): break
        flo.click("#cc_prev" if not flo.locator("#cc_prev").is_disabled() else "#cc_next"); flo.wait_for_timeout(300); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    ok(RAD[0] in flo.locator("#cc_radicadoLabel").inner_text(), "la flotante llega al 01")
    B.escribir(flo, "#cc_comentario", "SOLO EL NUMERO, DESDE LA FLOTANTE"); guardar(flo); flo.wait_for_timeout(1500)
    flo.close()

    pag.reload(wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail", "prueba@gmail.com"); pag.fill("#loginPassword", "123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000); pag.wait_for_timeout(1200)
    g = guardados(pag)
    ok(g.get(RAD[0], {}).get("comentario") == "SOLO EL NUMERO, DESDE LA FLOTANTE", "tras recargar, el 01 tiene lo de la flotante → %r" % g.get(RAD[0], {}).get("comentario"))
    ok(g.get(RAD[1], {}).get("res") == "770002", "y el 02 conserva su resolución")

    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    salida = os.path.join(os.environ.get("TMPDIR", "/tmp"), "t33_masiva.xlsx")
    with pag.expect_download(timeout=30000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count():
            rp = pag.locator("#preflightDialog").inner_text()
            print("   revisión previa:", rp[:400].replace("\n", " | "))
            ok("fecha de asignación está vacía" in rp, "la revisión previa avisa que la fecha de asignación sale en blanco")
            pag.click("#preflightProceed")
    dl.value.save_as(salida)
    ws = openpyxl.load_workbook(salida).active
    filas = [[("" if c is None else str(c)) for c in f] for f in ws.iter_rows(values_only=True)]
    cab, cuerpo = filas[0], {f[0]: f for f in filas[1:]}
    ok(sorted(cuerpo) == RAD, "la masiva trae los dos → " + str(sorted(k[-2:] for k in cuerpo)))
    for r in RAD:
        f = cuerpo.get(r)
        if f:
            ok(f[1] == "" and f[8] == "", "%s: fecha de radicación y de asignación VACÍAS en la masiva → %r / %r" % (r[-2:], f[1], f[8]))
            print("   fila %s:" % r[-2:], dict((h, v) for h, v in zip(cab, f) if v))

    pag.click("#cerrarSemanaNavBtn"); pag.wait_for_timeout(600); pag.click("#confirmOk"); pag.wait_for_timeout(2500)
    ok(pag.locator("#statTotal").inner_text().strip() == "0", "cerrar la semana los cierra → quedan %s" % pag.locator("#statTotal").inner_text())
    hist = pag.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_historial_v1::'));return (JSON.parse(localStorage.getItem(k)||'[]')).reduce((n,h)=>n+(h.records||[]).length,0)}")
    ok(hist == 2, "y quedan los 2 en el historial → %d" % hist)
    print("errores js:", err or "ninguno", "|", err2 or "ninguno")
    if err or err2: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
