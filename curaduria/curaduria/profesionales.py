"""Profesionales que intervienen en el proyecto.

Cada uno aparece en la resolución con su título, nombre, documento y matrícula
profesional, y el título y el participio tienen que concordar con el sexo de la
persona ("la Arquitecta X, identificada con…"). Es justamente donde más se
cuelan errores al copiar párrafos de una resolución anterior.
"""

from __future__ import annotations

from dataclasses import dataclass

from .gramatica import (FEMENINO, MASCULINO, SINGULAR, flexionar,
                        formato_documento, unir_con_y)

# id -> (título masculino, título femenino, cómo se nombra el rol en el texto)
ROLES: dict[str, tuple[str, str, str]] = {
    "proyectista": ("Arquitecto", "Arquitecta", "proyecto arquitectónico"),
    "estructural": ("Ingeniero Civil", "Ingeniera Civil",
                    "diseño estructural y de elementos no estructurales"),
    "revisor_independiente": ("Ingeniero Civil", "Ingeniera Civil",
                              "revisión independiente del diseño estructural"),
    "suelos": ("Ingeniero Civil", "Ingeniera Civil", "estudio de suelos"),
    "geotecnia": ("Ingeniero Geotecnista", "Ingeniera Geotecnista",
                  "estudio geotécnico"),
    "geologo": ("Ingeniero Geólogo", "Ingeniera Geóloga",
                "estudio geológico de amenaza y riesgo"),
    "topografo": ("Topógrafo", "Topógrafa", "levantamiento topográfico"),
    "constructor": ("Arquitecto", "Arquitecta", "construcción de la obra"),
    "supervisor": ("Ingeniero Civil", "Ingeniera Civil",
                   "supervisión técnica independiente"),
    "electrico": ("Ingeniero Electricista", "Ingeniera Electricista",
                  "diseño eléctrico"),
    "hidraulico": ("Ingeniero Civil", "Ingeniera Civil",
                   "diseño hidrosanitario"),
}

ETIQUETA_ROL = {
    "proyectista": "Proyectista arquitectónico",
    "estructural": "Diseñador estructural",
    "revisor_independiente": "Revisor independiente del diseño estructural",
    "suelos": "Estudio de suelos",
    "geotecnia": "Geotecnia",
    "geologo": "Geología (amenaza y riesgo)",
    "topografo": "Topografía",
    "constructor": "Constructor responsable",
    "supervisor": "Supervisor técnico independiente",
    "electrico": "Diseño eléctrico",
    "hidraulico": "Diseño hidrosanitario",
}


@dataclass
class Profesional:
    rol: str
    nombre: str
    genero: str = MASCULINO
    documento: str = ""
    matricula: str = ""
    titulo_personalizado: str = ""

    @property
    def titulo(self) -> str:
        if self.titulo_personalizado:
            return self.titulo_personalizado
        masculino, femenino, _ = ROLES.get(
            self.rol, ("Profesional", "Profesional", ""))
        return femenino if self.genero == FEMENINO else masculino

    @property
    def articulo(self) -> str:
        return flexionar("articulo", self.genero, SINGULAR)

    def frase(self) -> str:
        """"el Arquitecto JUAN PÉREZ, identificado con CC No. 79.000.000 y con
        Matrícula Profesional No. 25700-55387"."""
        participio = flexionar("identificado", self.genero, SINGULAR)
        partes = [f"{self.articulo} {self.titulo} {self.nombre}"]
        if self.documento:
            partes.append(
                f"{participio} con CC No. {formato_documento(self.documento)}")
        if self.matricula:
            partes.append(f"con Matrícula Profesional No. {self.matricula}")
        frase = ", ".join(partes[:2])
        if len(partes) > 2:
            frase += f" y {partes[2]}"
        return frase

    def frase_sin_articulo(self) -> str:
        return self.frase().split(" ", 1)[1] if self.frase() else ""


def etiquetas(profesionales: list[Profesional]) -> dict[str, str]:
    """Etiquetas por rol: {{proyectista}}, {{proyectista_nombre}}, …

    Si hay varios profesionales con el mismo rol (un grupo interdisciplinario,
    por ejemplo), se enumeran en una sola frase.
    """
    datos: dict[str, str] = {}
    por_rol: dict[str, list[Profesional]] = {}
    for profesional in profesionales:
        if profesional.nombre.strip():
            por_rol.setdefault(profesional.rol, []).append(profesional)

    for rol in ROLES:
        grupo = por_rol.get(rol, [])
        datos[rol] = unir_con_y([p.frase() for p in grupo])
        datos[f"{rol}_nombre"] = unir_con_y([p.nombre for p in grupo])
        datos[f"{rol}_titulo"] = grupo[0].titulo if grupo else ""
        datos[f"{rol}_documento"] = unir_con_y(
            [formato_documento(p.documento) for p in grupo])
        datos[f"{rol}_matricula"] = unir_con_y([p.matricula for p in grupo])
    return datos
