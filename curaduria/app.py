"""Automatizador de resoluciones — formulario local en Streamlit.

Ejecutar:  streamlit run app.py
"""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from curaduria import plantilla as motor
from curaduria.genero_nombres import sugerir_genero
from curaduria.gramatica import TIPOS_DOCUMENTO, Titular
from curaduria.resolucion import SENTIDOS, TIPOS_TRAMITE, Inmueble, Resolucion

RUTA_PLANTILLAS = Path(__file__).parent / "plantillas"
CALIDADES = ("propietario", "poseedor", "apoderado", "solicitante", "titular")

st.set_page_config(page_title="Resoluciones de Curaduría", page_icon="📄",
                   layout="wide")


# --- Utilidades -------------------------------------------------------------

def plantillas_disponibles() -> list[Path]:
    if not RUTA_PLANTILLAS.exists():
        return []
    return sorted(p for p in RUTA_PLANTILLAS.glob("*.docx")
                  if not p.name.startswith("~$"))


def titulares_por_defecto() -> pd.DataFrame:
    return pd.DataFrame([
        {"nombre": "", "sexo": "Masculino", "tipo_doc": "CC",
         "numero_doc": "", "calidad": "propietario"},
    ])


def leer_titulares(tabla: pd.DataFrame) -> list[Titular]:
    titulares: list[Titular] = []
    for _, fila in tabla.iterrows():
        nombre = str(fila.get("nombre") or "").strip()
        if not nombre and not str(fila.get("numero_doc") or "").strip():
            continue  # fila vacía: la ignoramos
        titulares.append(Titular(
            nombre=nombre,
            genero="F" if str(fila.get("sexo")).startswith("Fem") else "M",
            tipo_documento=str(fila.get("tipo_doc") or "CC"),
            numero_documento=str(fila.get("numero_doc") or "").strip(),
            calidad=str(fila.get("calidad") or "propietario"),
        ))
    return titulares


# --- Encabezado -------------------------------------------------------------

st.title("📄 Automatizador de Resoluciones")
st.caption("Llene el formulario una sola vez: el género, las fechas y los "
           "números en letras se resuelven solos. El Word sale 100% editable.")

if "titulares" not in st.session_state:
    st.session_state.titulares = titulares_por_defecto()

# --- Barra lateral: plantilla ----------------------------------------------

with st.sidebar:
    st.header("Plantilla maestra")
    disponibles = plantillas_disponibles()
    subida = st.file_uploader("Subir plantilla (.docx)", type="docx")
    elegida = None
    if disponibles:
        nombres = ["(usar la plantilla subida)"] + [p.name for p in disponibles]
        seleccion = st.selectbox("O usar una guardada", nombres,
                                 index=1 if not subida else 0)
        if seleccion != nombres[0]:
            elegida = RUTA_PLANTILLAS / seleccion

    origen = subida if subida is not None else elegida
    if origen is None:
        st.warning("Suba una plantilla o guarde una en la carpeta `plantillas/`.")
    else:
        st.success(f"Plantilla: {getattr(origen, 'name', origen)}")

    st.divider()
    st.caption("Las etiquetas se escriben en Word como `{{nombre}}`. "
               "Ejecute `python crear_plantilla_ejemplo.py` para ver un modelo.")


# --- Formulario -------------------------------------------------------------

col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("1. Datos del acto")
    numero = st.text_input("Número de resolución", placeholder="01-2-0456")
    fecha = st.date_input("Fecha de la resolución", value=date.today(),
                          format="DD/MM/YYYY")
    radicado = st.text_input("Radicado", placeholder="11001-1-26-0123")
    fecha_radicado = st.date_input("Fecha del radicado", value=date.today(),
                                   format="DD/MM/YYYY")
    tipo_tramite = st.selectbox("Tipo de trámite", TIPOS_TRAMITE)
    sentido = st.selectbox("Sentido de la decisión", SENTIDOS)
    vigencia_meses = st.number_input("Vigencia (meses)", min_value=1,
                                     max_value=120, value=36, step=1)

with col_der:
    st.subheader("2. Curaduría")
    curaduria = st.text_input("Nombre de la curaduría",
                              placeholder="Curaduría Urbana No. 1 de ...")
    curador = st.text_input("Nombre de quien firma")
    genero_curador = st.radio("Tratamiento de la firma",
                              ["Curador Urbano", "Curadora Urbana"],
                              horizontal=True)

st.divider()
st.subheader("3. Titulares")
st.caption("El sexo se sugiere a partir del nombre; verifíquelo antes de generar. "
           "Agregue filas para varios titulares: el texto pasa a plural solo.")

col_a, col_b = st.columns([1, 3])
with col_a:
    if st.button("Sugerir sexo por nombre", width="stretch"):
        tabla = st.session_state.titulares.copy()
        for indice, fila in tabla.iterrows():
            nombre = str(fila.get("nombre") or "")
            if nombre.strip():
                sugerido = sugerir_genero(nombre)
                tabla.at[indice, "sexo"] = ("Femenino" if sugerido == "F"
                                            else "Masculino")
        st.session_state.titulares = tabla
        st.rerun()

tabla_titulares = st.data_editor(
    st.session_state.titulares,
    num_rows="dynamic",
    width="stretch",
    key="editor_titulares",
    column_config={
        "nombre": st.column_config.TextColumn("Nombre completo", width="large"),
        "sexo": st.column_config.SelectboxColumn(
            "Sexo", options=["Masculino", "Femenino"], required=True),
        "tipo_doc": st.column_config.SelectboxColumn(
            "Tipo doc.", options=list(TIPOS_DOCUMENTO), required=True),
        "numero_doc": st.column_config.TextColumn("Número"),
        "calidad": st.column_config.SelectboxColumn(
            "Calidad", options=list(CALIDADES), required=True),
    },
)
st.session_state.titulares = tabla_titulares
titulares = leer_titulares(tabla_titulares)

st.divider()
st.subheader("4. Predio")
pcol1, pcol2, pcol3 = st.columns(3)
with pcol1:
    direccion = st.text_input("Dirección")
    barrio = st.text_input("Barrio")
    municipio = st.text_input("Municipio")
    departamento = st.text_input("Departamento")
with pcol2:
    matricula = st.text_input("Matrícula inmobiliaria")
    cedula_catastral = st.text_input("Cédula catastral")
    chip = st.text_input("CHIP / referencia catastral", value="")
    uso = st.text_input("Uso del suelo")
with pcol3:
    area_lote = st.number_input("Área del lote (m²)", min_value=0.0, step=0.01,
                                format="%.2f")
    area_construida = st.number_input("Área construida (m²)", min_value=0.0,
                                      step=0.01, format="%.2f")
    pisos = st.number_input("Número de pisos", min_value=0, max_value=100, step=1)
    tratamiento_urbanistico = st.text_input("Tratamiento urbanístico")

st.divider()
st.subheader("5. Proyecto y cierre")
ccol1, ccol2 = st.columns(2)
with ccol1:
    proyectista = st.text_input("Proyectista / arquitecto")
    matricula_profesional = st.text_input("Matrícula profesional")
with ccol2:
    observaciones = st.text_area("Observaciones", height=120)

resolucion = Resolucion(
    numero=numero,
    fecha=fecha,
    radicado=radicado,
    fecha_radicado=fecha_radicado,
    tipo_tramite=tipo_tramite,
    sentido=sentido,
    curador=curador,
    genero_curador="M" if genero_curador == "Curador Urbano" else "F",
    curaduria=curaduria,
    titulares=titulares,
    inmueble=Inmueble(
        direccion=direccion, barrio=barrio, municipio=municipio,
        departamento=departamento, matricula_inmobiliaria=matricula,
        cedula_catastral=cedula_catastral, chip=chip,
        area_lote=area_lote, area_construida=area_construida,
        tratamiento_urbanistico=tratamiento_urbanistico, uso=uso,
        pisos=int(pisos),
    ),
    proyectista=proyectista,
    matricula_profesional=matricula_profesional,
    vigencia_meses=int(vigencia_meses),
    observaciones=observaciones,
)

etiquetas = resolucion.etiquetas()

# --- Vista previa de la concordancia ---------------------------------------

st.divider()
st.subheader("6. Revisión")

if titulares:
    vista1, vista2 = st.columns(2)
    with vista1:
        st.markdown("**Así quedará redactado:**")
        st.info(
            f"{etiquetas['identificacion']}, {etiquetas['verbo_obrar']} "
            f"{etiquetas['calidad']}, {etiquetas['verbo_solicitar']} "
            f"{tipo_tramite.lower()} para el predio de {etiquetas['direccion'] or '…'}."
        )
        st.info(
            f"Notificar {etiquetas['contraccion_a']} {etiquetas['interesado']} "
            f"{etiquetas['nombres']}, {etiquetas['quien']} "
            f"{etiquetas['verbo_podra']} interponer los recursos de ley."
        )
    with vista2:
        st.markdown("**Concordancia resuelta:**")
        st.write({
            "número gramatical": "plural" if len(titulares) > 1 else "singular",
            "género": "femenino" if etiquetas["articulo"] == "la" else "masculino",
            "artículo": etiquetas["articulo"],
            "tratamiento": etiquetas["tratamiento"],
            "participio": etiquetas["identificado"],
            "área lote": etiquetas["area_lote_letras"],
        })

errores = resolucion.errores()
if errores:
    for problema in errores:
        st.error(problema)

# --- Generación -------------------------------------------------------------

st.divider()
listo = origen is not None and not errores
if st.button("⚙️ Generar resolución en Word", type="primary", disabled=not listo,
             width="stretch"):
    try:
        if hasattr(origen, "seek"):
            origen.seek(0)
        documento = motor.abrir(origen)
        presentes = motor.etiquetas_del_documento(documento)
        faltantes = motor.rellenar(documento, etiquetas)
        memoria = io.BytesIO()
        documento.save(memoria)
        memoria.seek(0)
    except Exception as error:  # la plantilla puede estar corrupta o protegida
        st.exception(error)
    else:
        st.success(f"Documento generado. {len(presentes)} etiquetas en la plantilla.")
        if faltantes:
            st.warning(
                "Estas etiquetas de la plantilla no tienen dato y quedaron tal cual: "
                + ", ".join(f"`{{{{{c}}}}}`" for c in sorted(faltantes))
                + ". Agréguelas como campo libre o corrija la plantilla."
            )
        st.download_button(
            "⬇️ Descargar .docx",
            data=memoria,
            file_name=resolucion.nombre_archivo(),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            width="stretch",
        )

with st.expander("Ver todas las etiquetas disponibles para la plantilla"):
    st.caption("Escriba estas etiquetas en el Word, entre llaves dobles.")
    st.dataframe(
        pd.DataFrame(
            [{"etiqueta": f"{{{{{clave}}}}}", "valor actual": valor}
             for clave, valor in sorted(etiquetas.items())]
        ),
        width="stretch", height=400,
    )
