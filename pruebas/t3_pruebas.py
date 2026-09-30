# 2b. "agregar una pregunta de SI O NO ... preguntando si el usuario PIDIO O NO PIDIO PRUEBAS,
#      y esta informacion debe aparecer reflejada en el documento final"
# + comprueba de paso que la PLACA sale en su columna y que el archivo lleva cuadrícula.
from playwright.sync_api import sync_playwright
import base as B, sys, os, openpyxl
T="\t"
TIRA = T.join(["11001000000046855268","D01","19/04/2025","","No","COMPARENDERA","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","JOSE PÉREZ CASTAÑEDA","CALLE 13 36 31 BAHIA 1","ABC123"])
BLOQUE = "2026ER100\t01/09/2026\t03/09/2026\tJOSE PEREZ CASTANEDA"
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav,ctx,pag,errores=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    B.ir_a(pag,"2026ER100")

    print("1) la pregunta solo aparece cuando es AGENDAMIENTO")
    B.escribir(pag,"#cc_formato","T14")
    ok(pag.locator("#wrap_pruebas").is_hidden(), "con T14 no estorba")
    B.escribir(pag,"#cc_formato","AGENDAMIENTO")
    ok(pag.locator("#wrap_pruebas").is_visible(), "con AGENDAMIENTO aparece sola")
    ok("¿El ciudadano pidió pruebas?" in pag.locator("#wrap_pruebas").inner_text(), "y dice justo eso")
    ok("VACÍA" in pag.locator("#cc_pruebasEco").inner_text(), "sin responder, avisa que la columna saldría vacía")

    print("2) se responde de un clic y dice qué va a quedar escrito")
    B.pegar_tira(pag, TIRA)
    B.escribir(pag,"#cc_direccion","persona@gmail.com")
    pag.locator('#wrap_pruebas input[value="SI"]').check()
    pag.wait_for_timeout(400)
    ok("AGENDAR CON PRUEBAS" in pag.locator("#cc_pruebasEco").inner_text(), "SÍ → AGENDAR CON PRUEBAS")
    pag.locator('#wrap_pruebas input[value="NO"]').check()
    pag.wait_for_timeout(400)
    ok("AGENDAR SIN PRUEBAS" in pag.locator("#cc_pruebasEco").inner_text(), "NO → AGENDAR SIN PRUEBAS")

    print("3) la misma respuesta se ve en la ventana de Agendamientos")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.click("#agendaTriggerBtn"); pag.wait_for_selector("#agendaDialog[open]"); pag.wait_for_timeout(500)
    ok(pag.locator('#agendaDetalle input[name="ae_pruebas"][value="NO"]').is_checked(), "llega marcada en NO")
    pag.locator('#agendaDetalle input[name="ae_pruebas"][value="SI"]').check()
    pag.wait_for_timeout(500)
    ok("AGENDAR CON PRUEBAS" in pag.locator("#ae_pruebasWrap").inner_text(), "se puede cambiar ahí mismo")

    print("4) y sale en el archivo que se entrega")
    with pag.expect_download(timeout=20000) as dl:
        pag.click("#downloadAgendaBtn")
        pag.wait_for_timeout(700)
        if pag.locator("#preflightDialog[open]").count():
            pag.click("#preflightProceed")
    ruta = os.path.join(os.path.dirname(__file__), "plantilla_agenda.xlsx")
    dl.value.save_as(ruta)
    wb = openpyxl.load_workbook(ruta); ws = wb.active
    cab = [c.value for c in ws[1]]
    fila = [c.value for c in ws[2]]
    print("      encabezados:", cab)
    print("      fila:", fila)
    ok(cab[14]=="FORMATO" and fila[14]=="AGENDAR CON PRUEBAS", "columna FORMATO = AGENDAR CON PRUEBAS")
    ok(cab[7]=="PLACA" and fila[7]=="ABC123", "columna PLACA = ABC123 (no la dirección)")
    b = ws["A1"].border
    ok(all(x and x.style for x in (b.left,b.right,b.top,b.bottom)), "el archivo trae cuadrícula")
    ok(ws.freeze_panes=="A2", "y la fila de títulos queda congelada")

    print("\nerrores de JavaScript:", errores or "ninguno")
    if errores: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
