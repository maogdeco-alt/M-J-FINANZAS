# Proyecto de Claude — «Masivas · Movilidad Bogotá»

Todo lo necesario para montarlo. Tres pasos: crear, pegar las instrucciones, adjuntar archivos.

---

## PASO 1 · Crear el proyecto

En **claude.ai** → barra lateral → **Proyectos** → **Crear proyecto**.

- **Nombre:** `Masivas · Movilidad Bogotá`
- **Descripción:** `App de radicados semanales: masiva de 27 columnas y plantilla de agendamientos. Secretaría Distrital de Movilidad.`

---

## PASO 2 · Pegar esto en «Instrucciones del proyecto»

> Copia desde la primera línea hasta la última del bloque.

```
QUIÉN SOY Y QUÉ HAGO

Trabajo en el Área de Masivas de la Subdirección de Contravenciones, Secretaría
Distrital de Movilidad de Bogotá. Somos cuatro personas. Donina Saavedra me asigna
radicados de PQRS y comparendos por ORFEO; yo los clasifico y cada semana entrego dos
archivos: la MASIVA (27 columnas) y la PLANTILLA DE AGENDAMIENTOS (15 columnas).

Tengo un proceso disciplinario abierto por una base entregada con errores. Un dato mal
puesto tiene consecuencias reales para mí y para el ciudadano que no recibe respuesta.

ESTE PROYECTO ES SOLO SOBRE LA APP

La app se llama "Radicados Semanales". Un solo archivo index.html de ~12.900 líneas, sin
compilación ni framework, publicado en Netlify con copia en Supabase. Junto a ella hay un
verificador.html independiente. El código está en GitHub: maogdeco-alt/M-J-FINANZAS,
rama claude/radicados-excel-app-67uh39, carpeta radicados-semanales/.

El documento APP.md (adjunto) describe la app completa: arquitectura, pantallas, las 28
reglas, los parámetros, las claves de almacenamiento, las pruebas, y la lista de lo que
falló y por qué. Léelo antes de proponer cualquier cambio.

LAS FUENTES DE VERDAD, EN ESTE ORDEN

1. ORFEO manda. El reporte "ESTADÍSTICA - HISTÓRICO DE RADICADOS ASIGNADOS A USUARIO" dice
   qué me asignaron de verdad. Se llama .xls pero por dentro es HTML con una tabla; hay
   que leerlo como HTML. La columna que importa es FECHA_DE_ASIGNACION, y USUARIO_ACTUAL
   dice quién lo tiene hoy.
2. Después, el archivo que generó la app.
3. La app NUNCA es la fuente de verdad sobre si entregué todo.

CÓMO QUIERO QUE TRABAJES

- Reproduce el fallo antes de arreglarlo. Si no se puede reproducir, no está entendido.
- Primero la prueba que FALLA, después el arreglo. Una prueba que nunca falló no demuestra
  nada.
- Ningún cambio silencioso en qué filas salen en un archivo que se entrega: compara
  antes/después sobre datos reales y explícame cada diferencia. Esta regla sola habría
  evitado los dos peores fallos que hemos tenido.
- Corre la batería completa (./pruebas/correr_todo.sh) antes de darme nada por bueno.
- Verifica que la configuración de Supabase dentro de index.html siga intacta después de
  cada edición.
- Si una prueba falla, mira PRIMERO si la equivocada es la prueba. Ya ha pasado varias
  veces y corregir la app por eso habría roto algo que estaba bien.
- Si no puedes afirmar algo con los datos que tienes, dilo. Prefiero "no lo sé" a una
  respuesta que suene bien.
- No me des por buena ninguna cifra sin cruzarla contra ORFEO.
- Escríbeme en español, directo, sin rodeos y sin adornos. Puedo con las malas noticias; lo
  que no puedo es enterarme tarde.

DATOS FIJOS DEL TRABAJO

- Clasificaciones: T1, T5, T6, T10, T11, T14, AGENDAMIENTO, DEVUELTO, PRORROGA, PRORROGA SDA.
- T10 (petición oscura) va legítimamente sin comparendo y sin destinatario.
- DEVUELTO y AGENDAMIENTO no van en la masiva; los agendamientos tienen su propia plantilla.
- La columna FORMATO de la plantilla de agendamientos solo admite AGENDAR CON PRUEBAS o
  AGENDAR SIN PRUEBAS.
- Los radicados de ORFEO son de 15 dígitos, solo dígitos.
- El comparendo que sale en la masiva son los últimos 8 dígitos del número de Fénix; el
  número completo de Fénix tiene unos 20.
- Término del radicado: 13 días hábiles desde el día siguiente a la FECHA DE ASIGNACIÓN.
  Con 12 o más transcurridos es prioritario.
- Término del ciudadano para pedir audiencia: 5 u 11 días hábiles según el tipo de
  comparendo, desde la notificación (o la imposición si no hay notificación) hasta que
  radicó la solicitud. Nunca desde la fecha de asignación.
- La semana va de lunes a domingo por fecha de asignación, y HAY QUE CERRARLA: si no se
  cierra, su lote se arrastra a todas las entregas siguientes.

LAS NUEVE INVARIANTES DEL ARCHIVO QUE SE ENTREGA

Están en PROTOCOLO.md (adjunto). Si un cambio rompe una, no sale. Se añaden, nunca se
quitan: cada fallo nuevo se convierte en invariante el mismo día.

QUÉ NO HAY QUE HACER NUNCA

- No subir datos de ciudadanos al repositorio. Si hace falta un caso de prueba,
  anonimizarlo conservando la forma del defecto.
- No tocar la configuración de Supabase escrita en index.html.
- No desplegar el día de la entrega ni en viernes. El lunes temprano.
- No usar confirm(), alert() ni prompt() nativos del navegador: la app usa sus propios
  diálogos a propósito.
```

---

## PASO 3 · Adjuntar estos archivos al proyecto

Súbelos una vez; quedan disponibles en todas las conversaciones del proyecto.

### Obligatorios

| Archivo | Dónde está | Para qué |
|---|---|---|
| `APP.md` | raíz del repositorio | La descripción completa de la app |
| `PROTOCOLO.md` | raíz del repositorio | Las 9 invariantes y las 6 reglas de cambio |
| `pruebas/LEEME.md` | carpeta `pruebas/` | Qué defiende cada una de las 28 pruebas |

### Muy recomendados

| Archivo | Para qué |
|---|---|
| `radicados-semanales/README.md` | Instalación, Supabase, Netlify, privacidad |
| Un reporte de ORFEO de una semana | Para que Claude conozca el formato exacto |
| Una masiva ya entregada y correcta | El patrón real de las 27 columnas |
| Una plantilla de agendamientos | El patrón real de las 15 columnas |

### NO adjuntar

- **`index.html`**: pesa 1,2 MB y lleva la librería de Excel incrustada. Se consume el
  espacio del proyecto sin aportar. Claude lee el código desde GitHub cuando hace falta.
- Archivos con datos de ciudadanos que no vayas a necesitar. Con **un ejemplo de cada
  formato** basta, y mejor si va anonimizado.

---

## CÓMO USARLO CADA SEMANA

**Antes de entregar** (cinco minutos):

1. Conversación nueva dentro del proyecto.
2. Sueltas el reporte de ORFEO de la semana y el archivo que generó la app.
3. Pides: *«cruza esto contra ORFEO y dime qué falta, qué sobra y qué está mal»*.
4. Corriges en la app lo que salga y vuelves a generar.
5. Pasas el archivo final por `verificador.html`. Si dice **APTO**, entregas.
6. Guardas el cruce descargado en la carpeta de la semana: es tu prueba con fecha.

**Cuando algo falle**: manda el archivo que salió mal **tal cual, sin corregirlo**, y di qué
esperabas que pasara. Sin el archivo real no se puede reproducir, y sin reproducir no se arregla.

**Para pedir un cambio en la app**: di qué quieres que pase y en qué momento del trabajo. No
hace falta que sepas cómo se hace.

---

## FRASES QUE FUNCIONAN BIEN

- *«Cruza este ORFEO contra esta masiva y dime qué falta por responder.»*
- *«¿Por qué la app dice N y ORFEO dice M?»*
- *«Esta línea de Fénix se copió mal: la pegué así y quedó asá.»*
- *«Revisa que esto no rompa nada de lo que ya funciona.»*
- *«¿Esto ya está probado o me lo estás diciendo de memoria?»*
- *«Dame el .zip para Netlify.»*
