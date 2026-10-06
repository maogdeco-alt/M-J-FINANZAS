# LA MASIVA TIENE QUE DECIR DE CUÁNTAS SEMANAS ES.
#
# EL FALLO DE DISEÑO DE ORIGEN, Y EL MÁS CARO DE TODOS. La masiva exportaba SIEMPRE "todo lo que
# haya en la lista", sin ninguna noción de a qué semana pertenece cada radicado. Mientras la semana
# se cierre cada viernes no se nota; en cuanto una se queda sin cerrar, su lote sigue vivo y entra
# en todas las entregas siguientes.
#
# Caso real: el 2 de octubre de 2026 se entregó una masiva de 245 filas donde 124 eran del 24 al 28
# de AGOSTO. La app no dijo nada porque no tenía nada que decir -- para ella la palabra "semana" no
# existía. Se descubrió cruzando a mano contra ORFEO, un mes después.
#
# No se bloquea la entrega: hay motivos legítimos para entregar dos semanas juntas. Lo que no puede
# volver a pasar es entregarlas sin saberlo.
import sys, os; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B, openpyxl
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
# dos de esta semana (28-09 a 02-10) y dos de agosto, como en el caso real
AHORA = ["202661203706582", "202661203702962"]
AGOSTO = ["202661203171392", "202661203189052"]
BLOQUE = "\n".join([
  AHORA[0] +"\t01/09/2026\t28/09/2026\tPERSONA UNO",
  AHORA[1] +"\t01/09/2026\t30/09/2026\tPERSONA DOS",
  AGOSTO[0]+"\t01/08/2026\t24/08/2026\tPERSONA TRES",
  AGOSTO[1]+"\t01/08/2026\t26/08/2026\tPERSONA CUATRO",
])
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    for i,r in enumerate(AHORA+AGOSTO):
        B.ir_a(pag,r); B.pegar_tira(pag,TIRA.replace("46855268","4685526"+str(i)))
        B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p"+str(i)+"@gmail.com")
        B.escribir(pag,"#cc_res","13687"+str(i)); B.escribir(pag,"#cc_fechaRes","26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(450); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(700)

    print("1) LA REVISIÓN PREVIA AVISA DE QUE SON DOS SEMANAS")
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1600)
    ok(pag.locator("#preflightDialog[open]").count()==1, "la revisión se abre")
    res = pag.locator("#preflightResumen").inner_text()
    lista = pag.locator("#preflightLista").inner_text()
    ok("MEZCLA 2 SEMANAS" in res.upper(), "el resumen lo dice → "+res[res.upper().find("MEZCLA")-10:][:95])
    ok("semana del" in lista, "y desglosa cada semana")
    ok(lista.count("radicado(s)") >= 2, "con su cantidad cada una")
    ok(pag.locator('button[data-preflight-semana]').count()==2, "con un botón por semana para bajar solo esa")

    print("2) EL BOTÓN LLEVA AL CUADRE CON EL RANGO DE ESA SEMANA PUESTO")
    pag.locator('button[data-preflight-semana]').first.click(); pag.wait_for_timeout(1200)
    ok(pag.locator("#cuadreDialog[open]").count()==1, "abre el cuadre")
    d1, d2 = pag.input_value("#cuadreDesde"), pag.input_value("#cuadreHasta")
    ok(d1=="2026-09-28" and d2=="2026-10-04", "con la semana más reciente puesta → "+d1+" a "+d2)
    rango = pag.locator("#cuadreRango").inner_text()
    ok("2" in rango.split("\n")[0], "y dice que saldrían 2 → "+rango.split("\n")[0][:70])

    print("3) LA DESCARGA ACOTADA TRAE SOLO ESA SEMANA")
    with pag.expect_download(timeout=25000) as dl:
        pag.click("#cuadreRangoDescargar"); pag.wait_for_timeout(1500)
    ruta=os.path.join(os.path.dirname(__file__),"masiva_una_semana.xlsx"); dl.value.save_as(ruta)
    ws=openpyxl.load_workbook(ruta).active
    rads=[str(ws.cell(row=i,column=1).value) for i in range(2,ws.max_row+1)]
    ok(sorted(rads)==sorted(AHORA), "solo los dos de esta semana → "+str(rads))
    for a in AGOSTO: ok(a not in rads, "  no lleva el de agosto "+a)

    print("4) CON UNA SOLA SEMANA NO ESTORBA")
    pag.click("#cuadreClose"); pag.wait_for_timeout(400)
    # Se mueven los dos de agosto a la misma semana que los otros. (Borrarlos por almacenamiento
    # no sirve: la copia de la nube los devuelve en la siguiente fusión, que es exactamente lo que
    # la app debe hacer. Hay que subir la marca de tiempo para que mande lo que se escribe aquí.)
    pag.evaluate("""(ags)=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const l = JSON.parse(localStorage.getItem(k));
      l.forEach(r=>{ if(ags.indexOf(r.radicado)>-1){ r.fechaAsignacion='29-09-2026'; r.modificadoEn=Date.now()+60000; } });
      localStorage.setItem(k, JSON.stringify(l));
    }""", AGOSTO)
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1600)
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1600)
    if pag.locator("#preflightDialog[open]").count():
        res2 = pag.locator("#preflightResumen").inner_text()
        ok("MEZCLA" not in res2.upper(), "con una sola semana ya no avisa → "+res2[:80])
        ok(pag.locator('button[data-preflight-semana]').count()==0, "y no pinta el bloque de semanas")
        pag.click("#preflightCancel")
    else:
        ok(True, "con una sola semana ni siquiera abre la revisión")

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
