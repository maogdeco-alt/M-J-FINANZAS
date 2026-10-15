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
class EstadoCampo:
    """Un campo del formulario y si ya quedó listo."""

    nombre: str
    listo: bool
    detalle: str = ""
    critico: bool = True      # si no es crítico, se puede generar sin él

    @property
    def icono(self) -> str:
        if self.listo:
            return "✓"
        return "✕" if self.critico else "○"


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


# Quién radica la solicitud. Puede o no ser el propietario, y de eso depende
# toda la frase del considerando principal.
RESPONSABLES = {
    "titular": "El titular (propietario) radica directamente",
    "apoderado": "Un apoderado con poder especial",
    "representante": "El representante legal de una persona jurídica",
}


@dataclass
class Responsable:
    """Quién radica: el propio titular, un apoderado o un representante."""

    tipo: str = "titular"
    nombre: str = ""
    genero: str = "M"
    documento: str = ""

    @property
    def propio(self) -> bool:
        """El titular radica por sí mismo: no hay datos extra que pedir."""
        return self.tipo == "titular"

    @property
    def calidad(self) -> str:
        return {"apoderado": "apoderado del trámite",
                "representante": "representante legal"}.get(self.tipo, "")

    def frase(self) -> str:
        """"el señor X, identificado con CC. No. N, en calidad de apoderado…"."""
        if self.propio or not self.nombre.strip():
            return ""
        participio = "identificada" if self.genero == "F" else "identificado"
        articulo = "la" if self.genero == "F" else "el"
        tratamiento = "señora" if self.genero == "F" else "señor"
        documento = formato_documento(self.documento)
        texto = f"{articulo} {tratamiento} {self.nombre}"
        if documento:
            texto += f", {participio} con CC. No. {documento}"
        calidad = self.calidad
        if self.tipo == "representante":
            calidad = f"representante legal {{de_titular}}"
        return f"{texto}, en calidad de {calidad}"


# Nombre anterior, para no romper código que ya lo usaba.
Apoderado = Responsable


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
    responsable: Responsable = field(default_factory=Responsable)
    inmueble: Inmueble = field(default_factory=Inmueble)
    profesionales: list[Profesional] = field(default_factory=list)
    actuaciones: Actuaciones = field(default_factory=Actuaciones)
    notificacion: Notificacion = field(default_factory=Notificacion)
    vigencia_meses: int = 36
    prorroga_meses: int = 12
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
        """Quién radica la solicitud, con su calidad.

        Si radica el propio titular, se nombra a los titulares con su calidad;
        si radica un apoderado o un representante legal, se nombra a esa
        persona y se deja constancia de a quién representa.
        """
        concordancia = self.concordancia
        propios = (f"{concordancia.identificacion_completa()}, "
                   f"{concordancia.frase_calidad()}")
        if self.responsable.propio or not self.responsable.nombre.strip():
            return propios
        frase = self.responsable.frase()
        if self.responsable.tipo == "representante":
            frase = frase.replace("{de_titular}",
                                  f"de {concordancia.nombres()}")
        return frase

    def frase_responsable_sola(self) -> str:
        """El responsable sin la mención de a quién representa."""
        frase = self.responsable.frase()
        if not frase:
            return ""
        return frase.replace(" {de_titular}", "").replace("{de_titular}", "")

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

        if not self.responsable.propio:
            if not self.responsable.nombre.strip():
                problemas.append(
                    f"Indicó que radica {self.responsable.calidad}, pero falta "
                    "su nombre.")
            if not self.responsable.documento.strip():
                problemas.append(
                    f"Falta el documento de quien radica "
                    f"({self.responsable.nombre or 'sin nombre'}).")
        if self.responsable.tipo == "representante" and not any(
                t.es_juridica for t in self.titulares):
            problemas.append(
                "Indicó representante legal, pero ningún titular es persona "
                "jurídica (NIT).")

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
        if (self.solicitud.tramite_id == "construccion"
                and self.sentido == "otorgar"):
            roles = {p.rol for p in self.profesionales if p.nombre.strip()}
            faltan = [nombre for rol, nombre in
                      (("proyectista", "proyectista arquitectónico"),
                       ("constructor", "constructor responsable"))
                      if rol not in roles]
            if faltan:
                avisos.append(
                    "Sin " + unir_con_y(faltan) + ": el artículo resolutivo "
                    "los menciona, así que saldrán con raya para completarlos "
                    "en Word. Si los registra, el título y el participio "
                    "concuerdan solos.")
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
            "responsable_tipo": RESPONSABLES.get(self.responsable.tipo, ""),
            "responsable_nombre": self.responsable.nombre,
            "responsable_calidad": self.responsable.calidad,
            "apoderado_nombre": self.responsable.nombre,
            "apoderado_documento": formato_documento(
                self.responsable.documento),
            "apoderado_identificacion": self.frase_responsable_sola(),
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

    # --- Avance del formulario -------------------------------------------

    def estado_campos(self) -> list["EstadoCampo"]:
        """Los campos del Nivel 1, uno por uno, con su estado.

        Es lo que alimenta el indicador de avance: la sustanciadora ve en todo
        momento qué le falta, sin tener que llegar al final para descubrirlo.
        Los campos que el trámite no necesita no se cuentan.
        """
        inmueble = self.inmueble
        solicitud = self.solicitud
        tramite = solicitud.tramite
        modalidades = set(solicitud.modalidades_ids)

        campos: list[EstadoCampo] = [
            EstadoCampo("Tipo de trámite", bool(tramite.nombre),
                        tramite.nombre),
        ]

        if tramite.modalidades:
            campos.append(EstadoCampo(
                "Modalidad", bool(solicitud.modalidades_ids),
                solicitud.frase_modalidades() or "sin elegir"))

        campos += [
            EstadoCampo("Destinación / uso", bool(solicitud.usos_ids),
                        solicitud.frase_usos() or "sin elegir"),
            EstadoCampo("Resolución y fecha",
                        bool(self.numero.strip()) and self.fecha is not None,
                        self.numero or "sin número"),
            EstadoCampo("Radicado y fecha",
                        bool(self.radicado.strip())
                        and self.fecha_radicado is not None,
                        self.radicado or "sin radicado"),
            EstadoCampo("Expediente", bool(self.expediente),
                        self.expediente or "falta el consecutivo"),
            EstadoCampo("Titulares", self._titulares_completos(),
                        self._detalle_titulares()),
            EstadoCampo("Quién radica", self._responsable_completo(),
                        self._detalle_responsable()),
        ]

        if tramite.requiere_predio:
            campos += [
                EstadoCampo("Matrícula inmobiliaria",
                            bool(inmueble.matricula_inmobiliaria.strip()),
                            inmueble.matricula_inmobiliaria or "sin matrícula"),
                EstadoCampo("Ficha catastral",
                            bool(inmueble.ficha_catastral.strip()),
                            inmueble.ficha_catastral or "sin ficha",
                            critico=False),
                EstadoCampo("Dirección", bool(inmueble.direccion.strip()),
                            inmueble.direccion or "sin dirección"),
            ]

        if tramite.id in ("construccion", "reconocimiento"):
            campos.append(EstadoCampo(
                "Pisos y cubierta", bool(inmueble.pisos),
                f"{inmueble.pisos} piso(s), cubierta en {inmueble.cubierta}"
                if inmueble.pisos else "sin pisos"))

        # Áreas: solo las que la modalidad elegida exige.
        if modalidades & {"obra_nueva", "ampliacion", "adecuacion",
                          "modificacion"} or tramite.id == "reconocimiento":
            campos.append(EstadoCampo(
                "Área del lote y construida",
                bool(inmueble.area_lote) and bool(inmueble.area_construida),
                f"lote {formato_cifra(inmueble.area_lote)} m² · construida "
                f"{formato_cifra(inmueble.area_construida)} m²"))
        if modalidades & {"demolicion_total", "demolicion_parcial"}:
            campos.append(EstadoCampo(
                "Área a demoler", bool(inmueble.area_demoler),
                f"{formato_cifra(inmueble.area_demoler)} m²"
                if inmueble.area_demoler else "sin área"))

        # Condicionales: solo cuando el caso los pide.
        if modalidades & {"obra_nueva", "ampliacion"}:
            campos.append(EstadoCampo(
                "Índices (permitido y propuesto)",
                bool(inmueble.indice_ocupacion_permitido.strip())
                and bool(inmueble.indice_ocupacion_propuesto.strip()),
                "ocupación "
                f"{inmueble.indice_ocupacion_propuesto or '—'} de "
                f"{inmueble.indice_ocupacion_permitido or '—'}",
                critico=False))
        if solicitud.vivienda_interes:
            campos.append(EstadoCampo(
                f"Estrato (proyecto {solicitud.vivienda_interes})",
                bool(str(inmueble.estrato).strip()),
                str(inmueble.estrato) or "sin estrato", critico=False))

        return campos

    def _titulares_completos(self) -> bool:
        return bool(self.titulares) and all(
            t.nombre.strip() and t.numero_documento.strip()
            for t in self.titulares)

    def _detalle_titulares(self) -> str:
        if not self.titulares:
            return "sin titulares"
        incompletos = [t for t in self.titulares
                       if not t.nombre.strip() or not t.numero_documento.strip()]
        if incompletos:
            return f"{len(incompletos)} sin completar"
        concordancia = self.concordancia
        return (f"{len(self.titulares)}: "
                f"{concordancia.palabra('articulo')} "
                f"{concordancia.palabra('propietario')}")

    def _responsable_completo(self) -> bool:
        if self.responsable.propio:
            return self._titulares_completos()
        return bool(self.responsable.nombre.strip()
                    and self.responsable.documento.strip())

    def _detalle_responsable(self) -> str:
        if self.responsable.propio:
            return "el propio titular"
        if not self.responsable.nombre.strip():
            return f"falta el {self.responsable.calidad}"
        return f"{self.responsable.nombre} ({self.responsable.calidad})"

    @property
    def avance(self) -> tuple[int, int]:
        """(campos listos, campos en total) del Nivel 1."""
        campos = self.estado_campos()
        return sum(1 for c in campos if c.listo), len(campos)

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
