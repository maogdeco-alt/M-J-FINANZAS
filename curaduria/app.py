"""Automatizador de resoluciones — formulario local en Streamlit.

Ejecutar:  streamlit run app.py

El formulario pide solo los datos generales de los que se deriva el resto del
documento. Lo que aparece una o dos veces en la resolución no se pide: sale en
el cuadro con raya para completarlo en Word.
"""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from curaduria import armado, formato
from curaduria import plantilla as motor
from curaduria.auditoria import auditar
from curaduria.bloques import CATEGORIAS, Biblioteca, Bloque
from curaduria.catalogo import GRUPOS, TRAMITES, USOS, Solicitud, tramites_por_grupo
from curaduria.configuracion import Configuracion
from curaduria.genero_nombres import sugerir_genero
from curaduria.gramatica import TIPOS_DOCUMENTO, Titular
from curaduria.preparacion import preparar
from curaduria.profesionales import ROLES, Profesional
from curaduria.resolucion import (CUBIERTAS, RESPONSABLES, SENTIDOS,
                                  Actuaciones, Inmueble, Notificacion,
                                  Resolucion, Responsable)

RUTA_PLANTILLAS = Path(__file__).parent / "plantillas"
CALIDADES = ("propietario", "poseedor", "titular")
SEXOS = ["Masculino", "Femenino"]

st.set_page_config(page_title="Resoluciones de Curaduría", page_icon="📄",
                   layout="wide")


# --- Estado -----------------------------------------------------------------

@st.cache_resource
def biblioteca() -> Biblioteca:
    return Biblioteca()


def configuracion() -> Configuracion:
    if "configuracion" not in st.session_state:
        st.session_state.configuracion = Configuracion.cargar()
    return st.session_state.configuracion


def inicializar() -> None:
    st.session_state.setdefault("titulares", pd.DataFrame([
        {"nombre": "", "sexo": "Masculino", "tipo_doc": "CC",
         "numero_doc": "", "calidad": "propietario"}]))
    st.session_state.setdefault("profesionales", pd.DataFrame([
        {"rol": rol, "nombre": "", "sexo": "Masculino", "documento": "",
         "matricula": ""}
        for rol in ("proyectista", "constructor")]))
    st.session_state.setdefault("bloques_elegidos", None)


inicializar()
libreria = biblioteca()
config = configuracion()


# --- Campos con normalización en vivo --------------------------------------

def campo(etiqueta: str, clave: str, normalizador=None, ayuda: str = "",
          marcador: str = "") -> str:
    """Campo de texto que se corrige solo al salir de él.

    Si alguien escribe la matrícula sin guion, la deja con guion; si escribe un
    nombre en minúscula, lo pasa a mayúscula. El mensaje debajo dice qué pasó.
    """
    def al_cambiar() -> None:
        if normalizador is None:
            return
        revision = normalizador(st.session_state.get(clave, ""))
        if revision.valor:
            st.session_state[clave] = revision.valor

    st.text_input(etiqueta, key=clave, help=ayuda or None,
                  placeholder=marcador or None, on_change=al_cambiar)
    bruto = st.session_state.get(clave, "")
    revision = (normalizador(bruto) if normalizador
                else formato.Revision(bruto, "bien" if bruto else "vacio"))
    if revision.mensaje:
        color = {"bien": "gray", "duda": "orange", "mal": "red"}.get(
            revision.estado, "gray")
        st.markdown(f"<small style='color:{color}'>{revision.icono} "
                    f"{revision.mensaje}</small>", unsafe_allow_html=True)
    return revision.valor


def leer_titulares(tabla: pd.DataFrame) -> tuple[list[Titular], list[str]]:
    """Convierte la tabla en titulares, normalizando, y reporta lo dudoso."""
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
            tipo_documento=tipo,
            numero_documento=revision_doc.valor,
            calidad=str(fila.get("calidad") or "propietario"),
        ))
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
            matricula=str(fila.get("matricula") or "").strip(),
        ))
    return profesionales


def valores_del_despacho(config: Configuracion) -> dict[str, str]:
    """Los datos del despacho que pueden estar escritos literalmente."""
    valores = {"curador": config.curador, "sustanciador": config.sustanciador,
               "municipio": config.municipio}
    return {clave: valor for clave, valor in valores.items() if valor.strip()}


def plantillas_disponibles() -> list[Path]:
    if not RUTA_PLANTILLAS.exists():
        return []
    return sorted(p for p in RUTA_PLANTILLAS.glob("*.docx")
                  if not p.name.startswith("~$"))


# --- Encabezado -------------------------------------------------------------

st.title("Automatizador de Resoluciones")
st.caption(f"{config.municipio} · Curaduría Urbana No. {config.curaduria_numero}"
           if config.completa else
           "Primero complete la configuración del despacho (última pestaña).")

# --- Barra lateral ----------------------------------------------------------

with st.sidebar:
    if config.completa:
        st.success(f"**{config.curador}**  \n{config.despacho().tratamiento}")
        st.caption(f"Sustancia: {config.sustanciador}")
    else:
        st.error("Configuración incompleta: falta "
                 + ", ".join(config.faltantes()))

    st.divider()
    st.subheader("Plantilla")
    subida = st.file_uploader(
        "Subir plantilla (.docx)", type="docx",
        help="Si su plantilla es .doc (formato viejo), ábrala en Word y use "
             "Archivo → Guardar como → Documento de Word (*.docx).")
    disponibles = plantillas_disponibles()
    elegida = None
    if disponibles:
        nombres = ["(usar la plantilla subida)"] + [p.name for p in disponibles]
        indice = 0 if subida else 1
        if config.plantilla_preferida in nombres and not subida:
            indice = nombres.index(config.plantilla_preferida)
        seleccion = st.selectbox("O una guardada", nombres, index=indice)
        if seleccion != nombres[0]:
            elegida = RUTA_PLANTILLAS / seleccion
    origen_plantilla = subida if subida is not None else elegida

    if origen_plantilla is not None:
        with st.expander("Revisar esta plantilla"):
            try:
                if hasattr(origen_plantilla, "seek"):
                    origen_plantilla.seek(0)
                revision_plantilla = auditar(motor.abrir(origen_plantilla))
            except Exception as error:
                st.error(f"No pude leer la plantilla: {error}")
            else:
                st.caption(revision_plantilla.resumen())
                if revision_plantilla.etiquetas_desconocidas:
                    st.error("Etiquetas que la app no conoce (quedarían "
                             "impresas tal cual): "
                             + ", ".join(
                                 f"`{{{{{c}}}}}`" for c in
                                 revision_plantilla.etiquetas_desconocidas))
                if revision_plantilla.anclas:
                    st.success("Anclas: " + ", ".join(
                        f"`{{{{{a}}}}}`" for a in revision_plantilla.anclas))
                else:
                    st.warning("Sin anclas de sección: los bloques no se "
                               "insertarán. Agregue `{{considerandos}}` y "
                               "`{{resuelve}}`.")
                if revision_plantilla.blancos:
                    st.warning(f"{len(revision_plantilla.blancos)} espacios se "
                               "llenarían a mano.")
                    st.dataframe(pd.DataFrame([
                        {"párrafo": h.parrafo, "en blanco": h.texto,
                         "contexto": h.contexto[-50:],
                         "sugerencia": f"{{{{{h.sugerencia}}}}}"
                                       if h.sugerencia else ""}
                        for h in revision_plantilla.blancos[:40]]),
                        width="stretch", height=220)

                necesita_preparar = bool(revision_plantilla.blancos) or not \
                    revision_plantilla.anclas
                if necesita_preparar and st.button("Preparar esta plantilla",
                                                   width="stretch"):
                    try:
                        if hasattr(origen_plantilla, "seek"):
                            origen_plantilla.seek(0)
                        documento = motor.abrir(origen_plantilla)
                        informe_preparacion = preparar(
                            documento, valores_del_despacho(config))
                        memoria_plantilla = io.BytesIO()
                        documento.save(memoria_plantilla)
                        memoria_plantilla.seek(0)
                    except Exception as error:
                        st.error(f"No pude preparar la plantilla: {error}")
                    else:
                        st.success(informe_preparacion.resumen())
                        if informe_preparacion.nota_estructura:
                            st.info(informe_preparacion.nota_estructura)
                        if informe_preparacion.pendientes:
                            st.caption(
                                f"{len(informe_preparacion.pendientes)} "
                                "espacios se quedan con la raya: no encontré "
                                "una etiqueta segura.")
                        nombre_base = getattr(origen_plantilla, "name",
                                              "plantilla")
                        nombre_base = Path(str(nombre_base)).stem
                        st.download_button(
                            "Descargar la plantilla lista",
                            data=memoria_plantilla,
                            file_name=f"{nombre_base}_lista.docx",
                            mime="application/vnd.openxmlformats-officedocument"
                                 ".wordprocessingml.document",
                            width="stretch",
                            help="Guárdela en la carpeta plantillas/ y "
                                 "elíjala aquí arriba.")

    st.divider()
    modo = st.radio("Cómo se arma el documento",
                    ["Plantilla + bloques", "Solo bloques (sin plantilla)",
                     "Solo plantilla (etiquetas)"])
    incluir_hoja = st.checkbox("Incluir la hoja de datos", value=True)

pestanas = st.tabs(["1 · Datos de la resolución", "2 · Bloques de texto",
                    "3 · Generar", "4 · Biblioteca", "5 · Configuración",
                    "6 · Etiquetas"])

# --- 1. Datos ---------------------------------------------------------------

with pestanas[0]:
    hueco_avance = st.container()

    with st.container(border=True):
        st.markdown("#### Qué se solicita")
        c1, c2 = st.columns([1, 2])
        with c1:
            grupo = st.selectbox("Grupo de trámite", list(GRUPOS),
                                 format_func=GRUPOS.get)
        with c2:
            tramite = st.selectbox("Trámite", tramites_por_grupo()[grupo],
                                   format_func=lambda t: t.nombre)
        if tramite.nota:
            st.caption(f"ℹ️ {tramite.nota}")

        modalidades_ids: list[str] = []
        if tramite.modalidades:
            etiqueta = ("Modalidades — se pueden combinar"
                        if tramite.modalidades_multiples else "Modalidad")
            elegidas = st.multiselect(
                etiqueta, tramite.modalidades, format_func=lambda m: m.nombre,
                max_selections=None if tramite.modalidades_multiples else 1)
            modalidades_ids = [m.id for m in elegidas]
            for modalidad in elegidas:
                if modalidad.nota:
                    st.caption(f"ℹ️ {modalidad.nombre}: {modalidad.nota}")

        usos_elegidos = st.multiselect("Destinación / uso", USOS,
                                       format_func=lambda u: u.nombre)
        solicitud = Solicitud(tramite.id, modalidades_ids,
                              [u.id for u in usos_elegidos])
        if solicitud.vivienda_interes:
            st.info(f"Proyecto **{solicitud.vivienda_interes}**: se activan los "
                    "bloques de vivienda de interés y la exención del IDU.")
        for problema in solicitud.errores():
            st.error(problema)

    with st.container(border=True):
        st.markdown("#### Identificación del acto")
        a1, a2, a3 = st.columns(3)
        with a1:
            numero = campo("Resolución No.", "numero", marcador="73001-2-26-0456")
            fecha = st.date_input("Fecha de la resolución", value=date.today(),
                                  format="DD/MM/YYYY")
        with a2:
            radicado = campo("Radicación No.", "radicado",
                             formato.normalizar_radicado, marcador="2600789")
            fecha_radicado = st.date_input("Fecha de radicación",
                                           value=date.today(),
                                           format="DD/MM/YYYY")
        with a3:
            consecutivo = campo(
                "Consecutivo del expediente", "consecutivo",
                formato.normalizar_consecutivo, marcador="54",
                ayuda="Solo el consecutivo: el número completo se arma con el "
                      "código DANE, la curaduría y el año.")
            sentido = st.selectbox("Sentido de la decisión", list(SENTIDOS),
                                   format_func=lambda s: SENTIDOS[s][1])

    with st.container(border=True):
        st.markdown("#### Titulares y quién radica")
        if st.button("Sugerir sexo por el nombre"):
            tabla = st.session_state.titulares.copy()
            for indice, fila in tabla.iterrows():
                nombre = str(fila.get("nombre") or "")
                if nombre.strip():
                    tabla.at[indice, "sexo"] = (
                        "Femenino" if sugerir_genero(nombre) == "F"
                        else "Masculino")
            st.session_state.titulares = tabla
            st.rerun()

        tabla_titulares = st.data_editor(
            st.session_state.titulares, num_rows="dynamic", width="stretch",
            key="editor_titulares",
            column_config={
                "nombre": st.column_config.TextColumn("Nombre completo",
                                                      width="large"),
                "sexo": st.column_config.SelectboxColumn(
                    "Sexo", options=SEXOS, required=True,
                    help="De aquí sale toda la concordancia del documento."),
                "tipo_doc": st.column_config.SelectboxColumn(
                    "Tipo", options=list(TIPOS_DOCUMENTO), required=True),
                "numero_doc": st.column_config.TextColumn("Número"),
                "calidad": st.column_config.SelectboxColumn(
                    "Calidad", options=list(CALIDADES), required=True),
            })
        st.session_state.titulares = tabla_titulares
        titulares, avisos_titulares = leer_titulares(tabla_titulares)
        for aviso in avisos_titulares:
            st.caption(f"⚠️ {aviso}")

        tipo_responsable = st.radio(
            "¿Quién radica la solicitud?", list(RESPONSABLES),
            format_func=RESPONSABLES.get, horizontal=False)
        responsable = Responsable(tipo_responsable)
        if tipo_responsable != "titular":
            r1, r2, r3 = st.columns(3)
            with r1:
                responsable.nombre = campo(
                    "Nombre de quien radica", "resp_nombre",
                    lambda t: formato.normalizar_nombre(
                        t, config.nombres_en_mayuscula))
            with r2:
                responsable.genero = "F" if st.radio(
                    "Sexo", SEXOS, horizontal=True,
                    key="resp_sexo") == "Femenino" else "M"
            with r3:
                responsable.documento = campo(
                    "Documento", "resp_doc", formato.normalizar_documento)

    inmueble = Inmueble(cubierta=CUBIERTAS[0])
    if tramite.requiere_predio:
        with st.container(border=True):
            st.markdown("#### Predio")
            p1, p2, p3 = st.columns(3)
            with p1:
                inmueble.matricula_inmobiliaria = campo(
                    "Matrícula inmobiliaria", "matricula",
                    formato.normalizar_matricula, marcador="350-250605",
                    ayuda="Puede escribirla sin guion: se corrige sola.")
            with p2:
                inmueble.ficha_catastral = campo(
                    "Ficha catastral", "ficha",
                    formato.normalizar_ficha_catastral,
                    marcador="01-09-1014-0013-000",
                    ayuda="Quince dígitos; los guiones se ponen solos.")
            with p3:
                inmueble.direccion = campo(
                    "Dirección del predio", "direccion",
                    formato.normalizar_direccion,
                    marcador="Carrera 2 Sur No. 28 - 57")
            inmueble.barrio = campo("Barrio", "barrio")

    modalidades = set(modalidades_ids)
    pide_areas = bool(modalidades & {"obra_nueva", "ampliacion", "adecuacion",
                                     "modificacion"}) or \
        tramite.id == "reconocimiento"
    pide_demolicion = bool(modalidades & {"demolicion_total",
                                          "demolicion_parcial"})
    pide_indices = bool(modalidades & {"obra_nueva", "ampliacion"})
    pide_edificacion = tramite.id in ("construccion", "reconocimiento")

    if pide_edificacion or pide_areas or pide_demolicion:
        with st.container(border=True):
            st.markdown("#### El proyecto")
            st.caption("Solo se piden las áreas que la modalidad elegida "
                       "necesita.")
            e1, e2, e3, e4 = st.columns(4)
            if pide_edificacion:
                with e1:
                    inmueble.pisos = int(st.number_input("Pisos", 0, 100, 0))
                with e2:
                    inmueble.cubierta = st.selectbox("Cubierta", CUBIERTAS)
            if pide_areas:
                with e3:
                    inmueble.area_lote = st.number_input(
                        "Área del lote (m²)", 0.0, step=0.01, format="%.2f")
                with e4:
                    inmueble.area_construida = st.number_input(
                        "Área construida (m²)", 0.0, step=0.01, format="%.2f")
            if pide_demolicion:
                d1, d2 = st.columns(2)
                with d1:
                    inmueble.area_demoler = st.number_input(
                        "Área a demoler (m²)", 0.0, step=0.01, format="%.2f")
                with d2:
                    inmueble.area_existente = st.number_input(
                        "Área existente (m²)", 0.0, step=0.01, format="%.2f")
            if pide_indices:
                i1, i2, i3, i4 = st.columns(4)
                with i1:
                    inmueble.indice_construccion_permitido = campo(
                        "I. construcción permitido", "icp",
                        formato.normalizar_indice)
                with i2:
                    inmueble.indice_construccion_propuesto = campo(
                        "I. construcción propuesto", "icr",
                        formato.normalizar_indice)
                with i3:
                    inmueble.indice_ocupacion_permitido = campo(
                        "I. ocupación permitido", "iop",
                        formato.normalizar_indice)
                with i4:
                    inmueble.indice_ocupacion_propuesto = campo(
                        "I. ocupación propuesto", "ior",
                        formato.normalizar_indice)
            if solicitud.vivienda_interes:
                inmueble.estrato = campo(
                    f"Estrato (lo pide el proyecto {solicitud.vivienda_interes})",
                    "estrato",
                    ayuda="Define la exención del IDU y las expensas.")

    with st.expander("Datos adicionales (opcionales)"):
        st.caption("Nada de esto es obligatorio. Lo que deje vacío sale en el "
                   "cuadro con una raya para completarlo en Word.")
        inmueble.tratamiento_urbanistico = campo(
            "Tratamiento urbanístico", "tratamiento")
        inmueble.uso_principal = campo("Uso principal del suelo", "uso_suelo")
        inmueble.amenaza_riesgo = campo(
            "Amenaza y riesgo", "amenaza",
            marcador="riesgo medio por remoción en masa")
        st.markdown("**Profesionales** — el título y el participio concuerdan "
                    "con el sexo: *la Arquitecta … identificada con*.")
        tabla_profesionales = st.data_editor(
            st.session_state.profesionales, num_rows="dynamic",
            width="stretch", key="editor_profesionales",
            column_config={
                "rol": st.column_config.SelectboxColumn(
                    "Rol", options=list(ROLES), required=True),
                "nombre": st.column_config.TextColumn("Nombre", width="large"),
                "sexo": st.column_config.SelectboxColumn(
                    "Sexo", options=SEXOS, required=True),
                "documento": st.column_config.TextColumn("CC"),
                "matricula": st.column_config.TextColumn("Matrícula profesional"),
            })
        st.session_state.profesionales = tabla_profesionales
        observaciones = st.text_area("Observaciones", height=80)
        notificado_nombre = campo(
            "Se notifica a", "notificado",
            lambda t: formato.normalizar_nombre(t, config.nombres_en_mayuscula))
        notificado_sexo = st.radio("Sexo de quien se notifica", SEXOS,
                                   horizontal=True, key="notif_sexo")

profesionales = leer_profesionales(st.session_state.profesionales)

resolucion = Resolucion(
    numero=numero, fecha=fecha, radicado=radicado,
    fecha_radicado=fecha_radicado, consecutivo_expediente=consecutivo,
    sentido=sentido, solicitud=solicitud, despacho=config.despacho(),
    titulares=titulares, responsable=responsable, inmueble=inmueble,
    profesionales=profesionales, actuaciones=Actuaciones(),
    notificacion=Notificacion(
        nombre=notificado_nombre,
        genero="F" if notificado_sexo == "Femenino" else "M"),
    vigencia_meses=config.vigencia_meses,
    prorroga_meses=config.prorroga_meses,
    observaciones=observaciones,
)

etiquetas = resolucion.etiquetas()
filas_hoja = armado.filas_hoja_datos(etiquetas, resolucion.secciones_hoja_datos())
estado = resolucion.estado_campos()
listos, total = resolucion.avance

# El indicador de avance, arriba del formulario que ya se construyó.
with hueco_avance:
    columna_barra, columna_resumen = st.columns([3, 2])
    with columna_barra:
        st.progress(listos / total if total else 0.0,
                    text=f"**{listos} de {total}** datos listos")
    with columna_resumen:
        pendientes = [c.nombre for c in estado if not c.listo and c.critico]
        if pendientes:
            st.markdown("Falta: **" + "** · **".join(pendientes[:4]) + "**"
                        + (f" y {len(pendientes) - 4} más"
                           if len(pendientes) > 4 else ""))
        else:
            st.markdown("**Listo para generar.**")
    with st.expander(f"Ver el detalle de los {total} datos"):
        for campo_estado in estado:
            st.markdown(
                f"{campo_estado.icono} **{campo_estado.nombre}** — "
                f"<small>{campo_estado.detalle}</small>",
                unsafe_allow_html=True)
        st.caption("✓ listo · ✕ falta · ○ opcional para este trámite")

# --- 2. Bloques -------------------------------------------------------------

with pestanas[1]:
    st.subheader("Qué párrafos lleva esta resolución")
    st.caption(f"Catálogo filtrado para **{tramite.nombre}**. Los obligatorios "
               "vienen marcados; desmarque lo que no aplique.")

    if st.session_state.bloques_elegidos is None:
        st.session_state.bloques_elegidos = {
            b.id for b in libreria.obligatorios(tramite.id)}

    accion1, accion2, accion3 = st.columns(3)
    with accion1:
        if st.button("Solo los obligatorios", width="stretch"):
            st.session_state.bloques_elegidos = {
                b.id for b in libreria.obligatorios(tramite.id)}
            st.rerun()
    with accion2:
        if st.button("Marcar todos", width="stretch"):
            st.session_state.bloques_elegidos = {
                b.id for b in libreria.para_tramite(tramite.id)}
            st.rerun()
    with accion3:
        st.metric("Bloques elegidos", len(st.session_state.bloques_elegidos))

    elegidos: set[str] = set()
    for categoria, bloques_categoria in libreria.por_categoria(
            tramite.id).items():
        with st.expander(f"{CATEGORIAS[categoria]} ({len(bloques_categoria)})",
                         expanded=categoria in ("encabezado", "resuelve")):
            for bloque in bloques_categoria:
                marcado = st.checkbox(
                    f"**{bloque.titulo}**"
                    + (" · obligatorio" if bloque.obligatorio else ""),
                    value=bloque.id in st.session_state.bloques_elegidos,
                    key=f"chk_{bloque.id}")
                if marcado:
                    elegidos.add(bloque.id)
                if bloque.nota:
                    st.caption(bloque.nota)
                faltan = bloque.faltantes(etiquetas)
                if marcado and faltan:
                    st.caption("⚠️ sin dato: "
                               + ", ".join(f"`{{{{{c}}}}}`"
                                           for c in faltan[:6]))
                with st.popover("Ver texto"):
                    for parrafo in bloque.render(etiquetas):
                        st.write(parrafo)
    st.session_state.bloques_elegidos = elegidos

bloques_elegidos = libreria.seleccion(st.session_state.bloques_elegidos)

# --- 3. Generar -------------------------------------------------------------

with pestanas[2]:
    st.subheader("Revisión y generación")

    errores = resolucion.errores()
    avisos = resolucion.advertencias()

    rev1, rev2 = st.columns([3, 2])
    with rev1:
        st.markdown("**Así queda redactado**")
        st.info(etiquetas["solicitante_frase"] + ", solicita "
                + etiquetas["tramite_completo"] + ".")
        if titulares:
            st.info(f"Notificar {etiquetas['contraccion_a']} "
                    f"{etiquetas['interesado']} {etiquetas['nombres']}, "
                    f"{etiquetas['quien']} {etiquetas['verbo_podra']} "
                    "interponer los recursos de ley.")
    with rev2:
        st.markdown("**Resumen**")
        st.write({
            "expediente": etiquetas["expediente"] or "(sin consecutivo)",
            "trámite": etiquetas["tramite_completo"],
            "destinación": etiquetas["destinacion"] or "(sin uso)",
            "titulares": f"{len(titulares)} "
                         f"({'plural' if len(titulares) > 1 else 'singular'})",
            "género": "femenino" if etiquetas["articulo"] == "la"
                      else "masculino",
            "bloques": len(bloques_elegidos),
        })

    for problema in errores:
        st.error(problema)
    for aviso in avisos:
        st.warning(aviso)

    necesita_plantilla = modo != "Solo bloques (sin plantilla)"
    if necesita_plantilla and origen_plantilla is None:
        st.warning("Elija una plantilla en la barra lateral, o cambie el modo "
                   "a 'Solo bloques'.")

    listo = (not errores and config.completa
             and (origen_plantilla is not None or not necesita_plantilla))
    if not config.completa:
        st.error("Complete la configuración del despacho (pestaña 5).")

    if st.button("Generar documento de Word", type="primary",
                 disabled=not listo, width="stretch"):
        try:
            memoria = io.BytesIO()
            hoja = filas_hoja if incluir_hoja else None
            if modo == "Solo bloques (sin plantilla)":
                documento, faltantes = armado.armar_desde_bloques(
                    bloques_elegidos, etiquetas, hoja,
                    subtitulo_hoja=resolucion.subtitulo_hoja_datos())
                informe = {"faltantes": faltantes}
            else:
                if hasattr(origen_plantilla, "seek"):
                    origen_plantilla.seek(0)
                documento = motor.abrir(origen_plantilla)
                usar = (bloques_elegidos if modo == "Plantilla + bloques"
                        else [])
                informe = armado.armar_sobre_plantilla(
                    documento, usar, etiquetas, hoja,
                    subtitulo_hoja=resolucion.subtitulo_hoja_datos())
                faltantes = informe["faltantes"]
            documento.save(memoria)
            memoria.seek(0)
        except Exception as error:
            st.exception(error)
        else:
            st.success("Documento generado.")
            if modo == "Plantilla + bloques":
                conteo = informe.get("bloques_por_seccion", {})
                st.caption(
                    "Bloques insertados — encabezado: "
                    f"{conteo.get('encabezado', 0)}, considerandos: "
                    f"{conteo.get('considerando', 0)}, resuelve: "
                    f"{conteo.get('resuelve', 0)}, cierre: "
                    f"{conteo.get('cierre', 0)}.")
                desviadas = informe.get("secciones_desviadas") or []
                if desviadas:
                    st.info("La plantilla no tiene el ancla de: "
                            + ", ".join(f"`{{{{{s}}}}}`" for s in desviadas)
                            + ". Esos bloques fueron al ancla vecina.")
                if informe.get("hoja_datos") == "inicio":
                    st.caption("La hoja de datos quedó al inicio. Con "
                               "`{{hoja_datos}}` en la plantilla queda donde "
                               "usted la ponga.")
            if faltantes:
                st.warning("Quedaron sin dato (se conservan tal cual, para "
                           "llenarlos en Word): "
                           + ", ".join(f"`{{{{{c}}}}}`"
                                       for c in sorted(faltantes)[:25]))
            st.download_button(
                "Descargar resolución", data=memoria,
                file_name=resolucion.nombre_archivo(),
                mime="application/vnd.openxmlformats-officedocument"
                     ".wordprocessingml.document", width="stretch")

    st.divider()
    st.markdown("**Hoja de datos por separado**")
    if st.button("Generar hoja de datos", width="stretch"):
        documento = armado.documento_hoja_datos(
            filas_hoja, "HOJA DE DATOS DEL EXPEDIENTE",
            resolucion.subtitulo_hoja_datos())
        memoria = io.BytesIO()
        documento.save(memoria)
        memoria.seek(0)
        st.download_button(
            "Descargar hoja de datos", data=memoria,
            file_name=resolucion.nombre_archivo("hoja-datos"),
            mime="application/vnd.openxmlformats-officedocument"
                 ".wordprocessingml.document", width="stretch")

    with st.expander("Ver el cuadro en pantalla"):
        st.dataframe(pd.DataFrame(filas_hoja,
                                  columns=["Sección", "Campo", "Valor"]),
                     width="stretch", height=400)

# --- 4. Biblioteca ----------------------------------------------------------

with pestanas[3]:
    st.subheader("Biblioteca de bloques")
    st.caption("Guarde aquí los párrafos que usa seguido. Lo que cree o ajuste "
               "queda en `biblioteca/bloques_usuario.json` y no se pierde al "
               "actualizar la app.")

    busqueda = st.text_input("Buscar en la biblioteca",
                             placeholder="plusvalía, valla, VIS…")
    encontrados = libreria.buscar(busqueda)
    st.caption(f"{len(encontrados)} de {len(libreria)} bloques")

    with st.form("nuevo_bloque", clear_on_submit=True):
        st.markdown("**Nuevo bloque**")
        n1, n2 = st.columns([2, 1])
        with n1:
            titulo_nuevo = st.text_input("Título")
        with n2:
            categoria_nueva = st.selectbox(
                "Categoría", list(CATEGORIAS), format_func=CATEGORIAS.get,
                index=list(CATEGORIAS).index("notas"))
        texto_nuevo = st.text_area(
            "Texto", height=160,
            help="Puede usar etiquetas como {{nombres}} o {{matricula}}.")
        nota_nueva = st.text_input("Nota de uso (cuándo aplica)")
        aplica_nuevo = st.multiselect(
            "Aplica a", [t.id for t in TRAMITES],
            format_func=lambda i: next(t.nombre for t in TRAMITES
                                       if t.id == i),
            help="Vacío = aplica a todos los trámites.")
        if st.form_submit_button("Guardar bloque"):
            if not titulo_nuevo.strip() or not texto_nuevo.strip():
                st.error("El bloque necesita título y texto.")
            else:
                creado = libreria.crear(titulo_nuevo, texto_nuevo,
                                        categoria_nueva, nota_nueva,
                                        aplica_nuevo or ["*"])
                st.success(f"Guardado como `{creado.id}`.")
                st.rerun()

    st.divider()
    for bloque in encontrados:
        with st.expander(
                f"{bloque.titulo} · {CATEGORIAS.get(bloque.categoria, '')}"
                + (" · obligatorio" if bloque.obligatorio else "")):
            st.caption(f"`{bloque.id}` · origen: {bloque.origen}"
                       + (f" · {bloque.nota}" if bloque.nota else ""))
            with st.form(f"editar_{bloque.id}"):
                texto_editado = st.text_area("Texto", value=bloque.texto,
                                             height=200, key=f"txt_{bloque.id}")
                e1, e2, e3 = st.columns(3)
                with e1:
                    categoria_editada = st.selectbox(
                        "Categoría", list(CATEGORIAS),
                        index=list(CATEGORIAS).index(bloque.categoria)
                        if bloque.categoria in CATEGORIAS else 0,
                        format_func=CATEGORIAS.get, key=f"cat_{bloque.id}")
                with e2:
                    obligatorio_editado = st.checkbox(
                        "Obligatorio", value=bloque.obligatorio,
                        key=f"obl_{bloque.id}")
                with e3:
                    orden_editado = st.number_input(
                        "Orden", 1, 999, bloque.orden, key=f"ord_{bloque.id}")
                nota_editada = st.text_input("Nota de uso", value=bloque.nota,
                                             key=f"nota_{bloque.id}")
                guardar, quitar = st.columns(2)
                with guardar:
                    if st.form_submit_button("Guardar cambios",
                                             width="stretch"):
                        libreria.guardar(Bloque(
                            id=bloque.id, titulo=bloque.titulo,
                            categoria=categoria_editada, texto=texto_editado,
                            nota=nota_editada, obligatorio=obligatorio_editado,
                            aplica_a=bloque.aplica_a, orden=int(orden_editado),
                            origen=bloque.origen, activo=True))
                        st.success("Guardado.")
                        st.rerun()
                with quitar:
                    if st.form_submit_button("Quitar del catálogo",
                                             width="stretch"):
                        libreria.eliminar(bloque.id)
                        st.warning("Bloque retirado.")
                        st.rerun()
            if bloque.etiquetas():
                st.caption("Etiquetas: " + ", ".join(
                    f"`{{{{{c}}}}}`" for c in bloque.etiquetas()))

    inactivos = [b for b in libreria.todos(incluir_inactivos=True)
                 if not b.activo]
    if inactivos:
        with st.expander(f"Bloques retirados ({len(inactivos)})"):
            for bloque in inactivos:
                if st.button(f"Restaurar «{bloque.titulo}»",
                             key=f"rest_{bloque.id}"):
                    libreria.activar(bloque.id)
                    st.rerun()

# --- 5. Configuración -------------------------------------------------------

with pestanas[4]:
    st.subheader("Configuración del despacho")
    st.caption("Se llena una sola vez. Estos datos aparecen cerca de cincuenta "
               "veces en una resolución y no tienen por qué volverse a "
               "digitar.")

    with st.form("form_configuracion"):
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Despacho**")
            nueva = Configuracion(
                curaduria_numero=st.text_input(
                    "Curaduría No.", value=config.curaduria_numero),
                municipio=st.text_input("Municipio", value=config.municipio),
                departamento=st.text_input("Departamento",
                                           value=config.departamento),
                codigo_dane=st.text_input(
                    "Código DANE del municipio", value=config.codigo_dane,
                    help="Primer segmento del expediente: 73001 es Ibagué."),
            )
        with g2:
            st.markdown("**Quién firma y quién sustancia**")
            nueva.curador = st.text_input("Nombre de quien firma",
                                          value=config.curador)
            nueva.genero_curador = "F" if st.radio(
                "Tratamiento", ["Curadora Urbana", "Curador Urbano"],
                index=0 if config.genero_curador == "F" else 1,
                horizontal=True) == "Curadora Urbana" else "M"
            nueva.encargado = st.checkbox("En provisionalidad (P)",
                                          value=config.encargado)
            nueva.sustanciador = st.text_input("Sustanciador(a)",
                                               value=config.sustanciador)
            nueva.sustanciador_iniciales = st.text_input(
                "Iniciales de quien proyecta",
                value=config.sustanciador_iniciales, placeholder="gilt /S")

        st.markdown("**Valores por defecto de cada resolución**")
        v1, v2, v3 = st.columns(3)
        with v1:
            nueva.vigencia_meses = int(st.number_input(
                "Vigencia (meses)", 1, 120, config.vigencia_meses))
        with v2:
            nueva.prorroga_meses = int(st.number_input(
                "Prórroga (meses)", 1, 120, config.prorroga_meses))
        with v3:
            plantillas = [""] + [p.name for p in plantillas_disponibles()]
            nueva.plantilla_preferida = st.selectbox(
                "Plantilla por defecto", plantillas,
                index=plantillas.index(config.plantilla_preferida)
                if config.plantilla_preferida in plantillas else 0)

        st.markdown("**Cómo capturar los datos**")
        nueva.nombres_en_mayuscula = st.checkbox(
            "Pasar los nombres a MAYÚSCULA", value=config.nombres_en_mayuscula,
            help="Como van en las resoluciones.")
        nueva.sugerir_sexo = st.checkbox(
            "Sugerir el sexo a partir del nombre", value=config.sugerir_sexo)

        if st.form_submit_button("Guardar configuración", type="primary"):
            faltan = nueva.faltantes()
            if faltan:
                st.error("Falta: " + ", ".join(faltan))
            else:
                destino = nueva.guardar()
                st.session_state.configuracion = nueva
                st.success(f"Guardada en `{destino.name}`. No hay que volver "
                           "a escribir estos datos.")
                st.rerun()

    if config.completa:
        st.divider()
        st.markdown("**Así se escribirá en el documento**")
        despacho = config.despacho()
        st.info(f"{despacho.tratamiento_largo} en ejercicio de las funciones "
                "otorgadas por la Ley 388 de 1997 y el Decreto Único Nacional "
                "1077 de 2015 y,")
        st.caption(f"Firma: {config.curador} — {despacho.tratamiento}  \n"
                   f"Expediente: {despacho.expediente(date.today().year, '54')}")

# --- 6. Etiquetas -----------------------------------------------------------

with pestanas[5]:
    st.subheader("Etiquetas disponibles")
    st.caption("Escríbalas en la plantilla de Word entre llaves dobles. La "
               "columna de la derecha muestra el valor con los datos de ahora.")
    con_valor = st.checkbox("Mostrar solo las que ya tienen valor")
    st.dataframe(pd.DataFrame(
        [{"etiqueta": f"{{{{{clave}}}}}", "valor actual": valor}
         for clave, valor in sorted(etiquetas.items())
         if not con_valor or valor]), width="stretch", height=560)
