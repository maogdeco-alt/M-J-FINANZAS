"""Catálogo de trámites, modalidades y usos."""

import pytest

from curaduria.catalogo import (POR_ID, TRAMITES, USOS, Solicitud,
                                tramites_por_grupo)


def test_los_tres_grupos_tienen_tramites():
    agrupados = tramites_por_grupo()
    assert len(agrupados["licencia"]) == 5
    assert len(agrupados["reconocimiento"]) == 1
    assert len(agrupados["actuacion"]) >= 9


def test_construccion_tiene_las_modalidades_del_decreto():
    nombres = {m.nombre for m in POR_ID["construccion"].modalidades}
    assert {"OBRA NUEVA", "AMPLIACIÓN", "ADECUACIÓN", "MODIFICACIÓN",
            "RESTAURACIÓN", "REFORZAMIENTO ESTRUCTURAL", "DEMOLICIÓN TOTAL",
            "DEMOLICIÓN PARCIAL", "RECONSTRUCCIÓN", "CERRAMIENTO"} == nombres


def test_ids_de_tramite_unicos():
    ids = [t.id for t in TRAMITES]
    assert len(ids) == len(set(ids))


def test_nombre_acto_en_mayusculas():
    assert POR_ID["construccion"].nombre_acto == "Licencia de CONSTRUCCIÓN"
    assert POR_ID["subdivision"].nombre_acto == "Licencia de SUBDIVISIÓN"


def test_modalidades_combinadas():
    s = Solicitud("construccion", ["demolicion_total", "obra_nueva"])
    assert s.frase_modalidades() == (
        "en las modalidades de DEMOLICIÓN TOTAL y OBRA NUEVA")
    assert s.nombre_completo().startswith("Licencia de CONSTRUCCIÓN en las")
    assert s.errores() == []


def test_una_sola_modalidad():
    s = Solicitud("construccion", ["obra_nueva"])
    assert s.frase_modalidades() == "en la modalidad de OBRA NUEVA"


def test_subdivision_no_admite_dos_modalidades():
    s = Solicitud("subdivision", ["loteo", "subdivision_urbana"])
    assert any("una sola modalidad" in e for e in s.errores())


def test_demoliciones_excluyentes():
    s = Solicitud("construccion", ["demolicion_total", "demolicion_parcial"])
    assert any("excluyentes" in e for e in s.errores())


def test_falta_modalidad():
    assert any("exige indicar la modalidad" in e
               for e in Solicitud("construccion", []).errores())


def test_tramite_sin_modalidades_no_exige():
    assert Solicitud("concepto_uso", []).errores() == []


def test_vis_y_vip_detectados():
    assert Solicitud("construccion", ["obra_nueva"], ["vis_unifamiliar"]
                     ).vivienda_interes == "VIS"
    assert Solicitud("construccion", ["obra_nueva"], ["vip"]
                     ).vivienda_interes == "VIP"
    assert Solicitud("construccion", ["obra_nueva"], ["vip", "vis_unifamiliar"]
                     ).vivienda_interes == "VIP"
    assert Solicitud("construccion", ["obra_nueva"], ["comercio"]
                     ).vivienda_interes == ""


def test_usos_combinados():
    s = Solicitud("construccion", ["obra_nueva"], ["vivienda_unifamiliar",
                                                   "comercio"])
    assert s.frase_usos() == "VIVIENDA UNIFAMILIAR y COMERCIO"


def test_etiquetas_del_tramite():
    e = Solicitud("reconocimiento", [], ["vivienda_unifamiliar"]).etiquetas()
    assert e["tramite_grupo"] == "Reconocimiento de edificaciones"
    assert e["destinacion"] == "VIVIENDA UNIFAMILIAR"


@pytest.mark.parametrize("uso", USOS)
def test_todo_uso_tiene_categoria(uso):
    assert uso.categoria
