# EL CASO DEL NÚMERO INFLADO (5-10-2026). La app mostraba 219 radicados para la masiva cuando en
# ORFEO los aptos de la semana eran 176, y no había forma de saber de dónde salía la diferencia.
#
# Causa: TODAS las mezclas de datos de la app comparan por `id` interno (correcto, para no perder
# trabajo), ninguna por radicado. El mismo radicado pegado en dos sitios -- dos computadores, dos
# pestañas, o antes de que baje la lista de la nube -- deja DOS filas con dos `id`, y la masiva las
# contaba y las entregaba las dos.
#
# Esta prueba reproduce esa fusión por el camino real (otra ventana escribe en el almacenamiento y
# fusionarConLoGuardado la trae) y comprueba: que el archivo sale con una sola fila por radicado,
# que la pantalla lo dice, y que el cuadre explica el número y cruza contra ORFEO.
import sys, os; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B, openpyxl
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
R1="202642110702441"; R2="202642110702442"; R3="202642110702443"
BLOQUE="\n".join([
 R1+"\t01/09/2026\t02/10/2026\tJOSE AUGUSTO LOAIZA",
 R2+"\t01/09/2026\t02/10/2026\tPERSONA DOS",
 R3+"\t01/09/2026\t02/10/2026\tPERSONA TRES",
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
    for i,rad in enumerate((R1,R2,R3)): clasificar(pag,rad,str(i+1))
    pag.wait_for_timeout(700)
    ok(pag.locator("#masivaListaBadge").inner_text()=="3", "arranca en 3 → "+pag.locator("#masivaListaBadge").inner_text())

    print("1) LA OTRA VENTANA PEGA EL MISMO BLOQUE: aparece el radicado dos veces")
    # Esto es lo que de verdad pasa: otra ventana (u otro computador, por la nube) crea sus propias
    # filas para los mismos radicados, con otros `id`. Se escribe en el almacenamiento tal como lo
    # haría esa otra ventana, y la fusión de esta la trae al guardar.
    pag.evaluate("""(args)=>{
      const [r1,r2] = args;
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const lista = JSON.parse(localStorage.getItem(k));
      const copias = lista.filter(r=>r.radicado===r1||r.radicado===r2).map(function(r){
        const c = JSON.parse(JSON.stringify(r));
        c.id = 'otraventana_'+r.radicado;
        c.modificadoEn = Date.now()+1000;
        c.res = ''; c.fechaRes = ''; c.direccion = '';   // la otra ventana la dejó a medio hacer
        return c;
      });
      localStorage.setItem(k, JSON.stringify(lista.concat(copias)));
    }""", [R1,R2])
    # Un guardado cualquiera de ESTA ventana dispara la fusión con lo que dejó la otra.
    B.ir_a(pag,R3); B.escribir(pag,"#cc_idNum","x"); pag.click("#cc_save")
    pag.wait_for_timeout(900); B.cerrar_alerta(pag)
    filas = pag.locator("#queuePanel .queue-item").count()
    ok(filas==5, "la lista tiene ahora 5 filas para 3 radicados → "+str(filas))

    print("2) EL NÚMERO DE LA MASIVA NO SE INFLA")
    badge = pag.locator("#masivaListaBadge").inner_text()
    ok(badge=="3", "el contador sigue en 3, no en 5 → "+badge)
    pag.click("#abrirDocumentosBtn"); pag.wait_for_timeout(600)
    cuenta = pag.locator("#finalDocCount").inner_text()
    ok("de 5 en tu lista" in cuenta, "y dice de cuántas filas sale → "+cuenta)
    ok("repetida" in cuenta, "nombrando las repetidas → "+cuenta)
    aviso = pag.locator("#finalDocRepesAviso")
    ok(aviso.is_visible(), "con un aviso aparte a la vista")
    ok("2 caso" in aviso.inner_text(), "que cuenta los casos → "+aviso.inner_text()[:90])

    print("3) EL CUADRE EXPLICA EL NÚMERO Y LA SUMA CUADRA")
    pag.click("#abrirCuadreBtn"); pag.wait_for_timeout(600)
    ok(pag.locator("#cuadreDialog[open]").count()==1, "el cuadre se abre")
    cuentas = pag.locator("#cuadreCuentas").inner_text()
    ok("La cuenta cuadra" in cuentas, "la comprobación da bien → "+cuentas.split("\n")[-1][:110])
    ok(pag.locator("#cuadreCuentas .cuadre-check.bien").count()==1, "y se ve en verde")
    ok("Pegados dos veces" in cuentas, "el desglose tiene la línea de pegados dos veces")
    semanas = pag.locator("#cuadreSemanas").inner_text()
    ok("Asignados esta semana" in semanas or "semanas ANTERIORES" in semanas,
       "y el reparto por fecha de asignación está")

    print("4) EL CRUCE CONTRA ORFEO DICE QUÉ SOBRA Y QUÉ FALTA")
    # ORFEO trae R1 y R2 (y uno que ella no tiene); R3 no está en ORFEO.
    FALTANTE="202642110702499"
    pag.fill("#cuadreOrfeo", R1+"\n"+R2+"\n"+FALTANTE)
    pag.click("#cuadreCruzar"); pag.wait_for_timeout(500)
    cruce = pag.locator("#cuadreCruce").inner_text()
    ok("Están en tu lista y NO en ORFEO" in cruce, "la línea de lo que sobra está")
    ok(R3 in cruce, "y nombra el que sobra ("+R3+")")
    ok(FALTANTE in cruce, "y el que falta por trabajar ("+FALTANTE+")")

    print("4b) EL CRUCE LEE RADICADOS CON LETRAS Y CON BASURA ALREDEDOR")
    # El primer lector buscaba "el primer número largo" y con radicados tipo 2026ER001234 no
    # encontraba ninguno: la lista salía vacía y el cruce decía que TODO sobraba.
    pag.fill("#cuadreOrfeo", "RADICADO\tNOMBRE\n"+R1+"\tJOSE AUGUSTO LOAIZA\n  "+R2+"  ,algo\n2026ER001234;otro")
    pag.click("#cuadreCruzar"); pag.wait_for_timeout(500)
    cruce2 = pag.locator("#cuadreCruce").inner_text()
    ok("3" in cruce2.split("\n")[0], "lee los 3 (encabezado fuera) → "+cruce2.split("\n")[0])
    ok("2026ER001234" in cruce2, "incluido el que lleva letras")

    print("4c) SI NO ENTIENDE LO PEGADO, LO DICE EN VEZ DE DECIR QUE TODO SOBRA")
    pag.fill("#cuadreOrfeo", "hola\nqué tal\nnada de esto es un radicado")
    pag.click("#cuadreCruzar"); pag.wait_for_timeout(500)
    cruce3 = pag.locator("#cuadreCruce").inner_text()
    ok("No se reconoció ningún radicado" in cruce3, "avisa → "+cruce3.split("\n")[0][:110])
    ok("NO se cruzó nada" in cruce3, "y deja claro que no cruzó nada")
    ok(R3 not in cruce3, "sin declarar que la lista entera sobra")

    print("5) EL ARCHIVO SALE SIN FILAS REPETIDAS")
    pag.click("#cuadreClose"); pag.wait_for_timeout(300)
    with pag.expect_download(timeout=25000) as dl:
        pag.click("#downloadFinalBtn"); pag.wait_for_timeout(1400)
        if pag.locator("#preflightDialog[open]").count():
            res = pag.locator("#preflightResumen").inner_text()
            lista = pag.locator("#preflightLista").inner_text()
            ok("OJO CON EL NÚMERO" in res, "la revisión previa avisa de los repetidos → "+res[:120])
            ok(pag.locator(".preflight-repes").count()>=1, "en su propio bloque")
            ok("SALE" in lista and "queda FUERA" in lista, "diciendo cuál sale y cuál no")
            ok(pag.locator('.preflight-repes button[data-preflight-corregir]').count()>=4,
               "con botón para abrir cada una de las dos filas")
            pag.click("#preflightProceed")
    ruta=os.path.join(os.path.dirname(__file__),"masiva_cuadre.xlsx"); dl.value.save_as(ruta)
    ws=openpyxl.load_workbook(ruta).active
    rads=[str(ws.cell(row=i,column=1).value) for i in range(2,ws.max_row+1)]
    ok(len(rads)==3, "el archivo trae 3 filas, no 5 → "+str(len(rads)))
    ok(len(set(rads))==len(rads), "sin ningún radicado repetido → "+str(rads))

    print("6) de cada repetido sale la fila CON MÁS TRABAJO HECHO")
    # La copia de la otra ventana venía sin resolución; la buena sí la tiene.
    col = {ws.cell(row=1,column=c).value: c for c in range(1, ws.max_column+1)}
    cRes = next((c for t,c in col.items() if t and "RESOLUCION" in str(t).upper()), None)
    if cRes:
        vacias = [str(ws.cell(row=i,column=cRes).value or "") for i in range(2,ws.max_row+1)]
        ok(all(v.strip() for v in vacias), "ninguna fila del archivo quedó sin resolución → "+str(vacias))
    else:
        ok(False, "no se encontró la columna de resolución en el archivo")

    print("7) el cuadre de ORFEO se puede descargar como prueba")
    pag.click("#abrirCuadreBtn"); pag.wait_for_timeout(500)
    pag.fill("#cuadreOrfeo", R1+"\n"+R2+"\n"+FALTANTE)
    pag.click("#cuadreCruzar"); pag.wait_for_timeout(400)
    with pag.expect_download(timeout=25000) as dl2:
        pag.click("#cuadreDescargar"); pag.wait_for_timeout(1200)
    ruta2=os.path.join(os.path.dirname(__file__),"cuadre_orfeo.xlsx"); dl2.value.save_as(ruta2)
    ws2=openpyxl.load_workbook(ruta2).active
    textos=[" ".join(str(ws2.cell(row=i,column=c).value or "") for c in range(1,ws2.max_column+1))
            for i in range(2,ws2.max_row+1)]
    ok(any(R3 in t and "SOLO EN LA APP" in t for t in textos), "el Excel marca el que sobra")
    ok(any(FALTANTE in t and "SOLO EN ORFEO" in t for t in textos), "y el que falta")

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
