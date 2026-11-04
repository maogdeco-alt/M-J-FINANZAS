# LA FLOTANTE AL DÍA, EN SILENCIO (04-11-2026)
#
# Auditoría del guardado entre la principal y la flotante, pedida por la usuaria al aprobar el
# rediseño ("no olvides revisar a profundidad la ventana flotante y toda la forma de almacenar").
#   · El historial no viajaba entre ventanas: si se cerraba la semana en la principal, la flotante
#     seguía con el historial viejo hasta chocar con la nube. Ahora lo junta en el momento.
#   · Lo que se escribe en una ventana llega a la otra sin mensajes ("se actualizaron desde la otra
#     ventana", "traer lo más reciente"): estar al día es lo normal, no una noticia.
#   · La flotante muestra lo mismo que la principal: PENDIENTE con lo que falta, o LISTO.
# Se corre SIN NUBE (el servidor de mentira apagado para la flotante no es posible, así que se
# mira el almacenamiento del navegador directamente). Datos inventados.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
R1, R2 = "202670000000201", "202670000000202"
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, R1 + "\t02/11/2026\t03/11/2026\tJOSE PEREZ CASTANEDA\n" + R2 + "\t02/11/2026\t03/11/2026\tANA MARIA RUIZ LOPEZ")
    flo = ctx.new_page(); flo.set_viewport_size({"width": 620, "height": 540}); err2 = []
    flo.on("pageerror", lambda e: err2.append(str(e)))
    toasts_flo = []
    flo.goto(B.URL + "#flotante=1", wait_until="domcontentloaded")
    B.entrar_en(flo, "prueba@gmail.com"); flo.wait_for_timeout(1500)
    flo.evaluate("""()=>{ window.__t=[]; const el=document.getElementById('toast');
      new MutationObserver(()=>{ if(el.textContent) window.__t.push(el.textContent); }).observe(el,{childList:true,characterData:true,subtree:true}); }""")

    # 1) En la flotante: T14 sin comparendo -> PENDIENTE con lo que falta, igual que en la principal.
    ok(B.ir_a_compacto(flo, R1), "la flotante llega al radicado")
    B.escribir(flo, "#cc_formato", "T14"); B.escribir(flo, "#cc_direccion", "jose@gmail.com")
    flo.click("#cc_saveNext"); flo.wait_for_timeout(800); B.confirmar_nombre(flo)
    caja = flo.inner_text("#avisoImperativas") if flo.locator("#avisoImperativas:visible").count() else ""
    ok(R1 in flo.inner_text("#cc_radicadoLabel") and "PENDIENTE" in caja, "en la flotante tampoco sigue de largo → %r" % caja[:80])

    # 2) Lo de la flotante llega a la principal, sin mensajes.
    pag.wait_for_timeout(1200)
    B.ir_a(pag, R1)
    ok(pag.input_value("#cc_direccion") == "jose@gmail.com" and pag.input_value("#cc_formato") == "T14",
       "lo escrito en la flotante está en la principal")
    # 3) Y lo de la principal, en la flotante.
    B.escribir(pag, "#cc_res", "1368706")
    pag.click("#cc_save"); pag.wait_for_timeout(1500); B.confirmar_nombre(pag)
    flo.wait_for_timeout(800)
    ok(flo.input_value("#cc_res") == "1368706", "lo escrito en la principal aparece en la flotante")
    t = flo.evaluate("window.__t")
    ok(not any("otra ventana" in x or "más reciente" in x for x in t), "sin mensajes de «otra ventana» → %r" % t)

    # 4) Cerrar la semana en la principal: el historial llega a la flotante en el momento.
    antes = flo.evaluate("""()=>{try{return JSON.parse(localStorage.getItem('radicados_historial_v1::prueba@gmail.com')||'[]').length}catch(e){return -1}}""")
    pag.click("#cerrarSemanaNavBtn"); pag.wait_for_timeout(600)
    if pag.locator("#confirmDialog[open]").count(): pag.click("#confirmOk")
    pag.wait_for_timeout(2000)
    flo.wait_for_timeout(600)
    ok(not flo.locator("#captureForm").is_visible() and flo.inner_text("#statTotal") == "0", "la flotante ya no muestra la semana cerrada")
    flo.evaluate("()=>document.getElementById('historialTriggerBtn').click()"); flo.wait_for_timeout(800)
    hist = flo.inner_text("#historialDialog") if flo.locator("#historialDialog[open]").count() else ""
    ok(R1 in hist and R2 in hist, "el historial de la flotante ya tiene la semana cerrada, sin esperar a la nube")
    ok(not err and not err2, "sin errores de JavaScript → %r %r" % (err, err2))
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
