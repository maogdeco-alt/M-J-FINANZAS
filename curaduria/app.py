"""Automatizador de Resoluciones — Curaduría Urbana No. 2 de Ibagué.

Ejecutar:  streamlit run app.py

El trabajo va en tres pasos: llenar los datos, escoger los párrafos, generar.
Lo demás (configuración, biblioteca, plantillas) está en Ajustes, porque se
toca una vez y no todos los días.
"""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import ui
from curaduria import armado, formato
from curaduria import plantilla as motor
from curaduria.auditoria import auditar
from curaduria.bloques import CATEGORIAS, Biblioteca, Bloque
from curaduria.catalogo import GRUPOS, TRAMITES, USOS, Solicitud, tramites_por_grupo
from curaduria.configuracion import Configuracion
from curaduria.genero_nombres import sugerir_genero
from curaduria.gramatica import TIPOS_DOCUMENTO, Titular
from curaduria.marca import CIUDAD, LOGO, NOMBRE, hay_logo
from curaduria.preparacion import preparar
from curaduria.profesionales import ROLES, Profesional
from curaduria.resolucion import (CUBIERTAS, RESPONSABLES, SENTIDOS,
                                  Actuaciones, Inmueble, Notificacion,
                                  Resolucion, Responsable)

RUTA_PLANTILLAS = Path(__file__).parent / "plantillas"
CALIDADES = ("propietario", "poseedor", "titular")
SEXOS = ["Masculino", "Femenino"]
MIME_WORD = ("application/vnd.openxmlformats-officedocument"
             ".wordprocessingml.document")

st.set_page_config(page_title="Resoluciones · Curaduría Urbana No. 2",
                   page_icon=str(LOGO) if hay_logo() else "📄",
                   layout="wide", initial_sidebar_state="expanded")
ui.aplicar_marca()


# --- Estado -----------------------------------------------------------------

@st.cache_resource
def biblioteca() -> Biblioteca:
    return Biblioteca()


def configuracion() -> Configuracion:
    if "configuracion" not in st.session_state:
        st.session_state.configuracion = Configuracion.cargar()
    return st.session_state.configuracion


libreria = biblioteca()
config = configuracion()

TITULARES_VACIOS = pd.DataFrame([
    {"nombre": "", "sexo": "Masculino", "tipo_doc": "CC", "numero_doc": "",
     "calidad": "propietario"}])
PROFESIONALES_VACIOS = pd.DataFrame([
    {"rol": rol, "nombre": "", "sexo": "Masculino", "documento": "",
     "matricula": ""} for rol in ("proyectista", "constructor")])


def leer_titulares(tabla: pd.DataFrame) -> tuple[list[Titular], list[str]]:
    titulares: list[Titular] = []
    avisos: list[str] = []
    for numero, (_, fila) in enumerate(tabla.iterrows(), start=1):
        bruto_nombre = str(fila.get("nombre") or "")
        bruto_doc = str(fila.get("numero_doc") or "")
        if not bruto_nombre.strip() and not bruto_doc.strip():
            continue
        tipo = str(fila.get("tipo_doc") or "CC")
        revision_nombre = formato.normalizar_nombre(
            bruto_nombre, config.nombres_en_mayuscula)
        revision_doc = formato.normalizar_documento(bruto_doc, tipo)
        for revision, que in ((revision_nombre, "nombre"),
                              (revision_doc, "documento")):
            if revision.mensaje and revision.estado != "bien":
                avisos.append(f"Titular {numero} ({que}): {revision.mensaje}")
        titulares.append(Titular(
            nombre=revision_nombre.valor,
            genero="F" if str(fila.get("sexo")).startswith("Fem") else "M",
            tipo_documento=tipo, numero_documento=revision_doc.valor,
            calidad=str(fila.get("calidad") or "propietario")))
    return titulares, avisos


def leer_profesionales(tabla: pd.DataFrame) -> list[Profesional]:
    profesionales: list[Profesional] = []
    for _, fila in tabla.iterrows():
        nombre = str(fila.get("nombre") or "").strip()
        if not nombre:
            continue
        profesionales.append(Profesional(
            rol=str(fila.get("rol") or "proyectista"),
            nombre=formato.normalizar_nombre(
                nombre, config.nombres_en_mayuscula).valor,
            genero="F" if str(fila.get("sexo")).startswith("Fem") else "M",
            documento=formato.normalizar_documento(
                str(fila.get("documento") or "")).valor,
            matricula=str(fila.get("matricula") or "").strip()))
    return profesionales


def fijar_bloques(ids: set[str]) -> None:
    """Cambia la selección de párrafos desde un botón.

    No basta con guardar la lista: cada casilla conserva su propio estado por
    su clave y seguiría ganándole al valor nuevo. Hay que borrar esas claves
    para que las casillas vuelvan a tomar el valor que les corresponde.
    """
    st.session_state.bloques_elegidos = set(ids)
    for clave in [c for c in st.session_state if c.startswith("chk_")]:
        del st.session_state[clave]


def plantillas_disponibles() -> list[Path]:
    if not RUTA_PLANTILLAS.exists():
        return []
    return sorted(p for p in RUTA_PLANTILLAS.glob("*.docx")
                  if not p.name.startswith("~$"))


def valores_del_despacho(config: Configuracion) -> dict[str, str]:
    valores = {"curador": config.curador, "sustanciador": config.sustanciador,
               "municipio": config.municipio}
    return {clave: valor for clave, valor in valores.items() if valor.strip()}


# --- Membrete ---------------------------------------------------------------

ui.membrete(
    "Automatizador de Resoluciones",
    f"{NOMBRE} de {CIUDAD}" if config.completa
    else "Primero complete la configuración, en la pestaña Ajustes")

# --- Barra lateral ----------------------------------------------------------

with st.sidebar:
    if hay_logo():
        st.image(str(LOGO), width="stretch")
    st.markdown("## Despacho")
    if config.completa:
        st.markdown(f"**{config.curador}**")
        st.caption(config.despacho().tratamiento)
        st.caption(f"Sustancia: {config.sustanciador}")
    else:
        st.error("Falta configurar: " + ", ".join(config.faltantes()))

    st.markdown("## Plantilla")
    disponibles = plantillas_disponibles()
    nombres = [p.name for p in disponibles]
    if nombres:
        elegida_nombre = ui.opcion("Plantilla en uso", "plantilla_elegida",
                                   nombres)
        origen_plantilla = RUTA_PLANTILLAS / elegida_nombre
    else:
        origen_plantilla = None
        st.warning("No hay plantillas. Vaya a Ajustes → Plantillas.")

    st.markdown("## Nueva resolución")
    if st.button("Limpiar el formulario", width="stretch",
                 help="Borra los datos de esta resolución. La configuración "
                      "y la biblioteca no se tocan."):
        ui.limpiar_formulario(conservar=("plantilla_elegida",))
        st.session_state.pop("bloques_elegidos", None)
        st.rerun()

# --- Pestañas ---------------------------------------------------------------

paso1, paso2, paso3, ajustes = st.tabs(
    ["1 · Datos", "2 · Párrafos", "3 · Generar", "Ajustes"])

# --- Paso 1: Datos ----------------------------------------------------------

with paso1:
    hueco_avance = st.container()

    with ui.bloque("1", "Qué se solicita"):
        col1, col2 = st.columns([1, 2])
        with col1:
            grupo = ui.opcion("Grupo", "grupo", list(GRUPOS),
                              formato_opcion=GRUPOS.get)
        with col2:
            opciones_tramite = tramites_por_grupo()[grupo]
            tramite = ui.opcion("Trámite", f"tramite_{grupo}",
                                opciones_tramite,
                                formato_opcion=lambda t: t.nombre)
        if tramite.nota:
            st.caption(f"ℹ️ {tramite.nota}")

        modalidades_ids: list[str] = []
        if tramite.modalidades:
            etiqueta = ("Modalidades — se pueden combinar"
                        if tramite.modalidades_multiples else "Modalidad")
            elegidas = ui.varias(
                etiqueta, f"modalidades_{tramite.id}", list(tramite.modalidades),
                formato_opcion=lambda m: m.nombre,
                maximo=None if tramite.modalidades_multiples else 1)
            modalidades_ids = [m.id for m in elegidas]

        usos_elegidos = ui.varias("Destinación / uso", "usos", list(USOS),
                                  formato_opcion=lambda u: u.nombre)
        solicitud = Solicitud(tramite.id, modalidades_ids,
                              [u.id for u in usos_elegidos])
        if solicitud.vivienda_interes:
            st.info(f"Proyecto **{solicitud.vivienda_interes}**: se activan "
                    "sus bloques y la exención del IDU.")
        for problema in solicitud.errores():
            if solicitud.modalidades_ids or "exige indicar la modalidad" \
                    not in problema:
                st.error(problema)

    with ui.bloque("2", "Identificación del acto"):
        col1, col2, col3 = st.columns(3)
        with col1:
            numero = ui.texto("Resolución No.", "numero",
                              marcador="73001-2-26-0456")
            fecha = ui.fecha("Fecha de la resolución", "fecha")
        with col2:
            radicado = ui.texto("Radicación No.", "radicado",
                                formato.normalizar_radicado,
                                marcador="2600789")
            fecha_radicado = ui.fecha("Fecha de radicación", "fecha_radicado")
        with col3:
            consecutivo = ui.texto(
                "Consecutivo del expediente", "consecutivo",
                formato.normalizar_consecutivo, marcador="54",
                ayuda="Solo el consecutivo: el número completo se arma con el "
                      "código DANE, la curaduría y el año.")
            sentido = ui.opcion("Sentido de la decisión", "sentido",
                                list(SENTIDOS),
                                formato_opcion=lambda s: SENTIDOS[s][1])

    with ui.bloque("3", "Titulares"):
        if st.button("Sugerir el sexo por el nombre"):
            tabla_actual = ui.recordado("titulares", TITULARES_VACIOS).copy()
            for indice, fila in tabla_actual.iterrows():
                nombre = str(fila.get("nombre") or "")
                if nombre.strip():
                    tabla_actual.at[indice, "sexo"] = (
                        "Femenino" if sugerir_genero(nombre) == "F"
                        else "Masculino")
            st.session_state[ui.ALMACEN]["titulares"] = tabla_actual
            st.session_state.pop("editor_titulares", None)
            st.rerun()

        tabla_titulares = ui.tabla(
            "", "titulares", TITULARES_VACIOS,
            {"nombre": st.column_config.TextColumn("Nombre completo",
                                                   width="large"),
             "sexo": st.column_config.SelectboxColumn(
                 "Sexo", options=SEXOS, required=True,
                 help="De aquí sale toda la concordancia del documento."),
             "tipo_doc": st.column_config.SelectboxColumn(
                 "Tipo", options=list(TIPOS_DOCUMENTO), required=True),
             "numero_doc": st.column_config.TextColumn("Número"),
             "calidad": st.column_config.SelectboxColumn(
                 "Calidad", options=list(CALIDADES), required=True)},
            ayuda="Una fila por persona. Con dos o más, el texto pasa a plural "
                  "automáticamente. Use el + de la última fila para agregar.")
        titulares, avisos_titulares = leer_titulares(tabla_titulares)
        for aviso in avisos_titulares:
            st.caption(f"⚠️ {aviso}")

    with ui.bloque("4", "Quién radica la solicitud"):
        tipo_responsable = ui.opcion(
            "", "tipo_responsable", list(RESPONSABLES),
            formato_opcion=RESPONSABLES.get, como_botones=True)
        responsable = Responsable(tipo_responsable)
        if tipo_responsable != "titular":
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                responsable.nombre = ui.texto(
                    "Nombre de quien radica", "resp_nombre",
                    lambda t: formato.normalizar_nombre(
                        t, config.nombres_en_mayuscula))
            with col2:
                responsable.genero = "F" if ui.opcion(
                    "Sexo", "resp_sexo", SEXOS,
                    como_botones=True) == "Femenino" else "M"
            with col3:
                responsable.documento = ui.texto(
                    "Documento", "resp_doc", formato.normalizar_documento)

    inmueble = Inmueble(cubierta=CUBIERTAS[0])
    if tramite.requiere_predio:
        with ui.bloque("5", "Predio"):
            col1, col2 = st.columns(2)
            with col1:
                inmueble.matricula_inmobiliaria = ui.texto(
                    "Matrícula inmobiliaria", "matricula",
                    formato.normalizar_matricula, marcador="350-250605",
                    ayuda="Puede escribirla sin guion: se corrige sola.")
                inmueble.direccion = ui.texto(
                    "Dirección del predio", "direccion",
                    formato.normalizar_direccion,
                    marcador="Carrera 2 Sur No. 28 - 57")
            with col2:
                inmueble.ficha_catastral = ui.texto(
                    "Ficha catastral", "ficha",
                    formato.normalizar_ficha_catastral,
                    marcador="01-09-1014-0013-000",
                    ayuda="Quince dígitos; los guiones se ponen solos.")
                inmueble.barrio = ui.texto("Barrio", "barrio")

    modalidades = set(modalidades_ids)
    pide_areas = bool(modalidades & {"obra_nueva", "ampliacion", "adecuacion",
                                     "modificacion"}) or \
        tramite.id == "reconocimiento"
    pide_demolicion = bool(modalidades & {"demolicion_total",
                                          "demolicion_parcial"})
    pide_indices = bool(modalidades & {"obra_nueva", "ampliacion"})
    pide_edificacion = tramite.id in ("construccion", "reconocimiento")

    if pide_edificacion or pide_areas or pide_demolicion:
        with ui.bloque("6", "El proyecto"):
            st.caption("Solo se piden las áreas que la modalidad elegida "
                       "necesita.")
            if pide_edificacion:
                col1, col2 = st.columns(2)
                with col1:
                    inmueble.pisos = int(ui.numero("Pisos", "pisos",
                                                   maximo=100, entero=True))
                with col2:
                    inmueble.cubierta = ui.opcion("Cubierta", "cubierta",
                                                  list(CUBIERTAS))
            if pide_areas:
                col1, col2 = st.columns(2)
                with col1:
                    inmueble.area_lote = ui.numero(
                        "Área del lote (m²)", "area_lote", paso=0.01)
                with col2:
                    inmueble.area_construida = ui.numero(
                        "Área construida (m²)", "area_construida", paso=0.01)
            if pide_demolicion:
                col1, col2 = st.columns(2)
                with col1:
                    inmueble.area_demoler = ui.numero(
                        "Área a demoler (m²)", "area_demoler", paso=0.01)
                with col2:
                    inmueble.area_existente = ui.numero(
                        "Área existente (m²)", "area_existente", paso=0.01)
            if pide_indices:
                st.markdown("**Índices urbanísticos**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    inmueble.indice_construccion_permitido = ui.texto(
                        "Construcción permitido", "icp",
                        formato.normalizar_indice)
                with col2:
                    inmueble.indice_construccion_propuesto = ui.texto(
                        "Construcción propuesto", "icr",
                        formato.normalizar_indice)
                with col3:
                    inmueble.indice_ocupacion_permitido = ui.texto(
                        "Ocupación permitido", "iop",
                        formato.normalizar_indice)
                with col4:
                    inmueble.indice_ocupacion_propuesto = ui.texto(
                        "Ocupación propuesto", "ior",
                        formato.normalizar_indice)
            if solicitud.vivienda_interes:
                inmueble.estrato = ui.texto(
                    f"Estrato (lo pide el proyecto "
                    f"{solicitud.vivienda_interes})", "estrato",
                    ayuda="Define la exención del IDU y las expensas.")

    with st.expander("Datos opcionales — profesionales y predio"):
        st.caption("Nada de esto es obligatorio: lo que deje vacío sale en el "
                   "cuadro con una raya para completarlo en Word.")
        tabla_profesionales = ui.tabla(
            "Profesionales", "profesionales", PROFESIONALES_VACIOS,
            {"rol": st.column_config.SelectboxColumn(
                "Rol", options=list(ROLES), required=True),
             "nombre": st.column_config.TextColumn("Nombre", width="large"),
             "sexo": st.column_config.SelectboxColumn(
                 "Sexo", options=SEXOS, required=True),
             "documento": st.column_config.TextColumn("CC"),
             "matricula": st.column_config.TextColumn("Matrícula profesional")},
            ayuda="El título y el participio concuerdan con el sexo: "
                  "«la Arquitecta … identificada con».")
        col1, col2 = st.columns(2)
        with col1:
            inmueble.tratamiento_urbanistico = ui.texto(
                "Tratamiento urbanístico", "tratamiento")
            inmueble.amenaza_riesgo = ui.texto(
                "Amenaza y riesgo", "amenaza",
                marcador="riesgo medio por remoción en masa")
        with col2:
            inmueble.uso_principal = ui.texto("Uso principal del suelo",
                                              "uso_suelo")
            notificado_nombre = ui.texto(
                "Se notifica a", "notificado",
                lambda t: formato.normalizar_nombre(
                    t, config.nombres_en_mayuscula))

profesionales = leer_profesionales(ui.recordado("profesionales",
                                                PROFESIONALES_VACIOS))

resolucion = Resolucion(
    numero=numero, fecha=fecha, radicado=radicado,
    fecha_radicado=fecha_radicado, consecutivo_expediente=consecutivo,
    sentido=sentido, solicitud=solicitud, despacho=config.despacho(),
    titulares=titulares, responsable=responsable, inmueble=inmueble,
    profesionales=profesionales, actuaciones=Actuaciones(),
    notificacion=Notificacion(nombre=notificado_nombre),
    vigencia_meses=config.vigencia_meses,
    prorroga_meses=config.prorroga_meses)

etiquetas = resolucion.etiquetas()
filas_hoja = armado.filas_hoja_datos(etiquetas, resolucion.secciones_hoja_datos())
estado = resolucion.estado_campos()
listos, total = resolucion.avance
errores = resolucion.errores()
avisos = resolucion.advertencias()

with hueco_avance:
    with st.container(border=True):
        col1, col2 = st.columns([2, 3])
        with col1:
            st.progress(listos / total if total else 0.0,
                        text=f"**{listos} de {total}** datos listos")
        with col2:
            pendientes = [c.nombre for c in estado if not c.listo and c.critico]
            if pendientes:
                ui.pastillas([(p, "falta") for p in pendientes[:5]]
                             + ([(f"+{len(pendientes) - 5}", "falta")]
                                if len(pendientes) > 5 else []))
            else:
                ui.pastillas([("Listo para generar", "listo")])
        with st.expander(f"Ver los {total} datos uno por uno"):
            for campo in estado:
                st.markdown(f"{campo.icono} **{campo.nombre}** — "
                            f"<small>{campo.detalle}</small>",
                            unsafe_allow_html=True)
            st.caption("✓ listo · ✕ falta · ○ opcional para este trámite")

# --- Paso 2: Párrafos -------------------------------------------------------

with paso2:
    if "bloques_elegidos" not in st.session_state:
        st.session_state.bloques_elegidos = {
            b.id for b in libreria.obligatorios(tramite.id)}

    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(
                f"**{len(st.session_state.bloques_elegidos)} párrafos "
                f"elegidos** para {tramite.nombre}")
            st.caption("Los obligatorios ya vienen marcados. Marque además lo "
                       "que aplique a este caso.")
        with col2:
            if st.button("Solo obligatorios", width="stretch"):
                fijar_bloques({b.id for b in libreria.obligatorios(tramite.id)})
                st.rerun()
        with col3:
            if st.button("Marcar todos", width="stretch"):
                fijar_bloques({b.id for b in libreria.para_tramite(tramite.id)})
                st.rerun()

    elegidos: set[str] = set()
    for categoria, bloques_categoria in libreria.por_categoria(
            tramite.id).items():
        marcados_aqui = sum(
            1 for b in bloques_categoria
            if b.id in st.session_state.bloques_elegidos)
        with st.expander(
                f"{CATEGORIAS[categoria]}  ·  {marcados_aqui} de "
                f"{len(bloques_categoria)}",
                expanded=categoria in ("encabezado", "tramite")):
            for bloque_texto in bloques_categoria:
                col1, col2 = st.columns([5, 1])
                with col1:
                    marcado = st.checkbox(
                        bloque_texto.titulo
                        + ("  ·  obligatorio" if bloque_texto.obligatorio
                           else ""),
                        value=bloque_texto.id in st.session_state.bloques_elegidos,
                        key=f"chk_{bloque_texto.id}")
                    if bloque_texto.nota:
                        st.caption(bloque_texto.nota)
                    faltan = bloque_texto.faltantes(etiquetas)
                    if marcado and faltan:
                        st.caption("⚠️ sin dato: "
                                   + ", ".join(f"`{{{{{c}}}}}`"
                                               for c in faltan[:5]))
                with col2:
                    with st.popover("Ver texto", width="stretch"):
                        for parrafo in bloque_texto.render(etiquetas):
                            st.write(parrafo)
                if marcado:
                    elegidos.add(bloque_texto.id)
    st.session_state.bloques_elegidos = elegidos

bloques_elegidos = libreria.seleccion(st.session_state.bloques_elegidos)

# --- Paso 3: Generar --------------------------------------------------------

with paso3:
    with ui.bloque("1", "Revise cómo quedó redactado"):
        if titulares:
            st.info(etiquetas["solicitante_frase"] + ", solicita "
                    + etiquetas["tramite_completo"] + ".")
            st.info(f"Notificar {etiquetas['contraccion_a']} "
                    f"{etiquetas['interesado']} {etiquetas['nombres']}, "
                    f"{etiquetas['quien']} {etiquetas['verbo_podra']} "
                    "interponer los recursos de ley.")
        else:
            st.caption("Registre los titulares en el paso 1 para ver aquí "
                       "cómo queda redactado el documento.")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Expediente", etiquetas["expediente"] or "—")
        col2.metric("Titulares", f"{len(titulares)}")
        col3.metric("Género", "Femenino"
                    if etiquetas["articulo"] in ("la", "las") else "Masculino")
        col4.metric("Párrafos", f"{len(bloques_elegidos)}")

    if errores or avisos:
        with ui.bloque("2", "Antes de generar", gris=not errores):
            if errores:
                st.error(f"**Faltan {len(errores)} datos para poder "
                         f"generar.** Están en el paso 1.\n\n"
                         + "\n".join(f"- {problema}" for problema in errores))
            if avisos:
                st.warning("**Puede generar, pero revise:**\n\n"
                           + "\n".join(f"- {aviso}" for aviso in avisos))

    with ui.bloque("3" if (errores or avisos) else "2", "Generar el documento"):
        modo = ui.opcion(
            "Cómo se arma", "modo",
            ["Plantilla + párrafos elegidos", "Solo los párrafos elegidos",
             "Solo rellenar la plantilla"], como_botones=True,
            ayuda="Lo normal es el primero: la plantilla pone la estructura y "
                  "los párrafos elegidos entran en sus anclas.")
        incluir_hoja = ui.marca_casilla(
            "Agregar la hoja de datos al comienzo del documento",
            "incluir_hoja", True)

        necesita_plantilla = modo != "Solo los párrafos elegidos"
        if necesita_plantilla and origen_plantilla is None:
            st.warning("No hay plantilla elegida. Vaya a Ajustes → Plantillas, "
                       "o cambie a «Solo los párrafos elegidos».")
        if not config.completa:
            st.error("Complete la configuración del despacho en Ajustes.")

        listo_para_generar = (
            not errores and config.completa
            and (origen_plantilla is not None or not necesita_plantilla))

        if st.button("GENERAR LA RESOLUCIÓN EN WORD", type="primary",
                     width="stretch", disabled=not listo_para_generar):
            try:
                memoria = io.BytesIO()
                hoja = filas_hoja if incluir_hoja else None
                if modo == "Solo los párrafos elegidos":
                    documento, faltantes = armado.armar_desde_bloques(
                        bloques_elegidos, etiquetas, hoja,
                        subtitulo_hoja=resolucion.subtitulo_hoja_datos())
                    informe = {"faltantes": faltantes}
                else:
                    documento = motor.abrir(origen_plantilla)
                    usar = (bloques_elegidos
                            if modo == "Plantilla + párrafos elegidos" else [])
                    informe = armado.armar_sobre_plantilla(
                        documento, usar, etiquetas, hoja,
                        subtitulo_hoja=resolucion.subtitulo_hoja_datos())
                    faltantes = informe["faltantes"]
                documento.save(memoria)
                memoria.seek(0)
            except Exception as error:
                st.error(f"No pude generar el documento: {error}")
                st.exception(error)
            else:
                st.session_state.documento = memoria.getvalue()
                st.session_state.informe = informe
                st.session_state.nombre_documento = resolucion.nombre_archivo()
                st.rerun()

        if st.session_state.get("documento"):
            st.success("Documento generado.")
            st.download_button(
                "DESCARGAR LA RESOLUCIÓN", data=st.session_state.documento,
                file_name=st.session_state.nombre_documento, mime=MIME_WORD,
                width="stretch")
            informe = st.session_state.get("informe", {})
            conteo = informe.get("bloques_por_seccion")
            if conteo:
                st.caption(
                    f"Párrafos insertados — encabezado: "
                    f"{conteo.get('encabezado', 0)}, considerandos: "
                    f"{conteo.get('considerando', 0)}, resuelve: "
                    f"{conteo.get('resuelve', 0)}, cierre: "
                    f"{conteo.get('cierre', 0)}.")
            desviadas = informe.get("secciones_desviadas") or []
            if desviadas:
                st.info("La plantilla no tiene el ancla de: "
                        + ", ".join(f"`{{{{{s}}}}}`" for s in desviadas)
                        + ". Esos párrafos fueron al ancla vecina.")
            if informe.get("faltantes"):
                st.warning("Quedaron sin dato (se completan en Word): "
                           + ", ".join(sorted(informe["faltantes"])[:20]))

    with st.expander("Hoja de datos por separado"):
        st.caption("El cuadro solo, para imprimir o adjuntar al expediente.")
        if st.button("Preparar la hoja de datos", width="stretch"):
            documento = armado.documento_hoja_datos(
                filas_hoja, "HOJA DE DATOS DEL EXPEDIENTE",
                resolucion.subtitulo_hoja_datos())
            memoria = io.BytesIO()
            documento.save(memoria)
            st.session_state.hoja = memoria.getvalue()
        if st.session_state.get("hoja"):
            st.download_button(
                "Descargar la hoja de datos", data=st.session_state.hoja,
                file_name=resolucion.nombre_archivo("hoja-datos"),
                mime=MIME_WORD, width="stretch")
        st.dataframe(pd.DataFrame(filas_hoja,
                                  columns=["Sección", "Campo", "Valor"]),
                     width="stretch", height=300)

# --- Ajustes ----------------------------------------------------------------

with ajustes:
    seccion = ui.opcion("", "seccion_ajustes",
                        ["Configuración", "Plantillas", "Biblioteca",
                         "Etiquetas"], como_botones=True, horizontal=True)

    if seccion == "Configuración":
        with ui.bloque("⚙", "Datos del despacho"):
            st.caption("Se llenan una sola vez. Aparecen cerca de cincuenta "
                       "veces en una resolución.")
            with st.form("form_configuracion"):
                col1, col2 = st.columns(2)
                with col1:
                    nueva = Configuracion(
                        curaduria_numero=st.text_input(
                            "Curaduría No.", value=config.curaduria_numero),
                        municipio=st.text_input("Municipio",
                                                value=config.municipio),
                        departamento=st.text_input("Departamento",
                                                   value=config.departamento),
                        codigo_dane=st.text_input(
                            "Código DANE del municipio",
                            value=config.codigo_dane,
                            help="Primer segmento del expediente. "
                                 "Ibagué es 73001."))
                with col2:
                    nueva.curador = st.text_input("Nombre de quien firma",
                                                  value=config.curador)
                    nueva.genero_curador = "F" if st.radio(
                        "Tratamiento", ["Curadora Urbana", "Curador Urbano"],
                        index=0 if config.genero_curador == "F" else 1,
                        horizontal=True) == "Curadora Urbana" else "M"
                    nueva.encargado = st.checkbox("En provisionalidad (P)",
                                                  value=config.encargado)
                    nueva.sustanciador = st.text_input(
                        "Sustanciador(a)", value=config.sustanciador)
                    nueva.sustanciador_iniciales = st.text_input(
                        "Iniciales de quien proyecta",
                        value=config.sustanciador_iniciales,
                        placeholder="gilt /S")

                col1, col2, col3 = st.columns(3)
                with col1:
                    nueva.vigencia_meses = int(st.number_input(
                        "Vigencia (meses)", 1, 120, config.vigencia_meses))
                with col2:
                    nueva.prorroga_meses = int(st.number_input(
                        "Prórroga (meses)", 1, 120, config.prorroga_meses))
                with col3:
                    nueva.nombres_en_mayuscula = st.checkbox(
                        "Nombres en MAYÚSCULA",
                        value=config.nombres_en_mayuscula)
                    nueva.sugerir_sexo = st.checkbox(
                        "Sugerir el sexo por el nombre",
                        value=config.sugerir_sexo)

                if st.form_submit_button("GUARDAR LA CONFIGURACIÓN",
                                         type="primary", width="stretch"):
                    faltan = nueva.faltantes()
                    if faltan:
                        st.error("Falta: " + ", ".join(faltan))
                    else:
                        nueva.plantilla_preferida = config.plantilla_preferida
                        nueva.guardar()
                        st.session_state.configuracion = nueva
                        st.success("Guardada. No hay que volver a escribirla.")
                        st.rerun()

        if config.completa:
            with ui.bloque("✓", "Así se escribirá en el documento", gris=True):
                despacho = config.despacho()
                st.info(f"{despacho.tratamiento_largo} en ejercicio de las "
                        "funciones otorgadas por la Ley 388 de 1997 y el "
                        "Decreto Único Nacional 1077 de 2015 y,")
                st.caption(f"Firma: {config.curador} — {despacho.tratamiento}")

    elif seccion == "Plantillas":
        with ui.bloque("1", "Subir una plantilla"):
            subida = st.file_uploader(
                "Archivo .docx", type="docx",
                help="Si su plantilla es .doc (formato viejo), ábrala en Word "
                     "y use Archivo → Guardar como → Documento de Word.")
            if subida is not None and st.button("Guardar en la carpeta de "
                                                "plantillas", width="stretch"):
                RUTA_PLANTILLAS.mkdir(exist_ok=True)
                (RUTA_PLANTILLAS / subida.name).write_bytes(subida.getvalue())
                st.success(f"Guardada: {subida.name}")
                st.rerun()

        if origen_plantilla is not None:
            with ui.bloque("2", f"Revisar «{origen_plantilla.name}»"):
                try:
                    revision = auditar(motor.abrir(origen_plantilla))
                except Exception as error:
                    st.error(f"No pude leer la plantilla: {error}")
                    revision = None
                if revision is not None:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Etiquetas", len(revision.etiquetas))
                    col2.metric("Anclas", f"{len(revision.anclas)} de 5")
                    col3.metric("Espacios en blanco", len(revision.blancos))
                    if revision.etiquetas_desconocidas:
                        st.error("Etiquetas que la app no conoce: "
                                 + ", ".join(revision.etiquetas_desconocidas))
                    if revision.blancos or not revision.anclas:
                        st.warning("Esta plantilla todavía obliga a llenar "
                                   "cosas a mano.")
                        if st.button("PREPARARLA AUTOMÁTICAMENTE",
                                     type="primary", width="stretch"):
                            documento = motor.abrir(origen_plantilla)
                            informe_prep = preparar(
                                documento, valores_del_despacho(config))
                            memoria = io.BytesIO()
                            documento.save(memoria)
                            st.session_state.plantilla_lista = memoria.getvalue()
                            st.session_state.nombre_lista = \
                                f"{origen_plantilla.stem}_lista.docx"
                            st.session_state.informe_prep = \
                                informe_prep.resumen()
                            st.rerun()
                    else:
                        st.success("La plantilla está lista.")
                    if st.session_state.get("plantilla_lista"):
                        st.success(st.session_state.informe_prep)
                        st.download_button(
                            "Descargar la plantilla preparada",
                            data=st.session_state.plantilla_lista,
                            file_name=st.session_state.nombre_lista,
                            mime=MIME_WORD, width="stretch")
                        if st.button("Guardarla directamente en la carpeta",
                                     width="stretch"):
                            (RUTA_PLANTILLAS /
                             st.session_state.nombre_lista).write_bytes(
                                 st.session_state.plantilla_lista)
                            st.session_state.pop("plantilla_lista")
                            st.success("Guardada.")
                            st.rerun()

    elif seccion == "Biblioteca":
        with ui.bloque("+", "Guardar un párrafo propio"):
            with st.form("nuevo_bloque", clear_on_submit=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    titulo_nuevo = st.text_input("Título")
                with col2:
                    categoria_nueva = st.selectbox(
                        "Categoría", list(CATEGORIAS),
                        format_func=CATEGORIAS.get,
                        index=list(CATEGORIAS).index("notas"))
                texto_nuevo = st.text_area(
                    "Texto", height=150,
                    help="Puede usar etiquetas como {{nombres}} o "
                         "{{matricula}}.")
                nota_nueva = st.text_input("Cuándo se usa")
                if st.form_submit_button("GUARDAR EL PÁRRAFO", type="primary",
                                         width="stretch"):
                    if not titulo_nuevo.strip() or not texto_nuevo.strip():
                        st.error("Necesita título y texto.")
                    else:
                        creado = libreria.crear(titulo_nuevo, texto_nuevo,
                                                categoria_nueva, nota_nueva)
                        st.success(f"Guardado: {creado.titulo}")
                        st.rerun()

        busqueda = st.text_input("Buscar en la biblioteca",
                                 placeholder="plusvalía, valla, VIS…")
        encontrados = libreria.buscar(busqueda)
        st.caption(f"{len(encontrados)} de {len(libreria)} párrafos")
        for bloque_texto in encontrados[:40]:
            with st.expander(f"{bloque_texto.titulo}  ·  "
                             f"{CATEGORIAS.get(bloque_texto.categoria, '')}"):
                with st.form(f"editar_{bloque_texto.id}"):
                    texto_editado = st.text_area("Texto",
                                                 value=bloque_texto.texto,
                                                 height=180)
                    nota_editada = st.text_input("Cuándo se usa",
                                                 value=bloque_texto.nota)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Guardar cambios",
                                                 width="stretch"):
                            libreria.guardar(Bloque(
                                id=bloque_texto.id, titulo=bloque_texto.titulo,
                                categoria=bloque_texto.categoria,
                                texto=texto_editado, nota=nota_editada,
                                obligatorio=bloque_texto.obligatorio,
                                aplica_a=bloque_texto.aplica_a,
                                orden=bloque_texto.orden,
                                origen=bloque_texto.origen, activo=True))
                            st.success("Guardado.")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("Quitar del catálogo",
                                                 width="stretch"):
                            libreria.eliminar(bloque_texto.id)
                            st.rerun()

    else:
        st.caption("Las etiquetas que se pueden escribir en la plantilla de "
                   "Word, con el valor que tendrían ahora mismo.")
        solo_con_valor = st.checkbox("Solo las que ya tienen valor")
        st.dataframe(pd.DataFrame(
            [{"etiqueta": f"{{{{{clave}}}}}", "valor actual": valor}
             for clave, valor in sorted(etiquetas.items())
             if not solo_con_valor or valor]), width="stretch", height=520)
