"""La comprobación de instalación."""

import verificar


def test_la_comprobacion_pasa_en_una_instalacion_sana(capsys, monkeypatch):
    monkeypatch.setattr(verificar, "fallas", [])
    monkeypatch.setattr(verificar, "avisos", [])
    codigo = verificar.main()
    salida = capsys.readouterr().out
    assert codigo == 0, salida
    assert "[FALLA]" not in salida
    assert "Documento de prueba generado" in salida
    assert "los propietarios" in salida   # comprueba la concordancia


def test_la_generacion_de_prueba_deja_el_documento_con_datos(monkeypatch):
    monkeypatch.setattr(verificar, "fallas", [])
    monkeypatch.setattr(verificar, "avisos", [])
    verificar.revisar_generacion()
    assert verificar.fallas == []
