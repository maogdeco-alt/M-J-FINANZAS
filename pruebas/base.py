# Utilidades comunes a todas las pruebas de la app. TODO se hace por la interfaz de verdad
# (clics y teclado), como lo haría la usuaria: la app está dentro de una función cerrada y no
# expone nada por dentro, y así la prueba comprueba lo mismo que ella ve.
import urllib.request
from playwright.sync_api import sync_playwright

def reiniciar():
    """Deja la base de mentira en blanco: cada prueba empieza como el primer día."""
    r = urllib.request.Request("http://127.0.0.1:9870/__reset", method="DELETE")
    urllib.request.urlopen(r, timeout=5).read()

URL = "http://127.0.0.1:8871/index_test.html"
CHROMIUM = "/opt/pw-browsers/chromium"

def abrir(pw, headless=True):
    nav = pw.chromium.launch(executable_path=CHROMIUM, headless=headless, args=["--no-sandbox"])
    ctx = nav.new_context(accept_downloads=True, viewport={"width":1400,"height":950})
    errores = []
    pag = ctx.new_page()
    pag.on("pageerror", lambda e: errores.append("pageerror: " + str(e)))
    pag.on("console", lambda m: errores.append("console." + m.type + ": " + m.text) if m.type == "error" else None)
    return nav, ctx, pag, errores

def entrar(pag, correo="prueba@gmail.com", clave="123456", limpio=True):
    if limpio: reiniciar()
    pag.goto(URL, wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail", timeout=20000)
    pag.fill("#loginEmail", correo)
    pag.fill("#loginPassword", clave)
    pag.click("#loginBtn")
    pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(700)

def importar(pag, bloque):
    # Importar vive en su propia ventana (se abre con el botón del encabezado), igual que para ella.
    pag.click("#abrirImportarBtn")
    pag.wait_for_selector("#importDialog[open]", timeout=10000)
    pag.evaluate("""(b)=>{
      const acc=document.getElementById('paso1Accordion'); if(acc) acc.open=true;
      const t=document.getElementById('bulkPaste'); t.value=b;
      t.dispatchEvent(new Event('input',{bubbles:true}));
    }""", bloque)
    pag.click("#importBtn")
    pag.wait_for_timeout(700)
    if pag.locator("#importReportDialog[open]").count():
        pag.click("#importReportCerrar")
        pag.wait_for_timeout(300)
    if pag.locator("#importDialog[open]").count():
        pag.click("#importDialogClose")
        pag.wait_for_timeout(300)

def ir_a(pag, radicado):
    """Selecciona un radicado haciendo clic en su fila de la cola, como la usuaria."""
    pag.evaluate("""()=>{
      const b=document.querySelector('#filterTabs button[data-filter="all"]'); if(b) b.click();
    }""")
    pag.wait_for_timeout(200)
    fila = pag.locator('#queuePanel .queue-item', has_text=radicado).first
    fila.click()
    cerrar_alerta(pag)
    pag.wait_for_timeout(300)

def ir_a_compacto(pag, radicado, vueltas=12):
    """En la ventana flotante la cola no se ve: se navega con "Siguiente", como ahí mismo."""
    for _ in range(vueltas):
        if radicado in pag.locator("#cc_radicadoLabel").inner_text(): return True
        pag.click("#cc_next"); pag.wait_for_timeout(350); cerrar_alerta(pag)
    return radicado in pag.locator("#cc_radicadoLabel").inner_text()

def pegar_tira(pag, tira):
    pag.evaluate("""(t)=>{
      const el=document.getElementById('cc_comparendo');
      el.value=t; el.dispatchEvent(new Event('input',{bubbles:true}));
    }""", tira)
    pag.wait_for_timeout(250)

def escribir(pag, sel, valor):
    pag.fill(sel, valor)
    pag.dispatch_event(sel, "input")
    pag.wait_for_timeout(120)

def confirmar_nombre(pag):
    """La pregunta de "¿es la misma persona?" no es lo que se está probando aquí: se responde que sí."""
    if pag.locator("#nombreMismatchDialog[open]").count():
        pag.click("#nombreMismatchYes")
        pag.wait_for_timeout(300)

def avanzar(pag):
    """Guardar y siguiente, pasando por los diálogos que no son el objeto de la prueba."""
    confirmar_nombre(pag)
    pag.click("#cc_saveNext")
    pag.wait_for_timeout(500)
    confirmar_nombre(pag)
    pag.wait_for_timeout(400)

def cerrar_alerta(pag):
    """Cierra el aviso inmediato sin 'corregir' ni 'confirmar': lo más neutro posible."""
    if pag.locator("#alertaInmediataDialog[open]").count():
        pag.evaluate("()=>document.getElementById('alertaInmediataDialog').close()")
        pag.wait_for_timeout(200)

def chips(pag):
    return [c.strip() for c in pag.locator("#ccInsights .insight-chip").all_inner_texts()]

def desglose(pag):
    """Los campos separados de la tira, como los muestra la app."""
    pag.evaluate("()=>{const d=document.querySelector('.breakdown-details'); if(d) d.open=true;}")
    out = {}
    for it in pag.locator("#cc_breakdown .bd-item").all():
        k = it.locator(".k").inner_text().strip()
        v = it.locator(".v").inner_text().strip()
        out[k] = v
    return out

def avisos_alerta(pag):
    if not pag.locator("#alertaInmediataDialog[open]").count(): return []
    return [t.strip() for t in pag.locator("#alertaInmediataLista .alerta-item").all_inner_texts()]
