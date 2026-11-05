# LAS REGLAS SON LAS DEL CÓDIGO, SIEMPRE (05-11-2026)
#
# Auditoría pedida por la usuaria antes de una jornada de 60 radicados: "que las reglas estén súper
# claras". Desde el rediseño del 04-11 las reglas ya no se editan en la app (quedan fijas en el código
# y cada cambio lleva su prueba), pero la app SEGUÍA aplicando encima los parámetros guardados en la
# nube (tabla reglas_masivas, "reglas del área") y en el navegador. Una copia vieja allí -- de cuando
# las editaban cuatro personas -- podía aflojar una regla sin que nadie lo viera: por ejemplo, dejar
# pasar un T1 sin resolución o un T6 sin comparendo. Ahora se ignoran: mandan las del código.
import sys, os, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T = "\t"
R1, R2 = "202670000000451", "202670000000452"
TIRA1 = T.join(["11001000000046855451","C29","19/04/2025","25/04/2025","No","COMPARENDERA","VIGENTE","","","",
                "CEDULA DE CIUDADANIA","1886451","JOSE PEREZ CASTANEDA"])
fallos = []
def ok(c, m):
    print(("  OK  " if c else "  FALLA  ") + m)
    if not c: fallos.append(m)
def caja(p): return p.inner_text("#avisoImperativas") if p.locator("#avisoImperativas:visible").count() else ""
B.reiniciar()
# Reglas "del área" en la nube, aflojadas: T1 ya no exige resolución.
q = urllib.request.Request("http://127.0.0.1:9870/rest/v1/reglas_masivas?id=eq.masivas", method="PATCH",
    data=json.dumps({"params": {"formatosConResolucionObligatoria": ["T5", "T11", "T14"]}}).encode(),
    headers={"Content-Type": "application/json"})
urllib.request.urlopen(q, timeout=5).read()
with sync_playwright() as pw:
    nav, ctx, pag, err = B.abrir(pw)
    B.entrar(pag, limpio=False); pag.wait_for_timeout(1200)
    B.importar(pag, R1 + "\t02/11/2026\t03/11/2026\tJOSE PEREZ CASTANEDA\n" + R2 + "\t02/11/2026\t03/11/2026\tANA MARIA RUIZ")
    B.ir_a(pag, R1); B.pegar_tira(pag, TIRA1); B.escribir(pag, "#cc_formato", "T1"); B.escribir(pag, "#cc_direccion", "jose@gmail.com")
    pag.click("#cc_saveNext"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); pag.wait_for_timeout(300)
    ok(R1 in pag.inner_text("#cc_radicadoLabel") and "resolución" in caja(pag),
       "con reglas aflojadas en la nube, un T1 sin resolución sigue PENDIENTE → %r" % caja(pag)[:100])

    # Copia aflojada en el navegador: T6 ya no exigiría comparendo.
    p2 = ctx.new_page(); p2.goto("http://127.0.0.1:8871/manifest.webmanifest")
    p2.evaluate("""()=>localStorage.setItem('radicados_reglas_params_v1::area',
       JSON.stringify({formatosSinComparendo:['T10','T6'], formatosConResolucionObligatoria:[]}))""")
    p2.close()
    pag.reload(wait_until="domcontentloaded"); B.entrar_en(pag); pag.wait_for_timeout(1500)
    B.ir_a(pag, R2); B.escribir(pag, "#cc_formato", "T6"); B.escribir(pag, "#cc_direccion", "ana@gmail.com")
    pag.click("#cc_saveNext"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); pag.wait_for_timeout(300)
    ok(R2 in pag.inner_text("#cc_radicadoLabel") and "comparendo" in caja(pag).lower(),
       "con reglas aflojadas en el navegador, un T6 sin comparendo sigue PENDIENTE → %r" % caja(pag)[:100])
    ok(B.descargar(pag) is None, "y la masiva no sale")
    ok(not err, "sin errores de JavaScript → %r" % err[:3])
    nav.close()
print("RESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
