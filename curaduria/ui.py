"""Piezas de interfaz: marca, bloques, campos que no pierden lo escrito.

El problema que resuelve el almacén: Streamlit borra el estado de un campo que
no se dibuja en una corrida. Como el formulario se encoge según el trámite —si
no hay demolición, no se pide el área a demoler—, un campo que se oculta y
vuelve aparecía vacío. Aquí cada campo guarda su valor en un diccionario
aparte, que Streamlit no toca, y lo recupera cuando vuelve a mostrarse.

Este módulo es lo único que sabe de Streamlit además de `app.py`: el paquete
`curaduria` no depende de la interfaz.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from typing import Any, Callable, Sequence

import streamlit as st

from curaduria import formato
from curaduria.marca import CSS, LOGO, hay_logo, pastilla, titulo_bloque

ALMACEN = "_datos_guardados"


# --- Marca ------------------------------------------------------------------

def aplicar_marca() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def membrete(titulo: str, subtitulo: str = "") -> None:
    """La banda de identidad: logo a la izquierda, título al lado."""
    columnas = st.columns([1, 5], vertical_alignment="center")
    with columnas[0]:
        if hay_logo():
            st.image(str(LOGO), width="stretch")
    with columnas[1]:
        st.markdown(
            f'<div style="padding:.2rem 0">'
            f'<h1 style="font-size:1.5rem;margin:0;font-weight:700">{titulo}</h1>'
            f'<p style="margin:.2rem 0 0;color:#78787A">{subtitulo}</p></div>',
            unsafe_allow_html=True)
    st.markdown("<hr style='margin:.6rem 0 1.1rem'>", unsafe_allow_html=True)


@contextmanager
def bloque(numero: str, titulo: str, gris: bool = False):
    """Una tarjeta con número y título, para que se vea dónde empieza cada cosa."""
    with st.container(border=True):
        st.markdown(titulo_bloque(numero, titulo, gris), unsafe_allow_html=True)
        yield


def pastillas(etiquetas: Sequence[tuple[str, str]]) -> None:
    st.markdown(" ".join(pastilla(texto, estado) for texto, estado in etiquetas),
                unsafe_allow_html=True)


# --- Almacén ----------------------------------------------------------------

def _almacen() -> dict[str, Any]:
    if ALMACEN not in st.session_state:
        st.session_state[ALMACEN] = {}
    return st.session_state[ALMACEN]


def _sembrar(clave: str, por_defecto: Any) -> Any:
    """Pone en el estado el valor guardado antes, si el campo vuelve a salir."""
    almacen = _almacen()
    if clave not in st.session_state:
        st.session_state[clave] = almacen.get(clave, por_defecto)
    return st.session_state[clave]


def _recordar(clave: str, valor: Any) -> Any:
    _almacen()[clave] = valor
    return valor


def recordado(clave: str, por_defecto: Any = "") -> Any:
    """Lo último que se escribió en ese campo, aunque ahora esté oculto."""
    return _almacen().get(clave, por_defecto)


def limpiar_formulario(conservar: Sequence[str] = ()) -> None:
    """Deja el formulario en blanco para la siguiente resolución."""
    almacen = _almacen()
    for clave in list(almacen):
        if clave in conservar:
            continue
        almacen.pop(clave, None)
        st.session_state.pop(clave, None)


# --- Campos -----------------------------------------------------------------

def _pista(revision: formato.Revision) -> None:
    if revision.mensaje:
        st.markdown(f'<div class="pista {revision.estado}">{revision.icono} '
                    f'{revision.mensaje}</div>', unsafe_allow_html=True)


def texto(etiqueta: str, clave: str, normalizador: Callable | None = None,
          ayuda: str = "", marcador: str = "", area: bool = False) -> str:
    """Campo de texto que se corrige solo al salir de él y no pierde lo escrito."""
    _sembrar(clave, "")

    def al_cambiar() -> None:
        valor = st.session_state.get(clave, "")
        if normalizador is not None:
            revision = normalizador(valor)
            if revision.valor:
                valor = revision.valor
                st.session_state[clave] = valor
        _recordar(clave, valor)

    if area:
        st.text_area(etiqueta, key=clave, help=ayuda or None,
                     placeholder=marcador or None, on_change=al_cambiar,
                     height=90)
    else:
        st.text_input(etiqueta, key=clave, help=ayuda or None,
                      placeholder=marcador or None, on_change=al_cambiar)

    bruto = st.session_state.get(clave, "")
    _recordar(clave, bruto)
    if normalizador is None:
        return bruto
    revision = normalizador(bruto)
    _pista(revision)
    return revision.valor


def fecha(etiqueta: str, clave: str, ayuda: str = "") -> date:
    valor = _sembrar(clave, date.today())
    if not isinstance(valor, date):
        st.session_state[clave] = date.today()
    st.date_input(etiqueta, key=clave, format="DD/MM/YYYY", help=ayuda or None)
    return _recordar(clave, st.session_state[clave])


def numero(etiqueta: str, clave: str, minimo: float = 0.0,
           maximo: float | None = None, paso: float = 1.0,
           entero: bool = False, ayuda: str = "") -> float:
    por_defecto = int(minimo) if entero else float(minimo)
    _sembrar(clave, por_defecto)
    st.number_input(etiqueta, key=clave, min_value=por_defecto,
                    max_value=maximo, step=int(paso) if entero else paso,
                    format="%d" if entero else "%.2f", help=ayuda or None)
    return _recordar(clave, st.session_state[clave])


def opcion(etiqueta: str, clave: str, opciones: Sequence,
           formato_opcion: Callable | None = None, ayuda: str = "",
           horizontal: bool = False, como_botones: bool = False) -> Any:
    """Lista desplegable, o botones en línea cuando son pocas opciones."""
    guardado = recordado(clave, None)
    indice = opciones.index(guardado) if guardado in opciones else 0
    if clave not in st.session_state:
        st.session_state[clave] = opciones[indice] if opciones else None
    visibilidad = "collapsed" if not etiqueta else "visible"
    if como_botones:
        st.radio(etiqueta or " ", opciones, key=clave, horizontal=horizontal,
                 format_func=formato_opcion or str, help=ayuda or None,
                 label_visibility=visibilidad)
    else:
        st.selectbox(etiqueta or " ", opciones, key=clave,
                     format_func=formato_opcion or str, help=ayuda or None,
                     label_visibility=visibilidad)
    return _recordar(clave, st.session_state[clave])


def varias(etiqueta: str, clave: str, opciones: Sequence,
           formato_opcion: Callable | None = None, ayuda: str = "",
           maximo: int | None = None) -> list:
    guardados = [o for o in recordado(clave, []) if o in opciones]
    if clave not in st.session_state:
        st.session_state[clave] = guardados
    else:
        vigentes = [o for o in st.session_state[clave] if o in opciones]
        if vigentes != st.session_state[clave]:
            st.session_state[clave] = vigentes
    st.multiselect(etiqueta, opciones, key=clave,
                   format_func=formato_opcion or str, help=ayuda or None,
                   max_selections=maximo,
                   placeholder="Elija una o varias opciones")
    return _recordar(clave, list(st.session_state[clave]))


def marca_casilla(etiqueta: str, clave: str, por_defecto: bool = False,
                  ayuda: str = "") -> bool:
    _sembrar(clave, por_defecto)
    st.checkbox(etiqueta, key=clave, help=ayuda or None)
    return _recordar(clave, st.session_state[clave])


def tabla(etiqueta: str, clave: str, datos, configuracion: dict,
          ayuda: str = ""):
    """Tabla editable que conserva las filas entre corridas."""
    if etiqueta:
        st.markdown(f"**{etiqueta}**")
    if ayuda:
        st.caption(ayuda)
    guardada = recordado(clave, None)
    inicial = guardada if guardada is not None else datos
    editada = st.data_editor(inicial, num_rows="dynamic", width="stretch",
                             key=f"editor_{clave}", column_config=configuracion)
    return _recordar(clave, editada)
