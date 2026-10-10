# 2a. "En la columna de placa me arroja es la dirección, NO la placa."
from playwright.sync_api import sync_playwright
import base as B, sys

T = "\t"
# Tira REAL de Fénix con 15 columnas: la dirección del infractor va ANTES de la placa.
TIRA_15 = T.join(["11001000000046855268","D01","19/04/2025","19/04/2025","No","COMPARENDERA",
  "VIGENTE","","","","Permiso por protección temporal","1886999","JOSE PÉREZ CASTAÑEDA",
  "CALLE 13 36 31 BAHIA 1","ABC123"])
# Tira de 14 columnas (la de siempre): la placa va en la 14.
TIRA_14 = T.join(["11001000000046855269","C02","01/03/2025","","No","CAMARAS FIJAS",
  "VIGENTE","","","","CEDULA DE CIUDADANIA","52123456","ANA MARÍA GÓMEZ","XYZ12D"])
# Tira sin placa ninguna: la 14 trae la dirección y nada más.
TIRA_SIN = T.join(["11001000000046855270","D01","05/05/2025","06/05/2025","No","COMPARENDERA",
  "VIGENTE","","","","CEDULA DE CIUDADANIA","79123456","LUIS ALBERTO RUIZ","CRA 7 # 90-27"])

BLOQUE = "\n".join([
  "2026ER001\t01/09/2026\t03/09/2026\tJOSE PEREZ CASTAÑEDA",
  "2026ER002\t01/09/2026\t03/09/2026\tANA MARIA GOMEZ",
  "2026ER003\t01/09/2026\t03/09/2026\tLUIS ALBERTO RUIZ",
])

fallos = []
def ok(cond, msg):
    print(("  OK  " if cond else "  FALLA  ") + msg)
    if not cond: fallos.append(msg)

with sync_playwright() as pw:
    nav, ctx, pag, errores = B.abrir(pw)
    B.entrar(pag); B.importar(pag, BLOQUE)

    print("1) tira de 15 columnas (dirección antes de la placa)")
    B.ir_a(pag, "2026ER001"); B.pegar_tira(pag, TIRA_15)
    d = B.desglose(pag)
    ok(d.get("PLACA") == "ABC123", "la placa es ABC123, no la dirección  → " + repr(d.get("PLACA")))
    ok("CALLE 13" in (d.get("DIRECCIÓN INFRACTOR") or ""), "la dirección va a su propia casilla → " + repr(d.get("DIRECCIÓN INFRACTOR")))
    ok(d.get("TIPO DOCUMENTO") == "Permiso por protección temporal", "el tipo de documento no se corrió → " + repr(d.get("TIPO DOCUMENTO")))
    ok(d.get("NOMBRE INFRACTOR") == "JOSE PÉREZ CASTAÑEDA", "el nombre no se corrió → " + repr(d.get("NOMBRE INFRACTOR")))

    print("2) tira de 14 columnas (como siempre): nada cambia")
    B.ir_a(pag, "2026ER002"); B.pegar_tira(pag, TIRA_14)
    d = B.desglose(pag)
    ok(d.get("PLACA") == "XYZ12D", "la placa sigue siendo XYZ12D → " + repr(d.get("PLACA")))
    ok((d.get("DIRECCIÓN INFRACTOR") or "—") == "—", "sin dirección, la casilla queda vacía → " + repr(d.get("DIRECCIÓN INFRACTOR")))
    ok(d.get("FECHA NOTIF.") == "—", "la notificación vacía se queda vacía, sin inventar nada")

    print("3) tira sin placa: NO se inventa una, y se avisa")
    B.ir_a(pag, "2026ER003"); B.pegar_tira(pag, TIRA_SIN)
    d = B.desglose(pag)
    ok("CRA 7" in (d.get("PLACA") or ""), "se deja tal cual vino (no se borra en silencio) → " + repr(d.get("PLACA")))
    cs = " | ".join(B.chips(pag))
    ok("R22" in cs and "Placa" in cs, "sale el aviso de que eso no tiene forma de placa\n        chips: " + cs)

    print("\nerrores de JavaScript:", errores or "ninguno")
    if errores: fallos.append("hubo errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos)) + " FALLA(S)")
sys.exit(1 if fallos else 0)
