"""Automatizador de resoluciones de curaduría urbana.

Módulos:
    gramatica  concordancia de género y número, titulares
    numeros    números a letras (español), formato de cifras
    fechas     fechas en la forma de los actos administrativos
    plantilla  relleno de plantillas .docx conservando el formato
    resolucion modelo de la resolución y diccionario de etiquetas
"""

from .gramatica import Concordancia, Titular
from .resolucion import Inmueble, Resolucion

__all__ = ["Concordancia", "Titular", "Inmueble", "Resolucion"]
