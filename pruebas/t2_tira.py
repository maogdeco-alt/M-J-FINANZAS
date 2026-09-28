# 1a. "NI SE ADVIERTE EN NINGUN LADO DE LA APP QUE SE COPIO MAL LA TIRA COMPLETA DE FENIX"
# 2c. La fecha de notificación vacía NO puede generar error.
from playwright.sync_api import sync_playwright
import base as B, sys
T = "\t"
BUENA = T.join(["11001000000046855268","D01","19/04/2025","19/04/2025","No","COMPARENDERA","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","JOSE PÉREZ CASTAÑEDA","ABC123"])
SIN_NOTIF = T.join(["11001000000046855271","D01","19/04/2025","","No","COMPARENDERA","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","JOSE PÉREZ CASTAÑEDA","ABC123"])
SIN_TABS = "11001000000046855268 D01 19/04/2025 19/04/2025 No COMPARENDERA VIGENTE CEDULA DE CIUDADANIA 1886999 JOSE PÉREZ CASTAÑEDA ABC123"
CORTADA  = T.join(["11001000000046855272","D01","19/04/2025","19/04/2025","No","COMPARENDERA","VIGENTE"])
CORRIDA  = T.join(["11001000000046855273","D01","COMPARENDERA","19/04/2025","No","VIGENTE","19/04/2025",
  "","","","19/04/2025","1886999","JOSE PÉREZ CASTAÑEDA","ABC123"])
SOLO_NUM = "11001000000046855274"

BLOQUE = "\n".join("2026ER0%02d\t01/09/2026\t03/09/2026\tJOSE PEREZ CASTANEDA" % i for i in range(1,7))
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

with sync_playwright() as pw:
    nav,ctx,pag,errores = B.abrir(pw)
    B.entrar(pag); B.importar(pag, BLOQUE)

    print("1) tira BUENA: ni un aviso de la tira")
    B.ir_a(pag,"2026ER001"); B.pegar_tira(pag, BUENA)
    cs=" | ".join(B.chips(pag))
    ok("R20" not in cs and "R21" not in cs and "R22" not in cs, "no inventa problemas donde no los hay\n        chips: "+cs)

    print("2) FECHA DE NOTIFICACIÓN VACÍA: normal, nunca un error (R23)")
    B.ir_a(pag,"2026ER002"); B.pegar_tira(pag, SIN_NOTIF)
    cs=" | ".join(B.chips(pag))
    ok("R20" not in cs and "R21" not in cs and "R22" not in cs, "no sale ningún aviso de regla")
    ok("notific" not in cs.lower() or "sin notificación en Fénix, es normal" in cs,
       "y si se nombra, es para decir que es normal\n        chips: "+cs)
    # y tampoco frena al pasar al siguiente
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","persona@gmail.com")
    pag.click("#cc_save"); pag.wait_for_timeout(400); B.confirmar_nombre(pag)
    B.avanzar(pag)
    av = B.avisos_alerta(pag)
    ok(not any("notific" in a.lower() for a in av), "y al avanzar tampoco lo menciona como problema\n        avisos: "+str(av))
    B.cerrar_alerta(pag)

    print("3) tira pegada SIN columnas (de un PDF o un correo)")
    B.ir_a(pag,"2026ER003"); B.pegar_tira(pag, SIN_TABS)
    cs=" | ".join(B.chips(pag))
    ok("R20" in cs, "avisa R20 al momento de pegarla\n        chips: "+cs)

    print("4) tira CORTADA a la mitad")
    B.ir_a(pag,"2026ER004"); B.pegar_tira(pag, CORTADA)
    cs=" | ".join(B.chips(pag))
    ok("R21" in cs, "avisa R21 y dice cuántas columnas llegaron\n        chips: "+cs)

    print("5) tira con las columnas CORRIDAS")
    B.ir_a(pag,"2026ER005"); B.pegar_tira(pag, CORRIDA)
    cs=" | ".join(B.chips(pag))
    ok("R22" in cs, "avisa R22 (un dato en la casilla que no es)\n        chips: "+cs)

    print("6) solo el número: sigue siendo R19, no R20")
    B.ir_a(pag,"2026ER006"); B.pegar_tira(pag, SOLO_NUM)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","persona@gmail.com")
    B.escribir(pag,"#cc_res","1368706"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(400); B.confirmar_nombre(pag)
    B.avanzar(pag)
    av=" | ".join(B.avisos_alerta(pag))
    ok("R19" in av, "R19 aparece al avanzar\n        avisos: "+av)
    ok("R20" not in av, "y R20 NO se duplica con él")
    B.cerrar_alerta(pag)

    print("\nerrores de JavaScript:", errores or "ninguno")
    if errores: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
