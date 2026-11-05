# PÁGINA DE INICIO SIN CLAVE, Y LA SESIÓN COMPARTIDA ENTRE LA PRINCIPAL Y LA FLOTANTE (04-11-2026)
#
# Pedido de la usuaria: "debe haber una página de inicio pero SIN clave, ya que es solo para mí".
# La clave se pide UNA sola vez por computador (la nube la necesita); después, solo "Entrar".
#
# Y el hueco que apareció en la auditoría del guardado: Supabase cambia el refresh_token en cada
# renovación (cada hora) y, si alguien usa uno ya gastado, ANULA la sesión entera. La principal y
# la flotante tenían cada una su copia en memoria: la segunda en renovar gastaba el viejo y las dos
# dejaban de subir a la nube. Aquí el servidor de mentira se comporta como Supabase (modo rotación)
# y se comprueba que eso ya no pasa. Datos inventados.
import sys, os, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
RAD = "202670000000040"
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def mock(ruta, metodo="POST"):
    r = urllib.request.Request("http://127.0.0.1:9870" + ruta, method=metodo, data=b"{}" if metodo == "POST" else None)
    return json.loads(urllib.request.urlopen(r, timeout=5).read() or b"{}")
def dentro(p):
    p.wait_for_function("""()=>{const d=document.getElementById('authDialog');const u=document.getElementById('userLabel');
      return d && !d.open && u && u.textContent && u.textContent!=='Iniciar sesión';}""", timeout=20000)
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.reiniciar(); mock("/__rotacion")
    pag.goto(B.URL, wait_until="domcontentloaded")
    pag.wait_for_selector("#loginEmail:visible", timeout=20000)
    ok(pag.locator("#loginPassword").is_visible(), "la primera vez en este computador pide correo y clave")
    pag.fill("#loginEmail", "prueba@gmail.com"); pag.fill("#loginPassword", "123456"); pag.click("#loginBtn")
    dentro(pag); pag.wait_for_timeout(800)
    B.importar(pag, RAD + "\t01/10/2026\t05/10/2026\tPERSONA DE PRUEBA")

    pag.reload(wait_until="domcontentloaded")
    pag.wait_for_selector("#inicioEntrarBtn:visible", timeout=20000)
    ok(not pag.locator("#loginPassword").is_visible(), "al volver a abrir la app NO pide clave")
    ok("Prueba" in pag.inner_text("#inicioNombre"), "la página de inicio la saluda por su nombre")
    pag.click("#inicioEntrarBtn"); dentro(pag); pag.wait_for_timeout(1200)
    ok(RAD in pag.inner_text("#queuePanel"), "con Entrar está todo lo que tenía guardado")
    ok(not pag.locator("#userBadge").is_enabled() or pag.get_attribute("#userBadge", "tabindex") == "-1",
       "ya no hay cambio de usuario desde el encabezado")

    flo = ctx.new_page(); flo.set_viewport_size({"width": 620, "height": 540}); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    dentro(flo); flo.wait_for_timeout(1500)
    ok(True, "la flotante entra sola, sin página de inicio ni clave")

    # Pasa "una hora": vencen los tokens de acceso. La principal guarda y renueva.
    mock("/__expirar")
    B.ir_a(pag, RAD); B.escribir(pag, "#cc_direccion", "persona@gmail.com"); pag.click("#cc_save")
    pag.wait_for_timeout(3000)
    # Pasa otra "hora": ahora renueva la flotante, que tenía en memoria el token del principio.
    mock("/__expirar")
    ok(B.ir_a_compacto(flo, RAD), "la flotante llega al radicado")
    B.escribir(flo, "#cc_res", "1368706"); flo.click("#cc_save"); B.confirmar_nombre(flo)
    flo.wait_for_timeout(3500)
    st = mock("/__rotacion", "GET")
    ok(st.get("reusos", 0) == 0, "ninguna ventana gastó un token ya usado → %r" % st)
    ok(not st.get("anulada"), "la sesión en la nube sigue viva después de que renovaran las dos")
    estado_flo = flo.inner_text("#saveStatus"); estado_pag = pag.inner_text("#saveStatus")
    ok("sincronizado con la nube" in estado_flo, "la flotante sigue subiendo a la nube → %r" % estado_flo)
    ok("sincronizado con la nube" in estado_pag, "y la principal también → %r" % estado_pag)
    # El 401 del token vencido lo escribe el navegador solo, antes de que la app renueve: es a propósito.
    err[:] = [e for e in err if "401 (Unauthorized)" not in e]
    ok(not err and not err2, "sin errores de JavaScript → %r %r" % (err, err2))
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
