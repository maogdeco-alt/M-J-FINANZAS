"""Catálogo de trámites a cargo del curador urbano.

Estructura conforme al Decreto Único Nacional 1077 de 2015 y la Ley 388 de
1997: licencias urbanísticas con sus modalidades, reconocimiento de la
existencia de edificaciones y otras actuaciones relacionadas (Art.
2.2.6.1.3.1).

La distinción importa porque de ella dependen tres cosas: el nombre del
trámite tal como se escribe en el acto, qué modalidades pueden combinarse, y
qué bloques de considerandos tienen sentido para el caso.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .gramatica import unir_con_y


@dataclass(frozen=True)
class Modalidad:
    id: str
    nombre: str               # como se escribe en el acto, en mayúsculas
    combinable: bool = True   # puede concurrir con otras modalidades
    nota: str = ""


@dataclass(frozen=True)
class Tramite:
    id: str
    nombre: str                           # "Licencia de Construcción"
    grupo: str                            # licencia | reconocimiento | actuacion
    genero: str = "F"                     # "la licencia", "el reconocimiento"
    modalidades: tuple[Modalidad, ...] = ()
    modalidades_multiples: bool = False   # admite varias a la vez
    requiere_predio: bool = True
    nota: str = ""

    @property
    def nombre_acto(self) -> str:
        """Como se nombra en el artículo resolutivo: "Licencia de CONSTRUCCIÓN"."""
        partes = self.nombre.split(" de ", 1)
        if len(partes) == 2:
            return f"{partes[0]} de {partes[1].upper()}"
        return self.nombre.upper()


# --- Licencia de construcción: las nueve modalidades ------------------------
# Art. 2.2.6.1.1.7 del Decreto 1077 de 2015. Son independientes o combinables.
MODALIDADES_CONSTRUCCION = (
    Modalidad("obra_nueva", "OBRA NUEVA"),
    Modalidad("ampliacion", "AMPLIACIÓN"),
    Modalidad("adecuacion", "ADECUACIÓN"),
    Modalidad("modificacion", "MODIFICACIÓN"),
    Modalidad("restauracion", "RESTAURACIÓN"),
    Modalidad("reforzamiento", "REFORZAMIENTO ESTRUCTURAL"),
    Modalidad("demolicion_total", "DEMOLICIÓN TOTAL"),
    Modalidad("demolicion_parcial", "DEMOLICIÓN PARCIAL"),
    Modalidad("reconstruccion", "RECONSTRUCCIÓN"),
    Modalidad("cerramiento", "CERRAMIENTO"),
)

MODALIDADES_URBANIZACION = (
    Modalidad("desarrollo", "DESARROLLO", combinable=False),
    Modalidad("saneamiento", "SANEAMIENTO", combinable=False),
    Modalidad("reurbanizacion", "REURBANIZACIÓN", combinable=False),
)

MODALIDADES_SUBDIVISION = (
    Modalidad("subdivision_rustica", "SUBDIVISIÓN RÚSTICA", combinable=False,
              nota="Suelo rural."),
    Modalidad("subdivision_rural", "SUBDIVISIÓN RURAL", combinable=False),
    Modalidad("subdivision_urbana", "SUBDIVISIÓN URBANA", combinable=False),
    Modalidad("loteo", "LOTEO", combinable=False,
              nota="Suelo urbano con licencia de urbanización vigente."),
)

TRAMITES: tuple[Tramite, ...] = (
    # --- 1. Licencias urbanísticas y sus modalidades
    Tramite("construccion", "Licencia de Construcción", "licencia", "F",
            MODALIDADES_CONSTRUCCION, modalidades_multiples=True,
            nota="Las nueve modalidades son independientes o combinables."),
    Tramite("urbanizacion", "Licencia de Urbanización", "licencia", "F",
            MODALIDADES_URBANIZACION),
    Tramite("parcelacion", "Licencia de Parcelación", "licencia", "F",
            nota="Predios rurales y suburbanos."),
    Tramite("subdivision", "Licencia de Subdivisión", "licencia", "F",
            MODALIDADES_SUBDIVISION),
    Tramite("espacio_publico",
            "Licencia de Intervención y Ocupación del Espacio Público",
            "licencia", "F",
            nota="Ante el curador, únicamente con ocasión de proyectos de "
                 "urbanización."),
    # --- 2. Reconocimiento de la existencia de edificaciones
    Tramite("reconocimiento", "Reconocimiento de la Existencia de Edificaciones",
            "reconocimiento", "M",
            nota="Edificación construida sin licencia, terminada al menos cinco "
                 "(5) años antes, que cumple sismo resistencia y habitabilidad."),
    # --- 3. Otras actuaciones relacionadas (Art. 2.2.6.1.3.1)
    Tramite("ajuste_cotas", "Ajuste de Cotas y Áreas", "actuacion", "M"),
    Tramite("planos_alinderamiento", "Aprobación de los Planos de Alinderamiento",
            "actuacion", "F",
            nota="Para sometimiento al Régimen de Propiedad Horizontal."),
    Tramite("modificacion_urbanizacion",
            "Aprobación de Planos para la Modificación de Urbanizaciones Aceptadas",
            "actuacion", "F"),
    Tramite("piscinas", "Aprobación de Piscinas", "actuacion", "F",
            nota="Verificación de normas de seguridad y protección."),
    Tramite("movimiento_tierras", "Autorización para el Movimiento de Tierras",
            "actuacion", "F"),
    Tramite("concepto_norma", "Concepto de Norma Urbanística", "actuacion", "M"),
    Tramite("concepto_uso", "Concepto de Uso del Suelo", "actuacion", "M"),
    Tramite("copias_planos", "Copias Certificadas de Planos", "actuacion", "F"),
    Tramite("prorroga", "Prórroga de Licencia", "actuacion", "F",
            nota="Licencia vigente. Se solicita a más tardar treinta (30) días "
                 "hábiles antes del vencimiento."),
    Tramite("revalidacion", "Revalidación de Licencia", "actuacion", "F",
            nota="Licencia vencida hace menos de dos (2) meses, con el proyecto "
                 "en las condiciones originales."),
    Tramite("modificacion_licencia", "Modificación de Licencia Vigente",
            "actuacion", "F"),
)

POR_ID = {t.id: t for t in TRAMITES}

GRUPOS = {
    "licencia": "Licencias urbanísticas",
    "reconocimiento": "Reconocimiento de edificaciones",
    "actuacion": "Otras actuaciones relacionadas",
}


# --- Usos y destinaciones ---------------------------------------------------

@dataclass(frozen=True)
class Uso:
    id: str
    nombre: str
    categoria: str
    vivienda_interes: str = ""   # "", "VIS" o "VIP"


USOS: tuple[Uso, ...] = (
    Uso("vivienda_unifamiliar", "VIVIENDA UNIFAMILIAR", "residencial"),
    Uso("vivienda_bifamiliar", "VIVIENDA BIFAMILIAR", "residencial"),
    Uso("vivienda_trifamiliar", "VIVIENDA TRIFAMILIAR", "residencial"),
    Uso("vivienda_multifamiliar", "VIVIENDA MULTIFAMILIAR", "residencial"),
    Uso("vis_unifamiliar", "VIVIENDA DE INTERÉS SOCIAL UNIFAMILIAR",
        "residencial", "VIS"),
    Uso("vis_multifamiliar", "VIVIENDA DE INTERÉS SOCIAL MULTIFAMILIAR",
        "residencial", "VIS"),
    Uso("vip", "VIVIENDA DE INTERÉS PRIORITARIO", "residencial", "VIP"),
    Uso("comercio", "COMERCIO", "comercial"),
    Uso("comercio_especial", "COMERCIO ESPECIAL", "comercial"),
    Uso("oficinas", "OFICINAS", "comercial"),
    Uso("servicios", "SERVICIOS", "comercial"),
    Uso("institucional", "INSTITUCIONAL", "institucional"),
    Uso("educativo", "EDUCATIVO", "institucional"),
    Uso("salud", "SALUD", "institucional"),
    Uso("culto", "CULTO RELIGIOSO", "institucional"),
    Uso("industrial", "INDUSTRIAL", "industrial"),
    Uso("bodega", "BODEGA", "industrial"),
    Uso("mixto", "MIXTO (VIVIENDA Y COMERCIO)", "mixto"),
)

USOS_POR_ID = {u.id: u for u in USOS}


# --- Composición del nombre del trámite ------------------------------------

@dataclass
class Solicitud:
    """El trámite concreto: qué licencia, en qué modalidades y para qué uso."""

    tramite_id: str = "construccion"
    modalidades_ids: list[str] = field(default_factory=list)
    usos_ids: list[str] = field(default_factory=list)

    @property
    def tramite(self) -> Tramite:
        return POR_ID[self.tramite_id]

    @property
    def modalidades(self) -> list[Modalidad]:
        disponibles = {m.id: m for m in self.tramite.modalidades}
        return [disponibles[i] for i in self.modalidades_ids if i in disponibles]

    @property
    def usos(self) -> list[Uso]:
        return [USOS_POR_ID[i] for i in self.usos_ids if i in USOS_POR_ID]

    @property
    def vivienda_interes(self) -> str:
        """"VIS", "VIP" o "" según los usos elegidos."""
        marcas = {u.vivienda_interes for u in self.usos if u.vivienda_interes}
        if "VIP" in marcas:
            return "VIP"
        return "VIS" if "VIS" in marcas else ""

    def frase_modalidades(self) -> str:
        """"en las modalidades de DEMOLICIÓN TOTAL Y OBRA NUEVA"."""
        nombres = [m.nombre for m in self.modalidades]
        if not nombres:
            return ""
        if len(nombres) == 1:
            return f"en la modalidad de {nombres[0]}"
        return "en las modalidades de " + unir_con_y(nombres)

    def frase_usos(self) -> str:
        nombres = [u.nombre for u in self.usos]
        return unir_con_y(nombres)

    def nombre_completo(self) -> str:
        """"Licencia de CONSTRUCCIÓN en las modalidades de OBRA NUEVA…"."""
        partes = [self.tramite.nombre_acto, self.frase_modalidades()]
        return " ".join(p for p in partes if p)

    def errores(self) -> list[str]:
        problemas: list[str] = []
        tramite = self.tramite
        if tramite.modalidades and not self.modalidades_ids:
            problemas.append(
                f"{tramite.nombre} exige indicar la modalidad.")
        if len(self.modalidades_ids) > 1:
            if not tramite.modalidades_multiples:
                problemas.append(
                    f"{tramite.nombre} admite una sola modalidad por acto.")
            else:
                no_combinables = [m.nombre for m in self.modalidades
                                  if not m.combinable]
                if no_combinables:
                    problemas.append(
                        "No se combinan con otras modalidades: "
                        + unir_con_y(no_combinables))
        if {"demolicion_total", "demolicion_parcial"} <= set(self.modalidades_ids):
            problemas.append(
                "Demolición total y parcial son excluyentes entre sí.")
        return problemas

    def etiquetas(self) -> dict[str, str]:
        tramite = self.tramite
        return {
            "tramite": tramite.nombre,
            "tramite_acto": tramite.nombre_acto,
            "tramite_completo": self.nombre_completo(),
            "tramite_grupo": GRUPOS[tramite.grupo],
            "modalidades": self.frase_modalidades(),
            "modalidades_lista": unir_con_y([m.nombre for m in self.modalidades]),
            "destinacion": self.frase_usos(),
            "uso": self.frase_usos(),
            "vivienda_interes": self.vivienda_interes,
        }


def tramites_por_grupo() -> dict[str, list[Tramite]]:
    agrupados: dict[str, list[Tramite]] = {clave: [] for clave in GRUPOS}
    for tramite in TRAMITES:
        agrupados[tramite.grupo].append(tramite)
    return agrupados
