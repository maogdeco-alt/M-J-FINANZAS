# UNA JORNADA DE 60 RADICADOS CON LAS DOS VENTANAS A LA VEZ (04-11-2026)
#
# Pedido de la usuaria antes de cargar 60 radicados (una jornada de más de 6 horas): "que bajo
# ninguna circunstancia, ni en la ventana flotante, ni en la ventana principal, se vaya a perder o
# a trastocar información" y que al completar un radicado se diga en el acto qué falta, no al final.
#
# Se hace una jornada entera por la interfaz, como ella:
#   · 60 radicados; la principal trabaja del 1 al 30 y la flotante del 31 al 60, casilla por casilla
#     y ALTERNANDO entre las dos ventanas (las dos escriben a la vez todo el tiempo).
#   · Mitad de jornada: se recarga la principal; y la flotante se CIERRA DE GOLPE (como si se
#     colgara: sin eventos de cierre) justo después de escribir un correo, sin guardar, y se vuelve a abrir.
#   · Cada radicado se intenta completar primero con un dato faltante: la app tiene que frenar en
#     ese mismo radicado y decir qué falta.
# Al final se exige: cada radicado tiene EXACTAMENTE lo suyo (nada perdido) y nada de otro radicado
# (nada cruzado); 60 LISTOS; la masiva sale con una fila por radicado que va a la masiva, cada una
# con sus propios datos; y un computador vacío que entra con la misma cuenta trae los 60 de la nube.
# Datos inventados.
import sys, os, json, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
N = 60
RAD = ["2026700000%05d" % (900 + i) for i in range(1, N + 1)]   # 15 dígitos
FORMATOS = ["T6", "T5", "T1", "T11", "T10", "AGENDAMIENTO", "DEVUELTO", "T6", "T5", "T1"]
def formato(i): return FORMATOS[(i - 1) % len(FORMATOS)]
def nombre(i): return "PERSONA NUMERO %d PRUEBA" % i
def correo(i): return "r%d.persona@gmail.com" % i
def comparendo(i): return "1100100000004%07d" % (8000000 + i)     # 20 dígitos
def doc(i): return "52%06d" % i
def res(i): return "77%05d" % i
def placa(i): return "QX%04d" % i
def tira(i):
    medio = "COMPARENDERA" if formato(i) == "T1" else "CAMARAS SALVAVIDAS"
    return T.join([comparendo(i), "C29", "19/04/2025", "25/04/2025", "No", medio, "VIGENTE", "", "", "",
                   "CEDULA DE CIUDADANIA", doc(i), nombre(i), placa(i)])
BLOQUE = "\n".join("%s\t02/11/2026\t03/11/2026\t%s" % (RAD[i - 1], nombre(i)) for i in range(1, N + 1))
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def caja(p): return p.inner_text("#avisoImperativas") if p.locator("#avisoImperativas:visible").count() else ""
def guardar_siguiente(p):
    p.click("#cc_saveNext"); p.wait_for_timeout(500); B.confirmar_nombre(p); p.wait_for_timeout(300)

frenos_mal = []      # radicados en que la app NO frenó con un dato faltante
pendientes_raros = []

def trabajar(p, i, flotante):
    """Un radicado entero, como generador: cada 'yield' le pasa el turno a la otra ventana."""
    f = formato(i); r = RAD[i - 1]
    if not flotante:
        B.ir_a(p, r)
    yield
    if r not in p.inner_text("#cc_radicadoLabel"):
        frenos_mal.append("%s: la ventana no estaba en el radicado (%s)" % (r, p.inner_text("#cc_radicadoLabel")))
        return
    B.escribir(p, "#cc_formato", f); yield
    if f == "DEVUELTO":
        guardar_siguiente(p); yield; return
    if f != "T10":
        B.pegar_tira(p, tira(i)); yield
    if f in ("T1", "T5", "T11"):
        B.escribir(p, "#cc_res", res(i)); B.escribir(p, "#cc_fechaRes", "15/05/2025"); yield
    if f == "AGENDAMIENTO":
        p.check("#cc_pruebasSi"); p.wait_for_timeout(150); yield
    # Primero SIN correo: tiene que frenar aquí mismo y decir qué falta.
    guardar_siguiente(p)
    if r not in p.inner_text("#cc_radicadoLabel") or "correo" not in caja(p).lower():
        frenos_mal.append("%s (%s): sin correo no frenó o no lo dijo → %r" % (r, f, caja(p)[:100]))
    yield
    B.escribir(p, "#cc_direccion", correo(i)); yield
    guardar_siguiente(p)
    if r in p.inner_text("#cc_radicadoLabel") and "LISTO" not in caja(p).split("\n")[0]:
        pendientes_raros.append("%s (%s, %s) no avanzó al guardar completo: caja=%r toast=%r" % (r, f, "flotante" if flotante else "principal", caja(p)[:200], B.toast(p)[:120]))
        if p.locator("#faltasDejarPendiente:visible").count():
            p.click("#faltasDejarPendiente"); p.wait_for_timeout(500)
        elif not p.locator("#cc_next").is_disabled():
            p.click("#cc_next"); p.wait_for_timeout(500)
    yield

with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag); B.importar(pag, BLOQUE)
    ok(pag.inner_text("#statPend") == str(N), "entran los %d radicados, todos PENDIENTES → %s" % (N, pag.inner_text("#statPend")))

    def abrir_flotante():
        flo = ctx.new_page(); flo.set_viewport_size({"width": 620, "height": 540})
        flo.on("pageerror", lambda e: err.append("flotante pageerror: " + str(e)))
        flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
        B.entrar_en(flo); flo.wait_for_timeout(1200)
        return flo
    flo = abrir_flotante()
    ok(B.ir_a_compacto(flo, RAD[30], vueltas=45), "la flotante llega al radicado 31")

    principal = [i for i in range(1, 31)]
    flotante = [i for i in range(31, N + 1)]
    gp = None; gf = None; hechos_p = 0; hechos_f = 0
    recargada = False; cerrada = False
    while principal or flotante or gp or gf:
        if gp is None and principal:
            gp = trabajar(pag, principal.pop(0), False)
        if gp is not None:
            try: next(gp)
            except StopIteration:
                gp = None; hechos_p += 1
                if hechos_p == 12 and not recargada:
                    recargada = True
                    pag.reload(wait_until="domcontentloaded"); B.entrar_en(pag); pag.wait_for_timeout(1200)
        if gf is None and flotante:
            i = flotante.pop(0)
            if i == 41 and not cerrada:   # el 41 es T6
                # La flotante se cierra de golpe justo después de escribir el correo, sin guardar.
                cerrada = True
                r = RAD[i - 1]
                ok(r in flo.inner_text("#cc_radicadoLabel"), "la flotante está en el radicado 41")
                B.escribir(flo, "#cc_formato", "T6"); B.pegar_tira(flo, tira(i))
                flo.fill("#cc_direccion", correo(i)); flo.dispatch_event("#cc_direccion", "input")
                flo.close()                      # antes del autoguardado de 1,2 s
                pag.wait_for_timeout(800)
                x = [y for y in pag.evaluate("""()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));
                      return JSON.parse(localStorage.getItem(k)||'[]')}""") if y.get("radicado") == r][0]
                ok(x.get("direccion") == correo(i) and x.get("formato") == "T6" and comparendo(i) in json.dumps(x),
                   "lo escrito en la flotante justo antes de cerrarla de golpe quedó guardado → %r" % {k: x.get(k) for k in ("formato", "direccion")})
                flo = abrir_flotante()
                # Ya está LISTO, así que la flotante (que muestra los pendientes) sigue con el 46.
                ok(B.ir_a_compacto(flo, RAD[i], vueltas=45), "al volver a abrir la flotante se sigue con el 42")
                hechos_f += 1
                continue
            gf = trabajar(flo, i, True)
        if gf is not None:
            try: next(gf)
            except StopIteration:
                gf = None; hechos_f += 1

    ok(not frenos_mal, "en cada radicado, sin correo la app frenó AHÍ MISMO y dijo qué faltaba → %r" % frenos_mal[:3])
    ok(not pendientes_raros, "con todo completo, cada uno quedó LISTO al guardar → %r" % pendientes_raros[:3])
    pag.wait_for_timeout(2000)

    # ---- nada perdido, nada cruzado (lo guardado en el navegador de la principal) ----
    def registros(p):
        return p.evaluate("""()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));
          return JSON.parse(localStorage.getItem(k)||'[]')}""")
    def revisar(lista, donde):
        por = {}
        for x in lista: por.setdefault(x.get("radicado"), []).append(x)
        perdidos, cruzados, dobles = [], [], []
        for i in range(1, N + 1):
            r = RAD[i - 1]; f = formato(i)
            xs = por.get(r, [])
            if len(xs) != 1: dobles.append("%s está %d veces" % (r, len(xs))); continue
            x = xs[0]
            esperado = {"formato": f}
            if f != "DEVUELTO": esperado["direccion"] = correo(i)
            if f in ("T1", "T5", "T11"): esperado.update({"res": res(i), "fechaRes": "15/05/2025"})
            for k, v in esperado.items():
                if str(x.get(k, "")).strip().replace("-", "/") != v: perdidos.append("%s.%s=%r (debía %r)" % (r, k, x.get(k), v))
            if f not in ("T10", "DEVUELTO"):
                if comparendo(i)[-8:] not in json.dumps(x): perdidos.append("%s sin su comparendo" % r)
                if doc(i) not in json.dumps(x): perdidos.append("%s sin su documento" % r)
            # nada de NINGÚN otro radicado dentro de este
            texto = json.dumps({k: v for k, v in x.items() if k not in ("id", "radicado", "order")})
            for j in range(1, N + 1):
                if j == i: continue
                if correo(j) in texto or comparendo(j)[-8:] in texto or ("\"%s\"" % res(j)) in texto or nombre(j) + "\"" in texto:
                    cruzados.append("%s tiene datos del %s" % (r, RAD[j - 1]))
        ok(not dobles, "%s: cada radicado está una sola vez → %r" % (donde, dobles[:3]))
        ok(not perdidos, "%s: nada se perdió (cada radicado tiene exactamente lo suyo) → %r" % (donde, perdidos[:4]))
        ok(not cruzados, "%s: nada se cruzó entre radicados → %r" % (donde, cruzados[:4]))
    lista = registros(pag)
    ok(len(lista) == N, "la principal tiene %d radicados → %d" % (N, len(lista)))
    revisar(lista, "principal")
    revisar(registros(flo), "flotante")
    pag.reload(wait_until="domcontentloaded"); B.entrar_en(pag); pag.wait_for_timeout(1500)
    ok(pag.inner_text("#statDone") == str(N) and pag.inner_text("#statPend") == "0",
       "tras recargar: %d LISTOS y 0 pendientes → %s / %s" % (N, pag.inner_text("#statDone"), pag.inner_text("#statPend")))

    # ---- la masiva: una fila por radicado que va a la masiva, cada una con lo suyo ----
    ruta = B.descargar(pag)
    ok(ruta is not None, "con todo LISTO la masiva se descarga")
    if ruta:
        ws = openpyxl.load_workbook(ruta).active
        filas = [r for r in ws.iter_rows(min_row=2, values_only=True) if r and r[0]]
        van = [i for i in range(1, N + 1) if formato(i) not in ("AGENDAMIENTO", "DEVUELTO")]
        ok(len(filas) == len(van), "la masiva tiene %d filas (sin agendamientos ni devueltos) → %d" % (len(van), len(filas)))
        mal = []
        por = {str(f[0]): f for f in filas}
        for i in van:
            f = por.get(RAD[i - 1])
            if not f: mal.append("falta %s" % RAD[i - 1]); continue
            if str(f[5]).strip().lower() != correo(i): mal.append("%s correo %r" % (RAD[i - 1], f[5]))
            if formato(i) != "T10" and (str(f[2]) != comparendo(i)[-8:] or str(f[13]) != comparendo(i)[-8:]):
                mal.append("%s comparendo %r/%r" % (RAD[i - 1], f[2], f[13]))
            if formato(i) in ("T1", "T5", "T11") and str(f[16]) != res(i): mal.append("%s resolución %r" % (RAD[i - 1], f[16]))
            if formato(i) != "T10" and str(f[22]) != doc(i): mal.append("%s documento %r" % (RAD[i - 1], f[22]))
        ok(not mal, "cada fila de la masiva tiene los datos de SU radicado → %r" % mal[:4])

    # ---- un computador vacío con la misma cuenta: trae los 60 de la nube ----
    ctx2 = nav.new_context(viewport={"width": 1400, "height": 950})
    p3 = ctx2.new_page()
    B.entrar(p3, limpio=False); p3.wait_for_timeout(2500)
    lista3 = registros(p3)
    ok(len(lista3) == N, "en un navegador vacío, la nube devuelve los %d → %d" % (N, len(lista3)))
    revisar(lista3, "nube")
    ok(not err, "sin errores de JavaScript → %r" % err[:3])
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
