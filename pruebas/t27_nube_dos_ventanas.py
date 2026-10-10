# LA NUBE CON DOS VENTANAS ABIERTAS (principal + flotante), contra un servidor que se porta como
# la Supabase de verdad.
#
# Por qué existe: hasta el 10-10-2026 el servidor de mentira ignoraba el filtro
# ?actualizado=eq.<marca> con el que cada ventana se protege de pisar a la otra. Con la Supabase
# real ese filtro SÍ se aplica: en cuanto una ventana sube, la otra queda con una marca vieja, su
# siguiente subida no cambia nada, y esa ventana se queda en "conflicto" y deja de subir a la nube
# para el resto de la sesión. Lo trabajado ahí queda solo en este navegador. Ninguna prueba lo vio
# porque el servidor de mentira aceptaba todo.
#
# Lo que se exige aquí es lo que la usuaria necesita: trabajar en las dos ventanas a la vez, y
# que TODO lo de las dos llegue a la nube, sin avisos de conflicto y sin que un radicado reciba
# datos de otro. Y que entrando desde un navegador limpio (otro computador) esté todo.
import sys, os, json, hashlib, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
CORREO = "prueba@gmail.com"
def tira(i): return T.join(["1100100000004685%04d" % i, "C02", "19/04/2025", "19/04/2025", "No",
  "CAMARAS SALVAVIDAS", "VIGENTE", "", "", "", "CEDULA DE CIUDADANIA", "520000%03d" % i, "PERSONA %d" % i, "ABC%03d" % i])
RAD = ["2026100000000%02d" % i for i in range(1, 5)]
BLOQUE = "\n".join("%s\t01/09/2026\t03/09/2026\tPERSONA %d" % (r, i + 1) for i, r in enumerate(RAD))
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)

def uid(correo):
    h = hashlib.md5(correo.strip().lower().encode()).hexdigest()
    return "%s-%s-%s-%s-%s" % (h[0:8], h[8:12], h[12:16], h[16:20], h[20:32])
def nube():
    url = "http://127.0.0.1:9870/rest/v1/radicados_datos?usuario_id=eq." + uid(CORREO)
    filas = json.loads(urllib.request.urlopen(url, timeout=5).read().decode())
    recs = (filas[0].get("records") if filas else None) or []
    return {r.get("radicado"): r for r in recs}

def clasificar(pag, rad, i, comentario):
    B.ir_a(pag, rad); B.pegar_tira(pag, tira(i))
    B.escribir(pag, "#cc_formato", "T14"); B.escribir(pag, "#cc_direccion", "p%d@gmail.com" % i)
    B.escribir(pag, "#cc_res", "13687%02d" % i); B.escribir(pag, "#cc_fechaRes", "26/07/2024")
    B.escribir(pag, "#cc_comentario", comentario)
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

def en_conflicto(pag):
    st = pag.locator("#saveStatus").inner_text()
    banner = pag.locator("#dataSafetyBanner")
    txt = banner.inner_text() if banner.is_visible() else ""
    return ("otro lugar" in st.lower()) or ("OTRO lugar" in txt) or ("bloque" in st.lower())

with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag); B.importar(pag, BLOQUE)
    clasificar(pag, RAD[0], 1, "UNO EN LA PRINCIPAL")
    pag.wait_for_timeout(2500)
    ok(nube().get(RAD[0], {}).get("comentario") == "UNO EN LA PRINCIPAL", "lo de la principal llega a la nube")

    print("(a) se abre la flotante y se trabaja en las dos, en radicados distintos")
    flo = ctx.new_page(); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail", CORREO); flo.fill("#loginPassword", "123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    flo.wait_for_timeout(1500)
    # La flotante abre en el primer pendiente, que es el 002: ese se trabaja ahí.
    ok(RAD[1] in flo.locator("#cc_radicadoLabel").inner_text(),
       "la flotante abre en el 002 → " + flo.locator("#cc_radicadoLabel").inner_text())
    B.pegar_tira(flo, tira(2)); B.escribir(flo, "#cc_formato", "T14")
    B.escribir(flo, "#cc_comentario", "DOS EN LA FLOTANTE")
    flo.click("#cc_save"); flo.wait_for_timeout(500); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    flo.wait_for_timeout(2500)
    clasificar(pag, RAD[2], 3, "TRES EN LA PRINCIPAL")
    pag.wait_for_timeout(2500)
    # y otra vez la flotante, ya después de que subió la principal
    B.escribir(flo, "#cc_res", "999")
    flo.click("#cc_save"); flo.wait_for_timeout(500); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    flo.wait_for_timeout(2500)
    clasificar(pag, RAD[3], 4, "CUATRO EN LA PRINCIPAL")
    pag.wait_for_timeout(3000)
    ok(RAD[1] in flo.locator("#cc_radicadoLabel").inner_text(), "la flotante sigue en el 002")

    ok(not en_conflicto(pag), "la principal NO queda en conflicto → " + repr(pag.locator("#saveStatus").inner_text()))
    ok(not en_conflicto(flo), "la flotante NO queda en conflicto → " + repr(flo.locator("#saveStatus").inner_text()))

    n = nube()
    print("(b) la nube tiene lo de las dos ventanas")
    ok(n.get(RAD[0], {}).get("comentario") == "UNO EN LA PRINCIPAL", "001 → " + repr(n.get(RAD[0], {}).get("comentario")))
    ok(n.get(RAD[1], {}).get("comentario") == "DOS EN LA FLOTANTE", "002 comentario (flotante) → " + repr(n.get(RAD[1], {}).get("comentario")))
    ok(n.get(RAD[1], {}).get("res") == "999", "002 resolución (flotante, después) → " + repr(n.get(RAD[1], {}).get("res")))
    ok(n.get(RAD[2], {}).get("comentario") == "TRES EN LA PRINCIPAL", "003 → " + repr(n.get(RAD[2], {}).get("comentario")))
    ok(n.get(RAD[3], {}).get("comentario") == "CUATRO EN LA PRINCIPAL", "004 → " + repr(n.get(RAD[3], {}).get("comentario")))
    print("(c) ningún radicado recibió datos de otro")
    for i, r in enumerate(RAD):
        rec = n.get(r, {})
        if rec.get("comparendoCompleto"):
            ok(rec.get("comparendoCompleto") == "1100100000004685%04d" % (i + 1),
               r + " conserva SU comparendo → " + repr(rec.get("comparendoCompleto")))
    print("(d) desde un navegador limpio (otro computador) está todo")
    nav2, ctx2, p2, e3 = B.abrir(pw)
    B.entrar(p2, limpio=False); p2.wait_for_timeout(1200)
    for r, esperado in ((RAD[0], "UNO EN LA PRINCIPAL"), (RAD[1], "DOS EN LA FLOTANTE"),
                        (RAD[2], "TRES EN LA PRINCIPAL"), (RAD[3], "CUATRO EN LA PRINCIPAL")):
        B.ir_a(p2, r)
        ok(p2.input_value("#cc_comentario") == esperado, r + " en el otro computador → " + repr(p2.input_value("#cc_comentario")))
    nav2.close()

    print("(e) cerrar la semana justo después de que subió la flotante")
    B.escribir(flo, "#cc_comentario", "DOS EN LA FLOTANTE, OTRA VEZ")
    flo.click("#cc_save"); flo.wait_for_timeout(500); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    flo.wait_for_timeout(2500)
    pag.click("#cerrarSemanaNavBtn"); pag.wait_for_timeout(600)
    pag.click("#confirmOk"); pag.wait_for_timeout(4000)
    filas = json.loads(urllib.request.urlopen("http://127.0.0.1:9870/rest/v1/radicados_datos?usuario_id=eq." + uid(CORREO), timeout=5).read().decode())
    recs = (filas[0].get("records") if filas else None) or []
    hist = (filas[0].get("history") if filas else None) or []
    ok(len(recs) == 0, "en la nube la lista quedó vacía (no resucita lo archivado) → %d radicados" % len(recs))
    archivados = sum(len(h.get("records") or []) for h in hist)
    ok(archivados == 4, "y los 4 quedaron en el historial de la nube → %d" % archivados)
    ok(not en_conflicto(pag), "la principal no quedó en conflicto ni bloqueada → " + repr(pag.locator("#saveStatus").inner_text()))
    print("errores js:", err or "ninguno", "|", err2 or "ninguno")
    if err or err2: fallos.append("errores de JavaScript")
    nav.close()

print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
