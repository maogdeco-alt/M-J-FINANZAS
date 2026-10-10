# BLOQUE DE LA MAÑANA — asignaciones de Donina. Se prueba con el ARCHIVO REAL del 30/9/2026.
# NOTA: esta prueba corre contra index_test_manana.html, la copia con el bloque de la
# mañana ENCENDIDO. En la app ese bloque está apagado desde el 10-10-2026; se sigue
# probando para que, si algún día se reactiva, funcione igual que el día que se apagó.
import sys, os; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B, openpyxl
SHEET = os.path.join(os.path.dirname(__file__), "sheet_donina.xlsx")
# El sheet de Donina lleva datos de ciudadanos reales: NO va en el repositorio (ver .gitignore).
# Para correr esta prueba, deja una copia del archivo del día aquí con ese nombre.
if not os.path.exists(SHEET):
    print("  SALTADA: falta pruebas/sheet_donina.xlsx (el sheet real no se guarda en el repositorio).")
    print("  Copia aquí el archivo de un día cualquiera con ese nombre y vuelve a correrla.")
    sys.exit(0)
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag, url=B.URL_MANANA)

    print("1) el selector de bloques")
    ok(pag.locator("#selBloqueManana").is_visible(), "se ve «Trabajo de la mañana»")
    ok(pag.locator("#selBloqueTarde").is_visible(), "se ve «Trabajo de la tarde»")
    ok(pag.locator("#paso2Section").is_visible(), "arranca en la tarde (la masiva de siempre)")
    pag.click("#selBloqueManana"); pag.wait_for_timeout(600)
    ok(pag.locator("#bloqueManana").is_visible(), "al pulsar mañana, aparece su pantalla")
    ok(pag.locator("#paso2Section").is_hidden(), "y la masiva queda escondida, no borrada")

    print("2) cargar el sheet real de Donina (las dos hojas de una vez)")
    B.cargar_sheet_manana(pag, SHEET)
    sin = pag.locator("#manCuentaSin").inner_text(); ia = pag.locator("#manCuentaIa").inner_text()
    print("      sin clasificar:", sin, "| revisar al modelo:", ia)
    ok(sin.endswith("/ 65"), "leyó las 65 filas de «RAD.NO TOMADOS POR EL MODELO»")
    ok(ia.endswith("/ 167"), "leyó las 167 filas de «RAD.CLASIFICADOS POR EL MODELO»")

    print("3) respeta lo que ya venía diligenciado en el archivo")
    pag.uncheck("#manSoloPendientes"); pag.wait_for_timeout(500)
    ok("0 /" in sin, "las 65 de la hoja 1 ya venían clasificadas → 0 pendientes ("+sin+")")
    ok(ia.startswith("120 /"), "de la hoja 2, quedan 120 por revisar ("+ia+")")

    print("4) el catálogo de clasificaciones sale del propio archivo")
    pag.check("#manSoloPendientes"); pag.wait_for_timeout(400)
    pag.click('#manTabs button[data-mantab="ia"]'); pag.wait_for_timeout(600)
    primera = pag.locator("#manPanel .man-fila").first
    primera.locator("input[data-manclas]").click(); pag.wait_for_timeout(500)
    opciones = pag.locator("#manSugerenciasVivas .fd-item")
    ok(opciones.count() > 20, "el desplegable ofrece las clasificaciones del sheet (%d)" % opciones.count())
    textos = opciones.all_inner_texts()
    ok(any("MASIVO TIPO 1"==t.strip() for t in textos), "está «MASIVO TIPO 1»")
    ok(any("PETICION OSCURA"==t.strip() for t in textos), "está «PETICION OSCURA»")
    pag.keyboard.press("Escape"); pag.wait_for_timeout(300)

    print("5) confirmar que el modelo acertó, y corregirlo")
    filas = pag.locator("#manPanel .man-fila")
    rad_ok = filas.nth(0).locator(".man-rad").inner_text()
    filas.nth(0).locator("button[data-manok]").click(); pag.wait_for_timeout(600)
    filas = pag.locator("#manPanel .man-fila")
    rad_corr = filas.nth(0).locator(".man-rad").inner_text()
    inp = filas.nth(0).locator("input[data-manclas]")
    inp.click(); inp.fill("PETICION OSCURA"); pag.wait_for_timeout(400)
    pag.keyboard.press("Enter"); pag.wait_for_timeout(700)
    print("      confirmado:", rad_ok, "| corregido:", rad_corr)
    ok(pag.locator("#manCuentaIa").inner_text().startswith("118 /"), "bajan los pendientes a 118 → "+pag.locator("#manCuentaIa").inner_text())

    print("6) las dos listas que se entregan")
    B.abrir_listas(pag)
    with pag.expect_download(timeout=20000) as dl1:
        pag.click("#manDescargar1")
    r1=os.path.join(os.path.dirname(__file__),"lista1.xlsx"); dl1.value.save_as(r1)
    ws1=openpyxl.load_workbook(r1).active
    ok([c.value for c in ws1[1]]==["RADICADO","CLASIFICACIÓN"], "lista 1: solo dos columnas → "+str([c.value for c in ws1[1]]))
    ok(ws1.max_row==66, "lista 1: 65 radicados + títulos → %d filas" % ws1.max_row)
    ok(ws1["B2"].value=="ABOGADO  SUSTANCIADOR ", "conserva los espacios exactos del sheet → "+repr(ws1["B2"].value))

    with pag.expect_download(timeout=20000) as dl2:
        pag.click("#manDescargar2")
    r2=os.path.join(os.path.dirname(__file__),"lista2.xlsx"); dl2.value.save_as(r2)
    ws2=openpyxl.load_workbook(r2).active
    print("      lista 2:", ws2.max_row-1, "filas")
    negrillas=[(ws2.cell(row=i,column=1).value, ws2.cell(row=i,column=2).value)
               for i in range(2, ws2.max_row+1) if ws2.cell(row=i,column=2).font.bold]
    normales=[(ws2.cell(row=i,column=1).value, ws2.cell(row=i,column=2).value)
              for i in range(2, ws2.max_row+1) if not ws2.cell(row=i,column=2).font.bold]
    ok(all(v=="OK" for _,v in normales), "las confirmadas salen como «OK» en letra normal (%d)" % len(normales))
    ok(len(negrillas)==1, "solo la corregida sale resaltada (%d)" % len(negrillas))
    if negrillas:
        c=ws2.cell(row=[i for i in range(2,ws2.max_row+1) if ws2.cell(row=i,column=2).font.bold][0], column=2)
        ok(c.font.bold and c.font.underline=="single", "y va en NEGRILLA y SUBRAYADA → %r" % c.value)
        ok(str(negrillas[0][0])==rad_corr, "en el radicado que corregí (%s)" % negrillas[0][0])

    B.cerrar_listas(pag)
    print("7) cerrar el día: archiva y deja limpio")
    pag.click("#manCerrarDiaBtn"); pag.wait_for_timeout(700)
    ok(pag.locator("#manCerrarDialog[open]").count()==1, "pide confirmación")
    ok("232" in pag.locator("#manCerrarResumen").inner_text(), "dice cuántos se archivan → "+pag.locator("#manCerrarResumen").inner_text()[:100])
    pag.click("#manCerrarOk"); pag.wait_for_timeout(1200)
    ok(pag.locator("#manCuentaSin").inner_text()=="0 / 0", "la pantalla queda limpia")
    pag.click("#manHistorialBtn"); pag.wait_for_timeout(700)
    ok(pag.locator("#manHistorialLista .preflight-item").count()==1, "y el día queda en el historial")
    pag.click("#manHistorialClose"); pag.wait_for_timeout(400)

    print("8) la masiva de la tarde sigue intacta")
    pag.click("#selBloqueTarde"); pag.wait_for_timeout(600)
    ok(pag.locator("#paso2Section").is_visible(), "vuelve la pantalla de siempre")
    ok(pag.locator("#descargarMasivaBtn").is_visible() and pag.locator("#cerrarSemanaNavBtn").is_visible(),
       "con sus botones de siempre")
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
