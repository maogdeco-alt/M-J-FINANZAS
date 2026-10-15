"""Biblioteca de bloques de texto predeterminado.

La resolución no se escribe de cero: se arma escogiendo párrafos de un catálogo
y descartando los que no aplican al caso. Esta biblioteca guarda ese catálogo
con tres datos que el documento de Word no puede guardar: a qué trámites aplica
cada bloque, si es obligatorio y una nota de cuándo usarlo.

Hay dos capas:
    - `bloques_base.json`  catálogo de la curaduría, versionado con la app.
    - `bloques_usuario.json`  lo que agregue o ajuste la sustanciadora. Nunca
      se sobrescribe al actualizar la app, y puede desactivar un bloque base
      sin borrarlo.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from .plantilla import ETIQUETA

RUTA_BIBLIOTECA = Path(__file__).resolve().parent.parent / "biblioteca"
ARCHIVO_BASE = RUTA_BIBLIOTECA / "bloques_base.json"
ARCHIVO_USUARIO = RUTA_BIBLIOTECA / "bloques_usuario.json"

CATEGORIAS = {
    "encabezado": "Encabezado y solicitud",
    "tramite": "Actuaciones del trámite",
    "titularidad": "Titularidad y poderes",
    "vivienda_interes": "VIS / VIP",
    "soportes": "Soportes y aprobaciones",
    "terceros": "Vecinos y terceros",
    "tecnico": "Soportes técnicos",
    "normativa": "Normativa urbanística",
    "plusvalia": "Plusvalía",
    "expensas": "Expensas, IDU y exenciones",
    "resuelve": "Parte resolutiva",
    "cierre": "Cierre, firma y notificación",
    "notas": "Notas de la sustanciadora",
}

ORDEN_CATEGORIAS = list(CATEGORIAS)


@dataclass
class Bloque:
    id: str
    titulo: str
    categoria: str = "notas"
    texto: str = ""
    nota: str = ""
    obligatorio: bool = False
    aplica_a: list[str] = field(default_factory=lambda: ["*"])
    orden: int = 999
    origen: str = "usuario"
    activo: bool = True
    modificado: str = ""

    def aplica(self, tramite_id: str) -> bool:
        return "*" in self.aplica_a or tramite_id in self.aplica_a

    def etiquetas(self) -> list[str]:
        """Etiquetas {{...}} que usa el bloque, sin repetir."""
        vistas: dict[str, None] = {}
        for clave in ETIQUETA.findall(self.texto):
            vistas.setdefault(clave, None)
        return list(vistas)

    def parrafos(self) -> list[str]:
        """El texto partido en párrafos, como se insertará en el Word."""
        return [p for p in re.split(r"\n{2,}", self.texto.strip()) if p.strip()]

    def render(self, datos: Mapping[str, str]) -> list[str]:
        """Párrafos con las etiquetas resueltas. Las que no tienen dato quedan."""
        def sustituir(coincidencia: re.Match) -> str:
            clave = coincidencia.group(1)
            if clave in datos and datos[clave] not in (None, ""):
                return str(datos[clave])
            return coincidencia.group(0)
        return [ETIQUETA.sub(sustituir, p) for p in self.parrafos()]

    def faltantes(self, datos: Mapping[str, str]) -> list[str]:
        return [c for c in self.etiquetas()
                if c not in datos or datos[c] in (None, "")]

    def a_dict(self) -> dict:
        return {
            "id": self.id, "titulo": self.titulo, "categoria": self.categoria,
            "texto": self.texto, "nota": self.nota,
            "obligatorio": self.obligatorio, "aplica_a": self.aplica_a,
            "orden": self.orden, "origen": self.origen, "activo": self.activo,
            "modificado": self.modificado,
        }

    @classmethod
    def de_dict(cls, datos: Mapping) -> "Bloque":
        return cls(
            id=datos["id"],
            titulo=datos.get("titulo", datos["id"]),
            categoria=datos.get("categoria", "notas"),
            texto=datos.get("texto", ""),
            nota=datos.get("nota", ""),
            obligatorio=bool(datos.get("obligatorio", False)),
            aplica_a=list(datos.get("aplica_a", ["*"])),
            orden=int(datos.get("orden", 999)),
            origen=datos.get("origen", "usuario"),
            activo=bool(datos.get("activo", True)),
            modificado=datos.get("modificado", ""),
        )


class Biblioteca:
    """Catálogo base + ajustes del usuario, con guardado en disco."""

    def __init__(self, archivo_base: Path | None = None,
                 archivo_usuario: Path | None = None):
        self.archivo_base = archivo_base or ARCHIVO_BASE
        self.archivo_usuario = archivo_usuario or ARCHIVO_USUARIO
        self._bloques: dict[str, Bloque] = {}
        self.cargar()

    # --- Persistencia -----------------------------------------------------

    def cargar(self) -> None:
        self._bloques = {}
        for archivo, origen in ((self.archivo_base, "base"),
                                (self.archivo_usuario, "usuario")):
            if not archivo or not archivo.exists():
                continue
            try:
                datos = json.loads(archivo.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"La biblioteca {archivo.name} tiene un error de formato: {error}"
                ) from error
            for entrada in datos:
                bloque = Bloque.de_dict(entrada)
                if origen == "base" and bloque.origen == "usuario":
                    bloque.origen = "base"
                self._bloques[bloque.id] = bloque

    def guardar_usuario(self) -> None:
        """Guarda solo lo que el usuario creó o ajustó."""
        propios = []
        base = self._leer_base_cruda()
        for bloque in self._bloques.values():
            original = base.get(bloque.id)
            if original is None or original != bloque.a_dict():
                propios.append(bloque.a_dict())
        self.archivo_usuario.parent.mkdir(parents=True, exist_ok=True)
        self.archivo_usuario.write_text(
            json.dumps(propios, ensure_ascii=False, indent=2), encoding="utf-8")

    def _leer_base_cruda(self) -> dict[str, dict]:
        if not self.archivo_base or not self.archivo_base.exists():
            return {}
        datos = json.loads(self.archivo_base.read_text(encoding="utf-8"))
        crudos = {}
        for entrada in datos:
            bloque = Bloque.de_dict(entrada)
            if bloque.origen == "usuario":
                bloque.origen = "base"
            crudos[bloque.id] = bloque.a_dict()
        return crudos

    # --- Consulta ---------------------------------------------------------

    def __len__(self) -> int:
        return len(self._bloques)

    def __contains__(self, id_: str) -> bool:
        return id_ in self._bloques

    def obtener(self, id_: str) -> Bloque:
        return self._bloques[id_]

    def todos(self, incluir_inactivos: bool = False) -> list[Bloque]:
        bloques = [b for b in self._bloques.values()
                   if b.activo or incluir_inactivos]
        return sorted(bloques, key=lambda b: (b.orden, b.titulo))

    def para_tramite(self, tramite_id: str) -> list[Bloque]:
        return [b for b in self.todos() if b.aplica(tramite_id)]

    def obligatorios(self, tramite_id: str) -> list[Bloque]:
        return [b for b in self.para_tramite(tramite_id) if b.obligatorio]

    def por_categoria(self, tramite_id: str | None = None
                      ) -> dict[str, list[Bloque]]:
        bloques = self.para_tramite(tramite_id) if tramite_id else self.todos()
        agrupados: dict[str, list[Bloque]] = {}
        for bloque in bloques:
            agrupados.setdefault(bloque.categoria, []).append(bloque)
        return {clave: agrupados[clave] for clave in ORDEN_CATEGORIAS
                if clave in agrupados}

    def buscar(self, texto: str) -> list[Bloque]:
        termino = texto.strip().lower()
        if not termino:
            return self.todos()
        return [b for b in self.todos()
                if termino in b.titulo.lower() or termino in b.texto.lower()
                or termino in b.nota.lower()]

    def seleccion(self, ids: Iterable[str]) -> list[Bloque]:
        """Los bloques indicados, en el orden del catálogo."""
        elegidos = [self._bloques[i] for i in ids if i in self._bloques]
        return sorted(elegidos, key=lambda b: (b.orden, b.titulo))

    # --- Edición ----------------------------------------------------------

    def guardar(self, bloque: Bloque) -> Bloque:
        if not bloque.id.strip():
            raise ValueError("El bloque necesita un identificador.")
        if not bloque.titulo.strip():
            raise ValueError("El bloque necesita un título.")
        bloque.modificado = datetime.now().isoformat(timespec="seconds")
        self._bloques[bloque.id] = bloque
        self.guardar_usuario()
        return bloque

    def crear(self, titulo: str, texto: str, categoria: str = "notas",
              nota: str = "", aplica_a: list[str] | None = None,
              orden: int = 999) -> Bloque:
        bloque = Bloque(
            id=self._id_libre(titulo), titulo=titulo.strip(), categoria=categoria,
            texto=texto, nota=nota, aplica_a=aplica_a or ["*"], orden=orden,
            origen="usuario",
        )
        return self.guardar(bloque)

    def desactivar(self, id_: str) -> None:
        """Oculta un bloque sin borrarlo (los base no se pueden borrar)."""
        bloque = self._bloques[id_]
        bloque.activo = False
        self.guardar(bloque)

    def activar(self, id_: str) -> None:
        bloque = self._bloques[id_]
        bloque.activo = True
        self.guardar(bloque)

    def eliminar(self, id_: str) -> None:
        bloque = self._bloques[id_]
        if bloque.origen == "base":
            self.desactivar(id_)
            return
        del self._bloques[id_]
        self.guardar_usuario()

    def _id_libre(self, titulo: str) -> str:
        sin_tildes = "".join(
            c for c in unicodedata.normalize("NFD", titulo.strip().lower())
            if unicodedata.category(c) != "Mn")
        base = re.sub(r"[^a-z0-9]+", "_", sin_tildes).strip("_") or "bloque"
        candidato = base
        contador = 2
        while candidato in self._bloques:
            candidato = f"{base}_{contador}"
            contador += 1
        return candidato
