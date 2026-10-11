# PEGAR LA TIRA DE FÉNIX EN UN RADICADO QUE ENTRÓ SOLO CON EL NÚMERO
#
# Lo que más le facilita el trabajo es pegar la línea completa de Fénix: tiene que seguir llenando
# sola las casillas del comparendo, también en un radicado cargado solo con el número, en la
# principal y en la flotante. Y si ella ya había escrito algo a mano y la línea trae otra cosa,
# la app no lo reemplaza en silencio: se lo muestra y ella elige. Datos inventados.
import sys, os, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
RAD = ["2026600000000%02d" % i for i in range(1, 6)]
def tira(i, extra_dir=False):
    cols = ["1100100000004685%04d" % i, "C02", "19/04/2025", "21/04/2025", "No", "CAMARAS SALVAVIDAS", "VIGENTE",
            "", "", "", "CEDULA DE CIUDADANIA", "520000%03d" % i, "PERSONA %d" % i]
    if extra_dir: cols.append("CALLE FALSA 123")
    return T.join(cols + ["ABC%03d" % i])
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def guardar(p):
    p.click("#cc_save"); p.wait_for_timeout(500); B.confirmar_nombre(p); B.cerrar_alerta(p)
def casillas(p):
    return {k: p.input_value("#m_" + k) for k in ("comparendoCompleto", "cod", "imposicion", "notificacion", "medio", "estado", "placa")}
def registro(p, rad):
    return {r.get("radicado"): r for r in p.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));return JSON.parse(localStorage.getItem(k)||'[]')}")}.get(rad, {})
LLENAS = lambda i: {"comparendoCompleto": "1100100000004685%04d" % i, "cod": "C02", "imposicion": "19/04/2025",
                    "notificacion": "21/04/2025", "medio": "CAMARAS SALVAVIDAS", "estado": "VIGENTE", "placa": "ABC%03d" % i}

with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, "\n".join(RAD))
    print("(a) principal: se pega la tira en un radicado de solo número")
    B.ir_a(pag, RAD[0]); B.pegar_tira(pag, tira(1))
    ok(casillas(pag) == LLENAS(1), "las casillas del comparendo se llenan solas → %s" % casillas(pag))
    B.escribir(pag, "#cc_formato", "T14"); B.escribir(pag, "#cc_res", "770001"); B.escribir(pag, "#cc_fechaRes", "26/07/2024")
    guardar(pag)
    r = registro(pag, RAD[0])
    ok(r.get("cod") == "C02" and r.get("tipoId") == "CEDULA DE CIUDADANIA" and r.get("nombreF") == "PERSONA 1",
       "y queda guardado lo de la tira → %r / %r / %r" % (r.get("cod"), r.get("tipoId"), r.get("nombreF")))

    print("(d) después de pegar, corregir una casilla a mano no borra el documento")
    B.ir_a(pag, RAD[4]); B.pegar_tira(pag, tira(5, extra_dir=True))
    ok(pag.input_value("#m_placa") == "ABC005", "con 15 columnas la placa es la placa → %r" % pag.input_value("#m_placa"))
    B.escribir(pag, "#m_estado", "VIGENTE "); B.escribir(pag, "#m_cod", "C29")
    B.escribir(pag, "#cc_formato", "T14"); guardar(pag)
    r = registro(pag, RAD[4])
    ok(r.get("tipoId") == "CEDULA DE CIUDADANIA" and r.get("idNum") == "520000005" and r.get("cod") == "C29" and r.get("placa") == "ABC005",
       "documento, placa y la corrección quedan → %r / %r / %r / %r" % (r.get("tipoId"), r.get("idNum"), r.get("cod"), r.get("placa")))

    print("(c) lo escrito a mano y una tira que trae otra cosa")
    B.ir_a(pag, RAD[2])
    B.escribir(pag, "#m_comparendoCompleto", "11001000000046850003"); B.escribir(pag, "#m_cod", "C99")
    B.pegar_tira(pag, tira(3))
    ok(pag.locator("#tiraDistintaDialog[open]").count() == 1, "la app lo dice en su propio diálogo, no en silencio")
    txt = pag.locator("#tiraDistintaLista").inner_text() if pag.locator("#tiraDistintaDialog[open]").count() else ""
    ok("C99" in txt and "C02" in txt and "N.° de comparendo" not in txt,
       "muestra solo lo distinto (infracción: C99 contra C02) → %r" % txt)
    if pag.locator("#tiraDistintaDialog[open]").count(): pag.click("#tiraDistintaMios")
    ok(pag.input_value("#m_cod") == "C99" and pag.input_value("#m_estado") == "VIGENTE",
       "«Dejar lo que escribí» deja C99 y conserva lo demás de la tira → %r / %r" % (pag.input_value("#m_cod"), pag.input_value("#m_estado")))
    B.escribir(pag, "#cc_formato", "T14"); guardar(pag)
    r = registro(pag, RAD[2])
    ok(r.get("cod") == "C99" and r.get("medio") == "CAMARAS SALVAVIDAS", "y así se guarda → %r / %r" % (r.get("cod"), r.get("medio")))
    B.ir_a(pag, RAD[3])
    B.escribir(pag, "#m_cod", "C99"); B.pegar_tira(pag, tira(4))
    if pag.locator("#tiraDistintaDialog[open]").count(): pag.click("#tiraDistintaFenix")
    B.escribir(pag, "#cc_formato", "T14"); guardar(pag)
    ok(registro(pag, RAD[3]).get("cod") == "C02", "«Usar lo de Fénix» deja C02 → %r" % registro(pag, RAD[3]).get("cod"))
    print("   (y pegar otra tira encima de una tira pegada no pregunta nada)")
    B.ir_a(pag, RAD[0]); B.pegar_tira(pag, tira(1).replace("C02", "C03"))
    ok(pag.locator("#tiraDistintaDialog[open]").count() == 0, "re-pegar una tira no abre el diálogo")
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    B.pegar_tira(pag, tira(1)); guardar(pag)

    print("(b) flotante: se pega la tira en otro radicado de solo número")
    flo = ctx.new_page(); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail", "prueba@gmail.com"); flo.fill("#loginPassword", "123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000); flo.wait_for_timeout(1500)
    if flo.locator("#captureEmptyVerTodos").is_visible(): flo.click("#captureEmptyVerTodos"); flo.wait_for_timeout(400)
    for _ in range(6):
        if RAD[1] in flo.locator("#cc_radicadoLabel").inner_text(): break
        lab = flo.locator("#cc_radicadoLabel").inner_text()
        flo.click("#cc_next" if int(lab.strip()[-2:]) < 2 else "#cc_prev"); flo.wait_for_timeout(300); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    ok(RAD[1] in flo.locator("#cc_radicadoLabel").inner_text(), "la flotante está en el 02")
    B.pegar_tira(flo, tira(2))
    ok(casillas(flo) == LLENAS(2), "en la flotante también se llenan solas → %s" % casillas(flo))
    B.escribir(flo, "#cc_formato", "T14"); B.escribir(flo, "#cc_res", "770002"); B.escribir(flo, "#cc_fechaRes", "26/07/2024")
    guardar(flo); flo.wait_for_timeout(1500); flo.close()
    pag.wait_for_timeout(800)
    B.ir_a(pag, RAD[1])
    ok(casillas(pag) == LLENAS(2), "y la principal ve lo que se pegó en la flotante → %s" % casillas(pag))

    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    salida = os.path.join(os.environ.get("TMPDIR", "/tmp"), "t36_masiva.xlsx")
    with pag.expect_download(timeout=30000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightProceed")
    dl.value.save_as(salida)
    ws = openpyxl.load_workbook(salida).active
    cuerpo = {f[0]: [("" if c is None else str(c)) for c in f] for f in ws.iter_rows(min_row=2, values_only=True)}
    for i in (1, 2):
        f = cuerpo.get(RAD[i - 1], [""] * 27)
        ok(f[2] == "4685%04d" % i and f[13] == f[2] and f[11] == "CAMARAS SALVAVIDAS" and f[12] == "19-abr-2025" and f[15] == "21-abr-2025"
           and f[14] == "C02" and f[21] == "CEDULA DE CIUDADANIA" and f[4] == "PERSONA %d" % i,
           "%02d: la masiva sale con los datos de la tira en sus columnas → %s" % (i, f[:23]))
    print("errores js:", err or "ninguno", "|", err2 or "ninguno")
    if err or err2: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
