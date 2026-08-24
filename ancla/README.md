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

> **Estado: beta (v0.5.0)**, para cargar y probar de verdad, con cosas por corregir. La
> versión se muestra abajo del todo en Ajustes → Acerca de Ancla, útil para decir "esto
> pasó en la v0.5.0" al reportar algo raro.

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
- **Tienda de conchitas 🐚**: moneda aparte de los puntos que suben de nivel — se gana con
  cada check-in del día a día y se gasta vistiendo a Boya: gorros (lana, paja, boina,
  pañuelo pirata, corona), gafas (sol, redondas, de corazón), cuello (bufanda, moño,
  collar de conchitas, capa de heroína), y fondos alternativos para su círculo (atardecer,
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
  **sin números, sin racha, sin conchitas** — es la única sección de la app donde no hay
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

## Preparado para Supabase (todavía no conectado)

Esta beta sigue siendo 100% local a propósito, pero el modelo de datos ya está pensado
para no tener que rehacerse cuando se conecte Supabase:

- `usuario:{nombre, foto}` mapea directo a una futura fila en `profiles` — el único
  cambio real sería subir la foto a Supabase Storage en vez de guardarla como imagen
  incrustada, y guardar la URL en vez del archivo.
- `entradas`, `ropa`, `miniRecordatorios`, `contadores` y `medallasGanadas` ya son
  estructuras independientes por tipo (no un blob mezclado), listas para volverse tablas
  con `usuario_id`.
- Cuando se conecte, la idea es que siga funcionando offline-first: seguir escribiendo en
  `localStorage` al toque y sincronizar en segundo plano, nunca bloquear un toque
  esperando red — eso rompería la fricción cero que es la prioridad de esta app.

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
