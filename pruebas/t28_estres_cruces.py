# ESTRÉS: ¿SE CRUZA INFORMACIÓN ENTRE RADICADOS?
#
# La usuaria trabaja rápido: escribe en una casilla y salta al siguiente radicado sin esperar,
# con la principal y la flotante abiertas a la vez. Esta prueba hace eso mismo muchas veces, con
# una secuencia pseudoaleatoria FIJA (siempre la misma, para que una falla se pueda repetir), y
# al final exige dos cosas de cada radicado:
#   1. que tenga EXACTAMENTE lo último que se le escribió (no se perdió nada), y
#   2. que no tenga nada escrito para OTRO radicado (no se cruzó nada).
# Cada valor lleva dentro el número del radicado al que se le escribió, así que un cruce se ve
# en el acto. La principal trabaja los radicados 1-4 y la flotante los 5-8: cada radicado tiene
# un solo dueño, y así "lo último que se le escribió" no es ambiguo.
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
N = 8
RAD = ["2026200000000%02d" % i for i in range(1, N + 1)]
def tira(i): return T.join(["1100100000004685%04d" % i, "C02", "19/04/2025", "19/04/2025", "No",
  "CAMARAS SALVAVIDAS", "VIGENTE", "", "", "", "CEDULA DE CIUDADANIA", "520000%03d" % i, "PERSONA %d" % i, "ABC%03d" % i])
BLOQUE = "\n".join("%s\t01/09/2026\t03/09/2026\tPERSONA %d" % (r, i + 1) for i, r in enumerate(RAD))
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)

CAMPOS = ["#cc_comentario", "#cc_res", "#cc_direccion"]
def valor(campo, i, n):
    if campo == "#cc_res": return "%d%04d" % (i, n)                 # el radicado va al principio
    if campo == "#cc_direccion": return "r%dv%d@gmail.com" % (i, n)
    return "RAD%d-V%d" % (i, n)

def ir(pag, rad):
    if "flotante=1" in pag.url:
        # En la flotante no hay cola ni buscador: Siguiente / Anterior, como ahí mismo.
        # (B.ir_a_compacto no sirve aquí: al llegar al final rebota entre los dos últimos.)
        for _ in range(N + 2):
            if pag.locator("#captureEmptyVerTodos").is_visible():
                pag.click("#captureEmptyVerTodos"); pag.wait_for_timeout(400); B.cerrar_alerta(pag)
            lab = pag.locator("#cc_radicadoLabel").inner_text()
            if not lab.strip()[-2:].isdigit(): print("   etiqueta rara:", repr(lab)); return False
            if rad in lab: return True
            actual = int(lab.strip()[-2:]); destino = int(rad[-2:])
            pag.click("#cc_next" if destino > actual else "#cc_prev")
            pag.wait_for_timeout(250); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
        return rad in pag.locator("#cc_radicadoLabel").inner_text()
    B.ir_a(pag, rad)
    B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    return rad in pag.locator("#cc_radicadoLabel").inner_text()

with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag); B.importar(pag, BLOQUE)
    # Todo clasificado primero: así ningún aviso de "falta el formato" frena los saltos.
    for i, r in enumerate(RAD, 1):
        B.ir_a(pag, r); B.pegar_tira(pag, tira(i))
        B.escribir(pag, "#cc_formato", "T14"); B.escribir(pag, "#cc_direccion", "r%dv0@gmail.com" % i)
        B.escribir(pag, "#cc_res", "%d0000" % i); B.escribir(pag, "#cc_fechaRes", "26/07/2024")
        B.escribir(pag, "#cc_comentario", "RAD%d-V0" % i)
        pag.click("#cc_save"); pag.wait_for_timeout(350); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(1500)

    flo = ctx.new_page(); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail", "prueba@gmail.com"); flo.fill("#loginPassword", "123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    flo.wait_for_timeout(1500)

    esperado = {}
    for i in range(1, N + 1):
        esperado[(i, "#cc_comentario")] = "RAD%d-V0" % i
        esperado[(i, "#cc_res")] = "%d0000" % i
        esperado[(i, "#cc_direccion")] = "r%dv0@gmail.com" % i

    rnd = random.Random(int(os.environ.get("SEMILLA", "20261010")))
    navegacion_fallida = 0
    for paso in range(1, 61):
        enFlo = rnd.random() < 0.5
        p = flo if enFlo else pag
        i = rnd.randint(5, 8) if enFlo else rnd.randint(1, 4)
        if not ir(p, RAD[i - 1]):
            navegacion_fallida += 1
            print("   no llegó a", RAD[i-1][-2:], "| está en", p.locator("#cc_radicadoLabel").inner_text() if p.locator("#cc_radicadoLabel").is_visible() else "(formulario oculto)",
                  "| next:", p.locator("#cc_next").is_disabled(), "prev:", p.locator("#cc_prev").is_disabled(),
                  "| diálogos:", p.evaluate("()=>[...document.querySelectorAll('dialog[open]')].map(d=>d.id)"))
            continue
        campo = rnd.choice(CAMPOS)
        v = valor(campo, i, paso)
        p.fill(campo, v); p.dispatch_event(campo, "input")
        esperado[(i, campo)] = v
        modo = rnd.choice(["salta", "salta", "espera", "guarda", "tab"])
        if os.environ.get("VERBOSO"): print("   paso %d: %s rad %d %s = %s → %s" % (paso, "FLO" if enFlo else "PRI", i, campo, v, modo))
        if modo == "espera": p.wait_for_timeout(rnd.choice([300, 900, 1500]))
        elif modo == "guarda":
            p.click("#cc_save"); p.wait_for_timeout(250); B.confirmar_nombre(p); B.cerrar_alerta(p)
        elif modo == "tab": p.keyboard.press("Tab"); p.wait_for_timeout(100)
        # "salta": nada, el siguiente paso navega de inmediato
    pag.wait_for_timeout(2500); flo.wait_for_timeout(500)
    ok(navegacion_fallida == 0, "todas las navegaciones llegaron a su radicado (%d fallidas)" % navegacion_fallida)

    guardado = pag.evaluate("""()=>{
      const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));
      return JSON.parse(localStorage.getItem(k)||'[]');
    }""")
    porRad = {r.get("radicado"): r for r in guardado}
    clave = {"#cc_comentario": "comentario", "#cc_res": "res", "#cc_direccion": "direccion"}
    perdidos, cruzados = [], []
    for (i, campo), v in sorted(esperado.items()):
        real = str(porRad.get(RAD[i - 1], {}).get(clave[campo], ""))
        if real != v: perdidos.append("%s %s: esperaba %r, hay %r" % (RAD[i - 1][-2:], clave[campo], v, real))
    for i, r in enumerate(RAD, 1):
        rec = porRad.get(r, {})
        for c in ("comentario", "res", "direccion"):
            s = str(rec.get(c, ""))
            dueno = None
            if c == "comentario" and s.startswith("RAD"): dueno = int(s[3:s.index("-")])
            if c == "direccion" and s.startswith("r"): dueno = int(s[1:s.index("v")])
            if c == "res" and s: dueno = int(s[0])
            if dueno is not None and dueno != i: cruzados.append("%s %s = %r (es del %d)" % (r[-2:], c, s, dueno))
        if rec.get("comparendoCompleto") != "1100100000004685%04d" % i:
            cruzados.append("%s comparendo = %r" % (r[-2:], rec.get("comparendoCompleto")))
    ok(not cruzados, "ningún radicado tiene datos de otro" + ("" if not cruzados else " → " + "; ".join(cruzados[:8])))
    ok(not perdidos, "ningún dato escrito se perdió" + ("" if not perdidos else " → " + "; ".join(perdidos[:8])))
    print("errores js:", err or "ninguno", "|", err2 or "ninguno")
    if err or err2: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
