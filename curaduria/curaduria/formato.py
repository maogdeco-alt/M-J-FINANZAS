"""Normalización de los datos que digita la sustanciadora.

La precisión no se consigue pidiendo cuidado: se consigue aceptando el dato
como venga y dejándolo en la forma correcta. Si alguien escribe la matrícula
como "350250605", la app la guarda como "350-250605"; si escribe un nombre en
minúscula, lo pasa a mayúscula como van en las resoluciones.

Cada función devuelve un `Revision`: el valor ya normalizado, si quedó bien, y
un mensaje para mostrar al lado del campo. Nunca lanza excepciones: un dato a
medio escribir no debe romper el formulario.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .gramatica import formato_documento


@dataclass
class Revision:
    valor: str
    estado: str = "vacio"      # vacio | bien | duda | mal
    mensaje: str = ""

    @property
    def bien(self) -> bool:
        return self.estado in ("bien", "vacio")

    @property
    def icono(self) -> str:
        return {"vacio": "", "bien": "✓", "duda": "⚠️", "mal": "✕"}[self.estado]


def _solo_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto or "")


# --- Matrícula inmobiliaria -------------------------------------------------

def normalizar_matricula(texto: str) -> Revision:
    """Círculo de registro (3 dígitos) + número: "350250605" -> "350-250605"."""
    bruto = (texto or "").strip()
    if not bruto:
        return Revision("")
    digitos = _solo_digitos(bruto)
    if not digitos:
        return Revision(bruto, "mal", "La matrícula son dígitos: 350-250605.")
    if len(digitos) < 7:
        return Revision(bruto, "duda",
                        f"Van {len(digitos)} dígitos; una matrícula tiene al "
                        "menos 7 (círculo de 3 + número).")
    if len(digitos) > 11:
        return Revision(bruto, "mal",
                        f"{len(digitos)} dígitos es demasiado para una "
                        "matrícula. Revise si se repitió alguno.")
    normalizada = f"{digitos[:3]}-{digitos[3:]}"
    return Revision(normalizada, "bien", f"Círculo {digitos[:3]}")


# --- Ficha catastral -------------------------------------------------------

def normalizar_ficha_catastral(texto: str) -> Revision:
    """Quince dígitos en cinco grupos: 01-09-1014-0013-000."""
    bruto = (texto or "").strip()
    if not bruto:
        return Revision("")
    digitos = _solo_digitos(bruto)
    if not digitos:
        return Revision(bruto, "mal",
                        "La ficha son dígitos: 01-09-1014-0013-000.")
    if len(digitos) == 15:
        normalizada = (f"{digitos[:2]}-{digitos[2:4]}-{digitos[4:8]}-"
                       f"{digitos[8:12]}-{digitos[12:]}")
        return Revision(normalizada, "bien", "")
    faltan = 15 - len(digitos)
    if faltan > 0:
        return Revision(bruto, "duda",
                        f"Van {len(digitos)} de 15 dígitos (faltan {faltan}).")
    return Revision(bruto, "mal",
                    f"{len(digitos)} dígitos: la ficha tiene exactamente 15.")


# --- Documentos de identidad ----------------------------------------------

def normalizar_documento(texto: str, tipo: str = "CC") -> Revision:
    """Puntos de miles, y el dígito de verificación del NIT se conserva."""
    bruto = (texto or "").strip()
    if not bruto:
        return Revision("")
    if tipo in ("PAS", "PEP"):      # pueden traer letras
        return Revision(bruto.upper(), "bien", "")

    cuerpo, _, verificacion = bruto.partition("-")
    digitos = _solo_digitos(cuerpo)
    if not digitos:
        return Revision(bruto, "mal", "El documento son dígitos.")
    normalizado = formato_documento(bruto)

    if tipo == "NIT":
        if not verificacion:
            return Revision(normalizado, "duda",
                            "Al NIT le falta el dígito de verificación "
                            "(900123456-1).")
        return Revision(normalizado, "bien", "")
    if len(digitos) < 5:
        return Revision(normalizado, "duda",
                        f"Solo {len(digitos)} dígitos: ¿está completa?")
    if len(digitos) > 11:
        return Revision(normalizado, "mal",
                        f"{len(digitos)} dígitos es demasiado para una cédula.")
    return Revision(normalizado, "bien", "")


# --- Nombres ---------------------------------------------------------------

def normalizar_nombre(texto: str, mayuscula: bool = True) -> Revision:
    """Quita espacios de más y pasa a mayúscula, como van en las resoluciones."""
    bruto = re.sub(r"\s+", " ", (texto or "").strip())
    if not bruto:
        return Revision("")
    valor = bruto.upper() if mayuscula else bruto

    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", valor)
                         if unicodedata.category(c) != "Mn")
    if re.search(r"\d", valor):
        return Revision(valor, "duda", "El nombre tiene números.")
    if len(sin_tildes.split()) < 2:
        return Revision(valor, "duda", "Falta el apellido.")
    return Revision(valor, "bien", "")


# --- Radicado y consecutivos ----------------------------------------------

def normalizar_radicado(texto: str) -> Revision:
    """El radicado de correspondencia: dígitos, sin espacios."""
    bruto = re.sub(r"\s+", "", (texto or "").strip())
    if not bruto:
        return Revision("")
    if not re.fullmatch(r"[\d.\-]+", bruto):
        return Revision(bruto, "duda",
                        "El radicado suele ser solo números: 2600789.")
    return Revision(bruto.replace(".", ""), "bien", "")


def normalizar_consecutivo(texto: str) -> Revision:
    """El consecutivo del expediente: hasta cuatro dígitos."""
    bruto = (texto or "").strip()
    if not bruto:
        return Revision("")
    digitos = _solo_digitos(bruto)
    if not digitos:
        return Revision(bruto, "mal", "El consecutivo son dígitos: 54.")
    if len(digitos) > 4:
        return Revision(digitos, "mal",
                        "El consecutivo del expediente son máximo 4 dígitos.")
    return Revision(digitos.zfill(4), "bien", "")


# --- Direcciones -----------------------------------------------------------

ABREVIATURAS = {
    r"\bcl\b": "Calle", r"\bcll\b": "Calle", r"\bcalle\b": "Calle",
    r"\bcra\b": "Carrera", r"\bkra\b": "Carrera", r"\bkr\b": "Carrera",
    r"\bcarrera\b": "Carrera", r"\bav\b": "Avenida", r"\bavenida\b": "Avenida",
    r"\bdg\b": "Diagonal", r"\btv\b": "Transversal", r"\bmz\b": "Manzana",
}


CONECTORES = {"de", "del", "la", "las", "el", "los", "y", "no"}


def _capitalizar_direccion(texto: str) -> str:
    """Pone el nombre de la vía y el barrio en mayúscula inicial.

    Deja los números, el "No." y los conectores como están: "Avenida Ambalá
    No. 42 - 15 Barrio Córdoba Parte Baja".
    """
    palabras = texto.split(" ")
    salida = []
    for indice, palabra in enumerate(palabras):
        if not palabra or not palabra[0].isalpha() or palabra == "No.":
            salida.append(palabra)
            continue
        if palabra.lower() in CONECTORES and indice > 0:
            salida.append(palabra.lower())
            continue
        salida.append(palabra[0].upper() + palabra[1:].lower()
                      if palabra.isupper() or palabra.islower() else palabra)
    return " ".join(salida)


def normalizar_direccion(texto: str) -> Revision:
    """Desarma las abreviaturas de vía: "cra 2 sur 28-57" -> "Carrera 2 Sur…"."""
    bruto = re.sub(r"\s+", " ", (texto or "").strip())
    if not bruto:
        return Revision("")
    valor = bruto
    for patron, reemplazo in ABREVIATURAS.items():
        valor = re.sub(patron, reemplazo, valor, flags=re.IGNORECASE)
    valor = re.sub(r"\bno\.?\s*", "No. ", valor, flags=re.IGNORECASE)
    valor = re.sub(r"\s+", " ", valor).strip()
    valor = _capitalizar_direccion(valor)
    if not re.search(r"\d", valor):
        return Revision(valor, "duda", "La dirección no tiene números.")
    return Revision(valor, "bien", "")


# --- Índices ---------------------------------------------------------------

def normalizar_indice(texto: str) -> Revision:
    """Acepta "0,70", "70%" o "2.5" y deja la coma decimal."""
    bruto = (texto or "").strip()
    if not bruto:
        return Revision("")
    porcentaje = bruto.endswith("%")
    limpio = bruto.replace("%", "").replace(",", ".").strip()
    try:
        valor = float(limpio)
    except ValueError:
        return Revision(bruto, "mal", "Escriba un número: 0,70 o 70%.")
    if porcentaje:
        return Revision(f"{valor:g}%".replace(".", ","), "bien", "")
    return Revision(f"{valor:g}".replace(".", ","), "bien", "")
