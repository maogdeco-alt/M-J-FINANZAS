"""Nivel 0: los datos del despacho, que se escriben una sola vez.

La curaduría, el municipio, quién firma y quién sustancia no cambian entre
resoluciones, y en la plantilla modelo aparecen cerca de cincuenta veces. No
tienen por qué volverse a digitar nunca: se guardan aquí y la app los carga al
arrancar.

Se guarda en `configuracion.json`, al lado de la app. Es un archivo de texto
que se puede abrir y corregir a mano si hace falta.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

ARCHIVO = Path(__file__).resolve().parent.parent / "configuracion.json"


@dataclass
class Configuracion:
    """Todo lo que no cambia entre resoluciones."""

    # Despacho
    curaduria_numero: str = "2"
    municipio: str = "Ibagué"
    departamento: str = "Tolima"
    codigo_dane: str = "73001"

    # Quién firma
    curador: str = ""
    genero_curador: str = "F"
    encargado: bool = True

    # Quién sustancia
    sustanciador: str = ""
    sustanciador_iniciales: str = ""

    # Valores por defecto de cada resolución nueva
    vigencia_meses: int = 36
    prorroga_meses: int = 12
    plantilla_preferida: str = ""

    # Preferencias de captura
    nombres_en_mayuscula: bool = True
    sugerir_sexo: bool = True

    def despacho(self):
        """Construye el Despacho del modelo con estos datos."""
        from .resolucion import Despacho
        return Despacho(
            curaduria_numero=self.curaduria_numero,
            municipio=self.municipio,
            departamento=self.departamento,
            codigo_dane=self.codigo_dane,
            curador=self.curador,
            genero_curador=self.genero_curador,
            encargado=self.encargado,
            sustanciador=self.sustanciador,
            sustanciador_iniciales=self.sustanciador_iniciales,
        )

    # --- Estado -----------------------------------------------------------

    def faltantes(self) -> list[str]:
        """Qué falta para que la configuración sirva."""
        pendientes = []
        if not self.curaduria_numero.strip():
            pendientes.append("número de la curaduría")
        if not self.municipio.strip():
            pendientes.append("municipio")
        if not self.codigo_dane.strip().isdigit():
            pendientes.append("código DANE (cinco dígitos)")
        if not self.curador.strip():
            pendientes.append("nombre de quien firma")
        if not self.sustanciador.strip():
            pendientes.append("nombre de quien sustancia")
        return pendientes

    @property
    def completa(self) -> bool:
        return not self.faltantes()

    # --- Persistencia -----------------------------------------------------

    def guardar(self, archivo: Path | None = None) -> Path:
        destino = archivo or ARCHIVO
        contenido = json.dumps(asdict(self), ensure_ascii=False, indent=2)
        destino.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporal = tempfile.mkstemp(
            dir=destino.parent, prefix=f".{destino.name}.", suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as salida:
                salida.write(contenido)
                salida.flush()
                os.fsync(salida.fileno())
            os.replace(temporal, destino)
        except BaseException:
            Path(temporal).unlink(missing_ok=True)
            raise
        return destino

    @classmethod
    def cargar(cls, archivo: Path | None = None) -> "Configuracion":
        """Lee la configuración. Si no existe o está dañada, usa los valores
        por defecto en vez de fallar: la app siempre tiene que abrir."""
        origen = archivo or ARCHIVO
        if not origen.exists():
            return cls()
        try:
            datos = json.loads(origen.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        if not isinstance(datos, dict):
            return cls()
        validos = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in datos.items() if k in validos})
