# 📕 Instructivo: la nueva tarjeta "Prioritarios"

Como si tuvieras 9 años — paso a paso, sin tecnicismos.

---

## 1. ¿Qué le agregamos a la app?

Antes, tu app ya te decía:
- Cuántos radicados **Importaste** en total
- Cuántos están **Pendientes**
- Cuántos ya **Completaste**
- Qué **% de Avance** llevas
- Qué **% de Devueltos** tienes

Le agregamos **una tarjeta nueva, roja, que dice "Prioritarios"**, justo al lado de las demás. Ahí ves de un solo vistazo **cuántos radicados ya se te están venciendo**, sin necesidad de bajar la pantalla ni de revisar caso por caso.

---

## 2. ¿Dónde la vas a ver?

Apenas abras la app, en la parte de arriba, donde ya estaban las tarjetitas de números — vas a ver una tarjeta más, de color rojo, con el título **"Prioritarios"**.

Si le pasas el mouse por encima (o la tocas en el celular), te explica exactamente qué significa el número.

---

## 3. ¿Cómo funciona por dentro? (bien fácil)

Piensa que la app hace esta pregunta por cada radicado que tienes pendiente:

> "¿Ya llevas 12 días hábiles o más desde que TE lo asignaron a ti, y todavía no lo has clasificado?"

- Si la respuesta es **SÍ** → ese radicado cuenta como "Prioritario" (se te está acabando el término de 13 días hábiles).
- Si la respuesta es **NO** → no cuenta.
- Si el radicado **ya lo completaste** (ya tiene Formato puesto) → tampoco cuenta, así lleve mucho tiempo, porque ya no es un pendiente.

La tarjeta simplemente **suma cuántos radicados dijeron "SÍ"** y te muestra ese número grande y en rojo.

Este es exactamente el mismo cálculo que ya usaba la app para poner el radicado de primero en la lista y mostrarle el sello 🔴 PRIORITARIO — no inventamos una regla nueva, solo la convertimos también en un contador visible arriba.

---

## 4. ¿Cómo la implementamos? (los pasos que se dieron, en orden)

1. **Buscamos dónde vivían las otras tarjetas** ("Importados", "Pendientes", "Completados", "Avance", "% Devuelto") dentro del archivo de la app.
2. **Copiamos ese mismo molde** y creamos una tarjeta más, con su propio numerito (`statPrioritarios`) y su propio color rojo (para que salte a la vista, distinto a las demás).
3. **Le dijimos a la app dónde sacar el número**: usamos la misma función que ya existía (`esPrioritario`) — la que decide si un radicado es urgente o no — y simplemente contamos cuántos radicados de tu lista actual dicen que sí.
4. **Conectamos ese conteo con la tarjeta nueva**, para que cada vez que la app se actualiza (importas, guardas, avanzas un caso), el número de la tarjeta se recalcule solo, sin que tengas que hacer nada.
5. **Probamos que el número fuera correcto** antes de subir el cambio: armamos una prueba con radicados de ejemplo (uno viejo y urgente, uno reciente, uno ya completado, uno sin fecha) y confirmamos que la tarjeta contara exactamente el que debía contar y ninguno más.
6. **Subimos el cambio** a tu app (a la misma rama de siempre) — ya quedó guardado y listo.

---

## 5. ¿Tienes que hacer algo tú?

**No.** No necesitas instalar nada, ni configurar nada, ni tocar ningún botón especial. La próxima vez que abras la app (o la recargues), la tarjeta roja de "Prioritarios" va a aparecer sola, ya contando por ti.

---

## 6. Resumen en una frase

> Ahora, con solo mirar arriba de la pantalla —sin bajar el cursor ni revisar caso por caso— sabes de inmediato cuántos radicados se te están por vencer.
