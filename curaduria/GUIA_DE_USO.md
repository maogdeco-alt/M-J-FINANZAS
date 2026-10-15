# Guía paso a paso — Etapa 1: en el PC de la sustanciadora

Esta guía va desde un computador en el que no hay nada instalado hasta la
primera resolución generada, y luego hasta la plantilla real de la curaduría
funcionando. No supone conocimientos de programación.

Tiempo estimado: **40 minutos la primera vez** (instalación incluida). Después,
arrancar la app es un doble clic.

---

## Parte A — Instalación (una sola vez)

### Paso 1. Instalar Python

1. Entre a **https://www.python.org/downloads/** y descargue la versión para
   Windows.
2. Ejecute el instalador. **En la primera pantalla, marque la casilla
   "Add python.exe to PATH"** (abajo). Es el paso que más se olvida y sin él
   nada funciona.
3. Haga clic en *Install Now* y espere.

> Si Python ya estaba instalado, no lo reinstale. Siga al paso 2; si falla,
> vuelva aquí y use *Modify* para marcar la casilla del PATH.

### Paso 2. Poner la carpeta de la app en el PC

Copie la carpeta `curaduria` completa a un lugar estable, por ejemplo
`C:\Resoluciones`. **No la deje en el Escritorio ni en Descargas**: ahí se
borra por accidente.

### Paso 3. Instalar la app

Doble clic en **`instalar.bat`**.

Se abre una ventana negra que descarga los componentes, crea la plantilla de
ejemplo y comprueba que todo quedó bien. Al final debe decir:

```
  Instalacion completa. Ahora puede usar iniciar.bat
```

Si en cambio dice `[FALLA]` en alguna línea, ahí mismo dice el remedio. El
caso más común es *"Python no está instalado o no quedó en el PATH"*: vuelva
al paso 1 y marque la casilla.

### Paso 4. Comprobar

Doble clic en **`verificar.py`**, o en la ventana negra escriba
`python verificar.py`. Debe salir una lista de `[ok]` y al final
*"Todo en orden"*. Esta comprobación genera una resolución de prueba completa,
así que si pasa, la app sirve de verdad.

---

## Parte B — La primera resolución (15 minutos)

### Paso 5. Arrancar

Doble clic en **`iniciar.bat`**. Se abre el navegador en
`http://localhost:8501`.

**La ventana negra que queda abierta es la app.** Si la cierra, la app se
apaga. Minimícela.

Para cerrar la app al final del día: cierre esa ventana, o presione
`Ctrl + C` dentro de ella.

### Paso 6. Llenar los datos del despacho (una vez)

En la **barra lateral izquierda**, llene lo que no cambia entre resoluciones:
curaduría, municipio, departamento, código DANE, nombre de quien firma,
tratamiento (Curadora / Curador), si está en provisionalidad, nombre de la
sustanciadora y sus iniciales.

> Estos datos se vuelven a escribir cada vez que se arranca la app. Si quiere
> dejarlos fijos para siempre, dígalo y se precargan en el código: es un
> cambio de dos minutos.

### Paso 7. Pestaña 1 · Hoja de datos

Llene el cuadro en el orden en que viene, que es el orden en que se lee el
expediente:

1. **Acto** — número de resolución, fechas, radicado y el *consecutivo del
   expediente*. El número completo (`73001-2-26-0054`) se arma solo con el
   código DANE, la curaduría, el año del radicado y ese consecutivo.
2. **Trámite** — grupo, trámite, modalidades (en construcción se pueden
   marcar varias) y destinación.
3. **Vigencia y cierre** — meses de vigencia y prórroga, y a quién se
   notifica.
4. **Titulares** — una fila por persona. El botón *Sugerir sexo por nombre*
   lo propone; **verifíquelo siempre**. Con dos o más titulares todo el texto
   pasa a plural solo.
5. **Predio** — dirección, matrícula, ficha catastral, estrato, áreas, pisos,
   índices.
6. **Profesionales** — una fila por profesional, con su rol. El título y el
   participio concuerdan solos: *"la Arquitecta … identificada con"*.
7. **Actuaciones** (desplegable) — oficios, autos, IDU, factura, cantidad de
   planos. Lo que no tenga, déjelo vacío.

### Paso 8. Pestaña 2 · Bloques de texto

Aquí se decide qué párrafos lleva **esta** resolución. El catálogo viene
filtrado según el trámite que eligió y los obligatorios ya están marcados.

- *Solo los obligatorios* → deja lo mínimo del acto.
- Vaya abriendo las categorías y marque lo que aplique al caso: ¿hubo citación
  a vecinos? ¿intervino un tercero? ¿es VIS? ¿quedó exento del IDU?
- Debajo de cada bloque hay una nota de cuándo se usa, y *Ver texto* muestra
  el párrafo ya con los datos del expediente puestos.
- Si un bloque marcado le falta un dato, se lo avisa ahí mismo
  (`⚠️ sin dato: {{...}}`).

### Paso 9. Pestaña 3 · Generar

Arriba se ve cómo quedó redactado y el resumen. Abajo:

- En **rojo** lo que impide generar (falta un dato obligatorio, una cifra
  incoherente). El botón queda bloqueado hasta resolverlo.
- En **amarillo** lo que conviene revisar pero no bloquea.

Clic en **⚙️ Generar documento de Word** → **⬇️ Descargar resolución**.

El archivo cae en Descargas con el nombre
`Resolucion_<número>_<fecha>.docx`. Ábralo en Word y termine las precisiones
propias de la solicitud: **el documento es 100% editable**.

El botón *Generar hoja de datos* produce el cuadro solo, para imprimir o
adjuntar al expediente.

---

## Parte C — Pasar la plantilla real de la curaduría

La app trae una plantilla de ejemplo. Lo que sigue es cambiarla por la de la
curaduría. **Este es el paso que más tiempo toma y el que más rinde.**

### Paso 10. Convertir el .doc a .docx

La plantilla modelo está en `.doc`, el formato viejo de Word, que la app no
puede leer.

1. Ábrala en Word.
2. **Archivo → Guardar como → Documento de Word (*.docx)**.
3. Guárdela dentro de la carpeta `plantillas` de la app.

### Paso 11. Revisarla

En la ventana negra, escriba:

```
python revisar_plantilla.py plantillas\NOMBRE_DE_SU_PLANTILLA.docx
```

Le va a reportar tres cosas:

- **Etiquetas que la app no conoce** — normalmente son errores de escritura
  (`{{matrikula}}`). Tal como están quedarían *impresas* en la resolución.
  Corríjalas.
- **Anclas de sección** — si dicen `no`, los bloques no se insertan (vea el
  paso 12).
- **Espacios en blanco** — cada `XXXX`, `____` o `XX de ___ de 2026` que
  quedó, con el número de párrafo y **la etiqueta que sugiere poner en su
  lugar**.

En la plantilla modelo de construcción hay **100 espacios en blanco**, de los
cuales 49 son fechas. Cada uno es una digitación manual que se puede eliminar.

Lo mismo se puede ver dentro de la app: barra lateral → *Revisar esta
plantilla*.

### Paso 12. Convertir los blancos en etiquetas

En Word, reemplace cada espacio por la etiqueta sugerida. Por ejemplo:

| Antes (se llena a mano) | Después (se llena solo) |
|---|---|
| `Matrícula Inmobiliaria No. ________` | `Matrícula Inmobiliaria No. {{matricula}}` |
| `el XX de ______ de 2026` | `el {{fecha_larga}}` |
| `Ficha Catastral No. ________` | `Ficha Catastral No. {{ficha_catastral}}` |
| `consecutivo No. 0XXX` | `consecutivo No. {{reparto_numero}}` |

La lista completa de etiquetas, con el valor que tendrían ahora mismo, está en
la **pestaña 5 · Etiquetas** de la app. Úsela como diccionario mientras edita.

**Consejo:** hágalo por partes. Convierta primero el encabezado, el
considerando de la solicitud y el artículo 1 —que es donde se concentran los
datos repetidos—, pruebe, y siga. No intente convertir las 16 páginas de una
sentada.

### Paso 13. Poner las anclas de sección

Para que los bloques de la pestaña 2 se inserten, la plantilla necesita cuatro
marcas. En el lugar correspondiente del documento, escriba en un párrafo
propio:

| Escriba esto | Donde va |
|---|---|
| `{{encabezado}}` | Donde está el párrafo de *"en ejercicio de las funciones…"* |
| `{{considerandos}}` | Debajo del título **CONSIDERANDO**, borrando los párrafos que ahora están ahí |
| `{{resuelve}}` | Debajo del título **RESUELVE**, borrando los artículos |
| `{{cierre}}` | Donde va la firma y la notificación |

Suena drástico borrar los párrafos: **no se pierden**, están en la biblioteca
de bloques, y desde ahí se escogen uno por uno según el caso. Eso es
exactamente lo que ahorra el trabajo de borrar media resolución cada vez.

Si prefiere no tocar la estructura todavía, deje la plantilla sin anclas y use
el modo **"Solo plantilla (etiquetas)"** en la barra lateral: la app solo
rellena los datos. Es un paso intermedio perfectamente válido.

### Paso 14. Volver a revisar

```
python revisar_plantilla.py plantillas\NOMBRE_DE_SU_PLANTILLA.docx
```

Repita hasta que diga *"La plantilla está lista"*.

---

## Parte D — Dejarla a punto para el día a día

### Paso 15. Guardar sus propios bloques

Pestaña **4 · Biblioteca**. Cada vez que escriba un párrafo que va a volver a
usar, guárdelo ahí con una nota de cuándo aplica. Queda disponible en la
pestaña 2 para las siguientes resoluciones.

También puede corregir el texto de los bloques del catálogo: su versión se
guarda aparte y **no se pierde** cuando la app se actualice.

### Paso 16. Respaldar

Doble clic en **`respaldar.bat`** de vez en cuando (una vez a la semana está
bien). Copia `biblioteca` y `plantillas` a `respaldos\AAAA-MM-DD`.

Lleve esa carpeta a la carpeta compartida o a una USB. Es **lo único** que la
app guarda en disco: con eso, si el PC se daña, no se pierde nada del trabajo
de armar la biblioteca.

---

## Si algo sale mal

| Qué pasa | Qué hacer |
|---|---|
| *"Python no se reconoce como un comando"* | No quedó en el PATH. Reinstale Python marcando *"Add python.exe to PATH"*. |
| El navegador dice *"No se puede acceder a este sitio"* | La ventana negra se cerró. Doble clic en `iniciar.bat` otra vez. |
| La app se ve en blanco o rara | Recargue con `Ctrl + F5`. |
| *"Address already in use"* o *"puerto en uso"* | Ya hay una copia corriendo. Use la pestaña que ya está abierta, o cierre la otra ventana negra. |
| La plantilla no aparece en la lista | Debe estar en la carpeta `plantillas` y terminar en `.docx` (no `.doc`). |
| Word dice que el archivo está dañado | La plantilla quedó mal guardada. Ábrala en Word y vuelva a *Guardar como .docx*. |
| El botón de generar está gris | Hay algo en rojo en la pestaña 3. Resuélvalo y se activa. |
| Salió un `{{algo}}` impreso en la resolución | Ese dato quedó vacío, o la etiqueta está mal escrita en la plantilla. Corra `revisar_plantilla.py`. |
| Cualquier otra cosa | Corra `python verificar.py`: dice qué está mal y cómo arreglarlo. |

---

## Lo que queda para después

Esta guía cubre la **Etapa 1**: la app en el PC de la sustanciadora. Cuando
esto esté rodando y la plantilla real esté convertida, siguen:

- **Etapa 2** — un PC de la curaduría como servidor, para que todos entren
  desde su navegador y compartan una sola biblioteca de bloques.
- **Etapa 3** — servidor interno, con arranque automático y respaldo.

Las dos usan el mismo código: solo cambia cómo se arranca.
