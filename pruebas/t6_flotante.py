# LA VENTANA FLOTANTE. "ha sido una debilidad de la app": todo lo nuevo tiene que verse y
# guardarse también ahí, no solo en la pantalla grande.
from playwright.sync_api import sync_playwright
import base as B, sys
T="\t"
TIRA = T.join(["11001000000046855268","D01","19/04/2025","","No","COMPARENDERA","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","JOSE PEREZ CASTANEDA","CALLE 13 36 31 BAHIA 1","ABC123"])
BLOQUE = "2026ER800\t01/09/2026\t03/09/2026\tJOSE PEREZ CASTANEDA\n2026ER801\t01/09/2026\t03/09/2026\tOTRA PERSONA"
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav,ctx,pag,errores=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)

    # segunda ventana, la "flotante" (la misma página con #flotante=1, que es lo que carga el iframe)
    flo = ctx.new_page()
    err_flo=[]
    flo.on("pageerror", lambda e: err_flo.append("pageerror: "+str(e)))
    flo.on("console", lambda m: err_flo.append("console."+m.type+": "+m.text) if m.type=="error" else None)
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    flo.wait_for_selector("#loginEmail", timeout=20000)
    flo.fill("#loginEmail","prueba@gmail.com"); flo.fill("#loginPassword","123456")
    flo.click("#loginBtn"); flo.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    flo.wait_for_timeout(1200)

    print("1) arranca en modo compacto")
    ok(flo.evaluate("()=>document.documentElement.classList.contains('es-flotante')"), "la clase es-flotante está puesta")
    ok(flo.locator("#captureForm").is_visible(), "el formulario de captura se ve")

    print("2) la tira de Fénix se separa igual de bien aquí")
    ok(B.ir_a_compacto(flo,"2026ER800"), "se llega al radicado con Siguiente")
    B.pegar_tira(flo, TIRA)
    d = B.desglose(flo)
    ok(d.get("PLACA")=="ABC123", "la placa sale bien en la flotante → "+repr(d.get("PLACA")))
    ok("CALLE 13" in (d.get("DIRECCIÓN INFRACTOR") or ""), "y la dirección va aparte")

    print("3) la pregunta de SÍ/NO también está aquí")
    B.escribir(flo,"#cc_formato","AGENDAMIENTO")
    ok(flo.locator("#wrap_pruebas").is_visible(), "la pregunta se ve en la ventana flotante")
    flo.locator('#wrap_pruebas input[value="SI"]').check(); flo.wait_for_timeout(500)
    ok("AGENDAR CON PRUEBAS" in flo.locator("#cc_pruebasEco").inner_text(), "y se puede responder")

    print("4) lo que se escribe en la flotante queda guardado de verdad")
    B.escribir(flo,"#cc_direccion","jose@gmail.com")
    flo.click("#cc_save"); flo.wait_for_timeout(700); B.confirmar_nombre(flo); B.cerrar_alerta(flo)
    flo.wait_for_timeout(900)
    # la ventana principal, recargada, tiene que ver lo mismo
    pag.reload(wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1200)
    B.ir_a(pag,"2026ER800")
    ok(pag.input_value("#cc_formato").strip().upper()=="AGENDAMIENTO", "el formato llegó a la principal → "+repr(pag.input_value("#cc_formato")))
    ok(pag.input_value("#cc_direccion").strip()=="jose@gmail.com", "el correo llegó → "+repr(pag.input_value("#cc_direccion")))
    ok(pag.locator('#wrap_pruebas input[value="SI"]').is_checked(), "y la respuesta de las pruebas también")
    d2 = B.desglose(pag)
    ok(d2.get("PLACA")=="ABC123", "y la placa quedó guardada bien → "+repr(d2.get("PLACA")))

    print("\nerrores en la principal:", errores or "ninguno")
    print("errores en la flotante:", err_flo or "ninguno")
    if errores or err_flo: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
