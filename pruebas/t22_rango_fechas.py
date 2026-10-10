# "NECESITO LOS RADICADOS QUE TRABAJÉ DESDE EL 28 DE SEPTIEMBRE HASTA AHORA, NO LOS ANTERIORES,
#  NO LOS VIEJOS, NO REPETIR LOS RADICADOS" (5-10-2026).
#
# El botón normal de la masiva saca TODA la lista. Cuando quedan vivas semanas anteriores sin
# cerrar, eso arrastra radicados viejos. Esta prueba vigila la salida por rango de fechas:
#   · entra lo asignado dentro del rango y NADA de antes,
#   · una sola fila por radicado (si tiene dos asignaciones dentro, la más reciente),
#   · lo que no tiene fecha legible NO se cuela, pero se lista,
#   · y el botón normal de la masiva sigue sacando todo, sin recortar nada.
import sys, os; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B, openpyxl
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
VIEJO   ="202642110700001"   # 10 de septiembre — NO debe salir
BORDE   ="202642110700002"   # 28 de septiembre — primer día del rango, SÍ
RECIENTE="202642110700003"   # 2 de octubre — SÍ
SINFECHA="202642110700004"   # sin fecha de asignación — NO, pero se lista
BLOQUE="\n".join([
 VIEJO   +"\t01/09/2026\t10/09/2026\tPERSONA VIEJA",
 BORDE   +"\t01/09/2026\t28/09/2026\tPERSONA DEL BORDE",
 RECIENTE+"\t01/09/2026\t02/10/2026\tPERSONA RECIENTE",
 SINFECHA+"\t01/09/2026\t\tPERSONA SIN FECHA",
])
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

def clasificar(pag, rad, suf):
    B.ir_a(pag,rad); B.pegar_tira(pag,TIRA.replace("46855268","4685526"+suf))
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p"+suf+"@gmail.com")
    B.escribir(pag,"#cc_res","13687"+suf); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    for i,rad in enumerate((VIEJO,BORDE,RECIENTE,SINFECHA)): clasificar(pag,rad,str(i+1))
    pag.wait_for_timeout(600)

    print("0) el radicado del borde se reasigna DENTRO del rango: no puede salir dos veces")
    pag.evaluate("""(rad)=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const lista = JSON.parse(localStorage.getItem(k));
      const base = lista.find(r=>r.radicado===rad);
      const nuevo = JSON.parse(JSON.stringify(base));
      nuevo.id='reasignado_dentro'; nuevo.fechaAsignacion='01-10-2026';
      nuevo.modificadoEn = Date.now()+60000;
      lista.push(nuevo);
      localStorage.setItem(k, JSON.stringify(lista));
    }""", BORDE)
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1600)
    ok(pag.locator("#masivaListaBadge").inner_text()=="5",
       "la masiva completa lleva las 5 filas → "+pag.locator("#masivaListaBadge").inner_text())

    print("1) EL RANGO 28-SEP A HOY DEJA FUERA LO VIEJO")
    pag.click("#abrirDocumentosBtn"); pag.wait_for_timeout(600)
    pag.click("#abrirCuadreBtn"); pag.wait_for_timeout(800)
    ok(pag.locator("#cuadreDesde").input_value()!="", "propone un rango de entrada → "+pag.locator("#cuadreDesde").input_value())
    pag.fill("#cuadreDesde","2026-09-28"); pag.dispatch_event("#cuadreDesde","change")
    pag.fill("#cuadreHasta","2026-10-05"); pag.dispatch_event("#cuadreHasta","change")
    pag.wait_for_timeout(600)
    txt = pag.locator("#cuadreRango").inner_text()
    ok("del 28-09-2026 al 05-10-2026" in txt, "dice el rango en palabras → "+txt.split("\n")[0][:90])
    ok(VIEJO not in txt.split("Los que NO se incluyen")[0], "el viejo no está entre los que saldrían")
    ok(SINFECHA in txt, "el de sin fecha se lista aparte, no desaparece")

    print("2) EL ARCHIVO DEL RANGO: SIN VIEJOS Y SIN REPETIR")
    with pag.expect_download(timeout=25000) as dl:
        pag.click("#cuadreRangoDescargar"); pag.wait_for_timeout(1500)
    ruta=os.path.join(os.path.dirname(__file__),"masiva_rango.xlsx"); dl.value.save_as(ruta)
    ws=openpyxl.load_workbook(ruta).active
    rads=[str(ws.cell(row=i,column=1).value) for i in range(2,ws.max_row+1)]
    ok(VIEJO not in rads, "el viejo (10-09) NO está → "+str(rads))
    ok(SINFECHA not in rads, "el que no tiene fecha NO está")
    ok(BORDE in rads, "el del 28-09 (primer día) SÍ está")
    ok(RECIENTE in rads, "el del 02-10 SÍ está")
    ok(rads.count(BORDE)==1, "el reasignado sale UNA sola vez → "+str(rads.count(BORDE)))
    ok(len(rads)==len(set(rads)), "ningún radicado repetido → "+str(rads))
    ok(len(rads)==2, "en total 2 filas → "+str(len(rads)))

    print("3) de las dos asignaciones del borde sale LA MÁS RECIENTE")
    col={ws.cell(row=1,column=c).value:c for c in range(1,ws.max_column+1)}
    cAsig=next((c for t,c in col.items() if t and "ASIGNA" in str(t).upper()), None)
    if cAsig:
        fila=next(i for i in range(2,ws.max_row+1) if str(ws.cell(row=i,column=1).value)==BORDE)
        val=str(ws.cell(row=fila,column=cAsig).value or "")
        # El formato MASIVA escribe la fecha como dd-mmm-yyyy en español ("01-oct-2026").
        ok(val.startswith("01-oct"), "sale la del 1 de octubre, no la del 28 de septiembre → "+val)
    else:
        print("  (el formato MASIVA no trae columna de fecha de asignación: se omite)")

    print("4) EL BOTÓN NORMAL DE LA MASIVA SIGUE SACANDO TODO")
    pag.click("#cuadreClose"); pag.wait_for_timeout(400)
    with pag.expect_download(timeout=25000) as dl2:
        pag.click("#downloadFinalBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightProceed")
    ruta2=os.path.join(os.path.dirname(__file__),"masiva_completa_rango.xlsx"); dl2.value.save_as(ruta2)
    ws2=openpyxl.load_workbook(ruta2).active
    rads2=[str(ws2.cell(row=i,column=1).value) for i in range(2,ws2.max_row+1)]
    ok(VIEJO in rads2, "el completo sigue trayendo el viejo (no se recortó nada) → "+str(len(rads2))+" filas")
    ok(len(rads2)==5, "las 5 filas de siempre → "+str(rads2))

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
