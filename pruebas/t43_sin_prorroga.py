# PRORROGA Y PRORROGA SDA SE ELIMINAN (04-11-2026)
#
# Pedido de la usuaria, palabra por palabra: "elimina totalmente porroga y porroga sda".
# Se exige: que no aparezcan como clasificación en ningún lado (desplegable, conteo por formato),
# tampoco para quien ya las tenía guardadas en sus Ajustes (navegador o nube); que un radicado que
# las tuviera quede PENDIENTE pidiendo otra clasificación y no salga en la masiva; y que el
# historial ya archivado NO se toque. Datos inventados.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
R1, R2 = "202670000000431", "202670000000432"
T = "\t"
TIRA = T.join(["11001000000046855431","C29","19/04/2025","25/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE","","","",
               "CEDULA DE CIUDADANIA","1886999","JOSE PEREZ CASTANEDA"])
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag)
    B.importar(pag, R1 + "\t02/11/2026\t03/11/2026\tJOSE PEREZ CASTANEDA\n" + R2 + "\t02/11/2026\t03/11/2026\tANA MARIA RUIZ")
    opciones = pag.evaluate("()=>[...document.querySelectorAll('#formatoOptions option')].map(o=>o.value)")
    ok(not any("PRORROGA" in o.upper() for o in opciones), "el desplegable de clasificación ya no las ofrece → %r" % opciones)
    barra = pag.inner_text("body")
    ok("PRORROGA" not in barra.upper(), "ni el conteo por formato ni nada en pantalla las nombra")

    print("quien ya las tenía guardadas en sus Ajustes (y un radicado clasificado así)")
    p2 = ctx.new_page(); p2.goto("http://127.0.0.1:8871/manifest.webmanifest")
    p2.evaluate("""([r1])=>{
      const ks = Object.keys(localStorage).find(k=>k.startsWith('radicados_settings_v1::'));
      const s = JSON.parse(localStorage.getItem(ks)||'{}');
      s.formatCategories = ["T1","T5","T6","T10","T11","T14","AGENDAMIENTO","DEVUELTO","PRORROGA","PRORROGA SDA"];
      s.formatToPlantilla = Object.assign({}, s.formatToPlantilla||{}, {"PRORROGA":"PRORROGA","PRORROGA SDA":"PRORROGA SDA"});
      localStorage.setItem(ks, JSON.stringify(s));
      const kr = Object.keys(localStorage).find(k=>k.startsWith('radicados_semanales_v2::'));
      const l = JSON.parse(localStorage.getItem(kr));
      l.forEach(r=>{ if(r.radicado===r1){ r.formato='PRORROGA'; r.direccion='jose@gmail.com'; r.modificadoEn=Date.now()+60000; } });
      localStorage.setItem(kr, JSON.stringify(l));
      const kh = Object.keys(localStorage).find(k=>k.startsWith('radicados_historial_v1::')) || 'radicados_historial_v1::prueba@gmail.com';
      localStorage.setItem(kh, JSON.stringify([{closedAt: '2026-10-30T20:00:00.000Z', closedAtDisplay:'30/10/2026',
        weekLabel:'2026-W44', total:1, done:1, pct:100, devuelto:0, pctDevuelto:0,
        records:[{id:'h1', radicado:'202670000000430', formato:'PRORROGA SDA', fechaAsignacion:'27/10/2026'}]}]));
    }""", [R1])
    p2.close()
    pag.reload(wait_until="domcontentloaded"); B.entrar_en(pag); pag.wait_for_timeout(1500)
    opciones = pag.evaluate("()=>[...document.querySelectorAll('#formatoOptions option')].map(o=>o.value)")
    ok(not any("PRORROGA" in o.upper() for o in opciones), "aun con Ajustes viejos, el desplegable no las ofrece → %r" % opciones)
    B.ir_a(pag, R1); pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag)
    f = " | ".join(B.faltas(pag))
    ok("no es una clasificación" in f, "un radicado que quedó en PRORROGA queda PENDIENTE pidiendo otra clasificación → %r" % f[:120])
    ok(B.descargar(pag) is None, "y con él así la masiva no sale")
    hist = pag.evaluate("()=>{const k=Object.keys(localStorage).find(k=>k.startsWith('radicados_historial_v1::'));return JSON.stringify(JSON.parse(localStorage.getItem(k)||'[]'))}")
    ok("PRORROGA SDA" in hist, "el historial ya archivado no se toca")
    ok(not err, "sin errores de JavaScript → %r" % err)
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
