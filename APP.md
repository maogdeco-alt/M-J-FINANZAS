# Radicados Semanales — descripción completa de la app

Documento de referencia para el proyecto de Claude. Todo lo de aquí está sacado del código,
no de la memoria de nadie. Última revisión: 10 de octubre de 2026.

---

## 1. PARA QUÉ EXISTE

El Área de Masivas de la Subdirección de Contravenciones (Secretaría Distrital de Movilidad de
Bogotá) recibe cada día radicados de PQRS y comparendos asignados por ORFEO. Hay que clasificar
cada uno y entregar cada semana **dos archivos**:

| Archivo | Columnas | Qué lleva |
|---|---|---|
| **MASIVA** | 27 | Todo lo clasificado, menos DEVUELTO y AGENDAMIENTO |
| **PLANTILLA DE AGENDAMIENTOS** | 15 | Solo los AGENDAMIENTO, con su cita |

La app organiza ese trabajo y genera los dos archivos. **No reemplaza a ORFEO ni a Fénix**: toma
lo que se copia de ellos, lo valida y lo arma.

Trabajan cuatro personas en el área. Cada una entra con su correo y ve solo lo suyo.

---

## 2. CÓMO ESTÁ HECHA

- **Un solo archivo**: `radicados-semanales/index.html`, ~12 900 líneas. HTML, CSS y JavaScript
  en el mismo archivo. **No hay compilación, ni npm, ni framework.** Se edita y se publica.
- **SheetJS 0.18.5** (versión comunidad) va incrustada dentro. Al analizar el archivo con
  herramientas de texto hay que excluirla: `awk 'length($0)<3000' index.html`.
- **Netlify** la publica. **Supabase** guarda la copia en la nube.
- Se puede instalar como aplicación (PWA) en PC y celular. `sw.js` es el service worker, con
  estrategia *primero la red*: nunca se queda pegado en una versión vieja.
- Funciona **sin internet**; sincroniza cuando vuelve.

### Archivos del repositorio

```
radicados-semanales/
  index.html            la app entera
  verificador.html      comprobación independiente (ver §7)
  sw.js                 service worker (PWA)
  manifest.webmanifest  nombre e iconos de la app instalada
  netlify.toml          cabeceras y publicación
  icons/                iconos
  supabase/migrations/  el SQL de la base
  README.md             instalación y uso
  INSTRUCTIVO_PRIORITARIOS.md
PROTOCOLO.md            las 9 invariantes y las 6 reglas de cambio
APP.md                  este documento
PROYECTO_CLAUDE.md      cómo montar el proyecto de Claude
pruebas/                33 pruebas automáticas (ver §8)
```

### Configuración que NUNCA se toca

Dentro de `index.html`, cerca de la línea 2834:

```js
var HARDCODED_SUPABASE_CONFIG = {
  url: "https://hgfqoodogpxhqbdyubsd.supabase.co",
  anonKey: "sb_publishable_iCRdHg1fDvtG481Zw7nxsg_w8CWmrFo"
};
```

Si esto cambia, la app deja de sincronizar y nadie se entera hasta que falta trabajo. **Se
verifica después de cada edición.**

### Dónde se guarda cada cosa

| Clave en el navegador | Qué guarda |
|---|---|
| `radicados_semanales_v2::<correo>` | los radicados de la semana en curso |
| `radicados_historial_v1::<correo>` | las semanas ya cerradas |
| `radicados_settings_v1::<correo>` | ajustes, parámetros de reglas, bitácora |
| `radicados_manana_v1::<correo>` | el bloque de la mañana (hoy apagado) |
| `radicados_bloque_v1::<correo>::<ventana>` | en qué bloque estaba cada ventana |
| `radicados_repetidos_ok_v1::<correo>` | repeticiones confirmadas a mano |
| `radicados_borrados_v1` | canal entre ventanas para avisar de borrados |

Todas llevan el correo: dos personas en el mismo computador nunca se mezclan. En Supabase, cada
persona es una fila con las columnas `records`, `history`, `settings` y `manana`.

La sesión (los tokens) vive **solo en memoria**, nunca en el navegador: al recargar hay que
entrar de nuevo, a propósito.

---

## 3. EL FLUJO DE TRABAJO

```
ORFEO  ──(pegar el bloque)──►  PASO 1  Importar la semana
                                  │
                              PASO 2  Clasificar uno por uno
                                  │     · pegar la línea de Fénix
                                  │     · elegir clasificación
                                  │     · correo, resolución, fecha
                                  │
                           REVISIÓN PREVIA  ◄── obligatoria, no bloquea
                                  │
                     ┌────────────┴────────────┐
                 MASIVA .xlsx          AGENDAMIENTOS .xlsx
                                  │
                           CERRAR SEMANA  ──► Historial
```

**Cerrar la semana es parte del trabajo, no un extra.** Si no se cierra, su lote sigue vivo y
entra en todas las entregas siguientes. Así se entregaron 124 radicados de agosto el 2 de octubre.

### Las dos entradas de datos

1. **El bloque de ORFEO** (Paso 1): se pega tal cual. Cada línea trae radicado, fecha de
   radicación, fecha de asignación y nombre. La app detecta sola la forma del bloque (4 o 5
   columnas) y avisa línea por línea de lo que no cuadre.
2. **La línea de Fénix** (Paso 2): se copia del sistema Fénix y se pega entera. La app la separa
   en comparendo, código, fechas, medio, estado, documento, nombre del infractor y placa.
   **Hay que pegarla completa**: de ella salen ocho columnas de la masiva.

---

## 4. LAS PANTALLAS

La barra de arriba tiene seis botones; todo lo demás vive dentro de ventanas.

| Botón | Qué abre |
|---|---|
| **Importar semana** | pegar el bloque de ORFEO |
| **Agendamientos** | la lista de agendamientos, su término y la plantilla |
| **Historial** | todo lo pasado por la app: entregado, devuelto, agendado, sin clasificar |
| **Descargar masiva** | genera el archivo (pasa por la revisión previa) |
| **Documentos** | masiva, cuadre, revisar una masiva hecha fuera, respaldo .json |
| **Cerrar semana** | archiva la semana y deja la lista limpia |

Ventanas principales: `#importDialog`, `#agendaDialog`, `#historialDialog`, `#documentosDialog`,
`#cuadreDialog`, `#preflightDialog`, `#reglasDialog`, `#settingsDialog`, `#auditarMasivaDialog`,
`#alertaInmediataDialog`, `#repetidoDialog`, `#termCalcDialog`.

**Ventana flotante**: la app puede abrirse en una ventanita siempre visible (picture-in-picture)
para capturar mientras se mira ORFEO. Recuerda su posición, su filtro y en qué radicado estaba.

---

## 5. LAS 28 REGLAS

Viven en un registro único (`var REGLAS`) y las aplica **un solo motor**
(`hallazgosDeRegistro`). No hay reglas escritas dos veces: si una cambia, cambia en todos los
sitios a la vez. Los parámetros se editan en Ajustes, con doble verificación y bitácora.

| Regla | Grupo | Cuándo | Qué dice |
|---|---|---|---|
| **R01** | Clasificación | captura | El Formato solo acepta una clasificación de la lista. |
| **R02** | Masiva | masiva | DEVUELTO y AGENDAMIENTO nunca salen en la masiva. |
| **R03** | Masiva | masiva | Un formato que no existe queda fuera — pero se muestra en grande. |
| **R04** | Comparendo | captura | Solo T10 puede ir sin comparendo; las demás lo exigen. |
| **R05** | Resolución | captura | T6 y T10 no llevan resolución. |
| **R06** | Resolución | captura | T1, T5, T11 y T14 siempre llevan resolución. |
| **R07** | Comparendo | captura | T1 es siempre comparendo MANUAL (medio = COMPARENDERA). |
| **R08** | Comparendo | captura | T14 es siempre comparendo ELECTRÓNICO. |
| **R09** | Devolución | captura | Códigos F y D12 obligan a DEVUELTO. |
| **R10** | Devolución | captura | Un comparendo que no esté VIGENTE obliga a DEVUELTO. |
| **R11** | Agendamientos | captura | AGENDAMIENTO exige la PLACA. |
| **R12** | Datos únicos | captura | El mismo radicado no puede aparecer dos veces. |
| **R13** | Datos únicos | captura | Comparendo repetido: avisa, pero es normal. |
| **R14** | Datos únicos | captura | Resolución repetida: avisa, pero es normal. |
| **R15** | Destinatario | masiva | El destinatario tiene que parecer el nombre de una persona. |
| **R16** | Notificación | masiva | En la casilla del correo no puede haber un comparendo. |
| **R17** | Agendamientos | agenda | La plantilla de Agendamientos se revisa antes de bajarla. |
| **R18** | Destinatario | captura | Tipo y número de documento van juntos; nunca se asume cédula. |
| **R19** | Comparendo | captura | La línea de Fénix va completa: el número solo no basta. |
| **R20** | Comparendo | captura | La línea se pega COMO COLUMNAS; si cae en una sola casilla, avisa. |
| **R21** | Comparendo | captura | Si la línea llegó cortada, dice qué falta. |
| **R22** | Comparendo | captura | Cada dato tiene que tener la forma de lo que dice ser. |
| **R23** | Comparendo | captura | Una FECHA DE NOTIFICACIÓN vacía **no** es un error. |
| **R24** | Agendamientos | captura | En un AGENDAMIENTO hay que responder si pidió pruebas. |
| **R25** | Fechas | masiva | Una fecha que no se entiende saldría vacía: se avisa antes. |
| **R26** | Notificación | captura | El correo se comprueba de verdad, no solo si tiene arroba. |
| **R27** | Datos únicos | captura | El radicado tiene que ser 15 dígitos y solo dígitos. |
| **R28** | Comparendo | captura | Un comparendo tiene entre 6 y 12 dígitos. |

### Parámetros editables (Ajustes → Reglas)

```
formatosSinComparendo:            ["T10"]
formatosSinResolucion:            ["T6", "T10"]
formatosConResolucionObligatoria: ["T1", "T5", "T11", "T14"]
formatosManualObligatorio:        ["T1"]
formatosElectronicoObligatorio:   ["T14"]
codigosQueObliganDevuelto:        ["F", "D12"]
estadoValidoComparendo:           "VIGENTE"
formatosFueraDeLaMasiva:          ["DEVUELTO", "AGENDAMIENTO"]
formatosQueExigenPlaca:           ["AGENDAMIENTO"]
gravedadRadicadoRepetido:         "grave"
gravedadComparendoRepetido:       "aviso"
gravedadResolucionRepetida:       "aviso"
dominiosDeCorreoConocidos:        [16 dominios]
comparendoDigitosMin / Max:       "6" / "12"
radicadoDigitos:                  "15"
```

### Dónde avisa cada cosa

- **Al guardar**: solo las reglas imperativas (nunca bloquean el guardado).
- **Al avanzar** (Guardar y siguiente / Siguiente / Anterior): el motor completo.
- **En la revisión previa**, antes de generar el archivo: el motor completo otra vez,
  incluidas las ya confirmadas, que se listan aparte.
- **R27 no frena al avanzar** a propósito: el radicado viene importado, no se escribe a mano.

Un aviso se puede confirmar («es correcto»), y entonces deja de preguntar **para ese dato
concreto**: si el dato cambia, vuelve a preguntar.

---

## 6. LAS CLASIFICACIONES

```
T1, T5, T6, T10, T11, T14, AGENDAMIENTO, DEVUELTO, PRORROGA, PRORROGA SDA
```

- **T10** = petición oscura: va legítimamente sin comparendo y sin destinatario.
- **DEVUELTO** y **AGENDAMIENTO** no entran en la masiva.
- En la plantilla de agendamientos, la columna FORMATO solo admite
  **AGENDAR CON PRUEBAS** o **AGENDAR SIN PRUEBAS** — lo decide la abogada caso por caso, y la
  app lo pregunta de frente.

### Los términos

- **Término del radicado**: 13 días hábiles desde el día siguiente a la **fecha de asignación**.
  Con 12 o más transcurridos, el radicado se marca prioritario y sube al principio de la cola.
- **Término del ciudadano para pedir audiencia**: 5 u 11 días hábiles según el tipo de comparendo,
  desde el día siguiente a la **notificación** (o a la imposición si no hay notificación) hasta
  que radicó la solicitud. Nunca se usa la fecha de asignación para esto.

---

## 7. LAS NUEVE INVARIANTES Y EL VERIFICADOR

`PROTOCOLO.md` define nueve propiedades que **todo archivo entregado** debe cumplir. Se comprueban
sobre el `.xlsx` ya generado, sin la app:

1. Ningún radicado repetido
2. Todo radicado de 15 dígitos y numérico
3. Todo radicado del archivo está en ORFEO de esa semana
4. Ninguna fila fuera de la semana declarada
5. Todo correo con estructura válida y dominio conocido
6. Todo comparendo entre 6 y 12 dígitos
7. Las dos columnas COMPARENDO coinciden fila por fila
8. 27 columnas con los títulos exactos y en orden
9. Ningún radicado asignado se queda fuera sin motivo registrado

**`verificador.html`** las comprueba. Es un archivo aparte que **no comparte una sola línea de
lógica con la app**: una comprobación que use el mismo código que produjo el archivo no comprueba
nada. Se abre con doble clic, funciona sin internet, y los archivos nunca salen del computador.
Se le sueltan la masiva, el reporte de ORFEO y la plantilla de agendamientos, y da **APTO** o
**NO APTO** con cada caso y su número de fila, más un informe en Excel.

### El cruce contra ORFEO

Dentro de la app: **Documentos → ¿De dónde sale este número?**

- Desglosa el conteo en grupos que no se solapan y **comprueba que la suma cuadre**.
- Reparte por fecha de asignación: esta semana contra semanas anteriores.
- Permite pegar la lista de ORFEO y dice qué sobra y qué falta, descargable en Excel.
- Permite **sacar solo un rango de fechas**, sin arrastre y sin repetidos.

---

## 8. LAS PRUEBAS

33 suites con navegador más 2 sin navegador (el Excel con cuadrícula), todas contra el `index.html` de verdad (`preparar.sh` rehace la copia en
cada corrida). Manejan la app **por la interfaz**, con clics y teclado, como la usuaria.

```bash
python3 pruebas/mock.py &                     # Supabase de mentira
python3 pruebas/serve.py pruebas/sitio 8871 & # sirve la copia
./pruebas/correr_todo.sh                      # tiene que decir TODAS LAS PRUEBAS PASAN
```

Lo que defiende cada una está en `pruebas/LEEME.md`. Las que más importan:

- **t19** · un radicado sin clasificar no puede quedarse fuera en silencio
- **t20** · el conteo no se infla y se puede explicar (el caso 219 contra 176)
- **t21** · un radicado reasignado en otra semana no pierde ninguna asignación
- **t23** · el verificador contra el caso real del 2 de octubre, anonimizado
- **t24** · correo, radicado y comparendo, caso por caso
- **t25** · la masiva avisa cuando mezcla semanas
- **t26** · el bloque de la mañana, apagado de verdad
- **t27–t30** · principal y flotante a la vez: nada se pierde, nada se cruza, las dos suben a la nube
- **t31** · una semana cerrada no vuelve y su historial no se pierde, aunque el cierre no haya subido
- **t32** · solo los números de radicado: entran y se llenan a mano
- **t33** · sin fecha de asignación: se trabaja igual, se marca «sin fecha», término «sin dato», la masiva lo avisa

`pruebas/caso_2oct/` guarda la masiva, el reporte de ORFEO y los agendamientos de aquella semana
**anonimizados**, conservando la forma exacta de cada defecto. **Nunca se suben datos de
ciudadanos al repositorio.**

---

## 9. LO QUE FALLÓ, Y POR QUÉ

Esta sección importa más que ninguna otra: cada fallo de aquí costó horas de trabajo o un
memorando, y todos siguen el mismo patrón.

| Qué pasó | Causa | Cerrado con |
|---|---|---|
| Un radicado asignado nunca se respondió | La revisión previa no podía ver los radicados sin clasificar: `finalDocEligible` y `finalDocFormatoDesconocido` exigían ambas tener formato | R03 + bloque propio en la revisión previa + aviso al cerrar la semana (t19) |
| El conteo decía 219 y ORFEO 176 | Todas las fusiones comparan por `id` interno, ninguna por radicado: el mismo radicado pegado en dos sitios quedaba dos veces | Reparto por asignación + cuadre del conteo (t20) |
| Agendamientos de la semana pasada mezclados | Al quitar repetidos se juntaba **solo por radicado**: un radicado reasignado perdía la asignación nueva y salía la vieja | Solo se junta con mismo radicado **y** misma fecha de asignación (t21) |
| 124 radicados de agosto en la masiva del 2 de octubre | La masiva exportaba «todo lo que haya»: la palabra «semana» no existía para la app | Aviso de semanas mezcladas + descarga por rango (t25) |
| 34 correos rotos entregados sin una alerta | La regla era, literal, «¿tiene una arroba?» | R26: estructura, lo que sobre delante, espacios y dominio por parecido (t24) |
| Un comparendo entregado como «11» | Ninguna regla miraba la longitud | R28, midiendo el número **corto**, que es el que sale al archivo (t24) |
| Con la principal y la flotante abiertas, una dejaba de subir a la nube y mostraba «Se guardó desde otro lugar» el resto del día | Cada ventana sube con la marca de la última vez; en cuanto sube la otra, la marca queda vieja y Supabase rechaza la subida. La ventana rechazada se rendía. El servidor de mentira de las pruebas aceptaba todo, así que nadie lo vio | Al chocar, se trae la nube, se junta sin quitar nada (lo archivado no resucita) y se vuelve a subir (t27). `mock.py` ahora aplica el filtro como el real |
| Un correo corregido en la flotante volvía al anterior, sin aviso | Lo que una ventana traía de la otra quedaba contado como «cambio hecho aquí», y en su siguiente guardado pisaba la corrección más nueva | La referencia de la mezcla se mueve con lo que se trae (t28 lo encontró, t29 lo fija) |
| Restaurar un punto de restauración deshacía lo corregido después | Los dos argumentos de la mezcla iban al revés: mandaba el dato viejo del punto | Manda lo de ahora; el punto solo rellena huecos, como dice la pantalla (t30) |
| Una semana cerrada volvía a la lista al entrar otra vez, y el historial quedaba vacío | Al iniciar sesión el historial de la nube **reemplazaba** al de este navegador, y los radicados de la copia vieja de la nube se sumaban a la lista. Si el cierre no alcanzó a subir (choque entre ventanas, o sin conexión), la semana volvía entera y su archivo se perdía | Al entrar, los historiales se juntan por fecha de cierre, y un radicado ya archivado que nadie tocó después del cierre no vuelve a la lista (t31) |
| Una lista de solo números de radicado no metía ninguno | La importación exigía 4 columnas (radicado, dos fechas, nombre) | Una línea que es solo un radicado de 15 dígitos entra con lo demás vacío, el informe lo dice y las casillas de fechas y nombre se abren solas (t32) |

Los cinco últimos se encontraron el 10-10-2026, en la auditoría tras el despliegue del bloque de la
mañana. Ninguno lo causó ese bloque: estaban antes. Pero los tres son justo «cruza información» y
«no guarda lo que trabajo», que es lo que se notó.

**El patrón**: ninguno era un error de cálculo. Todos eran **algo que la app no miraba**, y que
por tanto pasaba en silencio hasta que lo encontraba otra persona semanas después.

**La lección**: una batería de pruebas comprueba lo que quien la escribe imagina. Lo que de verdad
encontró estos fallos fue cruzar el archivo real contra ORFEO. Por eso el protocolo se apoya en
invariantes sobre el archivo entregado, no en las pruebas.

---

## 10. EL BLOQUE DE LA MAÑANA (apagado)

Hubo un segundo bloque para las asignaciones que Donina sube a las 8 a.m. **Está apagado** desde
el 10 de octubre de 2026 por decisión de la usuaria: la app se enfoca al 100 % en la masiva.

Se apagó con una constante, **no se borró**:

```js
var BLOQUE_MANANA_ACTIVO = false;   // ponerlo en true lo reactiva
```

Lo guardado en el navegador y en Supabase no se tocó. Sus pruebas (t15, t16, t17, t18) siguen
corriendo contra una copia con el interruptor encendido, para que si se reactiva funcione igual.

Quedó demostrado que **nunca tuvo que ver con ninguno de los fallos**: `t17` comprueba byte a byte
que trabajar en un bloque no mueve nada del otro, en los dos sentidos.

---

## 11. CÓMO SE TRABAJA SOBRE ESTA APP

Lo completo está en `PROTOCOLO.md`. En corto:

1. **Reproducir antes de arreglar.** Si no se puede reproducir, no está entendido.
2. **Primero la prueba que falla**, después el arreglo. Una prueba que nunca falló no demuestra nada.
3. **Ningún cambio silencioso en qué filas salen.** Diff antes/después sobre datos reales, con
   cada diferencia explicada. Esta regla sola habría evitado los dos peores fallos.
4. **Batería completa en verde** antes de cualquier despliegue.
5. **Siempre hay vuelta atrás**: Netlify → Deploys → la versión anterior → *Publish deploy*.
6. **Nunca desplegar en viernes ni el día de la entrega.** El lunes temprano.
7. **ORFEO manda.** La app nunca es la fuente de verdad sobre si se entregó todo.
8. Si una prueba falla, **mirar primero si la equivocada es la prueba**. Ya ha pasado varias veces.
