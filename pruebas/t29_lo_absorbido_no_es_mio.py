# UN VALOR VIEJO DE LA OTRA VENTANA NO PUEDE VOLVER A PISAR UNO NUEVO.
#
# Caso encontrado por t28_estres_cruces el 10-10-2026, aislado aquí paso a paso:
#   1. la flotante escribe el correo A en un radicado y se guarda solo (autoguardado);
#   2. la principal se entera (lo trae a su memoria) pero no guarda nada todavía;
#   3. la flotante corrige el correo a B y guarda;
#   4. la principal guarda cualquier cosa, en OTRO radicado.
# Antes: en el paso 4 la principal confundía la A que había traído en el paso 2 con un cambio
# hecho por ella misma, y la escribía encima de la B. El correo corregido se perdía sin aviso.
# Lo que se exige: en todas partes queda B.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
RAD = ["2026300000000%02d" % i for i in (1, 2)]
def tira(i): return T.join(["1100100000004685%04d" % i, "C02", "19/04/2025", "19/04/2025", "No",
  "CAMARAS SALVAVIDAS", "VIGENTE", "", "", "", "CEDULA DE CIUDADANIA", "520000%03d" % i, "PERSONA %d" % i, "ABC%03d" % i])
BLOQUE = "\n".join("%s\t01/09/2026\t03/09/2026\tPERSONA %d" % (r, i + 1) for i, r in enumerate(RAD))
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def en_disco(p, rad, campo):
    return p.evaluate("""([r,c])=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));
      const a=JSON.parse(localStorage.getItem(k)||'[]'); return String((a.find(x=>x.radicado===r)||{})[c]||'')}""", [rad, campo])
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag); B.importar(pag, BLOQUE)
    for i, r in enumerate(RAD, 1):
        B.ir_a(pag, r); B.pegar_tira(pag, tira(i))
        B.escribir(pag, "#cc_formato", "T14"); B.escribir(pag, "#cc_direccion", "inicial%d@gmail.com" % i)
        B.escribir(pag, "#cc_res", "13687%02d" % i); B.escribir(pag, "#cc_fechaRes", "26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(400); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    B.ir_a(pag, RAD[0])                      # la principal se queda en el 001
    pag.wait_for_timeout(800)
    flo = ctx.new_page(); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail", "prueba@gmail.com"); flo.fill("#loginPassword", "123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    flo.wait_for_timeout(1500)
    if flo.locator("#captureEmptyVerTodos").is_visible():
        flo.click("#captureEmptyVerTodos"); flo.wait_for_timeout(400)
    if RAD[1] not in flo.locator("#cc_radicadoLabel").inner_text():
        flo.click("#cc_next"); flo.wait_for_timeout(400); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    ok(RAD[1] in flo.locator("#cc_radicadoLabel").inner_text(), "la flotante está en el 002 → " + flo.locator("#cc_radicadoLabel").inner_text())

    print("1) la flotante escribe A y se autoguarda")
    flo.fill("#cc_direccion", "correoA@gmail.com"); flo.dispatch_event("#cc_direccion", "input")
    flo.wait_for_timeout(2000)
    ok(en_disco(pag, RAD[1], "direccion") == "correoA@gmail.com", "A quedó guardada")
    print("2) la principal la trae a su memoria sin guardar nada (no se toca)")
    pag.wait_for_timeout(500)
    print("3) la flotante corrige a B y guarda")
    flo.fill("#cc_direccion", "correoB@gmail.com"); flo.dispatch_event("#cc_direccion", "input")
    flo.click("#cc_save"); flo.wait_for_timeout(600); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    ok(en_disco(pag, RAD[1], "direccion") == "correoB@gmail.com", "B quedó guardada")
    print("4) la principal guarda algo en OTRO radicado (el 001)")
    pag.fill("#cc_comentario", "algo en el 001"); pag.dispatch_event("#cc_comentario", "input")
    pag.click("#cc_save"); pag.wait_for_timeout(600); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(1500)
    ok(en_disco(pag, RAD[1], "direccion") == "correoB@gmail.com",
       "el 002 sigue con B en el navegador → " + repr(en_disco(pag, RAD[1], "direccion")))
    B.ir_a(pag, RAD[1])
    ok(pag.input_value("#cc_direccion") == "correoB@gmail.com",
       "y la principal muestra B → " + repr(pag.input_value("#cc_direccion")))
    ok(en_disco(pag, RAD[0], "comentario") == "algo en el 001", "lo del 001 se guardó")
    print("errores js:", err or "ninguno", "|", err2 or "ninguno")
    if err or err2: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
