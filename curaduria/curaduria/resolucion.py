"""Modelo de la resolución y armado del diccionario de etiquetas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import fechas
from .gramatica import Concordancia, Titular
from .numeros import en_letras_y_cifra, entero_a_letras, formato_cifra

TIPOS_TRAMITE = (
    "Licencia de construcción - Obra nueva",
    "Licencia de construcción - Ampliación",
    "Licencia de construcción - Modificación",
    "Licencia de construcción - Reconocimiento",
    "Licencia de construcción - Demolición",
    "Licencia de urbanización",
    "Licencia de subdivisión",
    "Licencia de intervención del espacio público",
    "Prórroga de licencia",
    "Revalidación de licencia",
    "Modificación de licencia vigente",
)

SENTIDOS = ("Conceder", "Negar", "Archivar", "Desistir", "Corregir")


@dataclass
class Inmueble:
    direccion: str = ""
    barrio: str = ""
    municipio: str = ""
    departamento: str = ""
    matricula_inmobiliaria: str = ""
    cedula_catastral: str = ""
    chip: str = ""
    area_lote: float = 0.0
    area_construida: float = 0.0
    tratamiento_urbanistico: str = ""
    uso: str = ""
    pisos: int = 0


@dataclass
class Resolucion:
    numero: str = ""
    fecha: date | None = None
    radicado: str = ""
    fecha_radicado: date | None = None
    tipo_tramite: str = TIPOS_TRAMITE[0]
    sentido: str = SENTIDOS[0]
    curador: str = ""
    genero_curador: str = "M"
    curaduria: str = ""
    titulares: list[Titular] = field(default_factory=list)
    inmueble: Inmueble = field(default_factory=Inmueble)
    proyectista: str = ""
    matricula_profesional: str = ""
    vigencia_meses: int = 36
    observaciones: str = ""
    extras: dict[str, str] = field(default_factory=dict)

    # --- Validación -------------------------------------------------------

    def errores(self) -> list[str]:
        problemas: list[str] = []
        if not self.numero.strip():
            problemas.append("Falta el número de la resolución.")
        if self.fecha is None:
            problemas.append("Falta la fecha de la resolución.")
        if not self.titulares:
            problemas.append("Debe registrarse al menos un titular.")
        for titular in self.titulares:
            if not titular.nombre.strip():
                problemas.append("Hay un titular sin nombre.")
            if not titular.numero_documento.strip():
                problemas.append(
                    f"'{titular.nombre or 'titular sin nombre'}' no tiene número de documento.")
        documentos = [t.numero_documento.strip() for t in self.titulares
                      if t.numero_documento.strip()]
        repetidos = {d for d in documentos if documentos.count(d) > 1}
        for doc in sorted(repetidos):
            problemas.append(f"El documento {doc} está repetido entre los titulares.")
        if not self.inmueble.matricula_inmobiliaria.strip():
            problemas.append("Falta la matrícula inmobiliaria del predio.")
        if (self.fecha and self.fecha_radicado
                and self.fecha_radicado > self.fecha):
            problemas.append("El radicado no puede ser posterior a la resolución.")
        return problemas

    # --- Etiquetas --------------------------------------------------------

    def etiquetas(self) -> dict[str, str]:
        concordancia = Concordancia(self.titulares)
        inmueble = self.inmueble

        datos: dict[str, str] = {
            # Encabezado del acto
            "resolucion_numero": self.numero,
            "radicado": self.radicado,
            "tipo_tramite": self.tipo_tramite,
            "sentido": self.sentido,
            "curador": self.curador,
            "curaduria": self.curaduria,
            "curador_tratamiento": "Curador Urbano" if self.genero_curador == "M"
                                   else "Curadora Urbana",
            # Titulares
            "nombre": concordancia.nombres(),
            "nombres": concordancia.nombres(),
            "documentos": concordancia.documentos(),
            "identificacion": concordancia.identificacion_completa(),
            "calidad": concordancia.frase_calidad(),
            "cantidad_titulares": entero_a_letras(len(self.titulares)),
            # Predio
            "direccion": inmueble.direccion,
            "barrio": inmueble.barrio,
            "municipio": inmueble.municipio,
            "departamento": inmueble.departamento,
            "matricula": inmueble.matricula_inmobiliaria,
            "matricula_inmobiliaria": inmueble.matricula_inmobiliaria,
            "cedula_catastral": inmueble.cedula_catastral,
            "chip": inmueble.chip,
            "tratamiento_urbanistico": inmueble.tratamiento_urbanistico,
            "uso": inmueble.uso,
            "pisos": entero_a_letras(inmueble.pisos) if inmueble.pisos else "",
            "pisos_cifra": str(inmueble.pisos or ""),
            "area_lote": formato_cifra(inmueble.area_lote),
            "area_lote_letras": en_letras_y_cifra(inmueble.area_lote, "m2"),
            "area_construida": formato_cifra(inmueble.area_construida),
            "area_construida_letras": en_letras_y_cifra(inmueble.area_construida, "m2"),
            # Proyecto y vigencia
            "proyectista": self.proyectista,
            "matricula_profesional": self.matricula_profesional,
            "vigencia": f"{entero_a_letras(self.vigencia_meses)} ({self.vigencia_meses}) meses",
            "vigencia_meses": str(self.vigencia_meses),
            "observaciones": self.observaciones,
        }

        datos.update(fechas.etiquetas_fecha("fecha", self.fecha))
        datos.update(fechas.etiquetas_fecha("fecha_radicado", self.fecha_radicado))
        # Las formas gramaticales derivadas del género de los titulares.
        datos.update(concordancia.etiquetas())
        # Campos libres definidos por el usuario (no sobreescriben lo anterior
        # por accidente: se aplican al final a propósito).
        datos.update({k: v for k, v in self.extras.items() if k})
        return datos

    def nombre_archivo(self) -> str:
        numero = (self.numero or "sin-numero").replace("/", "-").replace(" ", "")
        fecha = fechas.fecha_corta(self.fecha).replace("/", "-") if self.fecha else "sin-fecha"
        return f"Resolucion_{numero}_{fecha}.docx"
