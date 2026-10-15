"""Pruebas de la lógica que no depende de Streamlit."""

from datetime import date

import pytest
from docx import Document

from curaduria import fechas, numeros, plantilla
from curaduria.genero_nombres import sugerir_genero
from curaduria.gramatica import Concordancia, Titular
from curaduria.resolucion import Inmueble, Resolucion


# --- Números ---------------------------------------------------------------

@pytest.mark.parametrize("valor,esperado", [
    (0, "cero"), (1, "uno"), (15, "quince"), (21, "veintiuno"),
    (31, "treinta y uno"), (100, "cien"), (101, "ciento uno"),
    (120, "ciento veinte"), (999, "novecientos noventa y nueve"),
    (1000, "mil"), (1001, "mil uno"), (2026, "dos mil veintiséis"),
    (15000, "quince mil"), (1_000_000, "un millón"),
    (2_500_000, "dos millones quinientos mil"),
])
def test_entero_a_letras(valor, esperado):
    assert numeros.entero_a_letras(valor) == esperado


def test_entero_fuera_de_rango():
    with pytest.raises(ValueError):
        numeros.entero_a_letras(1_000_000_000)


def test_decimal_a_letras():
    assert numeros.decimal_a_letras(120.5) == "ciento veinte con cincuenta"
    assert numeros.decimal_a_letras(0.05) == "cero con cinco"


def test_decimal_redondeo_desborda():
    assert numeros.decimal_a_letras(1.999) == "dos"


def test_formato_cifra_colombiano():
    assert numeros.formato_cifra(1234567.5) == "1.234.567,50"


def test_en_letras_y_cifra():
    assert numeros.en_letras_y_cifra(120.5, "m2") == (
        "ciento veinte con cincuenta m2 (120,50 m2)")


def test_concordar_uno():
    assert numeros.concordar_uno("veintiuno", "F") == "veintiuna"
    assert numeros.concordar_uno("veintiuno", "M") == "veintiún"
    assert numeros.concordar_uno("treinta y uno", "M") == "treinta y un"


# --- Fechas ----------------------------------------------------------------

def test_fechas():
    f = date(2026, 10, 15)
    assert fechas.fecha_corta(f) == "15/10/2026"
    assert fechas.fecha_larga(f) == "15 de octubre de 2026"
    assert fechas.fecha_en_letras(f) == (
        "quince (15) de octubre de dos mil veintiséis (2026)")


def test_etiquetas_fecha_vacia():
    assert fechas.etiquetas_fecha("fecha", None)["fecha_letras"] == ""


# --- Gramática -------------------------------------------------------------

def test_un_titular_femenino():
    c = Concordancia([Titular("MARÍA GÓMEZ", "F", "CC", "41000000")])
    assert c.palabra("articulo") == "la"
    assert c.palabra("propietario") == "propietaria"
    assert c.palabra("identificado") == "identificada"
    assert c.palabra("verbo_solicitar") == "solicita"
    assert c.frase_calidad() == "en calidad de propietaria"


def test_dos_titulares_mixto_va_a_masculino_plural():
    c = Concordancia([
        Titular("JUAN PÉREZ", "M", "CC", "79000000"),
        Titular("MARÍA GÓMEZ", "F", "CC", "41000000"),
    ])
    assert c.mixto
    assert c.palabra("articulo") == "los"
    assert c.palabra("propietario") == "propietarios"
    assert c.palabra("verbo_podra") == "podrán"
    assert c.nombres() == "JUAN PÉREZ y MARÍA GÓMEZ"


def test_tres_titulares_femeninas():
    c = Concordancia([
        Titular("ANA DÍAZ", "F", "CC", "1"),
        Titular("LUZ RUIZ", "F", "CC", "2"),
        Titular("ROSA LIMA", "F", "CC", "3"),
    ])
    assert c.palabra("articulo") == "las"
    assert c.palabra("tratamiento") == "señoras"
    assert c.nombres() == "ANA DÍAZ, LUZ RUIZ y ROSA LIMA"


def test_persona_juridica_se_identifica_en_femenino():
    t = Titular("CONSTRUCTORA XYZ S.A.S.", "M", "NIT", "900123456-1")
    assert "identificada con Número de Identificación Tributaria" in \
        t.frase_identificacion()


def test_etiquetas_incluyen_version_capitalizada():
    c = Concordancia([Titular("MARÍA GÓMEZ", "F")])
    e = c.etiquetas()
    assert e["articulo"] == "la" and e["Articulo"] == "La"


def test_flexionar_libre():
    from curaduria.gramatica import flexionar_libre
    assert flexionar_libre("arquitecto", "F", "S") == "arquitecta"
    assert flexionar_libre("arquitecto", "M", "P") == "arquitectos"


# --- Sugerencia de género --------------------------------------------------

@pytest.mark.parametrize("nombre,esperado", [
    ("MARÍA FERNANDA GÓMEZ", "F"),
    ("JUAN CARLOS PÉREZ", "M"),
    ("JOSÉ MARÍA RESTREPO", "M"),   # gana el primer nombre reconocido
    ("LUZ MARINA TORRES", "F"),
    ("YULIANA ESCOBAR", "F"),       # por terminación
    ("", "M"),
])
def test_sugerir_genero(nombre, esperado):
    assert sugerir_genero(nombre) == esperado


# --- Plantilla -------------------------------------------------------------

def _doc_con(texto_runs):
    doc = Document()
    parrafo = doc.add_paragraph()
    for fragmento in texto_runs:
        parrafo.add_run(fragmento)
    return doc


def test_reemplazo_simple():
    doc = _doc_con(["Hola {{nombre}}, bienvenido."])
    plantilla.rellenar(doc, {"nombre": "ANA"})
    assert doc.paragraphs[0].text == "Hola ANA, bienvenido."


def test_reemplazo_de_etiqueta_partida_en_varios_runs():
    doc = _doc_con(["Hola {{nom", "bre}}", " y adiós"])
    plantilla.rellenar(doc, {"nombre": "ANA"})
    assert doc.paragraphs[0].text == "Hola ANA y adiós"


def test_varias_etiquetas_en_un_parrafo():
    doc = _doc_con(["{{a}}-{{b}}-{{a}}"])
    plantilla.rellenar(doc, {"a": "1", "b": "2"})
    assert doc.paragraphs[0].text == "1-2-1"


def test_etiqueta_con_espacios_internos():
    doc = _doc_con(["X {{ nombre }} Y"])
    plantilla.rellenar(doc, {"nombre": "ANA"})
    assert doc.paragraphs[0].text == "X ANA Y"


def test_etiqueta_sin_dato_se_reporta_y_se_conserva():
    doc = _doc_con(["Hola {{desconocida}}"])
    faltantes = plantilla.rellenar(doc, {"nombre": "ANA"})
    assert faltantes == {"desconocida"}
    assert doc.paragraphs[0].text == "Hola {{desconocida}}"


def test_reemplazo_conserva_formato_del_run():
    doc = Document()
    parrafo = doc.add_paragraph()
    run = parrafo.add_run("{{nombre}}")
    run.bold = True
    plantilla.rellenar(doc, {"nombre": "ANA"})
    assert doc.paragraphs[0].runs[0].bold is True
    assert doc.paragraphs[0].text == "ANA"


def test_reemplazo_en_tablas_encabezado_y_pie():
    doc = Document()
    tabla = doc.add_table(rows=1, cols=1)
    tabla.cell(0, 0).paragraphs[0].add_run("Mat: {{matricula}}")
    doc.sections[0].header.paragraphs[0].add_run("{{curaduria}}")
    doc.sections[0].footer.paragraphs[0].add_run("Res. {{resolucion_numero}}")
    plantilla.rellenar(doc, {"matricula": "050-123", "curaduria": "CU1",
                             "resolucion_numero": "0456"})
    assert tabla.cell(0, 0).text == "Mat: 050-123"
    assert doc.sections[0].header.paragraphs[0].text == "CU1"
    assert doc.sections[0].footer.paragraphs[0].text == "Res. 0456"


def test_listar_etiquetas_del_documento():
    doc = _doc_con(["{{b}} {{a}} {{b}}"])
    assert plantilla.etiquetas_del_documento(doc) == ["b", "a"]


# --- Resolución ------------------------------------------------------------

def _resolucion_valida():
    return Resolucion(
        numero="01-2-0456",
        fecha=date(2026, 10, 15),
        radicado="11001-1-26-0123",
        fecha_radicado=date(2026, 9, 1),
        titulares=[Titular("MARÍA GÓMEZ", "F", "CC", "41000000")],
        inmueble=Inmueble(direccion="CL 10 # 5-20", municipio="Tunja",
                          matricula_inmobiliaria="070-123456",
                          area_lote=120.5, area_construida=85.0, pisos=2),
    )


def test_resolucion_valida_sin_errores():
    assert _resolucion_valida().errores() == []


def test_errores_detectados():
    r = Resolucion()
    errores = r.errores()
    assert any("número de la resolución" in e for e in errores)
    assert any("al menos un titular" in e for e in errores)
    assert any("matrícula inmobiliaria" in e for e in errores)


def test_error_documento_repetido():
    r = _resolucion_valida()
    r.titulares.append(Titular("OTRA PERSONA", "F", "CC", "41000000"))
    assert any("repetido" in e for e in r.errores())


def test_error_radicado_posterior():
    r = _resolucion_valida()
    r.fecha_radicado = date(2026, 12, 1)
    assert any("posterior" in e for e in r.errores())


def test_etiquetas_de_la_resolucion():
    e = _resolucion_valida().etiquetas()
    assert e["articulo"] == "la"
    assert e["propietario"] == "propietaria"
    assert e["fecha_letras"].startswith("quince (15) de octubre")
    assert e["area_lote_letras"] == "ciento veinte con cincuenta m2 (120,50 m2)"
    assert e["pisos"] == "dos"
    assert e["vigencia"] == "treinta y seis (36) meses"


def test_campos_libres_se_agregan():
    r = _resolucion_valida()
    r.extras = {"expediente": "EXP-99"}
    assert r.etiquetas()["expediente"] == "EXP-99"


def test_nombre_archivo():
    assert _resolucion_valida().nombre_archivo() == \
        "Resolucion_01-2-0456_15-10-2026.docx"


def test_plantilla_maestra_se_rellena_completa(tmp_path):
    """La plantilla de ejemplo no debe dejar ninguna etiqueta sin dato."""
    import crear_plantilla_ejemplo

    ruta = tmp_path / "p.docx"
    crear_plantilla_ejemplo.construir().save(ruta)
    doc = plantilla.abrir(ruta)
    faltantes = plantilla.rellenar(doc, _resolucion_valida().etiquetas())
    assert faltantes == set()
    texto = "\n".join(p.text for p in plantilla.recorrer_parrafos(doc))
    assert "{{" not in texto
    assert "la propietaria MARÍA GÓMEZ" in texto
