# Automatizador de Resoluciones (Curaduría Urbana)

Mini-app local para armar resoluciones. Hace tres cosas:

1. **Un cuadro de datos** que se diligencia una sola vez por expediente, antes
   de que el sustanciador abra el Word.
2. **Una biblioteca de párrafos** con el texto de la plantilla modelo, marcado
   por tipo de trámite: se escoge qué considerandos aplican y se descarta el
   resto, en vez de borrar a mano media resolución.
3. **El Word armado y editable**, con el género, las fechas, los números en
   letras y el expediente ya resueltos.

El problema que resuelve: en una resolución de 30-40 páginas los mismos datos
se repiten decenas de veces y la concordancia de género se arrastra de la
resolución anterior. Aquí se digita una vez y concuerda solo.

> **¿Es la primera vez?** Siga [GUIA_DE_USO.md](GUIA_DE_USO.md): el paso a
> paso desde un PC sin nada instalado hasta la plantilla real de la curaduría
> funcionando, escrito para la sustanciadora.

## Instalación y arranque

### En Windows (lo normal en la oficina)

1. Instale Python 3.10 o superior desde [python.org](https://www.python.org/downloads/),
   **marcando la casilla "Add Python to PATH"** al instalarlo.
2. Doble clic en **`instalar.bat`** — una sola vez. Instala los componentes y
   crea la plantilla de ejemplo.
3. Doble clic en **`iniciar.bat`**. Abre solo en ese equipo, en
   `http://localhost:8501`.

`instalar.bat` termina corriendo `verificar.py`, que genera una resolución de
prueba completa: si pasa, la app sirve de verdad y no solo quedó instalada.

La ventana negra que queda abierta **es la app**: si se cierra, la app se
apaga. Minimícela, no la cierre.

### Para toda la oficina

En el equipo que hará de servidor, doble clic en **`iniciar_servidor.bat`**.
La ventana muestra la IP de ese equipo; los demás sustanciadores entran desde
su navegador a `http://esa-ip:8501`. No hay que instalar nada en los demás
equipos — solo necesitan el navegador.

Para que quede visible hay que permitir el puerto 8501 en el Firewall de
Windows del equipo servidor (Firewall → Reglas de entrada → Nueva regla →
Puerto → TCP 8501 → Permitir, solo para la red privada de la oficina).

### En Linux o macOS

```bash
cd curaduria
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python crear_plantilla_ejemplo.py
./iniciar.sh            # solo este equipo
./iniciar.sh --red      # visible para la oficina
```

## Dónde se aloja (y dónde no)

**Netlify, Vercel y GitHub Pages no sirven**, y no es cuestión de
configuración. Esos servicios alojan sitios estáticos y funciones de vida
corta; Streamlit es un proceso de Python que queda corriendo y mantiene un
WebSocket abierto con el navegador para re-ejecutar el script en cada clic.
Sin ese proceso vivo no hay app.

Además, estas resoluciones llevan cédulas, matrículas y direcciones de
ciudadanos, en expedientes **en trámite**. Alojarlas en un servicio público
las saca de la red de la curaduría y entra en el terreno de la Ley 1581 de
2012. El camino va para el otro lado: que no salgan de la oficina.

| Etapa | Dónde corre | Cuándo |
|---|---|---|
| **Local** | El PC de cada sustanciador | Para empezar. `iniciar.bat`. |
| **Red de la oficina** | Un PC de la curaduría | Centralizado: una sola biblioteca de bloques para todos. `iniciar_servidor.bat`. |
| **Servidor interno** | Servidor o VM de la entidad | Si crece: arranque automático, respaldo, usuarios. |

Es el **mismo código** en las tres: solo cambia la dirección de escucha. Se
empieza local sin botar trabajo.

### Si crece a servidor interno

Para que la app arranque sola con el equipo, sin que nadie tenga que entrar a
darle doble clic:

- **Windows**: con [NSSM](https://nssm.cc/) se registra como servicio
  (`nssm install Resoluciones`), apuntando a `python -m streamlit run app.py`.
  Alternativa sin instalar nada: Programador de tareas → al iniciar el
  sistema → ejecutar `iniciar_servidor.bat`.
- **Linux**: una unidad `systemd` con `Restart=always`.
- Detrás de Nginx o IIS como proxy inverso si quieren quitar el `:8501` de la
  dirección, o poner HTTPS con un certificado de la entidad.

### Cuando varios trabajan a la vez

Los formularios son **independientes por persona**: lo que digita una
sustanciadora no se le aparece a otra. La **biblioteca de bloques sí es
compartida**, que es justamente lo que se quiere: un párrafo que mejore una
persona queda disponible para todas. Los guardados se escriben de forma
atómica, así que dos guardados simultáneos no corrompen el archivo — en el
peor caso se pierde el último, nunca la biblioteca.

Lo que conviene respaldar: la carpeta `biblioteca/` y la carpeta
`plantillas/`. Es todo lo que la app guarda en disco.

## Uso

Las cinco pestañas siguen el orden de trabajo:

| Pestaña | Para qué |
|---|---|
| **1 · Datos de la resolución** | Los datos generales, con indicador de avance y corrección en vivo. |
| **2 · Bloques de texto** | Qué párrafos lleva *esta* resolución. El catálogo viene filtrado por trámite y marca los obligatorios. |
| **3 · Generar** | Revisión, validaciones y descarga del `.docx` (y de la hoja de datos por separado). |
| **4 · Biblioteca** | Crear, editar y retirar bloques. Lo suyo queda guardado. |
| **5 · Configuración** | Los datos del despacho. Se llenan una vez y no se vuelven a digitar. |
| **6 · Etiquetas** | Todas las etiquetas con su valor actual, para armar o corregir la plantilla. |

En la barra lateral van los datos del despacho (que no cambian entre
resoluciones), la plantilla y el modo de armado.

## Qué datos se piden (y qué no)

El formulario pide solo los datos **generales** de los que se deriva el resto
del documento. Un dato que aparece una o dos veces en el acto se escribe más
rápido en Word que en un formulario, así que no se pide: sale en el cuadro con
una raya.

### Nivel 0 — Se llenan una vez en la vida (pestaña 5)

Curaduría, municipio, departamento, código DANE, quién firma, su tratamiento,
quién sustancia y sus iniciales. En la plantilla modelo estos datos aparecen
cerca de **cincuenta veces**; quedan guardados en `configuracion.json` y no se
vuelven a digitar.

### Nivel 1 — Lo que se llena por resolución (pestaña 1)

| Dato | Qué deriva la app sola |
|---|---|
| Tipo de trámite | Nombre del acto y qué bloques aplican |
| Modalidad(es) | "en las modalidades de… y…", y qué áreas pedir |
| Destinación / uso | Detecta VIS/VIP y activa esos bloques |
| Resolución y fecha | La fecha en letras y el nombre del archivo |
| Radicado y fecha | Cuatro formatos de fecha a partir de uno |
| Consecutivo | El expediente completo: `73001-2-26-0054` |
| Titulares (nombre, sexo, documento) | **Toda la concordancia** del documento |
| Quién radica | La frase completa del considerando principal |
| Matrícula inmobiliaria | |
| Ficha catastral | |
| Dirección | |
| Pisos, cubierta y áreas | Las áreas en letras y en cifra |

**El formulario se encoge según el trámite.** Un concepto de uso del suelo no
pide pisos ni índices; una demolición pide el área a demoler; los índices solo
aparecen en obra nueva o ampliación; el estrato, solo si el proyecto es
VIS o VIP.

Arriba del formulario hay un indicador de **cuántos datos van listos** y
cuáles faltan, para no descubrirlo al final.

### Fuera del formulario

Oficios, autos, certificado IDU, factura, escritura, notaría, anotación del
folio, cantidad de planos y los profesionales. Están en *Datos adicionales
(opcionales)* por si se quieren aprovechar, pero lo que quede vacío sale en el
cuadro con raya para completarlo en Word.

## Corrección en vivo

Los campos se corrigen solos al salir de ellos, y debajo dicen qué pasó:

| Se escribe | Queda |
|---|---|
| `350250605` | `350-250605` |
| `010910140013000` | `01-09-1014-0013-000` |
| `maría gómez de rojas` | `MARÍA GÓMEZ DE ROJAS` |
| `79351573` | `79.351.573` |
| `cra 2 sur no 28-57` | `Carrera 2 Sur No. 28-57` |
| `2.600.789` | `2600789` |
| `54` (consecutivo) | `0054` |

Y avisa sin bloquear cuando algo se ve incompleto: una matrícula de cinco
dígitos, una ficha a la que le faltan siete, un NIT sin dígito de
verificación, un nombre sin apellido.

## Los tres modos de armado

- **Plantilla + bloques** (recomendado): la plantilla aporta la estructura y el
  formato; los bloques elegidos se insertan en sus anclas.
- **Solo bloques**: sin plantilla, el documento se construye completo desde el
  catálogo. Útil para un acto corto.
- **Solo plantilla**: el comportamiento clásico de rellenar etiquetas.

## El catálogo de trámites

Sigue el Decreto Único Nacional 1077 de 2015 y la Ley 388 de 1997, con la
distinción entre licencia, modalidad y uso, porque de ella depende qué bloques
tienen sentido:

- **Licencias urbanísticas**: Urbanización (desarrollo, saneamiento,
  reurbanización), Parcelación, Subdivisión (rústica, rural, urbana, loteo),
  Construcción y Intervención y Ocupación del Espacio Público.
- **Licencia de construcción**: las nueve modalidades independientes o
  combinables — obra nueva, ampliación, adecuación, modificación,
  restauración, reforzamiento estructural, demolición (total o parcial),
  reconstrucción y cerramiento.
- **Reconocimiento de la existencia de edificaciones**.
- **Otras actuaciones** (Art. 2.2.6.1.3.1): ajuste de cotas y áreas, planos de
  alinderamiento, modificación de urbanizaciones aceptadas, piscinas,
  movimiento de tierras, concepto de norma, concepto de uso del suelo, copias
  certificadas de planos, prórrogas, revalidaciones y modificación de licencia
  vigente.

La app valida las combinaciones: Subdivisión admite una sola modalidad por
acto, demolición total y parcial son excluyentes, y una licencia que exige
modalidad no se genera sin ella.

## La biblioteca de bloques

Son **59 bloques**. Los del catálogo salen de la plantilla modelo de
construcción, **con su texto jurídico textual** — no se reescribió nada. Cada
uno guarda tres datos que el Word no puede guardar: a qué trámites aplica, si
es obligatorio y una nota de cuándo se usa.

Organizados en: encabezado y solicitud · actuaciones del trámite · titularidad
y poderes · VIS/VIP · soportes · vecinos y terceros · soportes técnicos ·
normativa urbanística · plusvalía · expensas, IDU y exenciones · parte
resolutiva · cierre y notificación · notas propias.

Dos capas en disco:

- `biblioteca/bloques_base.json` — el catálogo de la curaduría, versionado con
  la app.
- `biblioteca/bloques_usuario.json` — lo que usted cree o ajuste. **No se
  pierde al actualizar la app**, y editar un bloque del catálogo nunca toca el
  archivo base.

Un bloque del catálogo no se borra: se retira y se puede restaurar. Los
propios sí se borran.

## La plantilla maestra

Un `.docx` de Word con etiquetas `{{nombre}}`. Para partir de un modelo:

```bash
python crear_plantilla_ejemplo.py     # -> plantillas/plantilla_maestra.docx
```

Las etiquetas funcionan en el cuerpo, en tablas, en encabezados y en pies, y
**se conserva el formato** (negrita, fuente, interlineado). Una etiqueta
partida en varios *runs* de Word —frecuente cuando se escribió con el
corrector encima— también se reemplaza bien.

### Anclas de sección

Marcan dónde entran los bloques:

| Ancla | Qué recibe |
|---|---|
| `{{encabezado}}` | El preámbulo de competencia. |
| `{{considerandos}}` | Todos los considerandos elegidos, en el orden del catálogo. |
| `{{resuelve}}` | Artículos y parágrafos. |
| `{{cierre}}` | Firma, notificación y pie de archivo. |
| `{{hoja_datos}}` | El cuadro de datos. Sin esta ancla, el cuadro encabeza el documento seguido de un salto de página. |

Si falta un ancla, sus bloques se suman a la vecina (el encabezado a los
considerandos, el cierre a la parte resolutiva) y la app lo informa: nada se
pierde en silencio.

## Etiquetas de datos

| Etiqueta | Ejemplo |
|---|---|
| `{{resolucion_numero}}`, `{{radicado}}`, `{{expediente}}` | `73001-2-26-0456`, `2600789`, `73001-2-26-0054` |
| `{{fecha}}`, `{{fecha_larga}}`, `{{fecha_letras}}` | `15/10/2026`, `15 de octubre de 2026`, `quince (15) de octubre de dos mil veintiséis (2026)` |
| `{{tramite_acto}}`, `{{modalidades}}`, `{{tramite_completo}}` | `Licencia de CONSTRUCCIÓN`, `en las modalidades de DEMOLICIÓN TOTAL y OBRA NUEVA` |
| `{{destinacion}}` | `VIVIENDA UNIFAMILIAR` |
| `{{nombres}}`, `{{documentos}}` | `MARÍA GÓMEZ y JUAN PÉREZ`, `CC 41.000.000 y CC 79.000.000` |
| `{{identificacion}}` | `MARÍA GÓMEZ, identificada con cédula de ciudadanía No. 41.000.000 y JUAN PÉREZ, identificado con…` |
| `{{solicitante_frase}}` | El apoderado si lo hay; si no, los titulares con su calidad. |
| `{{apoderado_identificacion}}` | `el señor JUAN PABLO VARGAS, identificado con CC. No. 1.110.454.615` |
| `{{direccion}}`, `{{barrio}}`, `{{municipio}}`, `{{estrato}}` | |
| `{{matricula}}`, `{{ficha_catastral}}`, `{{chip}}` | `350-250605`, `01-09-1014-0013-000` |
| `{{area_lote}}`, `{{area_lote_letras}}` | `150,00`, `ciento cincuenta m2 (150,00 m2)` |
| `{{area_construida_letras}}`, `{{area_demoler_letras}}` | |
| `{{pisos}}`, `{{pisos_cifra}}`, `{{cubierta}}` | `dos`, `2`, `teja` |
| `{{indice_ocupacion_permitido}}` / `_propuesto` | y los de construcción |
| `{{proyectista}}`, `{{estructural}}`, `{{constructor}}`, … | `la Arquitecta FERNANDA GARCÍA, identificada con CC No. 93.383.328 y con Matrícula Profesional No. 25700-55387` |
| `{{idu_certificado}}`, `{{factura_numero}}`, `{{auto_numero}}` | |
| `{{planos_arquitectonicos}}`, `{{tomos_memorias}}` | |
| `{{vigencia}}`, `{{prorroga}}` | `treinta y seis (36) meses` |
| `{{curador}}`, `{{curador_tratamiento}}`, `{{curador_tratamiento_largo}}` | `Curadora Urbana No. 2 de Ibagué (P)`, `La Curadora Urbana No. 2 del Municipio de Ibagué (P)` |
| `{{sustanciador}}`, `{{sustanciador_iniciales}}`, `{{notificado_nombre}}` | |

Cada fecha trae sus variantes `_larga`, `_letras`, `_dia`, `_mes`, `_anio`.
El número de expediente se arma como `73001-2-26-0054` con el código DANE, el
número de curaduría, el año del radicado y el consecutivo.

## Etiquetas gramaticales

Se resuelven con el sexo de los titulares y cuántos son. Con una titular mujer
`{{articulo}} {{propietario}}` sale "la propietaria"; con dos, "los
propietarios".

`{{articulo}}` · `{{articulo_indefinido}}` · `{{contraccion_de}}` (del / de la)
· `{{contraccion_a}}` (al / a la) · `{{tratamiento}}` (señor/señora) ·
`{{propietario}}` · `{{poseedor}}` · `{{apoderado}}` · `{{solicitante}}` ·
`{{titular}}` · `{{interesado}}` · `{{identificado}}` · `{{representado}}` ·
`{{notificado}}` · `{{obligado}}` · `{{citado}}` · `{{mismo}}` · `{{este}}` ·
`{{aquel}}` · `{{cuyo}}` · `{{pronombre}}` · `{{quien}}` · `{{posesivo}}` ·
`{{documento}}` · y los verbos `{{verbo_ser}}` · `{{verbo_obrar}}` ·
`{{verbo_solicitar}}` · `{{verbo_presentar}}` · `{{verbo_deber}}` ·
`{{verbo_podra}}` · `{{verbo_acreditar}}` · `{{verbo_actuar}}` ·
`{{verbo_aportar}}`.

Cada una tiene su versión capitalizada para inicio de párrafo:
`{{Articulo}}`, `{{Propietario}}`, `{{Quien}}`…

### Reglas aplicadas

- Un titular → singular con su género. Varios → plural; grupo mixto →
  masculino genérico (`los propietarios`), como manda la concordancia.
- Persona jurídica (NIT) → "identificada con NIT…", que concuerda con "la
  sociedad". El NIT conserva su dígito de verificación.
- Los documentos se escriben con puntos de miles: `28.514.217`.
- Los profesionales concuerdan por separado: "la Arquitecta … identificada
  con", "el Ingeniero Civil … identificado con".
- Nombres y documentos se enumeran en lenguaje natural: `A`, `A y B`,
  `A, B y C`.
- El sexo se **sugiere** por el nombre de pila (botón *Sugerir sexo por
  nombre*) y queda editable: es una ayuda, no una decisión.

## Validaciones

Bloquean la generación:

- Número y fecha de la resolución, y nombre de quien firma.
- Al menos un titular, con nombre y documento; sin documentos repetidos.
- Nombre y documento de quien radica, si no es el propio titular; y que haya
  una persona jurídica si se indicó representante legal.
- Matrícula inmobiliaria con la forma `350-123456` y ficha catastral
  `01-09-1014-0013-000`.
- Modalidad indicada cuando el trámite la exige, sin combinaciones inválidas.
- Área a demoler si hay demolición total; área construida si hay obra nueva.
- Índice propuesto que no supere el permitido.
- Profesional sin matrícula.
- Radicado posterior a la resolución, o legal y debida forma anterior al
  radicado.

Avisan sin bloquear: titulares de distinto sexo, proyecto VIS/VIP sin estrato,
predio con amenaza o riesgo, expediente sin consecutivo, y la falta del
proyectista o del constructor (que son opcionales: salen con raya).

## Arquitectura

```
curaduria/
├── GUIA_DE_USO.md              paso a paso para la sustanciadora
├── instalar.bat                instalación por una sola vez (Windows)
├── iniciar.bat                 arranca la app en este equipo
├── iniciar_servidor.bat        arranca la app para la oficina
├── verificar.py                comprueba la instalación de punta a punta
├── revisar_plantilla.py        audita una plantilla antes de usarla
├── respaldar.bat               copia biblioteca y plantillas
├── app.py                      formulario Streamlit (solo UI)
├── crear_plantilla_ejemplo.py  genera la plantilla con anclas
├── curaduria/
│   ├── configuracion.py        Nivel 0: los datos del despacho
│   ├── formato.py              normalización y avisos de los campos
│   ├── catalogo.py             trámites, modalidades y usos (Decreto 1077)
│   ├── bloques.py              biblioteca de párrafos y su persistencia
│   ├── armado.py               hoja de datos e inserción en el Word
│   ├── resolucion.py           modelo, validaciones y etiquetas
│   ├── profesionales.py        roles y concordancia de títulos
│   ├── gramatica.py            concordancia de género y número
│   ├── numeros.py              números a letras, formato de cifras
│   ├── fechas.py               fechas de acto administrativo
│   ├── auditoria.py            revisión de plantillas
│   ├── genero_nombres.py       sugerencia de sexo por nombre
│   └── plantilla.py            relleno de .docx conservando formato
├── biblioteca/                 bloques base y los suyos
├── plantillas/                 sus plantillas maestras .docx
└── tests/                      212 pruebas, sin Streamlit
```

La lógica no depende de Streamlit: `app.py` solo recoge datos y llama al
paquete `curaduria`. Eso permite reutilizarla desde un script o un proceso por
lotes sin tocar la interfaz.

## Herramientas de línea de comandos

```bash
python verificar.py                              # ¿quedó bien la instalación?
python revisar_plantilla.py plantillas/x.docx    # ¿está lista esta plantilla?
python crear_plantilla_ejemplo.py                # plantilla modelo con anclas
./respaldar.sh                                   # copia biblioteca y plantillas
```

`revisar_plantilla.py` es la herramienta para convertir una plantilla real:
reporta las etiquetas mal escritas (que quedarían impresas en la resolución),
si tiene las anclas de sección, y **cada espacio en blanco manual con la
etiqueta que sugiere poner en su lugar**. Lo mismo se ve dentro de la app, en
la barra lateral → *Revisar esta plantilla*.

## Pruebas

```bash
pip install pytest
python -m pytest tests -q
```

## Datos y privacidad

Todo corre en la máquina local: la app no envía datos a ningún servicio. Los
documentos se entregan por el navegador y no se guardan en disco salvo que
usted los descargue. Lo único que se escribe es su biblioteca de bloques.
