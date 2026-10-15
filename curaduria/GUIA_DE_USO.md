# Guía de instalación y uso

De un computador sin nada instalado hasta la primera resolución generada.
Son **9 pasos**. La primera vez toma unos 30 minutos; después, arrancar la app
es un doble clic.

---

## Parte A · Instalar (una sola vez)

### 1. Instalar Python

Entre a **https://www.python.org/downloads/**, descargue la versión para
Windows y ejecute el instalador.

> **En la primera pantalla marque la casilla "Add python.exe to PATH"**, abajo.
> Es el paso que más se olvida y sin él nada funciona.

Luego *Install Now* y espere a que termine.

### 2. Poner la carpeta en el PC

Copie la carpeta `curaduria` a un lugar estable, por ejemplo
`C:\Resoluciones`. No la deje en el Escritorio ni en Descargas.

### 3. Instalar la app

Doble clic en **`instalar.bat`**.

Se abre una ventana negra que descarga lo necesario, crea la plantilla de
ejemplo y comprueba que todo quedó bien. Al final debe decir
*"Instalacion completa"*.

Si dice `[FALLA]` en alguna línea, ahí mismo aparece el remedio. El caso más
común es *"Python no está instalado o no quedó en el PATH"*: vuelva al paso 1
y marque la casilla.

---

## Parte B · Configurar (una sola vez)

### 4. Arrancar

Doble clic en **`iniciar.bat`**. Se abre el navegador en
`http://localhost:8501`.

> **La ventana negra que queda abierta es la app.** Si la cierra, la app se
> apaga. Minimícela. Para apagarla al final del día, ciérrela.

### 5. Llenar la configuración del despacho

Pestaña **Ajustes → Configuración**: curaduría, municipio, departamento, código
DANE, nombre de quien firma, tratamiento (Curadora / Curador), si está en
provisionalidad, nombre de la sustanciadora y sus iniciales. Clic en
**Guardar configuración**.

Estos datos aparecen cerca de **cincuenta veces** en una resolución. **No hay
que volver a escribirlos nunca.** Si cambia la curadora, se corrigen aquí y
listo.

---

## Parte C · Preparar la plantilla de la curaduría (una sola vez)

La app trae una plantilla de ejemplo para que pueda probar de una. Cuando
quiera usar la plantilla real de la curaduría, son dos pasos.

### 6. Guardarla como .docx

La plantilla modelo está en `.doc`, el formato viejo de Word, que la app no
puede leer.

1. Ábrala en Word.
2. **Archivo → Guardar como → Documento de Word (*.docx)**.
3. Guárdela en la carpeta `plantillas` de la app.

### 7. Prepararla con un comando

En la ventana negra escriba (cambiando el nombre por el de su archivo):

```
python preparar_plantilla.py plantillas\MI_PLANTILLA.docx
```

Le muestra **qué haría, sin tocar nada**. Si está de acuerdo, repita con
`--aplicar`:

```
python preparar_plantilla.py plantillas\MI_PLANTILLA.docx --aplicar
```

Queda un archivo nuevo, `MI_PLANTILLA_lista.docx`. **La original no se
modifica.**

En un solo paso hace las tres cosas que tocaría hacer a mano:

| Qué hace | En la plantilla modelo de construcción |
|---|---|
| Cambia los espacios en blanco (`XXXX`, `____`, `XX de ___ de 2026`) por la etiqueta que corresponde | **73 espacios** |
| Cambia los datos del despacho escritos a mano por su etiqueta | **26 veces "Ibagué"** |
| Recorta el catálogo de párrafos y deja las anclas de sección | **174 párrafos**, 4 anclas |

Lo que no pueda resolver con seguridad lo deja con la raya y se lo reporta: en
la plantilla modelo, **1 de 100**. Una etiqueta equivocada imprimiría el dato
de otro campo sin que se note; una raya se ve.

> **Los 174 párrafos recortados no se pierden.** Están en la biblioteca de
> bloques de la app, y de ahí se escogen según el caso en la pestaña 2. Eso es
> exactamente lo que ahorra borrar media resolución cada vez.

Ábrala en Word para revisarla, y después elíjala en la barra lateral de la
app. *(Lo mismo se puede hacer desde la app: barra lateral → Revisar esta
plantilla → Preparar esta plantilla.)*

---

## Parte D · Hacer una resolución

### 8. Llenar los datos (pestaña 1 · Datos)

Arriba hay una barra que dice **cuántos datos van listos y cuáles faltan**.
Se llena de arriba abajo:

1. **Qué se solicita** — trámite, modalidades (se pueden combinar) y
   destinación.
2. **Identificación del acto** — número y fecha, radicado y su fecha, y el
   consecutivo del expediente (el número completo `73001-2-26-0054` se arma
   solo).
3. **Titulares y quién radica** — una fila por persona. *Sugerir sexo por el
   nombre* lo propone; **verifíquelo**. Con dos o más titulares el texto pasa
   a plural solo. Abajo: ¿radica el titular, un apoderado o el representante
   legal?
4. **Predio** — matrícula, ficha catastral, dirección.
5. **El proyecto** — pisos, cubierta y **solo las áreas que la modalidad
   necesita**.

**Los campos se corrigen solos.** Escriba la matrícula sin guion
(`350250605`) y queda `350-250605`; la ficha de 15 dígitos se agrupa sola; los
nombres pasan a mayúscula; las cédulas quedan con puntos de miles.

Todo lo que está en *Datos adicionales* es opcional: lo que deje vacío sale en
el cuadro con una raya.

### 9. Elegir los párrafos y generar

**Pestaña 2 · Párrafos** — el catálogo viene filtrado por el trámite y los obligatorios
ya marcados. Marque lo que aplique al caso: ¿hubo citación a vecinos?
¿intervino un tercero? ¿es VIS? Cada bloque tiene una nota de cuándo se usa y
un botón *Ver texto* que lo muestra con los datos ya puestos.

**Pestaña 3 · Generar** — en rojo lo que impide generar, en amarillo lo que conviene
revisar. Clic en **Generar documento de Word** → **Descargar resolución**.

Ábralo en Word y termine las precisiones propias de la solicitud: el
documento es 100% editable.

---

## Para el día a día

- **Sus propios párrafos**: Ajustes → Biblioteca. Guarde los que use seguido
  con una nota de cuándo aplican. Quedan disponibles en la pestaña 2 y **no se
  pierden** al actualizar la app.
- **Respaldo**: doble clic en `respaldar.bat` una vez a la semana. Copia
  `biblioteca` y `plantillas`, que es lo único que la app guarda en disco.
- **Si algo se siente raro**: `python verificar.py` dice qué está mal y cómo
  arreglarlo.

---

## Si algo sale mal

| Qué pasa | Qué hacer |
|---|---|
| *"Python no se reconoce como un comando"* | No quedó en el PATH. Reinstale Python marcando *"Add python.exe to PATH"*. |
| *"No se puede acceder a este sitio"* | La ventana negra se cerró. Doble clic en `iniciar.bat`. |
| La app se ve rara o en blanco | Recargue con `Ctrl + F5`. |
| *"Address already in use"* | Ya hay una copia corriendo: use la pestaña abierta. |
| La plantilla no aparece en la lista | Debe estar en `plantillas` y terminar en `.docx` (no `.doc`). |
| Word dice que el archivo está dañado | Ábrala en Word y vuelva a *Guardar como .docx*. |
| El botón de generar está gris | Hay algo en rojo en la pestaña 3, o falta la configuración. |
| Salió un `{{algo}}` impreso en la resolución | La etiqueta está mal escrita en la plantilla. Corra `python revisar_plantilla.py plantillas\su_plantilla.docx`. |
| Cualquier otra cosa | `python verificar.py` |

---

## Después

Esto es la **Etapa 1**: la app en el PC de la sustanciadora. Cuando esté
rodando siguen la **Etapa 2** (un PC de la curaduría como servidor, para que
todos entren desde su navegador y compartan la biblioteca) y la **Etapa 3**
(servidor interno con arranque automático). Las dos usan el mismo código:
solo cambia cómo se arranca.
