"""Nivel 0: la configuración del despacho."""

import json

from curaduria.configuracion import Configuracion


def test_valores_por_defecto_de_ibague():
    config = Configuracion()
    assert config.municipio == "Ibagué"
    assert config.codigo_dane == "73001"
    assert config.genero_curador == "F"


def test_faltantes_y_completa():
    config = Configuracion()
    assert not config.completa
    assert "nombre de quien firma" in config.faltantes()
    config.curador = "SANDRA PARDO"
    config.sustanciador = "GLORIA LOZANO"
    assert config.completa
    assert config.faltantes() == []


def test_dane_no_numerico_es_falta():
    config = Configuracion(curador="A B", sustanciador="C D",
                           codigo_dane="ABCDE")
    assert any("DANE" in f for f in config.faltantes())


def test_construye_el_despacho():
    config = Configuracion(curador="SANDRA PARDO", sustanciador="GLORIA LOZANO")
    despacho = config.despacho()
    assert despacho.tratamiento_largo == (
        "La Curadora Urbana No. 2 del Municipio de Ibagué (P)")
    assert despacho.expediente(2026, "54") == "73001-2-26-0054"


def test_guardar_y_cargar(tmp_path):
    archivo = tmp_path / "configuracion.json"
    original = Configuracion(curador="SANDRA PARDO",
                             sustanciador="GLORIA LOZANO",
                             sustanciador_iniciales="gilt /S",
                             curaduria_numero="3", vigencia_meses=24)
    original.guardar(archivo)
    recuperada = Configuracion.cargar(archivo)
    assert recuperada.curador == "SANDRA PARDO"
    assert recuperada.curaduria_numero == "3"
    assert recuperada.vigencia_meses == 24
    assert recuperada.sustanciador_iniciales == "gilt /S"


def test_cargar_sin_archivo_devuelve_los_valores_por_defecto(tmp_path):
    config = Configuracion.cargar(tmp_path / "no_existe.json")
    assert config.municipio == "Ibagué"
    assert not config.completa


def test_cargar_archivo_danado_no_rompe_la_app(tmp_path):
    archivo = tmp_path / "configuracion.json"
    archivo.write_text("{ esto no es json", encoding="utf-8")
    assert Configuracion.cargar(archivo).municipio == "Ibagué"


def test_cargar_ignora_claves_desconocidas(tmp_path):
    archivo = tmp_path / "configuracion.json"
    archivo.write_text(json.dumps({"municipio": "Tunja", "inventado": 1}),
                       encoding="utf-8")
    config = Configuracion.cargar(archivo)
    assert config.municipio == "Tunja"


def test_guardar_es_atomico(tmp_path):
    """No queda un archivo a medio escribir ni temporales sueltos."""
    archivo = tmp_path / "configuracion.json"
    Configuracion(curador="A B").guardar(archivo)
    assert archivo.exists()
    assert list(tmp_path.glob(".*tmp")) == []
    json.loads(archivo.read_text(encoding="utf-8"))
