# REGRESIÓN: "es OBLIGATORIO que todas las mejoras, arreglos, reglas y demás configuraciones
# en la app se mantengan intactas". Esto recorre lo que ya estaba y comprueba que sigue ahí.
from playwright.sync_api import sync_playwright
import base as B, sys, os, openpyxl
T="\t"
MANUAL = T.join(["11001000000046855268","D01","19/04/2025","19/04/2025","No","COMPARENDERA","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","JOSE PEREZ CASTANEDA","ABC123"])
ELECT  = T.join(["11001000000046855269","C02","01/03/2025","02/03/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","52123456","ANA MARIA GOMEZ","XYZ12D"])
CERRADO= T.join(["11001000000046855270","F","01/03/2025","02/03/2025","No","COMPARENDERA","CERRADO",
  "","","","CEDULA DE CIUDADANIA","79123456","LUIS RUIZ","DEF456"])
BLOQUE = "\n".join([
 "2026ER900\t01/09/2026\t03/09/2026\tJOSE PEREZ CASTANEDA",
 "2026ER901\t01/09/2026\t03/09/2026\tANA MARIA GOMEZ",
 "2026ER902\t01/09/2026\t03/09/2026\tLUIS RUIZ",
 "2026ER903\t01/09/2026\t03/09/2026\tCARMEN DIAZ",
])
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav,ctx,pag,errores=B.abrir(pw)
    B.entrar(pag)
    print("1) la app entra y la configuración de la nube sigue intacta")
    ok(pag.locator("#captureEmpty, #captureForm").count()>0, "el Paso 2 existe")
    B.importar(pag, BLOQUE)
    ok(pag.locator("#queuePanel .queue-item").count()==4, "los 4 radicados entraron a la cola")

    print("2) la sección de REGLAS")
    pag.click("#reglasBtn"); pag.wait_for_selector("#reglasDialog[open]"); pag.wait_for_timeout(400)
    txt = pag.locator("#reglasDialog").inner_text()
    for r in ["R01","R05","R06","R07","R08","R09","R10","R11","R15","R16","R17","R18","R19","R20","R21","R22","R23","R24"]:
        ok(r in txt, "está " + r)
    ok("MIENTRAS TRABAJAS UN RADICADO" in txt.upper(), "siguen agrupadas por momento")
    ok("NUNCA ES UN ERROR" in txt.upper(), "la excepción de la notificación se ve con su etiqueta")
    pag.evaluate("()=>document.getElementById('reglasDialog').close()"); pag.wait_for_timeout(200)

    print("3) las reglas imperativas de siempre")
    B.ir_a(pag,"2026ER902"); B.pegar_tira(pag, CERRADO)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","luis@gmail.com")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag)
    pag.click("#cc_saveNext"); pag.wait_for_timeout(600)
    t = pag.locator("#toast").inner_text() if pag.locator("#toast").count() else ""
    ok("DEVUELTO" in t, "código F / estado CERRADO siguen obligando DEVUELTO → "+t[:90])
    B.cerrar_alerta(pag)

    print("4) un radicado normal, clasificado, entra en la masiva")
    B.ir_a(pag,"2026ER901"); B.pegar_tira(pag, ELECT)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","ana@gmail.com")
    B.escribir(pag,"#cc_res","1368706"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

    print("5) un AGENDAMIENTO NUNCA entra en la masiva")
    B.ir_a(pag,"2026ER900"); B.pegar_tira(pag, MANUAL)
    B.escribir(pag,"#cc_formato","AGENDAMIENTO"); B.escribir(pag,"#cc_direccion","jose@gmail.com")
    pag.locator('#wrap_pruebas input[value="SI"]').check(); pag.wait_for_timeout(300)
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

    print("6) DEVUELTO tampoco")
    B.ir_a(pag,"2026ER902")
    B.escribir(pag,"#cc_formato","DEVUELTO")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

    with pag.expect_download(timeout=25000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1000)
        if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightProceed")
    ruta=os.path.join(os.path.dirname(__file__),"masiva_reg.xlsx"); dl.value.save_as(ruta)
    ws=openpyxl.load_workbook(ruta).active
    rads=[ws.cell(row=i,column=1).value for i in range(2,ws.max_row+1)]
    print("      radicados en la masiva:", rads)
    ok(rads==["2026ER901"], "solo el clasificado normal: ni el AGENDAMIENTO ni el DEVUELTO")

    print("7) las ventanas de siempre abren sin romperse")
    for btn,dlg in [("#agendaTriggerBtn","#agendaDialog"),("#abrirDocumentosBtn","#documentosDialog"),
                    ("#abrirImportarBtn","#importDialog"),("#reglasBtn","#reglasDialog")]:
        pag.click(btn); pag.wait_for_timeout(500)
        ok(pag.locator(dlg+"[open]").count()==1, "abre "+dlg)
        pag.evaluate("(d)=>document.querySelector(d).close()", dlg); pag.wait_for_timeout(250)

    print("\nerrores de JavaScript:", errores or "ninguno")
    if errores: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
