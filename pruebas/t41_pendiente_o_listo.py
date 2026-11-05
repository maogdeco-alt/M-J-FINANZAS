# PENDIENTE O LISTO: LA APP NO SIGUE DE LARGO, Y LA MASIVA SOLO SALE CON TODO LISTO (04-11-2026)
#
# Pedido de la usuaria, palabra por palabra: "si la información que ingreso no sirve, no es apta,
# o no es clara, NO PUEDE SEGUIR DE LARGO la app y al final de todo el trabajo decirme que hay algo
# que falta o está mal. Cuando yo le doy descargar a la masiva, es OBLIGATORIO que la app ya haya
# estado segura que no hay errores, inconsistencias, ni falta información."
#
# Se comprueba: que "Guardar y siguiente" no avanza mientras falte algo y dice QUÉ, en la casilla;
# que lo escrito sí queda guardado; que "Descargar masiva" no descarga con pendientes (y lo dice en
# el botón antes de tocarlo); que no sale ningún diálogo de "¿es correcto?"; que un dominio de
# correo raro se aprende una vez; y que con todo LISTO descarga directo. Datos inventados.
import sys, os, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
R1, R2, R3 = "202670000000101", "202670000000102", "202670000000103"
TIRA1 = T.join(["11001000000046855268","C29","19/04/2025","25/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE","","","",
                "CEDULA DE CIUDADANIA","1886999","JOSE PEREZ CASTANEDA"])
TIRA2 = T.join(["11001000000046855999","C02","10/03/2025","15/03/2025","No","COMPARENDERA","VIGENTE","","","",
                "CEDULA DE CIUDADANIA","52111222","ANA MARIA RUIZ LOPEZ"])
TIRA3 = T.join(["11001000000046855777","C29","11/02/2025","18/02/2025","No","CAMARAS SALVAVIDAS","VIGENTE","","","",
                "CEDULA DE CIUDADANIA","80111333","LUIS CARLOS DIAZ PARRA"])
BLOQUE = "\n".join([R1 + "\t02/11/2026\t03/11/2026\tJOSE PEREZ CASTANEDA",
                    R2 + "\t02/11/2026\t03/11/2026\tANA MARIA RUIZ LOPEZ",
                    R3 + "\t02/11/2026\t04/11/2026\tLUIS CARLOS DIAZ PARRA"])
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def caja(p): return p.inner_text("#avisoImperativas") if p.locator("#avisoImperativas:visible").count() else ""
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    alertas = []
    B.entrar(pag); B.importar(pag, BLOQUE)
    ok(pag.inner_text("#statPend") == "3" and pag.inner_text("#statDone") == "0", "recién importados: 3 pendientes, 0 listos")
    ok("faltan 3" in pag.inner_text("#masivaListaBadge"), "el botón de la masiva dice de una vez «faltan 3»")

    # 1) T6 completo pero sin correo: no sigue, dice qué falta y lo marca en rojo.
    B.ir_a(pag, R1); B.pegar_tira(pag, TIRA1); B.escribir(pag, "#cc_formato", "T6")
    pag.click("#cc_saveNext"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); pag.wait_for_timeout(400)
    alertas.append(pag.locator("#alertaInmediataDialog[open]").count())
    ok(R1 in pag.inner_text("#cc_radicadoLabel"), "Guardar y siguiente NO avanza mientras falte algo")
    ok("Falta el correo" in caja(pag), "y dice qué falta, debajo del formulario → %r" % caja(pag)[:120])
    ok(pag.locator("#wrap_direccion.field-error").count() == 1, "la casilla del correo queda en rojo")

    # 2) Descargar con pendientes: no descarga, lleva al pendiente.
    descargo = False
    try:
        with pag.expect_download(timeout=2500):
            pag.click("#descargarMasivaBtn")
        descargo = True
    except Exception: pass
    ok(not descargo, "con pendientes, «Descargar masiva» NO descarga")
    ok(pag.locator("#preflightDialog[open]").count() == 0, "y no abre ninguna revisión al final")

    # 3) Se completa: ahora sí sigue, y queda LISTO.
    B.ir_a(pag, R1); B.escribir(pag, "#cc_direccion", "jose.perez@gmail.com")
    pag.click("#cc_saveNext"); pag.wait_for_timeout(800); B.confirmar_nombre(pag); pag.wait_for_timeout(400)
    ok(R1 not in pag.inner_text("#cc_radicadoLabel"), "completo, Guardar y siguiente sí avanza")
    ok(pag.inner_text("#statDone") == "1", "y ya cuenta 1 LISTO → %s" % pag.inner_text("#statDone"))

    # 4) T1 sin resolución: no sigue. «Dejar pendiente y seguir» sí deja ir, y queda pendiente.
    B.ir_a(pag, R2); B.pegar_tira(pag, TIRA2); B.escribir(pag, "#cc_formato", "T1")
    B.escribir(pag, "#cc_direccion", "ana.ruiz@gmail.com")
    pag.click("#cc_saveNext"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); pag.wait_for_timeout(400)
    alertas.append(pag.locator("#alertaInmediataDialog[open]").count())
    ok(R2 in pag.inner_text("#cc_radicadoLabel") and "resolución" in caja(pag), "T1 sin resolución: no sigue y lo dice")
    pag.click("#faltasDejarPendiente"); pag.wait_for_timeout(700)
    ok(R2 not in pag.inner_text("#cc_radicadoLabel"), "«Dejar pendiente y seguir» deja pasar al siguiente")
    B.ir_a(pag, R2)
    ok(pag.input_value("#cc_direccion") == "ana.ruiz@gmail.com", "lo escrito en el pendiente quedó guardado")
    # «Siguiente» frena con un pendiente trabajado; «Anterior» no (volver no es seguir de largo, y en
    # la flotante es la única forma de regresar).
    pag.click("#cc_next"); pag.wait_for_timeout(600); B.confirmar_nombre(pag)
    ok(R2 in pag.inner_text("#cc_radicadoLabel"), "«Siguiente» tampoco lo deja atrás")
    # (la cola pone primero los pendientes: R2, R3 y después R1, que ya está LISTO)
    B.ir_a(pag, R3); B.escribir(pag, "#cc_formato", "T14"); pag.click("#cc_save"); pag.wait_for_timeout(500)
    pag.click("#cc_prev"); pag.wait_for_timeout(600); B.confirmar_nombre(pag)
    ok(R2 in pag.inner_text("#cc_radicadoLabel"), "«Anterior» sí deja volver al anterior, aunque falten cosas")
    B.ir_a(pag, R2)

    # 5) Resolución con texto pegado: tampoco.
    B.escribir(pag, "#cc_res", "2103738236 del 11 de marzo de 2026"); B.escribir(pag, "#cc_fechaRes", "11/03/2026")
    pag.click("#cc_saveNext"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); pag.wait_for_timeout(400)
    ok(R2 in pag.inner_text("#cc_radicadoLabel") and "solo el número" in caja(pag), "resolución con texto pegado: no sigue")
    B.escribir(pag, "#cc_res", "2103738236")
    pag.click("#cc_saveNext"); pag.wait_for_timeout(800); B.confirmar_nombre(pag); pag.wait_for_timeout(400)
    ok(R2 not in pag.inner_text("#cc_radicadoLabel"), "con el número solo, sigue")

    # 6) Un dominio raro se frena, y se aprende con un clic.
    B.ir_a(pag, R3); B.pegar_tira(pag, TIRA3); B.escribir(pag, "#cc_formato", "T6")
    B.escribir(pag, "#cc_direccion", "luis.diaz@airliquide.com")
    pag.click("#cc_saveNext"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); pag.wait_for_timeout(400)
    ok(R3 in pag.inner_text("#cc_radicadoLabel") and pag.locator("#faltasDominioOk").count() == 1,
       "un dominio poco común frena, con el botón «está bien escrito»")
    pag.click("#faltasDominioOk"); pag.wait_for_timeout(600)
    ok("LISTO" in caja(pag) and "Falta" not in caja(pag), "al confirmarlo queda LISTO → %r" % caja(pag)[:80])
    ok(pag.inner_text("#statPend") == "0", "0 pendientes")
    ok(not any(alertas) and pag.locator("#alertaInmediataDialog[open]").count() == 0, "nunca salió un diálogo de «¿es correcto?»")

    # 7) Todo LISTO: descarga directo, sin ventanas en el medio, con las 3 filas.
    with pag.expect_download(timeout=15000) as dl:
        pag.click("#descargarMasivaBtn")
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "masiva_t41.xlsx")
    dl.value.save_as(ruta)
    ws = openpyxl.load_workbook(ruta).active
    filas = [[c.value for c in f] for f in ws.iter_rows(min_row=2)]
    ok(len(filas) == 3 and sorted(f[0] for f in filas) == [R1, R2, R3], "la masiva sale con los 3, todos LISTOS")
    ok(all(f[2] and f[2] == f[13] for f in filas), "las dos columnas COMPARENDO coinciden")
    os.remove(ruta)
    ok(not err, "sin errores de JavaScript → %r" % err)
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
