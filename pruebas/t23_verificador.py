# EL VERIFICADOR, CONTRA EL CASO REAL DEL 2 DE OCTUBRE DE 2026 (anonimizado).
#
# Esta es la prueba que PROTOCOLO.md llama "el caso real manda sobre la prueba imaginada".
# Los archivos de pruebas/caso_2oct/ son la masiva, el reporte de ORFEO y la plantilla de
# agendamientos de aquella semana, con los nombres, cédulas y correos sustituidos pero
# CONSERVANDO EXACTAMENTE la forma de cada defecto:
#
#   · 245 filas en la masiva, de las que 124 son de la semana del 24 al 28 de AGOSTO
#   · 218 radicados asignados del 28-09 al 02-10 en ORFEO
#   · 34 correos rotos (dos puntos al inicio, un espacio en la mitad, direcciones físicas
#     en la columna del correo, y dominios mal escritos: gmal, fmail, gmaial, gmail.co)
#   · un comparendo truncado a «11»
#   · UN radicado asignado que no está ni en la masiva ni en los agendamientos
#
# Si una versión futura del verificador deja de ver cualquiera de estas cosas, esta prueba falla.
# Esa es toda su razón de ser.
import sys, os; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import openpyxl
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "caso_2oct")
URL = "http://127.0.0.1:8871/verificador.html"
FALTA = open(os.path.join(D, "el_que_falta.txt")).read().strip()
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium", headless=True, args=["--no-sandbox"])
    ctx = nav.new_context(accept_downloads=True, viewport={"width":1300,"height":1000})
    pag = ctx.new_page(); errs = []
    pag.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pag.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    pag.goto(URL, wait_until="domcontentloaded"); pag.wait_for_timeout(900)

    print("1) lee los tres archivos, incluido el ORFEO que es HTML disfrazado de .xls")
    pag.set_input_files("#fMasiva", os.path.join(D, "masiva.xlsx"));        pag.wait_for_timeout(2200)
    pag.set_input_files("#fOrfeo",  os.path.join(D, "orfeo.xls"));          pag.wait_for_timeout(2200)
    pag.set_input_files("#fAgenda", os.path.join(D, "agendamientos.xlsx")); pag.wait_for_timeout(1400)
    ok("245 filas" in pag.inner_text("#eMasiva"), "masiva → " + pag.inner_text("#eMasiva"))
    ok("218 filas" in pag.inner_text("#eOrfeo"),  "ORFEO → " + pag.inner_text("#eOrfeo"))
    ok("20 filas"  in pag.inner_text("#eAgenda"), "agendamientos → " + pag.inner_text("#eAgenda"))
    ok(pag.input_value("#desde") == "2026-09-28" and pag.input_value("#hasta") == "2026-10-02",
       "deduce solo la semana del reporte → " + pag.input_value("#desde") + " a " + pag.input_value("#hasta"))

    print("2) el veredicto")
    pag.click("#verificar"); pag.wait_for_timeout(2500)
    ok("NO APTO" in pag.inner_text(".veredicto"), "NO APTO PARA ENTREGAR")

    filas = pag.locator("table.inv tbody tr")
    est = {}
    for i in range(filas.count()):
        c = filas.nth(i).locator("td")
        est[c.nth(0).inner_text().strip()] = (c.nth(2).inner_text().strip(), c.nth(3).inner_text().strip())
    ok(len(est) == 9, "se evalúan las 9 invariantes → " + str(len(est)))

    print("3) invariante por invariante")
    ok(est["I1"][0] == "PASA",  "I1 ningún radicado repetido")
    ok(est["I2"][0] == "PASA",  "I2 todos de 15 dígitos")
    ok(est["I3"][0] == "FALLA" and est["I3"][1].startswith("124 "), "I3 → " + est["I3"][1][:60])
    ok(est["I4"][0] == "FALLA" and est["I4"][1].startswith("124 "), "I4 → " + est["I4"][1][:60])
    ok(est["I5"][0] == "FALLA" and est["I5"][1].startswith("34 "),  "I5 → " + est["I5"][1][:60])
    ok(est["I6"][0] == "FALLA" and est["I6"][1].startswith("1 "),   "I6 → " + est["I6"][1][:60])
    ok(est["I7"][0] == "PASA",  "I7 las dos columnas COMPARENDO coinciden")
    ok(est["I8"][0] == "PASA",  "I8 cabecera de 27 columnas correcta")
    ok(est["I9"][0] == "FALLA" and est["I9"][1].startswith("1 "),   "I9 → " + est["I9"][1][:60])

    print("4) lo que falla se ve SIN tener que desplegarlo")
    texto = pag.inner_text("#salida")
    ok(FALTA in texto, "nombra el radicado sin responder (" + FALTA + ")")
    ok(pag.locator("table.inv details[open]").count() >= 5,
       "los detalles de lo que falla salen abiertos → " + str(pag.locator("table.inv details[open]").count()))

    print("5) cada tipo de correo roto se reconoce por su causa")
    for causa in ["empieza por «:»", "tiene un espacio en la mitad",
                  "es una DIRECCIÓN FÍSICA", "está mal escrito"]:
        ok(causa in texto, "reconoce: " + causa)

    print("6) el informe se descarga con una hoja por invariante que falla")
    with pag.expect_download(timeout=25000) as dl:
        pag.click("#descargar"); pag.wait_for_timeout(1200)
    ruta = os.path.join(os.path.dirname(__file__), "informe_verificador.xlsx"); dl.value.save_as(ruta)
    wb = openpyxl.load_workbook(ruta)
    ok("RESUMEN" in wb.sheetnames, "trae la hoja RESUMEN")
    ok(len([h for h in wb.sheetnames if h.startswith("I")]) == 5,
       "una hoja por cada invariante que falla → " + str(wb.sheetnames))

    print("7) con una masiva limpia solo debe quedar el problema DE VERDAD, no una alarma que siempre suena")
    # OJO con lo que se espera aquí: limpiar la masiva NO hace aparecer el radicado que nunca se
    # trabajó. I9 tiene que SEGUIR fallando, con exactamente 1, porque ese radicado sigue sin
    # respuesta en ningún archivo. Lo que se comprueba es que las otras ocho se callen: un
    # verificador que marca algo en un archivo correcto entrena a ignorarlo, y entonces no sirve.
    # Se queda solo con las filas que SÍ están en ORFEO y se arreglan los correos: debe pasar todo
    # menos lo que dependa de datos que no se tocaron.
    import re as _re
    src = openpyxl.load_workbook(os.path.join(D, "masiva.xlsx"))["Datos"]
    orf = open(os.path.join(D, "orfeo.xls"), encoding="latin-1").read()
    buenos = set(_re.findall(r"<td>(\d{15})</td>", orf))
    nb = openpyxl.Workbook(); ns = nb.active; ns.title = "Datos"
    ns.append([src.cell(row=1, column=c).value for c in range(1, src.max_column+1)])
    n = 0
    for r in range(2, src.max_row+1):
        v = [src.cell(row=r, column=c).value for c in range(1, src.max_column+1)]
        if str(v[0] or "").strip() not in buenos: continue
        v[5] = "ciudadano%d@gmail.com" % r                       # correo bueno
        if str(v[2] or "").strip() == "11": v[2] = v[13] = "52559342"   # comparendo bueno
        ns.append(v); n += 1
    limpia = os.path.join(os.path.dirname(__file__), "masiva_limpia_tmp.xlsx"); nb.save(limpia)
    pag.click("#limpiar"); pag.wait_for_timeout(400)
    pag.set_input_files("#fMasiva", limpia);                                pag.wait_for_timeout(2000)
    pag.set_input_files("#fOrfeo",  os.path.join(D, "orfeo.xls"));          pag.wait_for_timeout(2200)
    pag.set_input_files("#fAgenda", os.path.join(D, "agendamientos.xlsx")); pag.wait_for_timeout(1400)
    pag.click("#verificar"); pag.wait_for_timeout(2500)
    filas2 = pag.locator("table.inv tbody tr"); est2 = {}
    for i in range(filas2.count()):
        c = filas2.nth(i).locator("td")
        est2[c.nth(0).inner_text().strip()] = (c.nth(2).inner_text().strip(), c.nth(3).inner_text().strip())
    for k in ["I1","I2","I3","I4","I5","I6","I7","I8"]:
        ok(est2[k][0] == "PASA", "  " + k + " se calla con la masiva limpia → " + est2[k][0])
    ok(est2["I9"][0] == "FALLA" and est2["I9"][1].startswith("1 "),
       "  I9 sigue señalando el único radicado sin responder → " + est2["I9"][1][:52])
    fallan2 = [k for k in est2 if est2[k][0] == "FALLA"]
    ok(fallan2 == ["I9"], "  y es LA ÚNICA que falla → " + str(fallan2))
    try: os.remove(limpia)
    except OSError: pass

    print("errores js:", errs or "ninguno")
    if errs: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
