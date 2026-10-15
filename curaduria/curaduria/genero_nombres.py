"""Sugerencia de género a partir del nombre de pila.

Es solo una sugerencia editable: el operador siempre puede corregirla en el
formulario. Primero se consulta una lista de nombres frecuentes y, si no está,
se aplica la terminación. Los nombres compuestos se resuelven por el primero
que se reconozca ("JOSÉ MARÍA" -> masculino).
"""

from __future__ import annotations

import unicodedata

FEMENINOS = {
    "maria", "ana", "luz", "rosa", "carmen", "gloria", "martha", "marta",
    "claudia", "sandra", "diana", "paola", "angela", "patricia", "beatriz",
    "esperanza", "stella", "yolanda", "nancy", "mercedes", "ines", "pilar",
    "soledad", "isabel", "juana", "laura", "andrea", "catalina", "camila",
    "valentina", "daniela", "natalia", "carolina", "lorena", "mariana",
    "alejandra", "adriana", "liliana", "viviana", "johana", "yeimy", "leidy",
    "nubia", "amparo", "consuelo", "dolores", "elvira", "flor", "judith",
    "magnolia", "marlene", "miriam", "myriam", "olga", "ruth", "sonia",
    "teresa", "victoria", "virginia", "zoraida", "edith", "deisy", "yudi",
    "milena", "fanny", "cecilia", "dora", "aura", "blanca", "clara", "elsa",
    "emilse", "gladys", "lucia", "luisa", "nelly", "noemi", "piedad", "sara",
    "silvia", "yenny", "astrid", "carol", "ingrid", "karen", "lina", "paula",
    "tatiana", "veronica", "wendy", "ximena", "yamile", "zulma", "nidia",
}

MASCULINOS = {
    "jose", "juan", "luis", "carlos", "jorge", "pedro", "andres", "miguel",
    "fernando", "ricardo", "alberto", "gustavo", "hernan", "german", "oscar",
    "javier", "rafael", "mauricio", "alvaro", "diego", "camilo", "santiago",
    "sebastian", "david", "daniel", "felipe", "nicolas", "mateo", "samuel",
    "esteban", "julian", "cesar", "edgar", "hector", "hugo", "ivan", "manuel",
    "marco", "mario", "martin", "nelson", "omar", "pablo", "ramiro", "raul",
    "roberto", "rodrigo", "ruben", "sergio", "victor", "wilson", "yesid",
    "arturo", "bernardo", "cristian", "efrain", "eduardo", "elkin", "emilio",
    "enrique", "ernesto", "fabian", "fabio", "francisco", "gabriel", "gerardo",
    "gilberto", "guillermo", "harold", "henry", "jaime", "jairo", "jhon",
    "john", "leonardo", "libardo", "lucas", "orlando", "wilmar", "jesus",
    "alejandro", "alexander", "antonio", "armando", "augusto", "benjamin",
}

# Terminaciones que, en la práctica, no siguen la regla -o/-a.
EXCEPCIONES_SUFIJO = {
    "andrea": "M",   # en Colombia suele ser femenino, pero "Andrés" no aplica
}


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


def sugerir_genero(nombre_completo: str, por_defecto: str = "M") -> str:
    """Devuelve "M" o "F" como sugerencia para el nombre dado."""
    if not nombre_completo or not nombre_completo.strip():
        return por_defecto
    partes = [_normalizar(p) for p in nombre_completo.split() if p.strip()]
    for parte in partes:
        if parte in FEMENINOS:
            return "F"
        if parte in MASCULINOS:
            return "M"
    primera = partes[0] if partes else ""
    if primera in EXCEPCIONES_SUFIJO:
        return EXCEPCIONES_SUFIJO[primera]
    if primera.endswith(("a", "ia", "ina", "ela")):
        return "F"
    if primera.endswith(("o", "os", "el", "an", "in", "ar", "er", "or")):
        return "M"
    return por_defecto
