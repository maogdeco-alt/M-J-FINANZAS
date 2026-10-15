"""Modelo de la resolución y armado del diccionario de etiquetas.

Los campos siguen los datos que realmente aparecen repetidos en las
resoluciones de la curaduría: expediente, radicado, folio de matrícula,
ficha catastral, estrato, índices, profesionales y los oficios del trámite.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from . import fechas
from .catalogo import Solicitud
from .gramatica import Concordancia, Titular, formato_documento, unir_con_y
from .numeros import en_letras_y_cifra, entero_a_letras, formato_cifra
from .profesionales import Profesional
from .profesionales import etiquetas as etiquetas_profesionales

SENTIDOS = {
    "otorgar": ("OTORGAR", "Conceder la licencia o el reconocimiento"),
    "negar": ("NEGAR", "Negar la solicitud"),
    "archivar": ("ARCHIVAR", "Archivar por desistimiento o inactividad"),
    "desistir": ("ACEPTAR EL DESISTIMIENTO", "Desistimiento expreso"),
    "corregir": ("CORREGIR", "Corrección de un acto anterior"),
    "prorrogar": ("PRORROGAR", "Prórroga de licencia vigente"),
    "revalidar": ("REVALIDAR", "Revalidación de licencia vencida"),
}

CUBIERTAS = ("placa", "teja", "teja de barro", "teja de fibrocemento",
             "teja termoacústica", "placa y teja", "cubierta verde")

RE_FICHA_CATASTRAL = re.compile(r"^\d{2}-\d{2}-\d{4}-\d{4}-\d{3}$")
RE_MATRICULA = re.compile(r"^\d{3}-\d{4,8}$")


@dataclass
class Despacho:
    """La curaduría que expide el acto."""

    curaduria_numero: str = "2"
    municipio: str = "Ibagué"
    departamento: str = "Tolima"
    codigo_dane: str = "73001"
    curador: str = ""
    genero_curador: str = "F"
    encargado: bool = True          # el "(P)" de curador(a) en provisionalidad
    sustanciador: str = ""
    sustanciador_iniciales: str = ""

    @property
    def tratamiento(self) -> str:
        base = ("Curadora Urbana" if self.genero_curador == "F"
                else "Curador Urbano")
        return f"{base} No. {self.curaduria_numero} de {self.municipio}" + (
            " (P)" if self.encargado else "")

    @property
    def tratamiento_largo(self) -> str:
        articulo = "La" if self.genero_curador == "F" else "El"
        base = ("Curadora Urbana" if self.genero_curador == "F"
                else "Curador Urbano")
        return (f"{articulo} {base} No. {self.curaduria_numero} del Municipio de "
                f"{self.municipio}" + (" (P)" if self.encargado else ""))

    @property
    def nombre_curaduria(self) -> str:
        return (f"Curaduría Urbana No. {self.curaduria_numero} de "
                f"{self.municipio}")

    def expediente(self, anio: int | None, consecutivo: str) -> str:
        """Número de expediente: 73001-2-26-0054."""
        if not consecutivo.strip():
            return ""
        if anio is None:
            return ""
        return (f"{self.codigo_dane}-{self.curaduria_numero}-"
                f"{anio % 100:02d}-{consecutivo.strip().zfill(4)}")


@dataclass
class Inmueble:
    direccion: str = ""
    barrio: str = ""
    matricula_inmobiliaria: str = ""
    ficha_catastral: str = ""
    chip: str = ""
    estrato: str = ""
    area_lote: float = 0.0
    area_construida: float = 0.0
    area_demoler: float = 0.0
    area_existente: float = 0.0
    pisos: int = 0
    cubierta: str = "placa"
    tratamiento_urbanistico: str = ""
    uso_principal: str = ""
    indice_construccion_permitido: str = ""
    indice_construccion_propuesto: str = ""
    indice_ocupacion_permitido: str = ""
    indice_ocupacion_propuesto: str = ""
    areas_por_piso: str = ""        # texto libre: "PRIMER PISO de 113,50 m²…"
    parqueaderos: str = ""
    amenaza_riesgo: str = ""


@dataclass
class Apoderado:
    nombre: str = ""
    genero: str = "M"
    documento: str = ""

    def frase(self) -> str:
        if not self.nombre.strip():
            return ""
        participio = "identificada" if self.genero == "F" else "identificado"
        articulo = "la" if self.genero == "F" else "el"
        tratamiento = "señora" if self.genero == "F" else "señor"
        documento = formato_documento(self.documento)
        texto = f"{articulo} {tratamiento} {self.nombre}"
        if documento:
            texto += f", {participio} con CC. No. {documento}"
        return texto


@dataclass
class Actuaciones:
    """Oficios, autos y fechas del trámite. Todos opcionales."""

    reparto_numero: str = ""
    reparto_fecha: date | None = None
    fecha_debida_forma: date | None = None
    folio_fecha: date | None = None
    folio_anotacion: str = ""
    escritura_numero: str = ""
    escritura_fecha: date | None = None
    escritura_notaria: str = ""
    acta_observaciones_oficio: str = ""
    acta_observaciones_fecha: date | None = None
    respuesta_observaciones_oficio: str = ""
    respuesta_observaciones_fecha: date | None = None
    auto_numero: str = ""
    auto_fecha: date | None = None
    viabilidad_oficio: str = ""
    viabilidad_fecha: date | None = None
    idu_certificado: str = ""
    idu_valor: str = ""
    factura_numero: str = ""
    factura_fecha: date | None = None
    planos_arquitectonicos: int = 0
    planos_estructurales: int = 0
    tomos_memorias: int = 0
    tomos_suelos: int = 0
    valla_radicado: str = ""
    valla_fecha: date | None = None


@dataclass
class Notificacion:
    nombre: str = ""
    genero: str = "M"
    documento: str = ""
    calidad: str = "apoderado"     # apoderado | titular | tercero

    @property
    def rotulo(self) -> str:
        return "La notificada" if self.genero == "F" else "El notificado"


@dataclass
class Resolucion:
    numero: str = ""
    fecha: date | None = None
    radicado: str = ""
    fecha_radicado: date | None = None
    consecutivo_expediente: str = ""
    expediente_manual: str = ""
    sentido: str = "otorgar"
    solicitud: Solicitud = field(default_factory=Solicitud)
    despacho: Despacho = field(default_factory=Despacho)
    titulares: list[Titular] = field(default_factory=list)
    apoderado: Apoderado = field(default_factory=Apoderado)
    inmueble: Inmueble = field(default_factory=Inmueble)
    profesionales: list[Profesional] = field(default_factory=list)
    actuaciones: Actuaciones = field(default_factory=Actuaciones)
    notificacion: Notificacion = field(default_factory=Notificacion)
    vigencia_meses: int = 36
    prorroga_meses: int = 12
    observaciones: str = ""
    extras: dict[str, str] = field(default_factory=dict)

    # --- Derivados --------------------------------------------------------

    @property
    def expediente(self) -> str:
        if self.expediente_manual.strip():
            return self.expediente_manual.strip()
        anio = (self.fecha_radicado or self.fecha).year if (
            self.fecha_radicado or self.fecha) else None
        return self.despacho.expediente(anio, self.consecutivo_expediente)

    @property
    def concordancia(self) -> Concordancia:
        return Concordancia(self.titulares)

    def frase_solicitante(self) -> str:
        """Quién solicita: el apoderado si lo hay, o los titulares."""
        concordancia = self.concordancia
        if self.apoderado.nombre.strip():
            return (f"{self.apoderado.frase()} en calidad de apoderado del "
                    f"trámite")
        return f"{concordancia.identificacion_completa()}, " \
               f"{concordancia.frase_calidad()}"

    # --- Validación -------------------------------------------------------

    def errores(self) -> list[str]:
        problemas: list[str] = []
        if not self.numero.strip():
            problemas.append("Falta el número de la resolución.")
        if self.fecha is None:
            problemas.append("Falta la fecha de la resolución.")
        if not self.despacho.curador.strip():
            problemas.append("Falta el nombre de quien firma el acto.")
        if not self.titulares:
            problemas.append("Debe registrarse al menos un titular.")
        for titular in self.titulares:
            if not titular.nombre.strip():
                problemas.append("Hay un titular sin nombre.")
            if not titular.numero_documento.strip():
                problemas.append(
                    f"'{titular.nombre or 'titular sin nombre'}' no tiene "
                    "número de documento.")
        documentos = [t.numero_documento.strip() for t in self.titulares
                      if t.numero_documento.strip()]
        for doc in sorted({d for d in documentos if documentos.count(d) > 1}):
            problemas.append(f"El documento {doc} está repetido entre los titulares.")

        problemas.extend(self.solicitud.errores())

        inmueble = self.inmueble
        if self.solicitud.tramite.requiere_predio:
            if not inmueble.matricula_inmobiliaria.strip():
                problemas.append("Falta la matrícula inmobiliaria del predio.")
            elif not RE_MATRICULA.match(inmueble.matricula_inmobiliaria.strip()):
                problemas.append(
                    "La matrícula inmobiliaria no tiene la forma 350-123456: "
                    f"'{inmueble.matricula_inmobiliaria}'.")
            if inmueble.ficha_catastral.strip() and not RE_FICHA_CATASTRAL.match(
                    inmueble.ficha_catastral.strip()):
                problemas.append(
                    "La ficha catastral no tiene la forma 01-09-1014-0013-000: "
                    f"'{inmueble.ficha_catastral}'.")
            if not inmueble.direccion.strip():
                problemas.append("Falta la dirección del predio.")

        if (self.fecha and self.fecha_radicado
                and self.fecha_radicado > self.fecha):
            problemas.append("El radicado no puede ser posterior a la resolución.")
        if (self.actuaciones.fecha_debida_forma and self.fecha_radicado
                and self.actuaciones.fecha_debida_forma < self.fecha_radicado):
            problemas.append(
                "La fecha de legal y debida forma no puede ser anterior al radicado.")

        if "demolicion_total" in self.solicitud.modalidades_ids and not inmueble.area_demoler:
            problemas.append(
                "La modalidad de demolición total exige el área a demoler.")
        if ("obra_nueva" in self.solicitud.modalidades_ids
                and not inmueble.area_construida):
            problemas.append("La modalidad de obra nueva exige el área construida.")
        if (inmueble.area_lote and inmueble.area_construida
                and self.solicitud.tramite_id == "construccion"
                and inmueble.area_construida > inmueble.area_lote * 20):
            problemas.append(
                "El área construida supera veinte veces el área del lote: "
                "verifique las cifras.")
        for permitido, propuesto, nombre in (
            (inmueble.indice_construccion_permitido,
             inmueble.indice_construccion_propuesto, "construcción"),
            (inmueble.indice_ocupacion_permitido,
             inmueble.indice_ocupacion_propuesto, "ocupación"),
        ):
            valor_permitido = _a_numero(permitido)
            valor_propuesto = _a_numero(propuesto)
            if (valor_permitido is not None and valor_propuesto is not None
                    and valor_propuesto > valor_permitido):
                problemas.append(
                    f"El índice de {nombre} propuesto ({propuesto}) supera el "
                    f"permitido ({permitido}).")

        for profesional in self.profesionales:
            if profesional.nombre.strip() and not profesional.matricula.strip():
                problemas.append(
                    f"{profesional.nombre} no tiene matrícula profesional.")
        if (self.solicitud.tramite_id == "construccion"
                and self.sentido == "otorgar"):
            roles = {p.rol for p in self.profesionales if p.nombre.strip()}
            for rol, nombre in (("proyectista", "proyectista arquitectónico"),
                                ("constructor", "constructor responsable")):
                if rol not in roles:
                    problemas.append(f"Falta el {nombre}.")
        return problemas

    def advertencias(self) -> list[str]:
        """Cosas que no bloquean, pero conviene revisar antes de firmar."""
        avisos: list[str] = []
        inmueble = self.inmueble
        if self.concordancia.mixto:
            avisos.append(
                "Titulares de distinto sexo: el texto queda en masculino plural "
                "(los propietarios), como corresponde gramaticalmente.")
        if self.solicitud.vivienda_interes and not inmueble.estrato:
            avisos.append(
                f"Proyecto {self.solicitud.vivienda_interes} sin estrato: el "
                "estrato define la exención del IDU y las expensas.")
        if inmueble.amenaza_riesgo:
            avisos.append(
                "Predio con condición de amenaza o riesgo: recuerde el bloque "
                "del estudio geológico.")
        if not self.actuaciones.idu_certificado and self.sentido == "otorgar":
            avisos.append("Sin certificado IDU registrado.")
        if not self.expediente:
            avisos.append(
                "Sin número de expediente: indique el consecutivo para que se "
                "arme como 73001-2-26-0054.")
        return avisos

    # --- Etiquetas --------------------------------------------------------

    def etiquetas(self) -> dict[str, str]:
        concordancia = self.concordancia
        despacho = self.despacho
        inmueble = self.inmueble
        actuaciones = self.actuaciones
        sentido_verbo = SENTIDOS.get(self.sentido, ("OTORGAR", ""))[0]

        datos: dict[str, str] = {
            "resolucion_numero": self.numero,
            "radicado": self.radicado,
            "expediente": self.expediente,
            "sentido": sentido_verbo,
            "sentido_verbo": sentido_verbo,
            "vigencia": f"{entero_a_letras(self.vigencia_meses)} "
                        f"({self.vigencia_meses}) meses",
            "vigencia_meses": str(self.vigencia_meses),
            "prorroga": f"{entero_a_letras(self.prorroga_meses)} "
                        f"({self.prorroga_meses}) meses",
            "observaciones": self.observaciones,

            # Despacho
            "curaduria": despacho.nombre_curaduria,
            "curaduria_numero": despacho.curaduria_numero,
            "curador": despacho.curador,
            "curador_tratamiento": despacho.tratamiento,
            "curador_tratamiento_largo": despacho.tratamiento_largo,
            "municipio": despacho.municipio,
            "departamento": despacho.departamento,
            "sustanciador": despacho.sustanciador,
            "sustanciador_iniciales": despacho.sustanciador_iniciales,

            # Titulares y representación
            "nombre": concordancia.nombres(),
            "nombres": concordancia.nombres(),
            "documentos": concordancia.documentos(),
            "identificacion": concordancia.identificacion_completa(),
            "calidad": concordancia.frase_calidad(),
            "cantidad_titulares": entero_a_letras(len(self.titulares)),
            "apoderado_nombre": self.apoderado.nombre,
            "apoderado_documento": formato_documento(self.apoderado.documento),
            "apoderado_identificacion": self.apoderado.frase(),
            "solicitante_frase": self.frase_solicitante(),

            # Predio
            "direccion": inmueble.direccion,
            "barrio": inmueble.barrio,
            "matricula": inmueble.matricula_inmobiliaria,
            "matricula_inmobiliaria": inmueble.matricula_inmobiliaria,
            "ficha_catastral": inmueble.ficha_catastral,
            "cedula_catastral": inmueble.ficha_catastral,
            "chip": inmueble.chip,
            "estrato": inmueble.estrato,
            "estrato_letras": (f"{entero_a_letras(int(inmueble.estrato))} "
                               f"({inmueble.estrato})")
                              if str(inmueble.estrato).isdigit() else inmueble.estrato,
            "tratamiento_urbanistico": inmueble.tratamiento_urbanistico,
            "uso_principal": inmueble.uso_principal,
            "cubierta": inmueble.cubierta,
            "pisos": entero_a_letras(inmueble.pisos) if inmueble.pisos else "",
            "pisos_cifra": str(inmueble.pisos or ""),
            "area_lote": formato_cifra(inmueble.area_lote),
            "area_lote_letras": en_letras_y_cifra(inmueble.area_lote, "m2"),
            "area_construida": formato_cifra(inmueble.area_construida),
            "area_construida_letras": en_letras_y_cifra(
                inmueble.area_construida, "m2"),
            "area_demoler": formato_cifra(inmueble.area_demoler),
            "area_demoler_letras": en_letras_y_cifra(inmueble.area_demoler, "m2"),
            "area_existente": formato_cifra(inmueble.area_existente),
            "indice_construccion_permitido": inmueble.indice_construccion_permitido,
            "indice_construccion_propuesto": inmueble.indice_construccion_propuesto,
            "indice_ocupacion_permitido": inmueble.indice_ocupacion_permitido,
            "indice_ocupacion_propuesto": inmueble.indice_ocupacion_propuesto,
            "areas_por_piso": inmueble.areas_por_piso,
            "parqueaderos": inmueble.parqueaderos,
            "amenaza_riesgo": inmueble.amenaza_riesgo,

            # Actuaciones del trámite
            "reparto_numero": actuaciones.reparto_numero,
            "folio_anotacion": actuaciones.folio_anotacion,
            "escritura_numero": actuaciones.escritura_numero,
            "escritura_notaria": actuaciones.escritura_notaria,
            "escritura_fecha": (fechas.fecha_corta(actuaciones.escritura_fecha)
                                if actuaciones.escritura_fecha else ""),
            "acta_observaciones_oficio": actuaciones.acta_observaciones_oficio,
            "respuesta_observaciones_oficio":
                actuaciones.respuesta_observaciones_oficio,
            "auto_numero": actuaciones.auto_numero,
            "viabilidad_oficio": actuaciones.viabilidad_oficio,
            "idu_certificado": actuaciones.idu_certificado,
            "idu_valor": actuaciones.idu_valor,
            "factura_numero": actuaciones.factura_numero,
            "valla_radicado": actuaciones.valla_radicado,
            "planos_arquitectonicos": str(actuaciones.planos_arquitectonicos or ""),
            "planos_estructurales": str(actuaciones.planos_estructurales or ""),
            "tomos_memorias": str(actuaciones.tomos_memorias or ""),
            "tomos_suelos": str(actuaciones.tomos_suelos or ""),

            # Notificación
            "notificado_nombre": self.notificacion.nombre,
            "notificado_documento": (f"CC No. {formato_documento(self.notificacion.documento)}"
                                     if self.notificacion.documento else ""),
            "notificado_rotulo": self.notificacion.rotulo,
            "notificado_calidad": self.notificacion.calidad,
        }

        for prefijo, valor in (
            ("fecha", self.fecha),
            ("fecha_radicado", self.fecha_radicado),
            ("reparto_fecha", actuaciones.reparto_fecha),
            ("fecha_debida_forma", actuaciones.fecha_debida_forma),
            ("folio_fecha", actuaciones.folio_fecha),
            ("acta_observaciones_fecha", actuaciones.acta_observaciones_fecha),
            ("respuesta_observaciones_fecha",
             actuaciones.respuesta_observaciones_fecha),
            ("auto_fecha", actuaciones.auto_fecha),
            ("viabilidad_fecha", actuaciones.viabilidad_fecha),
            ("factura_fecha", actuaciones.factura_fecha),
            ("valla_fecha", actuaciones.valla_fecha),
        ):
            datos.update(fechas.etiquetas_fecha(prefijo, valor))

        datos.update(self.solicitud.etiquetas())
        datos.update(concordancia.etiquetas())
        datos.update(etiquetas_profesionales(self.profesionales))
        datos.update({k: v for k, v in self.extras.items() if k})
        return datos

    # --- Hoja de datos ----------------------------------------------------

    def secciones_hoja_datos(self) -> list[tuple[str, list[tuple[str, str]]]]:
        """Definición del cuadro: (sección, [(rótulo, etiqueta)])."""
        return [
            ("Identificación del acto", [
                ("Resolución No.", "resolucion_numero"),
                ("Fecha", "fecha_larga"),
                ("Radicación No.", "radicado"),
                ("Fecha de radicación", "fecha_radicado_larga"),
                ("Expediente No.", "expediente"),
                ("Legal y debida forma", "fecha_debida_forma_larga"),
                ("Trámite", "tramite_completo"),
                ("Destinación", "destinacion"),
                ("Sentido de la decisión", "sentido"),
            ]),
            ("Titulares", [
                ("Titular(es)", "nombres"),
                ("Documento(s)", "documentos"),
                ("Calidad", "calidad"),
                ("Apoderado", "apoderado_nombre"),
                ("Documento del apoderado", "apoderado_documento"),
            ]),
            ("Predio", [
                ("Dirección", "direccion"),
                ("Barrio", "barrio"),
                ("Matrícula inmobiliaria", "matricula"),
                ("Ficha catastral", "ficha_catastral"),
                ("Estrato", "estrato"),
                ("Tratamiento urbanístico", "tratamiento_urbanistico"),
                ("Uso principal", "uso_principal"),
                ("Amenaza y riesgo", "amenaza_riesgo"),
            ]),
            ("Proyecto", [
                ("Área del lote", "area_lote"),
                ("Área construida", "area_construida"),
                ("Área a demoler", "area_demoler"),
                ("Pisos", "pisos_cifra"),
                ("Cubierta", "cubierta"),
                ("Índice de construcción (perm./prop.)",
                 "indice_construccion_permitido"),
                ("Índice de ocupación (perm./prop.)",
                 "indice_ocupacion_permitido"),
                ("Parqueaderos", "parqueaderos"),
            ]),
            ("Profesionales", [
                ("Proyectista", "proyectista_nombre"),
                ("Matrícula proyectista", "proyectista_matricula"),
                ("Diseñador estructural", "estructural_nombre"),
                ("Revisor independiente", "revisor_independiente_nombre"),
                ("Estudio de suelos", "suelos_nombre"),
                ("Constructor responsable", "constructor_nombre"),
                ("Matrícula constructor", "constructor_matricula"),
            ]),
            ("Expensas e impuestos", [
                ("Oficio de viabilidad", "viabilidad_oficio"),
                ("Certificado IDU", "idu_certificado"),
                ("Valor IDU", "idu_valor"),
                ("Factura", "factura_numero"),
            ]),
            ("Trámite y planos", [
                ("Acta de observaciones", "acta_observaciones_oficio"),
                ("Respuesta a observaciones", "respuesta_observaciones_oficio"),
                ("Auto No.", "auto_numero"),
                ("Planos arquitectónicos", "planos_arquitectonicos"),
                ("Planos estructurales", "planos_estructurales"),
                ("Tomos de memorias", "tomos_memorias"),
                ("Tomos de estudio de suelos", "tomos_suelos"),
            ]),
            ("Cierre", [
                ("Firma", "curador"),
                ("Tratamiento", "curador_tratamiento"),
                ("Notificado", "notificado_nombre"),
                ("Sustanciador(a)", "sustanciador"),
                ("Proyectó", "sustanciador_iniciales"),
            ]),
        ]

    def subtitulo_hoja_datos(self) -> str:
        partes = [self.despacho.nombre_curaduria]
        if self.expediente:
            partes.append(f"Expediente {self.expediente}")
        if self.fecha:
            partes.append(fechas.fecha_larga(self.fecha))
        return " — ".join(partes)

    def nombre_archivo(self, sufijo: str = "") -> str:
        numero = (self.numero or "sin-numero").replace("/", "-").replace(" ", "")
        fecha = (fechas.fecha_corta(self.fecha).replace("/", "-")
                 if self.fecha else "sin-fecha")
        base = f"Resolucion_{numero}_{fecha}"
        return f"{base}{('_' + sufijo) if sufijo else ''}.docx"


def _a_numero(texto: str) -> float | None:
    """Lee un índice escrito como "0,70", "70%" o "2.5"."""
    if texto is None:
        return None
    limpio = str(texto).strip().replace("%", "").replace(",", ".")
    if not limpio:
        return None
    try:
        return float(limpio)
    except ValueError:
        return None
