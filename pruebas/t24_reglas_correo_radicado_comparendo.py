# LAS TRES COMPROBACIONES QUE LA APP NO TENÍA (R26, R27, R28).
#
# Salieron de la auditoría de "cada rincón" del 6 de octubre de 2026, contra la masiva real
# entregada el 2 de octubre:
#
#   R26  El correo se daba por bueno con solo tener una arroba. 34 correos rotos salieron sin
#        una sola alerta — a esos ciudadanos no les llegó la citación.
#   R27  El número de radicado, que identifica el expediente entero, era el ÚNICO dato sin
#        ninguna comprobación de forma.
#   R28  Ninguna regla miraba la longitud del comparendo: en la masiva entregada quedó un «11».
#
# Cada caso de aquí está copiado de esa masiva (con los datos cambiados, la forma del defecto no).
import sys, os; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
R1="202661203706582"
R2="202661203702962"
# Hacen falta DOS para poder usar "Guardar y siguiente": el motor completo de reglas corre al
# AVANZAR y en la revisión previa, no en «Guardar» a secas. Es deliberado — un aviso que salta en
# cada guardado parcial enseña a cerrarlo sin leerlo (está medido: 15 de 16 saltos eran ruido).
BLOQUE = "\n".join([R1+"\t01/09/2026\t28/09/2026\tPERSONA UNO",
                    R2+"\t01/09/2026\t28/09/2026\tPERSONA DOS"])
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

def avisos(pag):
    """Lo que la app muestra al guardar: el aviso inmediato es #alertaInmediataDialog
    (no #alertDialog — ese fue un error de esta prueba que costó una corrida)."""
    t = list(B.avisos_alerta(pag))
    for sel in ("#requiredSummary", "#alertaInmediataResumen"):
        loc = pag.locator(sel)
        if loc.count():
            try: t.append(loc.first.inner_text())
            except Exception: pass
    return "\n".join(t)

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE)
    B.ir_a(pag,R1); B.pegar_tira(pag,TIRA)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_res","136871")
    B.escribir(pag,"#cc_fechaRes","26/07/2024")

    print("1) R26 — CADA CLASE DE CORREO ROTO, CON SU CAUSA")
    casos = [
      (":dreyquintero@gmal.com",      ["sobra", "mal escrito"], "dos puntos delante + dominio mal escrito"),
      (":CASTANEDA@GMAIL.COM",        ["sobra"],                 "dos puntos delante"),
      ("gomezclara 1955@gmail.com",   ["espacio"],               "un espacio en la mitad"),
      ("bedima333@fmail.com",         ["mal escrito"],           "fmail → gmail"),
      ("jeidy13@gmaial.com",          ["mal escrito"],           "gmaial → gmail"),
      ("alguien@gmail.co",            ["mal escrito"],           "gmail.co → gmail.com"),
      ("sinarroba.gmail.com",         ["arroba"],                "sin arroba y no es dirección"),
    ]
    for correo, esperados, desc in casos:
        B.ir_a(pag,R1)
        B.escribir(pag,"#cc_direccion",correo)
        pag.click("#cc_saveNext"); pag.wait_for_timeout(600)
        B.confirmar_nombre(pag); pag.wait_for_timeout(400)
        txt = avisos(pag)
        hay = all(e.lower() in txt.lower() for e in esperados)
        ok(hay, "avisa de «"+correo+"» ("+desc+") → "+(txt.replace(chr(10)," ")[:90] if txt else "SIN AVISO"))
        B.cerrar_alerta(pag)

    print("2) R26 — UN CORREO BUENO NO PUEDE DISPARAR NINGUNA ALARMA")
    for bueno in ["ciudadano@gmail.com","nombre.apellido@hotmail.es","alguien@unal.edu.co",
                  "persona@outlook.com","CALLE 13 36 31 BAHIA 1"]:
        B.ir_a(pag,R1)
        B.escribir(pag,"#cc_direccion",bueno)
        pag.click("#cc_saveNext"); pag.wait_for_timeout(600)
        B.confirmar_nombre(pag); pag.wait_for_timeout(400)
        txt = avisos(pag)
        malo = ("no le llega" in txt.lower()) or ("sobra" in txt.lower()) or ("mal escrito" in txt.lower())
        ok(not malo, "no se queja de «"+bueno+"» (dato correcto)")
        B.cerrar_alerta(pag)

    print("3) R28 — LONGITUD DEL COMPARENDO")
    B.escribir(pag,"#cc_direccion","ciudadano@gmail.com")
    pag.click("#cc_save"); pag.wait_for_timeout(400); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    # el comparendo se escribe pegando la tira; se cambia solo ese dato
    pag.evaluate("""()=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const l = JSON.parse(localStorage.getItem(k));
      l.forEach(r=>{ r.comparendoCompleto='11'; r.modificadoEn=Date.now()+60000; });
      localStorage.setItem(k, JSON.stringify(l));
    }""")
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1500)
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
    txt = pag.locator("#preflightLista").inner_text() if pag.locator("#preflightDialog[open]").count() else ""
    ok("11" in txt and "dígito" in txt, "el comparendo «11» se señala → "+txt[txt.find("comparendo"):][:95] if "comparendo" in txt else "NO se señaló")
    if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightCancel")
    pag.wait_for_timeout(400)

    print("4) R27 — FORMATO DEL NÚMERO DE RADICADO")
    pag.evaluate("""()=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const l = JSON.parse(localStorage.getItem(k));
      l.forEach(r=>{ r.comparendoCompleto='52559342'; r.radicado='20266120370658'; r.modificadoEn=Date.now()+90000; });
      localStorage.setItem(k, JSON.stringify(l));
    }""")
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1500)
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
    txt2 = pag.locator("#preflightLista").inner_text() if pag.locator("#preflightDialog[open]").count() else ""
    ok("14 dígitos" in txt2 or "14 d" in txt2, "un radicado de 14 dígitos se señala")
    ok("15" in txt2, "y dice cuántos debería tener")
    if pag.locator("#preflightDialog[open]").count(): pag.click("#preflightCancel")
    pag.wait_for_timeout(400)

    print("5) un radicado de 15 dígitos no molesta")
    pag.evaluate("""()=>{
      const k = Object.keys(localStorage).find(x=>x.indexOf('radicados_semanales_v2::')===0);
      const l = JSON.parse(localStorage.getItem(k));
      l.forEach(r=>{ r.radicado='202661203706582'; r.modificadoEn=Date.now()+120000; });
      localStorage.setItem(k, JSON.stringify(l));
    }""")
    pag.reload(wait_until="domcontentloaded"); pag.wait_for_timeout(1200)
    pag.fill("#loginEmail","prueba@gmail.com"); pag.fill("#loginPassword","123456")
    pag.click("#loginBtn"); pag.wait_for_selector("#authDialog", state="hidden", timeout=20000)
    pag.wait_for_timeout(1500)
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1500)
    txt3 = pag.locator("#preflightLista").inner_text() if pag.locator("#preflightDialog[open]").count() else ""
    ok("dígitos y deberían ser" not in txt3, "no se queja de un radicado correcto")
    ok("dígito(s). Un comparendo" not in txt3, "ni del comparendo correcto")

    print("6) las tres reglas están en el catálogo de Ajustes")
    # La revisión previa puede haber quedado abierta: se cierra antes de tocar nada más.
    if pag.locator("#preflightDialog[open]").count():
        pag.click("#preflightCancel"); pag.wait_for_timeout(400)
    pag.click("#reglasBtn"); pag.wait_for_timeout(1200)
    cat = pag.locator("body").inner_text()
    for r in ("R26","R27","R28"):
        ok(r in cat, r+" aparece en el catálogo de reglas")

    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
