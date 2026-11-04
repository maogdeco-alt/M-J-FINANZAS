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
#
# Desde el 04-11-2026 una lista con dos semanas de asignación no descarga la masiva (invariante I4):
# lo dice una franja fija arriba, con los radicados de cada semana, y no descarta ninguno.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
    pag.locator('#wrap_pruebas input[value="SI"]').check(); pag.wait_for_timeout(250)
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
      nuevo.res = ''; nuevo.fechaRes = '';   // apenas empezado (un agendamiento no lleva resolución)
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
    ruta=B.descargar(pag, boton="#downloadAgendaBtn", ruta=os.path.join(os.path.dirname(__file__),"agenda_semanas.xlsx"), espera=20000)
    ok(ruta is not None, "la plantilla sale → "+B.toast(pag)[:100])
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
      lista.forEach(r=>{ if(r.radicado===rad){ r.formato='T14'; r.res = r.res || '1368712'; r.fechaRes = r.fechaRes || '26/07/2024'; r.modificadoEn = Date.now()+60000; } });
      localStorage.setItem(k, JSON.stringify(lista));
    }""", REASIG)
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    B.entrar_en(pag, "prueba@gmail.com")
    pass
    pag.wait_for_timeout(1500)
    ok(pag.locator("#masivaListaBadge").inner_text()=="3",
       "los 3 entran a la masiva (no se descartó ninguno) → "+pag.locator("#masivaListaBadge").inner_text())
    ok(B.descargar(pag) is None, "la masiva NO sale con dos semanas mezcladas")
    franja = pag.locator("#avisoSemanas")
    ok(franja.is_visible(), "una franja fija arriba lo dice")
    t = franja.inner_text()
    ok("2 semanas" in t and "28-09-2026" in t and "05-10-2026" in t, "con las dos semanas → "+t[-260:])
    ok(t.count(REASIG)==2, "y nombra las dos asignaciones del mismo radicado, sin descartar ninguna")

    print("4) UN PEGADO DOBLE DE VERDAD (misma fecha) TAMPOCO PASA CALLADO")
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
    B.entrar_en(pag, "prueba@gmail.com")
    pag.wait_for_timeout(1500)
    pag.evaluate("""()=>{const b=document.querySelector('#filterTabs button[data-filter="all"]'); if(b) b.click();}""")
    pag.wait_for_timeout(400)
    ok(pag.locator("#queuePanel .queue-item").count()==4,
       "hay 4 filas en la lista, ninguna se borró sola → "+str(pag.locator("#queuePanel .queue-item").count()))
    ok(pag.locator("#masivaListaBadge").inner_text().startswith("faltan"),
       "y el botón de la masiva dice que faltan → "+pag.locator("#masivaListaBadge").inner_text())
    B.ir_a(pag, OTRO)
    ok("DUPLICADO" in " ".join(B.faltas(pag)) or len(B.faltas(pag))>0, "la fila repetida dice por qué → "+" | ".join(B.faltas(pag))[:120])

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
