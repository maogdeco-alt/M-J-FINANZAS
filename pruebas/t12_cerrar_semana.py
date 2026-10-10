# "No veo el botón de borrar los radicados de la semana". Existía y funcionaba, pero vivía al
# fondo de la ventana "Documentos". Esta prueba vigila que se pueda encontrar Y que siga
# haciendo lo mismo desde los dos sitios, sin perder nada.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T="\t"
def tira(i,man=False): return T.join(["1100100000004685%04d"%i,"C02","19/04/2025","19/04/2025","No",
  "COMPARENDERA" if man else "CAMARAS SALVAVIDAS","VIGENTE","","","","CEDULA DE CIUDADANIA",
  "520000%03d"%i,"PERSONA %d"%i,"ABC%03d"%i])
BLOQUE="\n".join("2026ER%03d\t01/09/2026\t03/09/2026\tPERSONA %d"%(i,i) for i in (1,2,3))
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

def preparar(pag):
    B.importar(pag,BLOQUE)
    for i in (1,2):
        B.ir_a(pag,"2026ER%03d"%i); B.pegar_tira(pag,tira(i))
        B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p%d@gmail.com"%i)
        B.escribir(pag,"#cc_res","13687%02d"%i); B.escribir(pag,"#cc_fechaRes","26/07/2024")
        pag.click("#cc_save"); pag.wait_for_timeout(450); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    B.ir_a(pag,"2026ER003"); B.pegar_tira(pag,tira(3,True))
    B.escribir(pag,"#cc_formato","AGENDAMIENTO"); B.escribir(pag,"#cc_direccion","p3@gmail.com")
    pag.locator('#wrap_pruebas input[value="NO"]').check(); pag.wait_for_timeout(250)
    pag.click("#cc_save"); pag.wait_for_timeout(550); B.confirmar_nombre(pag); B.cerrar_alerta(pag)

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); preparar(pag)

    print("1) el botón se ve SIN abrir ninguna ventana")
    b=pag.locator("#cerrarSemanaNavBtn")
    ok(b.is_visible(), "está en la barra de arriba")
    ok("Cerrar semana" in b.inner_text(), "y dice lo que hace → "+b.inner_text().replace("\n"," "))
    ok(pag.locator("#cerrarSemanaBadge").inner_text()=="3", "con la cifra de lo que se cerraría → "+pag.locator("#cerrarSemanaBadge").inner_text())
    ok(b.bounding_box()["y"] < 200, "y arriba del todo, sin tener que bajar (y=%d px)" % b.bounding_box()["y"])

    print("2) pide confirmación antes de borrar nada")
    b.click(); pag.wait_for_timeout(700)
    ok(pag.locator("#confirmDialog[open]").count()==1, "sale el aviso de confirmación")
    txt=pag.locator("#confirmDialog").inner_text()
    ok("3" in txt, "dice cuántos se cierran")
    ok("AGENDAMIENTO" in txt.upper(), "y avisa del agendamiento que también se cierra")
    pag.click("#confirmCancel"); pag.wait_for_timeout(400)
    ok(pag.locator("#queuePanel .queue-item").count()==3, "al cancelar NO se borra nada")

    print("3) al confirmar: se archiva y se limpia todo")
    pag.click("#cerrarSemanaNavBtn"); pag.wait_for_timeout(600)
    pag.click("#confirmOk"); pag.wait_for_timeout(1300)
    ok(pag.locator("#queuePanel .queue-item").count()==0, "la cola queda vacía")
    ok(pag.locator("#cerrarSemanaBadge").inner_text()=="0", "y la cifra del botón vuelve a 0")
    pag.click("#agendaTriggerBtn"); pag.wait_for_timeout(600)
    ok(pag.locator("#agendaPanel .ws-row").count()==0, "los agendamientos también se cierran")
    pag.click("#agendaDialogClose"); pag.wait_for_timeout(300)
    pag.click("#settingsBtn"); pag.wait_for_timeout(700)
    filas=pag.locator("#historyTableBody tr")
    ok(filas.count()>0, "la semana queda archivada en el historial (%d fila/s)" % filas.count())
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())"); pag.wait_for_timeout(300)

    print("4) el botón de siempre, dentro de Documentos, sigue haciendo lo mismo")
    preparar(pag)
    pag.click("#abrirDocumentosBtn"); pag.wait_for_timeout(600)
    ok(pag.locator("#clearAllBtn").is_visible(), "sigue ahí donde estaba")
    pag.click("#clearAllBtn"); pag.wait_for_timeout(700)
    ok(pag.locator("#confirmDialog[open]").count()==1, "y abre el mismo aviso")
    pag.click("#confirmOk"); pag.wait_for_timeout(1300)
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())"); pag.wait_for_timeout(400)
    ok(pag.locator("#queuePanel .queue-item").count()==0, "y cierra la semana igual")
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
