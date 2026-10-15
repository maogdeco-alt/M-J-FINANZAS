"""Automatizador de resoluciones — formulario local en Streamlit.

Ejecutar:  streamlit run app.py
"""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from curaduria import armado
from curaduria import plantilla as motor
from curaduria.auditoria import auditar
from curaduria.bloques import CATEGORIAS, Biblioteca, Bloque
from curaduria.catalogo import (GRUPOS, TRAMITES, USOS, Solicitud,
                                tramites_por_grupo)
from curaduria.genero_nombres import sugerir_genero
from curaduria.gramatica import TIPOS_DOCUMENTO, Titular
from curaduria.profesionales import ETIQUETA_ROL, ROLES, Profesional
from curaduria.resolucion import (CUBIERTAS, SENTIDOS, Actuaciones, Apoderado,
                                  Despacho, Inmueble, Notificacion, Resolucion)

RUTA_PLANTILLAS = Path(__file__).parent / "plantillas"
CALIDADES = ("propietario", "poseedor", "apoderado", "solicitante", "titular")

st.set_page_config(page_title="Resoluciones de Curaduría", page_icon="📄",
                   layout="wide")


# --- Estado -----------------------------------------------------------------

@st.cache_resource
def biblioteca() -> Biblioteca:
    return Biblioteca()


def inicializar() -> None:
    st.session_state.setdefault("titulares", pd.DataFrame([
        {"nombre": "", "sexo": "Masculino", "tipo_doc": "CC",
         "numero_doc": "", "calidad": "propietario"}]))
    st.session_state.setdefault("profesionales", pd.DataFrame([
        {"rol": rol, "nombre": "", "sexo": "Masculino", "documento": "",
         "matricula": ""}
        for rol in ("proyectista", "estructural", "suelos", "constructor")]))
    st.session_state.setdefault("bloques_elegidos", None)


inicializar()
libreria = biblioteca()


def leer_titulares(tabla: pd.DataFrame) -> list[Titular]:
    titulares: list[Titular] = []
    for _, fila in tabla.iterrows():
        nombre = str(fila.get("nombre") or "").strip()
        if not nombre and not str(fila.get("numero_doc") or "").strip():
            continue
        titulares.append(Titular(
            nombre=nombre,
            genero="F" if str(fila.get("sexo")).startswith("Fem") else "M",
            tipo_documento=str(fila.get("tipo_doc") or "CC"),
            numero_documento=str(fila.get("numero_doc") or "").strip(),
            calidad=str(fila.get("calidad") or "propietario"),
        ))
    return titulares


def leer_profesionales(tabla: pd.DataFrame) -> list[Profesional]:
    profesionales: list[Profesional] = []
    for _, fila in tabla.iterrows():
        nombre = str(fila.get("nombre") or "").strip()
        if not nombre:
            continue
        profesionales.append(Profesional(
            rol=str(fila.get("rol") or "proyectista"),
            nombre=nombre,
            genero="F" if str(fila.get("sexo")).startswith("Fem") else "M",
            documento=str(fila.get("documento") or "").strip(),
            matricula=str(fila.get("matricula") or "").strip(),
        ))
    return profesionales


def plantillas_disponibles() -> list[Path]:
    if not RUTA_PLANTILLAS.exists():
        return []
    return sorted(p for p in RUTA_PLANTILLAS.glob("*.docx")
                  if not p.name.startswith("~$"))


# --- Encabezado -------------------------------------------------------------

st.title("📄 Automatizador de Resoluciones")
st.caption("Los datos se digitan una vez. El género, las fechas y los números "
           "en letras se resuelven solos; los párrafos salen del catálogo.")

with st.sidebar:
    st.header("Despacho")
    curaduria_numero = st.text_input("Curaduría No.", value="2")
    municipio = st.text_input("Municipio", value="Ibagué")
    departamento = st.text_input("Departamento", value="Tolima")
    codigo_dane = st.text_input("Código DANE del municipio", value="73001",
                                help="Primer segmento del expediente.")
    curador = st.text_input("Nombre de quien firma")
    genero_curador = st.radio("Tratamiento", ["Curadora Urbana", "Curador Urbano"],
                              horizontal=True)
    encargado = st.checkbox("En provisionalidad (P)", value=True)
    sustanciador = st.text_input("Sustanciador(a)")
    sustanciador_iniciales = st.text_input("Iniciales de quien proyecta",
                                           placeholder="gilt /S")

    st.divider()
    st.header("Plantilla")
    subida = st.file_uploader(
        "Subir plantilla (.docx)", type="docx",
        help="Si su plantilla es .doc (formato viejo), ábrala en Word y use "
             "Archivo → Guardar como → Documento de Word (*.docx).")
    disponibles = plantillas_disponibles()
    elegida = None
    if disponibles:
        nombres = ["(usar la plantilla subida)"] + [p.name for p in disponibles]
        seleccion = st.selectbox("O una guardada", nombres,
                                 index=0 if subida else 1)
        if seleccion != nombres[0]:
            elegida = RUTA_PLANTILLAS / seleccion
    origen_plantilla = subida if subida is not None else elegida

    if origen_plantilla is not None:
        with st.expander("Revisar esta plantilla"):
            try:
                if hasattr(origen_plantilla, "seek"):
                    origen_plantilla.seek(0)
                informe_plantilla = auditar(motor.abrir(origen_plantilla))
            except Exception as error:
                st.error(f"No pude leer la plantilla: {error}")
            else:
                st.caption(informe_plantilla.resumen())
                if informe_plantilla.etiquetas_desconocidas:
                    st.error(
                        "Etiquetas que la app no conoce (quedarían impresas "
                        "tal cual): "
                        + ", ".join(f"`{{{{{c}}}}}`" for c in
                                    informe_plantilla.etiquetas_desconocidas))
                if informe_plantilla.anclas:
                    st.success("Anclas: "
                               + ", ".join(f"`{{{{{a}}}}}`"
                                           for a in informe_plantilla.anclas))
                else:
                    st.warning(
                        "Sin anclas de sección: los bloques no se insertarán. "
                        "Agregue `{{considerandos}}` y `{{resuelve}}` donde "
                        "deban ir.")
                if informe_plantilla.blancos:
                    st.warning(
                        f"{len(informe_plantilla.blancos)} espacios se "
                        "llenarían a mano. Cámbielos por la etiqueta "
                        "sugerida:")
                    st.dataframe(pd.DataFrame([
                        {"párrafo": h.parrafo, "en blanco": h.texto,
                         "contexto": h.contexto[-60:],
                         "sugerencia": f"{{{{{h.sugerencia}}}}}"
                                       if h.sugerencia else ""}
                        for h in informe_plantilla.blancos[:40]]),
                        width="stretch", height=240)

    modo = st.radio(
        "Cómo se arma el documento",
        ["Plantilla + bloques", "Solo bloques (sin plantilla)",
         "Solo plantilla (etiquetas)"],
        help="Con 'Plantilla + bloques', los bloques se insertan donde la "
             "plantilla tenga {{considerandos}} y {{resuelve}}.",
    )
    incluir_hoja = st.checkbox("Incluir la hoja de datos en el documento",
                               value=True)

despacho = Despacho(
    curaduria_numero=curaduria_numero, municipio=municipio,
    departamento=departamento, codigo_dane=codigo_dane, curador=curador,
    genero_curador="F" if genero_curador == "Curadora Urbana" else "M",
    encargado=encargado, sustanciador=sustanciador,
    sustanciador_iniciales=sustanciador_iniciales,
)

pestanas = st.tabs(["1 · Hoja de datos", "2 · Bloques de texto",
                    "3 · Generar", "4 · Biblioteca", "5 · Etiquetas"])

# --- 1. Hoja de datos -------------------------------------------------------

with pestanas[0]:
    st.subheader("Información general fija del expediente")
    st.caption("Este es el cuadro que se diligencia antes de empezar a trabajar "
               "el archivo. Lo que quede en blanco sale con una raya para "
               "completar a mano.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Acto**")
        numero = st.text_input("Resolución No.")
        fecha = st.date_input("Fecha de la resolución", value=date.today(),
                              format="DD/MM/YYYY")
        radicado = st.text_input("Radicación No.", placeholder="2600789")
        fecha_radicado = st.date_input("Fecha de radicación", value=date.today(),
                                       format="DD/MM/YYYY")
        consecutivo = st.text_input("Consecutivo del expediente",
                                    placeholder="54",
                                    help="Se arma como 73001-2-26-0054.")
        expediente_manual = st.text_input("…o expediente completo a mano",
                                          placeholder="73001-2-26-0054")
        usar_debida_forma = st.checkbox("Registrar legal y debida forma")
        fecha_debida_forma = st.date_input(
            "Legal y debida forma", value=date.today(), format="DD/MM/YYYY",
            disabled=not usar_debida_forma)

    with col2:
        st.markdown("**Trámite**")
        agrupados = tramites_por_grupo()
        grupo = st.selectbox("Grupo", list(GRUPOS), format_func=GRUPOS.get)
        opciones = agrupados[grupo]
        tramite = st.selectbox("Trámite", opciones, format_func=lambda t: t.nombre)
        if tramite.nota:
            st.caption(f"ℹ️ {tramite.nota}")
        modalidades_ids: list[str] = []
        if tramite.modalidades:
            etiqueta = ("Modalidades (combinables)" if tramite.modalidades_multiples
                        else "Modalidad")
            elegidas = st.multiselect(
                etiqueta, tramite.modalidades, format_func=lambda m: m.nombre,
                max_selections=None if tramite.modalidades_multiples else 1)
            modalidades_ids = [m.id for m in elegidas]
        usos_elegidos = st.multiselect("Destinación / uso", USOS,
                                       format_func=lambda u: u.nombre)
        sentido = st.selectbox("Sentido de la decisión", list(SENTIDOS),
                               format_func=lambda s: SENTIDOS[s][1])

    with col3:
        st.markdown("**Vigencia y cierre**")
        vigencia_meses = st.number_input("Vigencia (meses)", 1, 120, 36)
        prorroga_meses = st.number_input("Prórroga (meses)", 1, 120, 12)
        notificado_nombre = st.text_input("Se notifica a")
        notificado_sexo = st.radio("Sexo de quien se notifica",
                                   ["Masculino", "Femenino"], horizontal=True)
        notificado_doc = st.text_input("Documento de quien se notifica")
        notificado_calidad = st.selectbox(
            "Calidad", ["apoderado", "titular", "tercero interviniente"])

    solicitud = Solicitud(tramite.id, modalidades_ids,
                          [u.id for u in usos_elegidos])

    st.divider()
    st.markdown("**Titulares**")
    st.caption("El sexo se sugiere por el nombre; verifíquelo. Con varios "
               "titulares el texto pasa a plural automáticamente.")
    if st.button("Sugerir sexo por nombre"):
        tabla = st.session_state.titulares.copy()
        for indice, fila in tabla.iterrows():
            nombre = str(fila.get("nombre") or "")
            if nombre.strip():
                tabla.at[indice, "sexo"] = (
                    "Femenino" if sugerir_genero(nombre) == "F" else "Masculino")
        st.session_state.titulares = tabla
        st.rerun()

    tabla_titulares = st.data_editor(
        st.session_state.titulares, num_rows="dynamic", width="stretch",
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
        })
    st.session_state.titulares = tabla_titulares
    titulares = leer_titulares(tabla_titulares)

    col_ap1, col_ap2, col_ap3 = st.columns(3)
    with col_ap1:
        apoderado_nombre = st.text_input("Apoderado del trámite")
    with col_ap2:
        apoderado_sexo = st.radio("Sexo del apoderado",
                                  ["Masculino", "Femenino"], horizontal=True)
    with col_ap3:
        apoderado_doc = st.text_input("Documento del apoderado")

    st.divider()
    st.markdown("**Predio y proyecto**")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        direccion = st.text_input("Dirección")
        barrio = st.text_input("Barrio")
        matricula = st.text_input("Matrícula inmobiliaria",
                                  placeholder="350-250605")
        ficha = st.text_input("Ficha catastral",
                              placeholder="01-09-1014-0013-000")
    with p2:
        chip = st.text_input("CHIP")
        estrato = st.text_input("Estrato")
        tratamiento_urbanistico = st.text_input("Tratamiento urbanístico")
        uso_principal = st.text_input("Uso principal del suelo")
    with p3:
        area_lote = st.number_input("Área del lote (m²)", 0.0, step=0.01,
                                    format="%.2f")
        area_construida = st.number_input("Área construida (m²)", 0.0, step=0.01,
                                          format="%.2f")
        area_demoler = st.number_input("Área a demoler (m²)", 0.0, step=0.01,
                                       format="%.2f")
        area_existente = st.number_input("Área existente (m²)", 0.0, step=0.01,
                                         format="%.2f")
    with p4:
        pisos = st.number_input("Pisos", 0, 100, 0)
        cubierta = st.selectbox("Cubierta", CUBIERTAS)
        amenaza_riesgo = st.text_input("Amenaza y riesgo",
                                       placeholder="riesgo medio por remoción")
        parqueaderos = st.text_input("Parqueaderos")

    i1, i2, i3, i4, i5 = st.columns(5)
    with i1:
        ic_permitido = st.text_input("I. construcción permitido")
    with i2:
        ic_propuesto = st.text_input("I. construcción propuesto")
    with i3:
        io_permitido = st.text_input("I. ocupación permitido")
    with i4:
        io_propuesto = st.text_input("I. ocupación propuesto")
    with i5:
        areas_por_piso = st.text_input("Áreas por piso",
                                       placeholder="PRIMER PISO de 113,50 m²…")

    st.divider()
    st.markdown("**Profesionales**")
    st.caption("El título y el participio concuerdan con el sexo: "
               "'la Arquitecta … identificada con'.")
    tabla_profesionales = st.data_editor(
        st.session_state.profesionales, num_rows="dynamic", width="stretch",
        key="editor_profesionales",
        column_config={
            "rol": st.column_config.SelectboxColumn(
                "Rol", options=list(ROLES), required=True,
                help="Define el título profesional que se escribe."),
            "nombre": st.column_config.TextColumn("Nombre", width="large"),
            "sexo": st.column_config.SelectboxColumn(
                "Sexo", options=["Masculino", "Femenino"], required=True),
            "documento": st.column_config.TextColumn("CC"),
            "matricula": st.column_config.TextColumn("Matrícula profesional"),
        })
    st.session_state.profesionales = tabla_profesionales
    profesionales = leer_profesionales(tabla_profesionales)

    with st.expander("Actuaciones del trámite (oficios, autos, planos)"):
        a1, a2, a3 = st.columns(3)
        with a1:
            reparto_numero = st.text_input("Consecutivo de reparto")
            folio_anotacion = st.text_input("Anotación del folio")
            escritura_numero = st.text_input("Escritura pública No.")
            escritura_notaria = st.text_input("Notaría",
                                              placeholder="Notaría Séptima")
            acta_oficio = st.text_input("Acta de observaciones — oficio")
        with a2:
            respuesta_oficio = st.text_input("Respuesta a observaciones — radicado")
            auto_numero = st.text_input("Auto No.")
            viabilidad_oficio = st.text_input("Oficio de viabilidad")
            idu_certificado = st.text_input("Certificado IDU")
            idu_valor = st.text_input("Valor del IDU")
        with a3:
            factura_numero = st.text_input("Factura No.")
            valla_radicado = st.text_input("Radicado de la valla")
            planos_arq = st.number_input("Planos arquitectónicos", 0, 999, 0)
            planos_est = st.number_input("Planos estructurales", 0, 999, 0)
            tomos_memorias = st.number_input("Tomos de memorias", 0, 99, 0)
            tomos_suelos = st.number_input("Tomos de estudio de suelos", 0, 99, 0)

    observaciones = st.text_area("Observaciones libres", height=80)

resolucion = Resolucion(
    numero=numero, fecha=fecha, radicado=radicado,
    fecha_radicado=fecha_radicado, consecutivo_expediente=consecutivo,
    expediente_manual=expediente_manual, sentido=sentido, solicitud=solicitud,
    despacho=despacho, titulares=titulares,
    apoderado=Apoderado(
        nombre=apoderado_nombre,
        genero="F" if apoderado_sexo == "Femenino" else "M",
        documento=apoderado_doc),
    inmueble=Inmueble(
        direccion=direccion, barrio=barrio, matricula_inmobiliaria=matricula,
        ficha_catastral=ficha, chip=chip, estrato=estrato,
        area_lote=area_lote, area_construida=area_construida,
        area_demoler=area_demoler, area_existente=area_existente,
        pisos=int(pisos), cubierta=cubierta,
        tratamiento_urbanistico=tratamiento_urbanistico,
        uso_principal=uso_principal,
        indice_construccion_permitido=ic_permitido,
        indice_construccion_propuesto=ic_propuesto,
        indice_ocupacion_permitido=io_permitido,
        indice_ocupacion_propuesto=io_propuesto,
        areas_por_piso=areas_por_piso, parqueaderos=parqueaderos,
        amenaza_riesgo=amenaza_riesgo),
    profesionales=profesionales,
    actuaciones=Actuaciones(
        reparto_numero=reparto_numero,
        fecha_debida_forma=fecha_debida_forma if usar_debida_forma else None,
        folio_anotacion=folio_anotacion, escritura_numero=escritura_numero,
        escritura_notaria=escritura_notaria,
        acta_observaciones_oficio=acta_oficio,
        respuesta_observaciones_oficio=respuesta_oficio,
        auto_numero=auto_numero, viabilidad_oficio=viabilidad_oficio,
        idu_certificado=idu_certificado, idu_valor=idu_valor,
        factura_numero=factura_numero, valla_radicado=valla_radicado,
        planos_arquitectonicos=int(planos_arq),
        planos_estructurales=int(planos_est),
        tomos_memorias=int(tomos_memorias), tomos_suelos=int(tomos_suelos)),
    notificacion=Notificacion(
        nombre=notificado_nombre,
        genero="F" if notificado_sexo == "Femenino" else "M",
        documento=notificado_doc, calidad=notificado_calidad),
    vigencia_meses=int(vigencia_meses), prorroga_meses=int(prorroga_meses),
    observaciones=observaciones,
)

etiquetas = resolucion.etiquetas()
filas_hoja = armado.filas_hoja_datos(etiquetas, resolucion.secciones_hoja_datos())

# --- 2. Bloques -------------------------------------------------------------

with pestanas[1]:
    st.subheader("Qué párrafos lleva esta resolución")
    st.caption(f"Catálogo filtrado para **{tramite.nombre}**. Los obligatorios "
               "vienen marcados; desmarque lo que no aplique al caso.")

    por_categoria = libreria.por_categoria(tramite.id)
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
    for categoria, bloques_categoria in por_categoria.items():
        with st.expander(f"{CATEGORIAS[categoria]} ({len(bloques_categoria)})",
                         expanded=categoria in ("encabezado", "resuelve")):
            for bloque in bloques_categoria:
                marcado = st.checkbox(
                    f"**{bloque.titulo}**" + (" · obligatorio"
                                              if bloque.obligatorio else ""),
                    value=bloque.id in st.session_state.bloques_elegidos,
                    key=f"chk_{bloque.id}")
                if marcado:
                    elegidos.add(bloque.id)
                if bloque.nota:
                    st.caption(bloque.nota)
                faltan = bloque.faltantes(etiquetas)
                if marcado and faltan:
                    st.caption("⚠️ sin dato: "
                               + ", ".join(f"`{{{{{c}}}}}`" for c in faltan[:6]))
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
    col_rev1, col_rev2 = st.columns(2)
    with col_rev1:
        st.markdown("**Así queda redactado**")
        st.info(etiquetas["solicitante_frase"] + ", solicita "
                + etiquetas["tramite_completo"] + ".")
        if titulares:
            st.info(f"Notificar {etiquetas['contraccion_a']} "
                    f"{etiquetas['interesado']} {etiquetas['nombres']}, "
                    f"{etiquetas['quien']} {etiquetas['verbo_podra']} interponer "
                    "los recursos de ley.")
        for profesional in profesionales[:2]:
            st.info(profesional.frase())
    with col_rev2:
        st.markdown("**Resumen**")
        st.write({
            "expediente": etiquetas["expediente"] or "(sin consecutivo)",
            "trámite": etiquetas["tramite_completo"],
            "destinación": etiquetas["destinacion"] or "(sin uso)",
            "número gramatical": "plural" if len(titulares) > 1 else "singular",
            "género": "femenino" if etiquetas["articulo"] == "la" else "masculino",
            "bloques": len(bloques_elegidos),
        })

    for problema in errores:
        st.error(problema)
    for aviso in avisos:
        st.warning(aviso)

    necesita_plantilla = modo != "Solo bloques (sin plantilla)"
    if necesita_plantilla and origen_plantilla is None:
        st.warning("Elija una plantilla en la barra lateral, o cambie el modo a "
                   "'Solo bloques'.")

    listo = not errores and (origen_plantilla is not None
                             or not necesita_plantilla)
    if st.button("⚙️ Generar documento de Word", type="primary",
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
                usar_bloques = (bloques_elegidos
                                if modo == "Plantilla + bloques" else [])
                informe = armado.armar_sobre_plantilla(
                    documento, usar_bloques, etiquetas, hoja,
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
                st.caption("Bloques insertados — encabezado: "
                           f"{conteo.get('encabezado', 0)}, considerandos: "
                           f"{conteo.get('considerando', 0)}, resuelve: "
                           f"{conteo.get('resuelve', 0)}, cierre: "
                           f"{conteo.get('cierre', 0)}.")
                desviadas = informe.get("secciones_desviadas") or []
                if desviadas:
                    st.info(
                        "La plantilla no tiene el ancla de: "
                        + ", ".join(f"`{{{{{s}}}}}`" for s in desviadas)
                        + ". Esos bloques se insertaron en el ancla vecina. "
                        "Agregue las etiquetas si los quiere en otro lugar.")
                sin_ancla = [a for a in informe.get("anclas_faltantes", [])
                             if a not in desviadas]
                if sin_ancla and not any(informe.get(f"ancla_{a}")
                                         for a in ("encabezado", "considerandos",
                                                   "resuelve", "cierre")):
                    st.warning(
                        "La plantilla no tiene ninguna ancla de bloques "
                        "(`{{considerandos}}`, `{{resuelve}}`): solo se "
                        "rellenaron las etiquetas de datos.")
                if informe.get("hoja_datos") == "inicio":
                    st.caption("La hoja de datos quedó al inicio, antes del "
                               "acto. Con `{{hoja_datos}}` en la plantilla "
                               "queda donde usted la ponga.")
            if faltantes:
                st.warning("Quedaron sin dato (se conservan tal cual): "
                           + ", ".join(f"`{{{{{c}}}}}`"
                                       for c in sorted(faltantes)[:25]))
            st.download_button("⬇️ Descargar resolución", data=memoria,
                               file_name=resolucion.nombre_archivo(),
                               mime="application/vnd.openxmlformats-officedocument"
                                    ".wordprocessingml.document",
                               width="stretch")

    st.divider()
    st.markdown("**Hoja de datos por separado**")
    st.caption("El cuadro solo, para diligenciar o imprimir antes de empezar.")
    if st.button("Generar hoja de datos", width="stretch"):
        documento = armado.documento_hoja_datos(
            filas_hoja, "HOJA DE DATOS DEL EXPEDIENTE",
            resolucion.subtitulo_hoja_datos())
        memoria = io.BytesIO()
        documento.save(memoria)
        memoria.seek(0)
        st.download_button("⬇️ Descargar hoja de datos", data=memoria,
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
            categoria_nueva = st.selectbox("Categoría", list(CATEGORIAS),
                                           format_func=CATEGORIAS.get,
                                           index=list(CATEGORIAS).index("notas"))
        texto_nuevo = st.text_area(
            "Texto", height=160,
            help="Puede usar etiquetas como {{nombres}} o {{matricula}}; "
                 "se reemplazan al generar.")
        nota_nueva = st.text_input("Nota de uso (cuándo aplica)")
        aplica_nuevo = st.multiselect(
            "Aplica a", [t.id for t in TRAMITES],
            format_func=lambda i: next(t.nombre for t in TRAMITES if t.id == i),
            help="Vacío = aplica a todos los trámites.")
        if st.form_submit_button("Guardar bloque"):
            if not titulo_nuevo.strip() or not texto_nuevo.strip():
                st.error("El bloque necesita título y texto.")
            else:
                creado = libreria.crear(
                    titulo_nuevo, texto_nuevo, categoria_nueva, nota_nueva,
                    aplica_nuevo or ["*"])
                st.success(f"Guardado como `{creado.id}`.")
                st.rerun()

    st.divider()
    for bloque in encontrados:
        with st.expander(f"{bloque.titulo} · {CATEGORIAS.get(bloque.categoria, '')}"
                         + (" · obligatorio" if bloque.obligatorio else "")):
            st.caption(f"`{bloque.id}` · origen: {bloque.origen}"
                       + (f" · nota: {bloque.nota}" if bloque.nota else ""))
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
                    if st.form_submit_button("Guardar cambios", width="stretch"):
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
                        st.warning("Bloque retirado del catálogo.")
                        st.rerun()
            if bloque.etiquetas():
                st.caption("Etiquetas: "
                           + ", ".join(f"`{{{{{c}}}}}`"
                                       for c in bloque.etiquetas()))

    inactivos = [b for b in libreria.todos(incluir_inactivos=True)
                 if not b.activo]
    if inactivos:
        with st.expander(f"Bloques retirados ({len(inactivos)})"):
            for bloque in inactivos:
                if st.button(f"Restaurar «{bloque.titulo}»",
                             key=f"rest_{bloque.id}"):
                    libreria.activar(bloque.id)
                    st.rerun()

# --- 5. Etiquetas -----------------------------------------------------------

with pestanas[4]:
    st.subheader("Etiquetas disponibles")
    st.caption("Escríbalas en la plantilla de Word entre llaves dobles. "
               "La columna de la derecha muestra el valor con los datos de "
               "ahora, para verificar antes de generar.")
    con_valor = st.checkbox("Mostrar solo las que ya tienen valor")
    filas = [{"etiqueta": f"{{{{{clave}}}}}", "valor actual": valor}
             for clave, valor in sorted(etiquetas.items())
             if not con_valor or valor]
    st.dataframe(pd.DataFrame(filas), width="stretch", height=560)
