"""Biblioteca de bloques de texto."""

import json

import pytest

from curaduria.bloques import CATEGORIAS, Biblioteca, Bloque


@pytest.fixture
def libreria(tmp_path):
    base = tmp_path / "base.json"
    base.write_text(json.dumps([
        {"id": "uno", "titulo": "Bloque uno", "categoria": "encabezado",
         "texto": "Que {{nombres}} solicita licencia.", "obligatorio": True,
         "aplica_a": ["*"], "orden": 10, "origen": "base"},
        {"id": "dos", "titulo": "Bloque dos", "categoria": "normativa",
         "texto": "Párrafo uno.\n\nPárrafo dos sobre {{matricula}}.",
         "aplica_a": ["construccion"], "orden": 20, "origen": "base"},
    ], ensure_ascii=False), encoding="utf-8")
    return Biblioteca(base, tmp_path / "usuario.json")


def test_carga_base(libreria):
    assert len(libreria) == 2
    assert "uno" in libreria


def test_filtra_por_tramite(libreria):
    assert {b.id for b in libreria.para_tramite("construccion")} == {"uno", "dos"}
    assert {b.id for b in libreria.para_tramite("subdivision")} == {"uno"}


def test_obligatorios(libreria):
    assert [b.id for b in libreria.obligatorios("construccion")] == ["uno"]


def test_parrafos_separados_por_linea_en_blanco(libreria):
    assert len(libreria.obtener("dos").parrafos()) == 2


def test_render_sustituye_y_conserva_lo_que_falta(libreria):
    bloque = libreria.obtener("dos")
    salida = bloque.render({"matricula": "350-123456"})
    assert salida[1] == "Párrafo dos sobre 350-123456."
    assert libreria.obtener("uno").render({})[0] == "Que {{nombres}} solicita licencia."


def test_faltantes(libreria):
    assert libreria.obtener("uno").faltantes({}) == ["nombres"]
    assert libreria.obtener("uno").faltantes({"nombres": "ANA"}) == []
    assert libreria.obtener("uno").faltantes({"nombres": ""}) == ["nombres"]


def test_crear_bloque_persiste(libreria, tmp_path):
    creado = libreria.crear("Mi párrafo de siempre", "Texto {{municipio}}",
                            "notas", "Para casos de X")
    assert creado.id == "mi_parrafo_de_siempre"
    otra = Biblioteca(libreria.archivo_base, libreria.archivo_usuario)
    assert "mi_parrafo_de_siempre" in otra
    assert otra.obtener("mi_parrafo_de_siempre").nota == "Para casos de X"


def test_id_no_colisiona(libreria):
    libreria.crear("Nota", "a")
    segundo = libreria.crear("Nota", "b")
    assert segundo.id == "nota_2"


def test_editar_bloque_base_no_toca_el_archivo_base(libreria):
    original = libreria.archivo_base.read_text(encoding="utf-8")
    bloque = libreria.obtener("uno")
    bloque.texto = "Texto corregido."
    libreria.guardar(bloque)
    assert libreria.archivo_base.read_text(encoding="utf-8") == original
    otra = Biblioteca(libreria.archivo_base, libreria.archivo_usuario)
    assert otra.obtener("uno").texto == "Texto corregido."


def test_eliminar_base_solo_desactiva(libreria):
    libreria.eliminar("uno")
    assert "uno" not in {b.id for b in libreria.todos()}
    assert "uno" in {b.id for b in libreria.todos(incluir_inactivos=True)}
    libreria.activar("uno")
    assert "uno" in {b.id for b in libreria.todos()}


def test_eliminar_propio_borra(libreria):
    creado = libreria.crear("Temporal", "x")
    libreria.eliminar(creado.id)
    assert creado.id not in libreria


def test_buscar(libreria):
    assert {b.id for b in libreria.buscar("matrícula")} == set()
    assert {b.id for b in libreria.buscar("matricula")} == {"dos"}
    assert {b.id for b in libreria.buscar("")} == {"uno", "dos"}


def test_seleccion_respeta_el_orden_del_catalogo(libreria):
    assert [b.id for b in libreria.seleccion(["dos", "uno"])] == ["uno", "dos"]


def test_biblioteca_mal_formada(tmp_path):
    malo = tmp_path / "base.json"
    malo.write_text("{no es json", encoding="utf-8")
    with pytest.raises(ValueError, match="error de formato"):
        Biblioteca(malo, tmp_path / "u.json")


def test_bloque_sin_titulo(libreria):
    with pytest.raises(ValueError):
        libreria.guardar(Bloque(id="x", titulo="  "))


# --- La biblioteca real que se distribuye con la app ----------------------

def test_biblioteca_real_es_coherente():
    real = Biblioteca()
    assert len(real) > 50
    ids = [b.id for b in real.todos()]
    assert len(ids) == len(set(ids))
    for bloque in real.todos():
        assert bloque.texto.strip(), f"{bloque.id} sin texto"
        assert bloque.categoria in CATEGORIAS, f"{bloque.id}: {bloque.categoria}"
        assert bloque.titulo.strip()


def test_biblioteca_real_tiene_los_bloques_nucleares():
    real = Biblioteca()
    for id_ in ("preambulo", "solicitud", "art_otorgar", "art_plazo",
                "cierre", "notificacion", "pie_archivo"):
        assert id_ in real, id_
    assert real.obtener("preambulo").obligatorio


def test_biblioteca_real_conserva_el_texto_de_la_plantilla():
    """Los bloques extraídos del modelo no se reescribieron."""
    real = Biblioteca()
    vis = real.obtener("vis")
    assert "Artículo 293 de la Ley 2294 de 2023" in vis.texto
    assert "ciento treinta y cinco (135) salarios mínimos" in vis.texto
    terceros = real.obtener("intervienen_terceros")
    assert "2.2.6.1.2.2.2 del Decreto Nacional 1077 de 2015" in terceros.texto
