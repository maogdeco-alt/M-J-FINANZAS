"""Fechas en la forma usada por los actos administrativos."""

from __future__ import annotations

from datetime import date

from .numeros import entero_a_letras

MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

DIAS_SEMANA = (
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
)


def mes(f: date) -> str:
    return MESES[f.month - 1]


def fecha_corta(f: date) -> str:
    """15/10/2026"""
    return f"{f.day:02d}/{f.month:02d}/{f.year}"


def fecha_larga(f: date) -> str:
    """15 de octubre de 2026"""
    return f"{f.day} de {mes(f)} de {f.year}"


def fecha_en_letras(f: date) -> str:
    """quince (15) de octubre de dos mil veintiséis (2026)"""
    dia = entero_a_letras(f.day)
    anio = entero_a_letras(f.year)
    return f"{dia} ({f.day}) de {mes(f)} de {anio} ({f.year})"


def dia_semana(f: date) -> str:
    return DIAS_SEMANA[f.weekday()]


def etiquetas_fecha(prefijo: str, f: date | None) -> dict[str, str]:
    """Genera las variantes de una fecha: {{fecha}}, {{fecha_letras}}, ..."""
    if f is None:
        return {prefijo: "", f"{prefijo}_larga": "", f"{prefijo}_letras": "",
                f"{prefijo}_dia": "", f"{prefijo}_mes": "", f"{prefijo}_anio": ""}
    return {
        prefijo: fecha_corta(f),
        f"{prefijo}_larga": fecha_larga(f),
        f"{prefijo}_letras": fecha_en_letras(f),
        f"{prefijo}_dia": str(f.day),
        f"{prefijo}_mes": mes(f),
        f"{prefijo}_anio": str(f.year),
    }
