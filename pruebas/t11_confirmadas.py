# SONDA: las anomalías CONFIRMADAS durante la semana, ¿se ven al entregar? (antes se contaban
# y no se mostraban en ninguna parte: se firmaba la base sin saber qué llevaba dentro)
import sys; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B
T="\t"
# T14 con MEDIO manual: rompe R08. Se confirma la anomalía y se sigue.
MALA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","COMPARENDERA","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","ANA MARIA GOMEZ","ABC123"])
BLOQUE="2026ER700\t01/09/2026\t03/09/2026\tANA MARIA GOMEZ\n2026ER701\t01/09/2026\t03/09/2026\tOTRA"
with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag); B.importar(pag,BLOQUE); B.ir_a(pag,"2026ER700")
    B.pegar_tira(pag,MALA)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","ana@gmail.com")
    B.escribir(pag,"#cc_res","1368706"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(700); B.confirmar_nombre(pag)
    # dejarlo atrás desde la lista: ahí el aviso sale y se puede confirmar
    pag.evaluate("()=>{const b=document.querySelector('#filterTabs button[data-filter=\"all\"]'); if(b) b.click();}")
    pag.wait_for_timeout(300)
    pag.locator('#queuePanel .queue-item', has_text="2026ER701").first.click()
    pag.wait_for_timeout(700)
    if pag.locator("#alertaInmediataDialog[open]").count():
        print("el aviso dice:", " / ".join(B.avisos_alerta(pag))[:160])
        pag.click("#alertaInmediataConfirmar"); pag.wait_for_timeout(700)
        print("→ se confirmó la anomalía")
    else:
        print("el aviso NO salió"); nav.close(); sys.exit(1)
    pag.click("#descargarMasivaBtn"); pag.wait_for_timeout(1400)
    if pag.locator("#preflightDialog[open]").count():
        print("\nRESUMEN de la revisión previa:")
        print("  ", pag.locator("#preflightResumen").inner_text())
        blq=pag.locator(".preflight-confirmados")
        print("¿sale el bloque de confirmadas?", blq.count()>0)
        if blq.count(): print("  ", blq.inner_text().replace("\n"," | ")[:320])
        pag.locator("#preflightDialog").screenshot(path="/home/user/M-J-FINANZAS/pruebas/f_confirmadas.png")
    else:
        print("la revisión previa NO se abrió — la base se habría entregado en silencio")
    mal = (blq.count()==0) if pag.locator("#preflightDialog[open]").count() else True
    print("errores js:", err or "ninguno")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not mal and not err else "FALLA")
sys.exit(1 if (mal or err) else 0)
