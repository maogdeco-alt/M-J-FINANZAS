# EL AVISO TIENE QUE VALER ALGO. Dos caras de la misma moneda:
#   (a) no puede saltar en radicados que todavía no se han trabajado (si sale siempre, se cierra
#       sin leer, y ahí es donde se pierde la alarma de verdad);
#   (b) pero TIENE que saltar en cuanto se trabaja uno y algo queda mal.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T="\t"
BLOQUE="\n".join("2026ER%03d\t01/09/2026\t03/09/2026\tPERSONA %d"%(i,i) for i in range(1,7))
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    pag.evaluate("()=>{const b=document.querySelector('#filterTabs button[data-filter=\"all\"]'); if(b) b.click();}")
    pag.wait_for_timeout(300)

    print("(a) recorrer radicados SIN empezar: no debe frenar ni una vez")
    veces=0
    for i in list(range(1,7))*2:
        pag.locator('#queuePanel .queue-item', has_text="2026ER%03d"%i).first.click()
        pag.wait_for_timeout(250)
        if pag.locator("#alertaInmediataDialog[open]").count():
            veces+=1
            pag.evaluate("()=>document.getElementById('alertaInmediataDialog').close()")
            pag.wait_for_timeout(120)
    ok(veces==0, "12 saltos, veces que frenó: "+str(veces))

    print("(b) en cuanto se trabaja uno y queda mal, SÍ frena")
    B.ir_a(pag,"2026ER001")
    # se clasifica pero se deja sin comparendo: eso sí es una anomalía de verdad
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p@gmail.com")
    pag.click("#cc_save"); pag.wait_for_timeout(600); B.confirmar_nombre(pag)
    pag.locator('#queuePanel .queue-item', has_text="2026ER002").first.click()
    pag.wait_for_timeout(600)
    av=" / ".join(B.avisos_alerta(pag))
    ok(pag.locator("#alertaInmediataDialog[open]").count()==1, "frena al dejar atrás uno trabajado y mal")
    ok("comparendo" in av.lower(), "y dice qué le falta → "+av[:120])
    ok("el formato  sí" not in av, "sin huecos en el texto (antes decía «el formato  sí lo exige»)")
    B.cerrar_alerta(pag)
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
