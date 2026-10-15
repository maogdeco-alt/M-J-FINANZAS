"""Conversión de números a letras en español, para redacción jurídica.

En las resoluciones los valores se escriben en letras seguidos de la cifra
entre paréntesis: "ciento veinte metros cuadrados (120,00 m2)".
"""

from __future__ import annotations

UNIDADES = (
    "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
    "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis",
    "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno",
    "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis",
    "veintisiete", "veintiocho", "veintinueve",
)

DECENAS = {
    3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta",
    7: "setenta", 8: "ochenta", 9: "noventa",
}

CENTENAS = {
    1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos",
    5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos",
    9: "novecientos",
}


def _menor_cien(n: int) -> str:
    if n < 30:
        return UNIDADES[n]
    decena, unidad = divmod(n, 10)
    if unidad == 0:
        return DECENAS[decena]
    return f"{DECENAS[decena]} y {UNIDADES[unidad]}"


def _menor_mil(n: int) -> str:
    if n < 100:
        return _menor_cien(n)
    centena, resto = divmod(n, 100)
    if n == 100:
        return "cien"
    if resto == 0:
        return CENTENAS[centena]
    return f"{CENTENAS[centena]} {_menor_cien(resto)}"


def _miles(n: int) -> str:
    miles, resto = divmod(n, 1000)
    if miles == 0:
        return _menor_mil(resto)
    prefijo = "mil" if miles == 1 else f"{_menor_mil(miles)} mil"
    if resto == 0:
        return prefijo
    return f"{prefijo} {_menor_mil(resto)}"


def entero_a_letras(n: int) -> str:
    """Devuelve el entero escrito en letras (0 a 999.999.999)."""
    if n < 0:
        return f"menos {entero_a_letras(-n)}"
    if n < 1_000_000:
        return _miles(n)
    if n >= 1_000_000_000:
        raise ValueError("Valor fuera del rango soportado (máx. 999.999.999)")
    millones, resto = divmod(n, 1_000_000)
    prefijo = "un millón" if millones == 1 else f"{_miles(millones)} millones"
    if resto == 0:
        return prefijo
    return f"{prefijo} {_miles(resto)}"


def concordar_uno(texto: str, genero: str) -> str:
    """Ajusta "uno"/"veintiuno" a femenino o apócope cuando acompaña un nombre.

    "veintiún metros", "veintiuna hectáreas".
    """
    if genero == "F":
        if texto.endswith("veintiuno"):
            return texto[: -len("veintiuno")] + "veintiuna"
        if texto.endswith("uno"):
            return texto[: -len("uno")] + "una"
        return texto
    if texto.endswith("veintiuno"):
        return texto[: -len("veintiuno")] + "veintiún"
    if texto.endswith(" y uno"):
        return texto[: -len(" y uno")] + " y un"
    if texto == "uno":
        return "un"
    return texto


def decimal_a_letras(valor: float, genero: str = "M", decimales: int = 2) -> str:
    """Convierte un decimal a letras: 120.5 -> "ciento veinte con cincuenta".

    Pensado para áreas y índices, donde la parte decimal se lee como centésimas.
    """
    negativo = valor < 0
    valor = abs(round(float(valor), decimales))
    entero = int(valor)
    frac = int(round((valor - entero) * (10 ** decimales)))
    if frac >= 10 ** decimales:  # el redondeo desbordó a la unidad siguiente
        entero += 1
        frac = 0
    letras = concordar_uno(entero_a_letras(entero), genero)
    if frac:
        letras = f"{letras} con {entero_a_letras(frac)}"
    return f"menos {letras}" if negativo else letras


def formato_cifra(valor: float, decimales: int = 2) -> str:
    """Formatea con punto de miles y coma decimal (convención colombiana)."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


def formato_entero(valor: int) -> str:
    return f"{int(valor):,}".replace(",", ".")


def en_letras_y_cifra(valor: float, unidad: str = "", genero: str = "M",
                      decimales: int = 2) -> str:
    """"ciento veinte con cincuenta metros cuadrados (120,50 m2)"."""
    letras = decimal_a_letras(valor, genero=genero, decimales=decimales)
    cifra = formato_cifra(valor, decimales)
    unidad_txt = f" {unidad}".rstrip()
    return f"{letras}{unidad_txt} ({cifra}{unidad_txt})"
