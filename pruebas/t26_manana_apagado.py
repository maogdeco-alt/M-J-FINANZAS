# EL BLOQUE DE LA MAÑANA, APAGADO (decisión del 10 de octubre de 2026).
#
# La app se enfoca al 100% en la masiva y los agendamientos. El bloque de la mañana se APAGA con
# una constante (BLOQUE_MANANA_ACTIVO = false), no se borra: volver atrás tiene que costar un
# minuto, no rehacerlo, y lo guardado en el navegador y en Supabase no se toca.
#
# Esta prueba vigila las dos mitades de esa promesa:
#   (a) apagado es apagado: ni selector, ni sección, ni barra, ni nada que se pueda pulsar;
#   (b) el bloque de la TARDE funciona igual que siempre, que es lo único que importa ahora.
import sys, os; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B, openpyxl
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
R1="202661203706582"
BLOQUE=R1+"\t01/09/2026\t28/09/2026\tPERSONA UNO"
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag)

    print("1) NO HAY NADA DE LA MAÑANA A LA VISTA")
    ok(not pag.locator(".bloque-sel").is_visible(), "el selector de bloque no se ve")
    ok(not pag.locator("#bloqueManana").is_visible(), "la sección de la mañana no se ve")
    ok(not pag.locator("#mananaNav").is_visible(), "su barra de trabajo no se ve")
    ok(not pag.locator("#selBloqueManana").is_visible(), "ni el botón para entrar")
    ok("bloque-manana" not in (pag.get_attribute("html","class") or ""),
       "la página no está en modo mañana")

    print("2) NI SIQUIERA FORZÁNDOLO SE PUEDE ENTRAR")
    # Alguien que tuviera guardada la preferencia "manana" de antes del apagado.
    pag.evaluate("""()=>{
      Object.keys(localStorage).filter(k=>k.indexOf('radicados_bloque_v1')===0)
        .forEach(k=>localStorage.setItem(k,'manana'));
    }""")
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1600)
    ok(not pag.locator("#bloqueManana").is_visible(),
       "con la preferencia vieja puesta en «manana», sigue sin abrirse")
    ok(pag.locator("#paso2Section").is_visible(), "y el Paso 2 de la masiva sí está a la vista")

    print("3) LO GUARDADO DE LA MAÑANA NO SE TOCÓ")
    # Se simula trabajo de la mañana guardado de antes del apagado.
    pag.evaluate("""()=>{
      const k='radicados_manana_v1::prueba@gmail.com';
      localStorage.setItem(k, JSON.stringify({fechaSheet:'30/09/2026',nombre:'ALEJANDRA',
        catalogo:[],personas:[],sin:[{rad:'1',cl:'T14'}],ia:[],historial:[],actualizadoEn:123}));
    }""")
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1800)
    guardado = pag.evaluate("()=>localStorage.getItem('radicados_manana_v1::prueba@gmail.com')")
    ok(guardado and "ALEJANDRA" in guardado and '"actualizadoEn":123' in guardado,
       "el trabajo guardado de la mañana sigue intacto, sin tocar")

    print("4) LA MASIVA FUNCIONA IGUAL QUE SIEMPRE")
    B.importar(pag,BLOQUE)
    B.ir_a(pag,R1); B.pegar_tira(pag,TIRA)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","ciudadano@gmail.com")
    B.escribir(pag,"#cc_res","136871"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(600); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(600)
    ok(pag.locator("#masivaListaBadge").inner_text()=="1",
       "el radicado entra a la masiva → "+pag.locator("#masivaListaBadge").inner_text())
    with pag.expect_download(timeout=25000) as dl:
        pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
        if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightProceed")
    ruta=os.path.join(os.path.dirname(__file__),"masiva_sin_manana.xlsx"); dl.value.save_as(ruta)
    ws=openpyxl.load_workbook(ruta).active
    ok(ws.max_row==2 and str(ws.cell(row=2,column=1).value)==R1,
       "y el archivo sale bien → "+str(ws.cell(row=2,column=1).value))
    ok(ws.max_column==27, "con las 27 columnas → "+str(ws.max_column))

    print("5) LAS VENTANAS Y BOTONES DE LA TARDE SIGUEN TODOS")
    for ident, nombre in (("#abrirDocumentosBtn","Documentos"), ("#agendaTriggerBtn","Agendamientos"),
                          ("#historialTriggerBtn","Historial"), ("#cerrarSemanaNavBtn","Cerrar semana"),
                          ("#abrirImportarBtn","Importar"), ("#reglasBtn","Reglas")):
        ok(pag.locator(ident).is_visible(), "  sigue el botón de "+nombre)

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
