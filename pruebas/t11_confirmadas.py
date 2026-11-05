# SONDA: las anomalías CONFIRMADAS durante la semana, ¿se ven al entregar? (antes se contaban
# y no se mostraban en ninguna parte: se firmaba la base sin saber qué llevaba dentro)
#
# Desde el 04-11-2026 ya no se confirma nada («es correcto» se quitó a pedido de ella): una regla
# se cumple o se corrige. La prueba exige ahora lo más fuerte: que una anomalía no se pueda dejar
# pasar de ningún modo, y que con ella la masiva no salga.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import base as B
T="\t"
# T14 con MEDIO manual: rompe R08. Se confirma la anomalía y se sigue.
MALA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","COMPARENDERA","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","ANA MARIA GOMEZ","ABC123"])
BLOQUE="202670000000700\t01/09/2026\t03/09/2026\tANA MARIA GOMEZ\n202670000000701\t01/09/2026\t03/09/2026\tOTRA"
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE); B.ir_a(pag,"202670000000700")
    B.pegar_tira(pag,MALA)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","ana@gmail.com")
    B.escribir(pag,"#cc_res","1368706"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(700); B.confirmar_nombre(pag)
    f=" / ".join(B.faltas(pag))
    ok("COMPARENDERA" in f, "R08 deja el radicado PENDIENTE y lo dice → "+f[:140])
    ok(pag.locator("#avisoImperativas button", has_text="correcto").count()==0, "no hay botón para darlo por bueno")
    B.avanzar(pag)
    ok("202670000000700" in pag.locator("#cc_radicadoLabel").inner_text(), "«Guardar y siguiente» no lo deja atrás")
    ok(pag.locator("#alertaInmediataDialog[open]").count()==0, "sin ventana emergente para confirmar")
    B.ir_a(pag,"202670000000701"); B.escribir(pag,"#cc_formato","DEVUELTO")
    pag.click("#cc_save"); pag.wait_for_timeout(500); B.confirmar_nombre(pag)
    ok(B.descargar(pag) is None, "y la masiva no sale mientras siga así")
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
