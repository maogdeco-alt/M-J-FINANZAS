# AISLAMIENTO ENTRE LOS DOS BLOQUES. La preocupación, textual: "es imperativo que el trabajo de la
# mañana y de la tarde tenga memorias y almacenamiento autónomo y separado y no se puede confundir
# la información bajo ninguna circunstancia".
# Esta prueba no lo afirma: lo mide. Toma una FOTO EXACTA de todo lo que la app guarda (navegador
# y nube), trabaja a fondo en un bloque, y comprueba que lo del otro no cambió NI UN BYTE.
import sys, os, json, hashlib, urllib.request; sys.path.insert(0,"/home/user/M-J-FINANZAS/pruebas")
from playwright.sync_api import sync_playwright
import base as B
SHEET = os.path.join(os.path.dirname(__file__), "sheet_donina.xlsx")
if not os.path.exists(SHEET):
    print("  SALTADA: falta pruebas/sheet_donina.xlsx (el sheet real no se guarda en el repositorio).")
    sys.exit(0)
T="\t"
TIRA=T.join(["11001000000046855268","C02","19/04/2025","19/04/2025","No","CAMARAS SALVAVIDAS","VIGENTE",
  "","","","CEDULA DE CIUDADANIA","1886999","PERSONA 1","ABC123"])
BLOQUE="\n".join("2026ER%03d\t01/09/2026\t03/09/2026\tPERSONA %d"%(i,i) for i in (1,2,3))
fallos=[]
def ok(c,m):
    print(("  OK  " if c else "  FALLA  ")+m)
    if not c: fallos.append(m)

def foto_local(pag):
    """Todo lo que la app guarda en este navegador, separado por bloque."""
    return pag.evaluate("""()=>{
      const todo={};
      for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);todo[k]=localStorage.getItem(k);}
      return todo;}""")
def foto_nube():
    d=json.loads(urllib.request.urlopen("http://127.0.0.1:9870/rest/v1/radicados_datos?usuario_id=eq.c81b5136-bcd1-0b43-9010-8c979ed28ee6",timeout=5).read())
    f=(d[0] if d else {}) or {}
    def h(x): return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return {"records":h(f.get("records")), "settings":h(f.get("settings")),
            "history":h(f.get("history")), "manana":h(f.get("manana"))}
# Llaves que NO son datos de ningún bloque: son preferencias de pantalla de este navegador
# (el tema, si la cola está plegada, y cuál de los dos bloques se está viendo). Que cambien es
# lo que se espera al cambiar de pestaña; no es información de trabajo.
PREFERENCIAS = ("radicados_bloque_v1", "radicados_theme_pref", "radicados_focus_mode",
                "radicados_queue_collapsed", "radicados_ultimo_visto_v1", "radicados_ultimo_filtro_v1")
def es_preferencia(k):
    return any(k.startswith(p) for p in PREFERENCIAS)
def claves_de(foto, quien):
    """quien='manana' -> solo los DATOS del bloque de la mañana; 'tarde' -> los de la masiva."""
    out={}
    for k,v in foto.items():
        if es_preferencia(k): continue
        esManana = "manana" in k
        if (quien=="manana") == esManana: out[k]=v
    return out

with sync_playwright() as pw:
    nav,ctx,pag,err=B.abrir(pw)
    B.entrar(pag)

    print("1) se llena el bloque de la TARDE (la masiva)")
    B.importar(pag,BLOQUE)
    B.ir_a(pag,"2026ER001"); B.pegar_tira(pag,TIRA)
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","p@gmail.com")
    B.escribir(pag,"#cc_res","1368706"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(700); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.wait_for_timeout(1200)
    tarde_antes = claves_de(foto_local(pag), "tarde")
    nube_antes = foto_nube()
    ok(len(tarde_antes) > 0, "la tarde tiene %d llaves guardadas en el navegador" % len(tarde_antes))

    print("2) se trabaja A FONDO en la MAÑANA: cargar sheet, clasificar, corregir, cerrar el día")
    pag.click("#selBloqueManana"); pag.wait_for_timeout(600)
    B.cargar_sheet_manana(pag, SHEET)
    pag.fill("#manNombre","ALEJANDRA"); pag.keyboard.press("Tab"); pag.wait_for_timeout(700)
    pag.click('#manTabs button[data-mantab="ia"]'); pag.wait_for_timeout(600)
    f = pag.locator("#manPanel .man-fila")
    f.nth(0).locator("button[data-manok]").click(); pag.wait_for_timeout(500)
    inp = pag.locator("#manPanel .man-fila").nth(0).locator("input[data-manclas]")
    inp.click(); inp.fill("MASIVO TIPO 9"); pag.wait_for_timeout(300)
    pag.keyboard.press("Enter"); pag.wait_for_timeout(900)
    pag.click("#manCerrarDiaBtn"); pag.wait_for_timeout(600)
    pag.click("#manCerrarOk"); pag.wait_for_timeout(1500)
    B.cargar_sheet_manana(pag, SHEET)   # y otro día encima
    pag.wait_for_timeout(1200)

    print("3) ¿cambió algo de la TARDE?")
    tarde_despues = claves_de(foto_local(pag), "tarde")
    nube_despues = foto_nube()
    cambiadas = [k for k in set(list(tarde_antes)+list(tarde_despues))
                 if tarde_antes.get(k) != tarde_despues.get(k)]
    ok(not cambiadas, "ni una llave de la tarde cambió en el navegador → " + (str(cambiadas)[:200] if cambiadas else "ninguna"))
    ok(nube_antes["records"] == nube_despues["records"], "la columna «records» de la nube quedó idéntica")
    ok(nube_antes["settings"] == nube_despues["settings"], "«settings» idéntica")
    ok(nube_antes["history"] == nube_despues["history"], "«history» idéntica")
    ok(nube_antes["manana"] != nube_despues["manana"], "y «manana» sí cambió (era lo que se estaba trabajando)")

    print("4) y al revés: se trabaja en la TARDE y se mira la MAÑANA")
    manana_antes = claves_de(foto_local(pag), "manana")
    nube_antes2 = foto_nube()
    pag.click("#selBloqueTarde"); pag.wait_for_timeout(600)
    B.ir_a(pag,"2026ER002"); B.pegar_tira(pag,TIRA.replace("46855268","46855999").replace("1886999","52000111"))
    B.escribir(pag,"#cc_formato","T14"); B.escribir(pag,"#cc_direccion","otro@gmail.com")
    B.escribir(pag,"#cc_res","999111"); B.escribir(pag,"#cc_fechaRes","26/07/2024")
    pag.click("#cc_save"); pag.wait_for_timeout(900); B.confirmar_nombre(pag); B.cerrar_alerta(pag)
    pag.evaluate("()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close())"); pag.wait_for_timeout(400)
    pag.click("#cerrarSemanaNavBtn"); pag.wait_for_timeout(700)
    pag.click("#confirmOk"); pag.wait_for_timeout(1800)   # cerrar la SEMANA entera
    manana_despues = claves_de(foto_local(pag), "manana")
    nube_despues2 = foto_nube()
    cambiadas2 = [k for k in set(list(manana_antes)+list(manana_despues))
                  if manana_antes.get(k) != manana_despues.get(k)]
    ok(not cambiadas2, "cerrar la SEMANA no tocó ni una llave de la mañana → " + (str(cambiadas2)[:200] if cambiadas2 else "ninguna"))
    ok(nube_antes2["manana"] == nube_despues2["manana"], "y la columna «manana» de la nube quedó idéntica")

    print("5) lo ÚNICO que comparten las dos partes")
    todas = foto_local(pag)
    compartidas = sorted(k for k in todas if es_preferencia(k))
    print("      llaves de preferencia de pantalla (no son datos):")
    for k in compartidas: print("        ", k)
    datos_m = sorted(claves_de(todas,"manana")); datos_t = sorted(claves_de(todas,"tarde"))
    print("      datos de la MAÑANA:", datos_m)
    print("      datos de la TARDE :", datos_t)
    ok(not set(datos_m) & set(datos_t), "ni una sola llave de datos en común")

    print("6) el bloque de la mañana sigue entero después de cerrar la semana")
    pag.click("#selBloqueManana"); pag.wait_for_timeout(700)
    ok(pag.locator("#manCuentaSin").inner_text().endswith("/ 65"), "sus 65 filas siguen → "+pag.locator("#manCuentaSin").inner_text())
    pag.click("#manHistorialBtn"); pag.wait_for_timeout(600)
    ok(pag.locator("#manHistorialLista .preflight-item").count()==1, "y su historial de días también")
    pag.click("#manHistorialClose"); pag.wait_for_timeout(300)

    print("7) el respaldo .json lleva los dos, cada uno en su llave")
    pag.click("#selBloqueTarde"); pag.wait_for_timeout(400)
    pag.click("#abrirDocumentosBtn"); pag.wait_for_timeout(600)
    with pag.expect_download(timeout=20000) as dl:
        pag.click("#downloadJsonBtn")
    ruta=os.path.join(os.path.dirname(__file__),"respaldo.json"); dl.value.save_as(ruta)
    data=json.load(open(ruta,encoding="utf-8"))
    ok("records" in data and "manana" in data, "el respaldo trae «records» y «manana» por separado → "+str(sorted(data.keys())))
    ok(isinstance(data.get("manana",{}).get("sin"), list) and len(data["manana"]["sin"])==65,
       "con las 65 filas de la mañana dentro → %s" % len(data.get("manana",{}).get("sin",[])))
    print("errores js:", err or "ninguno")
    if err: fallos.append("errores de JavaScript")
    nav.close()
print("\nRESULTADO:", "TODO BIEN" if not fallos else str(len(fallos))+" FALLA(S)")
sys.exit(1 if fallos else 0)
