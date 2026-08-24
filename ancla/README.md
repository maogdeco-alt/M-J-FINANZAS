# Ancla — para los días donde todo cuesta

App aparte de la de finanzas, independiente a propósito (aunque más adelante se puede
enlazar algo puntual entre las dos, y esta versión ya está armada pensando en eso — ver
"Preparado para Supabase" más abajo). Nace de una necesidad concreta: TDAH marcado + TOC,
donde cosas simples —comer, bañarse, ir al baño, elegir ropa, empezar una tarea chiquita—
se vuelven genuinamente difíciles sin un empujón externo, y donde la señal de hambre/sed/
cansancio a veces simplemente no llega.

No es una app de hábitos genérica. Cada decisión de diseño de acá responde a algo
específico de vivir con TDAH y TOC a la vez, con máxima prioridad en dos cosas: **fricción
casi cero** (un toque, nunca un formulario) y **gamificación con gancho instantáneo** (algo
pasa en la pantalla apenas tocas algo — no hay que esperar ni imaginarse el progreso).

> **Estado: beta (v0.16.0)**, para cargar y probar de verdad, con cosas por corregir. La
> versión se muestra abajo del todo en Ajustes → Acerca de Ancla, útil para decir "esto
> pasó en la v0.16.0" al reportar algo raro.

## Menos botones, más lista (v0.16.0)

La pantalla de Hoy tenía **más de veinte cosas tocables** y cansaba. El problema no era solo
la cantidad: era que **cada renglón llevaba un botón macizo**, y una fila de botones pesa
mucho más a la vista que una lista de chequeo, aunque tengan exactamente las mismas
acciones. Se cambió el mecanismo, no solo se escondieron cosas.

- **Los renglones dejaron de ser botones.** Ahora el renglón entero se toca, y a la derecha
  hay una **casilla** (si es algo que se marca) o una **flecha** (si lleva a otra pantalla).
  Se lee como una lista de chequeo tranquila en vez de una hilera de botones compitiendo.
- **La tarjeta grande tiene una sola acción.** La secundaria pasó de bloque sólido a enlace
  discreto del color del tema.
- **El resto del día en un solo renglón.** Antes había cuatro franjas siempre visibles
  (Mañana, Tarde, Noche, Todo el día). Ahora queda abierta la de *ahora* y todo lo demás se
  junta en un renglón único —*Resto del día · 3 de 6*— con los iconos de lo que contiene,
  encendidos si ya está hecho. Un toque lo despliega si hace falta.
- **La tarjeta de nivel se toca entera**, sin botón propio adentro.

De ~21 elementos tocables a **14**, sin quitar ni una sola función.

## Temas de color, y una pantalla que se entiende (v0.15.0)

### Elegir el color de la app
Seis temas completos en Ajustes → *Color de la app*: **Arena, Bruma, Rosa viejo, Bosque,
Lavanda y Noche**, más *Automático* (sigue el modo claro/oscuro del teléfono).

No cambian solo el fondo: cambian **la paleta entera de forma coherente** — tarjetas, texto,
líneas, acentos y también el mundo de Boya, que era justo el azul que aburría. Se aplican
como variables sobre el documento, así que ganan sobre el modo oscuro automático y quedan
guardados.

### Se veía duplicado
La pantalla tenía dos bloques, *Ahora* y *Pendiente ahora*, y el pendiente más urgente
**salía dos veces seguidas**: como tarjeta grande y otra vez como primer renglón. Además los
dos nombres decían lo mismo. Ahora hay **una sola sección, "Lo que sigue"**: el más urgente
va en grande con sus botones, el resto en renglones debajo, y un *"y N más"* si sobran. Un
concepto, un rótulo, sin repeticiones.

### Los botones ya no se ven sueltos
- En la tarjeta grande, la acción principal ocupa el doble que la secundaria, y la
  secundaria pasó a ser un contorno del color del tema — se ve que acompaña, no que compite.
- Todos los botones de renglón miden lo mismo, así la columna queda alineada en vez de
  quebrada.
- La cámara para la foto de respaldo quedaba flotando en el hueco entre casillas; ahora va
  pegada dentro de su casilla y toma el color de esa categoría.

### Se ve qué hay adentro sin abrir
Las franjas cerradas del día mostraban solo un contador. Ahora muestran **los iconos de lo
que contienen**, encendidos si ya está hecho y apagados si no — o sea que *Mañana 2 de 2* se
entiende de un vistazo sin desplegarla.

Los rótulos de sección (*Lo que sigue*, *El día*) pasaron de gris diminuto a un tamaño y
contraste que sí se leen, y los conteos usan un solo formato en toda la app (*4 de 8*).

## Color con oficio, y Boya de vuelta al centro (v0.14.0)

Corrección de rumbo. En la v0.13.0 se confundió **"de adulto" con "sin color"**: se
reemplazaron los emoji por iconos grises y el resultado fue una app beige sobre beige,
apagada y sin alma. El error de fondo fue creer que la sobriedad se consigue quitando
color. No: los adultos no rechazan el color, rechazan el color **incoherente**.

El sistema de iconos era la idea correcta. Pintarlos todos de gris fue el error.

### Un color por dominio, siempre el mismo
Ocho tonos profundos y de saturación pareja — ámbar, terracota, oliva, azul, ciruela,
índigo, agua y humo. Cada cosa tiene el suyo **y no lo cambia nunca**: el desayuno siempre
ámbar, el sueño siempre índigo, los medicamentos siempre ciruela, el trabajo siempre
terracota. Así el color *dice algo* — se reconoce la cosa antes de leer la palabra — en vez
de ser adorno. Y como todos comparten saturación, conviven sin pelearse, que es exactamente
lo que veinte emoji de veinte estilos distintos nunca logran.

El tono viaja con la cosa a donde vaya: la casilla, el renglón de "Pendiente ahora", la
tarjeta *Ahora* y hasta el botón de acción toman el color de lo que está mostrando.

### Boya vuelve a ser el alma
Se la había reducido a una miniatura de 74px en una fila, y buena parte de lo "sin alma"
era eso. Ahora tiene **una escena propia**: fondo con profundidad, su suelo, ella de cuerpo
entero con sombra, y un panel al lado con su estado y el avance del día. Tiene presencia sin
comerse la pantalla como antes (148px, no 230px), y sigue respondiendo al tacto.

### Y algo de profundidad
Fondo con un degradado sutil en vez de un plano beige, sombras reales en la escena, y la
barra de abajo toma el color de la sección en la que estás.

## Revisión completa antes de Supabase (v0.13.0)

Pasada de auditoría en tres frentes —que todo corra, que todo sirva, y que se vea como una
app para una adulta— antes de conectar el backend.

### Que corra
Se escribió un test que **hace clic en todos los botones de todas las pantallas** (119
acciones) y recarga para comprobar persistencia. Cero errores de ejecución. Se corrieron
además todas las suites anteriores sin regresiones.

### Que sirva — dos huecos reales encontrados
Al agregar los módulos nuevos habían quedado desconectados del resto de la app:

- **Los avisos no cubrían ni medicamentos ni perras.** El sistema de recordatorios solo
  sabía de desayuno, almuerzo, cena, dormir y agua — o sea, ignoraba justo lo dos cosas
  más importantes que se agregaron. Ahora los medicamentos avisan **a su hora exacta**, una
  sola vez por casilla y solo si esa toma no está registrada; las perras avisan cuando algo
  lleva mucho vencido, como máximo una vez por hora para no volverse ruido.
- **El sistema de recompensas ignoraba los módulos nuevos.** Se agregaron 7 medallas:
  todas las tomas de un día, 20 tomas registradas, 10 cuidados de las perras, un día
  completo para ellas, el primer bloque de trabajo, llegar a la meta diaria, y 600 minutos
  acumulados. Ahora la parte de juego cubre lo que de verdad cuesta.

### Que se vea de adulta
El problema de fondo era que **los emoji estaban haciendo el trabajo de la interfaz**. Cada
emoji viene con el estilo, el color y el grosor de otra persona, así que veinte emoji juntos
son veinte estilos peleando — y eso es lo que hace que una app se vea infantil o barata.

- **Set de iconos propio**: 25 iconos de una sola familia (mismo trazo, mismo tamaño) que
  **heredan el color del texto**, así el ícono acompaña al estado en vez de gritar por su
  cuenta — gris cuando está pendiente, teal cuando está hecho, coral cuando toca, rojo
  cuando lleva mucho. Reemplazan los emoji en la barra, las categorías, los cuidados, la
  tarjeta *Ahora*, los renglones y Calma.
- **El cuarto de Boya, ilustrado**: la planta, la lámpara, la alfombra, el cuadro, el
  estante y la ventana estaban puestos como emoji y se veían como calcomanías pegadas.
  Ahora están dibujados con el mismo trazo que Boya, así que el cuarto se lee como una sola
  ilustración. Lo mismo con las cosas tiradas cuando está desordenado.
- **Se conservan los emoji donde sí son contenido**: los que ella elige para sus
  recordatorios, la ropa de Boya en la tienda y las medallas.
- **"Pendiente ahora" ya no abruma**: mostraba las cuatro cosas de cada perra, o sea seis
  renglones. Ahora muestra solo lo más urgente de cada una, con tope de cuatro y un
  *"y N más en Cuidados ›"*.
- **Español de Colombia**: se había colado voseo argentino ("elegí", "por vos", "tocá",
  "volvés"). Corregido en toda la app.

## Medicamentos, y una interfaz que se puede leer (v0.12.0)

### Medicamentos
Van por **hora fija**, no por intervalo como las perras — y la pregunta que hay que
responder no es "¿ya toca?" sino **"¿ya me la tomé o me lo estoy imaginando?"**.

- Cada toma del día es **una casilla con su hora**. De un vistazo se ve cuál está tomada
  (y a qué hora exacta se tomó), cuál está sin registro y cuál es más tarde. No hay que
  recordar: se ve.
- Las horas se editan tocándolas.
- **Red de seguridad contra doble dosis**: si marcas una toma y ya registraste otra hace
  menos de 45 minutos, la app pregunta antes de anotarla. Y si marcaste una por error,
  tocarla otra vez ofrece borrar el registro.
- **Límite deliberado**: Ancla registra y recuerda. *Qué hacer con una dosis saltada lo
  decide ella con su médico, no la app* — no sugiere tomar, saltar ni doblar nada.
- Una toma vencida es lo primero en "Ahora", por encima de todo lo demás.

### El rediseño
El problema no era el contenido, era que **todo pesaba igual**: diez tarjetas idénticas,
mismo fondo, mismo borde, mismo tamaño, compitiendo entre sí. Cuando todo grita, no se oye
nada. Las reglas nuevas:

1. **Una sola cosa fuerte por pantalla.** La tarjeta *Ahora* es la única con tratamiento
   marcado. Todo lo demás se calla.
2. **Lo secundario va en renglones, no en cajas.** "Pendiente ahora" es una lista de
   renglones sobre el fondo, sin tarjeta propia por ítem.
3. **Un solo acento.** El coral se reserva para *la* acción; lo vencido usa el rojo
   profundo. El resto es tinta y gris — sin color decorativo.
4. **Lo que ya está hecho no ocupa espacio.** El día se pliega: solo la franja de *ahora*
   viene abierta, las demás quedan en un renglón con su contador y se abren con un toque.
5. **Boya acompaña, no protagoniza.** En Hoy pasa a un retrato compacto con el estado y el
   avance del día; sigue respondiendo al tacto. A tamaño completo vive en su cuarto, que es
   donde tiene sentido que sea la estrella.

Resultado: Hoy pasó de ~10 bloques del mismo peso a 4 niveles claros — Ahora, Boya,
Pendiente ahora, El día — y el progreso quedó de último, a propósito.

### Navegación
Medicamentos y perras son el mismo tipo de problema (cosas con hora que se olvidan), así
que comparten pestaña: **Cuidados**. La barra queda
**Hoy · Cuidados · Enfoque · Calma · Más**.

## De registrar el pasado a conducir el presente (v0.11.0)

El diagnóstico: hasta acá Ancla **anotaba lo que ya había pasado** (marcar que comí,
que me duché). Eso deja fuera lo más difícil, que es *hacer* la cosa. Y dejaba fuera algo
que pesa más que cualquier hábito propio: **las perras dependen de ella y no pueden
recordarle nada.**

### El registro ahora tiene hora
Todo el estado anterior era "hoy sí / hoy no". Con TDAH el problema casi nunca es saber
**si** algo pasó — es no tener ni idea de **cuándo**. Se agregó un registro de eventos con
marca de tiempo, del que sale el dato que la cabeza no guarda: *hace cuánto*. Es la base
de todo lo demás.

### Las perras
Módulo propio, porque no es autocuidado: es cuidado de alguien que depende de ti.

- Se agregan por nombre. Cada una tiene comida, salida, paseo largo y agua fresca, con las
  veces al día configurables (o apagadas si no aplican).
- Cada línea muestra **hace cuánto fue la última vez y a qué hora exacta** — siempre a la
  vista, para que no haya que acordarse: basta con mirar. Eso responde solo la pregunta de
  "¿ya comieron o me lo estoy imaginando?".
- Cuando pasa el intervalo esperado, la línea se marca; si pasa mucho más, se marca fuerte.
  **La urgencia está en el color, nunca en las palabras**: no dice "olvidaste", dice qué
  toca y cuándo fue la última vez.
- En Hoy aparecen siempre, agrupadas por perra, y se registran de un toque sin entrar.

### Enfoque: las dos horas, en pedazos
"Dos horas al día" es imposible de empezar porque el cerebro ve las dos horas enteras.

- **Nunca se empieza una sesión larga.** El botón principal es *"Arrancar 5 minutos"*.
  Cuando suena, decides si sigues — nunca al revés.
- Temporizador grande y a la vista, porque el tiempo no se siente. La sesión vive en los
  datos guardados, así que **si cierras la app sigue corriendo** y al volver está ahí.
- Los minutos se acumulan hacia la meta del día, que es configurable: *si nunca llegas, no
  es que falles, es que la meta está mal puesta.*
- **Captura de distracciones**: durante la sesión hay una caja de "se me ocurrió algo".
  Lo escribes, se guarda en tus pendientes y sigues. No hay que perseguir el pensamiento
  ni perderlo.
- Boya se queda trabajando a tu lado en su escritorio mientras dura el bloque.

### Vestirme
"Decide tú" pasó a ser una pantalla propia y se le quitó la decisión de encima: dices si
hace frío, normal o calor, y Ancla saca **una** de las combinaciones que ya guardaste, en
grande. Aceptas o pides otra. Nada más.

### "Ahora": una sola cosa
Arriba de Hoy hay una tarjeta que responde **qué toca en este momento**, con el botón para
hacerlo ahí mismo. Una lista obliga a elegir, y elegir es justo lo que se traba. El orden
de prioridad es explícito: primero lo que afecta a alguien que depende de ti, después la
sesión de trabajo que dejaste abierta, después tú, después el trabajo pendiente.

### Navegación
La barra pasó a **Hoy · Perras · Enfoque · Calma · Más**, ordenada por lo que se usa varias
veces al día. Rutinas, Vestirme, el cuarto de Boya, Herramientas, Avisos y Ajustes viven
ahora dentro de *Más*.

## Boya redibujada: se acabó lo que se despegaba (v0.10.0)

Se reportaron dos cosas: que partes del cuerpo se separaban al animarse, y que en general
se veía artificial y poco tierna. La primera era un bug real, no una impresión.

**El bug de las partes que se despegan.** Las piezas animadas (cola, brazo, ojos) tenían el
punto de giro mal calculado:

- La cola y el brazo usaban `transform-box:fill-box`, que hace que un `transform-origin` en
  píxeles se mida **desde la esquina de la caja de esa pieza**, no desde el sistema de
  coordenadas del dibujo. El pivote de la cola terminaba cayendo *fuera del personaje*, así
  que al girar hacía palanca desde lejos y se despegaba del cuerpo.
- Los ojos directamente no tenían `transform-origin`, así que al parpadear se encogían hacia
  el **centro del cuerpo**: literalmente se deslizaban cara abajo en cada parpadeo.

Corregido con `transform-box:view-box` y pivotes en coordenadas del dibujo, y verificado
congelando la animación en el fotograma exacto del parpadeo y en el extremo del giro de la
cola, para comprobar que nada se mueve de su sitio.

**El rediseño.** El cuerpo era un montón de elipses apiladas, y se notaban las costuras
donde una tapaba a la otra — ese era el aspecto de "recortable" que se veía artificial.
Ahora:

- **Una sola silueta continua** para cabeza y cuerpo: un único contorno, sin uniones
  visibles. Lo que va detrás (cola, orejas, patas, capa) queda tapado por el relleno, así
  que se lee como un cuerpo entero y no como piezas pegadas.
- **Volumen de verdad**: sombra interior pegada al contorno (recortada con `clipPath`),
  luz arriba, sombra abajo y bajo la barbilla. Eso es lo que hace que se vea redonda en vez
  de plana.
- **Cara más tierna**: ojos más grandes y juntos, con brillos; dos cachetes suaves que le
  dan estructura al hocico; boca en "w"; rubor visible en los estados buenos; cejas suaves
  en los estados bajos.
- **Cola de nutria de verdad**: gruesa en la base y afinándose, en vez del alambre de antes.
  El viewBox se ensanchó porque el cuerpo ocupaba todo el ancho y no le dejaba sitio.
- **Concha bien dibujada** entre las manos, con sus estrías, en vez de un asterisco.
- **Mechones de pelo** en el borde, recortados para que no se salgan del contorno.
- **La capa ahora cuelga por detrás** (antes se dibujaba delante y tapaba toda la panza como
  un babero): se ve el broche al cuello y la tela asomando por los lados.
- **Sin brazos largos**: las manitas van apoyadas en la panza, que es la pose real de una
  nutria de pie, y además así no queda ninguna pieza suelta que se pueda separar.

## Boya, más compacta, viva y con manta propia (v0.9.0)

Esta vuelta fue exclusivamente calidad: la anatomía, el movimiento y la sensación de que
el cuarto es un lugar habitado, no una foto fija.

- **Se acabó la animación "de péndulo"**: antes el cuerpo entero rotaba desde los pies (se
  veía como un juguete inclinándose de lado a lado) y el brazo saludaba en bucle infinito,
  sin que nadie la tocara, al mismo tiempo que la cola se movía en un reloj distinto. Tres
  movimientos sueltos y descoordinados = la sensación de "raro" que se reportó. Ahora hay
  **un solo movimiento**: una respiración sutil (sube/baja + un leve estiramiento, sin
  rotación), y el saludo del brazo **solo pasa cuando la tocas** — como debía ser desde el
  principio.
- **Cuerpo recompuesto para verse compacta, no alargada**: el torso pasó de ser una elipse
  angosta y larga a una más ancha y corta, las piernas y los brazos se acortaron y se
  recogieron más cerca del cuerpo. La cabeza (grande, como antes) no se tocó — es lo que le
  da su aire de personaje, no de animal realista. El resultado es una nutria más redonda,
  más "de escritorio", menos desproporcionada.
- **Ahora se le ve dormir y comer, en su cuarto**: según la hora del día y lo que ya
  registraste hoy —
  - Entre las 11pm y las 6am aparece **dormida**, tapada con su propia manta, ojos
    cerrados — y respira más lento.
  - En una ventana de comida (mañana/tarde/noche) si ya marcaste esa comida, aparece
    **comiendo**, con un platito entre las manos en vez del objeto que sostiene normalmente.
  - Fuera de esos momentos, sigue de pie como siempre. Nada de esto se guarda aparte: usa
    los mismos datos que ya registrás.
- **Decorar el cuarto, de verdad**: se agregó un selector de **pared** directo en el cuarto
  — un puñado de círculos de color, uno por cada fondo que hayas comprado (más el de
  siempre por defecto). Tocás uno y el cuarto cambia al instante, sin tener que ir a buscarlo
  entre la ropa. Es la primera pieza de "decorar algo del cuarto" con control directo, no
  solo automático.

## Boya, de cuerpo completo, con su propio cuarto (v0.8.0)

Boya pasa a ser el centro real de la app, con nombre definitivo — su nombre es **Boya**.

- **Cuerpo completo**: cabeza, torso, brazos, patas — ya no es solo una cara. Por eso la
  ropa por fin se ve puesta de verdad: la capa drapea sobre un torso real, el collar cae
  sobre un pecho real, en vez de flotar sobre nada.
- **Mucho más grande y presente en "Hoy"**: pasó de un círculo de 84px a un escenario
  propio a todo el ancho de la pantalla, con ella de pie de cuerpo entero.
- **Diálogo real**: al tocarla, ya no aparece como aviso genérico — sale de su boca en un
  globo de diálogo, con animación de saludo (el brazo se mueve).
- **El cuarto de Boya**, la pieza más importante de esta vuelta: su panel dedicado ahora
  es un cuarto de verdad —pared, piso, ella parada ahí— que **refleja el cuidado real de
  los últimos 3 días**, no algo decorativo nada más:
  - Poco cuidado reciente → el cuarto se ve desordenado (cosas tiradas por el piso, luz
    apagada) y lo que ya está decorado se ve deslucido.
  - Cuidado sostenido → el cuarto se ve impecable, brillante, con destellos.
  - La idea es exactamente la que se pidió: si el cuarto de Boya se ve desordenado, es una
    señal de que hace falta volver a ordenarlo — sin culpa, solo información visual.
  - **Tienda de decoración nueva**: planta, lámpara, alfombra, cuadro, estante, ventana —
    se compran con conchitas como todo lo demás y quedan puestas en el cuarto para
    siempre, sin necesidad de "equipar" nada.

## Organización real (v0.7.0)

La prioridad de esta vuelta: que la app sea útil de verdad, no solo entretenida.

- **"Hoy" organizado por momentos del día** (Mañana / Tarde / Noche + "Todo el día" para
  agua y baño) en vez de una parrilla plana — el momento actual se marca, pero absolutamente
  todo sigue tocable siempre, así sea tarde. Estructura real, sin agregar un solo toque
  extra a la app.
- **Pestaña "Rutinas"** — el sistema de organización de verdad, con tres piezas:
  - **Pendientes de hoy**: lista suelta para anotar y tachar, para lo que no es parte de
    ninguna rutina.
  - **Rutinas** con pasos propios (3 plantillas sugeridas — Mañana, Antes de salir, Noche —
    o crear una desde cero), cada una con su propia racha de días seguidos completándola
    (con el mismo margen de un día suelto que ya tiene la racha general).
  - Reemplazó a "Recordatorios" en la barra de abajo — Recordatorios se movió a Ajustes,
    sigue ahí completo, con un botón desde donde siempre estuvo.
- **Foto de respaldo opcional** en desayuno, almuerzo, cena y moverse — un ícono de cámara
  aparece después de marcar la categoría (nunca antes: primero se registra, la foto es
  evidencia extra, no una condición). Da +3 conchas la primera vez por categoría al día.
  A propósito **nunca obligatoria** — pedirla siempre rompería la app justo en un día malo,
  que es cuando más hace falta que siga funcionando.
- **Calma con menú de técnicas**, no una sola: Respirar (la que ya había), Aterrizar
  (5-4-3-2-1), y dos nuevas — **Relajación muscular progresiva** (tensar y soltar grupos
  de músculos, paso a paso) y **Solo mirar** (una escena de agua animada, sin nada que hacer
  ni lograr). Elegís la que necesites, ninguna en fila obligada.

**Límite honesto de las fotos**: viven comprimidas en `localStorage`, igual que el resto de
los datos — sin backend todavía, no se pueden guardar para siempre sin arriesgar quedarse
sin espacio. Por eso las fotos de más de 14 días se borran solas (los datos de esos días
quedan intactos, solo la imagen se va). Esto se resuelve de raíz conectando Supabase
(Storage tiene el espacio y la persistencia que `localStorage` no puede dar) — ver más abajo.

## Identidad visual (v0.6.0)

Ancla es para adultas neurodivergentes, no para niños — el diseño lo dice explícito:

- **Tipografía**: Fraunces (serifa con carácter, itálica en el nombre y en momentos con
  voz propia) para jerarquía editorial, Karla para el cuerpo, IBM Plex Mono para cifras
  (racha, nivel, conchas) — que las cifras se vean "medidas", no decorativas.
- **Paleta**: océano de noche, no pastel de guardería — petróleo profundo, terracota
  quemada, musgo apagado en vez de menta chicle y coral de fruta.
- **Forma**: bordes menos redondeados, sombras discretas — menos "todo es una burbuja
  flotando".
- **Voz**: se quitaron los diminutivos ("dormidita", "vasito", "cosita", "conchitas") y
  se afiló el banco de frases de Boya — menos dulzura genérica, más ingenio seco y
  observación específica. Los encabezados de sección perdieron el emoji decorativo
  (queda donde es icono funcional real, como las categorías del día).

## Qué hace

- **Perfil**: nombre y foto (mini avatar, recortada y comprimida en el momento) al entrar
  por primera vez — saltable con un toque si no tienes ganas ese día. Se puede cambiar
  cuando quieras desde Ajustes. La app te saluda por tu nombre.
- **Hoy**: 8 botones de un solo toque (desayuno, almuerzo, cena, agua, aseo, baño,
  moverme, dormí), con **Boya dentro de un anillo de progreso** que se llena en vivo según
  cuánto llevas del día. Sin formularios, sin campos obligatorios, sin orden que respetar.
- **Boya**, la compañera: una nutria marina dibujada a mano en SVG (con degradados de
  verdad, contorno como personaje de dibujo animado —no ícono plano—, cola que se mueve,
  textura de pelaje, ojos con brillo), no un emoji. Cinco estados de ánimo según cuánto
  llevas del día, cada uno con ojos y boca distintos, y parpadeo + bamboleo constante para
  que se sienta viva. No es una mascota que "se muere" si no la cuidas (ese patrón genera
  culpa, no ayuda) — en el peor de los casos está dormidita, nunca en peligro. Tocarla da
  un mensaje corto y amable.
- **Nace de un huevo**: la primera vez que se abre Ancla, antes de pedir ningún dato,
  aparece un huevo — al tocarlo se tambalea y se rompe (con confeti) y ahí nace tu nutria,
  recién entonces se le pone nombre a ella y a ti. Después crece de verdad: **cría** (recién
  nacida, sin bigotes, más chiquita) → **joven** → **adulta** con todo el detalle — el
  crecimiento sigue el nivel de vínculo, no el calendario, así que avanza con el uso real,
  no con el tiempo que pasa sola en el celular.
- **Vínculo con Boya**: aparte del progreso de autocuidado de hoy, hay una relación de
  fondo que solo crece — con cada check-in, cada vez que la tocas, cada compra. Tiene sus
  propios niveles ("Recién se conocen" → "Inseparables"), con una frase que describe cómo
  va esa relación, cada vez más cercana. Se abre tocando "Ver a Boya" desde Hoy.
- **Tienda de conchas 🐚**: moneda aparte de los puntos que suben de nivel — se gana con
  cada check-in del día a día y se gasta vistiendo a Boya: gorros (lana, paja, boina,
  pañuelo pirata, corona), gafas (sol, redondas, de corazón), cuello (bufanda, moño,
  collar de conchas, capa de heroína), y fondos alternativos para su círculo (atardecer,
  noche estrellada, arrecife). Algunos accesorios piden cierto nivel de vínculo para
  desbloquearse. Todo lo comprado es tuyo para siempre — se puede poner y quitar sin volver
  a pagarlo. Hay dos medallas ligadas directamente a esto: el primer regalo que le haces, y
  llegar al vínculo máximo con ella.
- **Boya "inteligente"**: al tocarla no repite frases al azar sin más — nota si llevas una
  racha larga (y te lo dice con el número exacto), si es de madrugada, si el día se fue en
  blanco, o si es la primera vez que se conocen, y ajusta lo que dice. También aparece
  dentro del círculo de respiración en Calma, "respirando" contigo.
- **Gancho instantáneo en cada toque**: al marcar algo salta un "+puntos" flotando, un pop
  de sonido, una vibración cortita (celular) y, en hitos (medalla nueva, subir de nivel,
  día completo), una tarjeta de celebración a pantalla completa con confeti. Todo se puede
  apagar por partes: el confeti se atenúa solo en modo suave, y sonido/vibración tienen su
  propio interruptor en Ajustes.
- **Racha, nivel y medallas**: mismo espíritu de "capa de juego" que ya usa la app de
  finanzas (racha/nivel/medallas), pero con ajustes clave para TDAH:
  - La racha **perdona un día suelto** — solo se rompe con dos días seguidos sin cumplir
    el mínimo. Evita el colapso de "todo o nada" típico de RSD (sensibilidad al rechazo).
  - Hay una medalla — **"Volviste"** — que se gana por reabrir la app después de varios
    días sin entrar. Premiar el regreso, no solo la constancia, es a propósito.
  - **Una medalla ganada no se pierde nunca**, así después dejes de cumplir la condición
    (se guarda aparte, no se recalcula desde cero cada vez).
- **Modo suave**: como el TOC puede convertir un sistema de números/rachas en otra cosa
  para chequear compulsivamente, hay un interruptor que cambia todo el lenguaje numérico
  por palabras cualitativas y baja la intensidad del confeti. Si la app detecta que se
  abrió 6+ veces en la última hora, ofrece activarlo sola (se puede ignorar, no insiste el
  resto del día).
- **Decide tú**: guarda combinaciones de ropa que ya sabes que te sirven; un botón elige
  por ti (rotando, sin repetir si hay opción) para cuando elegir se vuelve la parte
  imposible del día.
- **Mini recordatorios**: además de los 8 de siempre, puedes agregar los tuyos —
  medicina, regar una planta, llamar a alguien— con un emoji corto y un texto. Aparecen
  como botones de un toque en Hoy, igual de simples que el resto.
- **Divide esta tarea**: seis chips de un toque para lo más común (lavar ropa, lavar
  platos, ordenar el cuarto, sacar la basura, responder mensajes, trabajo/tarea) — o
  escribes la tuya si es otra cosa. La app la parte en 4-5 pasos chiquitos y concretos,
  con casillas para ir tachando.
- **Recordatorios**: horarios configurables para comidas/dormir + aviso de agua cada N
  horas, con botones sueltos de "recuérdamelo en 30 min" sin tener que configurar nada.
- **Calma**, pestaña propia en la barra de abajo (no escondida, para cuando los estímulos
  son muchos y buscar algo cuesta): respiración guiada tipo "caja" (inhala 4s, sostén 4s,
  exhala 4s, sostén 4s, con un círculo que se expande y se contrae) y un ejercicio de
  aterrizaje 5-4-3-2-1 (nombrar cosas que ves, tocas, oyes, hueles, sientes). A propósito
  **sin números, sin racha, sin conchas** — es la única sección de la app donde no hay
  nada que ganar, solo bajar el ritmo. El lenguaje evita el "todo está bien" (puede sonar
  invalidante en medio de una crisis real) y usa en cambio algo tipo "vamos a respirar
  juntas". No incluye línea de crisis ni contactos de emergencia en esta vuelta — quedó
  fuera a propósito, se puede sumar después si se decide que sí.

## Cómo usarla

No necesita cuenta ni internet. Los datos viven solo en el navegador/celular donde la
abras (`localStorage`), nada se sube a ningún servidor.

**Para probarla ya**: abre `ancla/index.html` directamente en el navegador.

**Para tenerla como una app en el celular** (recomendado, así los recordatorios funcionan
mejor y queda un ícono en la pantalla de inicio):

1. Sube la carpeta `ancla/` a Netlify (arrastrar y soltar, igual que `app/original.html`)
   o a cualquier hosting estático — necesita que `index.html`, `manifest.json`, `sw.js`
   e `icon.svg` queden en la misma carpeta.
2. Abre la URL en el celular.
3. **Android/Chrome**: te va a ofrecer "Agregar a pantalla de inicio" (o desde el menú ⋮).
   **iPhone/Safari**: botón compartir → "Agregar a pantalla de inicio".
4. Ábrela desde el ícono nuevo, no desde el navegador — así corre como app instalada.

## Límite honesto de los recordatorios (v1)

Los recordatorios de esta versión funcionan **mientras la app está abierta** (o
instalada y abierta) — revisan la hora cada 30 segundos y usan la API de notificaciones
del navegador. Eso quiere decir:

- Si cierras la app del todo, no van a sonar. No es una notificación push real de
  servidor todavía.
- En iPhone, las notificaciones web solo existen si la app está agregada a la pantalla de
  inicio (iOS 16.4+) — desde Safari normal no van a aparecer como notificación del
  sistema, solo como aviso dentro de la app.
- Si el navegador bloquea el permiso, la app avisa igual por dentro (mensaje + parpadeo
  del título de la pestaña), nunca se queda callada sin decir qué pasó.

Arreglar esto de raíz (notificaciones reales aunque la app esté cerrada) necesita un
service worker con *push* + un backend pequeño que las dispare (por ejemplo, Supabase Edge
Functions + Web Push, o algo como OneSignal) — queda como fase 2, ver abajo.

## Copia de seguridad

Como todo vive en el dispositivo, en Ajustes hay **"Descargar copia"** (exporta un
`.json`) e **"Importar copia"** — vale la pena descargar una copia de vez en cuando,
sobre todo antes de cambiar de celular o borrar el navegador.

## Preparado para Supabase (todavía no conectado) — próximo paso real

Esta beta sigue siendo 100% local a propósito, pero el modelo de datos ya está pensado
para no tener que rehacerse cuando se conecte Supabase:

- `usuario:{nombre, foto}` mapea directo a una futura fila en `profiles` — el único
  cambio real sería subir la foto a Supabase Storage en vez de guardarla como imagen
  incrustada, y guardar la URL en vez del archivo. Lo mismo para `entradas[fecha].fotos`
  (comidas/ejercicio) — hoy son imágenes comprimidas dentro del JSON local con poda a los
  14 días; en Supabase Storage no habría que borrar nada nunca.
- `entradas`, `ropa`, `miniRecordatorios`, `rutinas`, `pendientes`, `contadores` y
  `medallasGanadas` ya son estructuras independientes por tipo (no un blob mezclado),
  listas para volverse tablas con `usuario_id`.
- Cuando se conecte, la idea es que siga funcionando offline-first: seguir escribiendo en
  `localStorage` al toque y sincronizar en segundo plano, nunca bloquear un toque
  esperando red — eso rompería la fricción cero que es la prioridad de esta app.

**Lo que hace falta de tu parte para dar este paso** (no lo puedo crear yo por vos):

1. Entra a [supabase.com](https://supabase.com) y crea un proyecto nuevo, gratis — igual
   que ya hiciste para la app de finanzas (mismo proveedor, pero **un proyecto aparte**,
   no el mismo: Ancla no debe compartir base de datos con tus finanzas).
2. Cuando el proyecto esté listo, entra a **Project Settings → API** y copia dos cosas:
   el **Project URL** y la **llave anon/public**.
3. Me las pasás (o las pegás vos misma en una pantalla de "Conectar" dentro de Ancla,
   como ya funciona en `app/hogar.html`) y desde ahí armo el esquema (tablas, políticas
   de seguridad por usuario) y la sincronización real.

Avisame cuando tengas el proyecto creado y seguimos con eso.

## Fase 2 (ideas, no compromisos)

- Conectar Supabase (ver arriba) para respaldo automático y, más adelante, sincronizar
  entre celular y computador sin exportar/importar a mano.
- Notificaciones push reales (con backend), para que los recordatorios funcionen con la
  app cerrada.
- Empacar como app real de celular con Capacitor (mismo camino que ya se documentó para
  la app de finanzas en `docs/arquitectura-multiusuario.md`), para notificaciones nativas
  de verdad y no depender de que el navegador esté abierto.
- Enlace puntual y opcional con la app de finanzas: por ejemplo, un aviso suave si hay
  gasto en restaurantes/domicilios pero ninguna comida marcada en Ancla ese día — nunca
  automático ni obligatorio, y nunca compartiendo datos sin que la persona lo prenda ella
  misma.
- Recordatorio de medicación (si aplica), con la misma lógica de un toque = registrado.
- Modo "otra persona lo revisa" opcional, para quien quiera accountability compartido —
  siempre con consentimiento explícito, nunca vigilancia.

## Por qué existe

Esta app parte de una experiencia real, no de una lista genérica de "hábitos saludables":
días enteros sin comer porque el hambre no avisa, elegir ropa que se vuelve una pared,
tareas simples que se sienten imposibles sin algo que las haga concretas y con
recompensa. La apuesta es que, si funciona para eso, probablemente le sirva a más gente
con TDAH y/o TOC marcados — por eso el diseño evita a propósito culpa, vergüenza y
lenguaje de "deberías".
