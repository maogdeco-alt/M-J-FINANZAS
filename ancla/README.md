# Ancla — para los días donde todo cuesta

App aparte de la de finanzas, independiente a propósito (aunque más adelante se puede
enlazar algo puntual entre las dos). Nace de una necesidad concreta: TDAH marcado + TOC,
donde cosas simples —comer, bañarse, ir al baño, elegir ropa, empezar una tarea chiquita—
se vuelven genuinamente difíciles sin un empujón externo, y donde la señal de hambre/sed/
cansancio a veces simplemente no llega.

No es una app de hábitos genérica. Cada decisión de diseño de acá responde a algo
específico de vivir con TDAH y TOC a la vez.

## Qué hace

- **Hoy**: 8 botones de un solo toque (desayuno, almuerzo, cena, agua, aseo, baño,
  moverme, dormí). Sin formularios, sin campos obligatorios, sin orden que respetar.
- **Boya**, la compañera visual: no es una mascota que "se muere" si no la cuidas (ese
  patrón genera culpa, no ayuda). Es un flotador — se hunde un poco, nunca del todo, y
  siempre puede volver a flotar. Tocarla da un mensaje corto y amable al azar.
- **Racha, nivel y medallas**: mismo espíritu de "capa de juego" que ya usa la app de
  finanzas (racha/nivel/medallas), pero con dos ajustes clave para TDAH:
  - La racha **perdona un día suelto** — solo se rompe con dos días seguidos sin cumplir
    el mínimo. Evita el colapso de "todo o nada" típico de RSD (sensibilidad al rechazo).
  - Hay una medalla — **"Volviste"** — que se gana por reabrir la app después de varios
    días sin entrar. Premiar el regreso, no solo la constancia, es a propósito.
- **Modo suave**: como el TOC puede convertir un sistema de números/rachas en otra cosa
  para chequear compulsivamente, hay un interruptor que cambia todo el lenguaje numérico
  por palabras cualitativas. Si la app detecta que se abrió 6+ veces en la última hora,
  ofrece activarlo sola (se puede ignorar, no insiste el resto del día).
- **Decide tú**: guarda combinaciones de ropa que ya sabes que te sirven; un botón elige
  por ti (rotando, sin repetir si hay opción) para cuando elegir se vuelve la parte
  imposible del día.
- **Divide esta tarea**: escribes lo que te abruma ("lavar los platos", "ordenar el
  cuarto"...) y la app la parte en 4-5 pasos chiquitos y concretos, con casillas para ir
  tachando.
- **Recordatorios**: horarios configurables para comidas/dormir + aviso de agua cada N
  horas, con botones sueltos de "recuérdamelo en 30 min" sin tener que configurar nada.

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

## Fase 2 (ideas, no compromisos)

- Notificaciones push reales (con backend), para que los recordatorios funcionen con la
  app cerrada.
- Sincronizar entre dispositivos (opcional — hoy es local a propósito, por privacidad;
  si se agrega, que sea con el mismo patrón de cuenta propia que ya usa `app/hogar.html`,
  nunca obligatorio).
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
