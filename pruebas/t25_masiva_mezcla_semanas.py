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
# Hasta el 04-11-2026 no se bloqueaba la entrega (se avisaba y se ofrecía bajar una sola semana).
# Desde el rediseño simple, con su visto bueno, SÍ se bloquea: la masiva es de una semana, y una
# lista con dos lo dice desde que pasa, en una franja fija arriba, no al final.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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

    print("1) LA FRANJA DE ARRIBA DICE QUE SON DOS SEMANAS, SIN TOCAR NADA")
    franja = pag.locator("#avisoSemanas")
    ok(franja.is_visible(), "la franja se ve")
    t = franja.inner_text()
    ok("2 semanas" in t, "dice cuántas semanas → "+t[:90])
    ok(t.count("semana del") == 2, "y desglosa cada semana")
    ok("24-08-2026" in t and "28-09-2026" in t, "con sus fechas → "+t[-200:])
    ok(all(r in t for r in AHORA+AGOSTO), "y los radicados de cada una")

    print("2) LA MASIVA NO SALE ASÍ")
    ok(B.descargar(pag) is None, "no se descarga")
    ok("semanas" in B.toast(pag), "y dice por qué → "+B.toast(pag)[:90])

    print("3) CON UNA SOLA SEMANA, LA FRANJA SE VA Y LA MASIVA SALE")
    # Se mueven los dos de agosto a la misma semana que los otros, desde OTRA ventana (escrito desde
    # esta misma página, la app lo pisaría al recargar con lo que tiene en pantalla). Se sube la marca
    # de tiempo para que mande lo que se escribe aquí.
    B.ir_a(pag, AHORA[0])
    p2 = ctx.new_page(); p2.goto("http://127.0.0.1:8871/manifest.webmanifest")
    p2.evaluate("""(ags)=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const l = JSON.parse(localStorage.getItem(k));
      l.forEach(r=>{ if(ags.indexOf(r.radicado)>-1){ r.fechaAsignacion='29-09-2026'; r.modificadoEn=Date.now()+60000; } });
      localStorage.setItem(k, JSON.stringify(l));
    }""", AGOSTO)
    p2.close(); pag.wait_for_timeout(1000)
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    B.entrar_en(pag, "prueba@gmail.com")
    pag.wait_for_timeout(1600)
    ok(not pag.locator("#avisoSemanas").is_visible(), "la franja se fue sola")
    ruta = B.descargar(pag, ruta=os.path.join(os.path.dirname(__file__),"masiva_una_semana.xlsx"), espera=20000)
    ok(ruta is not None, "y la masiva sale")
    if ruta:
        ws=openpyxl.load_workbook(ruta).active
        rads=[str(ws.cell(row=i,column=1).value) for i in range(2,ws.max_row+1)]
        ok(sorted(rads)==sorted(AHORA+AGOSTO), "con los cuatro → "+str(rads))

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
