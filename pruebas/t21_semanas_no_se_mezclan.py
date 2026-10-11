# NO MEZCLAR SEMANAS (5-10-2026). Reportado en el trabajo: "tengo agendamientos de la semana
# pasada mezclados y las asignaciones de esta semana están mal".
#
# CAUSA, Y FUE UN ERROR INTRODUCIDO AL ARREGLAR EL CONTEO: al quitar los radicados repetidos se
# juntaban las filas SOLO por número de radicado, dando por hecho que un radicado repetido siempre
# es un pegado doble. Es falso: un radicado se puede reasignar en otra semana (devuelto, prórroga,
# reasignación) y entonces hay DOS asignaciones distintas, las dos con trabajo real. La fila de la
# semana pasada, más completa porque ya se trabajó, ganaba y dejaba FUERA la de esta semana.
# En los AGENDAMIENTOS eso es una cita que el ciudadano no recibe.
#
# REGLA QUE SE VIGILA AQUÍ: solo se juntan las filas que son la MISMA asignación -- mismo radicado
# Y misma fecha de asignación. Si la fecha difiere, salen las dos y la app lo avisa.
import sys, os; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B, openpyxl
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
REASIG="202642110702441"   # el mismo radicado, asignado dos semanas seguidas
OTRO  ="202642110702442"
BLOQUE="\n".join([
 REASIG+"\t01/09/2026\t28/09/2026\tJOSE AUGUSTO LOAIZA",   # asignación de la SEMANA PASADA
 OTRO  +"\t01/09/2026\t05/10/2026\tPERSONA DOS",
])
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)

    print("0) la semana pasada se trabajó a fondo el radicado reasignado")
    B.ir_a(pag,REASIG); B.pegar_tira(pag,TIRA)
    B.escribir(pag,"#cc_formato","AGENDAMIENTO"); B.escribir(pag,"#cc_direccion","jose@gmail.com")
    B.escribir(pag,"#cc_res","1368711"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(600); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    B.ir_a(pag,OTRO); B.pegar_tira(pag,TIRA.replace("46855268","46855269"))
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","dos@gmail.com")
    B.escribir(pag,"#cc_res","1368722"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(600); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(600)

    print("1) ESTA semana le vuelven a asignar el MISMO radicado (otra fecha), y recién empezado")
    # Lo crea otra ventana, que es como llega de verdad: por la fusión, con su propio `id`.
    pag.evaluate("""(rad)=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const lista = JSON.parse(localStorage.getItem(k));
      const viejo = lista.find(r=>r.radicado===rad);
      const nuevo = JSON.parse(JSON.stringify(viejo));
      nuevo.id = 'reasignado_de_esta_semana';
      nuevo.fechaAsignacion = '05-10-2026';     // ESTA semana
      nuevo.modificadoEn = Date.now()+1000;
      nuevo.res = ''; nuevo.fechaRes = ''; nuevo.direccion = '';   // apenas empezado
      nuevo.formato = 'AGENDAMIENTO';
      lista.push(nuevo);
      localStorage.setItem(k, JSON.stringify(lista));
    }""", REASIG)
    B.ir_a(pag,OTRO); B.escribir(pag,"#cc_idNum","x"); pag.click("#cc_save")
    pag.wait_for_timeout(900); B.cerrar_alerta(pag)
    ok(pag.locator("#queuePanel .queue-item").count()==3, "la lista tiene 3 filas")

    print("2) LA PLANTILLA DE AGENDAMIENTOS LLEVA LAS DOS ASIGNACIONES")
    pag.click("#agendaTriggerBtn"); pag.wait_for_timeout(700)
    cuenta = pag.locator("#agendaDocCount").inner_text()
    ok("2 radicados" in cuenta, "cuenta los 2 agendamientos, no 1 → "+cuenta)
    with pag.expect_download(timeout=25000) as dl:
        pag.click("#downloadAgendaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightProceed")
    ruta=os.path.join(os.path.dirname(__file__),"agenda_semanas.xlsx"); dl.value.save_as(ruta)
    ws=openpyxl.load_workbook(ruta).active
    filas=[[str(ws.cell(row=i,column=c).value or "") for c in range(1,ws.max_column+1)]
           for i in range(2,ws.max_row+1)]
    ok(len(filas)==2, "el archivo trae las DOS filas del agendamiento → "+str(len(filas)))
    todo=" | ".join(" ".join(f) for f in filas)
    ok(todo.count(REASIG)==2, "las dos asignaciones del mismo radicado están → "+str(todo.count(REASIG)))
    pag.click("#agendaDialogClose"); pag.wait_for_timeout(300)

    print("3) LA APP AVISA DE LAS DOS ASIGNACIONES, EN VEZ DE DECIDIR POR ELLA")
    # Se pasa a T14 para que entren a la masiva y se vea el aviso en la revisión previa.
    # La marca de tiempo SE SUBE: sin eso, al recargar gana la copia de la nube (más nueva) y
    # deshace el cambio. Costó una corrida entenderlo y es culpa de la prueba, no de la app.
    pag.evaluate("""(rad)=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const lista = JSON.parse(localStorage.getItem(k));
      lista.forEach(r=>{ if(r.radicado===rad){ r.formato='T14'; r.modificadoEn = Date.now()+60000; } });
      localStorage.setItem(k, JSON.stringify(lista));
    }""", REASIG)
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1500)
    ok(pag.locator("#masivaListaBadge").inner_text()=="3",
       "los 3 entran a la masiva (no se descartó ninguno) → "+pag.locator("#masivaListaBadge").inner_text())
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
    ok(pag.locator("#preflightDialog[open]").count()==1, "la revisión previa se abre")
    res = pag.locator("#preflightResumen").inner_text()
    lista = pag.locator("#preflightLista").inner_text()
    ok("OJO CON LAS SEMANAS" in res, "avisa de las dos asignaciones → "+res[:140])
    ok("28-09-2026" in lista and "05-10-2026" in lista, "mostrando las DOS fechas")
    ok("no decide por ti" in lista or "NO decide por ti" in res, "y dice que no decide por ella")
    pag.click("#preflightCancel"); pag.wait_for_timeout(400)

    print("4) UN PEGADO DOBLE DE VERDAD (misma fecha) SÍ SE JUNTA")
    pag.evaluate("""(rad)=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const lista = JSON.parse(localStorage.getItem(k));
      const base = lista.find(r=>r.radicado===rad);
      const copia = JSON.parse(JSON.stringify(base));
      copia.id='pegado_doble'; copia.res=''; copia.fechaRes=''; copia.direccion='';
      copia.modificadoEn = Date.now()+60000;
      lista.push(copia);
      localStorage.setItem(k, JSON.stringify(lista));
    }""", OTRO)
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1500)
    pag.evaluate("""()=>{const b=document.querySelector('#filterTabs button[data-filter="all"]'); if(b) b.click();}""")
    pag.wait_for_timeout(400)
    ok(pag.locator("#queuePanel .queue-item").count()==4,
       "hay 4 filas en la lista → "+str(pag.locator("#queuePanel .queue-item").count()))
    ok(pag.locator("#masivaListaBadge").inner_text()=="3",
       "pero a la masiva van 3: el pegado doble sí se juntó → "+pag.locator("#masivaListaBadge").inner_text())
    with pag.expect_download(timeout=25000) as dl2:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightProceed")
    ruta2=os.path.join(os.path.dirname(__file__),"masiva_semanas.xlsx"); dl2.value.save_as(ruta2)
    ws2=openpyxl.load_workbook(ruta2).active
    rads=[str(ws2.cell(row=i,column=1).value) for i in range(2,ws2.max_row+1)]
    ok(len(rads)==3, "el archivo trae 3 filas → "+str(rads))
    ok(rads.count(REASIG)==2, "las DOS asignaciones del reasignado siguen ahí → "+str(rads.count(REASIG)))
    ok(rads.count(OTRO)==1, "y el pegado doble sale una sola vez → "+str(rads.count(OTRO)))

    print("5) la fila que sale del pegado doble es la que tiene el trabajo hecho")
    col = {ws2.cell(row=1,column=c).value: c for c in range(1, ws2.max_column+1)}
    cRes = next((c for t,c in col.items() if t and "RESOLUCION" in str(t).upper()), None)
    if cRes:
        fila = next(i for i in range(2,ws2.max_row+1) if str(ws2.cell(row=i,column=1).value)==OTRO)
        ok(str(ws2.cell(row=fila,column=cRes).value or "").strip()=="1368722",
           "conserva la resolución → "+str(ws2.cell(row=fila,column=cRes).value))
    else:
        ok(False, "no se encontró la columna de resolución")

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
