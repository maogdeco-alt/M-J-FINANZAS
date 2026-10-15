"""Normalización de lo que digita la sustanciadora."""

import pytest

from curaduria import formato


@pytest.mark.parametrize("entrada,esperado", [
    ("350250605", "350-250605"),
    ("350-250605", "350-250605"),
    ("350 250 605", "350-250605"),
    ("350.250.605", "350-250605"),
])
def test_matricula_se_normaliza(entrada, esperado):
    revision = formato.normalizar_matricula(entrada)
    assert revision.valor == esperado
    assert revision.estado == "bien"


def test_matricula_corta_avisa_sin_bloquear():
    revision = formato.normalizar_matricula("35025")
    assert revision.estado == "duda"
    assert "al menos 7" in revision.mensaje


def test_matricula_larga_se_marca_mal():
    assert formato.normalizar_matricula("3502506051234").estado == "mal"


def test_matricula_vacia():
    assert formato.normalizar_matricula("").estado == "vacio"
    assert formato.normalizar_matricula("").bien


def test_matricula_sin_digitos():
    assert formato.normalizar_matricula("abc").estado == "mal"


@pytest.mark.parametrize("entrada", [
    "010910140013000", "01-09-1014-0013-000", "01 09 1014 0013 000",
])
def test_ficha_catastral_se_normaliza(entrada):
    revision = formato.normalizar_ficha_catastral(entrada)
    assert revision.valor == "01-09-1014-0013-000"
    assert revision.estado == "bien"


def test_ficha_incompleta_dice_cuantos_faltan():
    revision = formato.normalizar_ficha_catastral("01-09-1014")
    assert revision.estado == "duda"
    assert "faltan 7" in revision.mensaje


def test_ficha_con_demasiados_digitos():
    assert formato.normalizar_ficha_catastral("0" * 17).estado == "mal"


def test_documento_con_puntos_de_miles():
    assert formato.normalizar_documento("79351573").valor == "79.351.573"
    assert formato.normalizar_documento("79.351.573").valor == "79.351.573"


def test_nit_exige_digito_de_verificacion():
    sin = formato.normalizar_documento("900123456", "NIT")
    assert sin.estado == "duda" and "verificación" in sin.mensaje
    con = formato.normalizar_documento("900123456-1", "NIT")
    assert con.estado == "bien" and con.valor == "900.123.456-1"


def test_pasaporte_admite_letras():
    revision = formato.normalizar_documento("ab123456", "PAS")
    assert revision.valor == "AB123456"
    assert revision.estado == "bien"


def test_cedula_muy_corta_duda():
    assert formato.normalizar_documento("123").estado == "duda"


def test_nombre_a_mayuscula_y_sin_espacios_dobles():
    revision = formato.normalizar_nombre("  maría   gómez  de rojas ")
    assert revision.valor == "MARÍA GÓMEZ DE ROJAS"
    assert revision.estado == "bien"


def test_nombre_sin_apellido_avisa():
    assert formato.normalizar_nombre("maria").estado == "duda"


def test_nombre_con_numeros_avisa():
    assert formato.normalizar_nombre("JUAN 123 PÉREZ").estado == "duda"


def test_nombre_sin_mayuscula_cuando_se_pide():
    assert formato.normalizar_nombre("maría gómez", False).valor == "maría gómez"


def test_radicado_sin_puntos():
    assert formato.normalizar_radicado("2.600.789").valor == "2600789"
    assert formato.normalizar_radicado(" 2600789 ").valor == "2600789"


def test_radicado_con_letras_duda():
    assert formato.normalizar_radicado("RAD-2026-abc").estado == "duda"


def test_consecutivo_se_completa_a_cuatro_digitos():
    assert formato.normalizar_consecutivo("54").valor == "0054"
    assert formato.normalizar_consecutivo("1234").valor == "1234"


def test_consecutivo_demasiado_largo():
    assert formato.normalizar_consecutivo("12345").estado == "mal"


@pytest.mark.parametrize("entrada,esperado", [
    ("cra 2 sur no 28-57", "Carrera 2 Sur No. 28-57"),
    ("cl 10 # 5-20", "Calle 10 # 5-20"),
    ("av ambalá no 42-15", "Avenida Ambalá No. 42-15"),
])
def test_direccion_desarma_las_abreviaturas(entrada, esperado):
    assert formato.normalizar_direccion(entrada).valor == esperado


def test_direccion_sin_numeros_duda():
    assert formato.normalizar_direccion("barrio centro").estado == "duda"


@pytest.mark.parametrize("entrada,esperado", [
    ("0,70", "0,7"), ("0.70", "0,7"), ("70%", "70%"), ("2.5", "2,5"),
])
def test_indice_normalizado(entrada, esperado):
    assert formato.normalizar_indice(entrada).valor == esperado


def test_indice_no_numerico():
    assert formato.normalizar_indice("mucho").estado == "mal"


def test_iconos_de_estado():
    assert formato.normalizar_matricula("350250605").icono == "✓"
    assert formato.normalizar_matricula("35025").icono == "⚠️"
    assert formato.normalizar_matricula("abc").icono == "✕"
    assert formato.normalizar_matricula("").icono == ""
