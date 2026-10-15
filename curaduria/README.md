# Automatizador de Resoluciones (Curaduría)

Mini-app local: un formulario web que recoge los datos fijos de una resolución
(matrículas, documentos, áreas, fechas), **resuelve la concordancia de género y
número por sí solo** y genera el Word 100% editable a partir de una plantilla
maestra.

El problema que resuelve: en una resolución de 30-40 páginas los mismos datos
se repiten decenas de veces, y cada repetición es una oportunidad de error de
digitación. Aquí se digitan una vez.

## Instalación

```bash
cd curaduria
python -m venv .venv && source .venv/bin/activate   # opcional
pip install -r requirements.txt
```

## Uso

```bash
streamlit run app.py
```

Se abre en `http://localhost:8501`. Flujo:

1. En la barra lateral, elija la plantilla maestra (o súbala).
2. Llene los cinco bloques del formulario: acto, curaduría, titulares, predio,
   proyecto.
3. Revise el bloque **6. Revisión**: muestra cómo quedará redactado el texto y
   qué género/número se aplicó. Si falta algo, lo señala en rojo.
4. **Generar resolución en Word** → **Descargar .docx**.

## La plantilla maestra

Es un `.docx` normal de Word con etiquetas `{{nombre}}` donde van los datos
variables. Para partir de un modelo con todas las etiquetas puestas:

```bash
python crear_plantilla_ejemplo.py
# -> plantillas/plantilla_maestra.docx
```

Abra ese archivo, pegue el texto real de sus resoluciones y conserve las
etiquetas. Las etiquetas funcionan en el cuerpo, en tablas, en encabezados y en
pies de página, y **se conserva el formato** (negrita, fuente, interlineado).
Una etiqueta partida en varios *runs* de Word —algo frecuente cuando se la
escribió con el corrector encima— también se reemplaza bien.

La app lista todas las etiquetas con su valor actual en el panel final, y avisa
si la plantilla usa una etiqueta para la que no hay dato (la deja intacta en
lugar de borrarla silenciosamente).

### Etiquetas de datos

| Etiqueta | Ejemplo |
|---|---|
| `{{resolucion_numero}}`, `{{radicado}}` | `01-2-0456` |
| `{{fecha}}`, `{{fecha_larga}}`, `{{fecha_letras}}` | `15/10/2026`, `15 de octubre de 2026`, `quince (15) de octubre de dos mil veintiséis (2026)` |
| `{{fecha_radicado}}` y sus variantes | igual que arriba |
| `{{nombres}}` | `JUAN PÉREZ y MARÍA GÓMEZ` |
| `{{documentos}}` | `CC 79000000 y CC 41000000` |
| `{{identificacion}}` | `JUAN PÉREZ, identificado con cédula de ciudadanía No. 79.000.000 y MARÍA GÓMEZ, identificada con…` |
| `{{calidad}}` | `en calidad de propietarios` |
| `{{direccion}}`, `{{barrio}}`, `{{municipio}}`, `{{departamento}}` | |
| `{{matricula}}`, `{{cedula_catastral}}`, `{{chip}}` | |
| `{{area_lote}}`, `{{area_lote_letras}}` | `120,50`, `ciento veinte con cincuenta m2 (120,50 m2)` |
| `{{area_construida}}`, `{{area_construida_letras}}` | |
| `{{pisos}}`, `{{pisos_cifra}}` | `dos`, `2` |
| `{{vigencia}}` | `treinta y seis (36) meses` |
| `{{curaduria}}`, `{{curador}}`, `{{curador_tratamiento}}` | `Curadora Urbana` |
| `{{proyectista}}`, `{{matricula_profesional}}`, `{{observaciones}}` | |

### Etiquetas gramaticales

Se resuelven a partir del sexo de los titulares y de cuántos son. Con una
titular mujer `{{articulo}} {{propietario}}` sale "la propietaria"; con dos
titulares, "los propietarios".

`{{articulo}}` · `{{articulo_indefinido}}` · `{{contraccion_de}}` (del / de la) ·
`{{contraccion_a}}` (al / a la) · `{{tratamiento}}` (señor/señora) ·
`{{tratamiento_abrev}}` · `{{propietario}}` · `{{poseedor}}` · `{{apoderado}}` ·
`{{solicitante}}` · `{{titular}}` · `{{interesado}}` · `{{identificado}}` ·
`{{representado}}` · `{{notificado}}` · `{{obligado}}` · `{{citado}}` ·
`{{mismo}}` · `{{este}}` · `{{aquel}}` · `{{cuyo}}` · `{{pronombre}}` ·
`{{quien}}` · `{{posesivo}}` · `{{documento}}` · y los verbos
`{{verbo_ser}}` · `{{verbo_obrar}}` · `{{verbo_solicitar}}` ·
`{{verbo_presentar}}` · `{{verbo_deber}}` · `{{verbo_podra}}` ·
`{{verbo_acreditar}}` · `{{verbo_actuar}}` · `{{verbo_aportar}}`.

Cada una tiene su versión capitalizada para inicio de párrafo: `{{Articulo}}`,
`{{Propietario}}`, `{{Quien}}`…

### Reglas aplicadas

- Un solo titular → singular, con el género de esa persona.
- Varios titulares → plural; si el grupo es mixto, masculino genérico
  (`los propietarios`), como manda la concordancia del español.
- Persona jurídica (NIT) → se identifica en femenino ("identificada con NIT…"),
  porque concuerda con "la sociedad".
- Los nombres y documentos se enumeran en lenguaje natural: `A`, `A y B`,
  `A, B y C`.
- El sexo se **sugiere** a partir del nombre de pila (botón *Sugerir sexo por
  nombre*), pero siempre queda editable: la sugerencia es una ayuda, no una
  decisión.

## Validaciones antes de generar

El botón de generar está bloqueado hasta que no haya: número y fecha de
resolución, al menos un titular con nombre y documento, y matrícula
inmobiliaria. Además avisa si un documento está repetido entre titulares o si
el radicado quedó con fecha posterior a la resolución.

## Arquitectura

```
curaduria/
├── app.py                      formulario Streamlit (solo UI)
├── crear_plantilla_ejemplo.py  genera la plantilla de muestra
├── curaduria/
│   ├── gramatica.py            concordancia de género y número, titulares
│   ├── numeros.py              números a letras, formato de cifras
│   ├── fechas.py               fechas de acto administrativo
│   ├── plantilla.py            relleno de .docx conservando formato
│   └── resolucion.py           modelo y diccionario de etiquetas
├── plantillas/                 sus plantillas maestras .docx
└── tests/                      pruebas de la lógica (sin Streamlit)
```

La lógica no depende de Streamlit: `app.py` solo recoge datos y los pasa al
paquete `curaduria`. Eso permite reutilizarla desde un script o un lote sin
tocar la interfaz.

## Pruebas

```bash
pip install pytest
python -m pytest tests -q
```

## Datos y privacidad

Todo corre en la máquina local: la app no envía datos a ningún servicio. Los
documentos generados se entregan por el navegador y no se guardan en disco
salvo que usted los descargue.
