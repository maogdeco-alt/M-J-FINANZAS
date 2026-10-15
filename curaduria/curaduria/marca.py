"""Identidad visual de la Curaduría Urbana No. 2 de Ibagué.

Los colores salen del logo: el rojo de los bloques, el vinotinto de "URBANA"
y el gris de la trama del plano. Todo lo visual de la app sale de aquí, para
que cambiar un color sea cambiar una línea.
"""

from __future__ import annotations

from pathlib import Path

ROJO = "#BC2025"          # el rojo de los bloques del logo
VINOTINTO = "#7F1617"     # "URBANA"
GRIS = "#78787A"          # la trama del plano
GRIS_CLARO = "#E8E8EA"
GRIS_FONDO = "#F4F4F6"
BORDE_CAMPO = "#C9C9CF"
NEGRO = "#1A1A1A"
BLANCO = "#FFFFFF"
VERDE = "#1E7B45"         # solo para "listo"
AMBAR = "#B36B00"         # solo para avisos

RUTA_ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO = RUTA_ASSETS / "logo.png"
LOGO_MEMBRETE = RUTA_ASSETS / "logo_membrete.png"

NOMBRE = "Curaduría Urbana No. 2"
CIUDAD = "Ibagué"


def hay_logo() -> bool:
    return LOGO.exists()


CSS = f"""
<style>
  /* --- Tipografía y fondo ------------------------------------------- */
  html, body, [class*="st-"] {{ font-family: "Segoe UI", system-ui, sans-serif; }}
  .stApp {{ background: {GRIS_FONDO}; }}
  .block-container {{ padding-top: 1.2rem; max-width: 1280px; }}

  /* --- Banda de marca ------------------------------------------------ */
  .membrete {{
      display: flex; align-items: center; gap: 1.1rem;
      background: {BLANCO}; border-radius: 10px;
      border-left: 7px solid {ROJO};
      box-shadow: 0 1px 3px rgba(0,0,0,.10);
      padding: .85rem 1.3rem; margin-bottom: 1.1rem;
  }}
  .membrete h1 {{
      font-size: 1.45rem; margin: 0; color: {NEGRO};
      font-weight: 700; letter-spacing: -.01em; line-height: 1.2;
  }}
  .membrete p {{ margin: .15rem 0 0; color: {GRIS}; font-size: .9rem; }}

  /* --- Tarjetas de sección ------------------------------------------- */
  div[data-testid="stVerticalBlockBorderWrapper"] {{
      background: {BLANCO}; border: 1px solid {GRIS_CLARO} !important;
      border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,.05);
  }}
  .titulo-bloque {{
      display: flex; align-items: center; gap: .6rem;
      font-size: 1.05rem; font-weight: 700; color: {NEGRO};
      border-bottom: 2px solid {GRIS_CLARO};
      padding-bottom: .5rem; margin-bottom: 1rem;
  }}
  .numero-bloque {{
      background: {ROJO}; color: {BLANCO}; border-radius: 6px;
      width: 1.7rem; height: 1.7rem; display: inline-flex;
      align-items: center; justify-content: center;
      font-size: .9rem; font-weight: 700; flex: none;
  }}
  .numero-bloque.gris {{ background: {GRIS}; }}

  /* --- Botones -------------------------------------------------------- */
  .stButton > button, .stDownloadButton > button,
  .stFormSubmitButton > button {{
      border-radius: 8px; font-weight: 600; border: 1.5px solid {GRIS_CLARO};
      padding: .55rem 1.1rem; transition: all .12s ease;
  }}
  .stButton > button:hover, .stDownloadButton > button:hover {{
      border-color: {ROJO}; color: {ROJO};
  }}
  .stButton > button[kind="primary"],
  .stFormSubmitButton > button[kind="primary"],
  .stDownloadButton > button {{
      background: {ROJO}; color: {BLANCO}; border-color: {ROJO};
      font-size: 1rem; padding: .7rem 1.2rem;
  }}
  .stButton > button[kind="primary"]:hover,
  .stDownloadButton > button:hover {{
      background: {VINOTINTO}; border-color: {VINOTINTO}; color: {BLANCO};
  }}
  .stButton > button:disabled {{
      background: {GRIS_CLARO} !important; color: {GRIS} !important;
      border-color: {GRIS_CLARO} !important;
  }}

  /* --- Pestañas ------------------------------------------------------- */
  .stTabs [data-baseweb="tab-list"] {{ gap: .3rem; }}
  .stTabs [data-baseweb="tab"] {{
      background: {BLANCO}; border-radius: 8px 8px 0 0;
      padding: .6rem 1.2rem; font-weight: 600; color: {GRIS};
      border: 1px solid {GRIS_CLARO}; border-bottom: none;
  }}
  .stTabs [aria-selected="true"] {{
      background: {ROJO} !important; color: {BLANCO} !important;
      border-color: {ROJO} !important;
  }}

  /* --- Avance --------------------------------------------------------- */
  .stProgress > div > div > div > div {{ background: {ROJO}; }}
  .pastilla {{
      display: inline-block; padding: .18rem .6rem; border-radius: 999px;
      font-size: .78rem; font-weight: 600; margin: .12rem .25rem .12rem 0;
      background: {GRIS_CLARO}; color: {NEGRO};
  }}
  .pastilla.falta {{ background: #FBE3E4; color: {VINOTINTO}; }}
  .pastilla.listo {{ background: #E3F1E9; color: {VERDE}; }}

  /* --- Campos --------------------------------------------------------- */
  /* Las casillas tienen que verse como casillas: el borde que trae el tema
     es casi del color del fondo y sobre blanco parecen texto suelto. */
  [data-testid="stTextInputRootElement"],
  [data-testid="stNumberInputContainer"],
  .stDateInput [data-baseweb="input"],
  .stTextArea [data-baseweb="textarea"],
  [data-testid="stSelectbox"] [data-baseweb="select"] > div,
  [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
      border: 1.5px solid {BORDE_CAMPO} !important;
      border-radius: 7px !important;
      background: {BLANCO} !important;
  }}
  [data-testid="stTextInputRootElement"]:focus-within,
  [data-testid="stNumberInputContainer"]:focus-within,
  .stDateInput [data-baseweb="input"]:focus-within,
  [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
  [data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within {{
      border-color: {ROJO} !important;
      box-shadow: 0 0 0 2px rgba(188,32,37,.15) !important;
  }}

  label p {{ font-weight: 600 !important; color: {NEGRO} !important; }}
  .pista {{ font-size: .8rem; margin: -.4rem 0 .5rem; }}
  .pista.bien {{ color: {GRIS}; }}
  .pista.duda {{ color: {AMBAR}; }}
  .pista.mal  {{ color: {ROJO}; }}

  /* --- Barra lateral --------------------------------------------------- */
  section[data-testid="stSidebar"] {{
      background: {BLANCO}; border-right: 1px solid {GRIS_CLARO};
  }}
  section[data-testid="stSidebar"] h2 {{
      font-size: .78rem; text-transform: uppercase; letter-spacing: .08em;
      color: {GRIS}; font-weight: 700; margin-bottom: .4rem;
  }}

  /* --- Detalles -------------------------------------------------------- */
  div[data-testid="stExpander"] details {{
      border: 1px solid {GRIS_CLARO}; border-radius: 8px; background: {BLANCO};
  }}
  div[data-testid="stExpander"] summary {{ font-weight: 600; }}
  /* El icono del desplegable se baja de internet; si el equipo está sin red
     se vería el nombre del icono encima del título. Se dibuja aquí. */
  div[data-testid="stExpander"] summary span[data-testid="stIconMaterial"] {{
      font-size: 0 !important; width: .9rem; position: relative;
  }}
  div[data-testid="stExpander"] summary span[data-testid="stIconMaterial"]::after {{
      content: ""; position: absolute; left: 0; top: -.2rem;
      border: solid {GRIS}; border-width: 0 2px 2px 0;
      padding: 3px; transform: rotate(45deg);
  }}
  div[data-testid="stExpander"] details[open] summary
      span[data-testid="stIconMaterial"]::after {{
      transform: rotate(-135deg); top: .1rem;
  }}
  hr {{ border-color: {GRIS_CLARO}; }}
  #MainMenu, footer {{ visibility: hidden; }}
</style>
"""


def titulo_bloque(numero: str, texto: str, gris: bool = False) -> str:
    clase = "numero-bloque gris" if gris else "numero-bloque"
    return (f'<div class="titulo-bloque">'
            f'<span class="{clase}">{numero}</span>{texto}</div>')


def pastilla(texto: str, estado: str = "") -> str:
    clase = f"pastilla {estado}".strip()
    return f'<span class="{clase}">{texto}</span>'
