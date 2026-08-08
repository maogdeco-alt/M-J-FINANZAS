# Filosofía de producto — lo que ya existe vs. lo que falta

Punto de partida (en palabras de la fundadora): la meta no es una app de contabilidad,
es enseñar cultura financiera a gente que **nunca en su vida ha llevado ni un Excel** —
sesiones de uso de 1-2 minutos, pocas secciones principales pero bien organizadas por
dentro, con un componente de juego (niveles, rachas, medallas), y un rincón aparte,
reservado, para lo técnico (declaración de renta, extractos) — sin que eso estorbe el
uso diario.

## Buena noticia: casi todo esto ya está construido en `app/original.html`

Revisando el archivo a fondo, esta filosofía ya es, en gran parte, el diseño real de la
app — no hay que inventarla desde cero:

| Lo que se pidió | Dónde ya existe en la app |
|---|---|
| Pocas secciones principales | Barra inferior con solo 5 botones: **Hoy, Mi plata, Movimientos, Pagos, Más** (`NAV` en el código). |
| Cada sección con varias opciones organizadas por dentro | "Movimientos" tiene Lista / Bandeja / En qué se va. "Pagos" tiene Fijos / Deudas / Avisos. "Más" agrupa El año, Entre nosotros, Proyectos, Notas, Ajustes. |
| Enseñar paso a paso desde cero | Tarjeta **"🚀 Primeros pasos"** en la pantalla de Hoy: 4 pasos (poner el saldo, anotar lo fijo, registrar el primer gasto, ponerse una meta), con barra de progreso y el mensaje *"en 10 minutos queda lista"*. Se oculta sola cuando ya completaste los 4. |
| El componente de "videojuego" | Ya existe: **racha** (🔥 días seguidos anotando), **nivel** (Aprendiz → Ordenado → Constante → Estratega → Dueño del cuento → Maestro) y **medallas** (7 días seguidos, metas cumplidas, pagos al día, etc.), visibles en Hoy y en Más. |
| Un rincón aparte para lo técnico, sin estorbar el uso diario | Ya existe, y hasta tiene el mensaje exacto que se pidió: la sección **"🧾 Zona contable"** dice literalmente *"No necesitas entrar aquí para usar la app. Todo lo de esta sección es para cuadrar con el banco o para la declaración de renta."* Adentro: Renta del año, Punto de partida (Formulario 210), Cuadrar con el banco, Movimientos anulados, Exportar todo. |

## Lo que sí vale la pena afinar (ideas, no urgencias)

Nada de esto rompe lo que ya funciona — son ajustes de contenido/redacción, no de
estructura:

1. **Amarrar más las medallas a aprender, no solo a usar.** Hoy las medallas premian
   constancia (racha, pagos a tiempo, metas). Se le podrían sumar medallas de
   *aprendizaje* — ej. "Entendiste qué es la renta" al entrar por primera vez a Zona
   contable, o "Primer mes con Hogar cuadrado" al usar Entre nosotros por primera vez.
2. **La tarjeta de "Primeros pasos" podría mencionar, aunque sea de pasada, por qué
   importa** (no solo qué botón tocar) — una frase corta tipo "así sabes cuánto entra y
   cuánto sale antes de que se te olvide".
3. **Reforzar en el texto de "Zona contable" el "para qué le sirve a la persona"**, no
   solo el "qué contiene" — por ejemplo explicar en una frase qué es declarar renta y
   por qué le podría tocar a alguien sin saberlo (ligado a lo que se comentó: "la
   persona promedio ni sabe que tiene que declarar renta").

Estas tres son cambios chiquitos, de texto, aplicables sin tocar la lógica de la app —
se pueden hacer cuando se decida seguir, sin ningún riesgo de romper lo que ya sirve.
